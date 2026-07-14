"""Typed document rendering contracts and registry."""

from career_ai.rendering.ats_normalization import (
    AtsNormalizationOptions,
    AtsPunctuationStyle,
    normalize_accepted_resume_document,
    normalize_ats_contact,
    normalize_ats_email,
    normalize_ats_text,
    normalize_ats_url,
)
from career_ai.rendering.docx import DocxResumeRenderer
from career_ai.rendering.html_installation import (
    InstallCheckCode,
    RendererInstallCheck,
    RendererInstallStatus,
    check_html_playwright_installation,
)
from career_ai.rendering.html_pdf_engine import HtmlPdfEngine, SubprocessPlaywrightPdfEngine
from career_ai.rendering.html_playwright import HtmlPlaywrightResumeRenderer
from career_ai.rendering.html_template import (
    HTML_RENDERER_MARKER,
    PRINT_CSS,
    render_resume_html,
)
from career_ai.rendering.latex import LatexSourceResumeRenderer
from career_ai.rendering.registry import (
    RendererErrorCode,
    RendererOutcome,
    RendererRegistry,
    RendererRegistryError,
    RendererRequest,
    RendererSuccess,
    RenderFailure,
    ResumeRenderer,
)

__all__ = [
    "HTML_RENDERER_MARKER",
    "PRINT_CSS",
    "AtsNormalizationOptions",
    "AtsPunctuationStyle",
    "DocxResumeRenderer",
    "HtmlPdfEngine",
    "HtmlPlaywrightResumeRenderer",
    "InstallCheckCode",
    "LatexSourceResumeRenderer",
    "RenderFailure",
    "RendererErrorCode",
    "RendererInstallCheck",
    "RendererInstallStatus",
    "RendererOutcome",
    "RendererRegistry",
    "RendererRegistryError",
    "RendererRequest",
    "RendererSuccess",
    "ResumeRenderer",
    "SubprocessPlaywrightPdfEngine",
    "check_html_playwright_installation",
    "normalize_accepted_resume_document",
    "normalize_ats_contact",
    "normalize_ats_email",
    "normalize_ats_text",
    "normalize_ats_url",
    "render_resume_html",
]
