from hashlib import sha256
from pathlib import Path

from career_ai.application.tailoring_service import TailoringApplicationService
from career_ai.rendering.latex import LatexTemplateProfile
from career_ai.tailoring.document_contracts import StructuredResumeTailoringProposal
from career_ai.tailoring.host_run_store import HostPrepareResult, HostRenderFormat
from career_ai.tailoring.host_run_validation import save_accepted_run
from career_ai.tailoring.manifest_contracts import RunState
from career_ai.tailoring.proposal_contracts import (
    ValidationDecision,
    ValidationOutcome,
    calculate_proposal_hash,
)
from career_ai.tailoring.state_machine import ValidationStateResult, calculate_validation_hash
from tests.resume_document_helpers import accepted_bundle, accepted_document_candidate_facts


def test_application_service_prepares_and_inspects_latex_template(tmp_path: Path) -> None:
    # Given: a shared application service and user-provided sources.
    service = TailoringApplicationService(workspace=tmp_path)
    resume = tmp_path / "resume.txt"
    jd = tmp_path / "jd.txt"
    template = tmp_path / "resume.tex"
    _ = resume.write_text("Built Python data workflows.", encoding="utf-8")
    _ = jd.write_text("Requires Python data workflow experience.", encoding="utf-8")
    _ = template.write_text(
        "\\documentclass{article}\\begin{document}\\section{Summary}Old\\end{document}",
        encoding="utf-8",
    )

    # When: the service prepares a run and inspects the template.
    prepared = service.prepare(
        resume_file=resume,
        jd_file=jd,
        latex_template=template,
        language="zh-CN",
    )
    profile = service.inspect_latex_template(template)

    # Then: callers receive the same typed contracts used by CLI and Skill paths.
    assert isinstance(prepared, HostPrepareResult)
    assert prepared.template_type.value == "user"
    assert isinstance(profile, LatexTemplateProfile)
    assert profile.requires_mapping_confirmation is True


def test_application_service_renders_accepted_run_with_renderer_contracts(
    tmp_path: Path,
) -> None:
    # Given: an accepted host run persisted in the workspace.
    run_id = _save_accepted_run(tmp_path)
    service = TailoringApplicationService(workspace=tmp_path)

    # When: the shared render service is asked for all formats without LaTeX engines.
    result = service.render(
        run_id=run_id,
        render_format=HostRenderFormat.ALL,
        disable_latex_engines=True,
    )

    # Then: .tex remains renderable while LaTeX PDF reports the missing engine.
    statuses = {item.format: item.status for item in result.results}
    assert statuses[HostRenderFormat.TEX] == "rendered"
    assert statuses[HostRenderFormat.LATEX_PDF] == "unavailable"


def _save_accepted_run(tmp_path: Path) -> str:
    template_path = tmp_path / "resume.tex"
    _ = template_path.write_text(
        "\\documentclass{article}\\begin{document}@@RESUME_BODY@@\\end{document}",
        encoding="utf-8",
    )
    draft, proposal, _validation = accepted_bundle()
    resume_text = "Built typed APIs for production workflows."
    jd_text = "Requires typed API production workflow experience."
    proposal_payload = proposal.model_dump(mode="json")
    template_hash = sha256(template_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    proposal_payload["source_hashes"] = {
        "resume": sha256(resume_text.encode("utf-8")).hexdigest(),
        "jd": sha256(jd_text.encode("utf-8")).hexdigest(),
    }
    proposal_payload["template_hash"] = template_hash
    proposal_payload["proposal_hash"] = calculate_proposal_hash(proposal_payload)
    proposal = StructuredResumeTailoringProposal.model_validate(proposal_payload)
    validation_hash = calculate_validation_hash(
        proposal,
        ValidationOutcome.ACCEPTED,
        (),
        safety_passed=True,
        adequacy_passed=True,
    )
    validation = ValidationStateResult(
        state=RunState.ACCEPTED,
        decision=ValidationDecision(
            run_id=proposal.run_id,
            proposal_hash=proposal.proposal_hash,
            outcome=ValidationOutcome.ACCEPTED,
            findings=(),
            safety_passed=True,
            adequacy_passed=True,
            validation_hash=validation_hash,
        ),
        repair_attempts=0,
        repair_allowed=False,
        render_allowed=True,
    )
    save_accepted_run(
        tmp_path,
        request_payload={
            "resume_text": resume_text,
            "jd_text": jd_text,
            "template_path": str(template_path),
            "template_source": template_path.read_text(encoding="utf-8"),
            "output_language": "zh-CN",
        },
        draft=draft,
        proposal=proposal,
        validation=validation,
        candidate_facts=accepted_document_candidate_facts(),
    )
    return proposal.run_id
