"""Local runtime for on-device capability execution via Ollama / llama.cpp / LM Studio.

All provider details (endpoints, API format) are private to this module.
Uses the OpenAI-compatible /v1/chat/completions endpoint so it works with
any local server — just change base_url in config.
"""
from __future__ import annotations

import logging

import httpx

from capability_harness.domain.capability import CapabilitySpec, WorkRequest, WorkResult

logger = logging.getLogger(__name__)


class LocalRuntime:
    """Executes capabilities via local LLM servers.

    Compatible with Ollama (port 11434), llama.cpp (port 8080),
    and LM Studio (port 1234) — all expose the same OpenAI-compatible API.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "mistral",
        timeout_seconds: int = 120,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._timeout = timeout_seconds

    async def run(self, spec: CapabilitySpec, request: WorkRequest) -> WorkResult:
        system_prompt = request.context or spec.description
        user_message = (
            f"Capability: {spec.name}\n"
            f"Task ID: {request.task_id}\n\n"
            f"Produced artifacts: {', '.join(a.value for a in spec.produced_artifacts)}\n\n"
            "Complete the capability task described in the system prompt."
        )
        payload = {
            "model": self._default_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(f"{self._base_url}/v1/chat/completions", json=payload)
                resp.raise_for_status()
            data = resp.json()
            output = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return WorkResult(
                task_id=request.task_id,
                success=True,
                output=output,
                metadata={
                    "model": self._default_model,
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0),
                    "provider": "local",
                },
            )
        except httpx.ConnectError:
            return WorkResult(
                task_id=request.task_id,
                success=False,
                output="",
                error=f"Local runtime unavailable at {self._base_url}. Is Ollama running?",
            )
        except Exception as exc:
            logger.exception("LocalRuntime error for task %s", request.task_id)
            return WorkResult(
                task_id=request.task_id,
                success=False,
                output="",
                error=str(exc),
            )

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self._base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False
