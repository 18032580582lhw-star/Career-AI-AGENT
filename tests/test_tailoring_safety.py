from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pydantic import JsonValue

from career_ai.tailoring.models import (
    CandidateFact,
    CandidateFactId,
    EvidenceProvenance,
    EvidenceSpanId,
    MatchStatus,
    UserConfirmationProvenance,
)
from career_ai.tailoring.proposal_contracts import (
    ChangeOperation,
    ProposalStrategy,
    ProposedClaim,
    ResumeChange,
    ResumeTailoringProposal,
    calculate_proposal_hash,
)
from career_ai.tailoring.safety import evaluate_factual_safety

HASH_A: Final = "a" * 64
HASH_B: Final = "b" * 64


def _fact(
    fact_id: str,
    statement: str,
    *,
    confirmed: bool = False,
) -> CandidateFact:
    provenance = (
        UserConfirmationProvenance(confirmation=f"User confirmed: {statement}")
        if confirmed
        else EvidenceProvenance(evidence_span_ids=(EvidenceSpanId(f"evidence-{fact_id}"),))
    )
    return CandidateFact(
        id=CandidateFactId(fact_id),
        statement=statement,
        provenance=provenance,
    )


def _proposal(
    *,
    after: str,
    fact_ids: tuple[str, ...],
    claim_status: MatchStatus,
) -> ResumeTailoringProposal:
    claim = ProposedClaim(
        id="claim-1",
        statement=after,
        source_fact_ids=fact_ids,
        status=claim_status,
    )
    change = ResumeChange(
        id="change-1",
        section="experience",
        before="Original text.",
        after=after,
        source_fact_ids=fact_ids,
        target_requirement_ids=("requirement-1",),
        operation=ChangeOperation.REWRITE,
        proposed_claim_ids=(claim.id,),
    )
    payload: dict[str, JsonValue] = {
        "protocol_version": "1.0",
        "schema_version": 1,
        "run_id": "run-safety-001",
        "source_hashes": {"resume": HASH_A, "jd": HASH_B},
        "template_hash": None,
        "strategy": ProposalStrategy.ATS_ALIGNED,
        "rewritten_resume": after,
        "changes": [
            {
                "id": change.id,
                "section": change.section,
                "before": change.before,
                "after": change.after,
                "source_fact_ids": list(change.source_fact_ids),
                "target_requirement_ids": list(change.target_requirement_ids),
                "operation": change.operation.value,
                "proposed_claim_ids": list(change.proposed_claim_ids),
                "risk_notes": list(change.risk_notes),
            }
        ],
        "proposed_claims": [
            {
                "id": claim.id,
                "statement": claim.statement,
                "source_fact_ids": list(claim.source_fact_ids),
                "status": claim.status.value,
            }
        ],
    }
    payload["proposal_hash"] = calculate_proposal_hash(payload)
    return ResumeTailoringProposal.model_validate(payload)


def _evaluate(
    proposal: ResumeTailoringProposal,
    facts: tuple[CandidateFact, ...],
) -> tuple[bool, tuple[str, ...]]:
    result = evaluate_factual_safety(proposal, facts)
    return result.passed, tuple(finding.code for finding in result.findings)


fact = _fact
proposal = _proposal
evaluate = _evaluate


def test_safety_harness_accepts_evidence_preserving_rewrite() -> None:
    fact = _fact("fact-python", "Built Python data pipelines.")
    proposal = _proposal(
        after="Built Python data pipelines.",
        fact_ids=("fact-python",),
        claim_status=MatchStatus.SUPPORTED,
    )

    assert _evaluate(proposal, (fact,)) == (True, ())


def test_safety_harness_rejects_jd_only_technology() -> None:
    fact = _fact("fact-python", "Built Python data pipelines.")
    proposal = _proposal(
        after="Built Kubernetes data platforms.",
        fact_ids=("fact-python",),
        claim_status=MatchStatus.SUPPORTED,
    )

    assert _evaluate(proposal, (fact,)) == (False, ("unsupported_technology",))


def test_safety_harness_reports_responsibility_seniority_and_metric_inflation() -> None:
    fact = _fact("fact-support", "Supported a campaign dashboard for a manager.")
    proposal = _proposal(
        after="Owned global strategy, led a team of eight, and increased conversion by 45%.",
        fact_ids=("fact-support",),
        claim_status=MatchStatus.SUPPORTED,
    )

    assert _evaluate(proposal, (fact,)) == (
        False,
        ("unsupported_responsibility", "unsupported_seniority", "unsupported_metric"),
    )


def test_safety_harness_pauses_reasonable_inference_for_confirmation() -> None:
    fact = _fact("fact-research", "Facilitated recurring user interviews.")
    proposal = _proposal(
        after="Owned an end-to-end research program.",
        fact_ids=("fact-research",),
        claim_status=MatchStatus.NEEDS_CONFIRMATION,
    )

    assert _evaluate(proposal, (fact,)) == (False, ("inference_requires_confirmation",))


def test_safety_harness_accepts_only_explicitly_confirmed_fact() -> None:
    confirmed = _fact("fact-location", "Can relocate to Hong Kong.", confirmed=True)
    proposal = _proposal(
        after="Can relocate to Hong Kong.",
        fact_ids=("fact-location",),
        claim_status=MatchStatus.CONFIRMED,
    )

    assert _evaluate(proposal, (confirmed,)) == (True, ())


