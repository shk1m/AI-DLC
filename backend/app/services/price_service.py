"""BE-01: PriceService - 시세 데이터 조회 및 분석

핵심 기능:
- 카테고리별 현재 시세 조회
- 품목별 시세 추이 (시계열)
- Spike(이상치) 감지 (Z-Score 기반)
- 도매/소매 Gap 분석
- 캐싱 (Cache-Aside 패턴)

비즈니스 규칙:
- BR-01: 가격 데이터 유효성
- BR-02: Spike 감지 규칙
- BR-07: 데이터 캐싱 규칙
"""

import asyncio
import uuid
from datetime import date, timedelta
from typing import Optional

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.kamis import KamisAdapter
from app.adapters.public_data import PublicDataAdapter
from app.config import get_settings
from app.core.cache import cache_manager
from app.models.food_item import CategoryEnum, FoodItem
from app.models.price_record import PriceRecord, DataSourceEnum
from app.models.spike_event import SpikeEvent, SpikeTypeEnum
from app.schemas.price import (
    CategoryPriceSummary,
    PriceGapInfo,
    PriceItem,
    PriceTimePoint,
    PriceTimeSeries,
    SpikeEventResponse,
)

logger = structlog.get_logger()
settings = get_settings()

# 기간 → 일수 매핑
PERIOD_DAYS_MAP = {
    "1w": 7,
    "1m": 30,
    "3m": 90,
    "6m": 180,
    "1y": 365,
}


