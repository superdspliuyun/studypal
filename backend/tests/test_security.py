"""Security primitives round-trip tests."""

from __future__ import annotations

import time

import pytest

from app.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_roundtrip() -> None:
    h = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", h) is True
    assert verify_password("wrong", h) is False


def test_access_decode_returns_user_id() -> None:
    uid = 42
    tok = create_access_token(uid)
    assert decode_token(tok, expected_typ="access") == uid


def test_refresh_decode_returns_user_id() -> None:
    uid = 7
    tok = create_refresh_token(uid)
    assert decode_token(tok, expected_typ="refresh") == uid


def test_type_mismatch_raises() -> None:
    tok = create_access_token(1)
    with pytest.raises(TokenError):
        decode_token(tok, expected_typ="refresh")


def test_garbage_token_raises() -> None:
    with pytest.raises(TokenError):
        decode_token("not-a-jwt", expected_typ="access")


def test_sub_must_be_digit() -> None:
    from jose import jwt

    from app.config import settings

    bad = jwt.encode(
        {"sub": "abc", "typ": "access", "exp": int(time.time()) + 60},
        settings.jwt_secret,
        algorithm="HS256",
    )
    with pytest.raises(TokenError):
        decode_token(bad, expected_typ="access")