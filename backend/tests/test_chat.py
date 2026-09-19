"""Integration tests for /api/chat/*."""

from __future__ import annotations

import json

import httpx
import pytest
from fastapi.testclient import TestClient


# ---------- helpers ----------

def _register(client: TestClient, email: str = "c@c.com", password: str = "abcdefgh") -> dict:
    res = client.post("/api/auth/register", json={"email": email, "password": password})
    assert res.status_code == 201, res.text
    return res.json()


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------- session CRUD ----------

def test_create_and_list_session(client: TestClient) -> None:
    pair = _register(client)
    res = client.post("/api/chat/sessions", headers=_auth_headers(pair["access_token"]))
    assert res.status_code == 200
    body = res.json()
    assert body["user_id"] == pair["user_id"]
    sid = body["session_id"]

    res = client.get("/api/chat/sessions", headers=_auth_headers(pair["access_token"]))
    assert res.status_code == 200
    items = res.json()
    assert any(item["session_id"] == sid for item in items)


def test_create_session_unauthorized(client: TestClient) -> None:
    res = client.post("/api/chat/sessions")
    assert res.status_code == 401


def test_list_sessions_empty(client: TestClient) -> None:
    pair = _register(client)
    res = client.get("/api/chat/sessions", headers=_auth_headers(pair["access_token"]))
    assert res.status_code == 200
    assert res.json() == []


def test_list_sessions_other_user_invisible(client: TestClient) -> None:
    a = _register(client, "a@a.com")
    b = _register(client, "b@b.com")
    client.post("/api/chat/sessions", headers=_auth_headers(a["access_token"]))
    res = client.get("/api/chat/sessions", headers=_auth_headers(b["access_token"]))
    assert res.status_code == 200
    assert res.json() == []


# ---------- messages list ----------

def test_get_messages_own_empty(client: TestClient) -> None:
    pair = _register(client)
    sid = client.post("/api/chat/sessions", headers=_auth_headers(pair["access_token"])).json()[
        "session_id"
    ]
    res = client.get(
        f"/api/chat/sessions/{sid}/messages", headers=_auth_headers(pair["access_token"])
    )
    assert res.status_code == 200
    assert res.json() == []


def test_get_messages_other_user_404(client: TestClient) -> None:
    a = _register(client, "a@a.com")
    b = _register(client, "b@b.com")
    sid_a = client.post("/api/chat/sessions", headers=_auth_headers(a["access_token"])).json()[
        "session_id"
    ]
    res = client.get(
        f"/api/chat/sessions/{sid_a}/messages", headers=_auth_headers(b["access_token"])
    )
    assert res.status_code == 404


def test_get_messages_unauthorized(client: TestClient) -> None:
    res = client.get("/api/chat/sessions/1/messages")
    assert res.status_code == 401


# ---------- streaming send ----------

class _FakeSSETransport(httpx.AsyncBaseTransport):
    """Async transport yielding a hand-crafted SSE stream like DeepSeek's wire format."""

    def __init__(self, deltas: list[str], fail_after: int | None = None) -> None:
        self.deltas = deltas
        self.fail_after = fail_after

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        body = bytearray()
        for i, d in enumerate(self.deltas):
            if self.fail_after is not None and i >= self.fail_after:
                return httpx.Response(200, content=bytes(body))
            chunk = {"choices": [{"delta": {"content": d}, "index": 0}]}
            body.extend(f"data: {json.dumps(chunk)}\n\n".encode())
        body.extend(b"data: [DONE]\n\n")
        return httpx.Response(
            200,
            content=bytes(body),
            headers={"content-type": "text/event-stream"},
        )


def _patch_deepseek(monkeypatch, deltas, fail_after=None):
    """Replace the stream_chat symbol the chat router imported."""
    from app.routers import chat as chat_router
    from app.services import deepseek as ds

    async def _fake_stream(messages, *, transport=None, timeout=None):
        for i, d in enumerate(deltas):
            if fail_after is not None and i >= fail_after:
                raise ds.DeepSeekError("simulated upstream failure")
            yield d

    monkeypatch.setattr(chat_router, "stream_chat", _fake_stream)


def _read_sse(res) -> list[tuple[str, str]]:
    """Return list of (event_type, payload) decoded from the SSE response body."""
    raw_parts: list[str] = []
    for raw_line in res.iter_lines():
        raw_parts.append(raw_line + "\n")
    raw = "".join(raw_parts)
    events: list[tuple[str, str]] = []
    event_type = "message"
    for line in raw.split("\n"):
        line = line.rstrip("\r")
        if not line:
            event_type = "message"
            continue
        if line.startswith("event:"):
            event_type = line[len("event:") :].strip()
        elif line.startswith("data:"):
            events.append((event_type, line[len("data:") :].strip()))
    return events


