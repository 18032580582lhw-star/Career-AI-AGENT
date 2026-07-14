"""Proposal, validation, and confirmation protocol contracts."""

from __future__ import annotations

from enum import StrEnum, unique
from types import MappingProxyType
from typing import Annotated, Self, assert_never

from pydantic import Field, field_serializer, field_validator, model_validator
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
from career_ai.tailoring.models import MatchStatus
from career_ai.tailoring.proposal_hashing import calculate_proposal_hash

__all__ = ("calculate_proposal_hash",)


@unique
class ProposalStrategy(StrEnum):
    """Supported resume-tailoring strategies."""

    CONSERVATIVE = "conservative"
    ATS_ALIGNED = "ats-aligned"
    IMPACT_NARRATIVE = "impact-narrative"
    SAFE_FALLBACK = "safe-fallback"


@unique
class ChangeOperation(StrEnum):
    """Semantic operation applied by a proposed edit."""

    REWRITE = "rewrite"
    REORDER = "reorder"
    ADD = "add"
    REMOVE = "remove"
    COMPRESS = "compress"


@unique
class ValidationSeverity(StrEnum):
    """Severity assigned to a deterministic validation finding."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@unique
class ValidationOutcome(StrEnum):
    """Aggregate outcome of the dual-harness validation."""

    ACCEPTED = "accepted"
    NEEDS_CONFIRMATION = "needs_confirmation"
    REJECTED = "rejected"
    STALE = "stale"


@unique
class ConfirmationDecision(StrEnum):
    """User response to a confirmation request."""

    CONFIRM = "confirm"
    REJECT = "reject"


class SourceBinding(FrozenContractModel):
    """Immutable source identity included in a host task package."""

    role: Annotated[str, Field(pattern=r"^(resume|jd|latex_template)$")]
    artifact_id: EntityId
    sha256: Sha256


class TailoringTaskPackage(VersionedContract):
    """Complete typed input envelope shared by API and host generation."""

    run_id: RunId
    sources: Annotated[tuple[SourceBinding, ...], Field(min_length=2)]
    candidate_fact_ids: tuple[EntityId, ...]
    requirement_ids: tuple[EntityId, ...]
    output_language: NonEmptyText

    @model_validator(mode="after")
    def validate_unique_references(self) -> Self:
        """Reject ambiguous source roles and duplicate domain references."""
        roles = tuple(source.role for source in self.sources)
        require_unique(roles, field_name="source roles")
        require_unique(self.candidate_fact_ids, field_name="candidate_fact_ids")
        require_unique(self.requirement_ids, field_name="requirement_ids")
        return self


class ProposedClaim(FrozenContractModel):
    """Factual claim introduced or materially changed by a proposal."""

    id: EntityId
    statement: NonEmptyText
    source_fact_ids: tuple[EntityId, ...] = ()
    status: MatchStatus

    @model_validator(mode="after")
    def validate_evidence_requirement(self) -> Self:
        """Require source facts for claims represented as evidence-supported."""
        require_unique(self.source_fact_ids, field_name="source_fact_ids")
        match self.status:
            case MatchStatus.SUPPORTED:
                if not self.source_fact_ids:
                    error_code = "supported_claim_facts"
                    error_message = "supported claims require source facts"
                    raise PydanticCustomError(
                        error_code,
                        error_message,
                    )
            case MatchStatus.CONFIRMED | MatchStatus.NEEDS_CONFIRMATION | MatchStatus.REJECTED:
                pass
            case _:
                assert_never(self.status)
        return self


class ResumeChange(FrozenContractModel):
    """One auditable before/after resume edit."""

    id: EntityId
    section: NonEmptyText
    before: str
    after: NonEmptyText
    source_fact_ids: Annotated[tuple[EntityId, ...], Field(min_length=1)]
    target_requirement_ids: Annotated[tuple[EntityId, ...], Field(min_length=1)]
    operation: ChangeOperation
    proposed_claim_ids: tuple[EntityId, ...] = ()
    risk_notes: tuple[NonEmptyText, ...] = ()

    @model_validator(mode="after")
    def validate_unique_references(self) -> Self:
        """Keep every edit reference deterministic and unambiguous."""
        require_unique(self.source_fact_ids, field_name="source_fact_ids")
        require_unique(self.target_requirement_ids, field_name="target_requirement_ids")
        require_unique(self.proposed_claim_ids, field_name="proposed_claim_ids")
        return self


class ResumeTailoringProposal(VersionedContract):
    """Versioned host/API proposal validated by both harnesses."""

    run_id: RunId
    source_hashes: dict[NonEmptyText, Sha256]
    template_hash: Sha256 | None = None
    strategy: ProposalStrategy
    rewritten_resume: NonEmptyText
    changes: tuple[ResumeChange, ...]
    proposed_claims: tuple[ProposedClaim, ...]
    proposal_hash: Sha256

    @field_serializer("source_hashes")
    def serialize_source_hashes(self, value: dict[str, str]) -> dict[str, str]:
        return dict(value)

    @field_validator("rewritten_resume")
    @classmethod
    def validate_rewritten_resume(cls, value: str) -> str:
        """Reject whitespace-only full outputs at the protocol boundary."""
        if not value.strip():
            error_code = "empty_rewritten_resume"
            error_message = "rewritten_resume must contain visible text"
            raise PydanticCustomError(
                error_code,
                error_message,
            )
        return value

    @model_validator(mode="after")
    def validate_integrity(self) -> Self:
        """Validate unique references and the canonical proposal hash."""
        change_ids = tuple(change.id for change in self.changes)
        claim_ids = tuple(claim.id for claim in self.proposed_claims)
        require_unique(change_ids, field_name="change ids")
        require_unique(claim_ids, field_name="claim ids")
        available_claim_ids = set(claim_ids)
        referenced_claim_ids = {
            claim_id for change in self.changes for claim_id in change.proposed_claim_ids
        }
        if not referenced_claim_ids.issubset(available_claim_ids):
            error_code = "unknown_proposed_claim"
            error_message = "changes reference unknown proposed claims"
            raise PydanticCustomError(
                error_code,
                error_message,
            )
        payload = self.model_dump(mode="json", exclude={"proposal_hash"})
        expected = calculate_proposal_hash(payload)
        if self.proposal_hash != expected:
            error_code = "proposal_hash_mismatch"
            error_message = "proposal_hash does not match canonical proposal content"
            raise PydanticCustomError(
                error_code,
                error_message,
            )
        object.__setattr__(self, "source_hashes", MappingProxyType(dict(self.source_hashes)))
        return self


class ValidationFinding(FrozenContractModel):
    """Stable machine-readable finding produced by either harness."""

    id: EntityId
    code: EntityId
    severity: ValidationSeverity
    message: NonEmptyText
    change_id: EntityId | None = None
    claim_id: EntityId | None = None
    confirmation_prompt: NonEmptyText | None = None


class ValidationDecision(VersionedContract):
    """Aggregate safety and adequacy decision for one proposal."""

    run_id: RunId
    proposal_hash: Sha256
    outcome: ValidationOutcome
    findings: tuple[ValidationFinding, ...]
    safety_passed: bool
    adequacy_passed: bool
    validation_hash: Sha256

    @model_validator(mode="after")
    def validate_outcome(self) -> Self:
        """Prevent accepted decisions from contradicting their findings."""
        finding_ids = tuple(finding.id for finding in self.findings)
        require_unique(finding_ids, field_name="finding ids")
        match self.outcome:
            case ValidationOutcome.ACCEPTED:
                has_errors = any(
                    finding.severity is ValidationSeverity.ERROR for finding in self.findings
                )
                if has_errors:
                    error_code = "accepted_with_errors"
                    error_message = "accepted decisions cannot contain errors"
                    raise PydanticCustomError(
                        error_code,
                        error_message,
                    )
                if not self.safety_passed or not self.adequacy_passed:
                    error_code = "accepted_without_dual_pass"
                    error_message = "accepted decisions require both harnesses to pass"
                    raise PydanticCustomError(
                        error_code,
                        error_message,
                    )
            case (
                ValidationOutcome.NEEDS_CONFIRMATION
                | ValidationOutcome.REJECTED
                | ValidationOutcome.STALE
            ):
                pass
            case _:
                assert_never(self.outcome)
        return self


class ConfirmationResponse(VersionedContract):
    """User decision resolving one validation finding."""

    run_id: RunId
    proposal_hash: Sha256
    finding_id: EntityId
    decision: ConfirmationDecision
    confirmed_statement: NonEmptyText | None = None

    @model_validator(mode="after")
    def validate_statement(self) -> Self:
        """Require explicit language for confirmed facts only."""
        match self.decision:
            case ConfirmationDecision.CONFIRM:
                if self.confirmed_statement is None:
                    error_code = "missing_confirmed_statement"
                    error_message = "confirmed_statement is required when confirming"
                    raise PydanticCustomError(
                        error_code,
                        error_message,
                    )
            case ConfirmationDecision.REJECT:
                if self.confirmed_statement is not None:
                    error_code = "rejected_with_statement"
                    error_message = "confirmed_statement must be absent when rejecting"
                    raise PydanticCustomError(
                        error_code,
                        error_message,
                    )
            case _:
                assert_never(self.decision)
        return self
