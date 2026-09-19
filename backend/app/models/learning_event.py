"""LearningEvent ORM model — explicit study activity record.

Used for analytics aggregation alongside chat_messages. Today only the chat
router writes here (kind='chat', minutes=5 per message). Future changes can
add other event sources (goal completion, manual logging, etc.) by inserting
additional rows of different `kind` values.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LearningEvent(Base):
    __tablename__ = "learning_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(32), default="chat", nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )

    user = relationship("User")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"LearningEvent(id={self.id!r}, user_id={self.user_id!r}, "
            f"kind={self.kind!r}, minutes={self.minutes!r})"
        )