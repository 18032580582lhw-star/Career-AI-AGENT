"""Typed errors raised by LaTeX rendering and template handling."""

from dataclasses import dataclass
from typing import override

from career_ai.rendering.latex.models import LatexStructureErrorCode


@dataclass(frozen=True, slots=True)
class LatexStructureError(Exception):
    """A malformed or ambiguous document boundary."""

    code: LatexStructureErrorCode

    @override
    def __str__(self) -> str:
        """Return the stable machine-readable error code."""
        return self.code.value


@dataclass(frozen=True, slots=True)
class LatexTemplatePatchError(Exception):
    """A user-owned template cannot be safely patched."""

    reason: str

    @override
    def __str__(self) -> str:
        """Return a stable, non-sensitive patch failure reason."""
        return self.reason
