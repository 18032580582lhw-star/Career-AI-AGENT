"""Typed fixtures for host Skill conformance scenarios."""

from career_ai.tailoring.document_contracts import (
    CandidateIdentity,
    EducationEntry,
    ExperienceEntry,
    ResumeBullet,
    ResumeDocumentDraft,
    ResumeSection,
)


def conformance_draft(fact_id: str, language: str, resume_text: str) -> ResumeDocumentDraft:
    """Build the synthetic structured resume used by the accepted case."""
    bullet = ResumeBullet(text=resume_text, source_fact_ids=(fact_id,))
    return ResumeDocumentDraft(
        identity=CandidateIdentity(
            name="Taylor Example",
            headline="Software Engineer",
            source_fact_ids=(fact_id,),
        ),
        professional_summary=(bullet,),
        skills=(ResumeBullet(text="Python SQL APIs", source_fact_ids=(fact_id,)),),
        experience=(
            ExperienceEntry(
                organization="Example Ltd",
                title="Engineer",
                date_range="2022-2024",
                bullets=(bullet,),
                source_fact_ids=(fact_id,),
            ),
        ),
        projects=(),
        education=(
            EducationEntry(
                institution="Example University",
                credential="BSc Computer Science",
                source_fact_ids=(fact_id,),
            ),
        ),
        links=(),
        output_language=language,
        section_order=(
            ResumeSection.SUMMARY,
            ResumeSection.SKILLS,
            ResumeSection.EXPERIENCE,
            ResumeSection.EDUCATION,
        ),
    )
