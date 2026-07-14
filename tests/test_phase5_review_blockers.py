from __future__ import annotations

import pytest
from pydantic import ValidationError

from career_ai.rendering.ats_normalization import normalize_ats_text
from career_ai.tailoring.document_acceptance import (
    DocumentAcceptanceError,
    DocumentAcceptanceErrorCode,
    accept_resume_document,
)
from career_ai.tailoring.document_contracts import (
    CandidateIdentity,
    ResumeDocumentDraft,
    ResumeLink,
)
from career_ai.tailoring.manifest_contracts import RunState
from career_ai.tailoring.proposal_contracts import (
    ValidationFinding,
    ValidationSeverity,
)
from career_ai.tailoring.state_machine import calculate_validation_hash
from tests.resume_document_helpers import accepted_bundle, resume_document_draft


def test_draft_requires_all_core_resume_sections() -> None:
    payload = resume_document_draft().model_dump(mode="json")
    payload["professional_summary"] = []

    with pytest.raises(ValidationError, match="required core sections"):
        _ = ResumeDocumentDraft.model_validate(payload)


def test_acceptance_constructs_renderer_only_contract_and_rejects_forged_hash() -> None:
    draft, proposal, validation = accepted_bundle()
    forged = validation.model_copy(
        update={"decision": validation.decision.model_copy(update={"validation_hash": "f" * 64})},
    )

    with pytest.raises(DocumentAcceptanceError) as exc_info:
        _ = accept_resume_document(draft, proposal, forged, ())

    assert exc_info.value.code is DocumentAcceptanceErrorCode.BINDING_MISMATCH


def test_acceptance_rejects_forged_pass_flags() -> None:
    draft, proposal, validation = accepted_bundle()
    forged = validation.model_copy(
        update={
            "decision": validation.decision.model_copy(update={"safety_passed": False}),
            "state": RunState.ACCEPTED,
            "render_allowed": True,
        },
    )

    with pytest.raises(DocumentAcceptanceError) as exc_info:
        _ = accept_resume_document(draft, proposal, forged, ())

    assert exc_info.value.code is DocumentAcceptanceErrorCode.NOT_ACCEPTED


def test_acceptance_rejects_rehashed_accepted_warning_state() -> None:
    draft, proposal, validation = accepted_bundle()
    warning = ValidationFinding(
        id="finding-confirm",
        code="inference_requires_confirmation",
        severity=ValidationSeverity.WARNING,
        message="Confirmation required",
        confirmation_prompt="Confirm this inference",
    )
    decision = validation.decision.model_copy(update={"findings": (warning,)})
    decision = decision.model_copy(
        update={
            "validation_hash": calculate_validation_hash(
                proposal,
                decision.outcome,
                decision.findings,
                safety_passed=decision.safety_passed,
                adequacy_passed=decision.adequacy_passed,
            ),
        },
    )
    forged = validation.model_copy(update={"decision": decision})

    with pytest.raises(DocumentAcceptanceError) as exc_info:
        _ = accept_resume_document(draft, proposal, forged, ())

    assert exc_info.value.code is DocumentAcceptanceErrorCode.NOT_ACCEPTED


def test_acceptance_rejects_rehashed_noncanonical_finding_order() -> None:
    draft, proposal, validation = accepted_bundle()
    findings = tuple(
        ValidationFinding(
            id=finding_id,
            code="informational",
            severity=ValidationSeverity.INFO,
            message="Informational finding",
        )
        for finding_id in ("finding-z", "finding-a")
    )
    decision = validation.decision.model_copy(update={"findings": findings})
    decision = decision.model_copy(
        update={
            "validation_hash": calculate_validation_hash(
                proposal,
                decision.outcome,
                decision.findings,
                safety_passed=decision.safety_passed,
                adequacy_passed=decision.adequacy_passed,
            ),
        },
    )
    forged = validation.model_copy(update={"decision": decision})

    with pytest.raises(DocumentAcceptanceError) as exc_info:
        _ = accept_resume_document(draft, proposal, forged, ())

    assert exc_info.value.code is DocumentAcceptanceErrorCode.NOT_ACCEPTED


def test_malformed_ipv6_url_is_rejected_at_contract_boundary() -> None:
    with pytest.raises(ValidationError, match="valid HTTP or HTTPS URL"):
        _ = ResumeLink(
            label="Portfolio",
            url="https://[broken",
            source_fact_ids=("fact-link",),
        )


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com:bad",
        "http://exa mple.com",
        "http://.",
        "https://example.com/a b",
        "https:///missing",
    ],
)
def test_invalid_http_url_is_rejected_at_contract_boundary(url: str) -> None:
    with pytest.raises(ValidationError, match="valid HTTP or HTTPS URL"):
        _ = ResumeLink(
            label="Portfolio",
            url=url,
            source_fact_ids=("fact-link",),
        )


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com:notaport/path",
        "https://example.com/a b",
        "http://[::1",
    ],
)
def test_invalid_contact_url_is_rejected_at_identity_boundary(url: str) -> None:
    with pytest.raises(ValidationError, match="valid HTTP or HTTPS URL"):
        _ = CandidateIdentity(
            name="Ada Example",
            contact_lines=(url,),
            source_fact_ids=("fact-identity",),
        )


def test_ats_preserves_joiners_but_removes_directional_marks() -> None:
    assert normalize_ats_text("👩\u200d💻") == "👩\u200d💻"
    assert normalize_ats_text("क्\u200dष") == "क्\u200dष"
    assert normalize_ats_text("A\u061c\u200e\u200fB") == "AB"
