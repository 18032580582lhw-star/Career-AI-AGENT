"""Typed results and stable codes for the factual safety harness."""

from enum import StrEnum, unique
from typing import Self

from pydantic import model_validator
from pydantic_core import PydanticCustomError

from career_ai.tailoring.contract_base import FrozenContractModel, RunId, Sha256
from career_ai.tailoring.proposal_contracts import ValidationFinding


@unique
class SafetyViolationCode(StrEnum):
    """Stable machine-readable factual safety failures."""

    UNKNOWN_SOURCE_FACT = "unknown_source_fact"
    UNSUPPORTED_TECHNOLOGY = "unsupported_technology"
    UNSUPPORTED_RESPONSIBILITY = "unsupported_responsibility"
    UNSUPPORTED_SENIORITY = "unsupported_seniority"
    UNSUPPORTED_METRIC = "unsupported_metric"
    INFERENCE_REQUIRES_CONFIRMATION = "inference_requires_confirmation"
    CONFIRMATION_PROVENANCE_MISSING = "confirmation_provenance_missing"
    CONFIRMATION_STATEMENT_MISMATCH = "confirmation_statement_mismatch"
    DUPLICATE_SOURCE_FACT = "duplicate_source_fact"
    SUPPORTED_PROVENANCE_MISMATCH = "supported_provenance_mismatch"
    CHANGE_CLAIM_FACT_MISMATCH = "change_claim_fact_mismatch"
    PROMPT_INJECTION_CONTENT = "prompt_injection_content"
    UNSUPPORTED_CLAIM = "unsupported_claim"


class SafetyHarnessResult(FrozenContractModel):
    """Factual safety result kept separate from adequacy and run state."""

    run_id: RunId
    proposal_hash: Sha256
    passed: bool
    findings: tuple[ValidationFinding, ...]

    @model_validator(mode="after")
    def validate_passed_consistency(self) -> Self:
        """Prevent contradictory passed findings from bypassing aggregation."""
        if self.passed != (not self.findings):
            error_code = "safety_result_inconsistent"
            error_message = "passed must be true exactly when findings are empty"
            raise PydanticCustomError(error_code, error_message)
        return self
