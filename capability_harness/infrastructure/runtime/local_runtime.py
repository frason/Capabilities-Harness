"""Local runtime for on-device capability execution.

TODO: invoke local LLMs (Ollama, llama.cpp), Python functions, and
shell commands. Provider details stay private to this module.
"""
from __future__ import annotations

import logging

from capability_harness.domain.capability import CapabilitySpec, WorkRequest, WorkResult

logger = logging.getLogger(__name__)


class LocalRuntime:
    """Executes capabilities using local compute resources."""

    async def run(self, spec: CapabilitySpec, request: WorkRequest) -> WorkResult:
        logger.info("LocalRuntime: would run '%s' locally (stub)", spec.name)
        # TODO: route to Ollama/llama.cpp based on work_profile.quality
        return WorkResult(
            task_id=request.task_id,
            success=True,
            output=f"[local-stub] '{spec.name}' — local runtime not yet implemented",
        )
