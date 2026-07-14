"""Run and render provenance manifest contracts."""

from __future__ import annotations

from enum import StrEnum, unique
from typing import Annotated, Self, assert_never

from pydantic import Field, model_validator
from pydantic_core import PydanticCustomError

from career_ai.tailoring.contract_base import (
    FrozenContractModel,
    NonEmptyText,
    RunId,
    Sha256,
    VersionedContract,
    require_unique,
)


@unique
class RunState(StrEnum):
    """Persisted lifecycle state of one tailoring run."""

    DRAFT = "draft"
    VALIDATING = "validating"
    ACCEPTED = "accepted"
    NEEDS_CONFIRMATION = "needs_confirmation"
    REJECTED = "rejected"
    STALE = "stale"
    RENDERED = "rendered"


@unique
class TemplateType(StrEnum):
    """Origin of the LaTeX template bound to a run."""

    SYSTEM = "system"
    USER = "user"


@unique
class RenderBackend(StrEnum):
    """Specific renderer and engine recorded for an output artifact."""

    DOCX = "docx"
    HTML_PLAYWRIGHT = "html-playwright"
    LATEX_SOURCE = "latex-source"
    LATEX_TECTONIC = "latex-tectonic"
    LATEX_XELATEX = "latex-xelatex"


@unique
class RenderEngine(StrEnum):
    """Concrete engine used by a renderer invocation."""

    DOCX = "docx"
    LATEX_SOURCE = "latex-source"
    PLAYWRIGHT = "playwright"
    TECTONIC = "tectonic"
    XELATEX = "xelatex"


class OutputArtifact(FrozenContractModel):
    """Content-addressed output produced by one renderer invocation."""

    path: Annotated[str, Field(pattern=r"^[^\\/:*?\"<>|]+(?:/[^\\/:*?\"<>|]+)*$")]
    sha256: Sha256
    media_type: NonEmptyText


class RunManifest(VersionedContract):
    """Canonical state and provenance pointers for a tailoring run."""

    workspace_schema_version: Annotated[int, Field(ge=1)]
    run_id: RunId
    state: RunState
    source_hashes: dict[NonEmptyText, Sha256]
    request_hash: Sha256
    proposal_hash: Sha256 | None = None
    validation_hash: Sha256 | None = None
    accepted_document_hash: Sha256 | None = None
    template_hash: Sha256 | None = None

    @model_validator(mode="after")
    def validate_state_artifacts(self) -> Self:
        """Make lifecycle states consistent with available immutable artifacts."""
        match self.state:
            case RunState.ACCEPTED | RunState.RENDERED:
                if (
                    self.proposal_hash is None
                    or self.validation_hash is None
                    or self.accepted_document_hash is None
                ):
                    error_code = "accepted_state_artifacts"
                    error_message = (
                        "accepted state requires proposal, validation, and document hashes"
                    )
                    raise PydanticCustomError(
                        error_code,
                        error_message,
                    )
            case (
                RunState.DRAFT
                | RunState.VALIDATING
                | RunState.NEEDS_CONFIRMATION
                | RunState.REJECTED
                | RunState.STALE
            ):
                pass
            case _:
                assert_never(self.state)
        return self


class RenderManifest(VersionedContract):
    """Full provenance for one renderer backend and its outputs."""

    run_id: RunId
    proposal_hash: Sha256
    validation_hash: Sha256
    accepted_document_hash: Sha256
    template_type: TemplateType
    template_hash: Sha256
    backend: RenderBackend
    engine: RenderEngine
    engine_version: NonEmptyText | None = None
    font_bundle_version: NonEmptyText
    outputs: Annotated[tuple[OutputArtifact, ...], Field(min_length=1)]
    page_size: NonEmptyText
    language: NonEmptyText

    @model_validator(mode="after")
    def validate_backend_metadata(self) -> Self:
        """Require engine versions only for executable rendering backends."""
        output_paths = tuple(output.path for output in self.outputs)
        require_unique(output_paths, field_name="output paths")
        match self.backend:
            case RenderBackend.HTML_PLAYWRIGHT:
                _require_engine(self.engine, RenderEngine.PLAYWRIGHT)
                if self.engine_version is None:
                    error_code = "missing_engine_version"
                    error_message = "engine_version is required for compiled render backends"
                    raise PydanticCustomError(
                        error_code,
                        error_message,
                    )
            case RenderBackend.LATEX_TECTONIC:
                _require_engine(self.engine, RenderEngine.TECTONIC)
                if self.engine_version is None:
                    error_code = "missing_engine_version"
                    error_message = "engine_version is required for compiled render backends"
                    raise PydanticCustomError(
                        error_code,
                        error_message,
                    )
            case RenderBackend.LATEX_XELATEX:
                _require_engine(self.engine, RenderEngine.XELATEX)
                if self.engine_version is None:
                    error_code = "missing_engine_version"
                    error_message = "engine_version is required for compiled render backends"
                    raise PydanticCustomError(
                        error_code,
                        error_message,
                    )
            case RenderBackend.DOCX:
                _require_engine(self.engine, RenderEngine.DOCX)
            case RenderBackend.LATEX_SOURCE:
                _require_engine(self.engine, RenderEngine.LATEX_SOURCE)
            case _:
                assert_never(self.backend)
        return self


def _require_engine(actual: RenderEngine, expected: RenderEngine) -> None:
    if actual is expected:
        return
    error_code = "renderer_engine_mismatch"
    error_message = "renderer backend and engine must match"
    raise PydanticCustomError(error_code, error_message)
