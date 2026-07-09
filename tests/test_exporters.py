from pathlib import Path

from docx import Document

from career_ai.analysis import analyze_career_fit, get_sample_inputs
from career_ai.exporters import build_cover_letter_docx, build_resume_docx


def _read_docx_text(path: Path) -> str:
    document = Document(str(path))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def test_build_resume_docx_and_cover_letter_docx_include_key_content(tmp_path: Path) -> None:
    resume_text, jd_text = get_sample_inputs()
    report = analyze_career_fit(resume_text=resume_text, jd_text=jd_text)

    resume_path = build_resume_docx(report, tmp_path / "tailored-resume.docx")
    cover_path = build_cover_letter_docx(report, tmp_path / "cover-letter.docx")

    resume_doc = _read_docx_text(resume_path)
    cover_doc = _read_docx_text(cover_path)
    assert "AI Product Analyst" in resume_doc
    assert "Tailored Resume" in resume_doc
    assert cover_doc.startswith("Dear Hiring Team,")
