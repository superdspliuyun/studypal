"""/api/users/me router — read and patch the authenticated user's profile."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from sqlalchemy import select

from app.db import get_db
from app.deps import get_current_user
from app.models.profile import UserProfile
from app.models.user import User
from app.schemas.profile import ProfileOut, ProfileUpdate


router = APIRouter(prefix="/api/users", tags=["profile"])


def _to_profile_out(user: User, profile: UserProfile) -> ProfileOut:
    return ProfileOut(
        user_id=user.id,
        email=user.email,
        avatar_url=profile.avatar_url,
        streak_days=profile.streak_days,
        level=profile.level,
    )


def _load_profile(db: Session, user: User) -> UserProfile:
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    if profile is None:  # defensive: registration guarantees one
        raise RuntimeError(f"missing profile for user {user.id}")
    return profile


@router.get("/me", response_model=ProfileOut)
def get_me(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ProfileOut:
    return _to_profile_out(current, _load_profile(db, current))


@router.patch("/me", response_model=ProfileOut)
def patch_me(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ProfileOut:
    profile = _load_profile(db, current)
    # Pydantic already restricted fields, but defense-in-depth: ignore any
    # rogue keys (streak_days / level) the spec forbids from client writes.
    profile.avatar_url = payload.avatar_url
    db.commit()
    db.refresh(profile)
    return _to_profile_out(current, profile)