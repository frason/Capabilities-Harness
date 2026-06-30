"""CLI commands for task lifecycle management."""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console

from capability_harness.application.graph import NOOP_GRAPH, GraphExecutor
from capability_harness.application.policy import PolicyEngine
from capability_harness.application.registry import NOOP_CAPABILITY, CapabilityRegistry
from capability_harness.application.routing import RoutingEngine
from capability_harness.application.scheduler import HarnessScheduler
from capability_harness.cli.output import status_badge
from capability_harness.domain.task import Task
from capability_harness.infrastructure.eventbus.bus import InProcessEventBus
from capability_harness.infrastructure.persistence.state_store import InMemoryStateStore
from capability_harness.infrastructure.runtime.provider_registry import (
    NoOpRuntime,
    ProviderRegistry,
)

app = typer.Typer(help="Task lifecycle management")
console = Console()


def _build_composition_root() -> HarnessScheduler:
    """Wire up the skeleton composition root for CLI use."""
    policy = PolicyEngine()
    state_store = InMemoryStateStore()
    event_bus = InProcessEventBus()

    provider_registry = ProviderRegistry()
    provider_registry.register("noop", NoOpRuntime())

    registry = CapabilityRegistry()
    registry.register(NOOP_CAPABILITY)

    routing = RoutingEngine(provider_registry, policy)
    graph_executor = GraphExecutor(registry, routing, event_bus)

    return HarnessScheduler(
        graph_executor=graph_executor,
        policy=policy,
        state_store=state_store,
        event_bus=event_bus,
        default_graph=NOOP_GRAPH,
    )


@app.command("submit")
def submit(
    capability_name: str = typer.Option(..., "--capability", "-c", help="Capability to run"),
    input_file: str | None = typer.Option(None, "--input", "-i", help="Input artifact path"),
) -> None:
    """Submit a new task to the harness."""
    scheduler = _build_composition_root()
    task = Task(capability_name=capability_name)

    async def _run() -> str:
        return await scheduler.submit_task(task)

    task_id = asyncio.run(_run())
    console.print("[green]✓[/green] Task submitted")
    console.print(f"  ID:         [bold]{task_id}[/bold]")
    console.print(f"  Capability: {capability_name}")
    console.print(f"  State:      {status_badge(task.state)}")
    console.print(f"\nRun [bold]cap task status {task_id[:8]}[/bold] to check progress.")


@app.command("status")
def status(task_id: str = typer.Argument(..., help="Task ID (or prefix)")) -> None:
    """Show the current status of a task."""
    console.print(f"[dim]Status lookup for task {task_id!r} — state store not yet persistent.[/dim]")


@app.command("list")
def list_tasks(
    state: str | None = typer.Option(None, "--state", "-s", help="Filter by state"),
) -> None:
    """List all tasks."""
    console.print("[dim]No persistent tasks available — state store is in-memory only.[/dim]")


@app.command("cancel")
def cancel(task_id: str = typer.Argument(..., help="Task ID")) -> None:
    """Cancel a pending or running task."""
    console.print(f"[dim]Cancel for task {task_id!r} — not yet wired to persistent state.[/dim]")


@app.command("logs")
def logs(task_id: str = typer.Argument(..., help="Task ID")) -> None:
    """Stream logs for a task."""
    console.print(f"[dim]Logs for task {task_id!r} — telemetry streaming not yet implemented.[/dim]")
