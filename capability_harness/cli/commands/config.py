"""CLI commands for configuration management."""
from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty

from capability_harness.config.loader import ConfigNotFoundError, ConfigValidationError, load_config

app = typer.Typer(help="Configuration management")
console = Console()


@app.command("validate")
def validate(
    path: str = typer.Option("harness.toml", "--config", "-c", help="Path to harness.toml"),
) -> None:
    """Validate a harness.toml configuration file."""
    try:
        load_config(path)
        console.print(f"[green]✓[/green] Configuration valid: {path}")
    except ConfigNotFoundError as exc:
        console.print(f"[red]✗[/red] {exc}")
        raise typer.Exit(1) from None
    except ConfigValidationError as exc:
        console.print(f"[red]✗[/red] {exc}")
        raise typer.Exit(1) from None


@app.command("show")
def show(
    path: str = typer.Option("harness.toml", "--config", "-c", help="Path to harness.toml"),
) -> None:
    """Display the resolved configuration."""
    try:
        config = load_config(path)
        console.print(Panel(Pretty(config.model_dump()), title="Harness Configuration"))
    except (ConfigNotFoundError, ConfigValidationError) as exc:
        console.print(f"[red]✗[/red] {exc}")
        raise typer.Exit(1) from None
