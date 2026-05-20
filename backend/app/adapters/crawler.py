"""
News Crawler — EXT-04.

크롤 대상:
  - 네이버 뉴스 API (Naver Open API, search/news.json)
  - 농림축산식품부 보도자료 (mafra.go.kr)
  - 해양수산부 보도자료 (mof.go.kr)

NFR: AVAIL-03, BR-06-1~5, SECURITY-05
Fallback: 크롤링 실패 시 data/news/samples/ 의 로컬 샘플 JSON 반환.
"""

from __future__ import annotations

import json
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.adapters.s3_client import get_s3_client
from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.news import NewsArticle, NewsArticleCreate, NewsSourceEnum

logger = get_logger(__name__)

# 식자재 키워드 — BR-06-3 (최소 1개 포함된 기사만 저장)
FOOD_KEYWORDS: list[str] = [
    # 채소/농산물
    "배추", "무", "상추", "고추", "마늘", "양파", "대파", "시금치", "감자", "고구마",
    # 수산물
    "고등어", "삼치", "갈치", "전복", "새우", "굴", "미역", "오징어",
    # 축산물
    "돼지고기", "삼겹살", "닭고기", "한우", "소고기", "계란",
    # 과일
    "사과", "배", "딸기", "수박", "토마토",
    # 가공/원자재
    "식용유", "설탕", "밀가루", "간장", "된장",
    # 이슈
    "시세", "가격", "급등", "급락", "흉작", "풍작", "수입", "물가",
]


def extract_food_keywords(text: str) -> list[str]:
    """텍스트에서 식자재 키워드 추출 (BR-06-3)."""
    return [kw for kw in FOOD_KEYWORDS if kw in text]


def _is_valid_https_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


# ---------------------------------------------------------------------------
# Retry helper (BR-06-4 + NFR Design 1.2)
# ---------------------------------------------------------------------------
async def _fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    params: dict | None = None,
    max_retries: int = 3,
    timeout: float = 15.0,
) -> httpx.Response:
    """지수 백오프 + jitter 재시도 (NFR Design 1.2)."""
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            resp = await client.request(
                method, url, headers=headers or {}, params=params or {}, timeout=timeout
            )
            resp.raise_for_status()
            return resp
        except Exception as exc:
            last_exc = exc
            wait = (2**attempt) + random.uniform(0, 0.5)  # 1s/2s/4s + jitter
            logger.warning(
                "crawler_retry",
                url=url,
                attempt=attempt + 1,
                wait=round(wait, 2),
                error_type=type(exc).__name__,
            )
            time.sleep(wait)
    raise RuntimeError(f"Max retries exceeded for {url}") from last_exc


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------
class BaseCrawler(ABC):
    """크롤러 인터페이스."""

    source: NewsSourceEnum

    @abstractmethod
    async def crawl(self, limit: int = 20) -> list[NewsArticle]:
        """뉴스 목록 크롤링. 실패 시 빈 리스트 반환 (circuit breaker 상위에서 처리)."""
        ...

    def _sample_fallback(self, name: str) -> list[NewsArticle]:
        """로컬 샘플 JSON fallback (BR-06-5)."""
        samples_dir = Path(__file__).resolve().parents[3] / "data" / "news" / "samples"
        path = samples_dir / f"{name}.json"
        if not path.exists():
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return [
                NewsArticleCreate(**item).to_article()
                for item in raw
                if isinstance(item, dict)
            ]
        except Exception as exc:  # noqa: BLE001
            logger.error("crawler_fallback_error", file=str(path), error_type=type(exc).__name__)
            return []


