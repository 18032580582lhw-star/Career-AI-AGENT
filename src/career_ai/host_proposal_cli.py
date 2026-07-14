"""Typer command registration for host-proposal tailoring workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console  # noqa: TC002 - runtime object passed from root CLI.

from career_ai.application import TailoringApplicationService
from career_ai.host_proposal_output import (
    CliOutputMode,
    print_latex_profile,
    print_prepare_result,
    print_render_result,
    print_validation_result,
)
from career_ai.tailoring.host_run_store import (
    RENDER_STALE_EXIT_CODE,
    HostRenderFormat,
    HostRunError,
)

DEFAULT_WORKSPACE = Path()
DEFAULT_RESUME_FILE = Path("resume.txt")
DEFAULT_JD_FILE = Path("jd.txt")
DEFAULT_PROPOSAL_FILE = Path("proposal.json")
DEFAULT_CONFIRMATION_FILE = Path("confirmation.json")


def register_host_proposal_commands(  # noqa: C901
    app: typer.Typer,
    console: Console,
) -> None:
    """Attach host-proposal commands to the root CLI."""

    @app.command("prepare")
    def prepare_command(  # noqa: PLR0913 - Typer exposes user-facing CLI options.
        workspace: Annotated[
            Path,
            typer.Option(help="Career AI workspace root."),
        ] = DEFAULT_WORKSPACE,
        resume_file: Annotated[
            Path,
            typer.Option(help="Immutable resume source file."),
        ] = DEFAULT_RESUME_FILE,
        jd_file: Annotated[
            Path,
            typer.Option(help="Immutable job description source file."),
        ] = DEFAULT_JD_FILE,
        latex_template: Annotated[
            Path | None,
            typer.Option(help="Optional user-owned LaTeX template."),
        ] = None,
        language: Annotated[str, typer.Option("--language", help="Output language tag.")] = "en",
        output: Annotated[
            CliOutputMode,
            typer.Option("--output", help="Choose result summary, process details, or JSON."),
        ] = CliOutputMode.RESULT,
    ) -> None:
        """Prepare a no-API host-proposal request artifact."""
        result = TailoringApplicationService(workspace=workspace).prepare(
            resume_file=resume_file,
            jd_file=jd_file,
            latex_template=latex_template,
            language=language,
        )
        print_prepare_result(console, result, output)

    @app.command("validate-draft")
    def validate_draft_command(
        workspace: Annotated[
            Path,
            typer.Option(help="Career AI workspace root."),
        ] = DEFAULT_WORKSPACE,
        run_id: Annotated[str, typer.Option(help="Prepared run id.")] = "",
        proposal_file: Annotated[
            Path,
            typer.Option(help="Strict JSON proposal file."),
        ] = DEFAULT_PROPOSAL_FILE,
        output: Annotated[
            CliOutputMode,
            typer.Option("--output", help="Choose result summary, process details, or JSON."),
        ] = CliOutputMode.RESULT,
    ) -> None:
        """Validate a host-authored proposal through the local dual harness."""
        try:
            result = TailoringApplicationService(workspace=workspace).validate(
                run_id=run_id,
                proposal_file=proposal_file,
            )
        except HostRunError as error:
            console.print(str(error))
            raise typer.Exit(code=error.exit_code) from error
        print_validation_result(console, result, output)

    @app.command("confirm")
    def confirm_command(
        workspace: Annotated[
            Path,
            typer.Option(help="Career AI workspace root."),
        ] = DEFAULT_WORKSPACE,
        run_id: Annotated[str, typer.Option(help="Prepared run id.")] = "",
        confirmation_file: Annotated[
            Path,
            typer.Option(help="Strict JSON confirmation response file."),
        ] = DEFAULT_CONFIRMATION_FILE,
        output: Annotated[
            CliOutputMode,
            typer.Option("--output", help="Choose result summary, process details, or JSON."),
        ] = CliOutputMode.RESULT,
    ) -> None:
        """Persist a confirmation response and rerun validation."""
        try:
            result = TailoringApplicationService(workspace=workspace).confirm(
                run_id=run_id,
                confirmation_file=confirmation_file,
            )
        except HostRunError as error:
            console.print(str(error))
            raise typer.Exit(code=error.exit_code) from error
        print_validation_result(console, result, output)

    @app.command("tailor")
    def tailor_command(
        workspace: Annotated[
            Path,
            typer.Option(help="Career AI workspace root."),
        ] = DEFAULT_WORKSPACE,
        run_id: Annotated[str, typer.Option(help="Prepared run id.")] = "",
        host_proposal: Annotated[
            Path | None,
            typer.Option(help="Host-authored strict JSON proposal file."),
        ] = None,
        output: Annotated[
            CliOutputMode,
            typer.Option("--output", help="Choose result summary, process details, or JSON."),
        ] = CliOutputMode.RESULT,
    ) -> None:
        """Generate or validate proposals for a prepared tailoring run."""
        try:
            if host_proposal is not None:
                result = TailoringApplicationService(workspace=workspace).validate(
                    run_id=run_id,
                    proposal_file=host_proposal,
                )
            else:
                result = TailoringApplicationService(workspace=workspace).tailor_with_api(
                    run_id=run_id,
                )
        except HostRunError as error:
            console.print(str(error))
            raise typer.Exit(code=error.exit_code) from error
        print_validation_result(console, result, output)

    @app.command("render")
    def render_command(
        workspace: Annotated[
            Path,
            typer.Option(help="Career AI workspace root."),
        ] = DEFAULT_WORKSPACE,
        run_id: Annotated[str, typer.Option(help="Accepted run id.")] = "",
        render_format: Annotated[
            HostRenderFormat,
            typer.Option("--format", help="Artifact format to render."),
        ] = HostRenderFormat.ALL,
        disable_latex_engines: Annotated[  # noqa: FBT002 - Typer option.
            bool,
            typer.Option(help="Disable LaTeX engine discovery for deterministic QA."),
        ] = False,
        output: Annotated[
            CliOutputMode,
            typer.Option("--output", help="Choose result summary, process details, or JSON."),
        ] = CliOutputMode.RESULT,
    ) -> None:
        """Render accepted artifacts with live hash revalidation."""
        try:
            result = TailoringApplicationService(workspace=workspace).render(
                run_id=run_id,
                render_format=render_format,
                disable_latex_engines=disable_latex_engines,
            )
        except HostRunError as error:
            console.print(str(error))
            raise typer.Exit(code=error.exit_code) from error
        print_render_result(console, result, output)
        if any(item.status == "stale" for item in result.results):
            raise typer.Exit(code=RENDER_STALE_EXIT_CODE)

    @app.command("inspect-latex")
    def inspect_latex_command(
        template_file: Annotated[
            Path,
            typer.Option(help="User-owned resume.tex file to inspect."),
        ],
        output: Annotated[
            CliOutputMode,
            typer.Option("--output", help="Choose result summary, process details, or JSON."),
        ] = CliOutputMode.RESULT,
    ) -> None:
        """Inspect a user-owned LaTeX template without modifying it."""
        profile = TailoringApplicationService(workspace=DEFAULT_WORKSPACE).inspect_latex_template(
            template_file,
        )
        print_latex_profile(console, profile, output)

    registered_commands = (
        prepare_command,
        validate_draft_command,
        confirm_command,
        tailor_command,
        render_command,
        inspect_latex_command,
    )
    _ = registered_commands
