"""CLI commands for capability inspection."""
from __future__ import annotations

import typer
from rich.console import Console
from rich.pretty import Pretty
from rich.table import Table

from capability_harness.application.registry import (
    NOOP_CAPABILITY,
    CapabilityNotFoundError,
    CapabilityRegistry,
)

app = typer.Typer(help="Capability management")
console = Console()


def _default_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register(NOOP_CAPABILITY)
    return registry


@app.command("list")
def list_caps() -> None:
    """List all registered capabilities."""
    registry = _default_registry()
    table = Table(title="Capabilities", show_lines=True)
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Description")
    table.add_column("Tags")
    for spec in registry.list_capabilities():
        table.add_row(
            spec.name,
            spec.version,
            spec.description,
            ", ".join(spec.tags) or "-",
        )
    console.print(table)


@app.command("inspect")
def inspect(name: str = typer.Argument(..., help="Capability name")) -> None:
    """Show detailed spec for a capability."""
    registry = _default_registry()
    try:
        spec = registry.resolve(name)
        console.print(Pretty(spec.model_dump()))
    except CapabilityNotFoundError as exc:
        console.print(f"[red]✗[/red] {exc}")
        raise typer.Exit(1) from None
