"""DL-01: PriceRecord 도메인 엔티티 (시세 기록)"""

import uuid
from datetime import date, datetime
import enum

from sqlalchemy import String, Float, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DataSourceEnum(str, enum.Enum):
    """데이터 출처"""
    KAMIS = "KAMIS"
    PUBLIC_DATA = "공공데이터포털"
    EKAPEPIA = "축산유통정보"
    SFISH = "수산물유통정보"


class PriceRecord(Base):
    __tablename__ = "price_records"
    __table_args__ = (
        UniqueConstraint("item_id", "date", "source", name="uq_item_date_source"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("food_items.id"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    wholesale_price: Mapped[float] = mapped_column(Float, nullable=False)
    retail_price: Mapped[float] = mapped_column(Float, nullable=False)
    price_gap: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[DataSourceEnum] = mapped_column(
        SAEnum(DataSourceEnum, name="datasource_enum"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    food_item = relationship("FoodItem", back_populates="price_records")
