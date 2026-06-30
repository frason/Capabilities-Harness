"""Capability Graph — the canonical execution model for every task.

The Scheduler always dispatches through GraphExecutor, even for a single-capability task.
The graph represents a workflow as data; capabilities never modify it.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from capability_harness.domain.capability import CapabilitySpec, WorkRequest, WorkResult
from capability_harness.domain.events import CapabilityCompleted, CapabilityStarted
from capability_harness.domain.task import Task

logger = logging.getLogger(__name__)


class CyclicDependencyError(Exception):
    """Raised when the capability graph contains a cycle."""


class GraphNode(BaseModel):
    """A single node in a CapabilityGraph."""

    name: str
    depends_on: list[str] = Field(default_factory=list)


class CapabilityGraph(BaseModel):
    """A directed acyclic graph of capability names to be executed in order."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    nodes: list[GraphNode]
    metadata: dict[str, Any] = Field(default_factory=dict)

    def topological_order(self) -> list[str]:
        """Return node names in execution order (Kahn's algorithm)."""
        in_degree: dict[str, int] = {n.name: 0 for n in self.nodes}
        for node in self.nodes:
            for dep in node.depends_on:
                if dep not in in_degree:
                    raise ValueError(f"Unknown dependency '{dep}' in node '{node.name}'")
                in_degree[node.name] += 1

        queue = [name for name, deg in in_degree.items() if deg == 0]
        order: list[str] = []
        while queue:
            current = queue.pop(0)
            order.append(current)
            for node in self.nodes:
                if current in node.depends_on:
                    in_degree[node.name] -= 1
                    if in_degree[node.name] == 0:
                        queue.append(node.name)

        if len(order) != len(self.nodes):
            raise CyclicDependencyError(
                f"Cycle detected in capability graph {self.id!r}. "
                f"Processed {len(order)} of {len(self.nodes)} nodes."
            )
        return order


class GraphResult(BaseModel):
    """Aggregated result of executing a CapabilityGraph."""

    graph_id: str
    task_id: str
    success: bool
    node_results: dict[str, WorkResult] = Field(default_factory=dict)
    error: str | None = None


class GraphExecutor:
    """Executes a CapabilityGraph node-by-node in topological order."""

    def __init__(
        self,
        registry: Any,
        routing: Any,
        event_bus: Any,
    ) -> None:
        self._registry = registry
        self._routing = routing
        self._bus = event_bus

    async def execute(
        self,
        graph: CapabilityGraph,
        task: Task,
        memory_context: list[str] | None = None,
    ) -> GraphResult:
        node_results: dict[str, WorkResult] = {}
        try:
            order = graph.topological_order()
        except (CyclicDependencyError, ValueError) as exc:
            return GraphResult(
                graph_id=graph.id,
                task_id=task.id,
                success=False,
                error=str(exc),
            )

        for node_name in order:
            self._bus.publish(CapabilityStarted(task_id=task.id, capability_name=node_name))
            try:
                spec: CapabilitySpec = self._registry.resolve(node_name)
                runtime = self._routing.select_runtime(spec)
                request = WorkRequest(
                    task_id=task.id,
                    spec=spec,
                    context="",
                    memory_layers=memory_context or [],
                )
                result = await runtime.run(spec, request)
            except Exception as exc:
                result = WorkResult(
                    task_id=task.id,
                    success=False,
                    error=str(exc),
                )
                logger.exception("capability '%s' failed for task %s", node_name, task.id)

            node_results[node_name] = result
            self._bus.publish(
                CapabilityCompleted(
                    task_id=task.id,
                    capability_name=node_name,
                    success=result.success,
                )
            )
            if not result.success:
                return GraphResult(
                    graph_id=graph.id,
                    task_id=task.id,
                    success=False,
                    node_results=node_results,
                    error=result.error,
                )

        return GraphResult(
            graph_id=graph.id,
            task_id=task.id,
            success=True,
            node_results=node_results,
        )


# Default single-node graph used for testing and skeleton wiring
NOOP_GRAPH = CapabilityGraph(nodes=[GraphNode(name="noop")])
