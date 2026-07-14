from __future__ import annotations

from typing import Final

import pytest
from pydantic import JsonValue, ValidationError

from career_ai.tailoring.contract_base import SHA256_PATTERN
from career_ai.tailoring.manifest_contracts import (
    OutputArtifact,
    RenderBackend,
    RenderEngine,
    RenderManifest,
    RunManifest,
    RunState,
    TemplateType,
)
from career_ai.tailoring.models import MatchStatus
from career_ai.tailoring.proposal_contracts import (
    ChangeOperation,
    ConfirmationDecision,
    ConfirmationResponse,
    ProposalStrategy,
    ProposedClaim,
    ResumeChange,
    ResumeTailoringProposal,
    TailoringTaskPackage,
    ValidationDecision,
    ValidationFinding,
    ValidationOutcome,
    ValidationSeverity,
    calculate_proposal_hash,
)

HASH_A: Final = "a" * 64
HASH_B: Final = "b" * 64


def _change(*, change_id: str = "change-1") -> dict[str, JsonValue]:
    return {
        "id": change_id,
        "section": "experience",
        "before": "Built APIs.",
        "after": "Built typed APIs for production workflows.",
        "source_fact_ids": ["fact-1"],
        "target_requirement_ids": ["requirement-1"],
        "operation": ChangeOperation.REWRITE,
        "proposed_claim_ids": ["claim-1"],
        "risk_notes": [],
    }


def _claim() -> dict[str, JsonValue]:
    return {
        "id": "claim-1",
        "statement": "Built typed APIs.",
        "source_fact_ids": ["fact-1"],
        "status": "supported",
    }


def _proposal_payload() -> dict[str, JsonValue]:
    return {
        "protocol_version": "1.0",
        "schema_version": 1,
        "run_id": "run-20260711-001",
        "source_hashes": {"resume": HASH_A, "jd": HASH_B},
        "template_hash": None,
        "strategy": ProposalStrategy.ATS_ALIGNED,
        "rewritten_resume": "Engineer\nBuilt typed APIs for production workflows.",
        "changes": [_change()],
        "proposed_claims": [_claim()],
    }


def test_task_package_rejects_duplicate_source_roles() -> None:
    # Given
    payload = {
        "protocol_version": "1.0",
        "schema_version": 1,
        "run_id": "run-20260711-001",
        "sources": [
            {"role": "resume", "artifact_id": "resume-1", "sha256": HASH_A},
            {"role": "resume", "artifact_id": "resume-2", "sha256": HASH_B},
        ],
        "candidate_fact_ids": ["fact-1"],
        "requirement_ids": ["requirement-1"],
        "output_language": "zh-CN",
    }

    # When / Then
    with pytest.raises(ValidationError, match="source roles must be unique"):
        _ = TailoringTaskPackage.model_validate(payload)


def test_proposal_round_trips_and_detects_tampering() -> None:
    # Given
    payload = _proposal_payload()
    payload["proposal_hash"] = calculate_proposal_hash(payload)

    # When
    proposal = ResumeTailoringProposal.model_validate(payload)
    restored = ResumeTailoringProposal.model_validate_json(proposal.model_dump_json())

    # Then
    assert restored == proposal
    tampered = dict(payload)
    tampered["strategy"] = ProposalStrategy.CONSERVATIVE
    with pytest.raises(ValidationError, match="proposal_hash does not match"):
        _ = ResumeTailoringProposal.model_validate(tampered)


@pytest.mark.parametrize("bad_run_id", ["../run", "run with spaces", "RUN"])
def test_protocol_rejects_invalid_run_ids(bad_run_id: str) -> None:
    # Given
    payload = _proposal_payload()
    payload["run_id"] = bad_run_id
    payload["proposal_hash"] = calculate_proposal_hash(payload)

    # When / Then
    with pytest.raises(ValidationError, match="run_id"):
        _ = ResumeTailoringProposal.model_validate(payload)


def test_proposal_rejects_invalid_hash_and_unresolved_claim_reference() -> None:
    # Given
    payload = _proposal_payload()
    change = _change()
    change["proposed_claim_ids"] = ["missing-claim"]
    payload["changes"] = [change]
    payload["proposal_hash"] = "not-a-hash"

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        _ = ResumeTailoringProposal.model_validate(payload)
    assert SHA256_PATTERN in str(exc_info.value) or "sha256" in str(exc_info.value).lower()


