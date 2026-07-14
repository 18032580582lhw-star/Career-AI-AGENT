from __future__ import annotations

import pytest
from pydantic import ValidationError
from pydantic_core import PydanticCustomError

from career_ai.tailoring.adequacy_models import AdequacyHarnessResult
from career_ai.tailoring.manifest_contracts import RunState
from career_ai.tailoring.proposal_contracts import (
    ResumeTailoringProposal,
    ValidationFinding,
    ValidationOutcome,
    ValidationSeverity,
    calculate_proposal_hash,
)
from career_ai.tailoring.safety_models import SafetyHarnessResult
from career_ai.tailoring.state_machine import (
    ValidationContext,
    ValidationStateResult,
    advance_repair,
    decide_validation_state,
)
from tests.adequacy_helpers import proposal


def _finding(*, warning: bool = False) -> ValidationFinding:
    return ValidationFinding(
        id="finding-confirm" if warning else "finding-error",
        code="inference_requires_confirmation" if warning else "unsupported_metric",
        severity=ValidationSeverity.WARNING if warning else ValidationSeverity.ERROR,
        message="Confirm inference" if warning else "Unsupported metric",
        confirmation_prompt="Confirm explicitly" if warning else None,
    )


def _safety(*findings: ValidationFinding) -> SafetyHarnessResult:
    candidate = proposal()
    return SafetyHarnessResult(
        run_id=candidate.run_id,
        proposal_hash=candidate.proposal_hash,
        passed=not findings,
        findings=findings,
    )


def _adequacy(*findings: ValidationFinding) -> AdequacyHarnessResult:
    candidate = proposal()
    return AdequacyHarnessResult(
        run_id=candidate.run_id,
        proposal_hash=candidate.proposal_hash,
        passed=not findings,
        baseline_score=50,
        projected_score=60,
        findings=findings,
    )


def _decide(
    safety: SafetyHarnessResult,
    adequacy: AdequacyHarnessResult,
    *,
    repair_attempts: int = 0,
    current_hashes: dict[str, str] | None = None,
) -> tuple[RunState, ValidationOutcome, bool, str]:
    result = _state_result(
        safety,
        adequacy,
        repair_attempts=repair_attempts,
        current_hashes=current_hashes,
    )
    return (
        result.state,
        result.decision.outcome,
        result.repair_allowed,
        result.decision.validation_hash,
    )


def _state_result(
    safety: SafetyHarnessResult,
    adequacy: AdequacyHarnessResult,
    *,
    repair_attempts: int = 0,
    current_hashes: dict[str, str] | None = None,
) -> ValidationStateResult:
    candidate = proposal()
    context = ValidationContext(
        current_source_hashes=(
            candidate.source_hashes if current_hashes is None else current_hashes
        ),
        repair_attempts=repair_attempts,
    )
    return decide_validation_state(candidate, safety, adequacy, context)


finding = _finding
safety_result = _safety
adequacy_result = _adequacy
decide = _decide


def test_dual_pass_current_sources_is_accepted() -> None:
    state, outcome, repair_allowed, _ = _decide(_safety(), _adequacy())

    assert (state, outcome, repair_allowed) == (
        RunState.ACCEPTED,
        ValidationOutcome.ACCEPTED,
        False,
    )


def test_source_hash_change_has_stale_precedence() -> None:
    state, outcome, repair_allowed, _ = _decide(
        _safety(_finding()),
        _adequacy(),
        current_hashes={"resume": "c" * 64, "jd": "b" * 64},
    )

    assert (state, outcome, repair_allowed) == (
        RunState.STALE,
        ValidationOutcome.STALE,
        False,
    )


def test_warning_only_safety_pauses_for_confirmation() -> None:
    state, outcome, repair_allowed, _ = _decide(_safety(_finding(warning=True)), _adequacy())

    assert (state, outcome, repair_allowed) == (
        RunState.NEEDS_CONFIRMATION,
        ValidationOutcome.NEEDS_CONFIRMATION,
        False,
    )


def test_safety_or_adequacy_error_is_rejected() -> None:
    safety_result = _decide(_safety(_finding()), _adequacy())
    adequacy_result = _decide(_safety(), _adequacy(_finding()))

    assert safety_result[:3] == (RunState.REJECTED, ValidationOutcome.REJECTED, True)
    assert adequacy_result[:3] == (RunState.REJECTED, ValidationOutcome.REJECTED, True)


def test_repair_cap_allows_two_attempts_only() -> None:
    first = _decide(_safety(_finding()), _adequacy(), repair_attempts=0)
    second = _decide(_safety(_finding()), _adequacy(), repair_attempts=1)
    exhausted = _decide(_safety(_finding()), _adequacy(), repair_attempts=2)

    assert (first[2], second[2], exhausted[2]) == (True, True, False)


@pytest.mark.parametrize("attempts", [-1, 3])
def test_invalid_repair_attempts_are_rejected(attempts: int) -> None:
    with pytest.raises(ValidationError, match="repair_attempts"):
        _ = _decide(_safety(), _adequacy(), repair_attempts=attempts)


