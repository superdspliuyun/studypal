"""Password hashing and JWT issuing / verifying.

bcrypt cost factor is pinned to 12 (passlib default) so future tuning must be
explicit. JWTs carry `sub` (user_id as str), `typ` (access|refresh), and `exp`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

JWT_ALGORITHM = "HS256"
TokenType = Literal["access", "refresh"]


class TokenError(Exception):
    """Raised when a token is invalid, expired, or of the wrong type."""


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _build_token(
    *, user_id: int, typ: TokenType, ttl: timedelta, secret: str
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "typ": typ,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def create_access_token(user_id: int) -> str:
    return _build_token(
        user_id=user_id,
        typ="access",
        ttl=timedelta(minutes=settings.jwt_access_ttl_min),
        secret=settings.jwt_secret,
    )


def create_refresh_token(user_id: int) -> str:
    return _build_token(
        user_id=user_id,
        typ="refresh",
        ttl=timedelta(days=settings.jwt_refresh_ttl_day),
        secret=settings.jwt_secret,
    )


def decode_token(token: str, expected_typ: TokenType) -> int:
    """Return user_id from a JWT, raising TokenError on any validation failure."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise TokenError(f"invalid token: {exc}") from exc

    typ = payload.get("typ")
    sub = payload.get("sub")
    if typ != expected_typ:
        raise TokenError(f"expected token type {expected_typ!r}, got {typ!r}")
    if not isinstance(sub, str) or not sub.isdigit():
        raise TokenError("token missing or malformed sub claim")
    return int(sub)