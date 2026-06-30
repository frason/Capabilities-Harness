"""Unit tests for the Capability Registry."""
import pytest

from capability_harness.application.registry import (
    CapabilityNotFoundError,
    CapabilityRegistry,
    NOOP_CAPABILITY,
)
from capability_harness.domain.capability import CapabilitySpec


def test_register_and_resolve():
    registry = CapabilityRegistry()
    registry.register(NOOP_CAPABILITY)
    spec = registry.resolve("noop")
    assert spec.name == "noop"


def test_duplicate_registration_raises():
    registry = CapabilityRegistry()
    registry.register(NOOP_CAPABILITY)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(NOOP_CAPABILITY)


def test_resolve_missing_raises():
    registry = CapabilityRegistry()
    with pytest.raises(CapabilityNotFoundError):
        registry.resolve("nonexistent")


def test_list_capabilities():
    registry = CapabilityRegistry()
    registry.register(NOOP_CAPABILITY)
    extra = CapabilitySpec(name="extra", description="extra capability")
    registry.register(extra)
    names = {s.name for s in registry.list_capabilities()}
    assert names == {"noop", "extra"}


def test_capability_spec_has_no_model_fields():
    """CapabilitySpec must never expose model or provider fields."""
    fields = set(CapabilitySpec.model_fields.keys())
    forbidden = {"model", "default_model", "provider", "api_key", "execution_preference"}
    assert fields.isdisjoint(forbidden), f"Forbidden fields found: {fields & forbidden}"
