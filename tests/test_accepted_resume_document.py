from __future__ import annotations

import pytest
from pydantic import ValidationError

from career_ai.tailoring.document_contracts import (
    AcceptedResumeDocument,
    CandidateIdentity,
    ResumeSection,
)
from tests.resume_document_helpers import accepted_resume_document


def test_accepted_resume_document_round_trips_without_losing_provenance() -> None:
    # Given
    document = accepted_resume_document()

    # When
    restored = AcceptedResumeDocument.model_validate_json(document.model_dump_json())

    # Then
    assert restored == document
    assert restored.experience[0].bullets[0].source_fact_ids == ("fact-1",)


def test_accepted_document_rejects_populated_section_missing_from_order() -> None:
    # Given
    payload = accepted_resume_document().model_dump(mode="json")
    payload["section_order"] = [
        section.value
        for section in ResumeSection
        if section is not ResumeSection.EXPERIENCE
    ]

    # When / Then
    with pytest.raises(ValidationError, match="populated sections"):
        _ = AcceptedResumeDocument.model_validate(payload)


def test_accepted_document_rejects_empty_section_present_in_order() -> None:
    # Given
    payload = accepted_resume_document().model_dump(mode="json")
    payload["projects"] = []

    # When / Then
    with pytest.raises(ValidationError, match="populated sections"):
        _ = AcceptedResumeDocument.model_validate(payload)


def test_document_rejects_noncanonical_section_order() -> None:
    payload = accepted_resume_document().model_dump(mode="json")
    payload["section_order"][0:2] = [
        ResumeSection.SKILLS.value,
        ResumeSection.SUMMARY.value,
    ]

    with pytest.raises(ValidationError, match="canonical order"):
        _ = AcceptedResumeDocument.model_validate(payload)


def test_candidate_identity_requires_factual_provenance() -> None:
    # Given / When / Then
    with pytest.raises(ValidationError, match="source_fact_ids"):
        _ = CandidateIdentity.model_validate({"name": "Ada Example"})
