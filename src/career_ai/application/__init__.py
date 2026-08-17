"""Shared application services for CLI, Skills, and Streamlit."""

from typing import TYPE_CHECKING

from career_ai.application.career_fit_service import (
    CareerFitApplicationService,
    CareerFitRunResult,
)

if TYPE_CHECKING:
    from career_ai.application.tailoring_service import (
        TailoringApplicationService,
        WorkspaceRunSummary,
    )

__all__ = [
    "CareerFitApplicationService",
    "CareerFitRunResult",
    "TailoringApplicationService",
    "WorkspaceRunSummary",
]


def __getattr__(name: str) -> object:
    """Load tailoring services only when explicitly requested."""
    if name == "TailoringApplicationService":
        from career_ai.application import tailoring_service  # noqa: PLC0415

        return tailoring_service.TailoringApplicationService
    if name == "WorkspaceRunSummary":
        from career_ai.application import tailoring_service  # noqa: PLC0415

        return tailoring_service.WorkspaceRunSummary
    raise AttributeError(name)
