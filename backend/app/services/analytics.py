"""Analytics aggregation: per-day learning minutes from chat + learning_events.

The aggregation treats one user-sent chat message as 5 minutes of learning and
adds any explicit `learning_events.minutes` value for that UTC day. Empty days
are filled with minutes=0 so the response array length always matches `days`.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage
from app.models.learning_event import LearningEvent

CHAT_MINUTES_PER_MESSAGE = 5
ALLOWED_DAYS = (30, 60, 90, 180)
DEFAULT_DAYS = 90


def _utc_day(dt: datetime) -> date:
    return dt.astimezone(timezone.utc).date() if dt.tzinfo else dt.date()


def _window_start(days: int) -> date:
    return datetime.now(timezone.utc).date() - timedelta(days=days - 1)


def _normalize_days(days: int | None) -> int:
    if days is None:
        return DEFAULT_DAYS
    if days not in ALLOWED_DAYS:
        raise ValueError(f"days must be one of {ALLOWED_DAYS}, got {days}")
    return days


def aggregate_calendar(
    db: Session, user_id: int, days: int | None = None
) -> list[dict[str, int | str]]:
    """Return a length-`days` array of {date, minutes} sorted ascending by date.

    Minutes = chat_user_messages_on_that_day * CHAT_MINUTES_PER_MESSAGE +
              SUM(learning_events.minutes for that day).
    """
    n = _normalize_days(days)
    start = _window_start(n)
    end = start + timedelta(days=n - 1)

    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)

    # Aggregate chat user-message count by UTC date.
    # chat_messages.user_id is not stored — join via chat_sessions.user_id.
    from app.models.chat import ChatSession

    chat_rows = db.execute(
        select(
            func.date(ChatMessage.created_at).label("d"),
            func.count(ChatMessage.id),
        )
        .join(ChatSession, ChatSession.id == ChatMessage.session_id)
        .where(
            ChatSession.user_id == user_id,
            ChatMessage.role == "user",
            ChatMessage.created_at >= start_dt,
            ChatMessage.created_at < end_dt,
        )
        .group_by(func.date(ChatMessage.created_at))
    ).all()

    learn_rows = db.execute(
        select(
            func.date(LearningEvent.created_at).label("d"),
            func.coalesce(func.sum(LearningEvent.minutes), 0),
        )
        .where(
            LearningEvent.user_id == user_id,
            # Chat contributions are aggregated via chat_messages above.
            # LearningEvent is reserved for non-chat sources (goals, manual logs).
            LearningEvent.kind != "chat",
            LearningEvent.created_at >= start_dt,
            LearningEvent.created_at < end_dt,
        )
        .group_by(func.date(LearningEvent.created_at))
    ).all()

    minutes_by_day: dict[date, int] = defaultdict(int)
    for d, count in chat_rows:
        if d is None:
            continue
        day = date.fromisoformat(d) if isinstance(d, str) else d
        minutes_by_day[day] += int(count) * CHAT_MINUTES_PER_MESSAGE
    for d, mins in learn_rows:
        if d is None:
            continue
        day = date.fromisoformat(d) if isinstance(d, str) else d
        minutes_by_day[day] += int(mins)

    out: list[dict[str, int | str]] = []
    for offset in range(n):
        d = start + timedelta(days=offset)
        out.append({"date": d.isoformat(), "minutes": minutes_by_day.get(d, 0)})
    return out


def count_user_messages(db: Session, user_id: int) -> int:
    """Total user-role chat messages for a user (across all sessions)."""
    from app.models.chat import ChatSession

    return int(
        db.scalar(
            select(func.count(ChatMessage.id))
            .join(ChatSession, ChatSession.id == ChatMessage.session_id)
            .where(ChatSession.user_id == user_id, ChatMessage.role == "user")
        )
        or 0
    )


def current_streak_days(calendar: Iterable[dict]) -> int:
    """Number of consecutive days with minutes > 0 at the end of the calendar."""
    n = 0
    for day in reversed(list(calendar)):
        if int(day["minutes"]) > 0:
            n += 1
        else:
            break
    return n