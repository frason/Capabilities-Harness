"""Ollama provider — calls local Ollama server via OpenAI-compatible API.

Compatible with Ollama (port 11434), llama.cpp (port 8080), LM Studio (port 1234).
All provider SDK details are private to this module.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class OllamaProvider:
    """Inference provider for local Ollama-compatible servers."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "phi3",
        timeout_seconds: int = 120,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._timeout = timeout_seconds

    def provider_name(self) -> str:
        return "ollama"

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        resolved_model = model or self._default_model
        payload = {
            "model": resolved_model,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self._base_url}/v1/chat/completions", json=payload)
            resp.raise_for_status()
        data = resp.json()
        return str(data["choices"][0]["message"]["content"])

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self._base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False
