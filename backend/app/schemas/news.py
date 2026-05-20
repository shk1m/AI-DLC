"""Pydantic 스키마: 뉴스 도메인 (SECURITY-05: 입력 검증)"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class NewsSearchParams(BaseModel):
    """뉴스 검색 파라미터 (BR-08 검증)"""

    keyword: str = Field(max_length=50, description="검색 키워드")
    date_from: str | None = Field(default=None, description="시작일 (YYYY-MM-DD)")
    date_to: str | None = Field(default=None, description="종료일 (YYYY-MM-DD)")

    @field_validator("keyword")
    @classmethod
    def sanitize_keyword(cls, v: str) -> str:
        """특수문자 이스케이프 (BR-08-7)"""
        import re
        # 기본 특수문자 제거 (알파벳, 한글, 숫자, 공백만 허용)
        sanitized = re.sub(r'[^\w\s가-힣]', '', v)
        return sanitized.strip()


class NewsArticleResponse(BaseModel):
    """뉴스 기사 응답"""

    id: UUID
    title: str
    url: str
    source: str
    published_at: datetime
    keywords: list[str] = Field(default_factory=list)
    related_items: list[str] = Field(default_factory=list)
    summary: str | None = None

    model_config = {"from_attributes": True}


class TrendKeyword(BaseModel):
    """트렌드 키워드"""

    keyword: str
    ratio: float = Field(description="검색 비율 (0~100)")
    period: str
    category: str | None = None


# --- Unit 4 Crawler 호환 스키마 ---

from enum import Enum
from typing import Optional


class NewsSourceEnum(str, Enum):
    """뉴스 출처 열거형"""
    NAVER = "naver"
    MAFRA = "mafra"
    MOF = "mof"


class NewsArticleCreate(BaseModel):
    """뉴스 기사 생성 스키마 (크롤러 → DB 적재용)"""
    title: str = Field(max_length=500)
    url: str = Field(max_length=2000)
    source: NewsSourceEnum
    published_at: datetime
    keywords: list[str] = Field(default_factory=list)
    related_items: list[str] = Field(default_factory=list)
    summary: Optional[str] = None


class NewsArticle(BaseModel):
    """뉴스 기사 (DB 모델 호환)"""
    id: Optional[UUID] = None
    title: str = Field(max_length=500)
    url: str = Field(max_length=2000)
    source: NewsSourceEnum
    published_at: datetime
    keywords: list[str] = Field(default_factory=list)
    related_items: list[str] = Field(default_factory=list)
    summary: Optional[str] = None

    model_config = {"from_attributes": True}


# --- Unit 4 Test 호환 alias/함수 ---

import re as _re


def strip_html(text: str) -> str:
    """HTML 태그 제거 유틸리티 (XSS 방지)"""
    return _re.sub(r'<[^>]+>', '', text).strip()


# Alias for backward compatibility with Unit 4 tests
NewsSearchQuery = NewsSearchParams
