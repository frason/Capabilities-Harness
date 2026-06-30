"""Telemetry collector — instruments every capability execution.

Subscribes to domain events from the event bus rather than being called directly.
TODO: replace timing stubs with OpenTelemetry TracerProvider.
"""
from __future__ import annotations

import logging
import time
from collections.abc import Generator
from contextlib import contextmanager

from capability_harness.domain.events import (
    CapabilityCompleted,
    CapabilityStarted,
    TaskCompleted,
    TaskFailed,
    TaskStarted,
    ValidationFailed,
    ValidationPassed,
)
from capability_harness.infrastructure.eventbus.bus import InProcessEventBus
from capability_harness.infrastructure.telemetry.exporters import JSONFileExporter, SpanRecord

logger = logging.getLogger(__name__)


class TelemetryCollector:
    """Collects timing and token data for every task execution."""

    def __init__(
        self,
        enabled: bool = True,
        output_dir: str = ".harness/artifacts",
        event_bus: InProcessEventBus | None = None,
    ) -> None:
        self._enabled = enabled
        self._exporter = JSONFileExporter(output_dir)
        if event_bus and enabled:
            self._wire_event_bus(event_bus)

    def _wire_event_bus(self, bus: InProcessEventBus) -> None:
        bus.subscribe(TaskStarted, self._on_task_started)
        bus.subscribe(TaskCompleted, self._on_task_completed)
        bus.subscribe(TaskFailed, self._on_task_failed)
        bus.subscribe(CapabilityStarted, self._on_capability_started)
        bus.subscribe(CapabilityCompleted, self._on_capability_completed)
        bus.subscribe(ValidationPassed, self._on_validation_passed)
        bus.subscribe(ValidationFailed, self._on_validation_failed)

    def _on_task_started(self, event: TaskStarted) -> None:
        logger.debug("telemetry: task %s started", event.task_id)

    def _on_task_completed(self, event: TaskCompleted) -> None:
        logger.debug("telemetry: task %s completed success=%s", event.task_id, event.success)

    def _on_task_failed(self, event: TaskFailed) -> None:
        logger.debug("telemetry: task %s failed: %s", event.task_id, event.error)

    def _on_capability_started(self, event: CapabilityStarted) -> None:
        logger.debug("telemetry: capability %s started for task %s", event.capability_name, event.task_id)

    def _on_capability_completed(self, event: CapabilityCompleted) -> None:
        logger.debug("telemetry: capability %s completed", event.capability_name)

    def _on_validation_passed(self, event: ValidationPassed) -> None:
        logger.debug("telemetry: validation stage %s passed", event.stage)

    def _on_validation_failed(self, event: ValidationFailed) -> None:
        logger.debug("telemetry: validation stage %s FAILED: %s", event.stage, event.error)

    @contextmanager
    def task_span(self, task_id: str) -> Generator[None, None, None]:
        if not self._enabled:
            yield
            return
        start = time.monotonic()
        try:
            yield
        finally:
            duration_ms = (time.monotonic() - start) * 1000
            span = SpanRecord(task_id=task_id, name=f"task:{task_id}", duration_ms=duration_ms)
            self._exporter.export(span, task_id)

    @contextmanager
    def stage_span(self, task_id: str, name: str) -> Generator[None, None, None]:
        if not self._enabled:
            yield
            return
        start = time.monotonic()
        try:
            yield
        finally:
            duration_ms = (time.monotonic() - start) * 1000
            span = SpanRecord(task_id=task_id, name=f"stage:{name}", duration_ms=duration_ms)
            self._exporter.export(span, task_id)

    def record_model_call(
        self,
        task_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
    ) -> None:
        if not self._enabled:
            return
        span = SpanRecord(
            task_id=task_id,
            name="model_call",
            duration_ms=latency_ms,
            attributes={
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        )
        self._exporter.export(span, task_id)
        logger.debug(
            "model_call model=%s in=%d out=%d latency=%.1fms",
            model, input_tokens, output_tokens, latency_ms,
        )
