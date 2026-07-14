"""Deterministic factual safety checks for resume tailoring proposals."""

from __future__ import annotations

from hashlib import sha256
from typing import assert_never

from career_ai.tailoring.models import (
    CandidateFact,
    EvidenceProvenance,
    MatchStatus,
    UserConfirmationProvenance,
)
from career_ai.tailoring.proposal_contracts import (
    ProposedClaim,
    ResumeTailoringProposal,
    ValidationFinding,
    ValidationSeverity,
)
from career_ai.tailoring.safety_models import SafetyHarnessResult, SafetyViolationCode
from career_ai.tailoring.safety_rules import (
    has_prompt_injection_content,
    statement_is_supported,
    text_is_covered,
    unsupported_text_codes,
)


def evaluate_factual_safety(
    proposal: ResumeTailoringProposal,
    candidate_facts: tuple[CandidateFact, ...],
) -> SafetyHarnessResult:
    """Reject unsupported claims while pausing confirmation-worthy inferences."""
    fact_ids = tuple(str(fact.id) for fact in candidate_facts)
    if len(fact_ids) != len(set(fact_ids)):
        finding = _finding(SafetyViolationCode.DUPLICATE_SOURCE_FACT, reference=None)
        return SafetyHarnessResult(
            run_id=proposal.run_id,
            proposal_hash=proposal.proposal_hash,
            passed=False,
            findings=(finding,),
        )
    facts_by_id = {str(fact.id): fact for fact in candidate_facts}
    findings: list[ValidationFinding] = []
    seen: set[SafetyViolationCode] = set()
    for claim in proposal.proposed_claims:
        _evaluate_claim(claim, facts_by_id, findings, seen)
    claims_by_id = {claim.id: claim for claim in proposal.proposed_claims}
    for change in proposal.changes:
        if change.proposed_claim_ids:
            change_fact_ids = set(change.source_fact_ids)
            mismatched = any(
                set(claims_by_id[claim_id].source_fact_ids) != change_fact_ids
                for claim_id in change.proposed_claim_ids
            )
            if mismatched:
                _append_finding(
                    findings,
                    seen,
                    SafetyViolationCode.CHANGE_CLAIM_FACT_MISMATCH,
                    claim_id=change.id,
                )
            referenced = tuple(
                facts_by_id[fact_id]
                for fact_id in change.source_fact_ids
                if fact_id in facts_by_id
            )
            if len(referenced) == len(change.source_fact_ids):
                claim_texts = {
                    claims_by_id[claim_id].statement for claim_id in change.proposed_claim_ids
                }
                if change.after not in claim_texts:
                    _append_text_findings(
                        findings, seen, change.after, referenced, change.id
                    )
            continue
        referenced = tuple(
            facts_by_id[fact_id]
            for fact_id in change.source_fact_ids
            if fact_id in facts_by_id
        )
        if len(referenced) != len(change.source_fact_ids):
            _append_finding(
                findings,
                seen,
                SafetyViolationCode.UNKNOWN_SOURCE_FACT,
                claim_id=None,
            )
            continue
        _append_text_findings(findings, seen, change.after, referenced, None)
    _append_rewritten_resume_findings(proposal, candidate_facts, findings, seen)
    return SafetyHarnessResult(
        run_id=proposal.run_id,
        proposal_hash=proposal.proposal_hash,
        passed=not findings,
        findings=tuple(findings),
    )


