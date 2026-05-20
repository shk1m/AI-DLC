"""
Tests for app.schemas.news (PBT-08 round-trip).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st
from pydantic import ValidationError

from app.schemas.news import (
    NewsArticle,
    NewsArticleCreate,
    NewsSearchQuery,
    NewsSourceEnum,
    strip_html,
)


def _utc(year: int = 2026, month: int = 5, day: int = 20) -> datetime:
    return datetime(year, month, day, 12, 0, tzinfo=timezone.utc)


class TestStripHtml:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("<b>hello</b>", "hello"),
            ("<a href='x'>link</a>", "link"),
            ("plain text", "plain text"),
            ("multi   spaces", "multi spaces"),
            ("<script>alert(1)</script>safe", "alert(1)safe"),
        ],
    )
    def test_strip_html(self, raw: str, expected: str) -> None:
        assert strip_html(raw) == expected


class TestNewsArticle:
    def _valid_payload(self) -> dict:
        return {
            "title": "고등어 가격 급등 — 어획량 감소",
            "url": "https://example.com/news/1",
            "source": NewsSourceEnum.NAVER,
            "published_at": _utc(),
            "keywords": ["고등어", "수산물", "가격"],
        }

    def test_valid_creation(self) -> None:
        a = NewsArticle(**self._valid_payload())
        assert a.title == "고등어 가격 급등 — 어획량 감소"
        assert a.summary  # auto-filled from title
        assert "고등어" in a.keywords

    def test_html_stripped_in_title(self) -> None:
        p = self._valid_payload()
        p["title"] = "<b>고등어</b> <em>가격</em>"
        a = NewsArticle(**p)
        assert "<" not in a.title
        assert "고등어" in a.title

    def test_url_must_be_http(self) -> None:
        p = self._valid_payload()
        p["url"] = "ftp://example.com/x"
        with pytest.raises(ValidationError):
            NewsArticle(**p)

    def test_naive_datetime_rejected(self) -> None:
        p = self._valid_payload()
        p["published_at"] = datetime(2026, 5, 20, 12, 0)  # no tz
        with pytest.raises(ValidationError):
            NewsArticle(**p)

    def test_keyword_too_long_rejected(self) -> None:
        p = self._valid_payload()
        p["keywords"] = ["x" * 51]
        with pytest.raises(ValidationError):
            NewsArticle(**p)

    def test_keyword_dedup(self) -> None:
        p = self._valid_payload()
        p["keywords"] = ["고등어", "고등어", "  고등어  ", "수산물"]
        a = NewsArticle(**p)
        assert a.keywords == ["고등어", "수산물"]

    def test_extra_fields_forbidden(self) -> None:
        p = self._valid_payload()
        p["unknown"] = "value"
        with pytest.raises(ValidationError):
            NewsArticle(**p)

    def test_title_too_long_rejected(self) -> None:
        p = self._valid_payload()
        p["title"] = "x" * 501
        with pytest.raises(ValidationError):
            NewsArticle(**p)


class TestNewsArticleCreate:
    def test_to_article(self) -> None:
        c = NewsArticleCreate(
            title="배추 흉작",
            url="https://news.example.com/1",
            source=NewsSourceEnum.MAFRA,
            published_at=_utc(),
            keywords=["배추"],
        )
        a = c.to_article()
        assert isinstance(a, NewsArticle)
        assert a.title == "배추 흉작"


class TestNewsSearchQuery:
    def test_default_limit(self) -> None:
        q = NewsSearchQuery(keyword="고등어")
        assert q.limit == 10

    def test_invalid_date_range(self) -> None:
        with pytest.raises(ValidationError):
            NewsSearchQuery(
                keyword="x",
                date_from=_utc() + timedelta(days=1),
                date_to=_utc(),
            )

    def test_keyword_max_length(self) -> None:
        with pytest.raises(ValidationError):
            NewsSearchQuery(keyword="x" * 51)


# ---------------------------------------------------------------------------
# PBT-08: round-trip serialization
# ---------------------------------------------------------------------------
@pytest.mark.pbt
class TestNewsArticlePBT:
    @given(
        title=st.text(min_size=1, max_size=200).filter(lambda s: s.strip() != ""),
        keywords=st.lists(
            st.text(min_size=1, max_size=30).filter(lambda s: s.strip() != ""),
            max_size=10,
            unique_by=lambda s: s.lower().strip(),
        ),
        offset_min=st.integers(min_value=-720, max_value=720),
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
    def test_round_trip_dict(
        self, title: str, keywords: list[str], offset_min: int
    ) -> None:
        published = datetime.now(tz=timezone.utc) + timedelta(minutes=offset_min)
        try:
            article = NewsArticle(
                title=title,
                url="https://example.com/n",  # type: ignore[arg-type]
                source=NewsSourceEnum.NAVER,
                published_at=published,
                keywords=keywords,
            )
        except ValidationError:
            # 입력이 유효하지 않은 경우는 round-trip 대상 아님
            return

        dumped = article.model_dump(mode="json")
        restored = NewsArticle.model_validate(dumped)
        assert restored.title == article.title
        assert restored.keywords == article.keywords
        assert restored.source == article.source
        assert restored.published_at == article.published_at

    @given(
        title=st.text(min_size=1, max_size=200).filter(lambda s: s.strip() != ""),
        keywords=st.lists(
            st.text(min_size=1, max_size=30).filter(lambda s: s.strip() != ""),
            max_size=5,
        ),
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
    def test_round_trip_json(self, title: str, keywords: list[str]) -> None:
        try:
            a = NewsArticle(
                title=title,
                url="https://example.com/n",  # type: ignore[arg-type]
                source=NewsSourceEnum.NAVER,
                published_at=_utc(),
                keywords=keywords,
            )
        except ValidationError:
            return

        json_str = a.model_dump_json()
        b = NewsArticle.model_validate_json(json_str)
        assert b.title == a.title
        assert b.keywords == a.keywords
