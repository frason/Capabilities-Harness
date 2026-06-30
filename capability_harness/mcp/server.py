"""MCP server exposing Capability Harness tools to Claude Code.

Register this server in .mcp.json so Claude can call these tools directly.
The server wires the same composition root as the CLI — it calls Python APIs,
never shells out to `cap`.
"""
from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from capability_harness.application.graph import NOOP_GRAPH, GraphExecutor
from capability_harness.application.policy import PolicyEngine
from capability_harness.application.registry import NOOP_CAPABILITY, CapabilityRegistry
from capability_harness.application.routing import RoutingEngine
from capability_harness.application.scheduler import HarnessScheduler
from capability_harness.domain.artifact import ArtifactKind
from capability_harness.domain.task import Task, TaskState
from capability_harness.infrastructure.eventbus.bus import InProcessEventBus
from capability_harness.infrastructure.persistence.artifact_store import LocalArtifactStore
from capability_harness.infrastructure.persistence.state_store import InMemoryStateStore
from capability_harness.infrastructure.runtime.local_runtime import LocalRuntime
from capability_harness.infrastructure.runtime.model_manager import OllamaModelManager
from capability_harness.infrastructure.runtime.provider_registry import NoOpRuntime, ProviderRegistry

logger = logging.getLogger(__name__)

mcp = FastMCP("capability-harness")

# --- Composition root (shared across all tool calls in this process) ---

_policy = PolicyEngine()
_state_store = InMemoryStateStore()
_event_bus = InProcessEventBus()
_artifact_store = LocalArtifactStore(root=".harness/artifacts")
_model_manager = OllamaModelManager()

_provider_registry = ProviderRegistry()
_provider_registry.register("noop", NoOpRuntime())
_provider_registry.register("local", LocalRuntime())  # uses Ollama at localhost:11434

_registry = CapabilityRegistry()
_registry.register(NOOP_CAPABILITY)
_routing = RoutingEngine(_provider_registry, _policy)
_graph_executor = GraphExecutor(_registry, _routing, _event_bus)
_scheduler = HarnessScheduler(
    graph_executor=_graph_executor,
    policy=_policy,
    state_store=_state_store,
    event_bus=_event_bus,
    default_graph=NOOP_GRAPH,
)


def _write_output_artifact(task_id: str, output: str, capability_name: str) -> None:
    """Persist capability output as a PATCH artifact (primary output kind)."""
    if not output:
        return
    try:
        _artifact_store.write(ArtifactKind.PATCH, task_id, output)
    except Exception:
        logger.exception("Failed to write output artifact for task %s", task_id)


# --- Task tools ---


@mcp.tool()
async def task_submit(capability: str, context: str = "", input_file: str | None = None) -> dict[str, Any]:
    """Submit a task and run it synchronously. Returns task_id and final state.

    Args:
        capability: Name of the registered capability to run (e.g. 'noop').
        context: The task description or instructions for the capability.
        input_file: Optional path to an input artifact file.
    """
    task = Task(capability_name=capability)
    task_id = await _scheduler.submit_task(task)

    # Read input file content if provided
    input_content = context
    if input_file:
        try:
            from pathlib import Path
            input_content = Path(input_file).read_text()
        except Exception as exc:
            return {"error": f"Could not read input_file: {exc}"}

    # Execute the graph directly (synchronous dispatch for MCP — no polling needed)
    spec = _registry.resolve(capability)
    runtime = _routing.select_runtime(spec)

    from capability_harness.domain.capability import WorkRequest
    request = WorkRequest(task_id=task_id, spec=spec, context=input_content)

    try:
        _state_store.transition(task_id, TaskState.RUNNING, reason="mcp-dispatch")
        result = await runtime.run(spec, request)

        if result.success:
            _write_output_artifact(task_id, result.output, capability)
            _state_store.transition(task_id, TaskState.VALIDATION, reason="execution complete")
            # Auto-advance through validation to review (validation pipeline is Phase 8)
            _state_store.transition(task_id, TaskState.REVIEW, reason="validation skipped (stub)")
        else:
            _state_store.transition(task_id, TaskState.FAILED, reason=result.error or "runtime error")

        return {
            "task_id": task_id,
            "state": str(_state_store.get_task(task_id).state),
            "success": result.success,
            "output_preview": result.output[:500] if result.output else "",
            "error": result.error,
            "metadata": result.metadata,
        }
    except Exception as exc:
        _state_store.transition(task_id, TaskState.FAILED, reason=str(exc))
        return {"task_id": task_id, "state": "failed", "error": str(exc)}


