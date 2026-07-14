"""Renderer adapter for print-ready HTML and Playwright PDF outputs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from career_ai.rendering.artifacts import output_artifact
from career_ai.rendering.html_pdf_engine import (
    HtmlPdfEngine,
    SubprocessPlaywrightPdfEngine,
)
from career_ai.rendering.html_template import render_resume_html
from career_ai.rendering.models import RendererOutcome, RendererSuccess
from career_ai.tailoring.manifest_contracts import RenderBackend

if TYPE_CHECKING:
    from pathlib import Path

    from career_ai.tailoring.document_contracts import AcceptedResumeDocument

_HTML_NAME: Final = "resume.html"
_PDF_NAME: Final = "resume.pdf"
_HTML_MEDIA_TYPE: Final = "text/html; charset=utf-8"
_PDF_MEDIA_TYPE: Final = "application/pdf"


@final
class HtmlPlaywrightResumeRenderer:
    """Render accepted resume documents to static HTML and Playwright PDF."""

    def __init__(self, pdf_engine: HtmlPdfEngine | None = None) -> None:
        """Create a renderer with a production or test PDF engine."""
        self._pdf_engine = (
            SubprocessPlaywrightPdfEngine() if pdf_engine is None else pdf_engine
        )

    @property
    def backend(self) -> RenderBackend:
        """Return the registry backend implemented by this adapter."""
        return RenderBackend.HTML_PLAYWRIGHT

    def render(
        self,
        document: AcceptedResumeDocument,
        output_directory: Path,
    ) -> RendererOutcome:
        """Write HTML plus browser-produced PDF artifacts."""
        output_directory.mkdir(parents=True, exist_ok=True)
        html_path = output_directory / _HTML_NAME
        pdf_path = output_directory / _PDF_NAME
        _ = html_path.write_text(render_resume_html(document), encoding="utf-8")
        _ = self._pdf_engine.render_pdf(html_path, pdf_path)
        return RendererSuccess(
            backend=self.backend,
            artifacts=(
                output_artifact(
                    html_path,
                    relative_path=_HTML_NAME,
                    media_type=_HTML_MEDIA_TYPE,
                ),
                output_artifact(
                    pdf_path,
                    relative_path=_PDF_NAME,
                    media_type=_PDF_MEDIA_TYPE,
                ),
            ),
        )
