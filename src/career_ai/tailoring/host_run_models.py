"""Host-proposal run protocol models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Annotated, override

from pydantic import Field, JsonValue

from career_ai.tailoring.contract_base import (
    FrozenContractModel,
    NonEmptyText,
    RunId,
    Sha256,
    VersionedContract,
)
from career_ai.tailoring.document_contracts import (
    ResumeDocumentDraft,  # noqa: TC001
    StructuredResumeTailoringProposal,  # noqa: TC001
)
from career_ai.tailoring.generation_models import ProposalSource  # noqa: TC001
from career_ai.tailoring.manifest_contracts import (
    OutputArtifact,
    RenderBackend,
    RunState,
    TemplateType,
)
from career_ai.tailoring.proposal_contracts import ResumeTailoringProposal

RENDER_STALE_EXIT_CODE = 15


@unique
class HostRenderFormat(StrEnum):
    """CLI-facing render format choices."""

    DOCX = "docx"
    PDF = "pdf"
    TEX = "tex"
    LATEX_PDF = "latex-pdf"
    ALL = "all"


class HostRunRequest(VersionedContract):
    """Persistent immutable inputs that bind one host-proposal run."""

    run_id: RunId
    resume_text: NonEmptyText
    jd_text: NonEmptyText
    source_hashes: dict[NonEmptyText, Sha256]
    output_language: NonEmptyText
    resume_path: str | None = None
    jd_path: str | None = None
    template_type: TemplateType = TemplateType.SYSTEM
    template_path: str | None = None
    template_source: str | None = None
    template_hash: Sha256


class HostPrepareResult(FrozenContractModel):
    """Machine-readable prepare response for host proposal authors."""

    run_id: RunId
    request_artifact: NonEmptyText
    proposal_schema: dict[str, JsonValue]
    source_hashes: dict[NonEmptyText, Sha256]
    template_type: TemplateType
    template_hash: Sha256
    next_machine_instruction: NonEmptyText


class HostStructuredProposalPackage(FrozenContractModel):
    """Render-capable host package containing structured document material."""

    draft: ResumeDocumentDraft
    proposal: StructuredResumeTailoringProposal


type HostProposalInput = HostStructuredProposalPackage | ResumeTailoringProposal


class HostValidationResult(FrozenContractModel):
    """Machine-readable validation response."""

    run_id: RunId
    source: ProposalSource
    state: RunState
    proposal_hash: Sha256 | None = None
    validation_hash: Sha256 | None = None


class HostRenderItem(FrozenContractModel):
    """One render attempt outcome for a format."""

    format: HostRenderFormat
    status: Annotated[str, Field(pattern=r"^(rendered|failed|unavailable|stale)$")]
    backend: RenderBackend | None = None
    code: str | None = None
    artifacts: tuple[OutputArtifact, ...] = ()
    manifest_path: str | None = None


class HostRenderResult(FrozenContractModel):
    """Machine-readable render response."""

    run_id: RunId
    results: tuple[HostRenderItem, ...]


@dataclass(frozen=True, slots=True)
class HostRunError(Exception):
    """Expected host-run workflow failure."""

    message: str
    exit_code: int = 2

    @override
    def __str__(self) -> str:
        """Return the CLI-safe error message."""
        return self.message


def expand_render_formats(render_format: HostRenderFormat) -> tuple[HostRenderFormat, ...]:
    """Expand the aggregate render format into concrete formats."""
    match render_format:
        case HostRenderFormat.ALL:
            return (
                HostRenderFormat.DOCX,
                HostRenderFormat.PDF,
                HostRenderFormat.TEX,
                HostRenderFormat.LATEX_PDF,
            )
        case (
            HostRenderFormat.DOCX
            | HostRenderFormat.PDF
            | HostRenderFormat.TEX
            | HostRenderFormat.LATEX_PDF
        ):
            return (render_format,)
