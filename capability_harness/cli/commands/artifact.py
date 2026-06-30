"""CLI commands for artifact inspection."""
from __future__ import annotations

import typer
from rich.console import Console

from capability_harness.cli.output import artifact_panel, error_panel
from capability_harness.infrastructure.persistence.artifact_store import LocalArtifactStore

app = typer.Typer(help="Artifact management")
console = Console()


@app.command("list")
def list_artifacts(task_id: str = typer.Argument(..., help="Task ID")) -> None:
    """List artifacts produced by a task."""
    store = LocalArtifactStore()
    artifacts = store.read_task_artifacts(task_id)
    if not artifacts:
        console.print(f"No artifacts found for task [dim]{task_id}[/dim]")
        return
    for artifact in artifacts:
        console.print(artifact_panel(artifact))


@app.command("get")
def get(
    task_id: str = typer.Argument(..., help="Task ID"),
    kind: str = typer.Argument(..., help="Artifact kind (e.g. patch.diff)"),
) -> None:
    """Print the content of a specific artifact."""
    store = LocalArtifactStore()
    artifacts = store.read_task_artifacts(task_id)
    matching = [a for a in artifacts if a.kind.value == kind]
    if not matching:
        console.print(error_panel(f"No artifact '{kind}' found for task {task_id}"))
        raise typer.Exit(1) from None
    data = store.read(matching[0].id)
    console.print(data.decode(errors="replace"))
