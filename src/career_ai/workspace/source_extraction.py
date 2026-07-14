from io import BytesIO
from typing import Final
from zipfile import BadZipFile

from docx import Document
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from career_ai.rendering.latex import LatexStructureError, inspect_latex_structure
from career_ai.workspace.ingestion_errors import IngestionError, IngestionErrorCode

MEDIA_TYPES: Final[dict[str, str]] = {
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".tex": "application/x-tex",
}


def extract_source_text(content: bytes, suffix: str) -> str:
    """Extract readable text from one supported source without OCR."""
    normalized_suffix = suffix.lower()
    if normalized_suffix not in MEDIA_TYPES:
        raise IngestionError(
            IngestionErrorCode.UNSUPPORTED_MEDIA_TYPE,
            f"unsupported source suffix: {suffix or '<none>'}",
        )
    if normalized_suffix in {".txt", ".tex"}:
        text = _decode_utf8(content)
    elif normalized_suffix == ".docx":
        text = _extract_docx(content)
    else:
        text = _extract_pdf(content)
    if not text.strip():
        raise IngestionError(IngestionErrorCode.EMPTY_CONTENT, "no readable text was found")
    return text


def validate_latex_source(text: str) -> None:
    """Require unambiguous document boundaries for an ingested TeX template."""
    try:
        _ = inspect_latex_structure(text)
    except LatexStructureError as exc:
        raise IngestionError(IngestionErrorCode.INVALID_LATEX, str(exc)) from exc


def _decode_utf8(content: bytes) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IngestionError(IngestionErrorCode.INVALID_ENCODING, str(exc)) from exc


def _extract_docx(content: bytes) -> str:
    try:
        document = Document(BytesIO(content))
    except (BadZipFile, OSError, ValueError) as exc:
        raise IngestionError(IngestionErrorCode.SOURCE_READ_FAILED, str(exc)) from exc
    return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())


def _extract_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content))
    except (PdfReadError, OSError, ValueError) as exc:
        raise IngestionError(IngestionErrorCode.SOURCE_READ_FAILED, str(exc)) from exc
    if reader.is_encrypted and reader.decrypt("") == 0:
        raise IngestionError(
            IngestionErrorCode.ENCRYPTED_PDF,
            "password-protected PDFs are not supported",
        )
    try:
        text = "\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
    except (PdfReadError, OSError, ValueError) as exc:
        raise IngestionError(IngestionErrorCode.SOURCE_READ_FAILED, str(exc)) from exc
    if not text:
        raise IngestionError(
            IngestionErrorCode.SCANNED_PDF,
            "PDF contains no extractable text; OCR is not supported",
        )
    return text
