"""One local validation workflow for local and host proposals."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic_core import PydanticCustomError

from career_ai.tailoring.adequacy import evaluate_optimization_adequacy
from career_ai.tailoring.generation_models import (
    ProposalOutcome,
    ProposalSource,
    TailoringGenerationContext,
    TailoringGenerationResult,
)
from career_ai.tailoring.generation_strategies import generate_local_proposals
from career_ai.tailoring.manifest_contracts import RunState
from career_ai.tailoring.proposal_contracts import ProposalStrategy
from career_ai.tailoring.safety import evaluate_factual_safety
from career_ai.tailoring.state_machine import decide_validation_state

if TYPE_CHECKING:
    from career_ai.tailoring.proposal_contracts import ResumeTailoringProposal, TailoringTaskPackage


def run_local_strategy_workflow(
    context: TailoringGenerationContext,
) -> TailoringGenerationResult:
    """Generate and grade all built-in evidence-only proposal strategies."""
    return _grade_proposals(
        context,
        generate_local_proposals(context),
        ProposalSource.LOCAL,
        context.task_package(),
    )


def run_host_proposal_workflow(
    context: TailoringGenerationContext,
    proposals: tuple[ResumeTailoringProposal, ...],
    task_package: TailoringTaskPackage | None = None,
) -> TailoringGenerationResult:
    """Grade host-created proposals through the same local harness pipeline."""
    return _grade_proposals(
        context,
        proposals,
        ProposalSource.HOST,
        task_package or context.task_package(),
    )


def _grade_proposals(
    context: TailoringGenerationContext,
    proposals: tuple[ResumeTailoringProposal, ...],
    source: ProposalSource,
    task_package: TailoringTaskPackage,
) -> TailoringGenerationResult:
    _require_task_package(context, task_package)
    outcomes = tuple(_grade_proposal(context, proposal, source) for proposal in proposals)
    best = max(
        outcomes,
        key=lambda item: (item.score, _strategy_priority(item.proposal.strategy)),
        default=None,
    )
    return TailoringGenerationResult(
        outcomes=outcomes,
        best_strategy=best.proposal.strategy if best is not None and best.score > 0 else None,
    )


def _require_task_package(
    context: TailoringGenerationContext,
    task_package: TailoringTaskPackage,
) -> None:
    if task_package != context.task_package():
        error_code = "task_package_context_mismatch"
        error_message = "task package must bind to the current generation context"
        raise PydanticCustomError(error_code, error_message)


def _grade_proposal(
    context: TailoringGenerationContext,
    proposal: ResumeTailoringProposal,
    source: ProposalSource,
) -> ProposalOutcome:
    safety = evaluate_factual_safety(proposal, context.candidate_facts)
    adequacy = evaluate_optimization_adequacy(proposal, context.adequacy_context())
    state = decide_validation_state(proposal, safety, adequacy, context.validation_context())
    return ProposalOutcome(
        source=source,
        proposal=proposal,
        state=state.state,
        decision=state,
        score=_outcome_score(state.state),
    )


def _outcome_score(state: RunState) -> int:
    match state:
        case RunState.ACCEPTED:
            return 100
        case RunState.NEEDS_CONFIRMATION:
            return 60
        case (
            RunState.DRAFT
            | RunState.VALIDATING
            | RunState.REJECTED
            | RunState.STALE
            | RunState.RENDERED
        ):
            return 0


def _strategy_priority(strategy: ProposalStrategy) -> int:
    """Prefer the lower-risk strategy when two locally graded outcomes tie."""
    match strategy:
        case ProposalStrategy.CONSERVATIVE:
            return 3
        case ProposalStrategy.ATS_ALIGNED:
            return 2
        case ProposalStrategy.IMPACT_NARRATIVE:
            return 1
        case ProposalStrategy.SAFE_FALLBACK:
            return 0
