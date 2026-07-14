from dataclasses import dataclass
from enum import StrEnum, unique
from typing import override


@unique
class IngestionErrorCode(StrEnum):
    """Stable failures at untrusted source boundaries."""

    SOURCE_NOT_FOUND = "source_not_found"
    SOURCE_READ_FAILED = "source_read_failed"
    UNSUPPORTED_MEDIA_TYPE = "unsupported_media_type"
    INVALID_ENCODING = "invalid_encoding"
    EMPTY_CONTENT = "empty_content"
    ENCRYPTED_PDF = "encrypted_pdf"
    SCANNED_PDF = "scanned_pdf_ocr_not_supported"
    INVALID_LATEX = "invalid_latex"
    JD_FETCH_FAILED = "jd_fetch_failed"
    IMMUTABLE_SOURCE_CONFLICT = "immutable_source_conflict"


@dataclass(frozen=True, slots=True)
class IngestionError(Exception):
    """Typed source-ingestion failure safe for CLI mapping."""

    code: IngestionErrorCode
    reason: str

    @override
    def __str__(self) -> str:
        return f"{self.code.value}: {self.reason}"
