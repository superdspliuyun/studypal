"""/api/analytics/* router — calendar + achievements read-only endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.analytics import AchievementOut, CalendarDayOut
from app.services.achievements import compute_achievements
from app.services.analytics import ALLOWED_DAYS, aggregate_calendar


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/calendar", response_model=list[CalendarDayOut])
def get_calendar(
    days: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[CalendarDayOut]:
    if days is not None and days not in ALLOWED_DAYS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"days must be one of {list(ALLOWED_DAYS)}",
        )
    rows = aggregate_calendar(db, current.id, days)
    return [CalendarDayOut(**row) for row in rows]


@router.get("/achievements", response_model=list[AchievementOut])
def get_achievements(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[AchievementOut]:
    calendar = aggregate_calendar(db, current.id)
    items = compute_achievements(db, current.id, calendar)
    return [AchievementOut(**item) for item in items]