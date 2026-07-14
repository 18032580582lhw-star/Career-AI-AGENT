"""Typed renderer outcomes and stable registry errors."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Annotated, Self, override

from pydantic import Field, model_validator

from career_ai.tailoring.contract_base import FrozenContractModel, NonEmptyText, require_unique
from career_ai.tailoring.manifest_contracts import (  # noqa: TC001
    OutputArtifact,
    RenderBackend,
)


@unique
class RendererErrorCode(StrEnum):
    """Stable expected failure codes shared by renderer backends."""

    INVALID_BACKEND = "renderer_invalid_backend"
    DUPLICATE_BACKEND = "renderer_duplicate_backend"
    BACKEND_NOT_REGISTERED = "renderer_backend_not_registered"
    BACKEND_IDENTITY_MISMATCH = "renderer_backend_identity_mismatch"
    INVALID_OUTCOME = "renderer_invalid_outcome"
    NORMALIZATION_FAILED = "renderer_normalization_failed"
    BACKEND_UNAVAILABLE = "renderer_backend_unavailable"
    INVALID_DOCUMENT = "renderer_invalid_document"
    OUTPUT_FAILED = "renderer_output_failed"


@dataclass(frozen=True, slots=True)
class RendererRegistryError(Exception):
    """Invalid renderer registry configuration or lookup."""

    code: RendererErrorCode
    backend: RenderBackend | None = None

    @override
    def __str__(self) -> str:
        if self.backend is None:
            return self.code.value
        return f"{self.code.value}: {self.backend.value}"


class RendererSuccess(FrozenContractModel):
    """Unified artifact metadata returned by every successful renderer."""

    backend: RenderBackend
    artifacts: Annotated[tuple[OutputArtifact, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_unique_artifacts(self) -> Self:
        """Reject ambiguous duplicate artifact paths."""
        require_unique(
            tuple(artifact.path for artifact in self.artifacts),
            field_name="artifact paths",
        )
        return self


class RenderFailure(FrozenContractModel):
    """Expected renderer failure with a stable machine-readable code."""

    backend: RenderBackend | None
    code: RendererErrorCode
    message: NonEmptyText


type RendererOutcome = RendererSuccess | RenderFailure
