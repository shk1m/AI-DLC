"""EXT-03: Naver API Adapter (네이버 검색 + 데이터랩)

- 네이버 뉴스 검색 API
- 네이버 데이터랩 검색어 트렌드 API
- Circuit Breaker 적용
- Retry with Exponential Backoff
"""

from datetime import date, timedelta
from typing import Any

import httpx
import structlog

from app.config import get_settings
from app.core.circuit_breaker import naver_cb

logger = structlog.get_logger()

# 네이버 API 엔드포인트
NAVER_SEARCH_URL = "https://openapi.naver.com/v1/search/news.json"
NAVER_DATALAB_URL = "https://openapi.naver.com/v1/datalab/search"


class NaverAdapter:
    """네이버 검색 API + 데이터랩 어댑터

    - 뉴스 검색: 키워드 기반 뉴스 기사 검색
    - 데이터랩: 검색어 트렌드 조회
    """

    def __init__(self):
        settings = get_settings()
        self.client_id = settings.naver_client_id
        self.client_secret = settings.naver_client_secret
        self.timeout = httpx.Timeout(5.0, connect=3.0)

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

    async def search_news(
        self,
        keyword: str,
        display: int = 10,
        start: int = 1,
        sort: str = "date",
    ) -> list[dict[str, Any]]:
        """네이버 뉴스 검색

        Args:
            keyword: 검색 키워드
            display: 결과 개수 (최대 100)
            start: 시작 위치
            sort: 정렬 (date: 최신순, sim: 관련도순)

        Returns:
            뉴스 기사 리스트
        """
        params = {
            "query": keyword,
            "display": min(display, 100),
            "start": start,
            "sort": sort,
        }

        async def _fetch():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    NAVER_SEARCH_URL,
                    params=params,
                    headers=self._headers,
                )
                response.raise_for_status()
                return response.json()

        try:
            raw_data = await naver_cb.call(_fetch)
            return self._parse_news_response(raw_data)
        except Exception as e:
            logger.error("naver_news_search_error", keyword=keyword, error=str(e))
            return []

    async def get_search_trend(
        self,
        keywords: list[str],
        date_from: date | None = None,
        date_to: date | None = None,
        time_unit: str = "week",
    ) -> list[dict[str, Any]]:
        """네이버 데이터랩 검색어 트렌드 조회

        Args:
            keywords: 검색어 목록 (최대 5개)
            date_from: 시작일
            date_to: 종료일
            time_unit: 시간 단위 (date, week, month)

        Returns:
            검색어별 트렌드 데이터
        """
        if date_to is None:
            date_to = date.today()
        if date_from is None:
            date_from = date_to - timedelta(days=30)

        # 키워드 그룹 구성 (최대 5개)
        keyword_groups = [
            {"groupName": kw, "keywords": [kw]}
            for kw in keywords[:5]
        ]

        body = {
            "startDate": date_from.strftime("%Y-%m-%d"),
            "endDate": date_to.strftime("%Y-%m-%d"),
            "timeUnit": time_unit,
            "keywordGroups": keyword_groups,
        }

        async def _fetch():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    NAVER_DATALAB_URL,
                    json=body,
                    headers=self._headers,
                )
                response.raise_for_status()
                return response.json()

        try:
            raw_data = await naver_cb.call(_fetch)
            return self._parse_trend_response(raw_data)
        except Exception as e:
            logger.error("naver_trend_error", keywords=keywords, error=str(e))
            return []

    async def health_check(self) -> bool:
        """네이버 API 상태 확인"""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(3.0)) as client:
                response = await client.get(
                    NAVER_SEARCH_URL,
                    params={"query": "테스트", "display": 1},
                    headers=self._headers,
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning("naver_health_check_failed", error=str(e))
            return False

    def _parse_news_response(self, raw_data: dict) -> list[dict[str, Any]]:
        """네이버 뉴스 검색 응답 파싱"""
        results = []
        items = raw_data.get("items", [])

        for item in items:
            # HTML 태그 제거
            title = self._strip_html(item.get("title", ""))
            description = self._strip_html(item.get("description", ""))

            results.append({
                "title": title,
                "url": item.get("originallink", item.get("link", "")),
                "description": description,
                "published_at": item.get("pubDate", ""),
                "source": "네이버뉴스",
            })

        return results

    def _parse_trend_response(self, raw_data: dict) -> list[dict[str, Any]]:
        """네이버 데이터랩 응답 파싱"""
        results = []
        trend_results = raw_data.get("results", [])

        for result in trend_results:
            keyword = result.get("title", "")
            data_points = result.get("data", [])

            for point in data_points:
                results.append({
                    "keyword": keyword,
                    "period": point.get("period", ""),
                    "ratio": point.get("ratio", 0),
                })

        return results

    @staticmethod
    def _strip_html(text: str) -> str:
        """HTML 태그 제거"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).replace("&quot;", '"').replace("&amp;", "&")