@mcp.tool()
def task_status(task_id: str) -> dict[str, Any]:
    """Get the current state and details of a task."""
    try:
        task = _state_store.get_task(task_id)
        return {
            "id": task.id,
            "capability": task.capability_name,
            "state": str(task.state),
            "retry_count": task.retry_count,
            "error": task.error,
        }
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def task_list(state: str | None = None) -> list[dict[str, Any]]:
    """List all tasks, optionally filtered by state."""
    tasks = _state_store.list_tasks()
    if state:
        tasks = [t for t in tasks if str(t.state) == state]
    return [{"id": t.id, "capability": t.capability_name, "state": str(t.state)} for t in tasks]


@mcp.tool()
def task_approve(task_id: str) -> dict[str, Any]:
    """Approve a task that is in 'review' state, advancing it to 'approved'."""
    try:
        _state_store.transition(task_id, TaskState.APPROVED)
        return {"task_id": task_id, "state": str(TaskState.APPROVED)}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def task_reject(task_id: str, reason: str = "") -> dict[str, Any]:
    """Reject a task in review, sending it back to 'failed' state."""
    try:
        _state_store.transition(task_id, TaskState.FAILED, reason=reason)
        return {"task_id": task_id, "state": str(TaskState.FAILED)}
    except Exception as exc:
        return {"error": str(exc)}


# --- Artifact tools ---


@mcp.tool()
def artifact_list(task_id: str) -> list[dict[str, Any]]:
    """List artifacts produced by a task."""
    try:
        artifacts = _artifact_store.read_task_artifacts(task_id)
        return [{"id": a.id, "kind": a.kind.value, "size_bytes": a.size_bytes} for a in artifacts]
    except Exception as exc:
        return [{"error": str(exc)}]


@mcp.tool()
def artifact_get(task_id: str, kind: str = "patch.diff") -> dict[str, Any]:
    """Get the text content of a specific artifact for a task.

    Args:
        task_id: The task ID.
        kind: Artifact kind filename (default: patch.diff). Options: requirements.md,
              architecture.md, implementation_plan.json, patch.diff, test_report.json,
              review.md, telemetry.json
    """
    try:
        artifacts = _artifact_store.read_task_artifacts(task_id)
        match = next((a for a in artifacts if a.kind.value == kind), None)
        if not match:
            available = [a.kind.value for a in artifacts]
            return {"error": f"No artifact of kind '{kind}'. Available: {available}"}
        content = _artifact_store.read(match.id)
        return {"task_id": task_id, "kind": kind, "content": content.decode("utf-8", errors="replace")}
    except Exception as exc:
        return {"error": str(exc)}


# --- Capability tools ---


@mcp.tool()
def capability_list() -> list[dict[str, Any]]:
    """List all registered capabilities."""
    caps = _registry.list_capabilities()
    return [
        {
            "name": c.name,
            "description": c.description,
            "work_profile": c.work_profile.model_dump(),
        }
        for c in caps
    ]


# --- Benchmark tool ---


@mcp.tool()
def benchmark_report() -> dict[str, Any]:
    """Return an aggregated benchmark report for all tasks this session."""
    tasks = _state_store.list_tasks()
    total = len(tasks)
    succeeded = sum(1 for t in tasks if t.state == TaskState.ARCHIVED)
    failed = sum(1 for t in tasks if t.state == TaskState.FAILED)
    return {
        "total_tasks": total,
        "succeeded": succeeded,
        "failed": failed,
        "success_rate": round(succeeded / total, 3) if total else 0.0,
    }


# --- Model tools ---


@mcp.tool()
async def model_list() -> list[dict[str, Any]]:
    """List local models downloaded via Ollama."""
    try:
        models = await _model_manager.list_models()
        return [
            {
                "name": m.name,
                "size_gb": round(m.size_bytes / 1e9, 2),
                "family": m.family,
                "parameter_size": m.parameter_size,
                "quantization": m.quantization,
            }
            for m in models
        ]
    except Exception as exc:
        return [{"error": str(exc)}]


@mcp.tool()
async def model_pull(name: str) -> dict[str, Any]:
    """Download a model via Ollama (e.g. 'mistral', 'llama3', 'codellama')."""
    try:
        last_status = ""
        async for progress in _model_manager.pull_model(name):
            last_status = progress.status
        return {"status": "success", "model": name, "last_status": last_status}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