def test_proposal_rejects_duplicate_change_ids() -> None:
    # Given
    payload = _proposal_payload()
    payload["changes"] = [_change(), _change()]
    payload["proposal_hash"] = calculate_proposal_hash(payload)

    # When / Then
    with pytest.raises(ValidationError, match="change ids must be unique"):
        _ = ResumeTailoringProposal.model_validate(payload)


def test_validation_decision_rejects_accepted_error_findings() -> None:
    # Given
    finding = ValidationFinding(
        id="finding-1",
        code="unsupported_metric",
        severity=ValidationSeverity.ERROR,
        message="A metric has no evidence.",
        change_id="change-1",
    )

    # When / Then
    with pytest.raises(ValidationError, match="accepted decisions cannot contain errors"):
        _ = ValidationDecision(
            protocol_version="1.0",
            schema_version=1,
            run_id="run-20260711-001",
            proposal_hash=HASH_A,
            outcome=ValidationOutcome.ACCEPTED,
            findings=(finding,),
            safety_passed=True,
            adequacy_passed=True,
            validation_hash=HASH_B,
        )


def test_confirmation_requires_statement_only_when_confirmed() -> None:
    # Given / When
    confirmed = ConfirmationResponse(
        protocol_version="1.0",
        schema_version=1,
        run_id="run-20260711-001",
        proposal_hash=HASH_A,
        finding_id="finding-1",
        decision=ConfirmationDecision.CONFIRM,
        confirmed_statement="Led the migration.",
    )

    # Then
    assert confirmed.confirmed_statement == "Led the migration."
    with pytest.raises(ValidationError, match="confirmed_statement is required"):
        _ = ConfirmationResponse(
            protocol_version="1.0",
            schema_version=1,
            run_id="run-20260711-001",
            proposal_hash=HASH_A,
            finding_id="finding-1",
            decision=ConfirmationDecision.CONFIRM,
        )


def test_run_manifest_enforces_state_artifact_consistency() -> None:
    # Given / When / Then
    with pytest.raises(ValidationError, match="accepted state requires"):
        _ = RunManifest(
            workspace_schema_version=1,
            protocol_version="1.0",
            schema_version=1,
            run_id="run-20260711-001",
            state=RunState.ACCEPTED,
            source_hashes={"resume": HASH_A, "jd": HASH_B},
            request_hash=HASH_A,
            proposal_hash=None,
            validation_hash=None,
            accepted_document_hash=None,
            template_hash=None,
        )


def test_render_manifest_records_specific_backend_and_engine_contract() -> None:
    # Given
    output = OutputArtifact(path="resume.pdf", sha256=HASH_A, media_type="application/pdf")

    # When
    manifest = RenderManifest(
        protocol_version="1.0",
        schema_version=1,
        run_id="run-20260711-001",
        proposal_hash=HASH_A,
        validation_hash=HASH_B,
        accepted_document_hash=HASH_A,
        template_type=TemplateType.SYSTEM,
        template_hash=HASH_B,
        backend=RenderBackend.LATEX_TECTONIC,
        engine=RenderEngine.TECTONIC,
        engine_version="tectonic 0.15",
        font_bundle_version="noto-2026-01",
        outputs=(output,),
        page_size="A4",
        language="zh-CN",
    )

    # Then
    assert manifest.backend is RenderBackend.LATEX_TECTONIC
    payload = manifest.model_dump(mode="json")
    payload["engine_version"] = None
    with pytest.raises(ValidationError, match="engine_version"):
        _ = RenderManifest.model_validate(payload)


def test_contracts_forbid_extra_fields_and_invalid_enum_values() -> None:
    # Given
    payload = _proposal_payload()
    payload["strategy"] = "inventive"
    payload["proposal_hash"] = calculate_proposal_hash(payload)
    payload["unexpected"] = True

    # When / Then
    with pytest.raises(ValidationError):
        _ = ResumeTailoringProposal.model_validate(payload)


def test_proposed_claim_supported_status_requires_source_facts() -> None:
    # Given / When / Then
    with pytest.raises(ValidationError, match="supported claims require source facts"):
        _ = ProposedClaim(
            id="claim-1",
            statement="Knows Kubernetes.",
            source_fact_ids=(),
            status=MatchStatus.SUPPORTED,
        )


def test_resume_change_requires_distinct_fact_and_requirement_ids() -> None:
    # Given / When / Then
    with pytest.raises(ValidationError, match="source_fact_ids must be unique"):
        _ = ResumeChange(
            id="change-1",
            section="experience",
            before="Built APIs.",
            after="Built typed APIs.",
            source_fact_ids=("fact-1", "fact-1"),
            target_requirement_ids=("requirement-1",),
            operation=ChangeOperation.REWRITE,
        )
