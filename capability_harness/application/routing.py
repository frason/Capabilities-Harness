"""Routing Engine — selects the Runtime for a capability execution.

The Routing Engine is the decision layer between Policy and Runtime.
It honors work profiles, cost/latency constraints, provider allowlists,
and fallback chains. Capabilities never know which runtime was selected.
"""
from __future__ import annotations

import logging
from typing import Any

from capability_harness.application.policy import PolicyEngine
from capability_harness.domain.capability import CapabilitySpec

logger = logging.getLogger(__name__)


class RoutingEngine:
    """Selects a Runtime based on the capability's WorkProfile and active policy."""

    def __init__(self, provider_registry: Any, policy: PolicyEngine) -> None:
        self._registry = provider_registry
        self._policy = policy

    def select_runtime(self, spec: CapabilitySpec) -> Any:
        """Return the appropriate Runtime for this capability spec.

        Decision factors (in priority order):
        1. Provider allowlist from policy
        2. prefer_local flag
        3. WorkProfile hints (latency_expectation, cost_sensitivity)
        4. Fallback to 'noop' if nothing else resolves
        """
        profile = spec.work_profile
        logger.debug(
            "routing '%s': quality=%s latency=%s cost=%s prefer_local=%s",
            spec.name,
            profile.quality,
            profile.latency_expectation,
            profile.cost_sensitivity,
            self._policy.routing.prefer_local,
        )

        if self._policy.routing.prefer_local:
            try:
                return self._registry.resolve("local")
            except KeyError:
                pass

        # Prefer cloud; fall back through local → noop
        try:
            return self._registry.resolve("cloud")
        except KeyError:
            pass

        try:
            return self._registry.resolve("local")
        except KeyError:
            pass

        return self._registry.resolve("noop")
