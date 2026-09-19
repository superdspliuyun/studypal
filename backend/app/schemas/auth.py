"""Pydantic schemas for the /api/auth/* endpoints."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenPair(BaseModel):
    user_id: int
    email: EmailStr
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessOnly(BaseModel):
    access_token: str
    token_type: str = "bearer"