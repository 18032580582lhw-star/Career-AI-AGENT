from dataclasses import dataclass, field
from typing import Protocol

from career_ai.agent.enforcement import RuntimePolicy
from career_ai.agent.execution_records import (
    ToolExecutionRecord,
    completed_record,
    failed_record,
    failed_record_from_missing_result,
    runtime_denied_record,
    skipped_record,
)
from career_ai.agent.models import (
    AgentAutonomyPolicy,
    AgentExecutionPolicy,
    AgentStateEvent,
    AgentStateStatus,
)
from career_ai.agent.quality import CareerQualityOptimizerOptions
from career_ai.agent.recovery import RecoveryAction, RecoveryDecider, RuleRecoveryDecider
from career_ai.agent.tool_catalog import ToolCatalog, default_tool_catalog
from career_ai.agent.tool_models import AgentToolContext, ToolCall, ToolResult, ToolStatus


class AgentToolRunner(Protocol):
    """Minimal runner contract required by the execution loop."""

    def run(self, call: ToolCall, context: AgentToolContext) -> ToolResult:
        """Execute one tool call."""
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class AgentRuntimeOptions:
    """Optional runtime dependencies for the local execution loop."""

    tool_runner: AgentToolRunner | None = None
    execution_policy: AgentExecutionPolicy = field(default_factory=AgentExecutionPolicy)
    recovery_decider: RecoveryDecider = field(default_factory=RuleRecoveryDecider)
    tool_catalog: ToolCatalog = field(default_factory=default_tool_catalog)
    autonomy_policy: AgentAutonomyPolicy = field(default_factory=AgentAutonomyPolicy)
    runtime_policy: RuntimePolicy = field(default_factory=RuntimePolicy)
    quality_optimizer: CareerQualityOptimizerOptions = field(
        default_factory=CareerQualityOptimizerOptions,
    )

    def tool_execution_options(self) -> "ToolExecutionOptions":
        """Build single-call execution options from runtime settings."""
        return ToolExecutionOptions(
            execution_policy=self.execution_policy,
            recovery_decider=self.recovery_decider,
            runtime_policy=self.runtime_policy,
        )


@dataclass(frozen=True, slots=True)
class ToolExecutionOptions:
    """Policies used by one tool execution boundary."""

    execution_policy: AgentExecutionPolicy = field(default_factory=AgentExecutionPolicy)
    recovery_decider: RecoveryDecider = field(default_factory=RuleRecoveryDecider)
    runtime_policy: RuntimePolicy = field(default_factory=RuntimePolicy)


def execute_tool_call(
    *,
    call: ToolCall,
    context: AgentToolContext,
    runner: AgentToolRunner,
    options: ToolExecutionOptions | None = None,
) -> ToolExecutionRecord:
    """Run one tool call with recoverable retry and skip handling."""
    events: list[AgentStateEvent] = []
    execution_options = options or ToolExecutionOptions()
    policy = execution_options.execution_policy
    recovery_decider = execution_options.recovery_decider
    enforcement = execution_options.runtime_policy
    pre_check = enforcement.enforce_pre_tool_call(call=call, context=context)
    enforcement_events = [pre_check.event]
    if not pre_check.allowed_to_run:
        return runtime_denied_record(
            call=call,
            events=events,
            enforcement_events=enforcement_events,
            message=pre_check.event.reason,
        )
    enforced_call = pre_check.call
    last_result: ToolResult | None = None
    for attempt in range(1, policy.max_tool_attempts + 1):
        events.append(_running_event(enforced_call))
        result = runner.run(enforced_call, context)
        enforcement_events.append(
            enforcement.enforce_post_tool_call(call=enforced_call, result=result),
        )
        match result.status:
            case ToolStatus.SUCCESS:
                message = _success_message(result.message, attempt)
                events.append(
                    AgentStateEvent(
                        status=AgentStateStatus.TOOL_COMPLETED,
                        tool_name=enforced_call.name.value,
                        message=message,
                    ),
                )
                return completed_record(
                    call=enforced_call,
                    events=events,
                    enforcement_events=enforcement_events,
                    result=result,
                    message=message,
                )
            case ToolStatus.FAILURE:
                last_result = result
                events.append(_failure_event(enforced_call, result.message))
                decision = recovery_decider.decide(
                    call=enforced_call,
                    result=result,
                    attempt=attempt,
                    max_attempts=policy.max_tool_attempts,
                )
                events.append(_decision_event(enforced_call, decision.action, decision.reason))
                match decision.action:
                    case RecoveryAction.RETRY:
                        if result.recoverable and attempt < policy.max_tool_attempts:
                            events.append(_recovering_event(enforced_call, attempt + 1))
                            continue
                        return failed_record(
                            call=enforced_call,
                            events=events,
                            enforcement_events=enforcement_events,
                            result=result,
                        )
                    case RecoveryAction.SKIP:
                        return skipped_record(
                            call=enforced_call,
                            events=events,
                            enforcement_events=enforcement_events,
                            message=f"Model decided to skip: {decision.reason}",
                        )
                    case RecoveryAction.ABORT:
                        return failed_record(
                            call=enforced_call,
                            events=events,
                            enforcement_events=enforcement_events,
                            result=result.model_copy(update={"message": decision.reason}),
                        )
    return failed_record_from_missing_result(
        call=enforced_call,
        events=events,
        enforcement_events=enforcement_events,
        result=last_result,
    )


def _running_event(call: ToolCall) -> AgentStateEvent:
    return AgentStateEvent(
        status=AgentStateStatus.RUNNING_TOOL,
        tool_name=call.name.value,
        message="Running tool.",
    )


def _failure_event(call: ToolCall, message: str) -> AgentStateEvent:
    return AgentStateEvent(
        status=AgentStateStatus.FAILED_RECOVERABLE,
        tool_name=call.name.value,
        message=message,
    )


def _recovering_event(call: ToolCall, next_attempt: int) -> AgentStateEvent:
    return AgentStateEvent(
        status=AgentStateStatus.RECOVERING,
        tool_name=call.name.value,
        message=f"Retrying tool on attempt {next_attempt}.",
    )


def _decision_event(call: ToolCall, action: RecoveryAction, reason: str) -> AgentStateEvent:
    return AgentStateEvent(
        status=AgentStateStatus.RECOVERY_DECIDED,
        tool_name=call.name.value,
        message=f"{action.value}: {reason}",
    )


def _success_message(message: str, attempt: int) -> str:
    if attempt == 1:
        return message
    return f"{message} Recovered after {attempt} attempts."
