"""Policy Engine — defines all configurable project behavior.

The Scheduler executes policy; it never defines it.
All project-level behavioral decisions live here.
"""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class MergePolicy(StrEnum):
    HUMAN = "human"
    AUTO = "auto"


class ApprovalPolicy(StrEnum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    SKIP = "skip"


class RetryPolicy(BaseModel):
    max_attempts: int = 3
    backoff_seconds: float = 2.0
    retry_on: list[str] = ["RuntimeError"]


class RoutingPolicy(BaseModel):
    prefer_local: bool = False
    provider_allowlist: list[str] = []
    max_cost_per_task: float | None = None


class ContextPolicy(BaseModel):
    token_budget: int = 100_000
    required_layers: list[str] = ["repository", "task"]


class ConcurrencyPolicy(BaseModel):
    max_concurrent_tasks: int = 4


class PolicyEngine(BaseModel):
    """The single source of truth for all configurable project behavior."""

    merge: MergePolicy = MergePolicy.HUMAN
    approval: ApprovalPolicy = ApprovalPolicy.REQUIRED
    retry: RetryPolicy = RetryPolicy()
    routing: RoutingPolicy = RoutingPolicy()
    context: ContextPolicy = ContextPolicy()
    concurrency: ConcurrencyPolicy = ConcurrencyPolicy()
