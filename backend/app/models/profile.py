"""UserProfile ORM model — avatar / streak_days / level."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.user import User


DEFAULT_AVATAR_URL = "/static/avatars/default.png"
DEFAULT_STREAK_DAYS = 0
DEFAULT_LEVEL = 1


class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_profiles_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    avatar_url: Mapped[str] = mapped_column(
        String(2048),
        default=DEFAULT_AVATAR_URL,
        nullable=False,
    )
    streak_days: Mapped[int] = mapped_column(Integer, default=DEFAULT_STREAK_DAYS, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=DEFAULT_LEVEL, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"UserProfile(user_id={self.user_id!r}, level={self.level!r}, "
            f"streak_days={self.streak_days!r})"
        )