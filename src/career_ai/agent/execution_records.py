from pydantic import Field

from career_ai.agent.enforcement_models import RuntimeEnforcementEvent
from career_ai.agent.models import AgentStateEvent, AgentStateStatus, AgentStep, AgentStepStatus
from career_ai.agent.tool_models import ToolCall, ToolName, ToolResult, ToolStatus
from career_ai.models import FrozenModel, PromptHarnessResult


class ToolExecutionRecord(FrozenModel):
    """Recorded outcome for one tool call execution loop."""

    step: AgentStep
    events: list[AgentStateEvent]
    enforcement_events: list[RuntimeEnforcementEvent] = Field(default_factory=list)
    result: ToolResult | None = None


def completed_record(
    *,
    call: ToolCall,
    events: list[AgentStateEvent],
    enforcement_events: list[RuntimeEnforcementEvent],
    result: ToolResult,
    message: str,
) -> ToolExecutionRecord:
    """Build a completed tool execution record."""
    return ToolExecutionRecord(
        step=AgentStep(
            name=call.name.value,
            status=AgentStepStatus.COMPLETED,
            message=message,
        ),
        events=events,
        enforcement_events=enforcement_events,
        result=result,
    )


def failed_record(
    *,
    call: ToolCall,
    events: list[AgentStateEvent],
    enforcement_events: list[RuntimeEnforcementEvent],
    result: ToolResult,
) -> ToolExecutionRecord:
    """Build a failed or skipped record based on tool criticality."""
    if _is_critical_tool(call.name):
        return ToolExecutionRecord(
            step=AgentStep(
                name=call.name.value,
                status=AgentStepStatus.FAILED_RECOVERABLE,
                message=result.message,
            ),
            events=events,
            enforcement_events=enforcement_events,
            result=result,
        )
    return skipped_record(
        call=call,
        events=events,
        enforcement_events=enforcement_events,
        message=result.message,
    )


def failed_record_from_missing_result(
    *,
    call: ToolCall,
    events: list[AgentStateEvent],
    enforcement_events: list[RuntimeEnforcementEvent],
    result: ToolResult | None,
) -> ToolExecutionRecord:
    """Build a failure record when the retry loop exits without success."""
    if result is not None:
        return failed_record(
            call=call,
            events=events,
            enforcement_events=enforcement_events,
            result=result,
        )
    return skipped_record(
        call=call,
        events=events,
        enforcement_events=enforcement_events,
        message="Tool returned no result.",
    )


def runtime_denied_record(
    *,
    call: ToolCall,
    events: list[AgentStateEvent],
    enforcement_events: list[RuntimeEnforcementEvent],
    message: str,
) -> ToolExecutionRecord:
    """Build a record for a tool call denied before implementation execution."""
    result = ToolResult(
        name=call.name,
        status=ToolStatus.FAILURE,
        message=message,
        recoverable=True,
    )
    return failed_record(
        call=call,
        events=events,
        enforcement_events=enforcement_events,
        result=result,
    )


def skipped_record(
    *,
    call: ToolCall,
    events: list[AgentStateEvent],
    enforcement_events: list[RuntimeEnforcementEvent],
    message: str,
) -> ToolExecutionRecord:
    """Build a skipped record and its safe fallback result."""
    events.append(
        AgentStateEvent(
            status=AgentStateStatus.TOOL_SKIPPED,
            tool_name=call.name.value,
            message=message,
        ),
    )
    return ToolExecutionRecord(
        step=AgentStep(
            name=call.name.value,
            status=AgentStepStatus.SKIPPED,
            message=message,
        ),
        events=events,
        enforcement_events=enforcement_events,
        result=_fallback_result(call.name, message),
    )


def _fallback_result(name: ToolName, message: str) -> ToolResult | None:
    match name:
        case ToolName.COMPARE_PROMPT_STRATEGIES:
            return ToolResult(
                name=name,
                status=ToolStatus.FAILURE,
                message=message,
                recoverable=True,
                prompt_result=PromptHarnessResult(strategies=[], best_strategy_name=""),
            )
        case (
            ToolName.FETCH_JD
            | ToolName.EXTRACT_RESUME
            | ToolName.ANALYZE_CAREER_FIT
            | ToolName.EXPORT_RESUME_DOCX
            | ToolName.EXPORT_COVER_LETTER_DOCX
            | ToolName.SAVE_MEMORY_SUMMARY
        ):
            return None


def _is_critical_tool(name: ToolName) -> bool:
    match name:
        case ToolName.ANALYZE_CAREER_FIT:
            return True
        case (
            ToolName.FETCH_JD
            | ToolName.EXTRACT_RESUME
            | ToolName.COMPARE_PROMPT_STRATEGIES
            | ToolName.EXPORT_RESUME_DOCX
            | ToolName.EXPORT_COVER_LETTER_DOCX
            | ToolName.SAVE_MEMORY_SUMMARY
        ):
            return False
