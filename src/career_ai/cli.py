from pathlib import Path
from typing import Annotated, Final

import typer
from rich.console import Console

from career_ai.agent.executor import run_career_agent
from career_ai.agent.planner import agent_mode_label
from career_ai.evals.failure_corpus import (
    FailureCorpusRecord,
    failure_record_to_eval_case_draft,
)
from career_ai.evals.loader import EvalCaseLoadError
from career_ai.evals.model_harness_matrix import (
    default_model_harness_rows,
    run_model_harness_matrix,
)
from career_ai.evals.runner import run_eval_suite
from career_ai.host_doctor_cli import (
    install_latex_renderer_guidance,
    print_extended_doctor_status,
)
from career_ai.host_init_cli import register_init_command
from career_ai.host_proposal_cli import (
    register_host_proposal_commands,
)
from career_ai.llm.client import build_llm_client
from career_ai.llm.settings import LLMSettings
from career_ai.rendering.html_installation import (
    CHROMIUM_MISSING_EXIT_CODE,
    RendererInstallStatus,
    check_html_playwright_installation,
    install_html_renderer_chromium,
)
from career_ai.text_processing import extract_resume_text

app = typer.Typer(help="Local model-neutral Career Agent.")
console = Console()
DEFAULT_EVAL_CASE_DIR: Final[Path] = Path("evals/career_cases")
DEFAULT_PROMPT_DIR: Final[Path] = Path("prompts")


@app.command()
def doctor() -> None:
    """Show local agent configuration and model capability status."""
    settings = LLMSettings()
    profile = settings.capability_profile
    structured = "yes" if profile.supports_structured_output else "no"
    single_turn_tools = "yes" if profile.supports_single_turn_tool_calls else "no"
    multi_turn_tools = "yes" if profile.supports_multi_turn_tool_calls else "no"
    reasoning = "yes" if profile.supports_reasoning_mode else "no"
    streaming = "yes" if profile.supports_streaming else "no"
    tracing = "yes" if profile.supports_provider_tracing else "no"
    console.print(f"Provider: {settings.provider.value}")
    console.print(f"Model: {profile.model_name}")
    console.print(f"Structured output: {structured}")
    console.print(f"Single-turn tool calls: {single_turn_tools}")
    console.print(f"Multi-turn tool calls: {multi_turn_tools}")
    console.print(f"Reasoning mode: {reasoning}")
    console.print(f"Streaming: {streaming}")
    console.print(f"Provider tracing: {tracing}")
    renderer_status = check_html_playwright_installation(output_directory=Path.cwd())
    _print_renderer_status(renderer_status)
    print_extended_doctor_status(console)


@app.command("install-renderer")
def install_renderer(
    *,
    html: Annotated[
        bool,
        typer.Option("--html", help="Install Chromium for HTML/CSS PDF rendering."),
    ] = False,
    latex: Annotated[
        bool,
        typer.Option("--latex", help="Check LaTeX engines and print install guidance."),
    ] = False,
) -> None:
    """Install optional local renderer dependencies."""
    if not html and not latex:
        console.print("Choose a renderer to install, for example: --html or --latex")
        raise typer.Exit(code=2)
    if html:
        result = install_html_renderer_chromium()
        console.print(result.message)
        if not result.succeeded:
            raise typer.Exit(code=result.exit_code)
    if latex:
        install_latex_renderer_guidance(console)


@app.command()
def analyze(
    resume_text: Annotated[str, typer.Option(help="Inline resume text.")] = "",
    jd_text: Annotated[str, typer.Option(help="Inline job description text.")] = "",
    resume_file: Annotated[Path | None, typer.Option(help="Resume file path.")] = None,
) -> None:
    """Analyze a resume against a job description with the local agent."""
    resolved_resume = _resolve_resume_text(resume_text=resume_text, resume_file=resume_file)
    settings = LLMSettings()
    result = run_career_agent(
        resume_text=resolved_resume,
        jd_text=jd_text,
        prompt_dir=Path("prompts"),
        llm_client=build_llm_client(settings),
    )
    console.print(f"Mode: {agent_mode_label(result.mode)}")
    console.print(f"Role: {result.workflow.report.jd_analysis.role_title}")
    console.print(f"Match score: {result.workflow.report.match.score}")
    console.print(f"Best prompt: {result.workflow.prompt_result.best_strategy_name}")
    quality_status = "PASS" if result.quality_report.passed else "FAIL"
    completed_tools = [
        step.name for step in result.steps if step.status.value == "completed"
    ]
    skipped_tools = [
        step.name for step in result.steps if step.status.value == "skipped"
    ]
    failed_checks = [
        f"{check.name} - {check.message}"
        for check in result.quality_report.checks
        if not check.passed
    ]
    console.print(f"Quality: {quality_status}")
    console.print(f"Trace: {result.trace.run_id}")
    console.print(f"Completed tools: {', '.join(completed_tools) or 'none'}")
    console.print(f"Skipped tools: {', '.join(skipped_tools) or 'none'}")
    console.print("Memory summary: available")
    console.print(f"Failed checks: {'; '.join(failed_checks) if failed_checks else 'none'}")


