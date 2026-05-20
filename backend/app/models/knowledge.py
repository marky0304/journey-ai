import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, Float, Uuid, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserKnowledge(Base):
    __tablename__ = "user_knowledge"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    url: Mapped[str] = mapped_column(String(2000))
    platform: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(String(2000))
    knowledge_points: Mapped[dict] = mapped_column(JSON, default=dict)
    tags: Mapped[dict] = mapped_column(JSON, default=dict)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    practical_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    raw_content: Mapped[Optional[str]] = mapped_column(String(10000), nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    merged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class LearnHistory(Base):
    __tablename__ = "learn_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    url: Mapped[str] = mapped_column(String(2000))
    platform: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(String(2000))
    knowledge_points: Mapped[dict] = mapped_column(JSON, default=dict)
    tags: Mapped[dict] = mapped_column(JSON, default=dict)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    learned_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class GlobalKnowledge(Base):
    __tablename__ = "global_knowledge"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_user_ids: Mapped[dict] = mapped_column(JSON, default=dict)
    source_item_ids: Mapped[dict] = mapped_column(JSON, default=dict)
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(String(2000))
    knowledge_points: Mapped[dict] = mapped_column(JSON, default=dict)
    tags: Mapped[dict] = mapped_column(JSON, default=dict)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    practical_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    merged_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
