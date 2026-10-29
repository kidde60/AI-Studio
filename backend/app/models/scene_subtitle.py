from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class SceneSubtitle(Base):
    __tablename__ = "scene_subtitles"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    scene_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    cues: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    srt_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    scene: Mapped["Scene"] = relationship(back_populates="subtitles")
