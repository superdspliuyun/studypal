"""Build the system prompt for the AI assistant.

Injects known user-profile fields (streak_days, level, avatar_url). Missing
fields are skipped rather than raising — keeps the chat responsive even if a
profile row is somehow absent (defensive against legacy data).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.profile import UserProfile
    from app.models.user import User


_SYSTEM_TEMPLATE = """You are StudyPal Assistant, a friendly study coach for a
learner currently using the StudyPal web app.

Personalization context (may be partial):
{context}

Style guidance:
- Be concise; prefer bullet lists and short paragraphs.
- Use Markdown (GFM): headings, tables, task lists, and fenced code blocks
  with language tags when relevant.
- Never include `<script>`, `<iframe>`, or inline event handlers.
- Do not invent personal data the learner did not share; ask one clarifying
  question if the request is ambiguous.
"""


def _field_or_none(label: str, value) -> str | None:  # noqa: ANN001
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return f"- {label}: {value}"


def build_system_prompt(user: "User", profile: "UserProfile | None") -> str:
    context_lines: list[str] = []
    context_lines.append(f"- user_id: {user.id}")
    context_lines.append(f"- email: {user.email}")

    if profile is not None:
        for line in (
            _field_or_none("streak_days", getattr(profile, "streak_days", None)),
            _field_or_none("level", getattr(profile, "level", None)),
            _field_or_none("avatar_url", getattr(profile, "avatar_url", None)),
        ):
            if line is not None:
                context_lines.append(line)

    context = "\n".join(context_lines)
    return _SYSTEM_TEMPLATE.format(context=context)