def test_safety_harness_rejects_unknown_fact_reference() -> None:
    proposal = _proposal(
        after="Built Python data pipelines.",
        fact_ids=("fact-missing",),
        claim_status=MatchStatus.SUPPORTED,
    )

    assert _evaluate(proposal, ()) == (False, ("unknown_source_fact",))


def test_safety_harness_checks_change_without_proposed_claim() -> None:
    fact = _fact("fact-python", "Built Python data pipelines.")
    proposal = _proposal(
        after="Built Kubernetes data platforms.",
        fact_ids=("fact-python",),
        claim_status=MatchStatus.SUPPORTED,
    )
    payload = proposal.model_dump(mode="json")
    payload["changes"][0]["proposed_claim_ids"] = []
    payload["proposed_claims"] = []
    payload["proposal_hash"] = calculate_proposal_hash(payload)
    unclaimed = ResumeTailoringProposal.model_validate(payload)

    assert _evaluate(unclaimed, (fact,)) == (False, ("unsupported_technology",))


def test_confirmation_does_not_authorize_unrelated_claim_text() -> None:
    confirmed = _fact("fact-location", "Can relocate to Hong Kong.", confirmed=True)
    proposal = _proposal(
        after="Managed a team of 100 engineers.",
        fact_ids=("fact-location",),
        claim_status=MatchStatus.CONFIRMED,
    )

    assert _evaluate(proposal, (confirmed,)) == (
        False,
        ("confirmation_statement_mismatch",),
    )


def test_safety_harness_rejects_duplicate_candidate_fact_ids() -> None:
    first = _fact("fact-duplicate", "Built Python pipelines.")
    second = _fact("fact-duplicate", "Managed a team of 100 engineers.")
    proposal = _proposal(
        after="Built Python pipelines.",
        fact_ids=("fact-duplicate",),
        claim_status=MatchStatus.SUPPORTED,
    )

    assert _evaluate(proposal, (first, second)) == (False, ("duplicate_source_fact",))


def test_safety_harness_rejects_unclassified_unsupported_claim() -> None:
    fact = _fact("fact-python", "Built Python data pipelines.")
    proposal = _proposal(
        after="Won the Nobel Prize.",
        fact_ids=("fact-python",),
        claim_status=MatchStatus.SUPPORTED,
    )

    assert _evaluate(proposal, (fact,)) == (False, ("unsupported_claim",))


def test_supported_claim_requires_resume_evidence_provenance() -> None:
    confirmed = _fact("fact-location", "Can relocate to Hong Kong.", confirmed=True)
    proposal = _proposal(
        after="Can relocate to Hong Kong.",
        fact_ids=("fact-location",),
        claim_status=MatchStatus.SUPPORTED,
    )

    assert _evaluate(proposal, (confirmed,)) == (
        False,
        ("supported_provenance_mismatch",),
    )


def test_change_and_claim_must_use_the_same_fact_set() -> None:
    python_fact = _fact("fact-python", "Built Python pipelines.")
    sql_fact = _fact("fact-sql", "Built SQL reports.")
    proposal = _proposal(
        after="Built Python pipelines.",
        fact_ids=("fact-python",),
        claim_status=MatchStatus.SUPPORTED,
    )
    payload = proposal.model_dump(mode="json")
    payload["changes"][0]["source_fact_ids"] = ["fact-sql"]
    payload["proposal_hash"] = calculate_proposal_hash(payload)
    mismatched = ResumeTailoringProposal.model_validate(payload)

    assert _evaluate(mismatched, (python_fact, sql_fact)) == (
        False,
        ("change_claim_fact_mismatch",),
    )


def test_full_rewritten_resume_cannot_bypass_structured_safety() -> None:
    fact = _fact("fact-python", "Built Python data pipelines.")
    safe = _proposal(
        after="Built Python data pipelines.",
        fact_ids=("fact-python",),
        claim_status=MatchStatus.SUPPORTED,
    )
    payload = safe.model_dump(mode="json")
    payload["rewritten_resume"] = "Senior Kubernetes leader increased revenue by 500%."
    payload["proposal_hash"] = calculate_proposal_hash(payload)
    bypass = ResumeTailoringProposal.model_validate(payload)

    passed, codes = _evaluate(bypass, (fact,))
    assert passed is False
    assert "unsupported_claim" in codes


def test_claim_link_does_not_hide_unsafe_change_text() -> None:
    fact = _fact("fact-python", "Built Python data pipelines.")
    safe = _proposal(
        after="Built Python data pipelines.",
        fact_ids=("fact-python",),
        claim_status=MatchStatus.SUPPORTED,
    )
    payload = safe.model_dump(mode="json")
    payload["changes"][0]["after"] = "Managed a team of 100 engineers."
    payload["rewritten_resume"] = "Managed a team of 100 engineers."
    payload["proposal_hash"] = calculate_proposal_hash(payload)
    bypass = ResumeTailoringProposal.model_validate(payload)

    passed, codes = _evaluate(bypass, (fact,))
    assert passed is False
    assert "unsupported_seniority" in codes
    assert "unsupported_metric" in codes
