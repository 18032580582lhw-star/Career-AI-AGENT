"""Validation lifecycle decisions and bounded repair policy."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Annotated, Self

from pydantic import Field, JsonValue, field_serializer, model_validator
from pydantic_core import PydanticCustomError

from career_ai.tailoring.contract_base import (
    FrozenContractModel,
    NonEmptyText,
    RunId,
    Sha256,
    canonical_json_hash,
)
from career_ai.tailoring.manifest_contracts import RunState
from career_ai.tailoring.proposal_contracts import (
    ResumeTailoringProposal,
    ValidationDecision,
    ValidationFinding,
    ValidationOutcome,
    ValidationSeverity,
)

if TYPE_CHECKING:
    from career_ai.tailoring.adequacy_models import AdequacyHarnessResult
    from career_ai.tailoring.safety_models import SafetyHarnessResult

_MAX_REPAIR_ATTEMPTS = 2


class ValidationContext(FrozenContractModel):
    """Current immutable sources and bounded repair position."""

    current_source_hashes: dict[NonEmptyText, Sha256]
    current_template_hash: Sha256 | None = None
    run_id: RunId | None = None
    repair_attempts: Annotated[int, Field(ge=0, le=2)] = 0

    @field_serializer("current_source_hashes")
    def serialize_source_hashes(self, value: dict[str, str]) -> dict[str, str]:
        """Serialize the runtime-immutable current mapping as JSON."""
        return dict(value)

    @model_validator(mode="after")
    def validate_required_roles(self) -> Self:
        """Require current resume and JD identities before validation."""
        if not {"resume", "jd"} <= set(self.current_source_hashes):
            error_code = "missing_current_source_role"
            error_message = "current source hashes require resume and jd roles"
            raise PydanticCustomError(error_code, error_message)
        object.__setattr__(
            self,
            "current_source_hashes",
            MappingProxyType(dict(self.current_source_hashes)),
        )
        return self


class ValidationStateResult(FrozenContractModel):
    """One authoritative lifecycle decision and repair allowance."""

    state: RunState
    decision: ValidationDecision
    repair_attempts: Annotated[int, Field(ge=0, le=2)]
    repair_allowed: bool
    render_allowed: bool


def decide_validation_state(
    proposal: ResumeTailoringProposal,
    safety: SafetyHarnessResult,
    adequacy: AdequacyHarnessResult,
    context: ValidationContext,
) -> ValidationStateResult:
    """Apply stale, safety, confirmation, adequacy, and repair rules in order."""
    _require_bound_results(proposal, safety, adequacy)
    findings = tuple(sorted((*safety.findings, *adequacy.findings), key=lambda item: item.id))
    _require_unique_finding_ids(findings)
    stale = (
        (context.run_id is not None and context.run_id != proposal.run_id)
        or context.current_source_hashes != proposal.source_hashes
        or context.current_template_hash != proposal.template_hash
    )
    has_safety_error = any(
        item.severity is ValidationSeverity.ERROR for item in safety.findings
    )
    has_safety_warning = any(
        item.severity is ValidationSeverity.WARNING for item in safety.findings
    )
    if stale:
        state = RunState.STALE
        outcome = ValidationOutcome.STALE
    elif has_safety_error or not adequacy.passed:
        state = RunState.REJECTED
        outcome = ValidationOutcome.REJECTED
    elif has_safety_warning:
        state = RunState.NEEDS_CONFIRMATION
        outcome = ValidationOutcome.NEEDS_CONFIRMATION
    else:
        state = RunState.ACCEPTED
        outcome = ValidationOutcome.ACCEPTED
    validation_hash = calculate_validation_hash(
        proposal,
        outcome,
        findings,
        safety_passed=safety.passed,
        adequacy_passed=adequacy.passed,
    )
    decision = ValidationDecision(
        run_id=proposal.run_id,
        proposal_hash=proposal.proposal_hash,
        outcome=outcome,
        findings=findings,
        safety_passed=safety.passed,
        adequacy_passed=adequacy.passed,
        validation_hash=validation_hash,
    )
    repair_allowed = (
        state is RunState.REJECTED and context.repair_attempts < _MAX_REPAIR_ATTEMPTS
    )
    return ValidationStateResult(
        state=state,
        decision=decision,
        repair_attempts=context.repair_attempts,
        repair_allowed=repair_allowed,
        render_allowed=state is RunState.ACCEPTED,
    )


def advance_repair(
    result: ValidationStateResult,
    context: ValidationContext,
) -> ValidationContext:
    """Consume exactly one persisted repair allowance."""
    if not result.repair_allowed or result.repair_attempts != context.repair_attempts:
        error_code = "repair_not_allowed"
        error_message = "repair transition is not allowed from this validation state"
        raise PydanticCustomError(error_code, error_message)
    return ValidationContext(
        current_source_hashes=dict(context.current_source_hashes),
        current_template_hash=context.current_template_hash,
        run_id=context.run_id,
        repair_attempts=context.repair_attempts + 1,
    )


def _require_bound_results(
    proposal: ResumeTailoringProposal,
    safety: SafetyHarnessResult,
    adequacy: AdequacyHarnessResult,
) -> None:
    expected = (proposal.run_id, proposal.proposal_hash)
    if (safety.run_id, safety.proposal_hash) != expected or (
        adequacy.run_id,
        adequacy.proposal_hash,
    ) != expected:
        error_code = "harness_result_proposal_mismatch"
        error_message = "safety and adequacy results must bind to the current proposal"
        raise PydanticCustomError(error_code, error_message)


def _require_unique_finding_ids(findings: tuple[ValidationFinding, ...]) -> None:
    finding_ids = tuple(item.id for item in findings)
    if len(finding_ids) != len(set(finding_ids)):
        error_code = "duplicate_aggregate_finding"
        error_message = "safety and adequacy finding ids must be globally unique"
        raise PydanticCustomError(error_code, error_message)


def calculate_validation_hash(
    proposal: ResumeTailoringProposal,
    outcome: ValidationOutcome,
    findings: tuple[ValidationFinding, ...],
    *,
    safety_passed: bool,
    adequacy_passed: bool,
) -> str:
    """Recompute the tamper-evident hash for a validation decision."""
    finding_json = "\x1e".join(item.model_dump_json() for item in findings)
    payload: dict[str, JsonValue] = {
        "run_id": proposal.run_id,
        "proposal_hash": proposal.proposal_hash,
        "outcome": outcome.value,
        "safety_passed": safety_passed,
        "adequacy_passed": adequacy_passed,
        "findings_json": finding_json,
    }
    return canonical_json_hash(payload)
