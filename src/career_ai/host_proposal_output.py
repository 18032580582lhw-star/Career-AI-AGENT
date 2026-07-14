"""Terminal output formatting for host-proposal CLI workflows."""

from __future__ import annotations

from enum import StrEnum, unique
from typing import TYPE_CHECKING

from rich.console import Console  # noqa: TC002 - CLI boundary object.

if TYPE_CHECKING:
    from career_ai.rendering.latex import LatexTemplateProfile
    from career_ai.tailoring.host_run_store import (
        HostPrepareResult,
        HostRenderResult,
        HostValidationResult,
    )


@unique
class CliOutputMode(StrEnum):
    """Terminal output choices for human-first or machine-readable runs."""

    RESULT = "result"
    PROCESS = "process"
    JSON = "json"


def print_prepare_result(
    console: Console,
    result: HostPrepareResult,
    output: CliOutputMode,
) -> None:
    """Print prepare output according to the selected terminal mode."""
    match output:
        case CliOutputMode.RESULT:
            _print_prepare_summary(console, result)
        case CliOutputMode.PROCESS:
            _print_prepare_summary(console, result)
            console.out(result.model_dump_json(indent=2))
        case CliOutputMode.JSON:
            console.out(result.model_dump_json(indent=2))


def print_validation_result(
    console: Console,
    result: HostValidationResult,
    output: CliOutputMode,
) -> None:
    """Print validation output according to the selected terminal mode."""
    match output:
        case CliOutputMode.RESULT:
            _print_validation_summary(console, result)
        case CliOutputMode.PROCESS:
            _print_validation_summary(console, result)
            console.out(result.model_dump_json(indent=2))
        case CliOutputMode.JSON:
            console.out(result.model_dump_json(indent=2))


def print_render_result(
    console: Console,
    result: HostRenderResult,
    output: CliOutputMode,
) -> None:
    """Print render output according to the selected terminal mode."""
    match output:
        case CliOutputMode.RESULT:
            _print_render_summary(console, result)
        case CliOutputMode.PROCESS:
            _print_render_summary(console, result)
            console.out(result.model_dump_json(indent=2))
        case CliOutputMode.JSON:
            console.out(result.model_dump_json(indent=2))


def print_latex_profile(
    console: Console,
    profile: LatexTemplateProfile,
    output: CliOutputMode,
) -> None:
    """Print LaTeX inspection output according to the selected terminal mode."""
    match output:
        case CliOutputMode.RESULT:
            _print_latex_profile_summary(console, profile)
        case CliOutputMode.PROCESS:
            _print_latex_profile_summary(console, profile)
            console.out(profile.model_dump_json(indent=2))
        case CliOutputMode.JSON:
            console.out(profile.model_dump_json(indent=2))


def _print_latex_profile_summary(console: Console, profile: LatexTemplateProfile) -> None:
    console.print(f"Inspect status: {profile.documentclass}")
    console.print(f"Section mapping: {len(profile.section_mappings)} mapped sections")
    console.print(f"Unsafe findings: {len(profile.unsafe_findings)}")


def _print_prepare_summary(console: Console, result: HostPrepareResult) -> None:
    console.print(f"Prepared run: {result.run_id}")
    console.print(f"Request artifact: {result.request_artifact}")
    console.print(f"Template type: {result.template_type.value}")
    console.print(f"Next: {result.next_machine_instruction}")


def _print_validation_summary(console: Console, result: HostValidationResult) -> None:
    console.print(f"Run: {result.run_id}")
    console.print(f"Validation state: {result.state.value}")
    console.print(f"Proposal source: {result.source.value}")
    if result.proposal_hash is not None:
        console.print(f"Proposal hash: {result.proposal_hash}")


def _print_render_summary(console: Console, result: HostRenderResult) -> None:
    rendered_count = sum(1 for item in result.results if item.status == "rendered")
    console.print(f"Render run: {result.run_id}")
    console.print(f"Rendered formats: {rendered_count}/{len(result.results)}")
    for item in result.results:
        artifacts = ", ".join(artifact.path for artifact in item.artifacts)
        suffix = f" -> {artifacts}" if artifacts else ""
        code = f" ({item.code})" if item.code else ""
        console.print(f"- {item.format.value}: {item.status}{code}{suffix}")
