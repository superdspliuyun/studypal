"""Achievement engine: 5 badges evaluated on demand from current aggregates.

Order is stable and IDs are the contract — spec `achievements` Requirement 2
and 3 promise exactly these five IDs in this order.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.analytics import count_user_messages, current_streak_days


ACHIEVEMENT_DEFS: list[dict] = [
    {
        "id": "first_lesson",
        "title": "初次启航",
        "description": "发出你的第一条学习消息",
        "target": 1,
    },
    {
        "id": "streak_3",
        "title": "三日连击",
        "description": "连续学习 3 天",
        "target": 3,
    },
    {
        "id": "streak_7",
        "title": "七日打卡",
        "description": "连续学习 7 天",
        "target": 7,
    },
    {
        "id": "total_50",
        "title": "五十答问",
        "description": "累计 50 条学习消息",
        "target": 50,
    },
    {
        "id": "total_100",
        "title": "百答大成",
        "description": "累计 100 条学习消息",
        "target": 100,
    },
]


def _progress_for(def_id: str, total_messages: int, streak: int) -> int:
    if def_id == "first_lesson":
        return 1 if total_messages >= 1 else 0
    if def_id == "streak_3":
        return streak
    if def_id == "streak_7":
        return streak
    if def_id == "total_50":
        return min(total_messages, 50)
    if def_id == "total_100":
        return min(total_messages, 100)
    return 0


def compute_achievements(
    db: Session, user_id: int, calendar: list[dict]
) -> list[dict]:
    total_messages = count_user_messages(db, user_id)
    streak = current_streak_days(calendar)
    out: list[dict] = []
    for d in ACHIEVEMENT_DEFS:
        progress = _progress_for(d["id"], total_messages, streak)
        out.append(
            {
                "id": d["id"],
                "title": d["title"],
                "description": d["description"],
                "unlocked": progress >= d["target"],
                "progress": progress,
                "target": d["target"],
            }
        )
    return out