"""Workspace-bound file persistence helpers for the Streamlit app."""

from __future__ import annotations

from pathlib import Path, PureWindowsPath
from typing import TYPE_CHECKING, Final

import streamlit as st

from career_ai.jd_fetcher import FetchFailure, FetchSuccess, fetch_job_description_from_url
from career_ai.workspace import create_workspace, resolve_workspace_path

if TYPE_CHECKING:
    from streamlit.runtime.uploaded_file_manager import UploadedFile

UPLOAD_DIR: Final = Path(".career_ai/uploads")


def safe_resume_upload_path(temp_dir: Path, uploaded_name: str) -> Path:
    """Return a temp-contained path for a user-supplied upload filename."""
    safe_name = PureWindowsPath(Path(uploaded_name).name).name or "resume.txt"
    candidate = temp_dir / safe_name
    resolved_temp = temp_dir.resolve()
    resolved_candidate = candidate.resolve()
    if resolved_candidate.parent != resolved_temp:
        return resolved_temp / "resume.txt"
    return candidate


def persist_text_or_upload(
    workspace: Path,
    upload: UploadedFile | None,
    text: str,
    fallback_name: str,
) -> Path:
    """Persist uploaded bytes or text into a workspace-owned path."""
    if upload is not None:
        return persist_upload(workspace, upload, fallback_name)
    target = resolve_workspace_path(workspace, UPLOAD_DIR / fallback_name)
    target.parent.mkdir(parents=True, exist_ok=True)
    _ = target.write_text(text or " ", encoding="utf-8")
    return target


def persist_jd(workspace: Path, jd_url: str, fallback_text: str) -> Path:
    """Persist JD text, resolving an optional URL through the hardened fetcher."""
    target = resolve_workspace_path(workspace, UPLOAD_DIR / "jd.txt")
    target.parent.mkdir(parents=True, exist_ok=True)
    jd_text = _resolve_jd_text(jd_url, fallback_text)
    _ = target.write_text(jd_text or " ", encoding="utf-8")
    return target


def persist_upload(workspace: Path, upload: UploadedFile, fallback_name: str) -> Path:
    """Persist one upload under the workspace without trusting its filename."""
    _ = create_workspace(workspace)
    safe_path = safe_resume_upload_path(Path(), fallback_name)
    target = resolve_workspace_path(workspace, UPLOAD_DIR / safe_path.name)
    target.parent.mkdir(parents=True, exist_ok=True)
    _ = target.write_bytes(upload.getbuffer().tobytes())
    return target


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
