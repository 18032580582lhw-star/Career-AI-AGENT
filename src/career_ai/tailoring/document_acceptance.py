"""Trusted construction gate for renderer-ready accepted resume documents."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import TYPE_CHECKING, override

from pydantic import JsonValue, TypeAdapter, ValidationError

from career_ai.tailoring.ats_normalization import (
    DEFAULT_ATS_OPTIONS,
    normalize_accepted_resume_document,
    normalize_ats_text,
)
from career_ai.tailoring.document_contracts import (
    AcceptedResumeDocument,
    ResumeDocumentDraft,
    StructuredResumeTailoringProposal,
)
from career_ai.tailoring.document_text import (
    accepted_resume_core_text,
    resume_document_structure_hash,
)
from career_ai.tailoring.manifest_contracts import RunState
from career_ai.tailoring.proposal_contracts import ValidationOutcome, calculate_proposal_hash
from career_ai.tailoring.safety_rules import (
    has_prompt_injection_content,
    text_is_covered,
)
from career_ai.tailoring.state_machine import calculate_validation_hash

if TYPE_CHECKING:
    from career_ai.tailoring.document_contracts import (
        ResumeBullet,
    )
    from career_ai.tailoring.models import CandidateFact
    from career_ai.tailoring.state_machine import ValidationStateResult

_JSON_OBJECT_ADAPTER = TypeAdapter(dict[str, JsonValue])


@unique
class DocumentAcceptanceErrorCode(StrEnum):
    """Stable failures raised before a document may enter a renderer."""

    NOT_ACCEPTED = "document_not_accepted"
    BINDING_MISMATCH = "document_binding_mismatch"
    NORMALIZATION_FAILED = "document_normalization_failed"
    DUPLICATE_SOURCE_FACT = "document_duplicate_source_fact"
    UNKNOWN_SOURCE_FACT = "document_unknown_source_fact"
    UNSUPPORTED_TEXT = "document_unsupported_text"
    PROPOSAL_CONTENT_MISMATCH = "document_proposal_content_mismatch"
    PROMPT_INJECTION_CONTENT = "document_prompt_injection_content"


@dataclass(frozen=True, slots=True)
class DocumentAcceptanceError(Exception):
    """Typed document rejection with an optional failing reference."""

    code: DocumentAcceptanceErrorCode
    reference: str | None = None

    @override
    def __str__(self) -> str:
        if self.reference is None:
            return self.code.value
        return f"{self.code.value}: {self.reference}"


@dataclass(frozen=True, slots=True)
class _ProvenancedStatement:
    text: str
    source_fact_ids: tuple[str, ...]


def accept_resume_document(
    draft: ResumeDocumentDraft,
    proposal: StructuredResumeTailoringProposal,
    validation: ValidationStateResult,
    candidate_facts: tuple[CandidateFact, ...],
) -> AcceptedResumeDocument:
    """Authorize, normalize, and bind one structured document to accepted evidence."""
    _require_accepted(validation)
    proposal_payload = _JSON_OBJECT_ADAPTER.validate_python(
        proposal.model_dump(mode="json", exclude={"proposal_hash"}),
    )
    if (
        calculate_proposal_hash(proposal_payload) != proposal.proposal_hash
        or proposal.run_id != validation.decision.run_id
        or proposal.proposal_hash != validation.decision.proposal_hash
        or validation.decision.validation_hash
        != calculate_validation_hash(
            proposal,
            validation.decision.outcome,
            validation.decision.findings,
            safety_passed=validation.decision.safety_passed,
            adequacy_passed=validation.decision.adequacy_passed,
        )
    ):
        raise DocumentAcceptanceError(DocumentAcceptanceErrorCode.BINDING_MISMATCH)
    document = _bind_document(draft, proposal, validation)
    try:
        normalized = normalize_accepted_resume_document(
            document,
            options=DEFAULT_ATS_OPTIONS,
        )
    except ValidationError as error:
        raise DocumentAcceptanceError(
            DocumentAcceptanceErrorCode.NORMALIZATION_FAILED,
        ) from error
    facts_by_id = {str(fact.id): fact for fact in candidate_facts}
    if len(facts_by_id) != len(candidate_facts):
        raise DocumentAcceptanceError(DocumentAcceptanceErrorCode.DUPLICATE_SOURCE_FACT)
    for statement in _provenanced_statements(normalized):
        referenced = tuple(
            facts_by_id[fact_id]
            for fact_id in statement.source_fact_ids
            if fact_id in facts_by_id
        )
        if len(referenced) != len(statement.source_fact_ids):
            unknown = next(
                fact_id
                for fact_id in statement.source_fact_ids
                if fact_id not in facts_by_id
            )
            raise DocumentAcceptanceError(
                DocumentAcceptanceErrorCode.UNKNOWN_SOURCE_FACT,
                unknown,
            )
        source_texts = tuple(
            normalize_ats_text(fact.statement, options=DEFAULT_ATS_OPTIONS)
            for fact in referenced
        )
        if not text_is_covered(statement.text, source_texts):
            raise DocumentAcceptanceError(
                DocumentAcceptanceErrorCode.UNSUPPORTED_TEXT,
                ",".join(statement.source_fact_ids),
            )
    if resume_document_structure_hash(normalized) != proposal.document_structure_hash:
        raise DocumentAcceptanceError(
            DocumentAcceptanceErrorCode.PROPOSAL_CONTENT_MISMATCH,
        )
    document_text = accepted_resume_core_text(normalized)
    normalized_document_text = normalize_ats_text(
        document_text,
        options=DEFAULT_ATS_OPTIONS,
    )
    proposal_text = normalize_ats_text(
        proposal.rewritten_resume,
        options=DEFAULT_ATS_OPTIONS,
    )
    if has_prompt_injection_content(document_text):
        raise DocumentAcceptanceError(
            DocumentAcceptanceErrorCode.PROMPT_INJECTION_CONTENT,
        )
    if normalized_document_text != proposal_text:
        raise DocumentAcceptanceError(
            DocumentAcceptanceErrorCode.PROPOSAL_CONTENT_MISMATCH,
        )
    return normalized


def _require_accepted(validation: ValidationStateResult) -> None:
    finding_ids = tuple(finding.id for finding in validation.decision.findings)
    if (
        validation.state is not RunState.ACCEPTED
        or validation.decision.outcome is not ValidationOutcome.ACCEPTED
        or not validation.render_allowed
        or validation.repair_allowed
        or not validation.decision.safety_passed
        or not validation.decision.adequacy_passed
        or bool(finding_ids)
    ):
        raise DocumentAcceptanceError(DocumentAcceptanceErrorCode.NOT_ACCEPTED)


def _bind_document(
    draft: ResumeDocumentDraft,
    proposal: StructuredResumeTailoringProposal,
    validation: ValidationStateResult,
) -> AcceptedResumeDocument:
    return AcceptedResumeDocument(
        protocol_version=draft.protocol_version,
        schema_version=draft.schema_version,
        run_id=proposal.run_id,
        proposal_hash=proposal.proposal_hash,
        validation_hash=validation.decision.validation_hash,
        identity=draft.identity,
        professional_summary=draft.professional_summary,
        skills=draft.skills,
        experience=draft.experience,
        projects=draft.projects,
        education=draft.education,
        links=draft.links,
        output_language=draft.output_language,
        section_order=draft.section_order,
    )


def _provenanced_statements(
    document: AcceptedResumeDocument,
) -> tuple[_ProvenancedStatement, ...]:
    identity_lines = [document.identity.name]
    if document.identity.headline is not None:
        identity_lines.append(document.identity.headline)
    identity_lines.extend(document.identity.contact_lines)
    statements = [
        _ProvenancedStatement(
            text="\n".join(identity_lines),
            source_fact_ids=document.identity.source_fact_ids,
        ),
    ]
    statements.extend(_bullet_statement(item) for item in document.professional_summary)
    statements.extend(_bullet_statement(item) for item in document.skills)
    for item in document.experience:
        statements.append(
            _ProvenancedStatement(
                text="\n".join(
                    value
                    for value in (
                        item.organization,
                        item.title,
                        item.date_range,
                        item.location,
                    )
                    if value is not None
                ),
                source_fact_ids=item.source_fact_ids,
            ),
        )
        statements.extend(_bullet_statement(bullet) for bullet in item.bullets)
    for item in document.projects:
        statements.append(
            _ProvenancedStatement(
                text="\n".join(
                    value for value in (item.name, item.subtitle) if value is not None
                ),
                source_fact_ids=item.source_fact_ids,
            ),
        )
        statements.extend(_bullet_statement(bullet) for bullet in item.bullets)
    for item in document.education:
        statements.append(
            _ProvenancedStatement(
                text="\n".join(
                    value
                    for value in (item.institution, item.credential, item.date_range)
                    if value is not None
                ),
                source_fact_ids=item.source_fact_ids,
            ),
        )
        statements.extend(_bullet_statement(detail) for detail in item.details)
    statements.extend(
        _ProvenancedStatement(
            text=f"{item.label}\n{item.url}",
            source_fact_ids=item.source_fact_ids,
        )
        for item in document.links
    )
    return tuple(statements)


def _bullet_statement(bullet: ResumeBullet) -> _ProvenancedStatement:
    return _ProvenancedStatement(
        text=bullet.text,
        source_fact_ids=bullet.source_fact_ids,
    )
