from __future__ import annotations

from hashlib import sha256
from pathlib import Path  # noqa: TC003 - pytest tmp_path uses concrete Path.

from typer.testing import CliRunner

from career_ai.cli import app
from career_ai.tailoring.document_contracts import StructuredResumeTailoringProposal
from career_ai.tailoring.host_run_store import (
    HostRenderFormat,
    HostRenderResult,
    save_accepted_run,
)
from career_ai.tailoring.manifest_contracts import RunState
from career_ai.tailoring.proposal_contracts import (
    ValidationDecision,
    ValidationOutcome,
    calculate_proposal_hash,
)
from career_ai.tailoring.state_machine import ValidationStateResult, calculate_validation_hash
from tests.resume_document_helpers import (
    accepted_bundle,
    accepted_document_candidate_facts,
)


def test_render_before_validation_returns_stable_cli_error(tmp_path: Path) -> None:
    # Given: a prepared run without an accepted proposal.
    resume_path = tmp_path / "resume.txt"
    jd_path = tmp_path / "jd.txt"
    _ = resume_path.write_text("Built Python dashboards.", encoding="utf-8")
    _ = jd_path.write_text("Role: Analyst. Requires Python dashboards.", encoding="utf-8")
    runner = CliRunner()
    prepared = runner.invoke(
        app,
        [
            "prepare",
            "--workspace",
            str(tmp_path),
            "--resume-file",
            str(resume_path),
            "--jd-file",
            str(jd_path),
            "--output",
            "json",
        ],
    )
    run_id = prepared.stdout.split('"run_id": "')[1].split('"', maxsplit=1)[0]

    # When: render is called before validation has produced render-ready artifacts.
    result = runner.invoke(
        app,
        [
            "render",
            "--workspace",
            str(tmp_path),
            "--run-id",
            run_id,
            "--format",
            HostRenderFormat.TEX.value,
        ],
    )

    # Then: the CLI returns a stable user-facing error without leaking a traceback.
    assert result.exit_code == 2
    assert "not render-ready" in result.stdout
    assert "Traceback" not in result.stdout


def test_render_marks_run_stale_when_bound_template_changes(tmp_path: Path) -> None:
    # Given: an accepted run bound to a concrete user template file.
    run_id = _save_accepted_cli_run(tmp_path)
    template_path = tmp_path / "resume.tex"
    _ = template_path.write_text(
        "\\documentclass{article}\\begin{document}tampered\\end{document}",
        encoding="utf-8",
    )
    runner = CliRunner()

    # When: render attempts to use the old validation after template mutation.
    result = runner.invoke(
        app,
        [
            "render",
            "--workspace",
            str(tmp_path),
            "--run-id",
            run_id,
            "--format",
            HostRenderFormat.TEX.value,
        ],
    )

    # Then: no artifact is rendered from stale validation.
    assert result.exit_code == 15
    assert "stale" in result.stdout


def test_render_all_keeps_tex_available_when_latex_engine_is_missing(
    tmp_path: Path,
) -> None:
    # Given: an accepted run and disabled LaTeX engine discovery.
    run_id = _save_accepted_cli_run(tmp_path)
    runner = CliRunner()

    # When: all renderers are requested.
    result = runner.invoke(
        app,
        [
            "render",
            "--workspace",
            str(tmp_path),
            "--run-id",
            run_id,
            "--format",
            HostRenderFormat.ALL.value,
            "--disable-latex-engines",
            "--output",
            "json",
        ],
    )

    # Then: DOCX and .tex still render while latex-pdf reports its missing engine.
    assert result.exit_code == 0
    payload = HostRenderResult.model_validate_json(result.stdout)
    formats = {item.format.value for item in payload.results}
    assert {"docx", "pdf", "tex", "latex-pdf"} <= formats
    tex_result = next(item for item in payload.results if item.format is HostRenderFormat.TEX)
    latex_pdf_result = next(
        item
        for item in payload.results
        if item.format is HostRenderFormat.LATEX_PDF
    )
    assert tex_result.status == "rendered"
    assert latex_pdf_result.status == "unavailable"
    assert latex_pdf_result.code == "latex_no_engine"


def _save_accepted_cli_run(tmp_path: Path) -> str:
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
    request_payload = {
        "resume_text": resume_text,
        "jd_text": jd_text,
        "template_path": str(template_path),
        "template_source": template_path.read_text(encoding="utf-8"),
        "output_language": "zh-CN",
    }
    save_accepted_run(
        tmp_path,
        request_payload=request_payload,
        draft=draft,
        proposal=proposal,
        validation=validation,
        candidate_facts=accepted_document_candidate_facts(),
    )
    return proposal.run_id
