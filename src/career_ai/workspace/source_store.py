import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from career_ai.workspace.ingestion_errors import IngestionError, IngestionErrorCode
from career_ai.workspace.ingestion_models import IngestedSource, SourceKind, SourceOrigin
from career_ai.workspace.paths import resolve_workspace_path

_SOURCES_ROOT: Final = Path(".career_ai/sources")


@dataclass(frozen=True, slots=True)
class SourceMetadata:
    """Identity metadata supplied alongside immutable source bytes."""

    kind: SourceKind
    origin: SourceOrigin
    media_type: str
    original_name: str | None = None
    source_url: str | None = None


def persist_source(
    root: Path,
    *,
    content: bytes,
    extracted_text: str,
    metadata: SourceMetadata,
) -> IngestedSource:
    """Persist immutable source bytes and metadata without replacing existing data."""
    content_hash = hashlib.sha256(content).hexdigest()
    identity = json.dumps(
        {
            "kind": metadata.kind.value,
            "origin": metadata.origin.value,
            "sha256": content_hash,
            "media_type": metadata.media_type,
            "original_name": metadata.original_name,
            "source_url": metadata.source_url,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    artifact_id = hashlib.sha256(identity).hexdigest()
    content_path = _SOURCES_ROOT / "blobs" / content_hash
    extracted_path = _SOURCES_ROOT / "records" / artifact_id / "extracted.txt"
    metadata_path = _SOURCES_ROOT / "records" / artifact_id / "artifact.json"
    artifact = IngestedSource(
        artifact_id=artifact_id,
        kind=metadata.kind,
        origin=metadata.origin,
        sha256=content_hash,
        media_type=metadata.media_type,
        content_path=content_path.as_posix(),
        extracted_text_path=extracted_path.as_posix(),
        original_name=metadata.original_name,
        source_url=metadata.source_url,
    )
    raw_target = resolve_workspace_path(root, content_path)
    text_target = resolve_workspace_path(root, extracted_path)
    record_target = resolve_workspace_path(root, metadata_path)
    _write_once(raw_target, content)
    _write_once(text_target, extracted_text.encode("utf-8"))
    _write_once(record_target, f"{artifact.model_dump_json(indent=2)}\n".encode())
    return artifact


def _write_once(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        try:
            existing = path.read_bytes()
        except OSError as exc:
            raise IngestionError(IngestionErrorCode.SOURCE_READ_FAILED, str(exc)) from exc
        if existing != payload:
            raise IngestionError(
                IngestionErrorCode.IMMUTABLE_SOURCE_CONFLICT,
                f"existing content-addressed source differs: {path.name}",
            ) from None
        return
    try:
        with os.fdopen(descriptor, "wb") as stream:
            _ = stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        path.unlink(missing_ok=True)
        raise IngestionError(IngestionErrorCode.SOURCE_READ_FAILED, str(exc)) from exc
