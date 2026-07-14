"""Output artifact hashing for renderer backends."""

from __future__ import annotations

from hashlib import sha256
from typing import TYPE_CHECKING

from career_ai.tailoring.manifest_contracts import OutputArtifact

if TYPE_CHECKING:
    from pathlib import Path


def output_artifact(path: Path, *, relative_path: str, media_type: str) -> OutputArtifact:
    """Build content-addressed metadata for one renderer output file."""
    return OutputArtifact(
        path=relative_path,
        sha256=sha256(path.read_bytes()).hexdigest(),
        media_type=media_type,
    )
