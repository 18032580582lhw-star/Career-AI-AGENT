from pathlib import Path, PureWindowsPath
from tempfile import TemporaryDirectory

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from career_ai.analysis import analyze_career_fit, get_sample_inputs
from career_ai.exporters import build_cover_letter_docx, build_resume_docx
from career_ai.jd_fetcher import FetchFailure, FetchSuccess, fetch_job_description_from_url
from career_ai.models import CareerFitReport, PromptHarnessResult
from career_ai.prompt_harness import compare_prompt_strategies
from career_ai.text_processing import extract_resume_text


def main() -> None:
    """Run the Streamlit MVP app."""
    st.set_page_config(page_title="AI Career Intelligence Suite", layout="wide")
    _ = st.title("AI Career Intelligence Suite")

    sample_resume, sample_jd = get_sample_inputs()
    with st.sidebar:
        _ = st.header("Inputs")
        uploaded_resume = st.file_uploader("Resume file", type=["txt", "pdf", "docx"])
        resume_text = st.text_area("Resume text", value=sample_resume, height=240)
        jd_url = st.text_input("JD URL")
        jd_text = st.text_area("Job description", value=sample_jd, height=240)
        run_analysis = st.button("Analyze", type="primary")

    resolved_resume = _resolve_resume_text(uploaded_resume, resume_text)
    resolved_jd = _resolve_jd_text(jd_url, jd_text)

    if run_analysis:
        report = analyze_career_fit(resume_text=resolved_resume, jd_text=resolved_jd)
        prompt_result = compare_prompt_strategies(
            prompt_dir=Path("prompts"),
            resume_text=resolved_resume,
            jd_text=resolved_jd,
        )
        _render_report(report, prompt_result)


def _resolve_resume_text(uploaded_resume: UploadedFile | None, fallback_text: str) -> str:
    if uploaded_resume is None:
        return fallback_text
    with TemporaryDirectory() as temp_dir:
        upload_bytes = uploaded_resume.getbuffer().tobytes()
        path = safe_resume_upload_path(Path(temp_dir), _resume_upload_filename(upload_bytes))
        _ = path.write_bytes(upload_bytes)
        extracted = extract_resume_text(path)
    return extracted or fallback_text


def _resume_upload_filename(upload_bytes: bytes) -> str:
    if upload_bytes.startswith(b"%PDF"):
        return "resume.pdf"
    if upload_bytes.startswith(b"PK"):
        return "resume.docx"
    return "resume.txt"


def safe_resume_upload_path(temp_dir: Path, uploaded_name: str) -> Path:
    """Return a temp-contained path for a user-supplied upload filename."""
    safe_name = PureWindowsPath(Path(uploaded_name).name).name or "resume.txt"
    candidate = temp_dir / safe_name
    resolved_temp = temp_dir.resolve()
    resolved_candidate = candidate.resolve()
    if resolved_candidate.parent != resolved_temp:
        return resolved_temp / "resume.txt"
    return candidate


def _resolve_jd_text(jd_url: str, fallback_text: str) -> str:
    if not jd_url.strip():
        return fallback_text
    result = fetch_job_description_from_url(jd_url.strip())
    match result:
        case FetchSuccess(text=text):
            return text
        case FetchFailure(message=message):
            _ = st.warning(f"Could not fetch JD URL: {message}")
            return fallback_text


def _render_report(report: CareerFitReport, prompt_result: PromptHarnessResult) -> None:
    tabs = st.tabs(
        [
            "JD Analysis",
            "Match Score",
            "Resume Suggestions",
            "Cover Letter",
            "Prompt Evaluation",
            "Export",
        ],
    )
    with tabs[0]:
        _ = st.subheader(report.jd_analysis.role_title)
        _ = st.write(f"Seniority: {report.jd_analysis.seniority}")
        _ = st.write(report.jd_analysis.requirements)
    with tabs[1]:
        _ = st.metric("Match score", report.match.score)
        _ = st.write("Matched:", ", ".join(report.match.matched_keywords) or "None yet")
        _ = st.write("Missing:", ", ".join(report.match.missing_keywords) or "None")
    with tabs[2]:
        for suggestion in report.bullet_suggestions:
            _ = st.markdown(f"**Original:** {suggestion.original}")
            _ = st.markdown(f"**Improved:** {suggestion.improved}")
    with tabs[3]:
        _ = st.text_area("Cover letter draft", value=report.cover_letter_draft, height=320)
    with tabs[4]:
        for strategy in prompt_result.strategies:
            _ = st.write(f"{strategy.name}: {strategy.score}")
        _ = st.success(f"Best strategy: {prompt_result.best_strategy_name}")
    with tabs[5]:
        _render_exports(report)


def _render_exports(report: CareerFitReport) -> None:
    with TemporaryDirectory() as temp_dir:
        resume_path = build_resume_docx(report, Path(temp_dir) / "tailored-resume.docx")
        cover_path = build_cover_letter_docx(report, Path(temp_dir) / "cover-letter.docx")
        _ = st.download_button(
            "Download tailored resume",
            data=resume_path.read_bytes(),
            file_name="tailored-resume.docx",
        )
        _ = st.download_button(
            "Download cover letter",
            data=cover_path.read_bytes(),
            file_name="cover-letter.docx",
        )


if __name__ == "__main__":
    main()
