"""Runtime protocol and provider registry.

The Runtime layer is the ONLY subsystem that knows about model providers.
Nothing outside infrastructure/runtime/ may import provider SDKs directly.

Capabilities request work via WorkRequest.
The Runtime performs that work and returns a WorkResult.
"""
from __future__ import annotations

from typing import Protocol

from capability_harness.domain.capability import CapabilitySpec, WorkRequest, WorkResult


class Runtime(Protocol):
    """Protocol for all runtime implementations."""

    async def run(self, spec: CapabilitySpec, request: WorkRequest) -> WorkResult: ...


class ProviderRegistry:
    """Registry of named Runtime implementations.

    The Routing Engine calls resolve() to get the Runtime selected for a task.
    Provider SDK imports live only in concrete Runtime implementations.
    """

    def __init__(self) -> None:
        self._runtimes: dict[str, Runtime] = {}

    def register(self, name: str, runtime: Runtime) -> None:
        self._runtimes[name] = runtime

    def resolve(self, name: str) -> Runtime:
        if name not in self._runtimes:
            raise KeyError(f"Runtime '{name}' not registered. Available: {list(self._runtimes)}")
        return self._runtimes[name]

    def list_runtimes(self) -> list[str]:
        return list(self._runtimes.keys())


class NoOpRuntime:
    """Stub runtime used during skeleton wiring and tests."""

    async def run(self, spec: CapabilitySpec, request: WorkRequest) -> WorkResult:
        return WorkResult(
            task_id=request.task_id,
            success=True,
            output=f"[noop] '{spec.name}' executed with no operation",
        )
