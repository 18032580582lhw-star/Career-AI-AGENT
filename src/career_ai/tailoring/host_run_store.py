"""Compatibility exports for the host-proposal run workflow."""

from career_ai.tailoring.host_run_models import (
    RENDER_STALE_EXIT_CODE,
    HostPrepareResult,
    HostRenderFormat,
    HostRenderItem,
    HostRenderResult,
    HostRunError,
    HostRunRequest,
    HostValidationResult,
)
from career_ai.tailoring.host_run_persistence import load_run_context
from career_ai.tailoring.host_run_prepare import prepare_host_run
from career_ai.tailoring.host_run_render import render_host_run
from career_ai.tailoring.host_run_validation import (
    confirm_host_fact,
    save_accepted_run,
    tailor_with_api,
    validate_host_draft,
)

__all__ = [
    "RENDER_STALE_EXIT_CODE",
    "HostPrepareResult",
    "HostRenderFormat",
    "HostRenderItem",
    "HostRenderResult",
    "HostRunError",
    "HostRunRequest",
    "HostValidationResult",
    "confirm_host_fact",
    "load_run_context",
    "prepare_host_run",
    "render_host_run",
    "save_accepted_run",
    "tailor_with_api",
    "validate_host_draft",
]
