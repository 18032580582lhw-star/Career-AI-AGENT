from __future__ import annotations

from typing import TYPE_CHECKING

from career_ai.rendering.ats_normalization import normalize_accepted_resume_document
from career_ai.tailoring.document_contracts import (
    AcceptedResumeDocument,
    CandidateIdentity,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    ResumeBullet,
    ResumeDocumentDraft,
    ResumeLink,
    ResumeSection,
    StructuredResumeTailoringProposal,
)
from career_ai.tailoring.document_text import (
    accepted_resume_core_text,
    resume_document_structure_hash,
)
from career_ai.tailoring.manifest_contracts import RunState
from career_ai.tailoring.models import (
    CandidateFact,
    CandidateFactId,
    EvidenceProvenance,
    EvidenceSpanId,
)
from career_ai.tailoring.proposal_contracts import (
    ProposalStrategy,
    ValidationDecision,
    ValidationOutcome,
    calculate_proposal_hash,
)
from career_ai.tailoring.state_machine import (
    ValidationStateResult,
    calculate_validation_hash,
)

if TYPE_CHECKING:
    from pydantic import JsonValue


def resume_document_draft() -> ResumeDocumentDraft:
    """Build one complete untrusted structured resume for Phase 5 tests."""
    payload = accepted_resume_document().model_dump(
        mode="python",
        exclude={"run_id", "proposal_hash", "validation_hash"},
    )
    return ResumeDocumentDraft.model_validate(payload)


def accepted_resume_document(
    *,
    proposal_hash: str = "a" * 64,
    validation_hash: str = "b" * 64,
) -> AcceptedResumeDocument:
    bullet = ResumeBullet(
        text="Built typed APIs for 中文 production workflows.",
        source_fact_ids=("fact-1",),
    )
    return AcceptedResumeDocument(
        run_id="run-20260713-001",
        proposal_hash=proposal_hash,
        validation_hash=validation_hash,
        identity=CandidateIdentity(
            name="Ada Example",
            headline="Software Engineer",
            contact_lines=("Ada@Example.COM", "HTTPS://Example.COM/Ada"),
            source_fact_ids=("fact-identity",),
        ),
        professional_summary=(bullet,),
        skills=(bullet,),
        experience=(
            ExperienceEntry(
                organization="Example Ltd",
                title="Engineer",
                date_range="2022-2024",
                bullets=(bullet,),
                source_fact_ids=("fact-experience",),
            ),
        ),
        projects=(
            ProjectEntry(
                name="Typed Platform",
                bullets=(bullet,),
                source_fact_ids=("fact-project",),
            ),
        ),
        education=(
            EducationEntry(
                institution="Example University",
                credential="BSc Computer Science",
                details=(bullet,),
                source_fact_ids=("fact-education",),
            ),
        ),
        links=(
            ResumeLink(
                label="Portfolio",
                url="https://Example.COM/Ada",
                source_fact_ids=("fact-link",),
            ),
        ),
        output_language="zh-CN",
        section_order=(
            ResumeSection.SUMMARY,
            ResumeSection.SKILLS,
            ResumeSection.EXPERIENCE,
            ResumeSection.PROJECTS,
            ResumeSection.EDUCATION,
            ResumeSection.LINKS,
        ),
    )


def accepted_document_candidate_facts() -> tuple[CandidateFact, ...]:
    statements = (
        (
            "fact-identity",
            "Ada Example Software Engineer Ada@Example.COM HTTPS://Example.COM/Ada",
        ),
        ("fact-1", "Built typed APIs for 中文 production workflows."),
        ("fact-experience", "Example Ltd Engineer 2022-2024"),
        ("fact-project", "Typed Platform"),
        ("fact-education", "Example University BSc Computer Science"),
        ("fact-link", "Portfolio https://Example.COM/Ada"),
    )
    return tuple(
        CandidateFact(
            id=CandidateFactId(fact_id),
            statement=statement,
            provenance=EvidenceProvenance(
                evidence_span_ids=(EvidenceSpanId(f"span-{index}"),),
            ),
        )
        for index, (fact_id, statement) in enumerate(statements, start=1)
    )


def accepted_bundle() -> tuple[
    ResumeDocumentDraft,
    StructuredResumeTailoringProposal,
    ValidationStateResult,
]:
    """Build a cryptographically consistent draft/proposal/validation bundle."""
    draft = resume_document_draft()
    document = accepted_resume_document()
    normalized_document = normalize_accepted_resume_document(document)
    proposal_payload: dict[str, JsonValue] = {
        "protocol_version": "1.0",
        "schema_version": 1,
        "run_id": document.run_id,
        "source_hashes": {"resume": "c" * 64, "jd": "d" * 64},
        "template_hash": None,
        "strategy": ProposalStrategy.ATS_ALIGNED.value,
        "rewritten_resume": accepted_resume_core_text(normalized_document),
        "document_structure_hash": resume_document_structure_hash(normalized_document),
        "changes": [],
        "proposed_claims": [],
    }
    proposal_payload["proposal_hash"] = calculate_proposal_hash(proposal_payload)
    proposal = StructuredResumeTailoringProposal.model_validate(proposal_payload)
    validation_hash = calculate_validation_hash(
        proposal,
        ValidationOutcome.ACCEPTED,
        (),
        safety_passed=True,
        adequacy_passed=True,
    )
    decision = ValidationDecision(
        run_id=proposal.run_id,
        proposal_hash=proposal.proposal_hash,
        outcome=ValidationOutcome.ACCEPTED,
        findings=(),
        safety_passed=True,
        adequacy_passed=True,
        validation_hash=validation_hash,
    )
    validation = ValidationStateResult(
        state=RunState.ACCEPTED,
        decision=decision,
        repair_attempts=0,
        repair_allowed=False,
        render_allowed=True,
    )
    return draft, proposal, validation


def accepted_resume_from_draft(
    draft: ResumeDocumentDraft,
    run_id: str,
    proposal_hash: str,
    validation_hash: str,
) -> AcceptedResumeDocument:
    """Build a normalized accepted-shape projection for proposal setup only."""
    payload = draft.model_dump(mode="python")
    payload.update(
        run_id=run_id,
        proposal_hash=proposal_hash,
        validation_hash=validation_hash,
    )
    document = AcceptedResumeDocument.model_validate(payload)
    return normalize_accepted_resume_document(document)
