from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override

import pytest

from career_ai.rendering.registry import (
    RendererErrorCode,
    RendererRegistry,
    RendererRegistryError,
    RendererRequest,
    RendererSuccess,
    RenderFailure,
)
from career_ai.tailoring.document_text import accepted_resume_core_text
from career_ai.tailoring.manifest_contracts import OutputArtifact, RenderBackend
from tests.resume_document_helpers import (
    accepted_bundle,
    accepted_document_candidate_facts,
)

_OUTPUT_DIRECTORY = Path("outputs")

if TYPE_CHECKING:
    from career_ai.rendering.models import RendererOutcome
    from career_ai.tailoring.document_contracts import AcceptedResumeDocument


class RecordingRenderer:
    """Fake renderer that records the normalized accepted document it receives."""

    def __init__(self, backend: RenderBackend, extension: str, media_type: str) -> None:
        self._backend: RenderBackend = backend
        self._extension: str = extension
        self._media_type: str = media_type
        self.documents: list[AcceptedResumeDocument] = []

    @property
    def backend(self) -> RenderBackend:
        return self._backend

    def render(
        self,
        document: AcceptedResumeDocument,
        output_directory: Path,
    ) -> RendererOutcome:
        del output_directory
        self.documents.append(document)
        return RendererSuccess(
            backend=self.backend,
            artifacts=(
                OutputArtifact(
                    path=f"resume.{self._extension}",
                    sha256="c" * 64,
                    media_type=self._media_type,
                ),
            ),
        )


class MismatchedRenderer(RecordingRenderer):
    @override
    def render(
        self,
        document: AcceptedResumeDocument,
        output_directory: Path,
    ) -> RendererOutcome:
        del document, output_directory
        return RendererSuccess(
            backend=RenderBackend.LATEX_SOURCE,
            artifacts=(
                OutputArtifact(
                    path="resume.tex",
                    sha256="d" * 64,
                    media_type="application/x-tex",
                ),
            ),
        )


class SnapshotOutcomeRenderer(RecordingRenderer):
    """Renderer whose output identity stays fixed if its property mutates."""

    def __init__(self, backend: RenderBackend) -> None:
        super().__init__(backend, "docx", "application/zip")
        self._result_backend: RenderBackend = backend

    @override
    def render(
        self,
        document: AcceptedResumeDocument,
        output_directory: Path,
    ) -> RendererOutcome:
        del document, output_directory
        return RendererSuccess(
            backend=self._result_backend,
            artifacts=(
                OutputArtifact(
                    path="resume.docx",
                    sha256="e" * 64,
                    media_type="application/zip",
                ),
            ),
        )


