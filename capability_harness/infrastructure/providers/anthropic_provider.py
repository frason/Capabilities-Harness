"""Anthropic provider — calls the Anthropic Messages API.

All Anthropic SDK imports are private to this module.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class AnthropicProvider:
    """Inference provider for Anthropic Claude models."""

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "claude-sonnet-4-6",
        max_tokens: int = 8096,
    ) -> None:
        self._api_key = api_key
        self._default_model = default_model
        self._default_max_tokens = max_tokens

    def provider_name(self) -> str:
        return "anthropic"

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        max_tokens: int = 8096,
        **kwargs: Any,
    ) -> str:
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "anthropic package not installed. Run: pip install 'capability-harness[anthropic]'"
            ) from exc

        resolved_model = model or self._default_model
        resolved_max = max_tokens or self._default_max_tokens

        # Split system message from conversation turns
        system: str | None = None
        turns: list[dict[str, str]] = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                turns.append(msg)

        kwargs_: dict[str, Any] = {}
        if system:
            kwargs_["system"] = system

        client = anthropic.AsyncAnthropic(api_key=self._api_key)
        response = await client.messages.create(
            model=resolved_model,
            max_tokens=resolved_max,
            messages=turns,  # type: ignore[arg-type]
            **kwargs_,
        )
        return str(response.content[0].text)
