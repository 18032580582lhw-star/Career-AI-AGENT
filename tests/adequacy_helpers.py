"""Typed factories shared by adequacy harness tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from career_ai.tailoring.adequacy import evaluate_optimization_adequacy
from career_ai.tailoring.adequacy_models import AdequacyContext
from career_ai.tailoring.models import (
    CandidateFact,
    CandidateFactId,
    EvidenceProvenance,
    EvidenceRequirementMatch,
    EvidenceSpanId,
    FactRequirementMatchId,
    JDRequirement,
    JDRequirementId,
    MatchStatus,
    RequirementPriority,
)
from career_ai.tailoring.proposal_contracts import (
    ResumeTailoringProposal,
    calculate_proposal_hash,
)

if TYPE_CHECKING:
    from pydantic import JsonValue

HASH_A: Final = "a" * 64
HASH_B: Final = "b" * 64


@dataclass(frozen=True, slots=True)
class ProposalSpec:
    fact_ids: tuple[str, ...] = ("fact-1", "fact-2")
    target_ids: tuple[str, ...] = ("requirement-6",)
    before: str = "Built Python workflow 1."
    after: str = "Built Python workflow 1 and workflow 2."
    rewritten_resume: str = "Engineer\nBuilt Python workflow 1 and workflow 2."
    include_change: bool = True


DEFAULT_PROPOSAL_SPEC: Final = ProposalSpec()


def facts(count: int) -> tuple[CandidateFact, ...]:
    return tuple(
        CandidateFact(
            id=CandidateFactId(f"fact-{index}"),
            statement=f"Built Python workflow {index}.",
            provenance=EvidenceProvenance(
                evidence_span_ids=(EvidenceSpanId(f"evidence-{index}"),)
            ),
        )
        for index in range(1, count + 1)
    )


def requirements(count: int) -> tuple[JDRequirement, ...]:
    return tuple(
        JDRequirement(
            id=JDRequirementId(f"requirement-{index}"),
            statement=f"Required Python capability {index}",
            priority=RequirementPriority.REQUIRED,
            evidence_span_ids=(EvidenceSpanId(f"jd-evidence-{index}"),),
        )
        for index in range(1, count + 1)
    )


def evidence_match(
    requirement: int,
    fact: int,
    status: MatchStatus = MatchStatus.SUPPORTED,
) -> EvidenceRequirementMatch:
    return EvidenceRequirementMatch(
        id=FactRequirementMatchId(f"match-{requirement}-{fact}"),
        requirement_id=JDRequirementId(f"requirement-{requirement}"),
        candidate_fact_id=CandidateFactId(f"fact-{fact}"),
        evidence_span_ids=(EvidenceSpanId(f"evidence-{fact}"),),
        status=status,
    )


def proposal(spec: ProposalSpec = DEFAULT_PROPOSAL_SPEC) -> ResumeTailoringProposal:
    changes: list[JsonValue] = []
    if spec.include_change:
        changes.append(
            {
                "id": "change-1",
                "section": "experience",
                "before": spec.before,
                "after": spec.after,
                "source_fact_ids": list(spec.fact_ids),
                "target_requirement_ids": list(spec.target_ids),
                "operation": "rewrite",
                "proposed_claim_ids": [],
                "risk_notes": [],
            }
        )
    payload: dict[str, JsonValue] = {
        "protocol_version": "1.0",
        "schema_version": 1,
        "run_id": "run-adequacy-001",
        "source_hashes": {"resume": HASH_A, "jd": HASH_B},
        "template_hash": None,
        "strategy": "ats-aligned",
        "changes": changes,
        "proposed_claims": [],
        "rewritten_resume": spec.rewritten_resume,
    }
    payload["proposal_hash"] = calculate_proposal_hash(payload)
    return ResumeTailoringProposal.model_validate(payload)


def evaluate(
    candidate: ResumeTailoringProposal,
    adequacy_context: AdequacyContext,
) -> tuple[bool, int, int, tuple[str, ...]]:
    result = evaluate_optimization_adequacy(candidate, adequacy_context)
    return (
        result.passed,
        result.baseline_score,
        result.projected_score,
        tuple(finding.code for finding in result.findings),
    )


def context(
    fact_count: int,
    requirement_count: int,
    matches: tuple[EvidenceRequirementMatch, ...],
    baseline_ids: frozenset[str],
    baseline_text: str = "Engineer\nBuilt Python workflow 1.",
) -> AdequacyContext:
    return AdequacyContext(
        candidate_facts=facts(fact_count),
        requirements=requirements(requirement_count),
        evidence_matches=matches,
        baseline_covered_requirement_ids=baseline_ids,
        baseline_resume_text=baseline_text,
    )
