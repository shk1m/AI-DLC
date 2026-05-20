"""뉴스 API 라우터 (/api/news)

엔드포인트:
- GET /api/news/search - 뉴스 검색
- GET /api/news/trends/{category} - 검색어 트렌드
- POST /api/news/crawl - 크롤링 트리거 (관리용)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.news import NewsArticleResponse, NewsSearchParams, TrendKeyword
from app.services.news_service import NewsService

router = APIRouter()


@router.get("/search", response_model=list[NewsArticleResponse])
async def search_news(
    keyword: str = Query(max_length=50, description="검색 키워드"),
    date_from: str | None = Query(default=None, description="시작일 (YYYY-MM-DD)"),
    date_to: str | None = Query(default=None, description="종료일 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """뉴스 검색

    식자재 관련 뉴스를 키워드로 검색합니다.
    """
    service = NewsService(db)
    return await service.search_news(keyword, date_from, date_to)


@router.get("/trends/{category}", response_model=list[TrendKeyword])
async def get_trend_keywords(
    category: str,
    db: AsyncSession = Depends(get_db),
):
    """검색어 트렌드 조회 (네이버 데이터랩)

    카테고리별 식자재 관련 검색어 트렌드를 조회합니다.
    """
    service = NewsService(db)
    return await service.get_trend_keywords(category)


@router.post("/crawl", response_model=list[NewsArticleResponse])
async def trigger_crawl(
    db: AsyncSession = Depends(get_db),
):
    """정부 보도자료 크롤링 트리거 (관리용)

    농림축산식품부, 해양수산부 보도자료를 수동으로 크롤링합니다.
    """
    service = NewsService(db)
    return await service.crawl_government_press()
