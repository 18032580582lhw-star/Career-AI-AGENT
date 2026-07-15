"""Prepare host-proposal tailoring runs."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - Typer and Pydantic resolve runtime paths.

from pydantic import TypeAdapter

from career_ai.rendering.latex.templates import load_system_template
from career_ai.tailoring.generation_context import build_generation_context
from career_ai.tailoring.host_run_models import (
    HostPrepareResult,
    HostProposalInput,
    HostRunRequest,
)
from career_ai.tailoring.host_run_persistence import (
    CONTEXT_FILE,
    FACTS_FILE,
    REQUEST_FILE,
    artifact_name,
    ensure_run_dir,
    hash_text,
    new_run_id,
    read_text,
    write_candidate_facts,
)
from career_ai.tailoring.manifest_contracts import TemplateType
from career_ai.workspace import create_workspace, write_json_atomic

_HOST_PROPOSAL_INPUT_ADAPTER: TypeAdapter[HostProposalInput] = TypeAdapter(
    HostProposalInput,
)


def prepare_host_run(
    *,
    workspace: Path,
    resume_file: Path,
    jd_file: Path,
    latex_template: Path | None = None,
    language: str = "en",
) -> HostPrepareResult:
    """Create a persistent host-proposal request package."""
    _ = create_workspace(workspace)
    run_id = new_run_id()
    resume_text = read_text(resume_file)
    jd_text = read_text(jd_file)
    template_source = read_text(latex_template) if latex_template is not None else None
    template_type = TemplateType.USER if latex_template is not None else TemplateType.SYSTEM
    template_material = load_system_template() if template_source is None else template_source
    template_hash = hash_text(template_material)
    source_hashes = {"resume": hash_text(resume_text), "jd": hash_text(jd_text)}
    request = HostRunRequest(
        run_id=run_id,
        resume_text=resume_text,
        jd_text=jd_text,
        source_hashes=source_hashes,
        output_language=language,
        resume_path=str(resume_file),
        jd_path=str(jd_file),
        template_type=template_type,
        template_path=None if latex_template is None else str(latex_template),
        template_source=template_source,
        template_hash=template_hash,
    )
    context = build_generation_context(
        resume_text=resume_text,
        jd_text=jd_text,
        run_id=run_id,
    ).model_copy(update={"template_hash": template_hash, "output_language": language})
    run_dir = ensure_run_dir(workspace, run_id)
    write_json_atomic(run_dir / REQUEST_FILE, request)
    write_json_atomic(run_dir / CONTEXT_FILE, context)
    write_candidate_facts(run_dir / FACTS_FILE, context.candidate_facts)
    return HostPrepareResult(
        run_id=run_id,
        request_artifact=artifact_name(run_id, REQUEST_FILE),
        proposal_schema=_HOST_PROPOSAL_INPUT_ADAPTER.json_schema(),
        source_hashes=source_hashes,
        template_type=template_type,
        template_hash=template_hash,
        next_machine_instruction=(
            "career-ai-agent validate-draft --run-id "
            f"{run_id} --proposal-file proposal.json"
        ),
    )
