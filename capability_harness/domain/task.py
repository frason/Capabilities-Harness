"""Domain model for Tasks — the unit of work in Capability Harness."""
from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskState(StrEnum):
    """Lifecycle states a Task can occupy."""

    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    VALIDATION = "validation"
    REVIEW = "review"
    APPROVED = "approved"
    MERGED = "merged"
    ARCHIVED = "archived"
    FAILED = "failed"
    CANCELLED = "cancelled"


VALID_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.CREATED: {TaskState.READY, TaskState.CANCELLED},
    TaskState.READY: {TaskState.RUNNING, TaskState.CANCELLED},
    TaskState.RUNNING: {TaskState.VALIDATION, TaskState.FAILED},
    TaskState.VALIDATION: {TaskState.REVIEW, TaskState.RUNNING, TaskState.FAILED},
    TaskState.REVIEW: {TaskState.APPROVED, TaskState.RUNNING},
    TaskState.APPROVED: {TaskState.MERGED},
    TaskState.MERGED: {TaskState.ARCHIVED},
    TaskState.FAILED: {TaskState.READY},
    TaskState.CANCELLED: set(),
    TaskState.ARCHIVED: set(),
}


class TaskPriority(StrEnum):
    """Scheduling priority for a Task."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Task(BaseModel):
    """A single unit of work routed through the Capability Harness pipeline."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    capability_name: str
    state: TaskState = TaskState.CREATED
    priority: TaskPriority = TaskPriority.NORMAL
    depends_on: list[str] = Field(default_factory=list)
    input_artifacts: list[str] = Field(default_factory=list)
    output_artifacts: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    retry_count: int = 0
    error: str | None = None
    graph_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
