"""Configuration loader — reads harness.toml and applies env var overrides."""
from __future__ import annotations

import os
import tomllib
from pathlib import Path

from capability_harness.config.defaults import DEFAULT_CONFIG_PATH
from capability_harness.config.schema import HarnessConfig


class ConfigNotFoundError(Exception):
    """Raised when the config file does not exist."""


class ConfigValidationError(Exception):
    """Raised when the config file fails schema validation."""


def load_config(path: str = DEFAULT_CONFIG_PATH) -> HarnessConfig:
    """Load and validate configuration from a TOML file with env var overrides.

    Environment variable overrides use the CH_ prefix with __ as separator:
      CH_STATE__DATABASE_URL, CH_ARTIFACTS__ROOT_PATH,
      CH_TELEMETRY__ENABLED, CH_POLICY__MERGE, etc.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigNotFoundError(
            f"Configuration file not found: {config_path}. "
            "Run `cap config validate` to check your setup."
        )

    with config_path.open("rb") as f:
        raw = tomllib.load(f)

    # Apply CH_ env var overrides
    _apply_env_overrides(raw)

    try:
        return HarnessConfig.model_validate(raw)
    except Exception as exc:
        raise ConfigValidationError(f"Invalid configuration in {config_path}: {exc}") from exc


def _apply_env_overrides(data: dict) -> None:  # type: ignore[type-arg]
    """Mutate data dict with CH_SECTION__KEY=value overrides."""
    prefix = "CH_"
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        parts = key[len(prefix):].lower().split("__")
        target = data
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = _coerce(value)


def _coerce(value: str) -> bool | int | str:
    """Coerce string env var values to appropriate Python types."""
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    try:
        return int(value)
    except ValueError:
        return value
