"""Explicit immutable registry for accepted-document renderers."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol, assert_never, final

from pydantic import JsonValue, TypeAdapter, ValidationError

from career_ai.rendering.models import (
    RendererErrorCode,
    RendererOutcome,
    RendererRegistryError,
    RendererSuccess,
    RenderFailure,
)
from career_ai.tailoring.document_acceptance import (
    DocumentAcceptanceError,
    accept_resume_document,
)
from career_ai.tailoring.manifest_contracts import RenderBackend

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from career_ai.tailoring.document_contracts import (
        AcceptedResumeDocument,
        ResumeDocumentDraft,
        StructuredResumeTailoringProposal,
    )
    from career_ai.tailoring.models import CandidateFact
    from career_ai.tailoring.state_machine import ValidationStateResult

__all__ = [
    "RenderFailure",
    "RendererErrorCode",
    "RendererOutcome",
    "RendererRegistry",
    "RendererRegistryError",
    "RendererRequest",
    "RendererSuccess",
    "ResumeRenderer",
]


class ResumeRenderer(Protocol):
    """Renderer contract shared by DOCX, HTML-PDF, and LaTeX adapters."""

    @property
    def backend(self) -> RenderBackend:
        """Return the exact backend implemented by this renderer."""
        ...

    def render(
        self,
        document: AcceptedResumeDocument,
        output_directory: Path,
    ) -> RendererOutcome:
        """Render one normalized accepted document."""
        ...


@dataclass(frozen=True, slots=True)
class _RegisteredRenderer:
    backend: RenderBackend
    renderer: ResumeRenderer


@dataclass(frozen=True, slots=True)
class RendererRequest:
    """All trusted inputs required to authorize and render one resume draft."""

    draft: ResumeDocumentDraft
    proposal: StructuredResumeTailoringProposal
    validation: ValidationStateResult
    candidate_facts: tuple[CandidateFact, ...]
    output_directory: Path


_OUTCOME_ADAPTER: TypeAdapter[RendererOutcome] = TypeAdapter(RendererOutcome)


def _untrusted_backend(renderer: ResumeRenderer) -> RenderBackend | str:
    """Widen an adapter property before enforcing its runtime enum identity."""
    return renderer.backend


@final
class RendererRegistry:
    """Immutable renderer lookup and normalized dispatch boundary."""

    __slots__ = ("_renderers",)

    def __init__(self, renderers: Iterable[ResumeRenderer] = ()) -> None:
        """Build an immutable registry and reject duplicate backends."""
        registered: dict[RenderBackend, _RegisteredRenderer] = {}
        for renderer in renderers:
            untrusted_backend = _untrusted_backend(renderer)
            if not isinstance(untrusted_backend, RenderBackend):
                raise RendererRegistryError(code=RendererErrorCode.INVALID_BACKEND)
            backend = untrusted_backend
            if backend in registered:
                raise RendererRegistryError(
                    code=RendererErrorCode.DUPLICATE_BACKEND,
                    backend=backend,
                )
            registered[backend] = _RegisteredRenderer(backend=backend, renderer=renderer)
        self._renderers = MappingProxyType(registered)

    def backends(self) -> tuple[RenderBackend, ...]:
        """Return registered backends in stable enum declaration order."""
        return tuple(backend for backend in RenderBackend if backend in self._renderers)

    def _require_registered(
        self,
        backend: RenderBackend | str,
    ) -> _RegisteredRenderer:
        """Resolve one typed backend without fallback."""
        if not isinstance(backend, RenderBackend):
            raise RendererRegistryError(code=RendererErrorCode.INVALID_BACKEND)
        renderer = self._renderers.get(backend)
        if renderer is None:
            raise RendererRegistryError(
                code=RendererErrorCode.BACKEND_NOT_REGISTERED,
                backend=backend,
            )
        return renderer

    def render(
        self,
        backend: RenderBackend | str,
        request: RendererRequest,
    ) -> RendererOutcome:
        """Accept one draft, then dispatch its unique normalized document."""
        try:
            registered = self._require_registered(backend)
        except RendererRegistryError as error:
            return RenderFailure(
                backend=error.backend,
                code=error.code,
                message=str(error),
            )
        identity_failure = _backend_identity_failure(registered)
        if identity_failure is not None:
            return identity_failure
        try:
            accepted = accept_resume_document(
                request.draft,
                request.proposal,
                request.validation,
                request.candidate_facts,
            )
        except (DocumentAcceptanceError, ValidationError):
            return RenderFailure(
                backend=registered.backend,
                code=RendererErrorCode.INVALID_DOCUMENT,
                message="document did not pass the acceptance boundary",
            )
        try:
            untrusted_outcome = registered.renderer.render(
                accepted,
                request.output_directory,
            )
        except (ImportError, OSError, ValidationError) as error:
            return _backend_exception_failure(error, registered.backend)
        outcome = _validated_outcome(untrusted_outcome, registered.backend)
        result_backend = outcome.backend
        if result_backend is not registered.backend:
            return RenderFailure(
                backend=registered.backend,
                code=RendererErrorCode.BACKEND_IDENTITY_MISMATCH,
                message="renderer returned metadata for a different backend",
            )
        return outcome


def _validated_outcome(
    value: RendererOutcome | JsonValue,
    backend: RenderBackend,
) -> RendererOutcome:
    """Revalidate an untrusted adapter result, including model_construct values."""
    if not isinstance(value, (RendererSuccess, RenderFailure)):
        return RenderFailure(
            backend=backend,
            code=RendererErrorCode.INVALID_OUTCOME,
            message="renderer returned an invalid outcome",
        )
    try:
        return _OUTCOME_ADAPTER.validate_python(
            value.model_dump(mode="python", warnings=False),
        )
    except ValidationError:
        return RenderFailure(
            backend=backend,
            code=RendererErrorCode.INVALID_OUTCOME,
            message="renderer returned invalid outcome metadata",
        )


def _backend_identity_failure(
    registered: _RegisteredRenderer,
) -> RenderFailure | None:
    try:
        current_backend = _untrusted_backend(registered.renderer)
    except (ImportError, OSError) as error:
        return _backend_exception_failure(error, registered.backend)
    except (AttributeError, TypeError, ValueError):
        current_backend = "invalid"
    if current_backend is registered.backend:
        return None
    return RenderFailure(
        backend=registered.backend,
        code=RendererErrorCode.BACKEND_IDENTITY_MISMATCH,
        message="renderer backend identity changed after registration",
    )


def _backend_exception_failure(
    error: ImportError | OSError | ValidationError,
    backend: RenderBackend,
) -> RenderFailure:
    match error:
        case ImportError():
            return RenderFailure(
                backend=backend,
                code=RendererErrorCode.BACKEND_UNAVAILABLE,
                message="renderer backend dependency is unavailable",
            )
        case OSError():
            return RenderFailure(
                backend=backend,
                code=RendererErrorCode.OUTPUT_FAILED,
                message="renderer could not write output artifacts",
            )
        case ValidationError():
            return RenderFailure(
                backend=backend,
                code=RendererErrorCode.INVALID_OUTCOME,
                message="renderer could not construct valid outcome metadata",
            )
        case _:
            assert_never(error)
