"""Live integrity checks and manifest writes for host-run rendering."""

from __future__ import annotations

from pathlib import Path

from career_ai.rendering.latex.templates import load_system_template
from career_ai.tailoring.contract_base import canonical_json_hash
from career_ai.tailoring.document_contracts import (
    AcceptedResumeDocument,  # noqa: TC001
    StructuredResumeTailoringProposal,  # noqa: TC001
)
from career_ai.tailoring.host_run_models import HostRunRequest  # noqa: TC001
from career_ai.tailoring.host_run_persistence import (
    RUN_MANIFEST_FILE,
    hash_text,
    read_text,
    request_hash,
    run_path,
)
from career_ai.tailoring.manifest_contracts import RunManifest, RunState, TemplateType
from career_ai.tailoring.proposal_contracts import calculate_proposal_hash
from career_ai.tailoring.state_machine import ValidationStateResult, calculate_validation_hash
from career_ai.workspace import write_json_atomic


def run_is_current(
    request: HostRunRequest,
    proposal: StructuredResumeTailoringProposal,
    validation: ValidationStateResult,
    accepted: AcceptedResumeDocument,
) -> bool:
    """Recompute all identities that authorize rendering."""
    proposal_payload = proposal.model_dump(mode="json", exclude={"proposal_hash"})
    validation_hash = calculate_validation_hash(
        proposal,
        validation.decision.outcome,
        validation.decision.findings,
        safety_passed=validation.decision.safety_passed,
        adequacy_passed=validation.decision.adequacy_passed,
    )
    return (
        _current_source_hashes(request) == dict(proposal.source_hashes) == request.source_hashes
        and _current_template_hash(request) == proposal.template_hash == request.template_hash
        and calculate_proposal_hash(proposal_payload) == proposal.proposal_hash
        and validation_hash == validation.decision.validation_hash
        and accepted.proposal_hash == proposal.proposal_hash
        and accepted.validation_hash == validation.decision.validation_hash
    )


def write_stale_manifest(workspace: Path, request: HostRunRequest) -> None:
    """Persist a stale run manifest after live identity drift."""
    manifest = RunManifest(
        workspace_schema_version=1,
        run_id=request.run_id,
        state=RunState.STALE,
        source_hashes=request.source_hashes,
        request_hash=request_hash(request),
        template_hash=request.template_hash,
    )
    write_json_atomic(run_path(workspace, request.run_id, RUN_MANIFEST_FILE), manifest)


def write_rendered_run_manifest(
    workspace: Path,
    request: HostRunRequest,
    proposal: StructuredResumeTailoringProposal,
    validation: ValidationStateResult,
    accepted: AcceptedResumeDocument,
) -> None:
    """Persist the run-level rendered state."""
    manifest = RunManifest(
        workspace_schema_version=1,
        run_id=request.run_id,
        state=RunState.RENDERED,
        source_hashes=request.source_hashes,
        request_hash=request_hash(request),
        proposal_hash=proposal.proposal_hash,
        validation_hash=validation.decision.validation_hash,
        accepted_document_hash=accepted_document_hash(accepted),
        template_hash=request.template_hash,
    )
    write_json_atomic(run_path(workspace, request.run_id, RUN_MANIFEST_FILE), manifest)


def accepted_document_hash(accepted: AcceptedResumeDocument) -> str:
    """Hash the accepted document structure and provenance."""
    return canonical_json_hash(accepted.model_dump(mode="json"))


def _current_source_hashes(request: HostRunRequest) -> dict[str, str]:
    resume = (
        read_text(Path(request.resume_path))
        if request.resume_path is not None
        else request.resume_text
    )
    jd = read_text(Path(request.jd_path)) if request.jd_path is not None else request.jd_text
    return {"resume": hash_text(resume), "jd": hash_text(jd)}


def _current_template_hash(request: HostRunRequest) -> str:
    if request.template_type is TemplateType.SYSTEM or request.template_path is None:
        return hash_text(load_system_template())
    return hash_text(read_text(Path(request.template_path)))
