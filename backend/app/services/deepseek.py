"""Thin async client for the DeepSeek (OpenAI-compatible) chat-completions API.

Streams `delta.content` chunks via an async iterator. The transport is
injectable so tests can substitute a MockTransport without hitting the
real network.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.config import settings


class DeepSeekError(Exception):
    """Raised on transport / HTTP / parse failure from the DeepSeek API."""


_DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)


async def stream_chat(
    messages: list[dict[str, Any]],
    *,
    transport: httpx.BaseTransport | None = None,
    timeout: httpx.Timeout | None = None,
) -> AsyncIterator[str]:
    """Yield assistant content deltas for the given message history.

    The caller is responsible for accumulating deltas and persisting the
    final concatenated content.
    """
    url = f"{settings.deepseek_base_url.rstrip('/')}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "model": settings.deepseek_model,
        "messages": messages,
        "stream": True,
    }

    client_kwargs: dict[str, Any] = {"timeout": timeout or _DEFAULT_TIMEOUT}
    if transport is not None:
        client_kwargs["transport"] = transport

    try:
        async with httpx.AsyncClient(**client_kwargs) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code >= 400:
                    body = await response.aread()
                    raise DeepSeekError(
                        f"deepseek http {response.status_code}: {body.decode(errors='ignore')[:200]}"
                    )

                async for raw_line in response.aiter_lines():
                    if not raw_line:
                        continue
                    if not raw_line.startswith("data:"):
                        continue
                    data = raw_line[len("data:") :].strip()
                    if data == "[DONE]":
                        return
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError as exc:
                        raise DeepSeekError(f"invalid SSE JSON: {data!r}") from exc

                    delta = _extract_delta(chunk)
                    if delta:
                        yield delta
    except httpx.HTTPError as exc:
        raise DeepSeekError(f"deepseek transport error: {exc}") from exc


def _extract_delta(chunk: dict[str, Any]) -> str:
    try:
        return chunk["choices"][0]["delta"].get("content") or ""
    except (KeyError, IndexError, TypeError):
        return ""