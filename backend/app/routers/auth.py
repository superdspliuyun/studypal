"""/api/auth/* router — register, login, refresh."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.profile import DEFAULT_AVATAR_URL, DEFAULT_LEVEL, DEFAULT_STREAK_DAYS, UserProfile
from app.models.user import User
from app.schemas.auth import AccessOnly, LoginIn, RefreshIn, RegisterIn, TokenPair
from app.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])


def _issue_token_pair(user: User) -> TokenPair:
    return TokenPair(
        user_id=user.id,
        email=user.email,
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post(
    "/register",
    response_model=TokenPair,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterIn, db: Session = Depends(get_db)) -> TokenPair:
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="email already registered"
        )

    user = User(email=email, password_hash=hash_password(payload.password))
    user.profile = UserProfile(
        avatar_url=DEFAULT_AVATAR_URL,
        streak_days=DEFAULT_STREAK_DAYS,
        level=DEFAULT_LEVEL,
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="email already registered"
        )
    db.refresh(user)

    return _issue_token_pair(user)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> TokenPair:
    email = payload.email.lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        # Spec: unified 401 message — no enumeration.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials"
        )
    return _issue_token_pair(user)


@router.post("/refresh", response_model=AccessOnly)
def refresh(payload: RefreshIn) -> AccessOnly:
    try:
        user_id = decode_token(payload.refresh_token, expected_typ="refresh")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token"
        ) from exc

    return AccessOnly(access_token=create_access_token(user_id))