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
from capability_harness.domain.task import Task, TaskState
from capability_harness.infrastructure.eventbus.bus import InProcessEventBus
from capability_harness.infrastructure.persistence.state_store import InMemoryStateStore
from capability_harness.infrastructure.runtime.model_manager import OllamaModelManager
from capability_harness.infrastructure.runtime.provider_registry import NoOpRuntime, ProviderRegistry

logger = logging.getLogger(__name__)

mcp = FastMCP("capability-harness")

# --- Composition root (shared across all tool calls in this process) ---

_policy = PolicyEngine()
_state_store = InMemoryStateStore()
_event_bus = InProcessEventBus()
_provider_registry = ProviderRegistry()
_provider_registry.register("noop", NoOpRuntime())
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
_model_manager = OllamaModelManager()


# --- Task tools ---


@mcp.tool()
async def task_submit(capability: str, input_file: str | None = None) -> dict[str, Any]:
    """Submit a new task to Capability Harness."""
    task = Task(capability_name=capability)
    task_id = await _scheduler.submit_task(task)
    return {"task_id": task_id, "state": str(task.state)}


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
        _state_store.transition(task_id, TaskState.FAILED, error=reason)
        return {"task_id": task_id, "state": str(TaskState.FAILED)}
    except Exception as exc:
        return {"error": str(exc)}


# --- Artifact tools ---


@mcp.tool()
def artifact_list(task_id: str) -> list[dict[str, Any]]:
    """List artifacts produced by a task."""
    try:
        artifacts = _state_store.list_artifacts(task_id)
        return [{"id": a.id, "kind": a.kind.value, "size_bytes": a.size_bytes} for a in artifacts]
    except AttributeError:
        return []
    except Exception as exc:
        return [{"error": str(exc)}]


@mcp.tool()
def artifact_get(task_id: str, kind: str) -> dict[str, Any]:
    """Get the content of a specific artifact kind for a task."""
    return {"error": "Artifact store not yet persistent — implement LocalArtifactStore to enable."}


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
