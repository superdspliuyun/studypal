"""Pydantic schemas for /api/analytics/*."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CalendarDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: str
    minutes: int = Field(ge=0)


class AchievementOut(BaseModel):
    id: str
    title: str
    description: str
    unlocked: bool
    progress: int = Field(ge=0)
    target: int = Field(gt=0)