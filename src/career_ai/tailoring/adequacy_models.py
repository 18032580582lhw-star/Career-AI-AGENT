"""Typed results and stable codes for optimization adequacy."""

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Annotated, Self

from pydantic import Field, model_validator
from pydantic_core import PydanticCustomError

from career_ai.tailoring.contract_base import FrozenContractModel, RunId, Sha256
from career_ai.tailoring.models import CandidateFact, EvidenceRequirementMatch, JDRequirement
from career_ai.tailoring.proposal_contracts import ValidationFinding


@unique
class AdequacyViolationCode(StrEnum):
    """Stable machine-readable adequacy failures."""

    DUPLICATE_CANDIDATE_FACT = "duplicate_candidate_fact"
    DUPLICATE_REQUIREMENT = "duplicate_requirement"
    DUPLICATE_MATCH = "duplicate_match"
    UNKNOWN_FACT_REFERENCE = "unknown_fact_reference"
    UNKNOWN_REQUIREMENT_REFERENCE = "unknown_requirement_reference"
    INVALID_BASELINE_REFERENCE = "invalid_baseline_reference"
    INSUFFICIENT_REQUIRED_COVERAGE_GAIN = "insufficient_required_coverage_gain"
    SUBSTANTIVE_REWRITE_REQUIRED = "substantive_rewrite_required"
    KEYWORD_STUFFING = "keyword_stuffing"
    READABILITY_REGRESSION = "readability_regression"


class AdequacyHarnessResult(FrozenContractModel):
    """Adequacy result kept separate from safety and lifecycle state."""

    run_id: RunId
    proposal_hash: Sha256
    passed: bool
    baseline_score: Annotated[int, Field(ge=0, le=100)]
    projected_score: Annotated[int, Field(ge=0, le=100)]
    findings: tuple[ValidationFinding, ...]

    @model_validator(mode="after")
    def validate_passed_consistency(self) -> Self:
        """Prevent contradictory passed findings from bypassing aggregation."""
        if self.passed != (not self.findings):
            error_code = "adequacy_result_inconsistent"
            error_message = "passed must be true exactly when findings are empty"
            raise PydanticCustomError(error_code, error_message)
        return self


@dataclass(frozen=True, slots=True)
class AdequacyContext:
    """Trusted inputs needed to prove optimization rather than target-label it."""

    candidate_facts: tuple[CandidateFact, ...]
    requirements: tuple[JDRequirement, ...]
    evidence_matches: tuple[EvidenceRequirementMatch, ...]
    baseline_covered_requirement_ids: frozenset[str]
    baseline_resume_text: str
