from enum import StrEnum, unique
from typing import Literal

from career_ai.tailoring.models import (
    CandidateFact,
    EvidenceSpan,
    FrozenDomainModel,
    JDRequirement,
    SourceArtifactId,
)


class ResumeFactSource(FrozenDomainModel):
    """Source binding that structurally limits fact extraction to resumes."""

    role: Literal["resume"] = "resume"
    artifact_id: SourceArtifactId


@unique
class CandidateFactKind(StrEnum):
    """Deterministic resume element classified as candidate evidence."""

    PARAGRAPH = "paragraph"
    BULLET = "bullet"
    DATE = "date"
    NUMBER = "number"
    TECHNOLOGY = "technology"
    ORGANIZATION = "organization"
    ROLE = "role"
    RESULT = "result"


@unique
class JDRequirementCategory(StrEnum):
    """Closed job-requirement taxonomy used by the v1 extractor."""

    RESPONSIBILITY = "responsibility"
    REQUIRED_SKILL = "required_skill"
    PREFERRED_SKILL = "preferred_skill"
    SENIORITY = "seniority"
    INDUSTRY_LANGUAGE = "industry_language"
    OUTCOME = "outcome"
    ATS_KEYWORD = "ats_keyword"


class ExtractedCandidateFact(FrozenDomainModel):
    """Candidate fact paired with its deterministic semantic kind."""

    fact: CandidateFact
    kind: CandidateFactKind


class CandidateFactExtraction(FrozenDomainModel):
    """Complete evidence-backed extraction from one resume source."""

    evidence_spans: tuple[EvidenceSpan, ...]
    facts: tuple[ExtractedCandidateFact, ...]


class ExtractedJDRequirement(FrozenDomainModel):
    """JD requirement paired with its domain category."""

    requirement: JDRequirement
    category: JDRequirementCategory


class JDRequirementExtraction(FrozenDomainModel):
    """Complete typed extraction from one JD source."""

    evidence_spans: tuple[EvidenceSpan, ...]
    requirements: tuple[ExtractedJDRequirement, ...]