def test_validation_hash_is_deterministic() -> None:
    first = _decide(_safety(), _adequacy())[3]
    second = _decide(_safety(), _adequacy())[3]

    assert first == second


def test_contradictory_harness_results_are_rejected() -> None:
    candidate = proposal()
    with pytest.raises(ValidationError, match="passed"):
        _ = SafetyHarnessResult(
            run_id=candidate.run_id,
            proposal_hash=candidate.proposal_hash,
            passed=True,
            findings=(_finding(),),
        )
    with pytest.raises(ValidationError, match="passed"):
        _ = AdequacyHarnessResult(
            run_id=candidate.run_id,
            proposal_hash=candidate.proposal_hash,
            passed=True,
            baseline_score=50,
            projected_score=60,
            findings=(_finding(),),
        )


def test_duplicate_aggregate_finding_ids_are_rejected() -> None:
    duplicate = _finding()
    with pytest.raises(PydanticCustomError, match="globally unique"):
        _ = _state_result(_safety(duplicate), _adequacy(duplicate))


def test_missing_current_source_role_is_rejected() -> None:
    with pytest.raises(ValidationError, match="resume and jd"):
        _ = ValidationContext(
            current_source_hashes={"resume": "a" * 64},
            repair_attempts=0,
        )


def test_stale_precedes_warning_and_adequacy_failure() -> None:
    result = _decide(
        _safety(_finding(warning=True)),
        _adequacy(_finding()),
        current_hashes={"resume": "c" * 64, "jd": "b" * 64},
    )

    assert result[:3] == (RunState.STALE, ValidationOutcome.STALE, False)


def test_finding_order_does_not_change_validation_hash() -> None:
    first_finding = _finding(warning=True)
    second_finding = ValidationFinding(
        id="finding-second",
        code="second_confirmation",
        severity=ValidationSeverity.WARNING,
        message="Confirm second inference",
        confirmation_prompt="Confirm second explicitly",
    )
    first = _decide(_safety(first_finding, second_finding), _adequacy())[3]
    second = _decide(_safety(second_finding, first_finding), _adequacy())[3]

    assert first == second


def test_only_accepted_state_allows_rendering() -> None:
    accepted = _state_result(_safety(), _adequacy())
    confirmation = _state_result(_safety(_finding(warning=True)), _adequacy())
    rejected = _state_result(_safety(_finding()), _adequacy())

    assert (accepted.render_allowed, confirmation.render_allowed, rejected.render_allowed) == (
        True,
        False,
        False,
    )


def test_harness_results_cannot_be_substituted_across_proposals() -> None:
    candidate = proposal()
    forged = SafetyHarnessResult(
        run_id=candidate.run_id,
        proposal_hash="c" * 64,
        passed=True,
        findings=(),
    )
    with pytest.raises(PydanticCustomError, match="current proposal"):
        _ = _state_result(forged, _adequacy())


def test_source_hash_mappings_are_runtime_immutable() -> None:
    candidate = proposal()
    context = ValidationContext(
        current_source_hashes=candidate.source_hashes,
        repair_attempts=0,
    )

    with pytest.raises(TypeError):
        candidate.source_hashes["resume"] = "c" * 64
    with pytest.raises(TypeError):
        context.current_source_hashes["resume"] = "c" * 64


def test_template_hash_change_marks_proposal_stale() -> None:
    base = proposal()
    payload = base.model_dump(mode="json")
    payload["template_hash"] = "d" * 64
    payload["proposal_hash"] = calculate_proposal_hash(payload)
    candidate = ResumeTailoringProposal.model_validate(payload)
    safety = SafetyHarnessResult(
        run_id=candidate.run_id,
        proposal_hash=candidate.proposal_hash,
        passed=True,
        findings=(),
    )
    adequacy = AdequacyHarnessResult(
        run_id=candidate.run_id,
        proposal_hash=candidate.proposal_hash,
        passed=True,
        baseline_score=90,
        projected_score=90,
        findings=(),
    )
    context = ValidationContext(
        current_source_hashes=candidate.source_hashes,
        current_template_hash="e" * 64,
        repair_attempts=0,
    )

    result = decide_validation_state(candidate, safety, adequacy, context)
    assert (result.state, result.render_allowed) == (RunState.STALE, False)


def test_repair_transition_consumes_attempts_and_cannot_reset_itself() -> None:
    candidate = proposal()
    context = ValidationContext(current_source_hashes=candidate.source_hashes)
    first = decide_validation_state(candidate, _safety(_finding()), _adequacy(), context)
    second_context = advance_repair(first, context)
    second = decide_validation_state(
        candidate, _safety(_finding()), _adequacy(), second_context
    )
    exhausted_context = advance_repair(second, second_context)
    exhausted = decide_validation_state(
        candidate, _safety(_finding()), _adequacy(), exhausted_context
    )

    assert (second_context.repair_attempts, exhausted_context.repair_attempts) == (1, 2)
    assert exhausted.repair_allowed is False
    with pytest.raises(PydanticCustomError, match="not allowed"):
        _ = advance_repair(exhausted, exhausted_context)
