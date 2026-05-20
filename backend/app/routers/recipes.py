"""레시피 API 라우터 (/api/recipes)

엔드포인트:
- POST /api/recipes/simulate - 원가 시뮬레이션
- POST /api/recipes/suggest - AI 메뉴 추천
- POST /api/recipes/compare - 메뉴 비교
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.recipe import (
    CostSimulation,
    CostSimulationRequest,
    MenuComparisonResponse,
    MenuSuggestion,
)
from app.services.recipe_service import RecipeService

router = APIRouter()


@router.post("/simulate", response_model=CostSimulation)
async def simulate_cost(
    request: CostSimulationRequest,
    db: AsyncSession = Depends(get_db),
):
    """원가 시뮬레이션

    식수와 레시피를 기반으로 총 원가, 1식 단가를 계산합니다.
    대량 구매 할인율이 자동 적용됩니다 (1000식↑: 5%, 10000식↑: 10%).
    """
    service = RecipeService(db)
    if not request.recipe_id:
        raise HTTPException(status_code=400, detail="recipe_id가 필요합니다")
    try:
        return await service.calculate_cost(
            str(request.recipe_id), request.servings
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/suggest", response_model=list[MenuSuggestion])
async def suggest_menu(
    servings: int,
    budget: float | None = None,
    db: AsyncSession = Depends(get_db),
):
    """AI 메뉴 추천

    식수와 예산을 기반으로 최적 메뉴를 추천합니다.
    """
    if servings < 1 or servings > 100000:
        raise HTTPException(
            status_code=400, detail="식수는 1~100,000 범위여야 합니다"
        )
    service = RecipeService(db)
    return await service.suggest_menu(servings, budget)


@router.post("/compare", response_model=MenuComparisonResponse)
async def compare_menus(
    recipe_ids: list[str],
    servings: int,
    db: AsyncSession = Depends(get_db),
):
    """메뉴 비교

    여러 레시피의 원가를 비교합니다.
    """
    if servings < 1 or servings > 100000:
        raise HTTPException(
            status_code=400, detail="식수는 1~100,000 범위여야 합니다"
        )
    service = RecipeService(db)
    try:
        return await service.compare_menus(recipe_ids, servings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
