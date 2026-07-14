from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

import streamlit as st

from career_ai.application import TailoringApplicationService
from career_ai.streamlit_app.history_panel import render_history_sidebar, render_run_replay
from career_ai.streamlit_app.uploads import persist_jd, persist_text_or_upload, persist_upload
from career_ai.tailoring.host_run_models import HostRenderFormat, HostRunError
from career_ai.tailoring.manifest_contracts import RunState

if TYPE_CHECKING:
    from streamlit.runtime.uploaded_file_manager import UploadedFile

    from career_ai.rendering.latex import LatexTemplateProfile
    from career_ai.tailoring.host_run_models import (
        HostPrepareResult,
        HostRenderResult,
        HostValidationResult,
    )

DEFAULT_WORKSPACE: Final = Path()
OUTPUT_DETAIL_KEY: Final = "output_detail_mode"
SHOW_PROCESS_KEY: Final = "show_process_details"
RESULT_ONLY_LABEL: Final = "Result only"
RESULT_PROCESS_LABEL: Final = "Result + process"


@dataclass(frozen=True, slots=True)
class _PrepareInputs:
    resume_upload: UploadedFile | None
    resume_text: str
    jd_url: str
    jd_text: str
    latex_template: UploadedFile | None


def main() -> None:
    """Run the unified Streamlit tailoring app."""
    st.set_page_config(page_title="AI Career Intelligence Suite", layout="wide")
    _render_theme_css()
    _ = st.title("AI Career Intelligence Suite")
    _render_output_preferences()
    service = TailoringApplicationService(workspace=DEFAULT_WORKSPACE)
    service.initialize()
    selected_run = render_history_sidebar(service)
    _render_prepare_flow(service)
    if selected_run is not None:
        render_run_replay(selected_run)


def _render_prepare_flow(service: TailoringApplicationService) -> None:
    _ = st.header("Resume Tailoring")
    resume_column, jd_column, latex_column = st.columns(3)
    with resume_column:
        _ = st.subheader("Resume")
        uploaded_resume = st.file_uploader("Resume file", type=["txt", "pdf", "docx"])
        resume_text = st.text_area("Resume text", height=220)
    with jd_column:
        _ = st.subheader("Job Description")
        jd_url = st.text_input("JD URL")
        jd_text = st.text_area("Job description", height=220)
    with latex_column:
        _ = st.subheader("LaTeX")
        uploaded_template = st.file_uploader("resume.tex template", type=["tex"])
        _render_latex_inspection(uploaded_template)
    if st.button("Prepare", type="primary"):
        inputs = _PrepareInputs(
            resume_upload=uploaded_resume,
            resume_text=resume_text,
            jd_url=jd_url,
            jd_text=jd_text,
            latex_template=uploaded_template,
        )
        _prepare_from_inputs(service, inputs)
    _render_generation_controls(service)
    _render_renderer_controls(service)


def _prepare_from_inputs(
    service: TailoringApplicationService,
    inputs: _PrepareInputs,
) -> None:
    workspace = service.workspace
    resume_file = persist_text_or_upload(
        workspace,
        inputs.resume_upload,
        inputs.resume_text,
        "resume.txt",
    )
    jd_file = persist_jd(workspace, inputs.jd_url, inputs.jd_text)
    template_file = (
        persist_upload(workspace, inputs.latex_template, "resume.tex")
        if inputs.latex_template is not None
        else None
    )
    result = service.prepare(
        resume_file=resume_file,
        jd_file=jd_file,
        latex_template=template_file,
        language="en",
    )
    st.session_state["selected_run_id"] = result.run_id
    st.session_state["last_validation_state"] = None
    _ = st.success(f"Prepared run {result.run_id}")
    _render_process_json(result)


def _render_latex_inspection(uploaded_template: UploadedFile | None) -> None:
    _ = st.caption("Template type: system unless a resume.tex template is uploaded")
    _ = st.caption("Tectonic/XeLaTeX status is checked by career-ai-agent doctor")
    _ = st.caption("Compile error summary appears after LaTeX PDF rendering")
    if uploaded_template is None:
        _ = st.info("Inspect status: no user template uploaded")
        return
    template_path = persist_upload(DEFAULT_WORKSPACE, uploaded_template, "resume.tex")
    profile = TailoringApplicationService(workspace=DEFAULT_WORKSPACE).inspect_latex_template(
        template_path,
    )
    _render_latex_profile(profile)


