"""System LaTeX rendering for accepted resume documents."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, assert_never, final

from career_ai.rendering.artifacts import output_artifact
from career_ai.rendering.latex.escaping import escape_latex
from career_ai.rendering.latex.inspection import inspect_latex_structure
from career_ai.rendering.latex.models import LatexContext
from career_ai.rendering.latex.safety import find_unsafe_latex_commands
from career_ai.rendering.latex.templates import load_system_template
from career_ai.rendering.models import RendererOutcome, RendererSuccess
from career_ai.tailoring.document_contracts import ResumeSection
from career_ai.tailoring.manifest_contracts import RenderBackend

if TYPE_CHECKING:
    from pathlib import Path

    from career_ai.tailoring.document_contracts import (
        AcceptedResumeDocument,
        EducationEntry,
        ProjectEntry,
    )

_TEX_NAME: Final = "resume.tex"
_MEDIA_TYPE: Final = "application/x-tex"
_PLACEHOLDER: Final = "@@RESUME_BODY@@"


@final
class LatexSourceResumeRenderer:
    """Render accepted resume documents to safe system-template LaTeX source."""

    @property
    def backend(self) -> RenderBackend:
        """Return the registry backend implemented by this adapter."""
        return RenderBackend.LATEX_SOURCE

    def render(
        self,
        document: AcceptedResumeDocument,
        output_directory: Path,
    ) -> RendererOutcome:
        """Write one standalone .tex artifact without invoking a compiler."""
        output_directory.mkdir(parents=True, exist_ok=True)
        output_path = output_directory / _TEX_NAME
        tex = render_system_latex(document)
        _ = output_path.write_text(tex, encoding="utf-8")
        return RendererSuccess(
            backend=self.backend,
            artifacts=(
                output_artifact(
                    output_path,
                    relative_path=_TEX_NAME,
                    media_type=_MEDIA_TYPE,
                ),
            ),
        )


def render_system_latex(document: AcceptedResumeDocument) -> str:
    """Render a complete system-template LaTeX document from accepted content."""
    template = load_system_template()
    body = render_latex_body(document)
    rendered = template.replace(_PLACEHOLDER, body)
    if _PLACEHOLDER in rendered:
        return _render_failure_document("unresolved placeholder")
    structure = inspect_latex_structure(rendered)
    section_titles = tuple(section.title for section in structure.sections)
    required = ("Professional Summary", "Skills", "Experience", "Education")
    if not set(required) <= set(section_titles):
        return _render_failure_document("missing required section")
    if find_unsafe_latex_commands(rendered):
        return _render_failure_document("unsafe latex source")
    return rendered


def render_latex_body(document: AcceptedResumeDocument) -> str:
    """Render only the document body used by system and user-template paths."""
    lines = [
        _identity_block(document),
        *(_section_block(document, section) for section in document.section_order),
    ]
    return "\n\n".join(line for line in lines if line)


def render_latex_section(
    document: AcceptedResumeDocument,
    section: ResumeSection,
) -> str:
    """Render one controlled section body for user-template patching."""
    return _section_block(document, section)


def _identity_block(document: AcceptedResumeDocument) -> str:
    identity = document.identity
    lines = [
        r"\begin{center}",
        rf"{{\Large \textbf{{{escape_latex(identity.name)}}}}}\\",
    ]
    if identity.headline is not None:
        lines.append(escape_latex(identity.headline))
    if identity.contact_lines:
        contacts = " $\\cdot$ ".join(
            escape_latex(contact, context=LatexContext.CUSTOM_MACRO_ARGUMENT)
            for contact in identity.contact_lines
        )
        lines.append(contacts)
    lines.append(r"\end{center}")
    return "\n".join(lines)


def _section_block(document: AcceptedResumeDocument, section: ResumeSection) -> str:
    match section:
        case ResumeSection.SUMMARY:
            return _bullet_section(
                "Professional Summary",
                tuple(bullet.text for bullet in document.professional_summary),
            )
        case ResumeSection.SKILLS:
            return _bullet_section(
                "Skills",
                tuple(skill.text for skill in document.skills),
            )
        case ResumeSection.EXPERIENCE:
            return _experience_section(document)
        case ResumeSection.PROJECTS:
            return _project_section(document)
        case ResumeSection.EDUCATION:
            return _education_section(document)
        case ResumeSection.LINKS:
            return _bullet_section(
                "Links",
                tuple(f"{link.label}: {link.url}" for link in document.links),
            )
        case _:
            assert_never(section)


def _bullet_section(title: str, items: tuple[str, ...]) -> str:
    if not items:
        return ""
    lines = [_section_title(title), r"\begin{itemize}"]
    lines.extend(rf"\item {escape_latex(item, context=LatexContext.BULLET)}" for item in items)
    lines.append(r"\end{itemize}")
    return "\n".join(lines)


def _experience_section(document: AcceptedResumeDocument) -> str:
    lines = [_section_title("Experience")]
    for entry in document.experience:
        lines.extend(_role_lines(entry.title, entry.organization, entry.date_range))
        lines.extend(_bullet_list(tuple(bullet.text for bullet in entry.bullets)))
    return "\n".join(lines)


def _project_section(document: AcceptedResumeDocument) -> str:
    if not document.projects:
        return ""
    lines = [_section_title("Projects")]
    for entry in document.projects:
        lines.extend(_project_lines(entry))
    return "\n".join(lines)


def _education_section(document: AcceptedResumeDocument) -> str:
    lines = [_section_title("Education")]
    for entry in document.education:
        lines.extend(_education_lines(entry))
    return "\n".join(lines)


def _section_title(title: str) -> str:
    return rf"\section{{{escape_latex(title, context=LatexContext.SECTION_TITLE)}}}"


def _role_lines(title: str, organization: str, date_range: str) -> list[str]:
    role = rf"\textbf{{{escape_latex(title)}}}, {escape_latex(organization)}"
    date = rf"\hfill {escape_latex(date_range, context=LatexContext.DATE)}"
    return [
        f"{role}{date}",
    ]


def _project_lines(entry: ProjectEntry) -> list[str]:
    subtitle = "" if entry.subtitle is None else f" -- {escape_latex(entry.subtitle)}"
    return [
        rf"\textbf{{{escape_latex(entry.name)}}}{subtitle}",
        *_bullet_list(tuple(bullet.text for bullet in entry.bullets)),
    ]


def _education_lines(entry: EducationEntry) -> list[str]:
    date = "" if entry.date_range is None else rf"\hfill {escape_latex(entry.date_range)}"
    education = (
        rf"\textbf{{{escape_latex(entry.institution)}}}: "
        rf"{escape_latex(entry.credential)}{date}"
    )
    return [
        education,
        *_bullet_list(tuple(detail.text for detail in entry.details)),
    ]


def _bullet_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return []
    return [
        r"\begin{itemize}",
        *(rf"\item {escape_latex(item, context=LatexContext.BULLET)}" for item in items),
        r"\end{itemize}",
    ]


def _render_failure_document(reason: str) -> str:
    return rf"\begin{{document}}\section{{Renderer Failure}}{escape_latex(reason)}\end{{document}}"
