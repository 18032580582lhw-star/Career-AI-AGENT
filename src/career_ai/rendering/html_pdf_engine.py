"""Playwright PDF engine for HTML resume rendering."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from importlib.util import find_spec
from typing import TYPE_CHECKING, Final, Protocol

if TYPE_CHECKING:
    from pathlib import Path

_PLAYWRIGHT_MODULE: Final = "playwright.sync_api"
_PLAYWRIGHT_PDF_SCRIPT: Final = """
from pathlib import Path
from sys import argv

from playwright.sync_api import sync_playwright

html_path = Path(argv[1]).resolve().as_uri()
pdf_path = Path(argv[2]).resolve()
with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page()
    page.goto(html_path, wait_until="networkidle")
    page.pdf(path=str(pdf_path), format="Letter", print_background=True)
    browser.close()
"""


class HtmlPdfEngine(Protocol):
    """Minimal browser PDF boundary used by the HTML renderer."""

    def render_pdf(self, html_path: Path, pdf_path: Path) -> str:
        """Render one local HTML file to PDF and return the engine version."""
        ...


@dataclass(frozen=True, slots=True)
class SubprocessPlaywrightPdfEngine:
    """Playwright PDF engine isolated behind a typed subprocess boundary."""

    timeout_seconds: int = 60

    def render_pdf(self, html_path: Path, pdf_path: Path) -> str:
        """Invoke Playwright's Chromium PDF support for one local HTML file."""
        require_playwright_module()
        try:
            completed = subprocess.run(  # noqa: S603 - constant script via current Python.
                [sys.executable, "-c", _PLAYWRIGHT_PDF_SCRIPT, str(html_path), str(pdf_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            timeout_message = "playwright timed out"
            raise OSError(timeout_message) from error
        if completed.returncode != 0:
            failure_message = "playwright failed"
            raise OSError(failure_message)
        return "playwright-chromium"


def require_playwright_module() -> None:
    """Raise ImportError when Playwright's sync API cannot be imported."""
    try:
        playwright_spec = find_spec(_PLAYWRIGHT_MODULE)
    except ModuleNotFoundError as error:
        raise ImportError(_PLAYWRIGHT_MODULE) from error
    if playwright_spec is None:
        raise ImportError(_PLAYWRIGHT_MODULE)
