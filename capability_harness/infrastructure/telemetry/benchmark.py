"""Benchmarking — aggregate execution metrics across tasks."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class BenchmarkRecord(BaseModel):
    """Per-task benchmark metrics."""

    task_id: str
    capability: str
    wall_clock_ms: float = 0.0
    ai_time_ms: float = 0.0
    deterministic_time_ms: float = 0.0
    human_time_ms: float = 0.0
    cloud_tokens: int = 0
    local_tokens: int = 0
    avg_context_size: int = 0
    retry_count: int = 0
    validation_failures: int = 0
    artifacts_produced: int = 0
    estimated_cost_usd: float = 0.0
    success: bool = False


class BenchmarkCollector:
    """Accumulates BenchmarkRecords and computes aggregate statistics."""

    def __init__(self) -> None:
        self._records: list[BenchmarkRecord] = []

    def record(self, entry: BenchmarkRecord) -> None:
        self._records.append(entry)

    def summarize(self) -> dict[str, Any]:
        if not self._records:
            return {"total_tasks": 0}
        total = len(self._records)
        successes = sum(1 for r in self._records if r.success)
        return {
            "total_tasks": total,
            "success_rate": successes / total,
            "avg_wall_clock_ms": sum(r.wall_clock_ms for r in self._records) / total,
            "avg_ai_time_ms": sum(r.ai_time_ms for r in self._records) / total,
            "avg_deterministic_time_ms": sum(r.deterministic_time_ms for r in self._records) / total,
            "total_cloud_tokens": sum(r.cloud_tokens for r in self._records),
            "total_local_tokens": sum(r.local_tokens for r in self._records),
            "avg_context_size": sum(r.avg_context_size for r in self._records) / total,
            "total_retries": sum(r.retry_count for r in self._records),
            "total_validation_failures": sum(r.validation_failures for r in self._records),
            "total_artifacts_produced": sum(r.artifacts_produced for r in self._records),
            "total_estimated_cost_usd": sum(r.estimated_cost_usd for r in self._records),
        }