def _evaluate_claim(
    claim: ProposedClaim,
    facts_by_id: dict[str, CandidateFact],
    findings: list[ValidationFinding],
    seen: set[SafetyViolationCode],
) -> None:
    referenced = tuple(
        facts_by_id[fact_id] for fact_id in claim.source_fact_ids if fact_id in facts_by_id
    )
    if len(referenced) != len(claim.source_fact_ids):
        _append_finding(
            findings, seen, SafetyViolationCode.UNKNOWN_SOURCE_FACT, claim_id=claim.id
        )
        return
    match claim.status:
        case MatchStatus.SUPPORTED:
            if not all(_is_evidence_backed(fact) for fact in referenced):
                _append_finding(
                    findings,
                    seen,
                    SafetyViolationCode.SUPPORTED_PROVENANCE_MISMATCH,
                    claim_id=claim.id,
                )
            elif len(referenced) > 1 and claim.statement != "\n".join(
                fact.statement for fact in referenced
            ):
                _append_finding(
                    findings,
                    seen,
                    SafetyViolationCode.UNSUPPORTED_CLAIM,
                    claim_id=claim.id,
                )
            else:
                _append_text_findings(findings, seen, claim.statement, referenced, claim.id)
        case MatchStatus.CONFIRMED:
            confirmed = tuple(fact for fact in referenced if _is_user_confirmed(fact))
            code = (
                SafetyViolationCode.CONFIRMATION_STATEMENT_MISMATCH
                if confirmed and not statement_is_supported(claim.statement, confirmed)
                else SafetyViolationCode.CONFIRMATION_PROVENANCE_MISSING
            )
            if not confirmed or not statement_is_supported(claim.statement, confirmed):
                _append_finding(findings, seen, code, claim_id=claim.id)
        case MatchStatus.NEEDS_CONFIRMATION:
            _append_finding(
                findings,
                seen,
                SafetyViolationCode.INFERENCE_REQUIRES_CONFIRMATION,
                claim_id=claim.id,
            )
        case MatchStatus.REJECTED:
            _append_finding(
                findings, seen, SafetyViolationCode.UNSUPPORTED_CLAIM, claim_id=claim.id
            )
        case _:
            assert_never(claim.status)


def _is_user_confirmed(fact: CandidateFact) -> bool:
    match fact.provenance:
        case UserConfirmationProvenance():
            return True
        case EvidenceProvenance():
            return False
        case _:
            assert_never(fact.provenance)


def _append_rewritten_resume_findings(
    proposal: ResumeTailoringProposal,
    candidate_facts: tuple[CandidateFact, ...],
    findings: list[ValidationFinding],
    seen: set[SafetyViolationCode],
) -> None:
    authorized_texts = tuple(fact.statement for fact in candidate_facts) + tuple(
        change.after for change in proposal.changes
    )
    if has_prompt_injection_content(proposal.rewritten_resume):
        _append_finding(
            findings,
            seen,
            SafetyViolationCode.PROMPT_INJECTION_CONTENT,
            claim_id=None,
        )
    if not text_is_covered(proposal.rewritten_resume, authorized_texts):
        _append_finding(
            findings, seen, SafetyViolationCode.UNSUPPORTED_CLAIM, claim_id=None
        )


def _is_evidence_backed(fact: CandidateFact) -> bool:
    match fact.provenance:
        case EvidenceProvenance():
            return True
        case UserConfirmationProvenance():
            return False
        case _:
            assert_never(fact.provenance)


def _append_text_findings(
    findings: list[ValidationFinding],
    seen: set[SafetyViolationCode],
    statement: str,
    referenced: tuple[CandidateFact, ...],
    claim_id: str | None,
) -> None:
    for code in unsupported_text_codes(statement, referenced):
        _append_finding(findings, seen, code, claim_id=claim_id)


def _append_finding(
    findings: list[ValidationFinding],
    seen: set[SafetyViolationCode],
    code: SafetyViolationCode,
    *,
    claim_id: str | None,
) -> None:
    if code in seen:
        return
    seen.add(code)
    findings.append(_finding(code, reference=claim_id))


def _finding(
    code: SafetyViolationCode,
    *,
    reference: str | None,
) -> ValidationFinding:
    requires_confirmation = code is SafetyViolationCode.INFERENCE_REQUIRES_CONFIRMATION
    digest = sha256(f"{code.value}\x1f{reference or ''}".encode()).hexdigest()[:12]
    return ValidationFinding(
        id=f"safety-{digest}",
        code=code.value,
        severity=(
            ValidationSeverity.WARNING if requires_confirmation else ValidationSeverity.ERROR
        ),
        message=code.value.replace("_", " "),
        claim_id=reference,
        confirmation_prompt=(
            "Confirm this inferred candidate fact explicitly."
            if requires_confirmation
            else None
        ),
    )
