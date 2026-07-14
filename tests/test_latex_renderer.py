from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from career_ai.rendering.latex import (
    LatexCompilationFailure,
    LatexCompilationSuccess,
    LatexCompileErrorCode,
    LatexCompilerConfig,
    LatexSourceResumeRenderer,
    compile_latex_pdf,
    find_unsafe_latex_commands,
    inspect_latex_structure,
)
from career_ai.rendering.latex.models import LatexFindingCode
from career_ai.rendering.models import RendererSuccess
from career_ai.rendering.registry import RendererRegistry, RendererRequest
from career_ai.tailoring.manifest_contracts import RenderBackend
from tests.resume_document_helpers import (
    accepted_bundle,
    accepted_document_candidate_facts,
    accepted_resume_document,
)

if TYPE_CHECKING:
    import pytest


def _render_request(output_directory: Path) -> RendererRequest:
    draft, proposal, validation = accepted_bundle()
    return RendererRequest(
        draft=draft,
        proposal=proposal,
        validation=validation,
        candidate_facts=accepted_document_candidate_facts(),
        output_directory=output_directory,
    )


def test_system_latex_renderer_writes_safe_cjk_tex_through_registry(
    tmp_path: Path,
) -> None:
    # Given: an accepted CJK-capable resume document with LaTeX control characters
    registry = RendererRegistry((LatexSourceResumeRenderer(),))
    request = _render_request(tmp_path)

    # When: the registry renders LaTeX source
    outcome = registry.render(RenderBackend.LATEX_SOURCE, request)

    # Then: an inert system-template .tex artifact is written
    assert isinstance(outcome, RendererSuccess)
    assert outcome.backend is RenderBackend.LATEX_SOURCE
    artifact = outcome.artifacts[0]
    tex_path = tmp_path / artifact.path
    tex = tex_path.read_text(encoding="utf-8")
    assert artifact.media_type == "application/x-tex"
    assert "\\usepackage{fontspec}" in tex
    assert "Noto Sans CJK" in tex
    assert "Ada Example" in tex
    assert "Built typed APIs" in tex
    assert "@@RESUME_BODY@@" not in tex
    assert find_unsafe_latex_commands(tex) == ()
    structure = inspect_latex_structure(tex)
    assert tuple(section.title for section in structure.sections) == (
        "Professional Summary",
        "Skills",
        "Experience",
        "Projects",
        "Education",
        "Links",
    )


def test_latex_compiler_prefers_tectonic_then_falls_back_to_xelatex(
    tmp_path: Path,
) -> None:
    # Given: a fake tectonic command that fails and a fake XeLaTeX command that writes PDF
    fake_engine = tmp_path / "fake_latex_engine.py"
    _ = fake_engine.write_text(
        """
from pathlib import Path
from sys import argv, exit
if "--version" in argv:
    print(argv[1] + "-version")
    exit(0)
if argv[1] == "tectonic":
    exit(9)
pdf_path = Path(argv[-1]).with_suffix(".pdf")
pdf_path.write_bytes(b"%PDF-1.7\\n% fake xelatex\\n")
Path(argv[-1]).with_suffix(".aux").write_text("aux", encoding="utf-8")
exit(0)
""".strip(),
        encoding="utf-8",
    )
    tex_path = tmp_path / "resume.tex"
    _ = tex_path.write_text("\\begin{document}Ada\\end{document}", encoding="utf-8")
    config = LatexCompilerConfig(
        tectonic_command=(sys.executable, str(fake_engine), "tectonic"),
        xelatex_command=(sys.executable, str(fake_engine), "xelatex"),
    )

    # When: latex-pdf compilation runs
    result = compile_latex_pdf(tex_path, config=config)

    # Then: XeLaTeX fallback succeeds and temporary aux files are removed
    assert isinstance(result, LatexCompilationSuccess)
    assert result.backend is RenderBackend.LATEX_XELATEX
    assert result.pdf_path.read_bytes().startswith(b"%PDF-1.7")
    assert not tex_path.with_suffix(".aux").exists()


def test_latex_compiler_uses_restricted_cwd_for_relative_tex_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given: a relative .tex path and a fake XeLaTeX command that writes argv[-1].pdf
    monkeypatch.chdir(tmp_path)
    work_dir = Path("workspace")
    work_dir.mkdir()
    tex_path = work_dir / "resume.tex"
    _ = tex_path.write_text("\\begin{document}Ada\\end{document}", encoding="utf-8")
    fake_engine = tmp_path / "fake_latex_engine.py"
    _ = fake_engine.write_text(
        """
from pathlib import Path
from sys import argv, exit
if "--version" in argv:
    print("xelatex-version")
    exit(0)
if "/" in argv[-1] or "\\\\" in argv[-1]:
    exit(7)
Path(argv[-1]).with_suffix(".pdf").write_bytes(b"%PDF-1.7\\n")
exit(0)
""".strip(),
        encoding="utf-8",
    )
    relative_tex = tex_path

    # When: the compiler runs inside the .tex directory
    result = compile_latex_pdf(
        relative_tex,
        config=LatexCompilerConfig(
            tectonic_command=(),
            xelatex_command=(sys.executable, str(fake_engine), "xelatex"),
        ),
    )

    # Then: only the file name is passed to the engine and the PDF is found
    assert isinstance(result, LatexCompilationSuccess)
    assert result.pdf_path == relative_tex.with_suffix(".pdf")


def test_latex_compiler_reports_missing_engine_without_blocking_tex_generation(
    tmp_path: Path,
) -> None:
    # Given: LaTeX source was generated successfully
    renderer = LatexSourceResumeRenderer()
    source_outcome = renderer.render(accepted_resume_document(), tmp_path)
    tex_path = tmp_path / "resume.tex"

    # When: no Tectonic or XeLaTeX command is available
    result = compile_latex_pdf(
        tex_path,
        config=LatexCompilerConfig(tectonic_command=(), xelatex_command=()),
    )

    # Then: .tex remains available and latex-pdf fails with a stable missing-engine code
    assert isinstance(source_outcome, RendererSuccess)
    assert tex_path.exists()
    assert isinstance(result, LatexCompilationFailure)
    assert result.code is LatexCompileErrorCode.NO_ENGINE


def test_latex_security_scanner_ignores_comments_but_flags_active_shell_escape() -> None:
    # Given: one commented shell escape and one active shell escape package.
    source = "% \\write18{ignored}\n\\usepackage{shellesc}\nSafe text"

    # When: static LaTeX safety scanning runs without expanding commands.
    findings = find_unsafe_latex_commands(source)

    # Then: comment text stays inert while active shell-escape support is blocked.
    assert tuple(finding.code for finding in findings) == (
        LatexFindingCode.SHELL_ESCAPE_PACKAGE,
    )
