"""Tectonic-first and XeLaTeX fallback compiler boundary."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from career_ai.rendering.latex.models import (
    LatexCompilationFailure,
    LatexCompilationResult,
    LatexCompilationSuccess,
    LatexCompileErrorCode,
    LatexCompilerConfig,
)
from career_ai.tailoring.manifest_contracts import RenderBackend

if TYPE_CHECKING:
    from pathlib import Path

_AUXILIARY_SUFFIXES: Final = (".aux", ".log", ".out")


@dataclass(frozen=True, slots=True)
class _EngineCandidate:
    backend: RenderBackend
    command: tuple[str, ...]


def compile_latex_pdf(
    tex_path: Path,
    *,
    config: LatexCompilerConfig | None = None,
) -> LatexCompilationResult:
    """Compile one .tex file with Tectonic first, then XeLaTeX."""
    active_config = LatexCompilerConfig() if config is None else config
    candidates = _engine_candidates(active_config)
    if not candidates:
        return LatexCompilationFailure(
            code=LatexCompileErrorCode.NO_ENGINE,
            message="Tectonic and XeLaTeX are unavailable",
        )
    last_failure: LatexCompilationFailure | None = None
    for candidate in candidates:
        result = _compile_with_engine(tex_path, candidate, active_config.timeout_seconds)
        match result:
            case LatexCompilationSuccess():
                return result
            case LatexCompilationFailure():
                last_failure = result
    if last_failure is not None:
        return last_failure
    return LatexCompilationFailure(
        code=LatexCompileErrorCode.NO_ENGINE,
        message="Tectonic and XeLaTeX are unavailable",
    )


def _engine_candidates(config: LatexCompilerConfig) -> tuple[_EngineCandidate, ...]:
    candidates: list[_EngineCandidate] = []
    tectonic = _resolve_command(config.tectonic_command, executable="tectonic")
    if tectonic is not None:
        candidates.append(
            _EngineCandidate(backend=RenderBackend.LATEX_TECTONIC, command=tectonic),
        )
    xelatex = _resolve_command(config.xelatex_command, executable="xelatex")
    if xelatex is not None:
        candidates.append(
            _EngineCandidate(backend=RenderBackend.LATEX_XELATEX, command=xelatex),
        )
    return tuple(candidates)


def _resolve_command(
    configured: tuple[str, ...] | None,
    *,
    executable: str,
) -> tuple[str, ...] | None:
    if configured == ():
        return None
    if configured is not None:
        return configured
    discovered = shutil.which(executable)
    if discovered is None:
        return None
    return (discovered,)


def _compile_with_engine(
    tex_path: Path,
    candidate: _EngineCandidate,
    timeout_seconds: int,
) -> LatexCompilationResult:
    command = _compile_command(candidate, tex_path)
    try:
        completed = subprocess.run(  # noqa: S603 - argv-only configured engine.
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=tex_path.parent,
        )
    except subprocess.TimeoutExpired:
        return LatexCompilationFailure(
            code=LatexCompileErrorCode.TIMEOUT,
            backend=candidate.backend,
            message="LaTeX engine timed out",
        )
    except OSError:
        return LatexCompilationFailure(
            code=LatexCompileErrorCode.ENGINE_FAILED,
            backend=candidate.backend,
            message="LaTeX engine could not start",
        )
    try:
        return _compile_result(tex_path, candidate, completed)
    finally:
        _cleanup_auxiliary_files(tex_path)


def _compile_command(candidate: _EngineCandidate, tex_path: Path) -> list[str]:
    match candidate.backend:
        case RenderBackend.LATEX_TECTONIC:
            return [*candidate.command, str(tex_path.name)]
        case RenderBackend.LATEX_XELATEX:
            return [
                *candidate.command,
                "-no-shell-escape",
                "-halt-on-error",
                "-interaction=nonstopmode",
                str(tex_path.name),
            ]
        case RenderBackend.DOCX | RenderBackend.HTML_PLAYWRIGHT | RenderBackend.LATEX_SOURCE:
            return [*candidate.command, str(tex_path)]


def _compile_result(
    tex_path: Path,
    candidate: _EngineCandidate,
    completed: subprocess.CompletedProcess[str],
) -> LatexCompilationResult:
    pdf_path = tex_path.with_suffix(".pdf")
    if completed.returncode != 0:
        return LatexCompilationFailure(
            code=LatexCompileErrorCode.ENGINE_FAILED,
            backend=candidate.backend,
            message="LaTeX engine failed",
            first_error=_first_error(completed.stderr, completed.stdout),
        )
    if not pdf_path.exists():
        return LatexCompilationFailure(
            code=LatexCompileErrorCode.OUTPUT_MISSING,
            backend=candidate.backend,
            message="LaTeX engine did not produce a PDF",
            first_error=_first_error(completed.stderr, completed.stdout),
        )
    return LatexCompilationSuccess(
        backend=candidate.backend,
        pdf_path=pdf_path,
        engine_version=_engine_version(candidate),
    )


def _engine_version(candidate: _EngineCandidate) -> str:
    try:
        completed = subprocess.run(  # noqa: S603 - argv-only configured engine.
            [*candidate.command, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return candidate.backend.value
    version = _first_error(completed.stdout, completed.stderr)
    return candidate.backend.value if version is None else version


def _first_error(primary: str, secondary: str) -> str | None:
    for raw_line in (*primary.splitlines(), *secondary.splitlines()):
        line = raw_line.strip()
        if line:
            return line[:500]
    return None


def _cleanup_auxiliary_files(tex_path: Path) -> None:
    for suffix in _AUXILIARY_SUFFIXES:
        path = tex_path.with_suffix(suffix)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            continue
