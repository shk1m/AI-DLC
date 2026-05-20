"""
News domain schemas (Pydantic v2).

도메인 정의: domain-entities.md §3
검증 규칙: BR-08 (Input Validation)
NFR: SECURITY-05 (입력 검증), PBT-08 (round-trip)

> 주의: NewsService(BE-05)는 Unit 2 영역. 본 스키마는 Unit 4 크롤러/저장소가 사용하는 임시 모델.
> 16:30 통합 테스트 싱크포인트에서 Unit 2와 통합 합의.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from urllib.parse import urlparse
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class NewsSourceEnum(str, Enum):
    """뉴스 출처. domain-entities.md §3과 일치."""

    NAVER = "NAVER"
    MAFRA = "MAFRA"  # 농림축산식품부
    MOF = "MOF"  # 해양수산부


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    """간단한 HTML 태그 제거 + 공백 정규화 (XSS 보호 + 가독성)."""
    return _WHITESPACE_RE.sub(" ", _HTML_TAG_RE.sub("", text)).strip()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class NewsArticle(BaseModel):
    """
    뉴스 기사 도메인 객체.

    Validation:
    - title: ≤500자, HTML 태그 제거
    - url: 절대 URL, HTTP/HTTPS만 허용
    - keywords: 각 ≤50자 (BR-08-7)
    - published_at: timezone-aware datetime
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        ser_json_timedelta="iso8601",
    )

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(min_length=1, max_length=500)
    url: HttpUrl
    source: NewsSourceEnum
    published_at: datetime
    keywords: list[str] = Field(default_factory=list, max_length=20)
    related_items: list[UUID] = Field(default_factory=list, max_length=20)
    summary: str = Field(default="", max_length=2000)
    body: str | None = Field(default=None, max_length=50_000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=__import__("datetime").timezone.utc))

    # ---- field validators ----
    @field_validator("title", "summary", mode="before")
    @classmethod
    def _strip_html_tags(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return strip_html(str(v))

    @field_validator("keywords", mode="before")
    @classmethod
    def _normalize_keywords(cls, v: object) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            v = [v]
        if not isinstance(v, list):
            raise ValueError("keywords must be a list of strings")
        out: list[str] = []
        seen: set[str] = set()
        for k in v:
            if not isinstance(k, str):
                raise ValueError("each keyword must be a string")
            stripped = k.strip()
            if not stripped:
                continue
            if len(stripped) > 50:
                raise ValueError(f"keyword exceeds 50 chars: {stripped[:20]}...")
            if stripped.lower() not in seen:
                seen.add(stripped.lower())
                out.append(stripped)
        return out

    @field_validator("url")
    @classmethod
    def _validate_url_scheme(cls, v: HttpUrl) -> HttpUrl:
        scheme = urlparse(str(v)).scheme.lower()
        if scheme not in {"http", "https"}:
            raise ValueError(f"only http(s) URLs allowed, got: {scheme}")
        return v

    @field_validator("published_at")
    @classmethod
    def _require_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("published_at must be timezone-aware")
        return v

    @model_validator(mode="after")
    def _validate_consistency(self) -> NewsArticle:
        """summary가 비었으면 title 일부로 채움 (BR-05-5 컨설턴트 응답 위함)."""
        if not self.summary:
            self.summary = self.title[:200]
        return self


class NewsArticleCreate(BaseModel):
    """크롤러/외부 API에서 받은 raw 데이터 → DB 저장 전 변환용."""

    model_config = ConfigDict(extra="ignore")

    title: str
    url: str
    source: NewsSourceEnum
    published_at: datetime
    keywords: list[str] = Field(default_factory=list)
    summary: str = ""
    body: str | None = None

    def to_article(self, related_items: list[UUID] | None = None) -> NewsArticle:
        """관련 식자재 매핑 후 NewsArticle 생성."""
        return NewsArticle(
            title=self.title,
            url=self.url,  # type: ignore[arg-type]
            source=self.source,
            published_at=self.published_at,
            keywords=self.keywords,
            summary=self.summary,
            body=self.body,
            related_items=related_items or [],
        )


class NewsSearchQuery(BaseModel):
    """뉴스 검색 요청 (BR-08-6/7)."""

    model_config = ConfigDict(extra="forbid")

    keyword: str = Field(min_length=1, max_length=50)
    date_from: datetime | None = None
    date_to: datetime | None = None
    limit: int = Field(default=10, ge=1, le=100)

    @model_validator(mode="after")
    def _check_date_range(self) -> NewsSearchQuery:
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be <= date_to")
        return self
