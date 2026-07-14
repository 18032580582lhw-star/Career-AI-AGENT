from __future__ import annotations

import pytest
from pydantic import ValidationError

from career_ai.tailoring.manifest_contracts import (
    OutputArtifact,
    RenderBackend,
    RenderEngine,
    RenderManifest,
    TemplateType,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def test_render_manifest_records_specific_backend_engine_and_output_hashes() -> None:
    # Given: a compiled LaTeX PDF artifact.
    artifact = OutputArtifact(
        path="resume.pdf",
        sha256=HASH_A,
        media_type="application/pdf",
    )

    # When: the render manifest is constructed.
    manifest = RenderManifest(
        run_id="run-phase-nine",
        proposal_hash=HASH_A,
        validation_hash=HASH_B,
        accepted_document_hash=HASH_C,
        template_type=TemplateType.USER,
        template_hash=HASH_B,
        backend=RenderBackend.LATEX_XELATEX,
        engine=RenderEngine.XELATEX,
        engine_version="XeTeX 3.141592653",
        font_bundle_version="noto-2026-07",
        outputs=(artifact,),
        page_size="A4",
        language="zh-CN",
    )

    # Then: it names the exact backend and engine, never a generic pdf backend.
    assert manifest.backend is RenderBackend.LATEX_XELATEX
    assert manifest.engine is RenderEngine.XELATEX
    assert manifest.outputs[0].sha256 == HASH_A


def test_render_manifest_rejects_generic_pdf_backend_names() -> None:
    # Given: a manifest payload trying to hide renderer identity behind "pdf".
    payload = {
        "protocol_version": "1.0",
        "schema_version": 1,
        "run_id": "run-phase-nine",
        "proposal_hash": HASH_A,
        "validation_hash": HASH_B,
        "accepted_document_hash": HASH_C,
        "template_type": TemplateType.SYSTEM.value,
        "template_hash": HASH_B,
        "backend": "pdf",
        "engine": RenderEngine.PLAYWRIGHT.value,
        "engine_version": "playwright 1.0",
        "font_bundle_version": "noto-2026-07",
        "outputs": [
            {"path": "resume.pdf", "sha256": HASH_A, "media_type": "application/pdf"},
        ],
        "page_size": "A4",
        "language": "en",
    }

    # When / Then: strict enum parsing rejects the ambiguous backend.
    with pytest.raises(ValidationError):
        _ = RenderManifest.model_validate(payload)


def test_render_manifest_requires_matching_engine_for_pdf_backends() -> None:
    # Given: a LaTeX backend paired with the browser engine.
    artifact = OutputArtifact(
        path="resume.pdf",
        sha256=HASH_A,
        media_type="application/pdf",
    )

    # When / Then: backend and engine must agree.
    with pytest.raises(ValidationError, match="engine"):
        _ = RenderManifest(
            run_id="run-phase-nine",
            proposal_hash=HASH_A,
            validation_hash=HASH_B,
            accepted_document_hash=HASH_C,
            template_type=TemplateType.SYSTEM,
            template_hash=HASH_B,
            backend=RenderBackend.LATEX_TECTONIC,
            engine=RenderEngine.PLAYWRIGHT,
            engine_version="playwright 1.0",
            font_bundle_version="noto-2026-07",
            outputs=(artifact,),
            page_size="A4",
            language="en",
        )
