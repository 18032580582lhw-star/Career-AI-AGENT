"""Structural LaTeX inspection without expansion, file access, or execution."""

import re
from typing import Final

from career_ai.rendering.latex.errors import LatexStructureError
from career_ai.rendering.latex.models import (
    LatexSection,
    LatexStructure,
    LatexStructureErrorCode,
)
from career_ai.rendering.latex.syntax import mask_latex_comments

_BEGIN_DOCUMENT: Final = re.compile(r"\\begin\s*\{\s*document\s*\}")
_END_DOCUMENT: Final = re.compile(r"\\end\s*\{\s*document\s*\}")
_SECTION: Final = re.compile(r"\\section(?P<star>\*)?\s*\{(?P<title>[^{}]*)\}")


def inspect_latex_structure(source: str) -> LatexStructure:
    """Inspect document boundaries and literal section markers in memory."""
    masked = mask_latex_comments(source)
    begins = list(_BEGIN_DOCUMENT.finditer(masked))
    ends = list(_END_DOCUMENT.finditer(masked))
    if not begins:
        raise LatexStructureError(LatexStructureErrorCode.MISSING_BEGIN_DOCUMENT)
    if not ends:
        raise LatexStructureError(LatexStructureErrorCode.MISSING_END_DOCUMENT)
    if ends[0].start() < begins[0].start():
        raise LatexStructureError(LatexStructureErrorCode.REVERSED_DOCUMENT_BOUNDARY)
    if len(begins) > 1:
        raise LatexStructureError(LatexStructureErrorCode.DUPLICATE_BEGIN_DOCUMENT)
    if len(ends) > 1:
        raise LatexStructureError(LatexStructureErrorCode.DUPLICATE_END_DOCUMENT)

    body_start = begins[0].end()
    body_end = ends[0].start()
    body_mask = masked[body_start:body_end]
    sections = tuple(
        LatexSection(
            title=match.group("title").strip(),
            starred=match.group("star") is not None,
            source_offset=body_start + match.start(),
        )
        for match in _SECTION.finditer(body_mask)
    )
    return LatexStructure(
        body=source[body_start:body_end],
        body_start=body_start,
        body_end=body_end,
        sections=sections,
    )