@app.command("eval")
def run_eval_command(
    case_dir: Annotated[
        Path,
        typer.Option(help="Directory containing career eval case JSON files."),
    ] = DEFAULT_EVAL_CASE_DIR,
    prompt_dir: Annotated[
        Path,
        typer.Option(help="Directory containing prompt strategy markdown files."),
    ] = DEFAULT_PROMPT_DIR,
) -> None:
    """Run deterministic career eval cases through the local agent harness."""
    settings = LLMSettings()
    try:
        result = run_eval_suite(
            case_dir=case_dir,
            prompt_dir=prompt_dir,
            llm_client=build_llm_client(settings),
        )
    except EvalCaseLoadError as error:
        console.print(str(error))
        raise typer.Exit(code=2) from error
    console.print(f"Total cases: {result.total_cases}")
    console.print(f"Passed cases: {result.passed_cases}")
    console.print(f"Failed cases: {result.failed_cases}")
    for case_result in result.case_results:
        console.print(f"- {case_result.case_id}: {'PASS' if case_result.passed else 'FAIL'}")
        for check in case_result.checks:
            if not check.passed:
                console.print(f"  - {check.name}: {check.message}")


@app.command("eval-matrix")
def run_eval_matrix_command(
    case_dir: Annotated[
        Path,
        typer.Option(help="Directory containing career eval case JSON files."),
    ] = DEFAULT_EVAL_CASE_DIR,
    prompt_dir: Annotated[
        Path,
        typer.Option(help="Directory containing prompt strategy markdown files."),
    ] = DEFAULT_PROMPT_DIR,
) -> None:
    """Run eval cases across local model-harness configurations."""
    try:
        result = run_model_harness_matrix(
            case_dir=case_dir,
            prompt_dir=prompt_dir,
            rows=default_model_harness_rows(),
        )
    except EvalCaseLoadError as error:
        console.print(str(error))
        raise typer.Exit(code=2) from error
    console.print(f"Total rows: {result.total_rows}")
    console.print(f"Passed rows: {result.passed_rows}")
    console.print(f"Failed rows: {result.failed_rows}")
    console.print(f"Skipped rows: {result.skipped_rows}")
    console.print(f"Unsupported capabilities: {result.unsupported_capability_count}")
    for row_result in result.row_results:
        row_summary = " ".join(
            [
                f"- {row_result.name}: {row_result.provider}/{row_result.model}",
                f"status={row_result.status}",
                f"passed={row_result.passed_cases}",
                f"failed={row_result.failed_cases}",
            ],
        )
        console.print(row_summary)
        for failed_check in row_result.failed_checks:
            console.print(f"  - failed check: {failed_check}")
        for capability in row_result.unsupported_capabilities:
            console.print(f"  - unsupported capability: {capability}")
        if row_result.skip_reason:
            console.print(f"  - skip reason: {row_result.skip_reason}")


@app.command("failure-to-eval")
def convert_failure_to_eval_command(
    record_file: Annotated[
        Path,
        typer.Option(help="JSON failure-corpus candidate file."),
    ],
    output_file: Annotated[
        Path,
        typer.Option(help="Destination eval-case draft JSON file."),
    ],
) -> None:
    """Convert an accepted failure-corpus candidate into a redacted eval draft."""
    record = FailureCorpusRecord.model_validate_json(record_file.read_text(encoding="utf-8-sig"))
    draft = failure_record_to_eval_case_draft(record)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    _ = output_file.write_text(draft.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"Wrote eval draft: {output_file}")


def _resolve_resume_text(*, resume_text: str, resume_file: Path | None) -> str:
    if resume_file is None:
        return resume_text
    extracted = extract_resume_text(resume_file)
    return extracted or resume_text


def _print_renderer_status(status: RendererInstallStatus) -> None:
    renderer_status = "available" if status.available else "unavailable"
    console.print(f"HTML renderer: {renderer_status}")
    for check in status.checks:
        check_status = "PASS" if check.passed else "FAIL"
        repair = ""
        if not check.passed and check.code.value == "playwright_chromium":
            repair = (
                " (repair: career-ai-agent install-renderer --html exits "
                f"{CHROMIUM_MISSING_EXIT_CODE} on install failure)"
            )
        console.print(f"  - {check.code.value}: {check_status} - {check.message}{repair}")


register_init_command(app, console)
register_host_proposal_commands(app, console)