def test_stream_complete(client: TestClient, monkeypatch) -> None:
    pair = _register(client)
    sid = client.post("/api/chat/sessions", headers=_auth_headers(pair["access_token"])).json()[
        "session_id"
    ]
    _patch_deepseek(monkeypatch, ["你好", "，", "世界"])

    with client.stream(
        "POST",
        f"/api/chat/sessions/{sid}/messages",
        json={"content": "hello"},
        headers=_auth_headers(pair["access_token"]),
    ) as res:
        assert res.status_code == 200
        assert res.headers["content-type"].startswith("text/event-stream")
        events = _read_sse(res)

    # Three delta events + a final done event.
    assert len([e for e in events if e[0] == "message"]) == 3
    assert events[-1][0] == "done"

    # Messages persisted (user + assistant) and assistant marked complete.
    msgs = client.get(
        f"/api/chat/sessions/{sid}/messages", headers=_auth_headers(pair["access_token"])
    ).json()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"
    assert msgs[1]["status"] == "complete"
    assert msgs[1]["content"] == "你好，世界"


def test_stream_failure_marks_incomplete(client: TestClient, monkeypatch) -> None:
    pair = _register(client)
    sid = client.post("/api/chat/sessions", headers=_auth_headers(pair["access_token"])).json()[
        "session_id"
    ]
    # fail_after=0 means the very first iteration raises — the spec requires
    # that an interrupted stream still persists any partial content as
    # status=incomplete. With no deltas at all we get a complete-but-empty
    # incomplete message, which is the most defensible edge case.
    _patch_deepseek(monkeypatch, ["would-be-delta"], fail_after=0)

    with client.stream(
        "POST",
        f"/api/chat/sessions/{sid}/messages",
        json={"content": "hi"},
        headers=_auth_headers(pair["access_token"]),
    ) as res:
        assert res.status_code == 200
        events = _read_sse(res)

    # Stream should end with an error event (not done).
    assert events[-1][0] == "error"

    msgs = client.get(
        f"/api/chat/sessions/{sid}/messages", headers=_auth_headers(pair["access_token"])
    ).json()
    assert msgs[1]["role"] == "assistant"
    assert msgs[1]["status"] == "incomplete"
    assert msgs[1]["content"] == ""


def test_stream_empty_content_422(client: TestClient, monkeypatch) -> None:
    pair = _register(client)
    sid = client.post("/api/chat/sessions", headers=_auth_headers(pair["access_token"])).json()[
        "session_id"
    ]
    res = client.post(
        f"/api/chat/sessions/{sid}/messages",
        json={"content": "   "},
        headers=_auth_headers(pair["access_token"]),
    )
    assert res.status_code == 422


def test_stream_other_session_404(client: TestClient, monkeypatch) -> None:
    a = _register(client, "a@a.com")
    b = _register(client, "b@b.com")
    sid_a = client.post("/api/chat/sessions", headers=_auth_headers(a["access_token"])).json()[
        "session_id"
    ]
    res = client.post(
        f"/api/chat/sessions/{sid_a}/messages",
        json={"content": "hi"},
        headers=_auth_headers(b["access_token"]),
    )
    assert res.status_code == 404


def test_stream_unauthorized(client: TestClient) -> None:
    res = client.post("/api/chat/sessions/1/messages", json={"content": "hi"})
    assert res.status_code == 401


# ---------- personalize ----------

def test_personalize_injects_known_fields() -> None:
    from app.models.profile import UserProfile
    from app.models.user import User
    from app.services.personalize import build_system_prompt

    user = User(id=1, email="x@y.com", password_hash="h")
    profile = UserProfile(user_id=1, avatar_url="/a.png", streak_days=5, level=2)
    prompt = build_system_prompt(user, profile)
    assert "streak_days: 5" in prompt
    assert "level: 2" in prompt
    assert "avatar_url: /a.png" in prompt


def test_personalize_missing_profile_skips_fields() -> None:
    from app.models.user import User
    from app.services.personalize import build_system_prompt

    user = User(id=2, email="y@y.com", password_hash="h")
    prompt = build_system_prompt(user, None)
    assert "streak_days" not in prompt
    assert "level" not in prompt
    assert "user_id: 2" in prompt


# ---------- deepseek client parser ----------

@pytest.mark.asyncio
async def test_deepseek_stream_chat_parses_sse(monkeypatch) -> None:
    from app.services import deepseek as ds

    captured: list[str] = []

    async def _collect():
        async for d in ds.stream_chat(
            [{"role": "user", "content": "hi"}],
            transport=_FakeSSETransport(["a", "b", "c"]),
        ):
            captured.append(d)

    await _collect()
    assert captured == ["a", "b", "c"]