"""Pydantic schemas for /api/chat/*."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class SessionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: int
    created_at: datetime
    updated_at: datetime
    preview: str = ""


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: int
    role: str
    content: str
    status: str
    created_at: datetime


class SendMessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=8192)

    @field_validator("content")
    @classmethod
    def _no_whitespace_only(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be empty or whitespace-only")
        return v