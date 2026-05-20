"""Tests for app.adapters.crawler (EXT-04) — mock mode only."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from app.adapters.crawler import (
    MafraCrawler,
    MofCrawler,
    NaverNewsCrawler,
    NewsCrawlerService,
    extract_food_keywords,
)
from app.schemas.news import NewsArticle


class TestExtractFoodKeywords:
    def test_finds_known_keywords(self) -> None:
        kws = extract_food_keywords("배추 가격 급등 소식, 상추도 올랐다")
        assert "배추" in kws
        assert "상추" in kws
        assert "가격" in kws

    def test_empty_text(self) -> None:
        assert extract_food_keywords("") == []

    def test_no_match(self) -> None:
        assert extract_food_keywords("오늘 날씨가 맑습니다") == []

    def test_deduplication_implicit(self) -> None:
        kws = extract_food_keywords("고등어 고등어 고등어")
        assert kws.count("고등어") == 1


class TestNaverNewsCrawlerMock:
    async def test_mock_mode_returns_fallback_list(self) -> None:
        # USE_MOCK=true (conftest autouse)
        crawler = NaverNewsCrawler()
        result = await crawler.crawl(limit=5)
        # 샘플 파일 없으면 빈 리스트, 있으면 NewsArticle 목록
        assert isinstance(result, list)
        for a in result:
            assert isinstance(a, NewsArticle)

    async def test_mock_multiple_keywords(self) -> None:
        crawler = NaverNewsCrawler()
        result = await crawler.crawl_multiple_keywords(
            keywords=["고등어", "배추"], limit_per_kw=5
        )
        assert isinstance(result, list)


class TestMafraCrawlerMock:
    async def test_mock_mode_returns_fallback_list(self) -> None:
        crawler = MafraCrawler()
        result = await crawler.crawl()
        assert isinstance(result, list)

    async def test_html_parsing_with_mock_html(self) -> None:
        from app.adapters.crawler import MafraCrawler
        import httpx
        crawler = MafraCrawler()
        mock_html = """
        <table><tbody>
          <tr><td><a href="/news/123">배추 가격 안정세 유지</a></td></tr>
          <tr><td><a href="/news/124">고등어 수산물 급등</a></td></tr>
          <tr><td><a href="/news/125">오늘의 날씨</a></td></tr>
        </tbody></table>
        """
        client = httpx.AsyncClient()
        result = crawler._parse_listing(mock_html, "https://mafra.go.kr", 10, client)
        await client.aclose()
        assert len(result) >= 1
        titles = [a.title for a in result]
        assert any("배추" in t or "고등어" in t for t in titles)


class TestMofCrawlerMock:
    async def test_mock_mode(self) -> None:
        crawler = MofCrawler()
        result = await crawler.crawl()
        assert isinstance(result, list)


class TestNewsCrawlerService:
    async def test_crawl_all_deduplicates(self) -> None:
        svc = NewsCrawlerService()
        result = await svc.crawl_all(upload_to_s3=False)
        urls = [str(a.url) for a in result]
        assert len(urls) == len(set(urls)), "중복 URL 존재"

    async def test_crawl_all_with_s3_upload(self, tmp_path: Path) -> None:
        """S3 mock 모드로 업로드까지 검증."""
        from app.adapters.s3_client import LocalMockS3Client, reset_s3_client
        import app.adapters.s3_client as s3_mod

        mock_s3 = LocalMockS3Client(bucket="test-bucket", root=tmp_path)
        s3_mod._default_client = mock_s3
        try:
            svc = NewsCrawlerService()
            svc._s3 = mock_s3
            result = await svc.crawl_all(upload_to_s3=True)
            assert isinstance(result, list)
            # 업로드된 파일 확인
            if result:
                keys = await mock_s3.list_objects(prefix="news/")
                assert len(keys) > 0
        finally:
            reset_s3_client()
            s3_mod._default_client = None


# PBT: invariant — 반환된 모든 NewsArticle은 Pydantic valid
@pytest.mark.pbt
class TestCrawlerPBT:
    @given(
        titles=st.lists(
            st.text(min_size=5, max_size=100).filter(lambda s: s.strip() != ""),
            min_size=1,
            max_size=10,
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=15)
    def test_extract_food_keywords_returns_subset(self, titles: list[str]) -> None:
        from app.adapters.crawler import FOOD_KEYWORDS
        for title in titles:
            kws = extract_food_keywords(title)
            for k in kws:
                assert k in FOOD_KEYWORDS
