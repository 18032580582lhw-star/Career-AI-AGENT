from __future__ import annotations

from pathlib import Path  # noqa: TC003 - pytest tmp_path uses concrete Path.

from typer.testing import CliRunner

from career_ai.cli import app
from career_ai.rendering.latex import LatexTemplateProfile
from career_ai.workspace import WorkspaceManifest


def test_cli_init_creates_workspace_manifest(tmp_path: Path) -> None:
    # Given
    runner = CliRunner()

    # When
    result = runner.invoke(app, ["init", "--workspace", str(tmp_path)])

    # Then
    assert result.exit_code == 0
    manifest = WorkspaceManifest.model_validate_json(result.stdout)
    assert manifest.schema_version == 1
    assert (tmp_path / ".career_ai" / "manifest.json").exists()


def test_cli_inspect_latex_outputs_template_profile(tmp_path: Path) -> None:
    # Given
    template = tmp_path / "resume.tex"
    _ = template.write_text(
        "\\documentclass{article}\\begin{document}\\section{Summary}Ada\\end{document}",
        encoding="utf-8",
    )
    runner = CliRunner()

    # When
    result = runner.invoke(
        app,
        ["inspect-latex", "--template-file", str(template), "--output", "json"],
    )

    # Then
    assert result.exit_code == 0
    profile = LatexTemplateProfile.model_validate_json(result.stdout)
    assert profile.documentclass == "article"
