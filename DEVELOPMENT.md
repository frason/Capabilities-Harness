# Development Guide

This guide covers local setup, running the project, and understanding the architecture.

## Setup

Clone the repository and install in editable mode with development dependencies:

```bash
git clone <repo-url>
cd capability-harness
pip install -e ".[dev]"
```

Verify the CLI is available:

```bash
cap --help
```

## Running the Skeleton End-to-End

The `noop` capability is a built-in that does nothing — it exists to exercise the full pipeline without side effects:

```bash
cap task submit --capability noop
```

You should see the task accepted, routed through the pipeline, and completed with a success status. This confirms that the Scheduler, Graph, Policy, Routing, Registry, and Runtime layers are all wired correctly.

## Running CI Checks Locally

Run all checks in the same order as CI:

```bash
ruff check .
ruff format --check .
mypy capability_harness --strict --ignore-missing-imports
pytest tests/unit -x
```

To auto-fix lint and format issues before committing:

```bash
ruff check --fix .
ruff format .
```

## Project Structure

The codebase follows a layered architecture inspired by Domain-Driven Design:

```
capability_harness/
  domain/           # Pure domain models and protocols — no I/O, no frameworks
  application/      # Use cases and orchestration — coordinates domain objects
  infrastructure/   # Adapters: database, HTTP, scheduling, telemetry
  cli/              # Typer-based CLI entry point
  capabilities/     # Built-in capability implementations

tests/
  unit/             # Fast, isolated tests — no external dependencies
  integration/      # Tests that require a real database, network, etc.

docs/
  adr/              # Architectural Decision Records
  capabilities.md   # Capability interface specification
```

### Layer Rules

- `domain` must not import from `application` or `infrastructure`.
- `application` may import from `domain`, but not from `infrastructure` directly — it depends on interfaces (protocols) that infrastructure implements.
- `infrastructure` may import from both `domain` and `application`.
- `cli` is a thin adapter — it parses input and delegates to `application`.

## Architectural Pipeline

A task moves through the following stages when submitted:

```
Scheduler
    |
    v
Graph          -- resolves capability dependencies and execution order
    |
    v
Policy         -- applies access control and quota checks
    |
    v
Routing        -- selects the target runtime based on capability metadata
    |
    v
Registry       -- looks up the registered capability implementation
    |
    v
Runtime        -- executes the capability and captures the result
```

Each stage is an independent component that can be tested and replaced in isolation. The pipeline is assembled in `capability_harness/application/pipeline.py`.
