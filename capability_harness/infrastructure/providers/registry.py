"""Provider Registry — registers and resolves inference providers by name.

The Runtime requests providers from this registry.
It never instantiates providers directly.
"""
from __future__ import annotations

from capability_harness.infrastructure.providers.protocol import Provider


class ProviderRegistry:
    """Registry of named Provider implementations.

    Providers are registered at composition root startup and resolved by name
    at execution time. The Runtime holds a reference to this registry.
    """

    def __init__(self) -> None:
        self._providers: dict[str, Provider] = {}

    def register(self, name: str, provider: Provider) -> None:
        self._providers[name] = provider

    def resolve(self, name: str) -> Provider:
        if name not in self._providers:
            available = list(self._providers)
            raise KeyError(
                f"Provider '{name}' not registered. Available: {available}. "
                "Check your [providers] config and composition root."
            )
        return self._providers[name]

    def list_providers(self) -> list[str]:
        return list(self._providers)

    def is_registered(self, name: str) -> bool:
        return name in self._providers
