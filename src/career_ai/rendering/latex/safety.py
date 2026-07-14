"""Static detection of unsafe LaTeX primitives and external inputs."""

import re
from pathlib import PurePosixPath
from typing import Final

from career_ai.rendering.latex.models import LatexFinding, LatexFindingCode
from career_ai.rendering.latex.syntax import mask_latex_comments

_COMMAND_PATTERNS: Final = (
    r"\\(?P<shell>write18|ShellEscape)(?![A-Za-z@])",
    r"\\(?P<lua>directlua|latelua)(?![A-Za-z@])",
    r"\\(?P<write>openout|closeout|write(?!18))(?![A-Za-z@])",
    r"\\(?P<read>openin|closein|read)(?![A-Za-z@])",
)
_COMMANDS: Final = re.compile("|".join(_COMMAND_PATTERNS))
_INPUT: Final = re.compile(
    r"\\(?P<command>input|include)(?![A-Za-z@])\s*\{(?P<target>[^{}]*)\}",
)
_SHELL_ESCAPE_PACKAGE: Final = re.compile(
    r"\\usepackage(?:\[[^\[\]{}]*\])?\s*\{(?P<package>shellesc)\}",
)
_WINDOWS_DRIVE: Final = re.compile(r"^[A-Za-z]:[/\\]")
_URL_SCHEME: Final = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def find_unsafe_latex_commands(source: str) -> tuple[LatexFinding, ...]:
    """Return ordered findings without expanding commands or reading referenced files."""
    masked = mask_latex_comments(source)
    findings = [_command_finding(source, match) for match in _COMMANDS.finditer(masked)]
    findings.extend(
        _finding(
            source,
            offset=match.start(),
            code=LatexFindingCode.SHELL_ESCAPE_PACKAGE,
            command="usepackage",
            target=match.group("package"),
        )
        for match in _SHELL_ESCAPE_PACKAGE.finditer(masked)
    )
    for match in _INPUT.finditer(masked):
        target = match.group("target").strip()
        code = _unsafe_input_code(target)
        if code is not None:
            findings.append(
                _finding(
                    source,
                    offset=match.start(),
                    code=code,
                    command=match.group("command"),
                    target=target,
                ),
            )
    return tuple(sorted(findings, key=lambda finding: (finding.line, finding.column)))


def _command_finding(source: str, match: re.Match[str]) -> LatexFinding:
    if match.group("shell") is not None:
        code = LatexFindingCode.SHELL_ESCAPE
        command = match.group("shell")
    elif match.group("lua") is not None:
        code = LatexFindingCode.LUA_EXECUTION
        command = match.group("lua")
    elif match.group("write") is not None:
        code = LatexFindingCode.FILE_WRITE
        command = match.group("write")
    else:
        code = LatexFindingCode.FILE_READ
        command = match.group("read")
    return _finding(source, offset=match.start(), code=code, command=command)


def _unsafe_input_code(target: str) -> LatexFindingCode | None:
    if "\\" in target and not _WINDOWS_DRIVE.match(target) and not target.startswith("\\\\"):
        return LatexFindingCode.DYNAMIC_INPUT_PATH
    normalized = target.replace("\\", "/")
    if (
        not normalized
        or normalized.startswith("/")
        or _WINDOWS_DRIVE.match(target)
        or _URL_SCHEME.match(target)
    ):
        return LatexFindingCode.OUT_OF_ROOT_INPUT
    depth = 0
    for part in PurePosixPath(normalized).parts:
        if part == "..":
            if depth == 0:
                return LatexFindingCode.OUT_OF_ROOT_INPUT
            depth -= 1
        elif part not in {".", ""}:
            depth += 1
    return None


def _finding(
    source: str,
    *,
    offset: int,
    code: LatexFindingCode,
    command: str,
    target: str | None = None,
) -> LatexFinding:
    line = source.count("\n", 0, offset) + 1
    line_start = source.rfind("\n", 0, offset) + 1
    return LatexFinding(
        code=code,
        command=command,
        line=line,
        column=offset - line_start + 1,
        target=target,
    )
