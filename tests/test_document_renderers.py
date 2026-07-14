from __future__ import annotations

from typing import TYPE_CHECKING

from docx import Document

from career_ai.rendering.docx import DocxResumeRenderer
from career_ai.rendering.html_fonts import check_font_bundle, html_font_css
from career_ai.rendering.html_installation import (
    InstallCheckCode,
    check_html_playwright_installation,
)
from career_ai.rendering.html_playwright import HtmlPlaywrightResumeRenderer
from career_ai.rendering.html_template import render_resume_html
from career_ai.rendering.models import RendererErrorCode, RendererSuccess, RenderFailure
from career_ai.rendering.registry import RendererRegistry, RendererRequest
from career_ai.tailoring.document_contracts import AcceptedResumeDocument
from career_ai.tailoring.manifest_contracts import RenderBackend
from tests.resume_document_helpers import (
    accepted_bundle,
    accepted_document_candidate_facts,
    accepted_resume_document,
)

if TYPE_CHECKING:
    from pathlib import Path


class RecordingPdfEngine:
    """Deterministic fake for the browser PDF boundary."""

    def __init__(self) -> None:
        self.calls: list[tuple[Path, Path]] = []

    def render_pdf(self, html_path: Path, pdf_path: Path) -> str:
        self.calls.append((html_path, pdf_path))
        _ = pdf_path.write_bytes(b"%PDF-1.4\n% fake playwright pdf\n")
        return "fake-playwright-1.0"


class MissingPdfEngine:
    """Deterministic fake for an unavailable Playwright dependency."""

    def render_pdf(self, html_path: Path, pdf_path: Path) -> str:
        del html_path, pdf_path
        missing_dependency = "playwright.sync_api"
        raise ImportError(missing_dependency)


class FailingPdfEngine:
    """Deterministic fake for a Playwright output failure."""

    def render_pdf(self, html_path: Path, pdf_path: Path) -> str:
        del html_path, pdf_path
        failure_message = "playwright failed"
        raise OSError(failure_message)


def _registry_request(output_directory: Path) -> RendererRequest:
    draft, proposal, validation = accepted_bundle()
    return RendererRequest(
        draft=draft,
        proposal=proposal,
        validation=validation,
        candidate_facts=accepted_document_candidate_facts(),
        output_directory=output_directory,
    )


def _docx_text(path: Path) -> str:
    document = Document(str(path))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def test_docx_renderer_writes_accepted_resume_sections_through_registry(
    tmp_path: Path,
) -> None:
    # Given
    registry = RendererRegistry((DocxResumeRenderer(),))

    # When
    outcome = registry.render(RenderBackend.DOCX, _registry_request(tmp_path))

    # Then
    assert isinstance(outcome, RendererSuccess)
    artifact = outcome.artifacts[0]
    rendered = tmp_path / artifact.path
    assert artifact.media_type == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert rendered.exists()
    text = _docx_text(rendered)
    assert "Ada Example" in text
    assert "Professional Summary" in text
    assert "Built typed APIs" in text
    assert "Portfolio" in text


def test_html_playwright_renderer_writes_escaped_html_and_pdf(
    tmp_path: Path,
) -> None:
    # Given
    engine = RecordingPdfEngine()
    renderer = HtmlPlaywrightResumeRenderer(pdf_engine=engine)
    document = accepted_resume_document()

    # When
    outcome = renderer.render(document, tmp_path)

    # Then
    assert isinstance(outcome, RendererSuccess)
    assert outcome.backend is RenderBackend.HTML_PLAYWRIGHT
    assert tuple(artifact.path for artifact in outcome.artifacts) == (
        "resume.html",
        "resume.pdf",
    )
    html_path = tmp_path / "resume.html"
    pdf_path = tmp_path / "resume.pdf"
    assert engine.calls == [(html_path, pdf_path)]
    assert pdf_path.read_bytes().startswith(b"%PDF-1.4")
    assert "<script" not in html_path.read_text(encoding="utf-8").casefold()


