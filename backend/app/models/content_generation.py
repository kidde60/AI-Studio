from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ContentGeneration(Base):
    __tablename__ = "content_generations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    style: Mapped[str] = mapped_column(String(50), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    target_audience: Mapped[str] = mapped_column(String(300), nullable=False)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    hook: Mapped[str] = mapped_column(Text, nullable=False)
    script: Mapped[str] = mapped_column(Text, nullable=False)
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    cta: Mapped[str] = mapped_column(Text, nullable=False)
    content_ideas: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

