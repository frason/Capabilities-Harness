"""CLI command to launch the Capability Harness MCP server."""
from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer(help="MCP server management")
console = Console()


@app.command("serve")
def serve() -> None:
    """Launch the Capability Harness MCP server (stdio transport).

    Add to Claude Code via .mcp.json or:
      claude mcp add --transport stdio capability-harness -- python -m capability_harness.mcp.server
    """
    try:
        from capability_harness.mcp.server import main

        console.print("[green]Starting Capability Harness MCP server...[/green]")
        main()
    except ImportError:
        console.print("[red]MCP dependencies not installed.[/red]")
        console.print("Run: [bold]pip install -e '.[mcp]'[/bold]")
        raise typer.Exit(1) from None
