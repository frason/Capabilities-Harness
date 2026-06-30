"""Cloud runtime for remote model provider execution.

TODO: route to Anthropic/OpenAI/etc via httpx. Provider SDK imports
live exclusively here — never imported outside infrastructure/runtime/.
"""
from __future__ import annotations

import logging

from capability_harness.domain.capability import CapabilitySpec, WorkRequest, WorkResult

logger = logging.getLogger(__name__)


class CloudRuntime:
    """Executes capabilities via cloud model providers."""

    def __init__(self, provider_name: str = "anthropic") -> None:
        self._provider = provider_name

    async def run(self, spec: CapabilitySpec, request: WorkRequest) -> WorkResult:
        logger.info(
            "CloudRuntime: would call '%s' via provider '%s' (stub)",
            spec.name,
            self._provider,
        )
        # TODO: build prompt from request.context + memory_layers,
        #       call provider SDK (kept private to this file),
        #       parse response into WorkResult.
        return WorkResult(
            task_id=request.task_id,
            success=True,
            output=f"[cloud-stub] '{spec.name}' via {self._provider} — not yet implemented",
        )
