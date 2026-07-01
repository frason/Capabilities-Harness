"""Configuration schema for Capability Harness."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from capability_harness.application.policy import (
    ApprovalPolicy,
    ConcurrencyPolicy,
    ContextPolicy,
    MergePolicy,
    PolicyEngine,
    RetryPolicy,
    RoutingPolicy,
)
from capability_harness.config.defaults import DEFAULT_ARTIFACTS_PATH, DEFAULT_STATE_DB


class StateConfig(BaseModel):
    database_url: str = DEFAULT_STATE_DB


class ArtifactConfig(BaseModel):
    root_path: str = DEFAULT_ARTIFACTS_PATH
    hash_algorithm: str = "sha256"


class PolicyConfig(BaseModel):
    merge: MergePolicy = MergePolicy.HUMAN
    approval: ApprovalPolicy = ApprovalPolicy.REQUIRED
    retry: RetryPolicy = RetryPolicy()
    routing: RoutingPolicy = RoutingPolicy()
    context: ContextPolicy = ContextPolicy()
    concurrency: ConcurrencyPolicy = ConcurrencyPolicy()


class TelemetryConfig(BaseModel):
    enabled: bool = True
    exporter: Literal["json", "otlp", "none"] = "json"
    otlp_endpoint: str | None = None


class ValidationConfig(BaseModel):
    stages: list[str] = ["formatting", "lint", "typecheck", "unit_tests", "ai_review"]
    fail_fast: bool = True


class ProviderConfig(BaseModel):
    """Configuration for a single inference provider."""

    model: str = ""
    base_url: str = ""          # for Ollama/OpenAI-compatible servers
    api_key: str = ""           # leave blank to read from env var
    timeout_seconds: int = 120
    max_tokens: int = 8096


class ProfileConfig(BaseModel):
    """Benchmark profile — maps capability names to provider names.

    Changing execution providers requires only changing this config block.
    No orchestration code changes when switching between profiles.
    """

    # Maps capability_name → provider_name
    # e.g. {"planner": "anthropic", "coder": "ollama", "review": "anthropic"}
    assignments: dict[str, str] = Field(default_factory=dict)
    default_provider: str = "noop"


class HarnessConfig(BaseModel):
    state: StateConfig = StateConfig()
    artifacts: ArtifactConfig = ArtifactConfig()
    policy: PolicyConfig = PolicyConfig()
    telemetry: TelemetryConfig = TelemetryConfig()
    validation: ValidationConfig = ValidationConfig()

    # Provider configurations — one entry per registered provider
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)

    # Named benchmark profiles — select one at runtime via CH_ACTIVE_PROFILE env var
    profiles: dict[str, ProfileConfig] = Field(default_factory=dict)

    # Active profile name (resolved at startup)
    active_profile: str = "quality"

    def to_policy_engine(self) -> PolicyEngine:
        return PolicyEngine(
            merge=self.policy.merge,
            approval=self.policy.approval,
            retry=self.policy.retry,
            routing=self.policy.routing,
            context=self.policy.context,
            concurrency=self.policy.concurrency,
        )

    def active_profile_config(self) -> ProfileConfig:
        return self.profiles.get(self.active_profile, ProfileConfig())
