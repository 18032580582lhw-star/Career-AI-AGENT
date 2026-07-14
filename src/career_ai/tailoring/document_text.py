"""Deterministic visible-text projection for accepted resume documents."""

from __future__ import annotations

from typing import assert_never

from pydantic import JsonValue, TypeAdapter

from career_ai.tailoring.contract_base import canonical_json_hash
from career_ai.tailoring.document_contracts import (
    AcceptedResumeDocument,
    ResumeDocumentDraft,
    ResumeSection,
)

_JSON_OBJECT_ADAPTER = TypeAdapter(dict[str, JsonValue])


def accepted_resume_core_text(
    document: AcceptedResumeDocument,
) -> str:
    """Project already-normalized renderer-independent visible text."""
    lines = [document.identity.name]
    if document.identity.headline is not None:
        lines.append(document.identity.headline)
    lines.extend(document.identity.contact_lines)
    for section in document.section_order:
        lines.extend(_section_core_lines(document, section))
    return "\n".join(lines)


def resume_document_structure_hash(
    document: AcceptedResumeDocument | ResumeDocumentDraft,
) -> str:
    """Bind exact renderer-neutral structure without circular acceptance hashes."""
    raw_payload = document.model_dump(
        mode="json",
        exclude={"run_id", "proposal_hash", "validation_hash"},
    )
    payload = _JSON_OBJECT_ADAPTER.validate_python(raw_payload)
    return canonical_json_hash(payload)


def _section_core_lines(
    document: AcceptedResumeDocument,
    section: ResumeSection,
) -> tuple[str, ...]:
    match section:
        case ResumeSection.SUMMARY:
            return tuple(item.text for item in document.professional_summary)
        case ResumeSection.SKILLS:
            return tuple(item.text for item in document.skills)
        case ResumeSection.EXPERIENCE:
            return tuple(
                value
                for item in document.experience
                for value in (
                    item.organization,
                    item.title,
                    item.date_range,
                    item.location,
                    *(bullet.text for bullet in item.bullets),
                )
                if value is not None
            )
        case ResumeSection.PROJECTS:
            return tuple(
                value
                for item in document.projects
                for value in (
                    item.name,
                    item.subtitle,
                    *(bullet.text for bullet in item.bullets),
                )
                if value is not None
            )
        case ResumeSection.EDUCATION:
            return tuple(
                value
                for item in document.education
                for value in (
                    item.institution,
                    item.credential,
                    item.date_range,
                    *(detail.text for detail in item.details),
                )
                if value is not None
            )
        case ResumeSection.LINKS:
            return tuple(
                value for item in document.links for value in (item.label, item.url)
            )
        case _:
            assert_never(section)
