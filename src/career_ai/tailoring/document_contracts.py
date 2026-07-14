"""Accepted resume document contract shared by every renderer."""

from __future__ import annotations

import unicodedata
from enum import StrEnum, unique
from typing import Annotated, Self
from urllib.parse import urlsplit

from pydantic import Field, HttpUrl, TypeAdapter, ValidationError, field_validator, model_validator
from pydantic_core import PydanticCustomError

from career_ai.tailoring.contract_base import (
    EntityId,
    FrozenContractModel,
    NonEmptyText,
    RunId,
    Sha256,
    VersionedContract,
    require_unique,
)
from career_ai.tailoring.proposal_contracts import ResumeTailoringProposal

FactReferences = Annotated[tuple[EntityId, ...], Field(min_length=1)]
_HTTP_URL_ADAPTER = TypeAdapter(HttpUrl)


def _require_valid_http_url(value: str) -> None:
    try:
        parsed = _HTTP_URL_ADAPTER.validate_python(value)
        raw = urlsplit(value)
        raw_hostname = raw.hostname
    except (ValidationError, ValueError) as error:
        error_code = "invalid_resume_url"
        error_message = "url must be a valid HTTP or HTTPS URL"
        raise PydanticCustomError(error_code, error_message) from error
    contains_forbidden_character = any(
        character.isspace() or unicodedata.category(character).startswith("C")
        for character in value
    )
    if (
        contains_forbidden_character
        or not raw.netloc
        or raw_hostname is None
        or parsed.host is None
        or not parsed.host.strip(".")
    ):
        error_code = "invalid_resume_url"
        error_message = "url must be a valid HTTP or HTTPS URL"
        raise PydanticCustomError(error_code, error_message)


@unique
class ResumeSection(StrEnum):
    """Canonical renderer-independent resume sections."""

    SUMMARY = "summary"
    SKILLS = "skills"
    EXPERIENCE = "experience"
    PROJECTS = "projects"
    EDUCATION = "education"
    LINKS = "links"


class ProvenancedDocumentEntry(FrozenContractModel):
    """Visible document content bound to one or more candidate facts."""

    source_fact_ids: FactReferences

    @model_validator(mode="after")
    def validate_fact_ids(self) -> Self:
        """Reject duplicate provenance references."""
        require_unique(self.source_fact_ids, field_name="source_fact_ids")
        return self


class CandidateIdentity(ProvenancedDocumentEntry):
    """Candidate identity and non-link contact details."""

    name: NonEmptyText
    headline: NonEmptyText | None = None
    contact_lines: tuple[NonEmptyText, ...] = ()

    @field_validator("contact_lines")
    @classmethod
    def validate_contact_urls(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Apply the strict URL boundary to URL-shaped contact lines."""
        for value in values:
            if value.casefold().startswith(("http://", "https://")):
                _require_valid_http_url(value)
        return values


class ResumeBullet(ProvenancedDocumentEntry):
    """One accepted text unit with complete factual provenance."""

    text: NonEmptyText


class ExperienceEntry(ProvenancedDocumentEntry):
    """Renderer-neutral professional experience entry."""

    organization: NonEmptyText
    title: NonEmptyText
    date_range: NonEmptyText
    location: NonEmptyText | None = None
    bullets: Annotated[tuple[ResumeBullet, ...], Field(min_length=1)]


class ProjectEntry(ProvenancedDocumentEntry):
    """Renderer-neutral project entry."""

    name: NonEmptyText
    subtitle: NonEmptyText | None = None
    bullets: Annotated[tuple[ResumeBullet, ...], Field(min_length=1)]


class EducationEntry(ProvenancedDocumentEntry):
    """Renderer-neutral education entry."""

    institution: NonEmptyText
    credential: NonEmptyText
    date_range: NonEmptyText | None = None
    details: tuple[ResumeBullet, ...] = ()


class ResumeLink(ProvenancedDocumentEntry):
    """Named link whose label and URL are rendered consistently."""

    label: NonEmptyText
    url: NonEmptyText

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        """Reject malformed or non-web URLs at the document boundary."""
        _require_valid_http_url(value)
        return value


class _ResumeDocumentContent(VersionedContract):
    """Renderer-neutral resume content with complete factual provenance."""

    identity: CandidateIdentity
    professional_summary: tuple[ResumeBullet, ...]
    skills: tuple[ResumeBullet, ...]
    experience: tuple[ExperienceEntry, ...]
    projects: tuple[ProjectEntry, ...]
    education: tuple[EducationEntry, ...]
    links: tuple[ResumeLink, ...]
    output_language: NonEmptyText
    section_order: tuple[ResumeSection, ...]

    @model_validator(mode="after")
    def validate_section_order(self) -> Self:
        """Require exactly one occurrence of every populated section."""
        require_unique(tuple(self.section_order), field_name="section_order")
        populated_sections = tuple(
            section
            for section, content in (
                (ResumeSection.SUMMARY, self.professional_summary),
                (ResumeSection.SKILLS, self.skills),
                (ResumeSection.EXPERIENCE, self.experience),
                (ResumeSection.PROJECTS, self.projects),
                (ResumeSection.EDUCATION, self.education),
                (ResumeSection.LINKS, self.links),
            )
            if content
        )
        required_sections = {
            ResumeSection.SUMMARY,
            ResumeSection.SKILLS,
            ResumeSection.EXPERIENCE,
            ResumeSection.EDUCATION,
        }
        if not required_sections <= set(populated_sections):
            error_code = "missing_required_core_section"
            error_message = (
                "required core sections are summary, skills, experience, and education"
            )
            raise PydanticCustomError(error_code, error_message)
        canonical_order = tuple(
            section for section in ResumeSection if section in populated_sections
        )
        if self.section_order != canonical_order:
            error_code = "section_order_population_mismatch"
            error_message = (
                "section_order must contain populated sections in canonical order"
            )
            raise PydanticCustomError(error_code, error_message)
        return self


class ResumeDocumentDraft(_ResumeDocumentContent):
    """Untrusted structured document awaiting the acceptance gate."""


class AcceptedResumeDocument(_ResumeDocumentContent):
    """Renderer-only contract constructed by the acceptance gate."""

    run_id: RunId
    proposal_hash: Sha256
    validation_hash: Sha256


class StructuredResumeTailoringProposal(ResumeTailoringProposal):
    """Accepted-proposal candidate bound to one exact document structure."""

    document_structure_hash: Sha256
