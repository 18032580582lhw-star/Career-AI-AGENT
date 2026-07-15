from __future__ import annotations

from pathlib import Path  # noqa: TC003 - pytest tmp_path uses concrete Path.
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from career_ai.cli import app
from career_ai.tailoring.host_run_store import (
    HostPrepareResult,
    HostValidationResult,
    load_run_context,
)
from career_ai.tailoring.proposal_contracts import (
    ResumeTailoringProposal,
    calculate_proposal_hash,
)
from tests.resume_document_helpers import accepted_bundle, resume_document_draft

if TYPE_CHECKING:
    import pytest


def test_prepare_outputs_machine_readable_host_proposal_package(tmp_path: Path) -> None:
    # Given: immutable source and template files inside a local workspace.
    resume_path = tmp_path / "resume.txt"
    jd_path = tmp_path / "jd.txt"
    template_path = tmp_path / "resume.tex"
    _ = resume_path.write_text("Built Python data workflows.", encoding="utf-8")
    _ = jd_path.write_text("Requires Python data workflow experience.", encoding="utf-8")
    _ = template_path.write_text(
        "\\documentclass{article}\\begin{document}@@RESUME_BODY@@\\end{document}",
        encoding="utf-8",
    )
    runner = CliRunner()

    # When: prepare is run.
    result = runner.invoke(
        app,
        [
            "prepare",
            "--workspace",
            str(tmp_path),
            "--resume-file",
            str(resume_path),
            "--jd-file",
            str(jd_path),
            "--latex-template",
            str(template_path),
            "--language",
            "zh-CN",
            "--output",
            "json",
        ],
    )

    # Then: the response has the run id, schema, source hashes, and next instruction.
    assert result.exit_code == 0
    payload = HostPrepareResult.model_validate_json(result.stdout)
    assert payload.run_id.startswith("run-")
    assert payload.request_artifact.endswith("/request.json")
    assert payload.source_hashes.keys() == {"jd", "resume"}
    assert payload.template_type == "user"
    assert payload.template_hash is not None
    schema_defs_value = payload.proposal_schema["$defs"]
    schema_options_value = payload.proposal_schema["anyOf"]
    assert isinstance(schema_defs_value, dict)
    assert isinstance(schema_options_value, list)
    schema_def_names = {str(name) for name in schema_defs_value}
    schema_refs = {
        ref
        for option in schema_options_value
        if isinstance(option, dict) and isinstance(ref := option.get("$ref"), str)
    }
    assert "HostStructuredProposalPackage" in schema_def_names
    assert "ResumeTailoringProposal" in schema_def_names
    assert "#/$defs/HostStructuredProposalPackage" in schema_refs
    assert "#/$defs/ResumeTailoringProposal" in schema_refs
    assert "validate-draft" in payload.next_machine_instruction


def test_validate_draft_rejects_markdown_code_fence_json(tmp_path: Path) -> None:
    # Given: a prepared run and a proposal wrapped in a Markdown code fence.
    run_id = _prepare_cli_run(tmp_path)
    proposal_file = tmp_path / "proposal.md"
    _ = proposal_file.write_text(
        '```json\n{"run_id":"run-forged"}\n```',
        encoding="utf-8",
    )
    runner = CliRunner()

    # When: validate-draft is run.
    result = runner.invoke(
        app,
        [
            "validate-draft",
            "--workspace",
            str(tmp_path),
            "--run-id",
            run_id,
            "--proposal-file",
            str(proposal_file),
        ],
    )

    # Then: the CLI refuses to guess JSON from fenced Markdown.
    assert result.exit_code != 0
    assert "strict JSON" in result.stdout


def test_tailor_host_mode_does_not_call_provider_api(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given: a prepared run and a host proposal.
    run_id = _prepare_cli_run(tmp_path)
    context = load_run_context(tmp_path, run_id)
    proposal = _accepted_strategy_proposal(context.run_id)
    proposal_file = tmp_path / "proposal.json"
    _ = proposal_file.write_text(proposal.model_dump_json(), encoding="utf-8")

    def forbidden_provider_call() -> None:
        message = "provider should not be built for host proposal mode"
        raise AssertionError(message)

    monkeypatch.setattr("career_ai.cli.build_llm_client", forbidden_provider_call)
    runner = CliRunner()

    # When: host mode tailoring runs.
    result = runner.invoke(
        app,
        [
            "tailor",
            "--workspace",
            str(tmp_path),
            "--run-id",
            run_id,
            "--host-proposal",
            str(proposal_file),
            "--output",
            "json",
        ],
    )

    # Then: the host proposal is locally validated without provider access.
    assert result.exit_code == 0
    payload = HostValidationResult.model_validate_json(result.stdout)
    assert payload.source.value == "host"


def _prepare_cli_run(tmp_path: Path) -> str:
    resume_path = tmp_path / "resume.txt"
    jd_path = tmp_path / "jd.txt"
    _ = resume_path.write_text("Built typed APIs for production workflows.", encoding="utf-8")
    _ = jd_path.write_text("Requires typed API production workflow experience.", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
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
    assert result.exit_code == 0
    return HostPrepareResult.model_validate_json(result.stdout).run_id


def _accepted_strategy_proposal(run_id: str) -> ResumeTailoringProposal:
    _ = resume_document_draft()
    proposal = accepted_bundle()[1]
    payload = proposal.model_dump(mode="json", exclude={"document_structure_hash"})
    payload["run_id"] = run_id
    payload["proposal_hash"] = calculate_proposal_hash(payload)
    return ResumeTailoringProposal.model_validate(payload)
