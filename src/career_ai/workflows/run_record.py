from typing import Final
from uuid import uuid4

from pydantic import Field

from career_ai.models import FrozenModel

DEFAULT_EXPECTED_BEHAVIOR: Final[str] = (
    "Produce a factual, privacy-preserving career fit analysis without retaining input text."
)


class RunInputSummary(FrozenModel):
    """Input sizes retained without personal input bodies."""

    resume_character_count: int = Field(ge=0)
    jd_character_count: int = Field(ge=0)

    @classmethod
    def from_inputs(cls, *, resume_text: str, jd_text: str) -> "RunInputSummary":
        """Create a summary without retaining either input body."""
        return cls(
            resume_character_count=len(resume_text),
            jd_character_count=len(jd_text),
        )


class RunQualityCheckRecord(FrozenModel):
    """Neutral outcome for one deterministic quality check."""

    name: str = Field(min_length=1)
    code: str = Field(min_length=1)
    status: str = Field(pattern="^(passed|failed)$")


class CareerFitRunRecord(FrozenModel):
    """Privacy-safe record of one deterministic career-fit workflow run."""

    run_id: str = Field(min_length=1)
    operation: str = Field(min_length=1)
    final_status: str = Field(min_length=1)
    input_summary: RunInputSummary
    step_names: list[str]
    quality_checks: list[RunQualityCheckRecord]
    expected_behavior: str = Field(default=DEFAULT_EXPECTED_BEHAVIOR, min_length=1)


def new_run_id() -> str:
    """Create an opaque audit identifier without embedding user data."""
    return f"run-{uuid4().hex}"
