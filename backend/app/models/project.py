from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    platform: Mapped[str] = mapped_column(String(50), default="TikTok", nullable=False)
    duration: Mapped[int] = mapped_column(default=45, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

    storyboards: Mapped[list["Storyboard"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    music: Mapped["ProjectMusic | None"] = relationship(back_populates="project", uselist=False, cascade="all, delete-orphan")
