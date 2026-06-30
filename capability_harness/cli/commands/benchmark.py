"""CLI command for benchmark reporting."""
from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer(help="Benchmarking and performance metrics")
console = Console()


@app.command("report")
def report() -> None:
    """Print aggregate benchmark metrics across all tasks."""
    console.print("[dim]No benchmark data collected yet.[/dim]")
    console.print(
        "\nBenchmark metrics will be available here once tasks have been executed.\n"
        "Metrics include: wall-clock time, AI vs deterministic tool time, "
        "token usage, retry count, validation failures, estimated cost, and success rate."
    )