def _render_latex_profile(profile: LatexTemplateProfile) -> None:
    _ = st.write(f"Inspect status: {profile.documentclass}")
    _ = st.write(f"Section mapping: {len(profile.section_mappings)} mapped sections")
    _ = st.write(f"Unsafe findings: {len(profile.unsafe_findings)}")
    if profile.requires_mapping_confirmation:
        _ = st.checkbox("Confirm section mapping")
    if profile.unsafe_findings:
        _ = st.json([finding.model_dump(mode="json") for finding in profile.unsafe_findings])


def _render_generation_controls(service: TailoringApplicationService) -> None:
    run_id = _selected_run_id()
    _ = st.subheader("Proposal")
    proposal_file = st.file_uploader("Host proposal JSON", type=["json"])
    generate_column, validate_column = st.columns(2)
    with generate_column:
        if st.button("Generate with API", disabled=run_id is None):
            _run_api_generation(service, run_id)
    with validate_column:
        if st.button("Validate host proposal", disabled=run_id is None or proposal_file is None):
            if proposal_file is None:
                return
            proposal_path = persist_upload(service.workspace, proposal_file, "proposal.json")
            _run_host_validation(service, run_id, proposal_path)
    _render_trust_panel()


def _run_api_generation(service: TailoringApplicationService, run_id: str | None) -> None:
    if run_id is None:
        return
    result = service.tailor_with_api(run_id=run_id)
    st.session_state["last_validation_state"] = result.state.value
    _ = st.success(f"Three strategies compared; state: {result.state.value}")
    _render_process_json(result)


def _run_host_validation(
    service: TailoringApplicationService,
    run_id: str | None,
    proposal_path: Path,
) -> None:
    if run_id is None:
        return
    try:
        result = service.validate(run_id=run_id, proposal_file=proposal_path)
    except HostRunError as error:
        _ = st.error(str(error))
        return
    st.session_state["last_validation_state"] = result.state.value
    _ = st.success(f"Validation state: {result.state.value}")
    _render_process_json(result)


def _render_renderer_controls(service: TailoringApplicationService) -> None:
    run_id = _selected_run_id()
    state = st.session_state.get("last_validation_state")
    accepted = isinstance(state, str) and state == RunState.ACCEPTED.value
    _ = st.subheader("Render")
    format_choice = st.selectbox(
        "Output format",
        [item.value for item in HostRenderFormat],
        index=0,
    )
    if st.button("Render", disabled=run_id is None or not accepted):
        result = service.render(
            run_id=run_id or "",
            render_format=HostRenderFormat(format_choice),
        )
        _render_render_result(result)
        _render_process_json(result)


def _render_trust_panel() -> None:
    _ = st.subheader("Safety/Adequacy")
    state = st.session_state.get("last_validation_state")
    if state is None:
        _ = st.info("Prepare a run, then generate or validate a proposal.")
        return
    if state == RunState.ACCEPTED.value:
        _ = st.success("Accepted; renderer buttons are enabled.")
        return
    _ = st.warning(f"Current validation state: {state}. Renderer buttons remain disabled.")


def _selected_run_id() -> str | None:
    selected = st.session_state.get("selected_run_id")
    if isinstance(selected, str) and selected:
        return selected
    return None


def _render_output_preferences() -> None:
    selected = st.radio(
        "Output detail",
        (RESULT_ONLY_LABEL, RESULT_PROCESS_LABEL),
        index=0,
        horizontal=True,
        key=OUTPUT_DETAIL_KEY,
    )
    st.session_state[SHOW_PROCESS_KEY] = selected == RESULT_PROCESS_LABEL


def _show_process_details() -> bool:
    return st.session_state.get(SHOW_PROCESS_KEY, False) is True


def _render_process_json(
    result: HostPrepareResult | HostValidationResult | HostRenderResult,
) -> None:
    if _show_process_details():
        with st.expander("Process details", expanded=False):
            _ = st.json(result.model_dump(mode="json"))


def _render_render_result(result: HostRenderResult) -> None:
    rendered_count = sum(1 for item in result.results if item.status == "rendered")
    _ = st.success(
        f"Rendered {rendered_count} of {len(result.results)} formats for run {result.run_id}",
    )
    for item in result.results:
        artifact_paths = ", ".join(artifact.path for artifact in item.artifacts)
        suffix = f": {artifact_paths}" if artifact_paths else ""
        _ = st.write(f"{item.format.value}: {item.status}{suffix}")


def _render_theme_css() -> None:
    theme_path = Path("static/app_theme.css")
    if theme_path.exists():
        theme_css = theme_path.read_text(encoding="utf-8")
        _ = st.markdown(f"<style>{theme_css}</style>", unsafe_allow_html=True)
