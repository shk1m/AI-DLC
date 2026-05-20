"""DL-01: NewsArticle 도메인 엔티티 (뉴스 기사)"""

import uuid
from datetime import datetime
import enum

from sqlalchemy import String, DateTime, Text, Enum as SAEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NewsSourceEnum(str, enum.Enum):
    """뉴스 출처"""
    NAVER = "네이버뉴스"
    MAFRA = "농림축산식품부"
    MOF = "해양수산부"


class NewsArticle(Base):
    __tablename__ = "news_articles"
    __table_args__ = (
        UniqueConstraint("url", name="uq_news_url"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False, unique=True)
    source: Mapped[NewsSourceEnum] = mapped_column(
        SAEnum(NewsSourceEnum, name="newssource_enum"), nullable=False
    )
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    related_item_ids: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
