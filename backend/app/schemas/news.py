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
