"""History and replay widgets for Streamlit."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import streamlit as st

from career_ai.legacy_history import load_legacy_history

if TYPE_CHECKING:
    from collections.abc import Sequence

    from career_ai.application import TailoringApplicationService, WorkspaceRunSummary
    from career_ai.history import HistoryEntry

SHOW_PROCESS_KEY: Final = "show_process_details"


def render_history_sidebar(
    service: TailoringApplicationService,
) -> WorkspaceRunSummary | None:
    """Render workspace run replay and legacy summaries in the sidebar."""
    with st.sidebar:
        _ = st.header("History")
        workspace_runs = service.list_workspace_runs()
        legacy_entries = load_legacy_history()
        selected = _render_workspace_runs(workspace_runs)
        _render_legacy_entries(legacy_entries)
        return selected


def render_run_replay(run: WorkspaceRunSummary) -> None:
    """Render a selected workspace run manifest without fabricating provenance."""
    _ = st.divider()
    _ = st.subheader(f"Run {run.run_id}")
    _ = st.write(f"State: {run.state.value}")
    _ = st.write(f"Template type: {run.template_type or 'unknown'}")
    _ = st.write(f"Safety/Adequacy: {run.state.value}")
    if run.render_manifests and _show_process_details():
        with st.expander("Process details", expanded=False):
            _ = st.json([manifest.model_dump(mode="json") for manifest in run.render_manifests])


def _render_workspace_runs(
    runs: tuple[WorkspaceRunSummary, ...],
) -> WorkspaceRunSummary | None:
    selected_run_id = _selected_run_id()
    selected: WorkspaceRunSummary | None = None
    for run in runs:
        with st.expander(f"{run.run_id} - {run.state.value}"):
            _ = st.caption(f"Template type: {run.template_type or 'unknown'}")
            _ = st.caption(f"Template hash: {run.template_hash or 'unavailable'}")
            if st.button("Replay run", key=f"run-{run.run_id}"):
                st.session_state["selected_run_id"] = run.run_id
                selected_run_id = run.run_id
            if run.run_id == selected_run_id:
                selected = run
    return selected


def _render_legacy_entries(entries: Sequence[HistoryEntry]) -> None:
    _ = st.subheader("Legacy")
    if not entries:
        _ = st.caption("No legacy history.")
        return
    for entry in entries:
        with st.expander(f"legacy: {entry.role_title} - {entry.match_score}"):
            _ = st.caption("legacy summary only")
            _ = st.write(f"Missing: {', '.join(entry.missing_keywords) or 'None'}")


def _selected_run_id() -> str | None:
    selected = st.session_state.get("selected_run_id")
    if isinstance(selected, str) and selected:
        return selected
    return None


def _show_process_details() -> bool:
    return st.session_state.get(SHOW_PROCESS_KEY, False) is True
