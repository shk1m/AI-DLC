"""Pydantic 스키마: 레시피/시뮬레이션 도메인 (SECURITY-05: 입력 검증)"""

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CostSimulationRequest(BaseModel):
    """원가 시뮬레이션 요청 (BR-04, BR-08 검증)"""

    recipe_id: UUID | None = None
    servings: int = Field(ge=1, le=100000, description="식수 (1~100,000)")
    budget: float | None = Field(default=None, gt=0, le=100_000_000, description="예산 (원)")
    constraints: dict | None = Field(default=None, description="제약 조건")

    @field_validator("servings")
    @classmethod
    def validate_servings(cls, v: int) -> int:
        if v < 1 or v > 100000:
            raise ValueError("식수는 1~100,000 범위여야 합니다")
        return v


class IngredientCost(BaseModel):
    """재료별 원가"""

    item_id: UUID
    item_name: str
    quantity_needed: float
    unit: str
    unit_price: float
    total_price: float
    price_source: str
    price_available: bool = True


class CostSimulation(BaseModel):
    """원가 시뮬레이션 결과"""

    recipe_id: UUID | None = None
    recipe_name: str
    servings: int
    total_cost: float
    cost_per_serving: float
    ingredient_costs: list[IngredientCost]
    budget: float | None = None
    budget_status: str | None = None  # "예산 내" | "예산 초과"
    over_amount: float | None = None
    bulk_discount_applied: bool = False
    discount_rate: float = 0.0


class MenuSuggestion(BaseModel):
    """AI 메뉴 추천"""

    recipe_name: str
    description: str
    category: str
    estimated_cost_per_serving: float
    ingredients: list[str]
    nutrition_summary: str | None = None
    cost_simulation: CostSimulation | None = None


class MenuComparisonResponse(BaseModel):
    """메뉴 비교 응답"""

    servings: int
    menus: list[CostSimulation]
    cheapest: str
    most_nutritious: str | None = None
