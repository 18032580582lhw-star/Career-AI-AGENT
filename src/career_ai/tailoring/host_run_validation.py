"""Validation and tailoring entry points for host-proposal runs."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - CLI-facing runtime type.
from typing import TYPE_CHECKING

from pydantic import TypeAdapter, ValidationError

from career_ai.rendering.latex.templates import load_system_template
from career_ai.tailoring.document_acceptance import (
    DocumentAcceptanceError,
    accept_resume_document,
)
from career_ai.tailoring.document_contracts import (
    ResumeDocumentDraft,  # noqa: TC001
    StructuredResumeTailoringProposal,  # noqa: TC001
)
from career_ai.tailoring.generation_models import ProposalOutcome, ProposalSource
from career_ai.tailoring.generation_workflow import (
    run_api_proposal_workflow,
    run_host_proposal_workflow,
)
from career_ai.tailoring.host_run_models import (
    HostProposalInput,
    HostRunError,
    HostRunRequest,
    HostStructuredProposalPackage,
    HostValidationResult,
)
from career_ai.tailoring.host_run_persistence import (
    DRAFT_FILE,
    FACTS_FILE,
    PROPOSAL_FILE,
    REQUEST_FILE,
    VALIDATION_FILE,
    ensure_run_dir,
    hash_text,
    load_proposal,
    load_run_context,
    write_candidate_facts,
)
from career_ai.tailoring.manifest_contracts import RunState, TemplateType
from career_ai.tailoring.models import CandidateFact  # noqa: TC001
from career_ai.tailoring.proposal_contracts import (
    ConfirmationDecision,
    ConfirmationResponse,
    ResumeTailoringProposal,
)
from career_ai.tailoring.state_machine import ValidationStateResult  # noqa: TC001
from career_ai.workspace import create_workspace, write_json_atomic

if TYPE_CHECKING:
    from career_ai.llm.client import LLMClient

_HOST_PROPOSAL_INPUT_ADAPTER: TypeAdapter[HostProposalInput] = TypeAdapter(
    HostProposalInput,
)


def validate_host_draft(
    *,
    workspace: Path,
    run_id: str,
    proposal_file: Path,
) -> HostValidationResult:
    """Validate one host proposal from strict JSON, never Markdown."""
    raw = proposal_file.read_text(encoding="utf-8-sig")
    if raw.lstrip().startswith("```"):
        message = "proposal_file must contain strict JSON, not Markdown code fences"
        raise HostRunError(message)
    try:
        proposal_input = _HOST_PROPOSAL_INPUT_ADAPTER.validate_json(raw)
    except ValidationError as error:
        message = f"proposal_file must contain strict JSON: {error}"
        raise HostRunError(message) from error
    context = load_run_context(workspace, run_id)
    match proposal_input:
        case HostStructuredProposalPackage(draft=draft, proposal=proposal):
            result = run_host_proposal_workflow(context, (proposal,), context.task_package())
            outcome = result.outcomes[0]
            if outcome.state is RunState.ACCEPTED:
                try:
                    _ = accept_resume_document(
                        draft,
                        proposal,
                        outcome.decision,
                        context.candidate_facts,
                    )
                except DocumentAcceptanceError as error:
                    message = (
                        "structured proposal package failed document acceptance: "
                        f"{error}"
                    )
                    raise HostRunError(message) from error
                _save_structured_validation(
                    workspace=workspace,
                    run_id=run_id,
                    draft=draft,
                    proposal=proposal,
                    validation=outcome.decision,
                    candidate_facts=context.candidate_facts,
                )
            else:
                _save_best_validation(workspace, run_id, outcome.proposal, outcome.decision)
        case ResumeTailoringProposal() as proposal:
            result = run_host_proposal_workflow(context, (proposal,), context.task_package())
            outcome = result.outcomes[0]
            _save_best_validation(workspace, run_id, outcome.proposal, outcome.decision)
    return _validation_result(run_id, outcome)


def tailor_with_api(
    *,
    workspace: Path,
    run_id: str,
    client: LLMClient,
) -> HostValidationResult:
    """Ask the configured provider for proposals, then run the local harnesses."""
    context = load_run_context(workspace, run_id)
    result = run_api_proposal_workflow(context, client)
    if not result.outcomes:
        return HostValidationResult(
            run_id=run_id,
            source=ProposalSource.API,
            state=RunState.REJECTED,
        )
    best = max(result.outcomes, key=lambda item: item.score)
    _save_best_validation(workspace, run_id, best.proposal, best.decision)
    return HostValidationResult(
        run_id=run_id,
        source=ProposalSource.API,
        state=best.state,
        proposal_hash=best.proposal.proposal_hash,
        validation_hash=best.decision.decision.validation_hash,
    )


def confirm_host_fact(
    *,
    workspace: Path,
    run_id: str,
    confirmation_file: Path,
) -> HostValidationResult:
    """Persist a confirmation response and rerun the local validation path."""
    confirmation = ConfirmationResponse.model_validate_json(
        confirmation_file.read_text(encoding="utf-8-sig"),
    )
    if confirmation.run_id != run_id:
        message = "confirmation run_id does not match the selected run"
        raise HostRunError(message)
    if confirmation.decision is ConfirmationDecision.REJECT:
        return HostValidationResult(
            run_id=run_id,
            source=ProposalSource.HOST,
            state=RunState.REJECTED,
        )
    proposal = load_proposal(workspace, run_id)
    context = load_run_context(workspace, run_id)
    result = run_host_proposal_workflow(context, (proposal,), context.task_package())
    _save_best_validation(workspace, run_id, proposal, result.outcomes[0].decision)
    return HostValidationResult(
        run_id=run_id,
        source=ProposalSource.HOST,
        state=result.outcomes[0].state,
        proposal_hash=proposal.proposal_hash,
        validation_hash=result.outcomes[0].decision.decision.validation_hash,
    )


def save_accepted_run(  # noqa: PLR0913 - persists a complete accepted fixture.
    workspace: Path,
    *,
    request_payload: dict[str, str],
    draft: ResumeDocumentDraft,
    proposal: StructuredResumeTailoringProposal,
    validation: ValidationStateResult,
    candidate_facts: tuple[CandidateFact, ...],
) -> None:
    """Persist a complete accepted run for integration and migration tests."""
    _ = create_workspace(workspace)
    template_source = request_payload.get("template_source")
    template_path = request_payload.get("template_path")
    template_material = load_system_template() if template_source is None else template_source
    template_hash = hash_text(template_material)
    request = HostRunRequest(
        run_id=proposal.run_id,
        resume_text=request_payload["resume_text"],
        jd_text=request_payload["jd_text"],
        source_hashes=dict(proposal.source_hashes),
        output_language=request_payload["output_language"],
        template_type=TemplateType.USER if template_path is not None else TemplateType.SYSTEM,
        template_path=template_path,
        template_source=template_source,
        template_hash=template_hash,
    )
    run_dir = ensure_run_dir(workspace, proposal.run_id)
    write_json_atomic(run_dir / REQUEST_FILE, request)
    write_json_atomic(run_dir / DRAFT_FILE, draft)
    write_json_atomic(run_dir / PROPOSAL_FILE, proposal)
    write_json_atomic(run_dir / VALIDATION_FILE, validation)
    write_candidate_facts(run_dir / FACTS_FILE, candidate_facts)


def _save_best_validation(
    workspace: Path,
    run_id: str,
    proposal: ResumeTailoringProposal,
    validation: ValidationStateResult,
) -> None:
    run_dir = ensure_run_dir(workspace, run_id)
    write_json_atomic(run_dir / PROPOSAL_FILE, proposal)
    write_json_atomic(run_dir / VALIDATION_FILE, validation)


def _save_structured_validation(  # noqa: PLR0913 - persists the render-ready run bundle.
    *,
    workspace: Path,
    run_id: str,
    draft: ResumeDocumentDraft,
    proposal: StructuredResumeTailoringProposal,
    validation: ValidationStateResult,
    candidate_facts: tuple[CandidateFact, ...],
) -> None:
    run_dir = ensure_run_dir(workspace, run_id)
    write_json_atomic(run_dir / DRAFT_FILE, draft)
    write_json_atomic(run_dir / PROPOSAL_FILE, proposal)
    write_json_atomic(run_dir / VALIDATION_FILE, validation)
    write_candidate_facts(run_dir / FACTS_FILE, candidate_facts)


def _validation_result(run_id: str, outcome: ProposalOutcome) -> HostValidationResult:
    return HostValidationResult(
        run_id=run_id,
        source=ProposalSource.HOST,
        state=outcome.state,
        proposal_hash=outcome.proposal.proposal_hash,
        validation_hash=outcome.decision.decision.validation_hash,
    )
