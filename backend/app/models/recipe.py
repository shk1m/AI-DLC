"""DL-01: Recipe 도메인 엔티티 (레시피)"""

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    servings: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    steps: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # 영양 정보 (1인분 기준)
    calories_per_serving: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein_per_serving: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbohydrate_per_serving: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_per_serving: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    ingredients = relationship("RecipeIngredient", back_populates="recipe")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("food_items.id"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)
    substitutable: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    recipe = relationship("Recipe", back_populates="ingredients")
    food_item = relationship("FoodItem")
