"""Print-ready HTML/CSS resume template for browser PDF rendering."""

from __future__ import annotations

from html import escape
from typing import Final, assert_never

from career_ai.rendering.html_fonts import html_font_css
from career_ai.tailoring.document_contracts import (
    AcceptedResumeDocument,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    ResumeSection,
)

HTML_RENDERER_MARKER: Final = "html-css-pdf"
PRINT_CSS: Final = """
@page {
  size: Letter;
  margin: 0.58in 0.62in;
}
* {
  box-sizing: border-box;
}
html {
  color: #111827;
  font-family: 'Noto Sans', 'SC', Arial, Helvetica, sans-serif;
  font-size: 10.5pt;
  line-height: 1.38;
}
body {
  margin: 0;
}
main {
  margin: 0 auto;
  max-width: 7.4in;
}
h1 {
  font-size: 21pt;
  margin: 0 0 0.04in;
}
h2 {
  border-bottom: 1px solid #9ca3af;
  font-size: 11pt;
  letter-spacing: 0;
  margin: 0.18in 0 0.07in;
  padding-bottom: 0.03in;
}
h3 {
  font-size: 10.5pt;
  margin: 0.09in 0 0.02in;
}
p {
  margin: 0.03in 0;
}
ul {
  margin: 0.04in 0 0 0.18in;
  padding: 0;
}
li {
  margin: 0.025in 0;
}
section,
article {
  break-inside: avoid;
  page-break-inside: avoid;
}
.contact,
.meta {
  color: #374151;
  font-size: 9pt;
}
@media print {
  a {
    color: inherit;
    text-decoration: none;
  }
}
"""


def render_resume_html(document: AcceptedResumeDocument) -> str:
    """Return deterministic print-ready HTML for one accepted resume document."""
    sections = "\n".join(
        _render_section(document, section) for section in document.section_order
    )
    return (
        "<!doctype html>\n"
        f'<html lang="{escape(document.output_language)}" data-renderer="{HTML_RENDERER_MARKER}">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Accepted Resume</title>\n"
        f"<style>\n{html_font_css()}{PRINT_CSS}</style>\n"
        "</head>\n"
        "<body><main>\n"
        f"<h1>{escape(document.identity.name)}</h1>\n"
        f"{_optional_paragraph(document.identity.headline, css_class='meta')}\n"
        f"{_contact_block(document)}\n"
        f"{sections}\n"
        "</main></body>\n"
        "</html>\n"
    )


def _render_section(document: AcceptedResumeDocument, section: ResumeSection) -> str:
    match section:
        case ResumeSection.SUMMARY:
            return _bullet_section(
                "Professional Summary",
                tuple(item.text for item in document.professional_summary),
            )
        case ResumeSection.SKILLS:
            return _bullet_section("Skills", tuple(item.text for item in document.skills))
        case ResumeSection.EXPERIENCE:
            entries = "".join(_experience_html(item) for item in document.experience)
            return f"<section><h2>Experience</h2>{entries}</section>"
        case ResumeSection.PROJECTS:
            entries = "".join(_project_html(item) for item in document.projects)
            return f"<section><h2>Projects</h2>{entries}</section>"
        case ResumeSection.EDUCATION:
            entries = "".join(_education_html(item) for item in document.education)
            return f"<section><h2>Education</h2>{entries}</section>"
        case ResumeSection.LINKS:
            items = tuple(f"{item.label}: {item.url}" for item in document.links)
            return _bullet_section("Links", items)
        case _:
            assert_never(section)


def _contact_block(document: AcceptedResumeDocument) -> str:
    contacts = " | ".join(escape(item) for item in document.identity.contact_lines)
    if not contacts:
        return ""
    return f'<p class="contact">{contacts}</p>'


def _optional_paragraph(value: str | None, *, css_class: str) -> str:
    if value is None:
        return ""
    return f'<p class="{css_class}">{escape(value)}</p>'


def _bullet_section(title: str, items: tuple[str, ...]) -> str:
    return f"<section><h2>{escape(title)}</h2>{_bullet_list(items)}</section>"


def _bullet_list(items: tuple[str, ...]) -> str:
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def _experience_html(item: ExperienceEntry) -> str:
    return "".join(
        (
            f"<article><h3>{escape(item.title)}, {escape(item.organization)}</h3>",
            f'<p class="meta">{escape(_experience_meta(item.date_range, item.location))}</p>',
            _bullet_list(tuple(bullet.text for bullet in item.bullets)),
            "</article>",
        ),
    )


def _project_html(item: ProjectEntry) -> str:
    return "".join(
        (
            f"<article><h3>{escape(item.name)}</h3>",
            _optional_paragraph(item.subtitle, css_class="meta"),
            _bullet_list(tuple(bullet.text for bullet in item.bullets)),
            "</article>",
        ),
    )


def _education_html(item: EducationEntry) -> str:
    return "".join(
        (
            f"<article><h3>{escape(item.institution)}</h3>",
            f"<p>{escape(_education_meta(item.credential, item.date_range))}</p>",
            _bullet_list(tuple(detail.text for detail in item.details)),
            "</article>",
        ),
    )


def _experience_meta(date_range: str, location: str | None) -> str:
    if location is None:
        return date_range
    return f"{date_range} | {location}"


def _education_meta(credential: str, date_range: str | None) -> str:
    if date_range is None:
        return credential
    return f"{credential} | {date_range}"
