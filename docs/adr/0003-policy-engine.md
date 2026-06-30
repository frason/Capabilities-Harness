# ADR 0003: Dedicated Policy Engine

## Status
Accepted

## Context

Early designs embedded merge policy, retry logic, concurrency limits, and routing rules directly in the Scheduler. This made the Scheduler responsible for both workflow execution and policy definition — two distinct concerns that change independently. Changing a policy required modifying scheduler code.

## Decision

Extract all configurable project behavior into a **dedicated Policy Engine** (`application/policy.py`).

The Policy Engine owns:
- **MergePolicy**: human (default) or auto
- **ApprovalPolicy**: required, optional, or skip
- **RetryPolicy**: max attempts, backoff, which exceptions trigger retry
- **RoutingPolicy**: prefer_local, provider_allowlist, max cost per task
- **ContextPolicy**: token budget, required memory layers
- **ConcurrencyPolicy**: max concurrent tasks

**The Scheduler executes policy. The Policy Engine defines it.**

The Policy Engine is loaded from `harness.toml` at startup and passed to the Scheduler, GraphExecutor, RoutingEngine, and MergeController as a read-only object. No subsystem mutates policy at runtime.

## Alternatives Considered

- **Config file only** (no Python object): rejected — too hard to compose and test
- **Keep policy in Scheduler**: rejected — violates single responsibility, makes testing harder

## Consequences

- Policy can be changed by editing `harness.toml` without touching framework code
- Each policy is testable in isolation
- Auditing "what policy was active when this task ran" is possible by capturing the PolicyEngine state in the task's telemetry