def test_html_css_pdf_template_uses_bundled_noto_fonts_without_network() -> None:
    # Given
    payload = accepted_resume_document().model_dump(mode="json")
    payload["identity"]["name"] = "Ada 中文 Example"
    document = AcceptedResumeDocument.model_validate(payload)

    # When
    html = render_resume_html(document)
    font_css = html_font_css()

    # Then
    assert 'data-renderer="html-css-pdf"' in html
    assert "@page" in html
    assert "@media print" in html
    assert "page-break-inside: avoid" in html
    assert "Noto Sans" in html
    assert "SC" in html
    assert "Ada 中文 Example" in html
    assert "fonts.googleapis" not in html
    assert "fonts.gstatic" not in html
    assert "https://" not in font_css


def test_font_bundle_contains_noto_sans_and_noto_sans_sc() -> None:
    # Given / When
    status = check_font_bundle()

    # Then
    assert status.available
    assert not status.missing_files


def test_html_renderer_escapes_visible_document_text(tmp_path: Path) -> None:
    # Given
    engine = RecordingPdfEngine()
    renderer = HtmlPlaywrightResumeRenderer(pdf_engine=engine)
    payload = accepted_resume_document().model_dump(mode="json")
    payload["identity"]["name"] = "<Ada Example>"
    document = AcceptedResumeDocument.model_validate(payload)

    # When
    outcome = renderer.render(document, tmp_path)

    # Then
    assert isinstance(outcome, RendererSuccess)
    html = (tmp_path / "resume.html").read_text(encoding="utf-8")
    assert "&lt;Ada Example&gt;" in html
    assert "<Ada Example>" not in html


def test_html_renderer_keeps_resume_urls_as_escaped_text_not_executable_links() -> None:
    # Given: an accepted document containing a valid source-backed URL.
    document = accepted_resume_document()

    # When: HTML is rendered for PDF conversion.
    html = render_resume_html(document)

    # Then: URL values remain visible text and are not emitted as executable anchors.
    assert "https://Example.COM/Ada" in html
    assert "<a " not in html
    assert "href=" not in html


def test_registry_reports_html_playwright_dependency_unavailable(
    tmp_path: Path,
) -> None:
    # Given
    registry = RendererRegistry(
        (HtmlPlaywrightResumeRenderer(pdf_engine=MissingPdfEngine()),),
    )

    # When
    outcome = registry.render(RenderBackend.HTML_PLAYWRIGHT, _registry_request(tmp_path))

    # Then
    assert isinstance(outcome, RenderFailure)
    assert outcome.code is RendererErrorCode.BACKEND_UNAVAILABLE


def test_registry_reports_html_playwright_output_failure(tmp_path: Path) -> None:
    # Given
    registry = RendererRegistry(
        (HtmlPlaywrightResumeRenderer(pdf_engine=FailingPdfEngine()),),
    )

    # When
    outcome = registry.render(RenderBackend.HTML_PLAYWRIGHT, _registry_request(tmp_path))

    # Then
    assert isinstance(outcome, RenderFailure)
    assert outcome.code is RendererErrorCode.OUTPUT_FAILED


def test_html_renderer_install_check_reports_local_prerequisites(
    tmp_path: Path,
) -> None:
    # Given / When
    status = check_html_playwright_installation(
        launch_browser=False,
        output_directory=tmp_path,
    )

    # Then
    check_codes = tuple(check.code for check in status.checks)
    assert InstallCheckCode.TEMPLATE in check_codes
    assert InstallCheckCode.FONT_BUNDLE in check_codes
    assert InstallCheckCode.WRITE_PERMISSION in check_codes
    assert InstallCheckCode.PYTHON_PACKAGE in check_codes
    assert status.backend is RenderBackend.HTML_PLAYWRIGHT
