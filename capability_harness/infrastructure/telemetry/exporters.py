"""Telemetry exporters — write span data to structured outputs."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class SpanRecord(BaseModel):
    """A single telemetry span."""

    span_id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: str
    name: str
    started_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    duration_ms: float = 0.0
    attributes: dict[str, Any] = Field(default_factory=dict)


class JSONFileExporter:
    """Appends spans as newline-delimited JSON to {output_dir}/{task_id}/telemetry.json."""

    def __init__(self, output_dir: str = ".harness/artifacts") -> None:
        self._root = Path(output_dir)

    def export(self, span: SpanRecord, task_id: str) -> None:
        task_dir = self._root / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        telemetry_path = task_dir / "telemetry.json"
        with telemetry_path.open("a") as f:
            f.write(span.model_dump_json() + "\n")
