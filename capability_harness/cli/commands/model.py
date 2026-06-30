"""CLI commands for local model management (Ollama)."""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeRemainingColumn
from rich.table import Table

from capability_harness.infrastructure.runtime.model_manager import OllamaModelManager

app = typer.Typer(help="Local model management (Ollama)")
console = Console()

_DEFAULT_BASE_URL = "http://localhost:11434"


@app.command("check")
def check(
    base_url: str = typer.Option(_DEFAULT_BASE_URL, "--url", help="Ollama base URL"),
) -> None:
    """Check if Ollama is running and reachable."""
    manager = OllamaModelManager(base_url)

    async def _run() -> bool:
        return await manager.is_running()

    running = asyncio.run(_run())
    if running:
        console.print(f"[green]✓[/green] Ollama is running at {base_url}")
    else:
        console.print(f"[red]✗[/red] Ollama is not reachable at {base_url}")
        console.print("\nTo start Ollama: [bold]ollama serve[/bold]")
        raise typer.Exit(1) from None


@app.command("list")
def list_models(
    base_url: str = typer.Option(_DEFAULT_BASE_URL, "--url", help="Ollama base URL"),
) -> None:
    """List locally downloaded models."""
    manager = OllamaModelManager(base_url)

    async def _run() -> None:
        if not await manager.is_running():
            console.print("[red]Ollama is not running.[/red] Start with: [bold]ollama serve[/bold]")
            raise typer.Exit(1) from None

        models = await manager.list_models()
        if not models:
            console.print("[dim]No models downloaded yet. Run [bold]cap model pull <name>[/bold].[/dim]")
            return

        table = Table(title="Local Models", show_header=True, header_style="bold magenta")
        table.add_column("Name", style="bold")
        table.add_column("Size", justify="right")
        table.add_column("Family")
        table.add_column("Parameters")
        table.add_column("Quantization")

        for m in models:
            size = f"{m.size_bytes / 1e9:.1f} GB"
            table.add_row(m.name, size, m.family, m.parameter_size, m.quantization)

        console.print(table)

    asyncio.run(_run())


@app.command("pull")
def pull(
    name: str = typer.Argument(..., help="Model name (e.g. mistral, llama3, codellama)"),
    base_url: str = typer.Option(_DEFAULT_BASE_URL, "--url", help="Ollama base URL"),
) -> None:
    """Download a model via Ollama."""
    manager = OllamaModelManager(base_url)

    async def _run() -> None:
        if not await manager.is_running():
            console.print("[red]Ollama is not running.[/red] Start with: [bold]ollama serve[/bold]")
            raise typer.Exit(1) from None

        console.print(f"Pulling [bold]{name}[/bold] from Ollama registry...")

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            pull_task = progress.add_task(f"Downloading {name}", total=100)
            last_status = ""

            async for prog in manager.pull_model(name):
                last_status = prog.status
                if prog.total > 0:
                    progress.update(pull_task, completed=prog.percent, description=prog.status)
                else:
                    progress.update(pull_task, description=prog.status)

        console.print(f"[green]✓[/green] {name} ready. Last status: {last_status}")
        console.print("\nVerify with: [bold]cap model list[/bold]")

    asyncio.run(_run())


@app.command("select")
def select(
    name: str = typer.Argument(..., help="Model name to set as default"),
) -> None:
    """Set the default local model in harness.toml."""
    console.print("[yellow]Note:[/yellow] Update [bold]examples/harness.toml[/bold]:")
    console.print("\n  [local_runtime]")
    console.print(f"  default_model = \"{name}\"")
    console.print(
        "\nAutomatic config writing not yet implemented — edit harness.toml manually."
    )
