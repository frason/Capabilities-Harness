"""Capability Harness CLI entry point.

The framework owns process. Capabilities own reasoning.
Models own inference. Providers own transport.
"""
from __future__ import annotations

import typer

from capability_harness.cli.commands import artifact, benchmark, capability, config, mcp, model, review, task

app = typer.Typer(
    name="cap",
    help=(
        "Capability Harness — a deterministic operating system for AI-assisted software engineering.\n\n"
        "The framework owns process. Capabilities own reasoning. "
        "Models own inference. Providers own transport."
    ),
    no_args_is_help=True,
)

app.add_typer(task.app, name="task")
app.add_typer(capability.app, name="capability")
app.add_typer(artifact.app, name="artifact")
app.add_typer(review.app, name="review")
app.add_typer(config.app, name="config")
app.add_typer(benchmark.app, name="benchmark")
app.add_typer(model.app, name="model")
app.add_typer(mcp.app, name="mcp")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
