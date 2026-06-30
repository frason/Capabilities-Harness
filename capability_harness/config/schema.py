"""Configuration schema for Capability Harness."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

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


class LocalRuntimeConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    default_model: str = "mistral"
    timeout_seconds: int = 120
    provider: Literal["ollama", "llama_cpp", "lm_studio"] = "ollama"


class HarnessConfig(BaseModel):
    state: StateConfig = StateConfig()
    artifacts: ArtifactConfig = ArtifactConfig()
    policy: PolicyConfig = PolicyConfig()
    telemetry: TelemetryConfig = TelemetryConfig()
    validation: ValidationConfig = ValidationConfig()
    local_runtime: LocalRuntimeConfig = LocalRuntimeConfig()

    def to_policy_engine(self) -> PolicyEngine:
        return PolicyEngine(
            merge=self.policy.merge,
            approval=self.policy.approval,
            retry=self.policy.retry,
            routing=self.policy.routing,
            context=self.policy.context,
            concurrency=self.policy.concurrency,
        )
