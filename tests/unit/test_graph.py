"""Unit tests for the Capability Graph."""
import pytest

from capability_harness.application.graph import (
    NOOP_GRAPH,
    CapabilityGraph,
    CyclicDependencyError,
    GraphExecutor,
    GraphNode,
)
from capability_harness.application.policy import PolicyEngine
from capability_harness.application.registry import NOOP_CAPABILITY, CapabilityRegistry
from capability_harness.application.routing import RoutingEngine
from capability_harness.domain.task import Task
from capability_harness.infrastructure.eventbus.bus import InProcessEventBus
from capability_harness.infrastructure.providers.noop_provider import NoOpProvider
from capability_harness.infrastructure.providers.registry import ProviderRegistry
from capability_harness.infrastructure.runtime.runtime import Runtime


def test_single_node_topological_order():
    graph = NOOP_GRAPH
    assert graph.topological_order() == ["noop"]


def test_multi_node_topological_order():
    graph = CapabilityGraph(nodes=[
        GraphNode(name="plan"),
        GraphNode(name="code", depends_on=["plan"]),
        GraphNode(name="review", depends_on=["code"]),
    ])
    order = graph.topological_order()
    assert order.index("plan") < order.index("code")
    assert order.index("code") < order.index("review")


def test_cyclic_graph_raises():
    graph = CapabilityGraph(nodes=[
        GraphNode(name="a", depends_on=["b"]),
        GraphNode(name="b", depends_on=["a"]),
    ])
    with pytest.raises(CyclicDependencyError):
        graph.topological_order()


def test_unknown_dependency_raises():
    graph = CapabilityGraph(nodes=[
        GraphNode(name="a", depends_on=["missing"]),
    ])
    with pytest.raises(ValueError, match="Unknown dependency"):
        graph.topological_order()


@pytest.mark.asyncio
async def test_graph_executor_noop():
    provider_registry = ProviderRegistry()
    provider_registry.register("noop", NoOpProvider())
    runtime = Runtime(provider_registry)

    registry = CapabilityRegistry()
    registry.register(NOOP_CAPABILITY)

    policy = PolicyEngine()
    routing = RoutingEngine(
        policy=policy,
        default_provider="noop",
        profile={"noop": "noop"},
        registered_providers=["noop"],
    )
    bus = InProcessEventBus()
    executor = GraphExecutor(registry, routing, bus, runtime=runtime)

    task = Task(capability_name="noop")
    result = await executor.execute(NOOP_GRAPH, task)

    assert result.success is True
    assert "noop" in result.node_results
    assert result.node_results["noop"].success is True
