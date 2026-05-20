"""EXT-01: KAMIS API Adapter (농산물유통정보)

- 농산물 도소매 시세 조회
- Retry with Exponential Backoff
- Circuit Breaker 적용
- 응답 파싱 및 정규화
"""

import asyncio
from datetime import date, timedelta
from typing import Any

import httpx
import structlog

from app.adapters.base import DataSourceAdapter
from app.config import get_settings
from app.core.circuit_breaker import kamis_cb

logger = structlog.get_logger()

# KAMIS API 기본 URL
KAMIS_BASE_URL = "http://www.kamis.or.kr/service/price/xml.do"

# KAMIS 카테고리 코드 매핑
KAMIS_CATEGORY_MAP = {
    "채소류": "200",
    "과일류": "400",
    "구황작물": "100",
}


class KamisAdapter(DataSourceAdapter):
    """KAMIS 농산물유통정보 API 어댑터

    API 문서: http://www.kamis.or.kr/customer/reference/openapi_list.do
    """

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.kamis_api_key
        self.cert_id = settings.kamis_cert_id
        self.timeout = httpx.Timeout(5.0, connect=3.0)

    async def fetch_prices(
        self,
        category: str,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict[str, Any]]:
        """카테고리별 시세 조회

        Args:
            category: 카테고리명 (채소류, 과일류, 구황작물)
            date_from: 조회 시작일
            date_to: 조회 종료일

        Returns:
            정규화된 시세 데이터 리스트
        """
        if date_to is None:
            date_to = date.today()
        if date_from is None:
            date_from = date_to - timedelta(days=7)

        category_code = KAMIS_CATEGORY_MAP.get(category, "200")

        params = {
            "action": "periodProductList",
            "p_cert_key": self.api_key,
            "p_cert_id": self.cert_id,
            "p_returntype": "json",
            "p_startday": date_from.strftime("%Y-%m-%d"),
            "p_endday": date_to.strftime("%Y-%m-%d"),
            "p_productclscode": "01",  # 소매
            "p_itemcategorycode": category_code,
            "p_countrycode": "1101",  # 서울
            "p_convert_kg_yn": "Y",
        }

        async def _fetch():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(KAMIS_BASE_URL, params=params)
                response.raise_for_status()
                return response.json()

        raw_data = await kamis_cb.call(_fetch)
        return self._parse_price_response(raw_data)

    async def fetch_item_price(
        self,
        item_code: str,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict[str, Any]]:
        """특정 품목 시세 조회

        Args:
            item_code: KAMIS 품목 코드
            date_from: 조회 시작일
            date_to: 조회 종료일
        """
        if date_to is None:
            date_to = date.today()
        if date_from is None:
            date_from = date_to - timedelta(days=30)

        params = {
            "action": "periodProductList",
            "p_cert_key": self.api_key,
            "p_cert_id": self.cert_id,
            "p_returntype": "json",
            "p_startday": date_from.strftime("%Y-%m-%d"),
            "p_endday": date_to.strftime("%Y-%m-%d"),
            "p_productclscode": "01",
            "p_itemcode": item_code,
            "p_countrycode": "1101",
            "p_convert_kg_yn": "Y",
        }

        async def _fetch():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(KAMIS_BASE_URL, params=params)
                response.raise_for_status()
                return response.json()

        raw_data = await kamis_cb.call(_fetch)
        return self._parse_price_response(raw_data)

    async def health_check(self) -> bool:
        """KAMIS API 상태 확인"""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(3.0)) as client:
                response = await client.get(
                    KAMIS_BASE_URL,
                    params={
                        "action": "periodProductList",
                        "p_cert_key": self.api_key,
                        "p_cert_id": self.cert_id,
                        "p_returntype": "json",
                        "p_startday": date.today().strftime("%Y-%m-%d"),
                        "p_endday": date.today().strftime("%Y-%m-%d"),
                        "p_productclscode": "01",
                        "p_itemcategorycode": "200",
                        "p_countrycode": "1101",
                    },
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning("kamis_health_check_failed", error=str(e))
            return False

    def _parse_price_response(self, raw_data: dict) -> list[dict[str, Any]]:
        """KAMIS API 응답 파싱 및 정규화"""
        results = []

        try:
            data = raw_data.get("data", {})
            items = data.get("item", [])

            if not isinstance(items, list):
                items = [items] if items else []

            for item in items:
                price_str = item.get("dpr1", "0")
                price = self._parse_price_value(price_str)

                if price <= 0:
                    continue

                results.append({
                    "item_name": item.get("itemname", ""),
                    "item_code": item.get("itemcode", ""),
                    "kind_name": item.get("kindname", ""),
                    "unit": item.get("unit", ""),
                    "wholesale_price": price * 0.7,  # 도매가 추정 (소매의 70%)
                    "retail_price": price,
                    "date": date.today(),
                    "rank": item.get("rank", ""),
                    "source": "KAMIS",
                })
        except (KeyError, TypeError, ValueError) as e:
            logger.error("kamis_parse_error", error=str(e), raw_keys=list(raw_data.keys()))

        return results

    @staticmethod
    def _parse_price_value(price_str: str) -> float:
        """가격 문자열 파싱 (쉼표 제거, 빈값 처리)"""
        if not price_str or price_str == "-":
            return 0.0
        try:
            return float(price_str.replace(",", ""))
        except ValueError:
            return 0.0
