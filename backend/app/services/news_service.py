"""BE-05: NewsService - 뉴스 수집 및 시세 이벤트 매핑

핵심 기능:
- 네이버 뉴스 검색
- Spike 이벤트에 뉴스 매핑
- 정부 보도자료 크롤링
- 검색어 트렌드 조회

비즈니스 규칙:
- BR-06: 뉴스 크롤링 규칙
- BR-07: 데이터 캐싱 규칙
"""

import uuid
from datetime import date, datetime, timedelta
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.naver import NaverAdapter
from app.config import get_settings
from app.core.cache import cache_manager
from app.models.news_article import NewsArticle, NewsSourceEnum
from app.schemas.news import NewsArticleResponse, TrendKeyword
from app.schemas.price import SpikeEventResponse

logger = structlog.get_logger()
settings = get_settings()


# 식자재 관련 키워드 목록
FOOD_KEYWORDS = [
    "배추", "무", "양파", "마늘", "고추", "상추", "시금치",
    "고등어", "삼치", "갈치", "새우", "전복",
    "한우", "돼지고기", "닭고기", "계란",
    "사과", "배", "감귤", "바나나",
]

PRICE_KEYWORDS = ["가격", "시세", "흉작", "풍작", "수입", "급등", "급락"]


class NewsService:
    """뉴스 수집 및 시세 이벤트 매핑 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.naver_adapter = NaverAdapter()

    async def search_news(
        self,
        keyword: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> list[NewsArticleResponse]:
        """뉴스 검색

        Args:
            keyword: 검색 키워드 (최대 50자, BR-08-7)
            date_from: 시작일 (YYYY-MM-DD)
            date_to: 종료일 (YYYY-MM-DD)

        Returns:
            뉴스 기사 목록
        """
        cache_key = f"news:{keyword}:{date.today()}"
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached

        logger.info("news_search", keyword=keyword)

        # 네이버 뉴스 검색
        raw_articles = await self.naver_adapter.search_news(
            keyword=keyword,
            display=20,
            sort="date",
        )

        results: list[NewsArticleResponse] = []
        for article in raw_articles:
            # BR-06-3: 식자재 키워드 1개 이상 포함 확인
            title = article.get("title", "")
            has_food_keyword = any(
                kw in title for kw in FOOD_KEYWORDS
            )

            if not has_food_keyword and keyword not in title:
                continue

            news_response = NewsArticleResponse(
                id=uuid.uuid4(),
                title=title,
                url=article.get("url", ""),
                source="네이버뉴스",
                published_at=self._parse_date(article.get("published_at", "")),
                keywords=self._extract_keywords(title),
                related_items=[],
                summary=article.get("description", ""),
            )
            results.append(news_response)

        # 캐시 저장 (TTL: 30분)
        await cache_manager.set(cache_key, results, settings.cache_ttl_news)
        return results

    async def get_news_for_spike(
        self,
        spike_event: SpikeEventResponse,
        item_name: str,
    ) -> list[NewsArticleResponse]:
        """Spike 이벤트에 뉴스 매핑

        뉴스 매핑 로직:
        1. Spike 발생일 기준 ±3일 범위 설정
        2. 해당 품목 키워드로 뉴스 검색
        3. 상위 3개 뉴스 매핑

        Args:
            spike_event: Spike 이벤트
            item_name: 품목명

        Returns:
            관련 뉴스 목록 (최대 3개)
        """
        # 검색 키워드 구성
        search_keyword = f"{item_name} 가격"

        # 네이버 뉴스 검색
        raw_articles = await self.naver_adapter.search_news(
            keyword=search_keyword,
            display=10,
            sort="sim",  # 관련도순
        )

        # 시간 근접도 기반 필터링 (±3일)
        spike_date = spike_event.date
        results: list[NewsArticleResponse] = []

        for article in raw_articles:
            pub_date = self._parse_date(article.get("published_at", ""))
            days_diff = abs((pub_date.date() - spike_date).days)

            if days_diff <= 3:
                news_response = NewsArticleResponse(
                    id=uuid.uuid4(),
                    title=article.get("title", ""),
                    url=article.get("url", ""),
                    source="네이버뉴스",
                    published_at=pub_date,
                    keywords=self._extract_keywords(article.get("title", "")),
                    related_items=[],
                    summary=article.get("description", ""),
                )
                results.append(news_response)

            if len(results) >= 3:
                break

        return results

    async def crawl_government_press(self) -> list[NewsArticleResponse]:
        """정부 보도자료 크롤링 (BR-06-4: 3회 재시도)

        대상:
        - 농림축산식품부 보도자료
        - 해양수산부 보도자료

        Returns:
            크롤링된 보도자료 목록
        """
        logger.info("government_press_crawl_start")
        results: list[NewsArticleResponse] = []

        # 농림축산식품부
        mafra_articles = await self._crawl_mafra()
        results.extend(mafra_articles)

        # 해양수산부
        mof_articles = await self._crawl_mof()
        results.extend(mof_articles)

        # DB 저장 (BR-06-1: 중복 URL 체크)
        saved_count = await self._save_articles(results)
        logger.info(
            "government_press_crawl_complete",
            total=len(results),
            saved=saved_count,
        )

        return results

    async def get_trend_keywords(
        self,
        category: str,
    ) -> list[TrendKeyword]:
        """검색어 트렌드 조회 (네이버 데이터랩)

        Args:
            category: 식자재 카테고리

        Returns:
            트렌드 키워드 목록
        """
        cache_key = f"trends:{category}"
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached

        # 카테고리별 키워드 선택
        keywords = self._get_category_keywords(category)

        # 네이버 데이터랩 조회
        raw_trends = await self.naver_adapter.get_search_trend(
            keywords=keywords[:5],
            time_unit="week",
        )

        results = [
            TrendKeyword(
                keyword=t["keyword"],
                ratio=t["ratio"],
                period=t["period"],
                category=category,
            )
            for t in raw_trends
        ]

        # 캐시 저장 (TTL: 6시간)
        await cache_manager.set(cache_key, results, settings.cache_ttl_trends)
        return results

    # ─── Private Methods ───────────────────────────────────────────

    async def _crawl_mafra(self) -> list[NewsArticleResponse]:
        """농림축산식품부 보도자료 크롤링"""
        # 실제 구현에서는 BeautifulSoup으로 크롤링
        # 시연용: 빈 리스트 반환 (Unit 4에서 구현)
        logger.info("mafra_crawl_placeholder")
        return []

    async def _crawl_mof(self) -> list[NewsArticleResponse]:
        """해양수산부 보도자료 크롤링"""
        # 실제 구현에서는 BeautifulSoup으로 크롤링
        # 시연용: 빈 리스트 반환 (Unit 4에서 구현)
        logger.info("mof_crawl_placeholder")
        return []

    async def _save_articles(
        self, articles: list[NewsArticleResponse]
    ) -> int:
        """뉴스 기사 DB 저장 (BR-06-1: URL 중복 체크)"""
        saved_count = 0

        for article in articles:
            # 중복 체크
            existing_stmt = select(NewsArticle).where(
                NewsArticle.url == article.url
            )
            existing = await self.db.execute(existing_stmt)
            if existing.scalar_one_or_none():
                continue

            # 새 기사 저장
            db_article = NewsArticle(
                id=article.id,
                title=article.title,
                url=article.url,
                source=NewsSourceEnum.NAVER,
                published_at=article.published_at,
                keywords=article.keywords,
                summary=article.summary,
            )
            self.db.add(db_article)
            saved_count += 1

        if saved_count > 0:
            await self.db.flush()

        return saved_count

    @staticmethod
    def _extract_keywords(text: str) -> list[str]:
        """텍스트에서 식자재 키워드 추출"""
        found = []
        for kw in FOOD_KEYWORDS:
            if kw in text:
                found.append(kw)
        for kw in PRICE_KEYWORDS:
            if kw in text:
                found.append(kw)
        return found

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """날짜 문자열 파싱 (다양한 포맷 지원)"""
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except (ValueError, TypeError):
                continue
        return datetime.utcnow()

    @staticmethod
    def _get_category_keywords(category: str) -> list[str]:
        """카테고리별 트렌드 검색 키워드"""
        category_keywords = {
            "채소류": ["배추 가격", "양파 시세", "마늘 가격", "고추 시세", "상추"],
            "수산물": ["고등어 가격", "삼치 시세", "새우 가격", "전복", "갈치"],
            "축산류": ["한우 가격", "돼지고기 시세", "닭고기 가격", "계란 가격"],
            "과일류": ["사과 가격", "배 시세", "감귤 가격", "바나나"],
            "가공식품": ["식용유 가격", "밀가루 시세", "설탕 가격"],
        }
        return category_keywords.get(category, ["식자재 가격"])
