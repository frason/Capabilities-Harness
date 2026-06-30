"""Validation Pipeline — ordered, fail-fast stage runner.

Stage list is driven by the capability spec's validation_requirements field.
Each stage is independent and produces a structured StageResult.
AIReview runs through the Capability Graph/Runtime like any other capability.
"""
from __future__ import annotations

import time
from typing import Any, Protocol

from pydantic import BaseModel

from capability_harness.domain.events import ValidationFailed, ValidationPassed
from capability_harness.domain.task import Task


class StageResult(BaseModel):
    stage: str
    passed: bool
    output: str = ""
    duration_seconds: float = 0.0
    error: str | None = None


class ValidationResult(BaseModel):
    passed: bool
    stages: list[StageResult]


class ValidationStage(Protocol):
    """Protocol for a single validation stage."""

    name: str

    def run(self, task: Task, artifacts: list[Any], workspace: str) -> StageResult: ...


class ValidationPipeline:
    """Runs validation stages in order, optionally short-circuiting on failure."""

    def __init__(
        self,
        stages: list[ValidationStage],
        fail_fast: bool = True,
        event_bus: Any | None = None,
    ) -> None:
        self._stages = stages
        self._fail_fast = fail_fast
        self._bus = event_bus

    def run(
        self, task: Task, artifacts: list[Any], workspace: str
    ) -> ValidationResult:
        results: list[StageResult] = []
        for stage in self._stages:
            start = time.monotonic()
            try:
                result = stage.run(task, artifacts, workspace)
            except Exception as exc:
                result = StageResult(
                    stage=stage.name,
                    passed=False,
                    error=str(exc),
                    duration_seconds=time.monotonic() - start,
                )
            results.append(result)

            if self._bus:
                if result.passed:
                    self._bus.publish(ValidationPassed(task_id=task.id, stage=stage.name))
                else:
                    self._bus.publish(
                        ValidationFailed(
                            task_id=task.id,
                            stage=stage.name,
                            error=result.error or result.output,
                        )
                    )

            if not result.passed and self._fail_fast:
                break

        return ValidationResult(
            passed=all(r.passed for r in results),
            stages=results,
        )
