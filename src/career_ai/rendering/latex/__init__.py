"""Safe LaTeX rendering, inspection, and compilation primitives."""

from career_ai.rendering.latex.compiler import compile_latex_pdf
from career_ai.rendering.latex.errors import LatexStructureError, LatexTemplatePatchError
from career_ai.rendering.latex.escaping import escape_latex
from career_ai.rendering.latex.inspection import inspect_latex_structure
from career_ai.rendering.latex.models import (
    LatexCompilationFailure,
    LatexCompilationResult,
    LatexCompilationSuccess,
    LatexCompileErrorCode,
    LatexCompilerConfig,
    LatexContext,
    LatexFinding,
    LatexFindingCode,
    LatexSection,
    LatexSectionMapping,
    LatexStructure,
    LatexStructureErrorCode,
    LatexTemplateProfile,
)
from career_ai.rendering.latex.renderer import (
    LatexSourceResumeRenderer,
    render_latex_body,
    render_latex_section,
    render_system_latex,
)
from career_ai.rendering.latex.safety import find_unsafe_latex_commands
from career_ai.rendering.latex.templates import load_system_template
from career_ai.rendering.latex.user_template import (
    inspect_user_latex_template,
    patch_user_latex_template,
)

__all__ = [
    "LatexCompilationFailure",
    "LatexCompilationResult",
    "LatexCompilationSuccess",
    "LatexCompileErrorCode",
    "LatexCompilerConfig",
    "LatexContext",
    "LatexFinding",
    "LatexFindingCode",
    "LatexSection",
    "LatexSectionMapping",
    "LatexSourceResumeRenderer",
    "LatexStructure",
    "LatexStructureError",
    "LatexStructureErrorCode",
    "LatexTemplatePatchError",
    "LatexTemplateProfile",
    "compile_latex_pdf",
    "escape_latex",
    "find_unsafe_latex_commands",
    "inspect_latex_structure",
    "inspect_user_latex_template",
    "load_system_template",
    "patch_user_latex_template",
    "render_latex_body",
    "render_latex_section",
    "render_system_latex",
]
