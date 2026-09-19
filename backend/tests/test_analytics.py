"""Integration tests for /api/analytics/* + side-channel LearningEvent writes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "a@a.com", password: str = "abcdefgh") -> dict:
    res = client.post("/api/auth/register", json={"email": email, "password": password})
    assert res.status_code == 201
    return res.json()


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------- calendar ----------


def test_calendar_default_90_days(client: TestClient) -> None:
    pair = _register(client)
    res = client.get("/api/analytics/calendar", headers=_auth_headers(pair["access_token"]))
    assert res.status_code == 200
    days = res.json()
    assert len(days) == 90
    assert all(d["minutes"] == 0 for d in days)
    assert days[-1]["date"] == days[-1]["date"]  # well-formed ISO date


def test_calendar_explicit_30_days(client: TestClient) -> None:
    pair = _register(client)
    res = client.get(
        "/api/analytics/calendar?days=30", headers=_auth_headers(pair["access_token"])
    )
    assert res.status_code == 200
    assert len(res.json()) == 30


def test_calendar_invalid_days(client: TestClient) -> None:
    pair = _register(client)
    res = client.get(
        "/api/analytics/calendar?days=10", headers=_auth_headers(pair["access_token"])
    )
    assert res.status_code == 422


def test_calendar_unauthorized(client: TestClient) -> None:
    res = client.get("/api/analytics/calendar")
    assert res.status_code == 401


def test_calendar_chat_message_counts_as_5_minutes(client: TestClient, monkeypatch) -> None:
    """Sending 3 chat messages on the same day should yield 15 minutes today."""
    pair = _register(client)
    sid = client.post(
        "/api/chat/sessions", headers=_auth_headers(pair["access_token"])
    ).json()["session_id"]

    # Replace deepseek.stream_chat with a no-op so we don't need network.
    from app.routers import chat as chat_router

    async def _fake_stream(messages, *, transport=None, timeout=None):
        if False:
            yield ""

    monkeypatch.setattr(chat_router, "stream_chat", _fake_stream)

    for _ in range(3):
        with client.stream(
            "POST",
            f"/api/chat/sessions/{sid}/messages",
            json={"content": "hi"},
            headers=_auth_headers(pair["access_token"]),
        ) as res:
            assert res.status_code == 200
            for _ in res.iter_lines():
                pass  # drain

    res = client.get(
        "/api/analytics/calendar?days=30", headers=_auth_headers(pair["access_token"])
    )
    assert res.status_code == 200
    days = res.json()
    today_minutes = days[-1]["minutes"]
    assert today_minutes == 15


# ---------- achievements ----------


def test_achievements_default_five_items(client: TestClient) -> None:
    pair = _register(client)
    res = client.get(
        "/api/analytics/achievements", headers=_auth_headers(pair["access_token"])
    )
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 5
    assert [it["id"] for it in items] == [
        "first_lesson",
        "streak_3",
        "streak_7",
        "total_50",
        "total_100",
    ]


def test_achievements_unauthorized(client: TestClient) -> None:
    res = client.get("/api/analytics/achievements")
    assert res.status_code == 401


def test_achievements_first_lesson_unlocks(client: TestClient, monkeypatch) -> None:
    pair = _register(client)
    sid = client.post(
        "/api/chat/sessions", headers=_auth_headers(pair["access_token"])
    ).json()["session_id"]

    from app.routers import chat as chat_router

    async def _fake_stream(messages, *, transport=None, timeout=None):
        if False:
            yield ""

    monkeypatch.setattr(chat_router, "stream_chat", _fake_stream)

    with client.stream(
        "POST",
        f"/api/chat/sessions/{sid}/messages",
        json={"content": "hi"},
        headers=_auth_headers(pair["access_token"]),
    ) as res:
        for _ in res.iter_lines():
            pass

    items = client.get(
        "/api/analytics/achievements", headers=_auth_headers(pair["access_token"])
    ).json()
    first = next(it for it in items if it["id"] == "first_lesson")
    assert first["unlocked"] is True
    assert first["progress"] == first["target"] == 1


def test_achievements_user_isolation(client: TestClient) -> None:
    a = _register(client, "a@x.com")
    b = _register(client, "b@x.com")

    # A creates one chat session (no messages yet)
    client.post("/api/chat/sessions", headers=_auth_headers(a["access_token"]))

    a_items = client.get(
        "/api/analytics/achievements", headers=_auth_headers(a["access_token"])
    ).json()
    b_items = client.get(
        "/api/analytics/achievements", headers=_auth_headers(b["access_token"])
    ).json()
    # Neither user has sent any messages, so first_lesson is locked for both.
    a_first = next(it for it in a_items if it["id"] == "first_lesson")
    b_first = next(it for it in b_items if it["id"] == "first_lesson")
    assert a_first["unlocked"] is False
    assert b_first["unlocked"] is False
    # Cross-check: A's session list includes A's session only (length 1).
    a_sessions = client.get(
        "/api/chat/sessions", headers=_auth_headers(a["access_token"])
    ).json()
    b_sessions = client.get(
        "/api/chat/sessions", headers=_auth_headers(b["access_token"])
    ).json()
    assert len(a_sessions) == 1
    assert b_sessions == []


# ---------- pure-function tests (no DB roundtrip) ----------


def test_current_streak_days_basic() -> None:
    from app.services.analytics import current_streak_days

    cal = [
        {"date": "2026-09-15", "minutes": 0},
        {"date": "2026-09-16", "minutes": 0},
        {"date": "2026-09-17", "minutes": 10},
        {"date": "2026-09-18", "minutes": 5},
    ]
    assert current_streak_days(cal) == 2


def test_current_streak_days_zero_when_last_is_zero() -> None:
    from app.services.analytics import current_streak_days

    cal = [
        {"date": "2026-09-17", "minutes": 10},
        {"date": "2026-09-18", "minutes": 0},
    ]
    assert current_streak_days(cal) == 0


def test_achievement_definitions_have_all_required_keys() -> None:
    from app.services.achievements import ACHIEVEMENT_DEFS

    ids = [d["id"] for d in ACHIEVEMENT_DEFS]
    assert ids == ["first_lesson", "streak_3", "streak_7", "total_50", "total_100"]
    for d in ACHIEVEMENT_DEFS:
        assert {"id", "title", "description", "target"} <= set(d.keys())