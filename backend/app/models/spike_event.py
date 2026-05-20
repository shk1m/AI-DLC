"""DL-01: SpikeEvent 도메인 엔티티 (가격 이상치 이벤트)"""

import uuid
from datetime import date, datetime
import enum

from sqlalchemy import String, Float, Date, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SpikeTypeEnum(str, enum.Enum):
    """Spike 유형"""
    SURGE = "급등"
    DROP = "급락"


class SpikeEvent(Base):
    __tablename__ = "spike_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("food_items.id"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    spike_type: Mapped[SpikeTypeEnum] = mapped_column(
        SAEnum(SpikeTypeEnum, name="spiketype_enum"), nullable=False
    )
    magnitude: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_price: Mapped[float] = mapped_column(Float, nullable=False)
    spike_price: Mapped[float] = mapped_column(Float, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    food_item = relationship("FoodItem", back_populates="spike_events")
