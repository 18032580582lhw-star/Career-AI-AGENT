from pathlib import Path
from typing import Final

from docx import Document
from pypdf import PdfReader

from career_ai.models import ResumeMatch

MIN_BULLET_WORDS: Final[int] = 4

SKILL_TERMS: Final[tuple[str, ...]] = (
    "ai",
    "business analysis",
    "cover letter",
    "data analysis",
    "dashboard",
    "evaluation",
    "excel",
    "jd analysis",
    "llm",
    "product",
    "prompt engineering",
    "python",
    "resume",
    "sql",
    "stakeholder",
    "streamlit",
)


def normalize_text(text: str) -> str:
    """Normalize text for deterministic keyword matching."""
    return " ".join(text.lower().split())


def extract_keywords(text: str) -> list[str]:
    """Return known career keywords present in text."""
    normalized = normalize_text(text)
    return [term for term in SKILL_TERMS if term in normalized]


def split_resume_bullets(resume_text: str) -> list[str]:
    """Extract resume bullet-like lines or sentence fallbacks."""
    lines = [line.strip(" -•\t") for line in resume_text.splitlines()]
    bullets = [line for line in lines if len(line.split()) >= MIN_BULLET_WORDS]
    if bullets:
        return bullets
    sentences = [part.strip() for part in resume_text.replace("\n", " ").split(".")]
    return [sentence for sentence in sentences if len(sentence.split()) >= MIN_BULLET_WORDS]


def match_keywords(resume_text: str, jd_keywords: list[str]) -> ResumeMatch:
    """Score the resume against target JD keywords."""
    unique_keywords = sorted({keyword.lower() for keyword in jd_keywords if keyword.strip()})
    resume_normalized = normalize_text(resume_text)
    matched = [keyword for keyword in unique_keywords if keyword in resume_normalized]
    missing = [keyword for keyword in unique_keywords if keyword not in resume_normalized]
    score = round((len(matched) / len(unique_keywords)) * 100) if unique_keywords else 0
    summary = f"Matched {len(matched)} of {len(unique_keywords)} target keywords."
    return ResumeMatch(
        score=score,
        matched_keywords=matched,
        missing_keywords=missing,
        summary=summary,
    )


def extract_resume_text(path: Path) -> str:
    """Extract readable text from a supported resume file."""
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8")
    if suffix == ".docx":
        document = Document(str(path))
        return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
    if suffix == ".pdf":
        reader = PdfReader(path)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    return ""
