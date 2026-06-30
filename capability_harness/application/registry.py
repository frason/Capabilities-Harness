"""Capability Registry — discovers and exposes declarative capability specs.

The registry knows only about metadata (CapabilitySpec).
It never knows about models, providers, or execution details.
"""
from __future__ import annotations

from capability_harness.domain.capability import (
    CapabilitySpec,
    MemoryLayerKind,
)


class CapabilityNotFoundError(Exception):
    """Raised when a capability name is not registered."""


class CapabilityRegistry:
    """In-memory registry of capability specs and optional Python implementations."""

    def __init__(self) -> None:
        self._specs: dict[str, CapabilitySpec] = {}
        self._impls: dict[str, object] = {}

    def register(self, spec: CapabilitySpec, impl: object = None) -> None:
        if spec.name in self._specs:
            raise ValueError(f"Capability '{spec.name}' is already registered.")
        self._specs[spec.name] = spec
        if impl is not None:
            self._impls[spec.name] = impl

    def resolve(self, name: str) -> CapabilitySpec:
        if name not in self._specs:
            raise CapabilityNotFoundError(
                f"Capability '{name}' not found. Registered: {list(self._specs)}"
            )
        return self._specs[name]

    def list_capabilities(self) -> list[CapabilitySpec]:
        return list(self._specs.values())

    def override_model(self, name: str, model_hint: str) -> None:
        """Allow the routing engine to attach a model hint without touching the spec."""
        # Model selection is stored separately — the spec itself never carries it
        self._impls[f"_model_hint:{name}"] = model_hint  # type: ignore[assignment]


# Built-in noop capability registered by default
NOOP_CAPABILITY = CapabilitySpec(
    name="noop",
    description="No-op capability for skeleton wiring and tests",
    required_memory=[MemoryLayerKind.TASK],
    produced_artifacts=[],
)
