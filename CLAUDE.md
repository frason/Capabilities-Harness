# Capability Harness — Repository Memory

This file is the **repository-layer memory** for AI capabilities working on this codebase.
It is read first, before any other context is loaded.

## Project Purpose

Capability Harness is a deterministic operating system for AI-assisted software engineering.
Deterministic software orchestrates work; AI performs reasoning only.

## Foundational Statements

> Capability Harness treats AI as a reasoning engine—not as the operating system.

> The framework owns process. Capabilities own reasoning. Models own inference. Providers own transport.

These statements govern every architectural boundary in this codebase.

## Module Map

| Package | Responsibility |
|---------|---------------|
| `domain/` | Pure business concepts: Task, Artifact, CapabilitySpec, DomainEvent. Zero I/O, no framework deps. |
| `application/` | Orchestration: Scheduler, GraphExecutor, PolicyEngine, RoutingEngine, CapabilityRegistry, MemoryContext, ValidationPipeline, RepositoryService. Depends on protocols, not concrete types. |
| `infrastructure/runtime/` | The ONLY place provider SDKs are imported. CloudRuntime, LocalRuntime, ProviderRegistry. |
| `infrastructure/persistence/` | State store and artifact store implementations. |
| `infrastructure/eventbus/` | InProcessEventBus — publish/subscribe for domain events. |
| `infrastructure/telemetry/` | TelemetryCollector, JSONFileExporter, BenchmarkCollector. |
| `infrastructure/git/` | GitRepository, WorktreeManager, DiffGenerator, MergeController — all via native subprocess. |
| `config/` | HarnessConfig schema, TOML loader, env var overrides. |
| `cli/` | `cap` CLI entry point and commands. Composition root lives in `cli/commands/task.py`. |

## Layering Rules

1. **`domain/`** imports nothing from this project.
2. **`application/`** imports `domain/` and uses `Protocol` for infrastructure dependencies.
3. **`infrastructure/`** imports `domain/` and `application/` protocols; provides concrete implementations.
4. **`cli/`** is the composition root — it wires concrete infrastructure into application interfaces.

**Never import a provider SDK outside `infrastructure/runtime/`.**

## Key Protocols

| Protocol | Location |
|----------|----------|
| `Runtime` | `infrastructure/runtime/provider_registry.py` |
| `StateStore` | `infrastructure/persistence/state_store.py` |
| `ArtifactStore` | `infrastructure/persistence/artifact_store.py` |
| `EventBus` | `infrastructure/eventbus/bus.py` |
| `RepositoryService` | `application/repository_service.py` |
| `ValidationStage` | `application/validation.py` |

## Capability Spec Format

Capabilities are declared in `capability.toml` files. **No model or provider fields — ever.**

```toml
[capability]
name = "my_capability"
required_memory = ["repository", "task"]
required_artifacts = ["requirements.md"]
produced_artifacts = ["patch.diff"]
validation_requirements = ["formatting", "lint", "unit_tests"]

[work_profile]
priority = "normal"
quality = "high"
latency_expectation = "relaxed"
cost_sensitivity = "balanced"
```

The Routing Engine reads `work_profile` to select a runtime. The capability never knows which one.

## Event Bus

Publish domain events from `domain/events.py`; never call subsystems directly.

```python
event_bus.publish(TaskStarted(task_id=task.id))
# NOT: telemetry_collector.on_task_started(task)
```

Subscribers (telemetry, CLI output, future automation) register independently.

## Architectural Pipeline

Every task flows: Scheduler → Capability Graph → Policy Engine → Routing Engine → Capability Registry → Runtime.

The Scheduler always calls `GraphExecutor.execute()`, even for single-node graphs.

## Testing Conventions

- Unit tests: `tests/unit/` — use `InMemoryStateStore`, `InProcessEventBus`, `NoOpRuntime`
- Integration tests: `tests/integration/` — may use real filesystem and git
- Async tests: use `pytest-asyncio` with `asyncio_mode = "auto"`
- Never mock the state machine transition rules — test with `InMemoryStateStore`

## CLI

Entry point: `cap` → `capability_harness.cli.app:app`

Commands: `cap task`, `cap capability`, `cap artifact`, `cap review`, `cap config`, `cap benchmark`