class PriceService:
    """시세 조회 및 분석 서비스

    외부 API(KAMIS, 공공데이터)에서 시세를 조회하고,
    캐싱/Spike 감지/Gap 분석 등 비즈니스 로직을 수행합니다.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.kamis_adapter = KamisAdapter()
        self.public_data_adapter = PublicDataAdapter()

    async def get_current_prices(
        self,
        category: str,
        subcategory: Optional[str] = None,
    ) -> list[PriceItem]:
        """카테고리별 현재 시세 조회 (캐시 우선)

        Args:
            category: 대분류 카테고리
            subcategory: 소분류 (선택)

        Returns:
            품목별 현재가 목록
        """
        cache_key = f"prices:{category}:{subcategory or 'all'}:{date.today()}"

        # Cache-Aside: 캐시 확인
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached

        # 캐시 미스 → 외부 API 호출
        logger.info("price_cache_miss", category=category, subcategory=subcategory)

        # 카테고리에 따라 적절한 어댑터 선택
        raw_prices = await self._fetch_from_adapters(category)

        # DB에서 기존 품목 매핑
        items = await self._get_food_items(category, subcategory)
        item_map = {item.name: item for item in items}

        # 결과 구성
        results: list[PriceItem] = []
        for price_data in raw_prices:
            item_name = price_data.get("item_name", "")
            item = item_map.get(item_name)

            if item:
                price_item = PriceItem(
                    item_id=item.id,
                    name=item.name,
                    category=item.category,
                    subcategory=item.subcategory,
                    unit=item.unit,
                    wholesale_price=price_data["wholesale_price"],
                    retail_price=price_data["retail_price"],
                    price_gap=self._calculate_gap(
                        price_data["wholesale_price"],
                        price_data["retail_price"],
                    ),
                    date=price_data.get("date", date.today()),
                    source=price_data.get("source", "KAMIS"),
                )
                results.append(price_item)

        # 캐시 저장 (TTL: 1시간)
        await cache_manager.set(cache_key, results, settings.cache_ttl_prices)

        return results

    async def get_price_history(
        self,
        item_id: str,
        period: str = "1m",
        interval: str = "daily",
    ) -> PriceTimeSeries:
        """품목별 시세 추이 조회

        Args:
            item_id: 품목 UUID
            period: 조회 기간 (1w, 1m, 3m, 6m, 1y)
            interval: 데이터 간격 (daily, weekly)

        Returns:
            시계열 가격 데이터 + Spike 이벤트
        """
        cache_key = f"prices:{item_id}:history:{period}"
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached

        days = PERIOD_DAYS_MAP.get(period, 30)
        date_from = date.today() - timedelta(days=days)

        # DB에서 가격 이력 조회
        stmt = (
            select(PriceRecord)
            .where(PriceRecord.item_id == uuid.UUID(item_id))
            .where(PriceRecord.date >= date_from)
            .order_by(PriceRecord.date)
        )
        result = await self.db.execute(stmt)
        records = result.scalars().all()

        # 품목 정보 조회
        item_stmt = select(FoodItem).where(FoodItem.id == uuid.UUID(item_id))
        item_result = await self.db.execute(item_stmt)
        food_item = item_result.scalar_one_or_none()

        item_name = food_item.name if food_item else "Unknown"

        # 시계열 데이터 구성
        time_series = [
            PriceTimePoint(
                date=record.date,
                wholesale_price=record.wholesale_price,
                retail_price=record.retail_price,
            )
            for record in records
        ]

        # Spike 감지
        spikes = await self.detect_spikes(item_id, period)

        result_data = PriceTimeSeries(
            item_id=uuid.UUID(item_id),
            item_name=item_name,
            period=period,
            time_series=time_series,
            spikes=spikes,
        )

        await cache_manager.set(cache_key, result_data, settings.cache_ttl_prices)
        return result_data

    async def detect_spikes(
        self,
        item_id: str,
        period: str = "1m",
    ) -> list[SpikeEventResponse]:
        """가격 이상치(Spike) 감지 - Z-Score 기반 (BR-02)

        알고리즘:
        1. 이동 평균(MA) 계산 (window=7일)
        2. 이동 표준편차(MSD) 계산 (window=7일)
        3. Z-Score = (price - MA) / MSD
        4. |Z-Score| > 2.0 → Spike 이벤트 생성

        Args:
            item_id: 품목 UUID
            period: 분석 기간

        Returns:
            Spike 이벤트 목록
        """
        days = PERIOD_DAYS_MAP.get(period, 30)
        date_from = date.today() - timedelta(days=days)

        # DB에서 가격 이력 조회
        stmt = (
            select(PriceRecord)
            .where(PriceRecord.item_id == uuid.UUID(item_id))
            .where(PriceRecord.date >= date_from)
            .order_by(PriceRecord.date)
        )
        result = await self.db.execute(stmt)
        records = result.scalars().all()

        # BR-02-2: 최소 7일 이상 데이터 필요
        if len(records) < 7:
            return []

        prices = [r.retail_price for r in records]
        dates = [r.date for r in records]

        # Z-Score 기반 Spike 감지
        spikes: list[SpikeEventResponse] = []
        window = 7

        for i in range(window, len(prices)):
            window_prices = prices[i - window:i]
            ma = sum(window_prices) / len(window_prices)
            msd = (sum((p - ma) ** 2 for p in window_prices) / len(window_prices)) ** 0.5

            if msd == 0:
                continue

            z_score = (prices[i] - ma) / msd

            # BR-02-1: |z_score| >= 2.0 → Spike
            if abs(z_score) >= 2.0:
                spike_type = "급등" if z_score > 0 else "급락"
                magnitude = ((prices[i] - ma) / ma) * 100

                # BR-02-5: 연속 Spike 병합 (3일 이내)
                if spikes and (dates[i] - spikes[-1].date).days <= 3:
                    continue

                spike = SpikeEventResponse(
                    id=uuid.uuid4(),
                    date=dates[i],
                    spike_type=spike_type,
                    magnitude=round(magnitude, 2),
                    baseline_price=round(ma, 2),
                    spike_price=prices[i],
                    news_articles=[],
                )
                spikes.append(spike)

        return spikes

    async def get_price_gap(self, item_id: str) -> PriceGapInfo:
        """도매/소매 Gap 분석

        Args:
            item_id: 품목 UUID

        Returns:
            Gap 분석 정보
        """
        # 최신 가격 레코드 조회
        stmt = (
            select(PriceRecord)
            .where(PriceRecord.item_id == uuid.UUID(item_id))
            .order_by(PriceRecord.date.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()

        # 품목 정보
        item_stmt = select(FoodItem).where(FoodItem.id == uuid.UUID(item_id))
        item_result = await self.db.execute(item_stmt)
        food_item = item_result.scalar_one_or_none()

        if not record or not food_item:
            raise ValueError(f"품목 또는 가격 데이터를 찾을 수 없습니다: {item_id}")

        gap_amount = record.retail_price - record.wholesale_price
        gap_rate = self._calculate_gap(record.wholesale_price, record.retail_price)

        return PriceGapInfo(
            item_id=uuid.UUID(item_id),
            item_name=food_item.name,
            wholesale_price=record.wholesale_price,
            retail_price=record.retail_price,
            gap_amount=gap_amount,
            gap_rate=gap_rate,
            date=record.date,
        )

    async def get_category_summary(self, category: str) -> CategoryPriceSummary:
        """카테고리 요약 통계

        Args:
            category: 대분류 카테고리

        Returns:
            카테고리 요약 (평균 가격, 급등/급락 품목)
        """
        cache_key = f"prices:summary:{category}"
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached

        # 해당 카테고리 품목 수
        item_count_stmt = (
            select(func.count(FoodItem.id))
            .where(FoodItem.category == category)
        )
        count_result = await self.db.execute(item_count_stmt)
        total_items = count_result.scalar() or 0

        # 최근 가격 평균
        recent_date = date.today() - timedelta(days=7)
        avg_stmt = (
            select(
                func.avg(PriceRecord.wholesale_price),
                func.avg(PriceRecord.retail_price),
            )
            .join(FoodItem, PriceRecord.item_id == FoodItem.id)
            .where(FoodItem.category == category)
            .where(PriceRecord.date >= recent_date)
        )
        avg_result = await self.db.execute(avg_stmt)
        avg_row = avg_result.one_or_none()

        avg_wholesale = float(avg_row[0] or 0) if avg_row else 0
        avg_retail = float(avg_row[1] or 0) if avg_row else 0
        avg_gap = self._calculate_gap(avg_wholesale, avg_retail) if avg_wholesale > 0 else 0

        summary = CategoryPriceSummary(
            category=CategoryEnum(category) if category in [e.value for e in CategoryEnum] else CategoryEnum.VEGETABLE,
            total_items=total_items,
            avg_wholesale_price=round(avg_wholesale, 2),
            avg_retail_price=round(avg_retail, 2),
            avg_gap_rate=round(avg_gap, 2),
            top_surge_items=[],
            top_drop_items=[],
        )

        await cache_manager.set(cache_key, summary, settings.cache_ttl_prices)
        return summary

    # ─── Private Methods ───────────────────────────────────────────

    async def _fetch_from_adapters(self, category: str) -> list[dict]:
        """카테고리에 따라 적절한 어댑터에서 시세 조회"""
        if category in ("채소류", "과일류", "구황작물"):
            return await self.kamis_adapter.fetch_prices(category)
        elif category in ("수산물", "축산류", "가공식품"):
            return await self.public_data_adapter.fetch_prices(category)
        else:
            # 병렬 호출
            kamis_task = self.kamis_adapter.fetch_prices(category)
            public_task = self.public_data_adapter.fetch_prices(category)
            results = await asyncio.gather(kamis_task, public_task, return_exceptions=True)

            combined = []
            for r in results:
                if isinstance(r, list):
                    combined.extend(r)
            return combined

    async def _get_food_items(
        self, category: str, subcategory: Optional[str] = None
    ) -> list[FoodItem]:
        """DB에서 식자재 목록 조회"""
        stmt = select(FoodItem).where(FoodItem.category == category)
        if subcategory:
            stmt = stmt.where(FoodItem.subcategory == subcategory)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def _calculate_gap(wholesale: float, retail: float) -> float:
        """도매/소매 Gap 비율 계산 (BR-01)"""
        if wholesale <= 0:
            return 0.0
        return round(((retail - wholesale) / wholesale) * 100, 2)
