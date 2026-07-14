"""Typer registration for workspace and host Skill initialization."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console  # noqa: TC002 - runtime object passed by root CLI.

from career_ai.skills import HostAgent, install_host_skills
from career_ai.workspace import create_workspace

DEFAULT_WORKSPACE = Path()


def register_init_command(app: typer.Typer, console: Console) -> None:
    """Attach idempotent workspace/host initialization to the root CLI."""

    @app.command("init")
    def init_command(
        workspace: Annotated[
            Path,
            typer.Option(help="Career AI workspace root."),
        ] = DEFAULT_WORKSPACE,
        agent: Annotated[
            HostAgent | None,
            typer.Option(help="Host adapter to install."),
        ] = None,
    ) -> None:
        """Initialize a local workspace and, optionally, host Skill adapters."""
        if agent is None:
            manifest = create_workspace(workspace)
            console.out(manifest.model_dump_json(indent=2))
            return
        result = install_host_skills(workspace=workspace, agent=agent)
        console.out(result.model_dump_json(indent=2))

    _ = init_command
