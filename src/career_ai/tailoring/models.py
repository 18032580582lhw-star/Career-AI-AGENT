from enum import StrEnum, unique
from typing import Annotated, ClassVar, Literal, NewType, Self, assert_never

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError

SourceArtifactId = NewType("SourceArtifactId", str)
EvidenceSpanId = NewType("EvidenceSpanId", str)
CandidateFactId = NewType("CandidateFactId", str)
JDRequirementId = NewType("JDRequirementId", str)
FactRequirementMatchId = NewType("FactRequirementMatchId", str)

_ID_PATTERN = r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$"
_SourceArtifactIdValue = Annotated[SourceArtifactId, Field(pattern=_ID_PATTERN)]
_EvidenceSpanIdValue = Annotated[EvidenceSpanId, Field(pattern=_ID_PATTERN)]
_CandidateFactIdValue = Annotated[CandidateFactId, Field(pattern=_ID_PATTERN)]
_JDRequirementIdValue = Annotated[JDRequirementId, Field(pattern=_ID_PATTERN)]
_FactRequirementMatchIdValue = Annotated[
    FactRequirementMatchId,
    Field(pattern=_ID_PATTERN),
]
_NonEmptyText = Annotated[str, Field(min_length=1)]
_EvidenceSpanIds = Annotated[tuple[_EvidenceSpanIdValue, ...], Field(min_length=1)]


class FrozenDomainModel(BaseModel):
    """Immutable boundary model for tailoring domain data."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")


@unique
class MatchStatus(StrEnum):
    """Evidence-to-requirement decision state."""

    SUPPORTED = "supported"
    CONFIRMED = "confirmed"
    NEEDS_CONFIRMATION = "needs_confirmation"
    REJECTED = "rejected"


@unique
class RequirementPriority(StrEnum):
    """Importance assigned to one job requirement."""

    REQUIRED = "required"
    PREFERRED = "preferred"
    CONTEXTUAL = "contextual"


class SourceArtifact(FrozenDomainModel):
    """Named source from which evidence may be quoted."""

    id: _SourceArtifactIdValue
    label: _NonEmptyText


class EvidenceSpan(FrozenDomainModel):
    """Verbatim text range tied to one source artifact."""

    id: _EvidenceSpanIdValue
    source_artifact_id: _SourceArtifactIdValue
    text: _NonEmptyText
    start_offset: Annotated[int, Field(ge=0)]
    end_offset: Annotated[int, Field(gt=0)]

    @model_validator(mode="after")
    def validate_offset_order(self) -> Self:
        """Reject reversed or empty source ranges."""
        if self.end_offset <= self.start_offset:
            error_code = "evidence_span_offset_order"
            error_message = "end_offset must be greater than start_offset"
            raise PydanticCustomError(error_code, error_message)
        return self


class EvidenceProvenance(FrozenDomainModel):
    """Fact provenance backed by one or more source spans."""

    kind: Literal["evidence"] = "evidence"
    evidence_span_ids: _EvidenceSpanIds


class UserConfirmationProvenance(FrozenDomainModel):
    """Fact provenance explicitly supplied or confirmed by the user."""

    kind: Literal["user_confirmation"] = "user_confirmation"
    confirmation: _NonEmptyText


type CandidateFactProvenance = Annotated[
    EvidenceProvenance | UserConfirmationProvenance,
    Field(discriminator="kind"),
]


class CandidateFact(FrozenDomainModel):
    """Candidate claim that is safe to reuse because its provenance is explicit."""

    id: _CandidateFactIdValue
    statement: _NonEmptyText
    provenance: CandidateFactProvenance


class JDRequirement(FrozenDomainModel):
    """Requirement extracted from JD evidence, never a candidate fact."""

    id: _JDRequirementIdValue
    statement: _NonEmptyText
    priority: RequirementPriority
    evidence_span_ids: _EvidenceSpanIds


class EvidenceRequirementMatch(FrozenDomainModel):
    """Typed decision connecting source evidence and a JD requirement."""

    id: _FactRequirementMatchIdValue
    requirement_id: _JDRequirementIdValue
    candidate_fact_id: _CandidateFactIdValue | None = None
    evidence_span_ids: tuple[_EvidenceSpanIdValue, ...] = ()
    status: MatchStatus

    @model_validator(mode="after")
    def validate_status_references(self) -> Self:
        """Require the references implied by supported and confirmed states."""
        match self.status:
            case MatchStatus.SUPPORTED:
                if self.candidate_fact_id is None or not self.evidence_span_ids:
                    error_code = "supported_match_references"
                    error_message = "supported matches require a candidate fact and evidence"
                    raise PydanticCustomError(error_code, error_message)
            case MatchStatus.CONFIRMED:
                if self.candidate_fact_id is None:
                    error_code = "confirmed_match_fact"
                    error_message = "confirmed matches require a candidate fact"
                    raise PydanticCustomError(error_code, error_message)
            case MatchStatus.NEEDS_CONFIRMATION | MatchStatus.REJECTED:
                pass
            case _:
                assert_never(self.status)
        return self


def describe_match_status(status: MatchStatus) -> str:
    """Return stable user-facing semantics for every match status."""
    match status:
        case MatchStatus.SUPPORTED:
            return "supported by source evidence"
        case MatchStatus.CONFIRMED:
            return "confirmed explicitly by the user"
        case MatchStatus.NEEDS_CONFIRMATION:
            return "requires user confirmation"
        case MatchStatus.REJECTED:
            return "rejected as unsupported"
        case _:
            assert_never(status)


def describe_requirement_priority(priority: RequirementPriority) -> int:
    """Return the stable sort rank for every requirement priority."""
    match priority:
        case RequirementPriority.REQUIRED:
            return 0
        case RequirementPriority.PREFERRED:
            return 1
        case RequirementPriority.CONTEXTUAL:
            return 2
        case _:
            assert_never(priority)
