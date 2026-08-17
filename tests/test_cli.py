import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from career_ai.application.career_fit_service import CareerFitRunResult
from career_ai.cli import app
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
    assert "Audit ID: " in result.stdout
    assert "Failed checks: none" in result.stdout
    assert "Workflow steps:" in result.stdout


def test_cli_analyze_json_is_typed_and_privacy_safe() -> None:
    runner = CliRunner()
    resume_text = "Private Candidate secret@example.com using Python and SQL."
    jd_text = (
        "Role: Data Analyst SECRET_JD_TOKEN api_key=secret-token "
        "C:\\Users\\Private\\jd.txt. Requires Python and SQL."
    )
    result = runner.invoke(
        app,
        [
            "analyze",
            "--resume-text",
            resume_text,
            "--jd-text",
            jd_text,
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    parsed = CareerFitRunResult.model_validate_json(result.stdout)
    assert parsed.workflow.report.jd_analysis.role_title == "Data Analyst"
    assert parsed.quality.passed
    assert parsed.run_record.operation == "career_fit_analysis"
    assert resume_text not in result.stdout
    assert jd_text not in result.stdout
    assert str(Path.cwd().resolve()) not in result.stdout
    assert "secret@example.com" not in result.stdout
    assert "SECRET_JD_TOKEN" not in result.stdout
    assert "secret-token" not in result.stdout
    assert "C:\\Users\\Private" not in result.stdout


def test_cli_import_does_not_eagerly_load_agent_or_llm_namespaces() -> None:
    # Given: a fresh interpreter imports the deterministic CLI composition root.
    script = (
        "import sys; import career_ai.cli; "
        "print(any(name == 'career_ai.agent' or name.startswith('career_ai.agent.') "
        "or name == 'career_ai.llm' or name.startswith('career_ai.llm.') "
        "for name in sys.modules))"
    )

    # When: import state is inspected before any doctor/eval-matrix command runs.
    completed = subprocess.run(  # noqa: S603 - fixed interpreter and inline probe.
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    # Then: analyze/eval startup remains independent of obsolete runtime namespaces.
    assert completed.stdout.strip() == "False"


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


def test_cli_eval_fails_when_case_directory_is_missing(tmp_path: Path) -> None:
    # Given: a case directory path that does not exist.
    missing_dir = tmp_path / "missing-cases"
    runner = CliRunner()

    # When: eval is run against the missing directory.
    result = runner.invoke(
        app,
        [
            "eval",
            "--case-dir",
            str(missing_dir),
            "--prompt-dir",
            "prompts",
        ],
    )

    # Then: the command fails loudly instead of reporting a successful zero-case run.
    assert result.exit_code == 2
    assert "Eval case directory does not exist" in result.stdout
    assert "Total cases: 0" not in result.stdout


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


def test_cli_eval_matrix_fails_when_case_directory_is_missing(tmp_path: Path) -> None:
    # Given: a case directory path that does not exist.
    missing_dir = tmp_path / "missing-cases"
    runner = CliRunner()

    # When: eval-matrix is run against the missing directory.
    result = runner.invoke(
        app,
        [
            "eval-matrix",
            "--case-dir",
            str(missing_dir),
            "--prompt-dir",
            "prompts",
        ],
    )

    # Then: the command fails loudly instead of marking fake-default as passed.
    assert result.exit_code == 2
    assert "Eval case directory does not exist" in result.stdout
    assert "status=passed passed=0 failed=0" not in result.stdout
