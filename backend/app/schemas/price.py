"""Pydantic 스키마: 가격 도메인 (SECURITY-05: 입력 검증)"""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.food_item import CategoryEnum


class PriceQueryParams(BaseModel):
    """시세 조회 쿼리 파라미터 (BR-08 입력 검증)"""

    category: CategoryEnum
    subcategory: str | None = None
    period: Literal["1w", "1m", "3m", "6m", "1y"] = "1m"

    @field_validator("subcategory")
    @classmethod
    def validate_subcategory(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 50:
            raise ValueError("subcategory는 50자 이내여야 합니다")
        return v


class PriceItem(BaseModel):
    """품목별 현재 시세"""

    item_id: UUID
    name: str
    category: CategoryEnum
    subcategory: str
    unit: str
    wholesale_price: float = Field(gt=0, description="도매가")
    retail_price: float = Field(gt=0, description="소매가")
    price_gap: float = Field(description="갭 비율 (%)")
    change_rate: float = Field(default=0.0, description="전일 대비 변동률 (%)")
    date: date
    source: str

    model_config = {"from_attributes": True}


class PriceTimePoint(BaseModel):
    """시계열 가격 데이터 포인트"""

    date: date
    wholesale_price: float
    retail_price: float


class SpikeEventResponse(BaseModel):
    """Spike 이벤트 응답"""

    id: UUID
    date: date
    spike_type: str  # "급등" | "급락"
    magnitude: float = Field(description="변동 크기 (%)")
    baseline_price: float
    spike_price: float
    news_articles: list["NewsArticleBrief"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class NewsArticleBrief(BaseModel):
    """뉴스 간략 정보 (Spike 매핑용)"""

    title: str
    url: str
    published_at: datetime


class PriceTimeSeries(BaseModel):
    """시세 추이 응답"""

    item_id: UUID
    item_name: str
    period: str
    time_series: list[PriceTimePoint]
    spikes: list[SpikeEventResponse] = Field(default_factory=list)


class PriceGapInfo(BaseModel):
    """도매/소매 갭 분석"""

    item_id: UUID
    item_name: str
    wholesale_price: float
    retail_price: float
    gap_amount: float = Field(description="갭 금액 (원)")
    gap_rate: float = Field(description="갭 비율 (%)")
    date: date


class CategoryPriceSummary(BaseModel):
    """카테고리 요약 통계"""

    category: CategoryEnum
    total_items: int
    avg_wholesale_price: float
    avg_retail_price: float
    avg_gap_rate: float
    top_surge_items: list[str] = Field(default_factory=list)
    top_drop_items: list[str] = Field(default_factory=list)


# Forward reference 해결
SpikeEventResponse.model_rebuild()
