"""Rendering for accepted host-proposal runs with live hash checks."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - renderer writes concrete paths.

from career_ai.rendering.docx import DocxResumeRenderer
from career_ai.rendering.html_playwright import HtmlPlaywrightResumeRenderer
from career_ai.rendering.latex import (
    LatexCompilationFailure,
    LatexCompilationSuccess,
    LatexCompilerConfig,
    compile_latex_pdf,
)
from career_ai.rendering.models import RendererSuccess, RenderFailure
from career_ai.tailoring.document_acceptance import accept_resume_document
from career_ai.tailoring.document_contracts import (
    AcceptedResumeDocument,
    ResumeDocumentDraft,
    StructuredResumeTailoringProposal,
)
from career_ai.tailoring.host_run_integrity import run_is_current, write_stale_manifest
from career_ai.tailoring.host_run_latex_output import write_latex_source
from career_ai.tailoring.host_run_models import (
    HostRenderFormat,
    HostRenderItem,
    HostRenderResult,
    HostRunError,
    HostRunRequest,
    expand_render_formats,
)
from career_ai.tailoring.host_run_persistence import (
    DRAFT_FILE,
    RENDER_DIR,
    ensure_run_dir,
    load_candidate_facts,
    load_request,
    load_structured_proposal,
    load_validation,
    output_artifact,
    run_path,
)
from career_ai.tailoring.host_run_render_manifest import write_render_manifest
from career_ai.tailoring.manifest_contracts import (
    RenderBackend,
    RenderEngine,
)
from career_ai.tailoring.state_machine import ValidationStateResult  # noqa: TC001


def render_host_run(
    *,
    workspace: Path,
    run_id: str,
    render_format: HostRenderFormat,
    disable_latex_engines: bool = False,
) -> HostRenderResult:
    """Render an accepted run after rechecking all immutable identities."""
    try:
        request = load_request(workspace, run_id)
        proposal = load_structured_proposal(workspace, run_id)
        validation = load_validation(workspace, run_id)
        draft = ResumeDocumentDraft.model_validate_json(
            run_path(workspace, run_id, DRAFT_FILE).read_text(encoding="utf-8-sig"),
        )
        facts = load_candidate_facts(workspace, run_id)
        accepted = accept_resume_document(draft, proposal, validation, facts)
    except (OSError, ValueError) as error:
        message = "run is not render-ready; validate and accept a proposal before rendering"
        raise HostRunError(message) from error
    if not run_is_current(request, proposal, validation, accepted):
        write_stale_manifest(workspace, request)
        return HostRenderResult(
            run_id=run_id,
            results=(HostRenderItem(format=render_format, status="stale", code="stale"),),
        )
    output_dir = ensure_run_dir(workspace, run_id) / RENDER_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    results = tuple(
        _render_one(
            workspace=workspace,
            request=request,
            proposal=proposal,
            validation=validation,
            accepted=accepted,
            output_dir=output_dir,
            render_format=item,
            disable_latex_engines=disable_latex_engines,
        )
        for item in expand_render_formats(render_format)
    )
    return HostRenderResult(run_id=run_id, results=results)


def _render_one(  # noqa: PLR0913 - render dispatch carries one run context.
    *,
    workspace: Path,
    request: HostRunRequest,
    proposal: StructuredResumeTailoringProposal,
    validation: ValidationStateResult,
    accepted: AcceptedResumeDocument,
    output_dir: Path,
    render_format: HostRenderFormat,
    disable_latex_engines: bool,
) -> HostRenderItem:
    match render_format:
        case HostRenderFormat.DOCX:
            outcome = DocxResumeRenderer().render(accepted, output_dir)
            return _renderer_item(
                workspace,
                request,
                proposal,
                validation,
                accepted,
                render_format,
                outcome,
                RenderEngine.DOCX,
            )
        case HostRenderFormat.PDF:
            outcome = HtmlPlaywrightResumeRenderer().render(accepted, output_dir)
            return _renderer_item(
                workspace,
                request,
                proposal,
                validation,
                accepted,
                render_format,
                outcome,
                RenderEngine.PLAYWRIGHT,
            )
        case HostRenderFormat.TEX:
            artifact = write_latex_source(request, accepted, output_dir)
            manifest = write_render_manifest(
                workspace,
                output_dir,
                request,
                accepted,
                proposal,
                validation,
                RenderBackend.LATEX_SOURCE,
                RenderEngine.LATEX_SOURCE,
                None,
                (artifact,),
            )
            return HostRenderItem(
                format=render_format,
                status="rendered",
                backend=RenderBackend.LATEX_SOURCE,
                artifacts=(artifact,),
                manifest_path=manifest.name,
            )
        case HostRenderFormat.LATEX_PDF:
            return _render_latex_pdf(
                workspace,
                request,
                proposal,
                validation,
                accepted,
                output_dir,
                disable_latex_engines,
            )
        case HostRenderFormat.ALL:
            message = "all must be expanded before rendering"
            raise HostRunError(message)


def _renderer_item(  # noqa: PLR0913 - converts one backend outcome with provenance.
    workspace: Path,
    request: HostRunRequest,
    proposal: StructuredResumeTailoringProposal,
    validation: ValidationStateResult,
    accepted: AcceptedResumeDocument,
    render_format: HostRenderFormat,
    outcome: RendererSuccess | RenderFailure,
    engine: RenderEngine,
) -> HostRenderItem:
    match outcome:
        case RendererSuccess():
            manifest = write_render_manifest(
                workspace,
                run_path(workspace, request.run_id, RENDER_DIR),
                request,
                accepted,
                proposal,
                validation,
                outcome.backend,
                engine,
                engine.value,
                outcome.artifacts,
            )
            return HostRenderItem(
                format=render_format,
                status="rendered",
                backend=outcome.backend,
                artifacts=outcome.artifacts,
                manifest_path=manifest.name,
            )
        case RenderFailure():
            return HostRenderItem(
                format=render_format,
                status="failed",
                backend=outcome.backend,
                code=outcome.code.value,
            )


def _render_latex_pdf(  # noqa: PLR0913
    workspace: Path,
    request: HostRunRequest,
    proposal: StructuredResumeTailoringProposal,
    validation: ValidationStateResult,
    accepted: AcceptedResumeDocument,
    output_dir: Path,
    disable_latex_engines: bool,  # noqa: FBT001 - internal render flag.
) -> HostRenderItem:
    tex_artifact = write_latex_source(request, accepted, output_dir)
    config = (
        LatexCompilerConfig(tectonic_command=(), xelatex_command=())
        if disable_latex_engines
        else None
    )
    result = compile_latex_pdf(output_dir / tex_artifact.path, config=config)
    match result:
        case LatexCompilationSuccess():
            artifact = output_artifact(result.pdf_path, result.pdf_path.name, "application/pdf")
            engine = (
                RenderEngine.TECTONIC
                if result.backend is RenderBackend.LATEX_TECTONIC
                else RenderEngine.XELATEX
            )
            manifest = write_render_manifest(
                workspace,
                output_dir,
                request,
                accepted,
                proposal,
                validation,
                result.backend,
                engine,
                result.engine_version,
                (artifact,),
            )
            return HostRenderItem(
                format=HostRenderFormat.LATEX_PDF,
                status="rendered",
                backend=result.backend,
                artifacts=(artifact,),
                manifest_path=manifest.name,
            )
        case LatexCompilationFailure():
            return HostRenderItem(
                format=HostRenderFormat.LATEX_PDF,
                status="unavailable",
                backend=result.backend,
                code=result.code.value,
            )
