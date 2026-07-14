"""Inspection and safe patching for user-owned resume.tex templates."""

from __future__ import annotations

import re
from hashlib import sha256
from typing import Final

from career_ai.rendering.latex.errors import LatexTemplatePatchError
from career_ai.rendering.latex.inspection import inspect_latex_structure
from career_ai.rendering.latex.models import (
    LatexSectionMapping,
    LatexTemplateProfile,
)
from career_ai.rendering.latex.renderer import render_latex_section
from career_ai.rendering.latex.safety import find_unsafe_latex_commands
from career_ai.tailoring.document_contracts import AcceptedResumeDocument, ResumeSection

_DOCUMENTCLASS: Final = re.compile(r"\\documentclass(?:\[[^\[\]{}]*\])?\{([^{}]+)\}")
_CUSTOM_COMMAND: Final = re.compile(r"\\(?:newcommand|renewcommand|providecommand)\b[^\n]*")
_PACKAGE: Final = re.compile(r"\\usepackage(?:\[[^\[\]{}]*\])?\{([^{}]+)\}")
_FONT: Final = re.compile(r"\\(?:setmainfont|setCJKmainfont)\{([^{}]+)\}")
_BEGIN_MARKER: Final = re.compile(
    r"%[ \t]*career-ai:begin[ \t]+(?P<section>summary|skills|experience|projects|education)[ \t]*",
)
_END_MARKER_TEMPLATE: Final = r"%[ \t]*career-ai:end[ \t]+{section}[ \t]*"


def inspect_user_latex_template(source: str) -> LatexTemplateProfile:
    """Build a static profile for a user-owned LaTeX template."""
    structure = inspect_latex_structure(source)
    documentclass = _documentclass(source)
    preamble = source[: structure.body_start]
    mappings = _marker_mappings(source)
    return LatexTemplateProfile(
        template_hash=sha256(source.encode("utf-8")).hexdigest(),
        documentclass=documentclass,
        preamble_hash=sha256(preamble.encode("utf-8")).hexdigest(),
        body_start=structure.body_start,
        body_end=structure.body_end,
        custom_commands=tuple(match.group(0) for match in _CUSTOM_COMMAND.finditer(preamble)),
        sections=structure.sections,
        section_mappings=mappings,
        packages=_split_csv_matches(_PACKAGE.findall(preamble)),
        fonts=tuple(match.group(1) for match in _FONT.finditer(preamble)),
        unsafe_findings=find_unsafe_latex_commands(source),
        requires_mapping_confirmation=not mappings,
    )


def patch_user_latex_template(
    *,
    source: str,
    profile: LatexTemplateProfile,
    document: AcceptedResumeDocument,
) -> str:
    """Return a new patched .tex source without modifying the user's source."""
    _assert_patchable(source, profile)
    pieces: list[str] = []
    cursor = 0
    for mapping in sorted(profile.section_mappings, key=lambda item: item.content_start):
        pieces.append(source[cursor : mapping.content_start])
        pieces.append("\n")
        pieces.append(render_latex_section(document, mapping.section))
        pieces.append("\n")
        cursor = mapping.content_end
    pieces.append(source[cursor:])
    patched = "".join(pieces)
    _ = inspect_latex_structure(patched)
    if find_unsafe_latex_commands(patched):
        reason = "patched_template_unsafe"
        raise LatexTemplatePatchError(reason)
    return patched


def _assert_patchable(source: str, profile: LatexTemplateProfile) -> None:
    if sha256(source.encode("utf-8")).hexdigest() != profile.template_hash:
        reason = "template_hash_mismatch"
        raise LatexTemplatePatchError(reason)
    if profile.unsafe_findings:
        reason = "template_contains_unsafe_latex"
        raise LatexTemplatePatchError(reason)
    if profile.requires_mapping_confirmation or not profile.section_mappings:
        reason = "template_mapping_requires_confirmation"
        raise LatexTemplatePatchError(reason)
    if any(not mapping.confirmed for mapping in profile.section_mappings):
        reason = "template_mapping_requires_confirmation"
        raise LatexTemplatePatchError(reason)


def _documentclass(source: str) -> str:
    matched = _DOCUMENTCLASS.search(source)
    if matched is None:
        return ""
    return matched.group(1).strip()


def _marker_mappings(source: str) -> tuple[LatexSectionMapping, ...]:
    mappings: list[LatexSectionMapping] = []
    for begin in _BEGIN_MARKER.finditer(source):
        section_name = begin.group("section")
        end_pattern = re.compile(_END_MARKER_TEMPLATE.format(section=section_name))
        end = end_pattern.search(source, begin.end())
        if end is None:
            continue
        mappings.append(
            LatexSectionMapping(
                section=ResumeSection(section_name),
                begin_marker=begin.start(),
                end_marker=end.end(),
                content_start=begin.end(),
                content_end=end.start(),
                confirmed=True,
            ),
        )
    return tuple(mappings)


def _split_csv_matches(values: list[str]) -> tuple[str, ...]:
    packages: list[str] = []
    for value in values:
        packages.extend(part.strip() for part in value.split(",") if part.strip())
    return tuple(packages)
