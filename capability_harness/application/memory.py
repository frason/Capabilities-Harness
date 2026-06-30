"""Memory Layer — assembles context for capability execution.

Consumes RepositoryService for repository-layer data.
Respects token budgets from ContextPolicy.
Capabilities declare required_memory in their spec; only those layers are loaded.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from capability_harness.domain.capability import MemoryLayerKind
from capability_harness.domain.task import Task


class MemoryLayer(BaseModel):
    """A single loaded memory layer with content and metadata."""

    kind: MemoryLayerKind
    content: str
    token_estimate: int
    source_path: str | None = None


class MemoryContext:
    """Assembles memory layers for a task, respecting the token budget."""

    def assemble(
        self,
        task: Task,
        kinds: list[MemoryLayerKind],
        budget: int,
        repo_service: Any,
    ) -> list[MemoryLayer]:
        """Load requested memory layers in priority order, trimming to fit budget.

        Layers are ordered lowest-to-highest specificity:
        Repository → Architecture → Project → Task → Scratchpad

        When the budget is exceeded, lower-priority layers are trimmed first.
        TODO: implement actual layer loading from filesystem and repo_service.
        """
        layers: list[MemoryLayer] = []
        remaining_budget = budget

        priority_order = [
            MemoryLayerKind.REPOSITORY,
            MemoryLayerKind.ARCHITECTURE,
            MemoryLayerKind.PROJECT,
            MemoryLayerKind.TASK,
            MemoryLayerKind.SCRATCHPAD,
        ]
        ordered_kinds = [k for k in priority_order if k in kinds]

        for kind in ordered_kinds:
            content = self._load_layer(kind, task, repo_service)
            tokens = self._estimate_tokens(content)
            if tokens > remaining_budget:
                # Trim content to fit
                max_chars = remaining_budget * 4
                content = content[:max_chars]
                tokens = self._estimate_tokens(content)
            if tokens > 0:
                layers.append(MemoryLayer(kind=kind, content=content, token_estimate=tokens))
                remaining_budget -= tokens

        return layers

    def _load_layer(
        self, kind: MemoryLayerKind, task: Task, repo_service: Any
    ) -> str:
        """Load content for a memory layer. Stub returns empty string."""
        if kind == MemoryLayerKind.REPOSITORY:
            # TODO: read CLAUDE.md from repo root via repo_service
            return ""
        if kind == MemoryLayerKind.TASK:
            return f"Task ID: {task.id}\nCapability: {task.capability_name}\nState: {task.state}"
        return ""

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Approximate token count at 4 characters per token."""
        return len(text) // 4
