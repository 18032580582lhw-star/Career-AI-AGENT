"""Installation checks for the HTML/CSS PDF renderer."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import Final, assert_never

from career_ai.rendering.html_fonts import check_font_bundle
from career_ai.rendering.html_pdf_engine import require_playwright_module
from career_ai.rendering.html_template import HTML_RENDERER_MARKER, PRINT_CSS
from career_ai.tailoring.manifest_contracts import RenderBackend

CHROMIUM_MISSING_EXIT_CODE: Final = 14
_PLAYWRIGHT_VERSION_COMMAND: Final = (sys.executable, "-m", "playwright", "--version")
_PLAYWRIGHT_MISSING_MESSAGE: Final = (
    "Playwright is not importable. Install project dependencies first, then rerun: "
    "career-ai-agent install-renderer --html"
)
_INSTALL_TIMEOUT_MESSAGE: Final = (
    "Chromium installation timed out. Retry with network access or preinstall "
    "Playwright Chromium."
)
_INSTALL_START_FAILURE_MESSAGE: Final = (
    "Chromium installer could not start. Verify Python and Playwright, then rerun: "
    "python -m playwright install chromium"
)
_INSTALL_FAILED_MESSAGE: Final = (
    "Chromium installation failed. Check network access, proxy settings, or run: "
    "python -m playwright install chromium"
)
_PLAYWRIGHT_BROWSER_SCRIPT: Final = """
from playwright.sync_api import sync_playwright

