"""Typed contracts for real resume-tailoring proposal generation."""

from __future__ import annotations

from enum import StrEnum, unique
from types import MappingProxyType
from typing import Self

from pydantic import Field, field_serializer, model_validator
from pydantic_core import PydanticCustomError

from career_ai.tailoring.adequacy_models import AdequacyContext
from career_ai.tailoring.contract_base import FrozenContractModel, NonEmptyText, RunId, Sha256
from career_ai.tailoring.manifest_contracts import RunState  # noqa: TC001
from career_ai.tailoring.models import (  # noqa: TC001
    CandidateFact,
    EvidenceRequirementMatch,
    JDRequirement,
)
from career_ai.tailoring.proposal_contracts import (
    ProposalStrategy,
    ResumeTailoringProposal,
    SourceBinding,
    TailoringTaskPackage,
)
from career_ai.tailoring.state_machine import ValidationContext, ValidationStateResult


@unique
class ProposalSource(StrEnum):
    """Origin of a proposal before local validation."""

    LOCAL = "local"
    API = "api"
    HOST = "host"


@unique
class ProviderProposalIssue(StrEnum):
    """Safe result for a provider response that contains no valid proposal."""

    INVALID_ENVELOPE = "invalid_provider_proposal_envelope"


class TailoringGenerationContext(FrozenContractModel):
    """Trusted evidence and current identities for one generation attempt."""

    run_id: RunId
    source_hashes: dict[NonEmptyText, Sha256]
    baseline_resume_text: NonEmptyText
    candidate_facts: tuple[CandidateFact, ...]
    requirements: tuple[JDRequirement, ...]
    evidence_matches: tuple[EvidenceRequirementMatch, ...]
    baseline_covered_requirement_ids: frozenset[NonEmptyText]
    template_hash: Sha256 | None = None
    output_language: NonEmptyText = "en"

    @field_serializer("source_hashes")
    def serialize_source_hashes(self, value: dict[str, str]) -> dict[str, str]:
        """Serialize the runtime-immutable source mapping for protocol output."""
        return dict(value)

    @model_validator(mode="after")
    def validate_source_roles(self) -> Self:
        """Require the immutable resume and JD sources that bind every proposal."""
        if not {"resume", "jd"} <= set(self.source_hashes):
            error_code = "missing_generation_source_role"
            error_message = "generation context requires resume and jd source hashes"
            raise PydanticCustomError(error_code, error_message)
        object.__setattr__(self, "source_hashes", MappingProxyType(dict(self.source_hashes)))
        return self

    def adequacy_context(self) -> AdequacyContext:
        """Build the deterministic optimization harness input for this run."""
        return AdequacyContext(
            candidate_facts=self.candidate_facts,
            requirements=self.requirements,
            evidence_matches=self.evidence_matches,
            baseline_covered_requirement_ids=self.baseline_covered_requirement_ids,
            baseline_resume_text=self.baseline_resume_text,
        )

    def validation_context(self) -> ValidationContext:
        """Bind validation to the source and template hashes current for this attempt."""
        return ValidationContext(
            current_source_hashes=dict(self.source_hashes),
            current_template_hash=self.template_hash,
            run_id=self.run_id,
        )

    def task_package(self) -> TailoringTaskPackage:
        """Create the shared API and host task envelope for this run."""
        sources = tuple(
            SourceBinding(
                role=role,
                artifact_id=f"{role}-source",
                sha256=self.source_hashes[role],
            )
            for role in ("resume", "jd")
        ) + _template_source(self.template_hash)
        return TailoringTaskPackage(
            run_id=self.run_id,
            sources=sources,
            candidate_fact_ids=tuple(str(item.id) for item in self.candidate_facts),
            requirement_ids=tuple(str(item.id) for item in self.requirements),
            output_language=self.output_language,
        )


def _template_source(template_hash: Sha256 | None) -> tuple[SourceBinding, ...]:
    if template_hash is None:
        return ()
    return (
        SourceBinding(
            role="latex_template",
            artifact_id="latex-template-source",
            sha256=template_hash,
        ),
    )


class ProviderProposalEnvelope(FrozenContractModel):
    """Strict API-provider response envelope for one untrusted proposal."""

    proposal: ResumeTailoringProposal


class ProposalOutcome(FrozenContractModel):
    """Locally graded result for one generated proposal."""

    source: ProposalSource
    proposal: ResumeTailoringProposal
    state: RunState
    decision: ValidationStateResult
    score: int = Field(ge=0, le=100)


class TailoringGenerationResult(FrozenContractModel):
    """All generated outcomes with a deterministic best valid strategy."""

    outcomes: tuple[ProposalOutcome, ...]
    best_strategy: ProposalStrategy | None = None
    provider_issue: ProviderProposalIssue | None = None
