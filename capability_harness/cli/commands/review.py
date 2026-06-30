"""CLI commands for human review of task output."""
from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer(help="Human review commands")
console = Console()


@app.command("diff")
def diff(task_id: str = typer.Argument(..., help="Task ID")) -> None:
    """Show the patch diff for a task."""
    console.print(f"[dim]Fetching diff for task {task_id}... (stub)[/dim]")


@app.command("approve")
def approve(task_id: str = typer.Argument(..., help="Task ID")) -> None:
    """Approve a task for merging."""
    console.print(f"[green]✓[/green] Task {task_id} approved (stub — state transition not yet wired)")


@app.command("reject")
def reject(
    task_id: str = typer.Argument(..., help="Task ID"),
    reason: str = typer.Option("", "--reason", "-r", help="Rejection reason"),
) -> None:
    """Reject a task and return it for revision."""
    console.print(
        f"[red]✗[/red] Task {task_id} rejected"
        + (f": {reason}" if reason else "") + " (stub)"
    )
