"""Rich-based output formatters for the cap CLI."""
from __future__ import annotations

from rich.panel import Panel
from rich.table import Table

from capability_harness.domain.artifact import Artifact
from capability_harness.domain.task import Task, TaskState

_STATE_COLORS = {
    TaskState.CREATED: "white",
    TaskState.READY: "cyan",
    TaskState.RUNNING: "yellow",
    TaskState.VALIDATION: "blue",
    TaskState.REVIEW: "magenta",
    TaskState.APPROVED: "green",
    TaskState.MERGED: "bright_green",
    TaskState.ARCHIVED: "dim",
    TaskState.FAILED: "red",
    TaskState.CANCELLED: "dim red",
}


def status_badge(state: TaskState) -> str:
    color = _STATE_COLORS.get(state, "white")
    return f"[{color}]{state.value}[/{color}]"


def task_table(tasks: list[Task]) -> Table:
    table = Table(title="Tasks", show_lines=True)
    table.add_column("ID", style="dim", max_width=12)
    table.add_column("Capability")
    table.add_column("State")
    table.add_column("Priority")
    table.add_column("Retries", justify="right")
    for task in tasks:
        table.add_row(
            task.id[:8],
            task.capability_name,
            status_badge(task.state),
            task.priority.value,
            str(task.retry_count),
        )
    return table


def artifact_panel(artifact: Artifact) -> Panel:
    content = (
        f"ID:      {artifact.id[:16]}...\n"
        f"Kind:    {artifact.kind.value}\n"
        f"Task:    {artifact.task_id[:8]}\n"
        f"Size:    {artifact.size_bytes} bytes\n"
        f"Path:    {artifact.path}"
    )
    return Panel(content, title=f"Artifact: {artifact.kind.value}", border_style="blue")


def error_panel(message: str) -> Panel:
    return Panel(message, title="Error", border_style="red")
