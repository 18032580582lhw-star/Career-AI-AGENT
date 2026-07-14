from pathlib import Path

from docx import Document
from pypdf import PdfWriter

from career_ai.text_processing import extract_keywords, extract_resume_text, match_keywords


def test_extract_resume_text_reads_txt_and_docx_files(tmp_path: Path) -> None:
    txt_path = tmp_path / "resume.txt"
    _ = txt_path.write_text("Built Streamlit dashboards with Python.", encoding="utf-8")

    docx_path = tmp_path / "resume.docx"
    document = Document()
    _ = document.add_paragraph("Analyzed hiring data with SQL.")
    document.save(str(docx_path))

    assert "Streamlit dashboards" in extract_resume_text(txt_path)
    assert "hiring data" in extract_resume_text(docx_path)


def test_extract_resume_text_returns_clear_message_for_empty_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "empty.pdf"
    writer = PdfWriter()
    _ = writer.add_blank_page(width=72, height=72)
    with pdf_path.open("wb") as output:
        _ = writer.write(output)

    assert extract_resume_text(pdf_path) == ""


def test_match_keywords_scores_strong_and_weak_matches() -> None:
    strong = match_keywords(
        resume_text="Python SQL Streamlit LLM evaluation dashboard",
        jd_keywords=["python", "sql", "streamlit", "llm"],
    )
    weak = match_keywords(
        resume_text="Excel coordinator",
        jd_keywords=["python", "sql", "streamlit", "llm"],
    )

    assert strong.score >= 90
    assert weak.score <= 25


def test_extract_keywords_preserves_jd_skill_phrases() -> None:
    # Given: a JD with multi-word career skills.
    jd_text = (
        "Requirements include dashboard storytelling, stakeholder communication, "
        "Python, SQL, and Streamlit."
    )

    # When: keywords are extracted for matching and eval grading.
    keywords = extract_keywords(jd_text)

    # Then: phrase-level requirements are preserved, not reduced to single words.
    assert "dashboard storytelling" in keywords
    assert "stakeholder communication" in keywords