# ---------------------------------------------------------------------------
# Naver News API Crawler (API 호출)
# ---------------------------------------------------------------------------
class NaverNewsCrawler(BaseCrawler):
    """
    네이버 검색 API — 뉴스 검색 (search/news.json).
    하루 25,000회 제한.
    """

    source = NewsSourceEnum.NAVER

    def __init__(self) -> None:
        self._settings = get_settings()

    async def crawl(self, limit: int = 20, keyword: str = "농산물 시세") -> list[NewsArticle]:  # type: ignore[override]
        if self._settings.is_mock or not self._settings.has_naver_credentials:
            logger.info("naver_crawler_mock", keyword=keyword)
            return self._sample_fallback("naver_news")

        articles: list[NewsArticle] = []
        async with httpx.AsyncClient() as client:
            try:
                resp = await _fetch_with_retry(
                    client,
                    self._settings.naver_news_api_url,
                    headers=self._settings.naver_auth_headers(),
                    params={"query": keyword, "display": min(limit, 100), "sort": "date"},
                    max_retries=self._settings.crawler_max_retries,
                    timeout=self._settings.crawler_timeout_seconds,
                )
                data: dict[str, Any] = resp.json()
            except Exception as exc:  # noqa: BLE001
                logger.error("naver_crawler_failed", error_type=type(exc).__name__)
                return self._sample_fallback("naver_news")

        seen_urls: set[str] = set()
        for item in data.get("items", []):
            raw_url = item.get("link", "") or item.get("originallink", "")
            if not _is_valid_https_url(raw_url) or raw_url in seen_urls:
                continue
            seen_urls.add(raw_url)

            title = item.get("title", "")
            description = item.get("description", "")
            combined = title + " " + description
            keywords = extract_food_keywords(combined)

            if not keywords:  # BR-06-3
                continue

            try:
                pub_str = item.get("pubDate", "")
                published = _parse_rfc822(pub_str) if pub_str else datetime.now(tz=timezone.utc)
                create = NewsArticleCreate(
                    title=title,
                    url=raw_url,
                    source=self.source,
                    published_at=published,
                    keywords=keywords,
                    summary=description[:500],
                )
                articles.append(create.to_article())
            except Exception as exc:  # noqa: BLE001
                logger.warning("naver_article_parse_error", error_type=type(exc).__name__)
                continue

        logger.info("naver_crawl_complete", count=len(articles), keyword=keyword)
        return articles

    async def crawl_multiple_keywords(
        self, keywords: list[str] | None = None, limit_per_kw: int = 10
    ) -> list[NewsArticle]:
        """여러 키워드 순차 크롤링. 중복 URL 제거."""
        kw_list = keywords or ["농산물 시세", "수산물 가격", "축산물 도매", "식자재 급등"]
        seen: set[str] = set()
        results: list[NewsArticle] = []
        for kw in kw_list:
            items = await self.crawl(limit=limit_per_kw, keyword=kw)
            for a in items:
                url_str = str(a.url)
                if url_str not in seen:
                    seen.add(url_str)
                    results.append(a)
        return results


# ---------------------------------------------------------------------------
# Government Press Release Crawlers
# ---------------------------------------------------------------------------
class MafraCrawler(BaseCrawler):
    """농림축산식품부 보도자료 크롤러 (mafra.go.kr)."""

    source = NewsSourceEnum.MAFRA

    async def crawl(self, limit: int = 10) -> list[NewsArticle]:
        settings = get_settings()
        if settings.is_mock:
            return self._sample_fallback("mafra_news")

        base_url = settings.mafra_base_url
        list_url = f"{base_url}/mafra.go.kr/bbs/mafra/71/artclList.do"

        async with httpx.AsyncClient(
            headers={"User-Agent": settings.crawler_user_agent},
            follow_redirects=True,
        ) as client:
            try:
                resp = await _fetch_with_retry(
                    client, list_url,
                    max_retries=settings.crawler_max_retries,
                    timeout=settings.crawler_timeout_seconds,
                )
                return self._parse_listing(resp.text, base_url, limit, client)
            except Exception as exc:  # noqa: BLE001
                logger.error("mafra_crawl_failed", error_type=type(exc).__name__)
                return self._sample_fallback("mafra_news")

    def _parse_listing(
        self,
        html: str,
        base_url: str,
        limit: int,
        _client: httpx.AsyncClient,
    ) -> list[NewsArticle]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[NewsArticle] = []
        items = soup.select("table tbody tr, ul.bbs-list li")[:limit]
        for item in items:
            a_tag = item.find("a")
            if not a_tag:
                continue
            title = a_tag.get_text(strip=True)
            href = a_tag.get("href", "")
            full_url = urljoin(base_url, href) if href else base_url

            kws = extract_food_keywords(title)
            if not kws:
                continue
            try:
                create = NewsArticleCreate(
                    title=title,
                    url=full_url,
                    source=self.source,
                    published_at=datetime.now(tz=timezone.utc),
                    keywords=kws,
                )
                results.append(create.to_article())
            except Exception:  # noqa: BLE001
                continue
        logger.info("mafra_crawl_complete", count=len(results))
        return results


