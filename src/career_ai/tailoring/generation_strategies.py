"""Deterministic proposal strategies that operate only on typed evidence."""

from __future__ import annotations

from typing import TYPE_CHECKING

from career_ai.tailoring.models import MatchStatus
from career_ai.tailoring.proposal_contracts import (
    ChangeOperation,
    ProposalStrategy,
    ProposedClaim,
    ResumeChange,
    ResumeTailoringProposal,
    calculate_proposal_hash,
)

if TYPE_CHECKING:
    from pydantic import JsonValue

    from career_ai.tailoring.generation_models import TailoringGenerationContext
    from career_ai.tailoring.models import CandidateFact


def generate_local_proposals(
    context: TailoringGenerationContext,
) -> tuple[ResumeTailoringProposal, ...]:
    """Generate conservative, ATS, and impact proposals from trusted facts only."""
    selections = _supported_selections(context)
    return (
        _conservative_proposal(context),
        _evidence_addition_proposal(context, ProposalStrategy.ATS_ALIGNED, selections),
        _evidence_addition_proposal(
            context,
            ProposalStrategy.IMPACT_NARRATIVE,
            _impact_selections(selections),
        ),
    )


def _conservative_proposal(context: TailoringGenerationContext) -> ResumeTailoringProposal:
    return _build_proposal(
        context,
        ProposalStrategy.CONSERVATIVE,
        rewritten_resume=context.baseline_resume_text,
        changes=(),
        claims=(),
    )


def _evidence_addition_proposal(
    context: TailoringGenerationContext,
    strategy: ProposalStrategy,
    selections: tuple[tuple[str, CandidateFact], ...],
) -> ResumeTailoringProposal:
    if not selections:
        return _build_proposal(
            context,
            strategy,
            rewritten_resume=context.baseline_resume_text,
            changes=(),
            claims=(),
        )
    selected_facts = _unique_facts(selections)
    source_fact_ids = tuple(str(item.id) for item in selected_facts)
    target_requirement_ids = tuple(dict.fromkeys(item[0] for item in selections))
    after = "\n".join(item.statement for item in selected_facts)
    claim_status = _claim_status(selected_facts)
    if claim_status is None:
        return _build_proposal(
            context,
            strategy,
            rewritten_resume=context.baseline_resume_text,
            changes=(),
            claims=(),
        )
    claim = ProposedClaim(
        id=f"claim-{strategy.value}",
        statement=after,
        source_fact_ids=source_fact_ids,
        status=claim_status,
    )
    change = ResumeChange(
        id=f"change-{strategy.value}",
        section="experience",
        before="",
        after=after,
        source_fact_ids=source_fact_ids,
        target_requirement_ids=target_requirement_ids,
        operation=ChangeOperation.ADD,
        proposed_claim_ids=(claim.id,),
    )
    return _build_proposal(
        context,
        strategy,
        rewritten_resume=f"{context.baseline_resume_text}\n{after}",
        changes=(change,),
        claims=(claim,),
    )


def _supported_selections(
    context: TailoringGenerationContext,
) -> tuple[tuple[str, CandidateFact], ...]:
    facts_by_id = {str(fact.id): fact for fact in context.candidate_facts}
    selections: list[tuple[str, CandidateFact]] = []
    for item in context.evidence_matches:
        if item.status not in {MatchStatus.SUPPORTED, MatchStatus.CONFIRMED}:
            continue
        if item.candidate_fact_id is None:
            continue
        fact = facts_by_id.get(str(item.candidate_fact_id))
        if fact is not None:
            selections.append((str(item.requirement_id), fact))
    return tuple(selections)


def _unique_facts(
    selections: tuple[tuple[str, CandidateFact], ...],
) -> tuple[CandidateFact, ...]:
    by_id: dict[str, CandidateFact] = {}
    for _, fact in selections:
        fact_id = str(fact.id)
        if fact_id not in by_id:
            by_id[fact_id] = fact
    return tuple(by_id.values())


def _impact_selections(
    selections: tuple[tuple[str, CandidateFact], ...],
) -> tuple[tuple[str, CandidateFact], ...]:
    unique = _unique_facts(selections)
    longest_facts = sorted(unique, key=lambda item: len(item.statement))[-1:]
    selected_ids = {str(item.id) for item in longest_facts}
    return tuple(item for item in selections if str(item[1].id) in selected_ids)


def _claim_status(facts: tuple[CandidateFact, ...]) -> MatchStatus | None:
    provenance_kinds = tuple(sorted({fact.provenance.kind for fact in facts}))
    match provenance_kinds:
        case ("evidence",):
            return MatchStatus.SUPPORTED
        case ("user_confirmation",):
            return MatchStatus.CONFIRMED
        case _:
            return None


def _build_proposal(
    context: TailoringGenerationContext,
    strategy: ProposalStrategy,
    *,
    rewritten_resume: str,
    changes: tuple[ResumeChange, ...],
    claims: tuple[ProposedClaim, ...],
) -> ResumeTailoringProposal:
    payload: dict[str, JsonValue] = {
        "protocol_version": "1.0",
        "schema_version": 1,
        "run_id": context.run_id,
        "source_hashes": dict(context.source_hashes),
        "template_hash": context.template_hash,
        "strategy": strategy.value,
        "rewritten_resume": rewritten_resume,
        "changes": [item.model_dump(mode="json") for item in changes],
        "proposed_claims": [item.model_dump(mode="json") for item in claims],
    }
    payload["proposal_hash"] = calculate_proposal_hash(payload)
    return ResumeTailoringProposal.model_validate(payload)
