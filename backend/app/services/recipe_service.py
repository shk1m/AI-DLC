"""BE-03: RecipeService - 레시피 제안 및 원가 시뮬레이션

핵심 기능:
- AI 기반 메뉴 추천 (Bedrock Claude)
- 식수별 원가 계산
- 메뉴 비교

비즈니스 규칙:
- BR-04: 원가 시뮬레이션 규칙
  - 식수 1~100,000
  - 대량 구매 할인율 (1000식 이상: 5%, 10000식 이상: 10%)
"""

import uuid
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.food_item import FoodItem
from app.models.price_record import PriceRecord
from app.models.recipe import Recipe, RecipeIngredient
from app.schemas.recipe import (
    CostSimulation,
    CostSimulationRequest,
    IngredientCost,
    MenuComparisonResponse,
    MenuSuggestion,
)
from app.services.price_service import PriceService

logger = structlog.get_logger()
settings = get_settings()


class RecipeService:
    """레시피 제안 및 원가 시뮬레이션 서비스

    AI 기반 메뉴 추천과 식수별 원가 계산을 수행합니다.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.price_service = PriceService(db)

    async def suggest_menu(
        self,
        servings: int,
        budget: Optional[float] = None,
        constraints: Optional[dict] = None,
    ) -> list[MenuSuggestion]:
        """AI 기반 메뉴 추천

        Args:
            servings: 식수
            budget: 예산 (원, 선택)
            constraints: 제약 조건 (영양, 알레르기 등)

        Returns:
            메뉴 추천 목록 (원가 시뮬레이션 포함)
        """
        logger.info(
            "menu_suggestion_requested",
            servings=servings,
            budget=budget,
            constraints=constraints,
        )

        # DB에서 레시피 목록 조회
        stmt = select(Recipe).limit(10)
        result = await self.db.execute(stmt)
        recipes = result.scalars().all()

        suggestions: list[MenuSuggestion] = []

        for recipe in recipes:
            # 각 레시피에 대해 원가 시뮬레이션
            try:
                cost_sim = await self.calculate_cost(str(recipe.id), servings)

                # 예산 필터링 (BR-04-3)
                if budget and cost_sim.total_cost > budget:
                    continue

                suggestion = MenuSuggestion(
                    recipe_name=recipe.name,
                    description=recipe.description or "",
                    category=recipe.category,
                    estimated_cost_per_serving=cost_sim.cost_per_serving,
                    ingredients=[],
                    nutrition_summary=self._format_nutrition(recipe),
                    cost_simulation=cost_sim,
                )
                suggestions.append(suggestion)
            except Exception as e:
                logger.warning(
                    "menu_suggestion_skip",
                    recipe_id=str(recipe.id),
                    error=str(e),
                )
                continue

        # 1식 단가 기준 정렬
        suggestions.sort(key=lambda s: s.estimated_cost_per_serving)

        return suggestions

    async def calculate_cost(
        self,
        recipe_id: str,
        servings: int,
    ) -> CostSimulation:
        """식수 기반 원가 계산

        알고리즘:
        1. 레시피 재료 목록 조회
        2. 각 재료의 현재 시세 조회
        3. 식수에 따른 필요 수량 계산
        4. 재료별 원가 계산
        5. 대량 구매 할인율 적용 (BR-04-5)

        Args:
            recipe_id: 레시피 UUID
            servings: 식수

        Returns:
            원가 시뮬레이션 결과
        """
        # 레시피 조회
        recipe_stmt = select(Recipe).where(Recipe.id == uuid.UUID(recipe_id))
        recipe_result = await self.db.execute(recipe_stmt)
        recipe = recipe_result.scalar_one_or_none()

        if not recipe:
            raise ValueError(f"레시피를 찾을 수 없습니다: {recipe_id}")

        # 재료 목록 조회
        ingredients_stmt = (
            select(RecipeIngredient)
            .where(RecipeIngredient.recipe_id == uuid.UUID(recipe_id))
        )
        ingredients_result = await self.db.execute(ingredients_stmt)
        ingredients = ingredients_result.scalars().all()

        # 각 재료별 원가 계산
        ingredient_costs: list[IngredientCost] = []
        total_cost = 0.0

        for ingredient in ingredients:
            # 식자재 정보 조회
            item_stmt = select(FoodItem).where(FoodItem.id == ingredient.item_id)
            item_result = await self.db.execute(item_stmt)
            food_item = item_result.scalar_one_or_none()

            if not food_item:
                continue

            # 현재 시세 조회 (최신 가격)
            price_stmt = (
                select(PriceRecord)
                .where(PriceRecord.item_id == ingredient.item_id)
                .order_by(PriceRecord.date.desc())
                .limit(1)
            )
            price_result = await self.db.execute(price_stmt)
            price_record = price_result.scalar_one_or_none()

            unit_price = price_record.wholesale_price if price_record else 0.0
            price_available = price_record is not None

            # 식수에 따른 필요 수량 계산
            base_servings = recipe.servings or 1
            quantity_needed = ingredient.quantity * (servings / base_servings)

            # 재료별 원가
            ingredient_total = quantity_needed * unit_price

            ingredient_costs.append(
                IngredientCost(
                    item_id=ingredient.item_id,
                    item_name=food_item.name,
                    quantity_needed=round(quantity_needed, 2),
                    unit=ingredient.unit,
                    unit_price=unit_price,
                    total_price=round(ingredient_total, 2),
                    price_source=price_record.source.value if price_record else "N/A",
                    price_available=price_available,
                )
            )
            total_cost += ingredient_total

        # 대량 구매 할인율 적용 (BR-04-5)
        discount_rate = self._get_bulk_discount_rate(servings)
        if discount_rate > 0:
            total_cost *= (1 - discount_rate)

        # 1식 단가 계산
        cost_per_serving = total_cost / servings if servings > 0 else 0

        return CostSimulation(
            recipe_id=uuid.UUID(recipe_id),
            recipe_name=recipe.name,
            servings=servings,
            total_cost=round(total_cost, 2),
            cost_per_serving=round(cost_per_serving, 2),
            ingredient_costs=ingredient_costs,
            bulk_discount_applied=discount_rate > 0,
            discount_rate=discount_rate,
        )

    async def compare_menus(
        self,
        recipe_ids: list[str],
        servings: int,
    ) -> MenuComparisonResponse:
        """메뉴 비교

        Args:
            recipe_ids: 비교할 레시피 ID 목록
            servings: 식수

        Returns:
            메뉴 비교 결과
        """
        simulations: list[CostSimulation] = []

        for recipe_id in recipe_ids:
            try:
                sim = await self.calculate_cost(recipe_id, servings)
                simulations.append(sim)
            except ValueError as e:
                logger.warning("menu_compare_skip", recipe_id=recipe_id, error=str(e))
                continue

        if not simulations:
            raise ValueError("비교할 수 있는 메뉴가 없습니다")

        # 가장 저렴한 메뉴
        cheapest = min(simulations, key=lambda s: s.cost_per_serving)

        return MenuComparisonResponse(
            servings=servings,
            menus=simulations,
            cheapest=cheapest.recipe_name,
            most_nutritious=None,  # 영양 비교는 추후 구현
        )

    # ─── Private Methods ───────────────────────────────────────────

    @staticmethod
    def _get_bulk_discount_rate(servings: int) -> float:
        """대량 구매 할인율 계산 (BR-04-5)

        - 1,000식 이상: 5%
        - 10,000식 이상: 10%
        """
        if servings >= 10000:
            return 0.10
        elif servings >= 1000:
            return 0.05
        return 0.0

    @staticmethod
    def _format_nutrition(recipe: Recipe) -> str:
        """영양 정보 포맷팅"""
        parts = []
        if recipe.calories_per_serving:
            parts.append(f"{recipe.calories_per_serving}kcal")
        if recipe.protein_per_serving:
            parts.append(f"단백질 {recipe.protein_per_serving}g")
        if recipe.carbohydrate_per_serving:
            parts.append(f"탄수화물 {recipe.carbohydrate_per_serving}g")
        if recipe.fat_per_serving:
            parts.append(f"지방 {recipe.fat_per_serving}g")
        return " / ".join(parts) if parts else "영양 정보 없음"
