from career_ai.agent.enforcement_boundaries import reason_boundary_label
from career_ai.agent.enforcement_models import (
    RuntimeBoundary,
    RuntimeEnforcementEvent,
    RuntimePolicyCheck,
    RuntimePolicyDecision,
)
from career_ai.agent.tool_models import ToolCall, ToolName, ToolResult, ToolStatus


def external_action_event(*, policy_version: str, action_name: str) -> RuntimeEnforcementEvent:
    """Create a denial event for an external action request."""
    normalized_action = action_name.strip() or "external action"
    return make_event(
        policy_version=policy_version,
        boundary=RuntimeBoundary.EXTERNAL_ACTION,
        decision=RuntimePolicyDecision.DENIED,
        reason=f"{normalized_action} is outside the local analysis boundary.",
        tool_name=normalized_action,
    )


def post_fetch_event(
    *,
    policy_version: str,
    call: ToolCall,
    result: ToolResult,
) -> RuntimeEnforcementEvent:
    """Create the post-fetch enforcement event from the safe fetch outcome."""
    match result.status:
        case ToolStatus.SUCCESS:
            return make_event(
                policy_version=policy_version,
                boundary=RuntimeBoundary.POST_TOOL_CALL,
                decision=RuntimePolicyDecision.ALLOWED,
                reason="fetch_jd completed runtime post-tool checks.",
                tool_name=call.name,
            )
        case ToolStatus.FAILURE:
            if "not allowed" in result.message.lower():
                return make_event(
                    policy_version=policy_version,
                    boundary=RuntimeBoundary.NETWORK_FETCH,
                    decision=RuntimePolicyDecision.DENIED,
                    reason="fetch_jd safe fetch boundary denied the target.",
                    tool_name=call.name,
                )
            return make_event(
                policy_version=policy_version,
                boundary=RuntimeBoundary.POST_TOOL_CALL,
                decision=RuntimePolicyDecision.ALLOWED,
                reason="fetch_jd failure remained inside the safe fetch boundary.",
                tool_name=call.name,
            )


def allowed_check(
    *,
    policy_version: str,
    call: ToolCall,
    boundary: RuntimeBoundary,
) -> RuntimePolicyCheck:
    """Create an allowed check result for a tool boundary."""
    boundary_label = reason_boundary_label(boundary)
    return RuntimePolicyCheck(
        call=call,
        event=make_event(
            policy_version=policy_version,
            boundary=boundary,
            decision=RuntimePolicyDecision.ALLOWED,
            reason=f"{call.name.value} passed runtime {boundary_label} checks.",
            tool_name=call.name,
        ),
        allowed_to_run=True,
    )


def denied_check(
    *,
    policy_version: str,
    call: ToolCall,
    boundary: RuntimeBoundary,
    reason: str,
) -> RuntimePolicyCheck:
    """Create a denied check result for a tool boundary."""
    return RuntimePolicyCheck(
        call=call,
        event=make_event(
            policy_version=policy_version,
            boundary=boundary,
            decision=RuntimePolicyDecision.DENIED,
            reason=reason,
            tool_name=call.name,
        ),
        allowed_to_run=False,
    )


def make_event(
    *,
    policy_version: str,
    boundary: RuntimeBoundary,
    decision: RuntimePolicyDecision,
    reason: str,
    tool_name: ToolName | str | None = None,
) -> RuntimeEnforcementEvent:
    """Create a trace-compatible runtime enforcement event."""
    return RuntimeEnforcementEvent(
        policy_version=policy_version,
        boundary=boundary,
        decision=decision,
        reason=reason,
        tool_name=str(tool_name or ""),
    )
