"""Pydantic schemas for /api/users/me."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    email: EmailStr
    avatar_url: str
    streak_days: int
    level: int


class ProfileUpdate(BaseModel):
    """PATCH body — only avatar_url is client-writable."""

    avatar_url: str = Field(min_length=1, max_length=2048)