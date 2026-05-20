"""시세 API 라우터 (/api/prices)

엔드포인트:
- GET /api/prices/{category} - 카테고리별 현재 시세
- GET /api/prices/{item_id}/history - 시세 추이
- GET /api/prices/{item_id}/spikes - Spike 감지
- GET /api/prices/{item_id}/gap - Gap 분석
- GET /api/prices/{category}/summary - 카테고리 요약
"""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.price import (
    CategoryPriceSummary,
    PriceGapInfo,
    PriceItem,
    PriceTimeSeries,
    SpikeEventResponse,
)
from app.services.price_service import PriceService

router = APIRouter()


@router.get("/{category}", response_model=list[PriceItem])
async def get_current_prices(
    category: str,
    subcategory: Optional[str] = Query(default=None, max_length=50),
    db: AsyncSession = Depends(get_db),
):
    """카테고리별 현재 시세 조회

    - **category**: 대분류 (채소류, 수산물, 축산류, 과일류, 가공식품, 구황작물)
    - **subcategory**: 소분류 (선택)
    """
    service = PriceService(db)
    return await service.get_current_prices(category, subcategory)


@router.get("/{item_id}/history", response_model=PriceTimeSeries)
async def get_price_history(
    item_id: str,
    period: Literal["1w", "1m", "3m", "6m", "1y"] = "1m",
    db: AsyncSession = Depends(get_db),
):
    """품목별 시세 추이 조회 (차트 데이터)

    - **item_id**: 품목 UUID
    - **period**: 조회 기간 (1w, 1m, 3m, 6m, 1y)
    """
    service = PriceService(db)
    try:
        return await service.get_price_history(item_id, period)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{item_id}/spikes", response_model=list[SpikeEventResponse])
async def get_spikes(
    item_id: str,
    period: Literal["1w", "1m", "3m", "6m", "1y"] = "3m",
    db: AsyncSession = Depends(get_db),
):
    """품목별 Spike(이상치) 감지

    - **item_id**: 품목 UUID
    - **period**: 분석 기간
    """
    service = PriceService(db)
    return await service.detect_spikes(item_id, period)


@router.get("/{item_id}/gap", response_model=PriceGapInfo)
async def get_price_gap(
    item_id: str,
    db: AsyncSession = Depends(get_db),
):
    """도매/소매 Gap 분석

    - **item_id**: 품목 UUID
    """
    service = PriceService(db)
    try:
        return await service.get_price_gap(item_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{category}/summary", response_model=CategoryPriceSummary)
async def get_category_summary(
    category: str,
    db: AsyncSession = Depends(get_db),
):
    """카테고리 요약 통계

    - **category**: 대분류 카테고리
    """
    service = PriceService(db)
    return await service.get_category_summary(category)
