# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - Unreleased

### Added

- Initial skeleton implementation of Capability Harness.
- Project configuration: `pyproject.toml` with hatchling build backend, ruff, mypy, and pytest settings.
- CI workflow (GitHub Actions) running lint, format check, type check, and unit tests on every push and pull request.
- Layered package structure: `domain`, `application`, `infrastructure`, `cli`, and `capabilities` modules.
- `cap` CLI entry point wired to `capability_harness.cli.app`.
- Built-in `noop` capability for end-to-end pipeline smoke testing.
- Entry-point group `capability_harness.capabilities` for third-party capability registration.
- Developer documentation: `CONTRIBUTING.md`, `DEVELOPMENT.md`, and this `CHANGELOG.md`.
- MIT license.

[Unreleased]: https://github.com/capability-harness/capability-harness/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/capability-harness/capability-harness/releases/tag/v0.1.0
