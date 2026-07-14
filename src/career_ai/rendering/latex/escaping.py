"""Context-aware escaping for untrusted LaTeX content."""

import re
from typing import Final, assert_never

from career_ai.rendering.latex.models import LatexContext

_SPECIAL_CHARACTER: Final = re.compile(r"[\\{}#$%&_~^]")
_ESCAPES: Final[dict[str, str]] = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "#": r"\#",
    "$": r"\$",
    "%": r"\%",
    "&": r"\&",
    "_": r"\_",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape_latex(value: str, *, context: LatexContext = LatexContext.TEXT) -> str:
    """Render untrusted Unicode as inert LaTeX content in the selected context."""
    contextual_value = _contextual_value(value, context)
    return _SPECIAL_CHARACTER.sub(
        lambda matched: _ESCAPES[matched.group()],
        contextual_value,
    )


def _contextual_value(value: str, context: LatexContext) -> str:
    match context:
        case LatexContext.TEXT | LatexContext.BULLET:
            return value
        case (
            LatexContext.URL
            | LatexContext.EMAIL
            | LatexContext.SECTION_TITLE
            | LatexContext.DATE
            | LatexContext.COMMAND_ARGUMENT
            | LatexContext.CUSTOM_MACRO_ARGUMENT
        ):
            return " ".join(value.splitlines())
        case _:
            assert_never(context)
