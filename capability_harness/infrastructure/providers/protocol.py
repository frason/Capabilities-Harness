"""Provider protocol — the interface every inference provider must implement.

All provider SDK imports live only in concrete Provider implementations,
never in this file or anywhere else in the codebase.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Provider(Protocol):
    """Inference provider interface.

    Concrete implementations: AnthropicProvider, OllamaProvider, OpenAIProvider, ...
    The Runtime communicates only through this interface.
    """

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        """Run inference and return the assistant response text."""
        ...

    def provider_name(self) -> str:
        """Return the canonical provider name (e.g. 'anthropic', 'ollama')."""
        ...
