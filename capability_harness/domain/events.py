"""Domain events emitted by the Capability Harness pipeline."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(UTC)


class DomainEvent(BaseModel):
    """Base class for all domain events."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = Field(default_factory=_utcnow)


class TaskCreated(DomainEvent):
    """Emitted when a new Task is created."""

    task_id: str
    capability_name: str


class TaskStarted(DomainEvent):
    """Emitted when a Task transitions to the RUNNING state."""

    task_id: str


class TaskCompleted(DomainEvent):
    """Emitted when a Task finishes execution (success or failure)."""

    task_id: str
    success: bool


class TaskFailed(DomainEvent):
    """Emitted when a Task enters the FAILED state."""

    task_id: str
    error: str


class CapabilityStarted(DomainEvent):
    """Emitted when a Capability begins executing within a graph node."""

    task_id: str
    capability_name: str


class CapabilityCompleted(DomainEvent):
    """Emitted when a Capability finishes executing within a graph node."""

    task_id: str
    capability_name: str
    success: bool


class ValidationPassed(DomainEvent):
    """Emitted when a validation stage passes."""

    task_id: str
    stage: str


class ValidationFailed(DomainEvent):
    """Emitted when a validation stage fails."""

    task_id: str
    stage: str
    error: str


class ArtifactCreated(DomainEvent):
    """Emitted when a new Artifact is written to the store."""

    task_id: str
    artifact_kind: str
    artifact_id: str


class ReviewCompleted(DomainEvent):
    """Emitted when a human or automated review concludes."""

    task_id: str
    approved: bool


class MergeApproved(DomainEvent):
    """Emitted when a merge is approved and initiated."""

    task_id: str
    branch: str
