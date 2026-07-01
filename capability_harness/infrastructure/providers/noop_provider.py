"""NoOp provider — returns a stub response without calling any inference API.

Used during skeleton wiring and unit tests.
"""
from __future__ import annotations

from typing import Any


class NoOpProvider:
    """Stub provider that echoes back a predictable response."""

    def provider_name(self) -> str:
        return "noop"

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            "(no user message)",
        )
        return f"[noop] received: {last_user[:120]}"
