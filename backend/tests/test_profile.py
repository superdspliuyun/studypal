"""Integration tests for /api/users/me."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _register_and_token(client: TestClient) -> dict:
    res = client.post(
        "/api/auth/register", json={"email": "p@p.com", "password": "abcdefgh"}
    )
    assert res.status_code == 201
    return res.json()


def test_get_me_success(client: TestClient) -> None:
    pair = _register_and_token(client)
    res = client.get(
        "/api/users/me", headers={"Authorization": f"Bearer {pair['access_token']}"}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == "p@p.com"
    assert body["streak_days"] == 0
    assert body["level"] == 1
    assert body["avatar_url"] == "/static/avatars/default.png"
    assert body["user_id"] == pair["user_id"]


def test_get_me_unauthorized(client: TestClient) -> None:
    res = client.get("/api/users/me")
    assert res.status_code == 401


def test_patch_avatar_success(client: TestClient) -> None:
    pair = _register_and_token(client)
    new_url = "https://cdn.example.com/me.png"
    res = client.patch(
        "/api/users/me",
        json={"avatar_url": new_url},
        headers={"Authorization": f"Bearer {pair['access_token']}"},
    )
    assert res.status_code == 200
    assert res.json()["avatar_url"] == new_url


def test_patch_avatar_too_long(client: TestClient) -> None:
    pair = _register_and_token(client)
    too_long = "x" * 2049
    res = client.patch(
        "/api/users/me",
        json={"avatar_url": too_long},
        headers={"Authorization": f"Bearer {pair['access_token']}"},
    )
    assert res.status_code == 422


def test_patch_streak_and_level_ignored(client: TestClient) -> None:
    pair = _register_and_token(client)
    res = client.patch(
        "/api/users/me",
        json={"avatar_url": "https://cdn.example.com/x.png", "streak_days": 99, "level": 99},
        headers={"Authorization": f"Bearer {pair['access_token']}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["avatar_url"] == "https://cdn.example.com/x.png"
    assert body["streak_days"] == 0
    assert body["level"] == 1


def test_default_avatar_served(client: TestClient) -> None:
    res = client.get("/static/avatars/default.png")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image/png")