"""Artifact-level render manifest writing for host runs."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - manifest writer receives concrete paths.

from career_ai.tailoring.document_contracts import (
    AcceptedResumeDocument,  # noqa: TC001
    StructuredResumeTailoringProposal,  # noqa: TC001
)
from career_ai.tailoring.host_run_integrity import (
    accepted_document_hash,
    write_rendered_run_manifest,
)
from career_ai.tailoring.host_run_models import HostRunRequest  # noqa: TC001
from career_ai.tailoring.manifest_contracts import (
    OutputArtifact,
    RenderBackend,
    RenderEngine,
    RenderManifest,
)
from career_ai.tailoring.state_machine import ValidationStateResult  # noqa: TC001
from career_ai.workspace import write_json_atomic


def write_render_manifest(  # noqa: PLR0913 - writes a complete provenance envelope.
    workspace: Path,
    output_dir: Path,
    request: HostRunRequest,
    accepted: AcceptedResumeDocument,
    proposal: StructuredResumeTailoringProposal,
    validation: ValidationStateResult,
    backend: RenderBackend,
    engine: RenderEngine,
    engine_version: str | None,
    artifacts: tuple[OutputArtifact, ...],
) -> Path:
    """Write artifact-level provenance and update the run manifest."""
    manifest = RenderManifest(
        run_id=request.run_id,
        proposal_hash=proposal.proposal_hash,
        validation_hash=validation.decision.validation_hash,
        accepted_document_hash=accepted_document_hash(accepted),
        template_type=request.template_type,
        template_hash=request.template_hash,
        backend=backend,
        engine=engine,
        engine_version=engine_version,
        font_bundle_version="bundled-noto-local",
        outputs=artifacts,
        page_size="A4",
        language=request.output_language,
    )
    manifest_path = output_dir / f"{backend.value}.render-manifest.json"
    write_json_atomic(manifest_path, manifest)
    write_rendered_run_manifest(workspace, request, proposal, validation, accepted)
    return manifest_path
