import pytest
from pydantic import ValidationError

from career_ai.tailoring.candidate_extractor import (
    create_confirmed_candidate_fact,
    extract_candidate_facts,
)
from career_ai.tailoring.extraction_types import CandidateFactKind, ResumeFactSource
from career_ai.tailoring.models import (
    EvidenceProvenance,
    SourceArtifactId,
    UserConfirmationProvenance,
)


def _resume_source() -> ResumeFactSource:
    return ResumeFactSource(artifact_id=SourceArtifactId("resume-source"))


def test_extract_candidate_facts_links_each_fact_to_resume_evidence() -> None:
    # Given
    resume = (
        "Senior Data Engineer | Acme Corp | 2021-2024\n"
        "- Built Python pipelines that reduced processing time by 35%."
    )

    # When
    extraction = extract_candidate_facts(resume, _resume_source())

    # Then
    span_ids = {span.id for span in extraction.evidence_spans}
    assert extraction.facts
    assert all(
        isinstance(item.fact.provenance, EvidenceProvenance)
        and set(item.fact.provenance.evidence_span_ids) <= span_ids
        for item in extraction.facts
    )


def test_extract_candidate_facts_covers_structured_resume_fact_kinds() -> None:
    # Given
    resume = (
        "Senior Data Engineer | Acme Corp | 2021-2024\n"
        "- Built Python pipelines that reduced processing time by 35%."
    )

    # When
    extraction = extract_candidate_facts(resume, _resume_source())

    # Then
    kinds = {item.kind for item in extraction.facts}
    assert {
        CandidateFactKind.BULLET,
        CandidateFactKind.DATE,
        CandidateFactKind.NUMBER,
        CandidateFactKind.TECHNOLOGY,
        CandidateFactKind.ORGANIZATION,
        CandidateFactKind.ROLE,
        CandidateFactKind.RESULT,
    } <= kinds


def test_extract_candidate_facts_is_stable_and_uses_resume_text_only() -> None:
    # Given
    resume = "工程师 | 示例科技有限公司 | 2022-至今\n- 使用 Python 将处理时间缩短 20%。"

    # When
    first = extract_candidate_facts(resume, _resume_source())
    second = extract_candidate_facts(resume, _resume_source())

    # Then
    assert first == second
    assert "Kubernetes" not in {item.fact.statement for item in first.facts}


def test_jd_source_role_is_rejected_before_candidate_fact_extraction() -> None:
    with pytest.raises(ValidationError):
        _ = ResumeFactSource.model_validate(
            {"role": "job_description", "artifact_id": "jd-source"}
        )


def test_user_confirmed_fact_has_explicit_stable_provenance() -> None:
    first = create_confirmed_candidate_fact(
        "可以常驻香港",
        confirmation="用户明确确认可以常驻香港",
    )
    second = create_confirmed_candidate_fact(
        "可以常驻香港",
        confirmation="用户明确确认可以常驻香港",
    )

    assert first == second
    assert isinstance(first.provenance, UserConfirmationProvenance)
    assert first.provenance.confirmation == "用户明确确认可以常驻香港"
