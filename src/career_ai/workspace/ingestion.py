from pathlib import Path

from career_ai.fetch_models import FetchFailure, FetchSuccess
from career_ai.jd_fetcher import fetch_job_description_from_url
from career_ai.workspace.ingestion_errors import IngestionError, IngestionErrorCode
from career_ai.workspace.ingestion_models import IngestedSource, SourceKind, SourceOrigin
from career_ai.workspace.service import validate_workspace
from career_ai.workspace.source_extraction import (
    MEDIA_TYPES,
    extract_source_text,
    validate_latex_source,
)
from career_ai.workspace.source_store import SourceMetadata, persist_source

__all__ = [
    "IngestedSource",
    "IngestionError",
    "IngestionErrorCode",
    "ingest_jd_file",
    "ingest_jd_text",
    "ingest_jd_url",
    "ingest_latex_template",
    "ingest_resume_file",
]


def ingest_resume_file(root: Path, source: Path) -> IngestedSource:
    """Extract and immutably persist one supported resume file."""
    return _ingest_file(root, source, SourceKind.RESUME, require_latex_structure=True)


def ingest_jd_file(root: Path, source: Path) -> IngestedSource:
    """Extract and immutably persist one supported job-description file."""
    return _ingest_file(root, source, SourceKind.JOB_DESCRIPTION, require_latex_structure=False)


def ingest_latex_template(root: Path, source: Path) -> IngestedSource:
    """Validate and persist a user-owned LaTeX template without modifying it."""
    if source.suffix.lower() != ".tex":
        raise IngestionError(
            IngestionErrorCode.UNSUPPORTED_MEDIA_TYPE,
            "LaTeX templates must use the .tex suffix",
        )
    return _ingest_file(root, source, SourceKind.LATEX_TEMPLATE, require_latex_structure=True)


def ingest_jd_text(root: Path, text: str) -> IngestedSource:
    """Persist direct JD text as UTF-8 source content."""
    _ = validate_workspace(root)
    if not text.strip():
        raise IngestionError(IngestionErrorCode.EMPTY_CONTENT, "JD text cannot be empty")
    content = text.encode("utf-8")
    return persist_source(
        root,
        content=content,
        extracted_text=text,
        metadata=SourceMetadata(
            kind=SourceKind.JOB_DESCRIPTION,
            origin=SourceOrigin.TEXT,
            media_type="text/plain",
        ),
    )


def ingest_jd_url(root: Path, url: str) -> IngestedSource:
    """Fetch through the hardened JD client, then persist only successful content."""
    _ = validate_workspace(root)
    result = fetch_job_description_from_url(url)
    match result:
        case FetchFailure(reason=reason, message=message):
            raise IngestionError(IngestionErrorCode.JD_FETCH_FAILED, f"{reason}: {message}")
        case FetchSuccess(text=text, source_url=source_url):
            return persist_source(
                root,
                content=text.encode("utf-8"),
                extracted_text=text,
                metadata=SourceMetadata(
                    kind=SourceKind.JOB_DESCRIPTION,
                    origin=SourceOrigin.URL,
                    media_type="text/plain",
                    source_url=source_url,
                ),
            )


def _ingest_file(
    root: Path,
    source: Path,
    kind: SourceKind,
    *,
    require_latex_structure: bool,
) -> IngestedSource:
    _ = validate_workspace(root)
    if not source.is_file():
        raise IngestionError(IngestionErrorCode.SOURCE_NOT_FOUND, str(source))
    suffix = source.suffix.lower()
    if suffix not in MEDIA_TYPES:
        raise IngestionError(
            IngestionErrorCode.UNSUPPORTED_MEDIA_TYPE,
            f"unsupported source suffix: {suffix or '<none>'}",
        )
    try:
        content = source.read_bytes()
    except OSError as exc:
        raise IngestionError(IngestionErrorCode.SOURCE_READ_FAILED, str(exc)) from exc
    text = extract_source_text(content, suffix)
    if suffix == ".tex" and require_latex_structure:
        validate_latex_source(text)
    return persist_source(
        root,
        content=content,
        extracted_text=text,
        metadata=SourceMetadata(
            kind=kind,
            origin=SourceOrigin.FILE,
            media_type=MEDIA_TYPES[suffix],
            original_name=source.name,
        ),
    )
