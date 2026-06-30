"""Ollama model management — list downloaded models and pull new ones.

Provider details (Ollama REST API) are private to this module.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from datetime import datetime

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LocalModel(BaseModel):
    name: str
    size_bytes: int
    family: str
    parameter_size: str
    quantization: str
    modified_at: datetime


class PullProgress(BaseModel):
    status: str
    completed: int = 0
    total: int = 0

    @property
    def percent(self) -> float:
        return (self.completed / self.total * 100) if self.total else 0.0


class OllamaModelManager:
    """Manages local model discovery and downloads via Ollama API."""

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self._base_url = base_url.rstrip("/")

    async def is_running(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self._base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[LocalModel]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{self._base_url}/api/tags")
            r.raise_for_status()
        models = []
        for m in r.json().get("models", []):
            details = m.get("details", {})
            models.append(
                LocalModel(
                    name=m["name"],
                    size_bytes=m.get("size", 0),
                    family=details.get("family", "unknown"),
                    parameter_size=details.get("parameter_size", "unknown"),
                    quantization=details.get("quantization_level", "unknown"),
                    modified_at=datetime.fromisoformat(
                        m.get("modified_at", "1970-01-01T00:00:00Z").replace("Z", "+00:00")
                    ),
                )
            )
        return models

    async def pull_model(self, name: str) -> AsyncIterator[PullProgress]:
        import json

        async with httpx.AsyncClient(timeout=None) as client, client.stream(
            "POST",
            f"{self._base_url}/api/pull",
            json={"name": name, "stream": True},
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    yield PullProgress(
                        status=data.get("status", ""),
                        completed=data.get("completed", 0),
                        total=data.get("total", 0),
                    )
                except Exception:
                    logger.debug("Could not parse pull progress line: %s", line)