def _three_renderers() -> tuple[RecordingRenderer, ...]:
    return (
        RecordingRenderer(
            RenderBackend.DOCX,
            "docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        RecordingRenderer(RenderBackend.HTML_PLAYWRIGHT, "pdf", "application/pdf"),
        RecordingRenderer(RenderBackend.LATEX_SOURCE, "tex", "application/x-tex"),
    )


def _render(
    registry: RendererRegistry,
    backend: RenderBackend | str,
    output_directory: Path = _OUTPUT_DIRECTORY,
) -> RendererOutcome:
    draft, proposal, validation = accepted_bundle()
    request = RendererRequest(
        draft=draft,
        proposal=proposal,
        validation=validation,
        candidate_facts=accepted_document_candidate_facts(),
        output_directory=output_directory,
    )
    return registry.render(backend, request)


def test_same_unique_accepted_document_enters_three_registered_backends() -> None:
    renderers = _three_renderers()
    registry = RendererRegistry(renderers)

    outcomes = tuple(_render(registry, renderer.backend) for renderer in renderers)

    assert all(isinstance(outcome, RendererSuccess) for outcome in outcomes)
    core_texts = tuple(
        accepted_resume_core_text(renderer.documents[0]) for renderer in renderers
    )
    assert core_texts == (core_texts[0],) * 3
    assert len({renderer.documents[0].validation_hash for renderer in renderers}) == 1


def test_registry_returns_stable_failure_for_unregistered_backend() -> None:
    outcome = _render(
        RendererRegistry(_three_renderers()[:1]),
        RenderBackend.HTML_PLAYWRIGHT,
    )

    assert isinstance(outcome, RenderFailure)
    assert outcome.code is RendererErrorCode.BACKEND_NOT_REGISTERED


def test_registry_rejects_duplicate_backend_registration() -> None:
    first = _three_renderers()[0]
    duplicate = RecordingRenderer(RenderBackend.DOCX, "docx", "application/zip")

    with pytest.raises(RendererRegistryError) as exc_info:
        _ = RendererRegistry((first, duplicate))

    assert exc_info.value.code is RendererErrorCode.DUPLICATE_BACKEND


def test_registry_rejects_raw_string_despite_strenum_equality() -> None:
    outcome = _render(RendererRegistry(_three_renderers()), "docx")

    assert isinstance(outcome, RenderFailure)
    assert outcome.code is RendererErrorCode.INVALID_BACKEND


def test_registry_rejects_renderer_with_runtime_corrupted_backend() -> None:
    renderer = _three_renderers()[0]
    renderer.__dict__["_backend"] = "docx"

    with pytest.raises(RendererRegistryError) as exc_info:
        _ = RendererRegistry((renderer,))

    assert exc_info.value.code is RendererErrorCode.INVALID_BACKEND


def test_registered_backends_follow_enum_declaration_order() -> None:
    backends = RendererRegistry(tuple(reversed(_three_renderers()))).backends()

    assert backends == (
        RenderBackend.DOCX,
        RenderBackend.HTML_PLAYWRIGHT,
        RenderBackend.LATEX_SOURCE,
    )


def test_registry_converts_backend_identity_mismatch_to_stable_failure() -> None:
    registry = RendererRegistry(
        (MismatchedRenderer(RenderBackend.DOCX, "docx", "application/zip"),),
    )

    outcome = _render(registry, RenderBackend.DOCX)

    assert isinstance(outcome, RenderFailure)
    assert outcome.code is RendererErrorCode.BACKEND_IDENTITY_MISMATCH


def test_registry_uses_registration_snapshot_if_adapter_mutates() -> None:
    renderer = _three_renderers()[0]
    registry = RendererRegistry((renderer,))
    renderer.__dict__["_backend"] = RenderBackend.LATEX_SOURCE

    outcome = _render(registry, RenderBackend.DOCX)

    assert isinstance(outcome, RenderFailure)
    assert outcome.code is RendererErrorCode.BACKEND_IDENTITY_MISMATCH


def test_registry_blocks_mutation_before_renderer_side_effects() -> None:
    renderer = SnapshotOutcomeRenderer(RenderBackend.DOCX)
    registry = RendererRegistry((renderer,))
    renderer.__dict__["_backend"] = RenderBackend.LATEX_SOURCE

    outcome = _render(registry, RenderBackend.DOCX)

    assert isinstance(outcome, RenderFailure)
    assert outcome.code is RendererErrorCode.BACKEND_IDENTITY_MISMATCH


def test_registry_revalidates_constructed_outcome_metadata() -> None:
    class InvalidOutcomeRenderer(RecordingRenderer):
        @override
        def render(
            self,
            document: AcceptedResumeDocument,
            output_directory: Path,
        ) -> RendererOutcome:
            del document, output_directory
            return RendererSuccess.model_construct(backend="docx", artifacts=())

    registry = RendererRegistry(
        (InvalidOutcomeRenderer(RenderBackend.DOCX, "docx", "application/zip"),),
    )

    outcome = _render(registry, RenderBackend.DOCX)

    assert isinstance(outcome, RenderFailure)
    assert outcome.code is RendererErrorCode.INVALID_OUTCOME


def test_registry_converts_outcome_construction_validation_error() -> None:
    class InvalidOutcomeRenderer(RecordingRenderer):
        @override
        def render(
            self,
            document: AcceptedResumeDocument,
            output_directory: Path,
        ) -> RendererOutcome:
            del document, output_directory
            return RendererSuccess(backend=RenderBackend.DOCX, artifacts=())

    registry = RendererRegistry(
        (InvalidOutcomeRenderer(RenderBackend.DOCX, "docx", "application/zip"),),
    )

    outcome = _render(registry, RenderBackend.DOCX)

    assert isinstance(outcome, RenderFailure)
    assert outcome.code is RendererErrorCode.INVALID_OUTCOME


@pytest.mark.parametrize(
    ("error", "expected_code"),
    [
        (ImportError("missing dependency"), RendererErrorCode.BACKEND_UNAVAILABLE),
        (OSError("sensitive path"), RendererErrorCode.OUTPUT_FAILED),
    ],
)
def test_registry_converts_expected_backend_errors(
    error: ImportError | OSError,
    expected_code: RendererErrorCode,
) -> None:
    class FailingRenderer(RecordingRenderer):
        @override
        def render(
            self,
            document: AcceptedResumeDocument,
            output_directory: Path,
        ) -> RendererOutcome:
            del document, output_directory
            raise error

    registry = RendererRegistry(
        (FailingRenderer(RenderBackend.DOCX, "docx", "application/zip"),),
    )

    outcome = _render(registry, RenderBackend.DOCX)

    assert isinstance(outcome, RenderFailure)
    assert outcome.code is expected_code
    assert "sensitive" not in outcome.message
