from pydantic import Field

from career_ai.models import FrozenModel


class EvalCaseInput(FrozenModel):
    """Resume and job-description text used by one deterministic eval case."""

    resume_text: str = Field(min_length=1)
    jd_text: str = Field(min_length=1)


class ExpectedCareerSignals(FrozenModel):
    """Expected observable signals for deterministic career eval checks."""

    role_title: str = Field(min_length=1)
    required_missing_keywords: list[str] = Field(default_factory=list)
    forbidden_new_claims: list[str] = Field(default_factory=list)
    prompt_strategy_count_min: int = Field(ge=1)


class CareerEvalCase(FrozenModel):
    """A golden career workflow case with inputs and expected quality signals."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    input: EvalCaseInput
    expected: ExpectedCareerSignals