class MofCrawler(BaseCrawler):
    """해양수산부 보도자료 크롤러 (mof.go.kr)."""

    source = NewsSourceEnum.MOF

    async def crawl(self, limit: int = 10) -> list[NewsArticle]:
        settings = get_settings()
        if settings.is_mock:
            return self._sample_fallback("mof_news")

        base_url = settings.mof_base_url
        list_url = f"{base_url}/mof.go.kr/synap/skin/doc.html"

        async with httpx.AsyncClient(
            headers={"User-Agent": settings.crawler_user_agent},
            follow_redirects=True,
        ) as client:
            try:
                resp = await _fetch_with_retry(
                    client, list_url,
                    max_retries=settings.crawler_max_retries,
                    timeout=settings.crawler_timeout_seconds,
                )
                return self._parse_listing(resp.text, base_url, limit)
            except Exception as exc:  # noqa: BLE001
                logger.error("mof_crawl_failed", error_type=type(exc).__name__)
                return self._sample_fallback("mof_news")

    def _parse_listing(self, html: str, base_url: str, limit: int) -> list[NewsArticle]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[NewsArticle] = []
        for a_tag in soup.find_all("a", href=True)[:limit * 3]:
            title = a_tag.get_text(strip=True)
            href = a_tag["href"]
            if not title or len(title) < 5:
                continue
            kws = extract_food_keywords(title)
            if not kws:
                continue
            full_url = urljoin(base_url, href)
            try:
                create = NewsArticleCreate(
                    title=title,
                    url=full_url,
                    source=self.source,
                    published_at=datetime.now(tz=timezone.utc),
                    keywords=kws,
                )
                results.append(create.to_article())
                if len(results) >= limit:
                    break
            except Exception:  # noqa: BLE001
                continue
        logger.info("mof_crawl_complete", count=len(results))
        return results


# ---------------------------------------------------------------------------
# Composite crawler — NewsService에서 호출
# ---------------------------------------------------------------------------
class NewsCrawlerService:
    """
    Unit 2의 NewsService(BE-05)에서 호출하는 통합 크롤러.
    Unit 4 담당 컴포넌트 (EXT-04).
    """

    def __init__(self) -> None:
        self._naver = NaverNewsCrawler()
        self._mafra = MafraCrawler()
        self._mof = MofCrawler()
        self._s3 = get_s3_client()

    async def crawl_all(self, upload_to_s3: bool = True) -> list[NewsArticle]:
        """전체 소스 크롤링 + S3 업로드 (RAG KB 소스)."""
        naver = await self._naver.crawl_multiple_keywords()
        mafra = await self._mafra.crawl()
        mof = await self._mof.crawl()
        all_articles = naver + mafra + mof

        # 중복 URL 제거 (BR-06-1)
        seen: set[str] = set()
        unique: list[NewsArticle] = []
        for a in all_articles:
            url_str = str(a.url)
            if url_str not in seen:
                seen.add(url_str)
                unique.append(a)

        if upload_to_s3 and unique:
            await self._upload_to_s3(unique)

        logger.info("crawl_all_complete", total=len(unique))
        return unique

    async def _upload_to_s3(self, articles: list[NewsArticle]) -> None:
        """크롤링 결과를 S3에 저장 → Bedrock KB 자동 동기화."""
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        for article in articles:
            key = f"news/{today}/{article.id}.json"
            try:
                await self._s3.upload_json(
                    key,
                    article.model_dump(mode="json"),
                    metadata={"source": article.source.value, "date": today},
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("s3_news_upload_failed", key=key, error_type=type(exc).__name__)


# ---------------------------------------------------------------------------
# RFC 822 date parser helper
# ---------------------------------------------------------------------------
def _parse_rfc822(date_str: str) -> datetime:
    """네이버 API pubDate (RFC 822) 파싱. 실패 시 현재 UTC."""
    from email.utils import parsedate_to_datetime
    try:
        return parsedate_to_datetime(date_str).astimezone(timezone.utc)
    except Exception:  # noqa: BLE001
        return datetime.now(tz=timezone.utc)
