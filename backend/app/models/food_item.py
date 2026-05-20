"""DL-01: FoodItem 도메인 엔티티 (식자재 마스터)"""

import uuid
from datetime import datetime

from sqlalchemy import String, Float, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base


class CategoryEnum(str, enum.Enum):
    """식자재 대분류"""
    GRAIN = "구황작물"
    SEAFOOD = "수산물"
    VEGETABLE = "채소류"
    FRUIT = "과일류"
    LIVESTOCK = "축산류"
    PROCESSED = "가공식품"


class FoodItem(Base):
    __tablename__ = "food_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[CategoryEnum] = mapped_column(
        SAEnum(CategoryEnum, name="category_enum"), nullable=False, index=True
    )
    subcategory: Mapped[str] = mapped_column(String(50), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    season: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # 영양 정보
    calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbohydrate: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    fiber: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    price_records = relationship("PriceRecord", back_populates="food_item")
    spike_events = relationship("SpikeEvent", back_populates="food_item")
