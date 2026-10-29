from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    storyboard_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("storyboards.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    scene_order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    narration: Mapped[str | None] = mapped_column(Text, nullable=True)
    visual_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    transition: Mapped[str] = mapped_column(String(50), default="cut", nullable=False)
    media_asset_ids: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

    storyboard: Mapped["Storyboard"] = relationship(back_populates="scenes")
    audio: Mapped["SceneAudio | None"] = relationship(back_populates="scene", uselist=False, cascade="all, delete-orphan")
    subtitles: Mapped["SceneSubtitle | None"] = relationship(back_populates="scene", uselist=False, cascade="all, delete-orphan")
