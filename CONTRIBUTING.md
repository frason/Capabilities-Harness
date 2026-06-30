# Contributing to Capability Harness

Thank you for your interest in contributing. This guide covers everything you need to get started.

## Prerequisites

- Python 3.12 or later
- A virtual environment manager (venv, pyenv, or uv)

Install the project in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

## Code Standards

All code must pass the following checks before merging.

### Linting and formatting

We use [ruff](https://docs.astral.sh/ruff/) for both linting and formatting:

```bash
ruff check .
ruff format .
```

### Type checking

We use [mypy](https://mypy.readthedocs.io/) in strict mode:

```bash
mypy capability_harness --strict --ignore-missing-imports
```

New code must not introduce mypy errors. `type: ignore` comments require a justification comment on the same line.

## Running Tests

Run the unit test suite:

```bash
pytest tests/unit
```

Run with verbose output and stop on first failure:

```bash
pytest tests/unit -xvs
```

Run the full test suite (including integration tests, which may require external services):

```bash
pytest tests/
```

## Pull Request Process

- Keep PRs small and focused — one logical change per PR.
- Use descriptive commit messages that explain the _why_, not just the _what_.
- Squash fixup commits before requesting review when practical.
- All CI checks must pass before a PR can be merged.
- At least one maintainer approval is required.

## Writing a Capability

Capabilities are the primary extension point for Capability Harness. To add a new capability:

1. Read `docs/capabilities.md` for the full specification and interface contract.
2. Create a module under `capability_harness/capabilities/`.
3. Implement the `Capability` protocol defined in `capability_harness/domain/capability.py`.
4. Register your capability via the `capability_harness.capabilities` entry point in your own package's `pyproject.toml`, or by adding it to the built-in registry for capabilities that belong in core.
5. Write unit tests under `tests/unit/capabilities/`.

## Architectural Decision Records (ADRs)

Significant architectural decisions should be documented as ADRs. To record a decision:

1. Create a new file in `docs/adr/` using the naming convention `NNNN-short-title.md` (e.g. `0002-use-sqlmodel-for-orm.md`).
2. Use the template in `docs/adr/0001-record-architecture-decisions.md` as a starting point.
3. Include the decision's context, the options considered, the decision made, and the consequences.

ADRs are append-only — do not edit a superseded ADR. Instead, write a new ADR that references the old one.
