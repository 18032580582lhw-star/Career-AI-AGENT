from __future__ import annotations

from pathlib import Path  # noqa: TC003 - pytest tmp_path uses concrete Path.

from typer.testing import CliRunner

from career_ai.cli import app


def test_prepare_defaults_to_result_summary_and_can_show_process_json(tmp_path: Path) -> None:
    # Given: immutable source files inside a local workspace.
    resume_path = tmp_path / "resume.txt"
    jd_path = tmp_path / "jd.txt"
    _ = resume_path.write_text("Built Python data workflows.", encoding="utf-8")
    _ = jd_path.write_text("Requires Python data workflow experience.", encoding="utf-8")
    runner = CliRunner()

    # When: prepare is run with the default terminal output mode.
    result = runner.invoke(
        app,
        [
            "prepare",
            "--workspace",
            str(tmp_path),
            "--resume-file",
            str(resume_path),
            "--jd-file",
            str(jd_path),
        ],
    )

    # Then: the terminal output is result-first and not raw process JSON.
    assert result.exit_code == 0
    assert "Prepared run:" in result.stdout
    assert "Request artifact:" in result.stdout
    assert '"proposal_schema"' not in result.stdout

    # When: process output is requested.
    process_result = runner.invoke(
        app,
        [
            "prepare",
            "--workspace",
            str(tmp_path),
            "--resume-file",
            str(resume_path),
            "--jd-file",
            str(jd_path),
            "--output",
            "process",
        ],
    )

    # Then: the same command includes the process JSON on demand.
    assert process_result.exit_code == 0
    assert "Prepared run:" in process_result.stdout
    assert '"proposal_schema"' in process_result.stdout
