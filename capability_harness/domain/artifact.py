"""Domain model for Artifacts — immutable outputs produced by Capabilities."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ArtifactKind(StrEnum):
    """Well-known artifact kinds produced by the pipeline."""

    REQUIREMENTS = "requirements.md"
    ARCHITECTURE = "architecture.md"
    IMPLEMENTATION_PLAN = "implementation_plan.json"
    PATCH = "patch.diff"
    TEST_REPORT = "test_report.json"
    REVIEW = "review.md"
    TELEMETRY = "telemetry.json"


class Artifact(BaseModel):
    """An immutable, content-addressed output produced by a Capability."""

    id: str  # sha256 of content
    kind: ArtifactKind
    task_id: str
    path: str
    size_bytes: int
    created_at: datetime
    content_hash: str
    metadata: dict[str, Any] = Field(default_factory=dict)
