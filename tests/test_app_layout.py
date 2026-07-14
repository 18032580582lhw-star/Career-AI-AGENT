from pathlib import Path

APP_ENTRYPOINT = Path("app.py")
APP_SOURCE = Path("src/career_ai/streamlit_app/main.py")
HISTORY_SOURCE = Path("src/career_ai/streamlit_app/history_panel.py")


def test_main_input_layout_keeps_resume_and_jd_on_canvas() -> None:
    # Given the Streamlit app entrypoint source.
    source = APP_SOURCE.read_text(encoding="utf-8")

    # When the input layout is inspected.
    uses_columns = "st.columns" in source

    # Then resume and JD inputs should live in the main canvas.
    assert uses_columns
    assert 'st.file_uploader("Resume file"' in source
    assert 'st.text_area("Job description"' in source


def test_sidebar_is_reserved_for_history() -> None:
    # Given the Streamlit app entrypoint source.
    source = HISTORY_SOURCE.read_text(encoding="utf-8")

    # When the sidebar usage is inspected.
    uses_sidebar = "with st.sidebar:" in source

    # Then the sidebar should be a history surface, not the input form.
    assert uses_sidebar
    assert "History" in source


def test_analysis_results_render_through_selected_history_only() -> None:
    # Given the Streamlit app entrypoint source.
    source = APP_SOURCE.read_text(encoding="utf-8")

    # When the analyze flow is inspected.
    direct_report_render = "_render_report(report, prompt_result)" in source

    # Then new tailoring runs should be selected through shared run state.
    assert not direct_report_render
    assert "TailoringApplicationService" in source
    assert "selected_run_id" in source


def test_analysis_results_surface_agent_trust_evidence() -> None:
    # Given the Streamlit app entrypoint source.
    source = APP_SOURCE.read_text(encoding="utf-8")

    # When the results surface is inspected.
    expected_signals = (
        "Safety/Adequacy",
        "Template type",
        "Inspect status",
        "Section mapping",
        "Unsafe findings",
        "Tectonic/XeLaTeX",
        "Compile error summary",
    )

    # Then it should render evidence from the shared tailoring state.
    assert "run_career_agent" not in source
    assert "_render_trust_panel" in source
    for signal in expected_signals:
        assert signal in source


def test_output_details_are_user_selectable_and_result_first() -> None:
    # Given the Streamlit app source.
    source = APP_SOURCE.read_text(encoding="utf-8")

    # When output rendering is inspected.
    has_result_only_default = '"Result only"' in source and "index=0" in source
    has_process_option = '"Result + process"' in source
    process_json_call_count = source.count("st.json(result.model_dump")

    # Then users can choose whether process JSON is shown after the result.
    assert has_result_only_default
    assert has_process_option
    assert "_render_process_json" in source
    assert process_json_call_count == 1


def test_app_py_is_a_thin_streamlit_entrypoint() -> None:
    # Given the root app file used by Streamlit.
    source = APP_ENTRYPOINT.read_text(encoding="utf-8")

    # When it is inspected.
    pure_lines = [
        line
        for line in source.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

    # Then it delegates to the shared Streamlit package.
    assert len(pure_lines) <= 8
    assert "career_ai.streamlit_app.main" in source
