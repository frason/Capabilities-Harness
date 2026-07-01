"""Routing Engine — selects the Provider for a capability execution.

The Routing Engine is the decision layer between Policy and Runtime.
It returns a provider name (string); the Runtime resolves and calls that provider.
No provider selection logic exists inside Runtime — it lives here.

Decision inputs (in priority order):
1. Active benchmark profile (maps capability name → provider name)
2. Provider allowlist from policy
3. WorkProfile hints (cost_sensitivity, quality, latency_expectation)
4. Fallback to default_provider from config
"""
from __future__ import annotations

import logging

from capability_harness.application.policy import PolicyEngine
from capability_harness.domain.capability import CapabilitySpec

logger = logging.getLogger(__name__)


class RoutingEngine:
    """Selects a provider name based on capability, profile, and active policy."""

    def __init__(
        self,
        policy: PolicyEngine,
        default_provider: str = "noop",
        profile: dict[str, str] | None = None,
        registered_providers: list[str] | None = None,
    ) -> None:
        self._policy = policy
        self._default_provider = default_provider
        # profile maps capability_name → provider_name, e.g. {"coder": "anthropic"}
        self._profile: dict[str, str] = profile or {}
        self._registered = set(registered_providers or [])

    def select_provider(self, spec: CapabilitySpec) -> str:
        """Return the provider name that should execute this capability.

        The Runtime will use this name to resolve the Provider from its registry.
        """
        work_profile = spec.work_profile

        # 1. Explicit profile assignment overrides everything
        if spec.name in self._profile:
            provider = self._profile[spec.name]
            logger.debug("routing '%s' → '%s' (profile assignment)", spec.name, provider)
            return provider

        # 2. WorkProfile quality hint: high quality → prefer non-noop provider
        if work_profile.quality == "high" and "anthropic" in self._registered:
            logger.debug("routing '%s' → 'anthropic' (quality=high)", spec.name)
            return "anthropic"

        # 3. Cost-optimized → prefer local
        if work_profile.cost_sensitivity == "cost_optimized" and "ollama" in self._registered:
            logger.debug("routing '%s' → 'ollama' (cost_optimized)", spec.name)
            return "ollama"

        # 4. Default provider from config
        logger.debug("routing '%s' → '%s' (default)", spec.name, self._default_provider)
        return self._default_provider

    # Keep backward-compatible shim for existing callers (GraphExecutor used select_runtime)
    def select_runtime(self, spec: CapabilitySpec) -> str:
        return self.select_provider(spec)
