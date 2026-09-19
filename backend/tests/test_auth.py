"""Integration tests for /api/auth/* endpoints."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import settings
from app.security import create_access_token, create_refresh_token


def _register(client: TestClient, email: str = "a@b.com", password: str = "abcdefgh") -> dict:
    res = client.post("/api/auth/register", json={"email": email, "password": password})
    assert res.status_code == 201, res.text
    return res.json()


def test_register_success(client: TestClient) -> None:
    body = _register(client)
    assert body["user_id"] >= 1
    assert body["email"] == "a@b.com"
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_register_duplicate_email(client: TestClient) -> None:
    _register(client)
    res = client.post(
        "/api/auth/register", json={"email": "a@b.com", "password": "abcdefgh"}
    )
    assert res.status_code == 409


def test_register_invalid_email(client: TestClient) -> None:
    res = client.post(
        "/api/auth/register", json={"email": "not-an-email", "password": "abcdefgh"}
    )
    assert res.status_code == 422


def test_register_short_password(client: TestClient) -> None:
    res = client.post(
        "/api/auth/register", json={"email": "a@b.com", "password": "short"}
    )
    assert res.status_code == 422


def test_login_success(client: TestClient) -> None:
    _register(client)
    res = client.post(
        "/api/auth/login", json={"email": "a@b.com", "password": "abcdefgh"}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["access_token"] and body["refresh_token"]


def test_login_wrong_password(client: TestClient) -> None:
    _register(client)
    res = client.post(
        "/api/auth/login", json={"email": "a@b.com", "password": "wrongpwd1"}
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "invalid credentials"


def test_login_unknown_email_same_message(client: TestClient) -> None:
    res = client.post(
        "/api/auth/login", json={"email": "ghost@x.com", "password": "abcdefgh"}
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "invalid credentials"


def test_refresh_success(client: TestClient) -> None:
    pair = _register(client)
    res = client.post("/api/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert res.status_code == 200
    assert res.json()["access_token"]
    assert res.json()["token_type"] == "bearer"


def test_refresh_with_access_token_rejected(client: TestClient) -> None:
    pair = _register(client)
    res = client.post("/api/auth/refresh", json={"refresh_token": pair["access_token"]})
    assert res.status_code == 401


def test_refresh_expired_rejected(client: TestClient) -> None:
    expired = jwt.encode(
        {
            "sub": "1",
            "typ": "refresh",
            "iat": int(time.time()) - 3600,
            "exp": int(time.time()) - 60,
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    res = client.post("/api/auth/refresh", json={"refresh_token": expired})
    assert res.status_code == 401
    assert res.json()["detail"] == "invalid refresh token"


def test_protected_route_no_header(client: TestClient) -> None:
    res = client.get("/api/users/me")
    assert res.status_code == 401


def test_protected_route_expired_token(client: TestClient) -> None:
    expired = jwt.encode(
        {
            "sub": "1",
            "typ": "access",
            "iat": int(time.time()) - 3600,
            "exp": int(time.time()) - 60,
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    res = client.get("/api/users/me", headers={"Authorization": f"Bearer {expired}"})
    assert res.status_code == 401