from pathlib import Path

import pytest
from typer.testing import CliRunner

from career_ai.agent.execution_loop import AgentRuntimeOptions
from career_ai.agent.executor import run_career_agent as run_real_career_agent
from career_ai.agent.models import AgentRun
from career_ai.agent.quality import CareerQualityCheck, CareerQualityReport
from career_ai.cli import app
from career_ai.llm.client import LLMClient
from career_ai.rendering.html_installation import (
    InstallCheckCode,
    InstallRendererResult,
    RendererInstallCheck,
    RendererInstallStatus,
)
from career_ai.tailoring.manifest_contracts import RenderBackend


def test_cli_doctor_reports_fake_provider_ready() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Provider: fake" in result.stdout
    assert "Model: local-fake" in result.stdout
    assert "Structured output: yes" in result.stdout
    assert "Single-turn tool calls: no" in result.stdout
    assert "Provider tracing: no" in result.stdout
    assert "HTML renderer:" in result.stdout


def test_cli_doctor_reports_html_renderer_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_check_html_renderer_installation(
        *,
        output_directory: Path,
    ) -> RendererInstallStatus:
        del output_directory
        return RendererInstallStatus(
            backend=RenderBackend.HTML_PLAYWRIGHT,
            available=False,
            checks=(
                RendererInstallCheck(
                    code=InstallCheckCode.TEMPLATE,
                    passed=True,
                    message="HTML/CSS PDF template is available",
                ),
                RendererInstallCheck(
                    code=InstallCheckCode.FONT_BUNDLE,
                    passed=True,
                    message="bundled Noto fonts are available",
                ),
                RendererInstallCheck(
                    code=InstallCheckCode.CHROMIUM,
                    passed=False,
                    message="playwright Chromium is unavailable",
                ),
            ),
        )

    monkeypatch.setattr(
        "career_ai.cli.check_html_playwright_installation",
        fake_check_html_renderer_installation,
    )
    runner = CliRunner()

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "HTML renderer: unavailable" in result.stdout
    assert "noto_font_bundle: PASS" in result.stdout
    assert "playwright_chromium: FAIL" in result.stdout
    assert "install-renderer --html exits 14" in result.stdout


def test_cli_install_renderer_html_returns_14_on_install_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_install_html_renderer_chromium() -> InstallRendererResult:
        return InstallRendererResult(
            succeeded=False,
            exit_code=14,
            message="Chromium installation failed. Check network access.",
        )

    monkeypatch.setattr(
        "career_ai.cli.install_html_renderer_chromium",
        fake_install_html_renderer_chromium,
    )
    runner = CliRunner()

    result = runner.invoke(app, ["install-renderer", "--html"])

    assert result.exit_code == 14
    assert "Chromium installation failed" in result.stdout


def test_cli_analyze_runs_with_inline_resume_and_jd() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "analyze",
            "--resume-text",
            "Product analyst using Python SQL Streamlit dashboards.",
            "--jd-text",
            "Role: AI Product Analyst. Requires Python, SQL, Streamlit, LLM evaluation.",
        ],
    )

    assert result.exit_code == 0
    assert "AI Product Analyst" in result.stdout
    assert "Match score" in result.stdout
    assert "Quality: PASS" in result.stdout
    assert "Trace: " in result.stdout
    assert "Failed checks: none" in result.stdout
    assert "Completed tools:" in result.stdout
    assert "Skipped tools: none" in result.stdout
    assert "Memory summary: available" in result.stdout


def test_cli_analyze_prints_failed_quality_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    def run_with_failed_quality(
        *,
        resume_text: str,
        jd_text: str,
        prompt_dir: Path,
        llm_client: LLMClient,
        runtime_options: AgentRuntimeOptions | None = None,
    ) -> AgentRun:
        agent_run = run_real_career_agent(
            resume_text=resume_text,
            jd_text=jd_text,
            prompt_dir=prompt_dir,
            llm_client=llm_client,
            runtime_options=runtime_options,
        )
        failed_quality = CareerQualityReport(
            checks=[
                CareerQualityCheck(
                    name="factual_consistency",
                    passed=False,
                    message="Remove unsupported resume claims.",
                ),
                CareerQualityCheck(
                    name="prompt_strategy_available",
                    passed=True,
                    message="Prompt strategy comparison is available.",
                ),
            ],
        )
        return agent_run.model_copy(update={"quality_report": failed_quality})

    monkeypatch.setattr("career_ai.cli.run_career_agent", run_with_failed_quality)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "analyze",
            "--resume-text",
            "Product analyst using Python SQL Streamlit dashboards.",
            "--jd-text",
            "Role: AI Product Analyst. Requires Python, SQL, Streamlit, LLM evaluation.",
        ],
    )

    assert result.exit_code == 0
    assert "Quality: FAIL" in result.stdout
    assert "Failed checks: factual_consistency - Remove unsupported resume claims." in result.stdout


def test_cli_eval_prints_deterministic_eval_summary() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "eval",
            "--case-dir",
            "evals/career_cases",
            "--prompt-dir",
            "prompts",
        ],
    )

    assert result.exit_code == 0
    assert "Total cases:" in result.stdout
    assert "Passed cases:" in result.stdout
    assert "Failed cases:" in result.stdout
    assert "sample_product_analyst" in result.stdout


def test_cli_eval_matrix_prints_fake_model_harness_summary() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "eval-matrix",
            "--case-dir",
            "evals/career_cases",
            "--prompt-dir",
            "prompts",
        ],
    )

    assert result.exit_code == 0
    assert "Total rows: 1" in result.stdout
    assert "fake-default: fake/local-fake" in result.stdout
    assert "status=passed" in result.stdout
    assert "passed=" in result.stdout
    assert "Failed rows: 0" in result.stdout
    assert "failed check:" not in result.stdout
    assert "Unsupported capabilities: 0" in result.stdout
