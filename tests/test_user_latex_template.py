from __future__ import annotations

import sys
from hashlib import sha256
from typing import TYPE_CHECKING

import pytest

from career_ai.rendering.latex import (
    LatexCompilationSuccess,
    LatexCompilerConfig,
    LatexFindingCode,
    LatexTemplatePatchError,
    compile_latex_pdf,
    find_unsafe_latex_commands,
    inspect_user_latex_template,
    patch_user_latex_template,
)
from career_ai.tailoring.document_contracts import ResumeSection
from career_ai.tailoring.manifest_contracts import RenderBackend
from tests.resume_document_helpers import accepted_resume_document

if TYPE_CHECKING:
    from pathlib import Path


_USER_TEMPLATE = r"""
\documentclass{article}
\newcommand{\resumeHeader}[1]{#1}
\begin{document}
\resumeHeader{Existing Header}
% career-ai:begin summary
Old summary
% career-ai:end summary
% career-ai:begin skills
Old skills
% career-ai:end skills
\section{Experience}
Keep layout
\end{document}
""".strip()


def test_inspect_user_template_profiles_marked_sections_and_hashes() -> None:
    # Given: a user-owned resume.tex with explicit career-ai markers
    # When: it is inspected without patching the source
    profile = inspect_user_latex_template(_USER_TEMPLATE)

    # Then: document identity, preamble, commands, and writable sections are explicit
    assert profile.documentclass == "article"
    assert profile.template_hash == sha256(_USER_TEMPLATE.encode("utf-8")).hexdigest()
    assert any(command.startswith("\\newcommand") for command in profile.custom_commands)
    assert profile.requires_mapping_confirmation is False
    assert tuple(mapping.section for mapping in profile.section_mappings) == (
        ResumeSection.SUMMARY,
        ResumeSection.SKILLS,
    )
    assert profile.unsafe_findings == ()


def test_patch_user_template_replaces_only_confirmed_marker_ranges(
    tmp_path: Path,
) -> None:
    # Given: an immutable user template file and an accepted document
    source_path = tmp_path / "resume.tex"
    _ = source_path.write_text(_USER_TEMPLATE, encoding="utf-8")
    original_hash = sha256(source_path.read_bytes()).hexdigest()
    profile = inspect_user_latex_template(_USER_TEMPLATE)

    # When: confirmed marker ranges are patched into a new output file
    patched = patch_user_latex_template(
        source=_USER_TEMPLATE,
        profile=profile,
        document=accepted_resume_document(),
    )
    output_path = tmp_path / "outputs" / "resume.tex"
    output_path.parent.mkdir()
    _ = output_path.write_text(patched, encoding="utf-8")

    # Then: only target ranges change and the original template remains byte-stable
    assert sha256(source_path.read_bytes()).hexdigest() == original_hash
    assert "\\newcommand{\\resumeHeader}[1]{#1}" in patched
    assert "\\resumeHeader{Existing Header}" in patched
    assert "Old summary" not in patched
    assert "Old skills" not in patched
    assert "Built typed APIs" in patched
    assert "Keep layout" in patched


def test_user_template_without_markers_requires_confirmed_mapping() -> None:
    # Given: a template with sections but no explicit career-ai markers
    source = "\\documentclass{article}\\begin{document}\\section{Summary}Old\\end{document}"
    profile = inspect_user_latex_template(source)

    # When / Then: automatic patching refuses to guess write ranges
    assert profile.requires_mapping_confirmation is True
    with pytest.raises(LatexTemplatePatchError):
        _ = patch_user_latex_template(
            source=source,
            profile=profile,
            document=accepted_resume_document(),
        )


def test_user_template_rejects_executable_or_external_latex() -> None:
    # Given: commands that could execute or read outside the template root
    source = r"""
\documentclass{article}
\usepackage{shellesc}
\begin{document}
\write18{calc}
\directlua{os.execute('whoami')}
\input{../secrets.tex}
\end{document}
"""

    # When: the source is scanned and inspected
    findings = find_unsafe_latex_commands(source)
    profile = inspect_user_latex_template(source)

    # Then: every executable or external primitive is rejected before patching
    assert LatexFindingCode.SHELL_ESCAPE_PACKAGE in {
        finding.code for finding in findings
    }
    assert profile.unsafe_findings
    with pytest.raises(LatexTemplatePatchError):
        _ = patch_user_latex_template(
            source=source,
            profile=profile,
            document=accepted_resume_document(),
        )


def test_patched_user_template_can_use_same_latex_compiler_runner(
    tmp_path: Path,
) -> None:
    # Given: a patched user template and a fake Tectonic-compatible engine
    source = patch_user_latex_template(
        source=_USER_TEMPLATE,
        profile=inspect_user_latex_template(_USER_TEMPLATE),
        document=accepted_resume_document(),
    )
    tex_path = tmp_path / "resume.tex"
    _ = tex_path.write_text(source, encoding="utf-8")
    fake_engine = tmp_path / "fake_latex_engine.py"
    _ = fake_engine.write_text(
        """
from pathlib import Path
from sys import argv, exit
if "--version" in argv:
    print("tectonic-version")
    exit(0)
Path(argv[-1]).with_suffix(".pdf").write_bytes(b"%PDF-1.7\\n% fake tectonic\\n")
exit(0)
""".strip(),
        encoding="utf-8",
    )

    # When: the same compiler runner compiles the patched template
    result = compile_latex_pdf(
        tex_path,
        config=LatexCompilerConfig(
            tectonic_command=(sys.executable, str(fake_engine), "tectonic"),
            xelatex_command=(),
        ),
    )

    # Then: Tectonic remains the preferred backend
    assert isinstance(result, LatexCompilationSuccess)
    assert result.backend is RenderBackend.LATEX_TECTONIC
