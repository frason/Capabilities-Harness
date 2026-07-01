"""Runtime — thin executor that dispatches capabilities to the selected Provider.

The Runtime does not contain provider selection logic.
The Routing Engine selects the provider; the Runtime executes it.
Provider selection is expressed in WorkRequest.provider and resolved
through the ProviderRegistry.
"""
from __future__ import annotations

import logging

from capability_harness.domain.capability import CapabilitySpec, WorkRequest, WorkResult
from capability_harness.infrastructure.providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)


class Runtime:
    """Provider-agnostic capability executor.

    Accepts a WorkRequest whose .provider field names the provider to use.
    Resolves the provider from the registry and calls complete().
    Has no knowledge of any specific provider.
    """

    def __init__(self, provider_registry: ProviderRegistry) -> None:
        self._providers = provider_registry

    async def run(self, spec: CapabilitySpec, request: WorkRequest) -> WorkResult:
        provider_name = request.provider or "noop"
        logger.info(
            "runtime: executing '%s' via provider '%s' (task=%s)",
            spec.name,
            provider_name,
            request.task_id,
        )
        try:
            provider = self._providers.resolve(provider_name)
        except KeyError as exc:
            return WorkResult(
                task_id=request.task_id,
                success=False,
                output="",
                error=str(exc),
            )

        system_prompt = request.context or spec.description
        user_message = (
            f"Capability: {spec.name}\n"
            f"Task ID: {request.task_id}\n\n"
            + (
                f"Produced artifacts: {', '.join(a.value for a in spec.produced_artifacts)}\n\n"
                if spec.produced_artifacts
                else ""
            )
            + "Complete the capability task described in the system prompt."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            output = await provider.complete(messages)
            return WorkResult(
                task_id=request.task_id,
                success=True,
                output=output,
                metadata={"provider": provider_name, "capability": spec.name},
            )
        except Exception as exc:
            logger.exception(
                "provider '%s' failed for task %s", provider_name, request.task_id
            )
            return WorkResult(
                task_id=request.task_id,
                success=False,
                output="",
                error=str(exc),
            )
