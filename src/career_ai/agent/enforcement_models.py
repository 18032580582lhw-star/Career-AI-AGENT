from enum import StrEnum, unique
from typing import Final

from pydantic import Field

from career_ai.agent.tool_models import ToolCall
from career_ai.models import FrozenModel

DEFAULT_RUNTIME_POLICY_VERSION: Final[str] = "policy-v1"


@unique
class RuntimePolicyDecision(StrEnum):
    """Execution-time policy decision values."""

    ALLOWED = "allowed"
    DENIED = "denied"
    REDACTED = "redacted"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    UNSUPPORTED = "unsupported"


@unique
class RuntimeBoundary(StrEnum):
    """Runtime boundary checked by the enforcement layer."""

    PRE_TOOL_CALL = "pre-tool-call"
    POST_TOOL_CALL = "post-tool-call"
    MEMORY_WRITE = "memory-write"
    NETWORK_FETCH = "network-fetch"
    DOCUMENT_EXPORT = "document-export"
    EXTERNAL_ACTION = "external-action"


class RuntimeEnforcementEvent(FrozenModel):
    """Trace-compatible runtime enforcement event."""

    policy_version: str = Field(min_length=1)
    boundary: RuntimeBoundary
    decision: RuntimePolicyDecision
    reason: str = Field(min_length=1)
    tool_name: str = ""


class RuntimePolicyCheck(FrozenModel):
    """Runtime decision plus the possibly sanitized tool call."""

    call: ToolCall
    event: RuntimeEnforcementEvent
    allowed_to_run: bool
