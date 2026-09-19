"""/api/chat/* router — sessions list/create, messages list, and SSE streaming send."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import db as db_module
from app.db import get_db
from app.deps import get_current_user
from app.models.chat import ChatMessage, ChatSession, MessageStatus
from app.models.learning_event import LearningEvent
from app.models.profile import UserProfile
from app.models.user import User
from app.schemas.chat import MessageOut, SendMessageIn, SessionListItem, SessionOut
from app.services.analytics import CHAT_MINUTES_PER_MESSAGE
from app.services.deepseek import DeepSeekError, stream_chat
from app.services.personalize import build_system_prompt

router = APIRouter(prefix="/api/chat", tags=["chat"])

_PREVIEW_LEN = 100
_STREAM_UPDATE_EVERY = 1  # characters — flush to DB every N chars; small for simplicity


def _owns_session(db: Session, session_id: int, user_id: int) -> ChatSession | None:
    sess = db.get(ChatSession, session_id)
    if sess is None or sess.user_id != user_id:
        return None
    return sess


@router.post("/sessions", response_model=SessionOut)
def create_session(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> SessionOut:
    sess = ChatSession(user_id=current.id)
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return SessionOut(
        session_id=sess.id,
        user_id=sess.user_id,
        created_at=sess.created_at,
        updated_at=sess.updated_at,
    )


@router.get("/sessions", response_model=list[SessionListItem])
def list_sessions(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[SessionListItem]:
    sessions = db.scalars(
        select(ChatSession).where(ChatSession.user_id == current.id).order_by(
            ChatSession.updated_at.desc()
        )
    ).all()

    items: list[SessionListItem] = []
    for sess in sessions:
        preview = ""
        if sess.messages:
            last = sess.messages[-1]
            preview = (last.content or "")[:_PREVIEW_LEN]
        items.append(
            SessionListItem(
                session_id=sess.id,
                created_at=sess.created_at,
                updated_at=sess.updated_at,
                preview=preview,
            )
        )
    return items


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
def list_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[MessageOut]:
    sess = _owns_session(db, session_id, current.id)
    if sess is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")
    return [
        MessageOut(
            message_id=m.id,
            role=m.role,
            content=m.content,
            status=m.status,
            created_at=m.created_at,
        )
        for m in sess.messages
    ]


def _build_history(messages: list[ChatMessage]) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in messages]


async def _stream_response(
    session_id: int, assistant_message_id: int, history_with_user: list[dict]
) -> AsyncIterator[bytes]:
    """SSE generator: yields data events for each delta, then a `done` event."""
    encoded = bytearray()
    last_flush_len = 0

    # The streaming loop runs against its own session because the request
    # session closes after the handler returns.
    db = db_module.SessionLocal()
    try:
        try:
            async for delta in stream_chat(history_with_user):
                encoded.extend(delta.encode("utf-8"))
                if len(encoded) - last_flush_len >= _STREAM_UPDATE_EVERY:
                    msg = db.get(ChatMessage, assistant_message_id)
                    if msg is not None:
                        msg.content = encoded.decode(errors="ignore")
                        db.commit()
                    last_flush_len = len(encoded)

                payload = json.dumps(
                    {"message_id": assistant_message_id, "role": "assistant", "delta": delta},
                    ensure_ascii=False,
                )
                yield f"data: {payload}\n\n".encode("utf-8")

            # Stream completed cleanly.
            msg = db.get(ChatMessage, assistant_message_id)
            if msg is not None:
                msg.content = encoded.decode(errors="ignore")
                msg.status = MessageStatus.COMPLETE.value
                db.commit()
            sess = db.get(ChatSession, session_id)
            if sess is not None:
                sess.updated_at = sess.updated_at  # onupdate triggers
                db.commit()

            done_payload = json.dumps(
                {"message_id": assistant_message_id, "status": "complete"}, ensure_ascii=False
            )
            yield f"event: done\ndata: {done_payload}\n\n".encode("utf-8")

        except DeepSeekError as exc:
            msg = db.get(ChatMessage, assistant_message_id)
            if msg is not None:
                msg.content = encoded.decode(errors="ignore")
                msg.status = MessageStatus.INCOMPLETE.value
                db.commit()
            err_payload = json.dumps({"detail": str(exc)}, ensure_ascii=False)
            yield f"event: error\ndata: {err_payload}\n\n".encode("utf-8")
    finally:
        db.close()


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: int,
    payload: SendMessageIn,
    current: User = Depends(get_current_user),
):
    # Validate ownership and persist user message + assistant placeholder
    # BEFORE the stream begins so the client can `listMessages` immediately.
    db = db_module.SessionLocal()
    try:
        sess = _owns_session(db, session_id, current.id)
        if sess is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="session not found"
            )

        profile = db.scalar(
            select(UserProfile).where(UserProfile.user_id == current.id)
        )
        system_prompt = build_system_prompt(current, profile)

        user_msg = ChatMessage(
            session_id=sess.id, role="user", content=payload.content, status="complete"
        )
        assistant_msg = ChatMessage(
            session_id=sess.id, role="assistant", content="", status="incomplete"
        )
        # Side-channel learning event for analytics aggregation.
        learn_event = LearningEvent(
            user_id=current.id,
            kind="chat",
            minutes=CHAT_MINUTES_PER_MESSAGE,
        )
        db.add_all([user_msg, assistant_msg, learn_event])
        db.commit()
        db.refresh(user_msg)
        db.refresh(assistant_msg)

        # Refresh session.updated_at so list ordering moves this session to top.
        sess.updated_at = sess.updated_at
        db.commit()

        history = [{"role": "system", "content": system_prompt}]
        history.extend(_build_history(sess.messages))  # includes the new user message
    finally:
        db.close()

    async def event_source() -> AsyncIterator[bytes]:
        async for chunk in _stream_response(session_id, assistant_msg.id, history):
            yield chunk
            await asyncio.sleep(0)  # cooperative yield

    from fastapi.responses import StreamingResponse

    return StreamingResponse(event_source(), media_type="text/event-stream")