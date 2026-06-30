"""Domain model for Capability specifications and work contracts."""
from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

from capability_harness.domain.artifact import ArtifactKind


class MemoryLayerKind(StrEnum):
    """The five memory layers available to a Capability."""

    REPOSITORY = "repository"
    ARCHITECTURE = "architecture"
    PROJECT = "project"
    TASK = "task"
    SCRATCHPAD = "scratchpad"


class WorkProfile(BaseModel):
    """Hints to the Routing Engine about how a Capability should be scheduled."""

    priority: Literal["low", "normal", "high"] = "normal"
    quality: Literal["draft", "standard", "high"] = "standard"
    latency_expectation: Literal["interactive", "relaxed", "batch"] = "relaxed"
    cost_sensitivity: Literal["cost_optimized", "balanced", "quality_optimized"] = "balanced"


class CapabilitySpec(BaseModel):
    """Declarative specification for a Capability registered in the harness."""

    name: str
    version: str = "0.1.0"
    description: str
    required_memory: list[MemoryLayerKind] = Field(default_factory=list)
    required_artifacts: list[ArtifactKind] = Field(default_factory=list)
    produced_artifacts: list[ArtifactKind] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    validation_requirements: list[str] = Field(default_factory=list)
    work_profile: WorkProfile = Field(default_factory=WorkProfile)
    tags: list[str] = Field(default_factory=list)


class WorkRequest(BaseModel):
    """The input contract passed to a Capability at execution time."""

    task_id: str
    spec: CapabilitySpec
    context: str
    artifacts: list[str] = Field(default_factory=list)
    memory_layers: list[str] = Field(default_factory=list)


class WorkResult(BaseModel):
    """The output contract returned by a Capability after execution."""

    task_id: str
    success: bool
    output: str = ""
    artifacts: list[str] = Field(default_factory=list)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