with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    browser.close()
"""


@unique
class InstallCheckCode(StrEnum):
    """Stable install check identifiers for HTML renderer dependencies."""

    PYTHON_PACKAGE = "playwright_python_package"
    CLI = "playwright_cli"
    CHROMIUM = "playwright_chromium"
    TEMPLATE = "html_css_template"
    FONT_BUNDLE = "noto_font_bundle"
    WRITE_PERMISSION = "output_write_permission"


@dataclass(frozen=True, slots=True)
class RendererInstallCheck:
    """One deterministic renderer installation check result."""

    code: InstallCheckCode
    passed: bool
    message: str


@dataclass(frozen=True, slots=True)
class RendererInstallStatus:
    """Installation status for a renderer backend."""

    backend: RenderBackend
    available: bool
    checks: tuple[RendererInstallCheck, ...]


@dataclass(frozen=True, slots=True)
class InstallRendererResult:
    """Result of installing an optional renderer dependency."""

    succeeded: bool
    exit_code: int
    message: str


def check_html_playwright_installation(
    *,
    launch_browser: bool = True,
    output_directory: Path | None = None,
    timeout_seconds: int = 20,
) -> RendererInstallStatus:
    """Check whether the local HTML/Playwright renderer can produce PDFs."""
    package_check = _package_check()
    checks = [
        _template_check(),
        _font_bundle_check(),
        _write_permission_check(output_directory),
        package_check,
    ]
    if package_check.passed:
        checks.append(
            _subprocess_check(
                InstallCheckCode.CLI,
                _PLAYWRIGHT_VERSION_COMMAND,
                timeout_seconds,
            ),
        )
        if launch_browser:
            checks.append(
                _subprocess_check(
                    InstallCheckCode.CHROMIUM,
                    (sys.executable, "-c", _PLAYWRIGHT_BROWSER_SCRIPT),
                    timeout_seconds,
                ),
            )
    return RendererInstallStatus(
        backend=RenderBackend.HTML_PLAYWRIGHT,
        available=all(check.passed for check in checks),
        checks=tuple(checks),
    )


def install_html_renderer_chromium(timeout_seconds: int = 600) -> InstallRendererResult:
    """Install Playwright Chromium for HTML PDF rendering."""
    try:
        require_playwright_module()
    except ImportError:
        return _install_failure(_PLAYWRIGHT_MISSING_MESSAGE)
    try:
        completed = subprocess.run(
            (sys.executable, "-m", "playwright", "install", "chromium"),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return _install_failure(_INSTALL_TIMEOUT_MESSAGE)
    except OSError:
        return _install_failure(_INSTALL_START_FAILURE_MESSAGE)
    if completed.returncode != 0:
        return _install_failure(_INSTALL_FAILED_MESSAGE)
    return InstallRendererResult(
        succeeded=True,
        exit_code=0,
        message="Playwright Chromium is installed for HTML PDF rendering.",
    )


def _install_failure(message: str) -> InstallRendererResult:
    return InstallRendererResult(
        succeeded=False,
        exit_code=CHROMIUM_MISSING_EXIT_CODE,
        message=message,
    )


def _package_check() -> RendererInstallCheck:
    try:
        require_playwright_module()
    except ImportError:
        return _failed_check(
            InstallCheckCode.PYTHON_PACKAGE,
            "playwright Python package is not installed",
        )
    return RendererInstallCheck(
        code=InstallCheckCode.PYTHON_PACKAGE,
        passed=True,
        message="playwright Python package is importable",
    )


def _template_check() -> RendererInstallCheck:
    marker_present = HTML_RENDERER_MARKER == "html-css-pdf" and "@page" in PRINT_CSS
    return RendererInstallCheck(
        code=InstallCheckCode.TEMPLATE,
        passed=marker_present,
        message=(
            "HTML/CSS PDF template is available"
            if marker_present
            else "HTML/CSS PDF template is missing required print markers"
        ),
    )


def _font_bundle_check() -> RendererInstallCheck:
    status = check_font_bundle()
    return RendererInstallCheck(
        code=InstallCheckCode.FONT_BUNDLE,
        passed=status.available,
        message=(
            "bundled Noto Sans and Noto Sans SC fonts are available"
            if status.available
            else f"font bundle is missing: {', '.join(status.missing_files)}"
        ),
    )


def _write_permission_check(output_directory: Path | None) -> RendererInstallCheck:
    if output_directory is None:
        output_directory = Path.cwd()
    check_path = output_directory / ".career-ai-render-write-check"
    try:
        output_directory.mkdir(parents=True, exist_ok=True)
        _ = check_path.write_text("ok", encoding="utf-8")
        check_path.unlink()
    except OSError:
        return _failed_check(
            InstallCheckCode.WRITE_PERMISSION,
            f"cannot write renderer outputs under {output_directory}",
        )
    return RendererInstallCheck(
        code=InstallCheckCode.WRITE_PERMISSION,
        passed=True,
        message=f"renderer output directory is writable: {output_directory}",
    )


def _subprocess_check(
    code: InstallCheckCode,
    command: tuple[str, ...],
    timeout_seconds: int,
) -> RendererInstallCheck:
    try:
        completed = subprocess.run(  # noqa: S603 - constant command from this module.
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return _failed_check(code, "check timed out")
    except OSError:
        return _failed_check(code, "check could not start")
    if completed.returncode != 0:
        return _failed_check(code, _check_failure_message(code))
    return RendererInstallCheck(
        code=code,
        passed=True,
        message=_check_success_message(code),
    )


def _failed_check(code: InstallCheckCode, message: str) -> RendererInstallCheck:
    return RendererInstallCheck(code=code, passed=False, message=message)


def _check_success_message(code: InstallCheckCode) -> str:
    match code:
        case InstallCheckCode.PYTHON_PACKAGE:
            return "playwright Python package is importable"
        case InstallCheckCode.CLI:
            return "playwright CLI is available"
        case InstallCheckCode.CHROMIUM:
            return "playwright Chromium can launch"
        case (
            InstallCheckCode.TEMPLATE
            | InstallCheckCode.FONT_BUNDLE
            | InstallCheckCode.WRITE_PERMISSION
        ):
            return "renderer local prerequisite is available"
        case _:
            assert_never(code)


def _check_failure_message(code: InstallCheckCode) -> str:
    match code:
        case InstallCheckCode.PYTHON_PACKAGE:
            return "playwright Python package is not installed"
        case InstallCheckCode.CLI:
            return "playwright CLI is unavailable"
        case InstallCheckCode.CHROMIUM:
            return (
                "playwright Chromium is unavailable; run "
                "career-ai-agent install-renderer --html"
            )
        case InstallCheckCode.TEMPLATE:
            return "HTML/CSS PDF template is unavailable"
        case InstallCheckCode.FONT_BUNDLE:
            return "bundled Noto fonts are unavailable"
        case InstallCheckCode.WRITE_PERMISSION:
            return "renderer output directory is not writable"
        case _:
            assert_never(code)
