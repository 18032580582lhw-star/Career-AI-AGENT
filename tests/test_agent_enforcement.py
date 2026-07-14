from pathlib import Path

from career_ai.agent.enforcement import RuntimePolicy
from career_ai.agent.enforcement_models import (
    RuntimeBoundary,
    RuntimePolicyDecision,
)
from career_ai.agent.execution_loop import ToolExecutionOptions, execute_tool_call
from career_ai.agent.models import AgentExecutionPolicy, AgentStepStatus
from career_ai.agent.recovery import RuleRecoveryDecider
from career_ai.agent.tools import (
    AgentToolContext,
    AnalyzeCareerFitInput,
    ComparePromptStrategiesInput,
    FetchJDInput,
    SaveMemorySummaryInput,
    ToolCall,
    ToolName,
    ToolResult,
    ToolStatus,
    default_tool_registry,
)


def test_execute_tool_call_denies_mismatched_arguments_before_runner() -> None:
    # Given: a planner-bypassed tool call whose arguments belong to another tool.
    runner = SpyRunner()
    call = ToolCall(
        name=ToolName.FETCH_JD,
        arguments=ComparePromptStrategiesInput(
            resume_text="resume",
            jd_text="jd",
            prompt_dir=Path("prompts"),
        ),
    )

    # When: the runtime execution boundary receives the unsafe call.
    record = execute_tool_call(
        call=call,
        context=AgentToolContext(prompt_dir=Path("prompts")),
        runner=runner,
        options=ToolExecutionOptions(
            execution_policy=AgentExecutionPolicy(),
            recovery_decider=RuleRecoveryDecider(),
            runtime_policy=RuntimePolicy(),
        ),
    )

    # Then: the call is denied before any tool implementation can run.
    assert runner.call_count == 0
    assert record.step.status == AgentStepStatus.SKIPPED
    assert record.enforcement_events[0].boundary == RuntimeBoundary.PRE_TOOL_CALL
    assert record.enforcement_events[0].decision == RuntimePolicyDecision.DENIED


def test_execute_tool_call_redacts_unsafe_memory_write_before_storage() -> None:
    # Given: a memory write with allowed fields but unsafe sensitive fragments.
    call = ToolCall(
        name=ToolName.SAVE_MEMORY_SUMMARY,
        arguments=SaveMemorySummaryInput(
            role_title="AI Analyst jane@example.com C:\\Users\\Jane\\resume.pdf",
            match_score=82,
            missing_keywords=["python", "phone 555-123-4567"],
        ),
    )

    # When: the save-memory tool runs through runtime enforcement.
    record = execute_tool_call(
        call=call,
        context=AgentToolContext(prompt_dir=Path("prompts")),
        runner=default_tool_registry(),
        options=ToolExecutionOptions(
            execution_policy=AgentExecutionPolicy(),
            recovery_decider=RuleRecoveryDecider(),
            runtime_policy=RuntimePolicy(),
        ),
    )

    # Then: storage receives a redacted summary and an enforcement event is emitted.
    assert record.step.status == AgentStepStatus.COMPLETED
    assert record.result is not None
    assert record.result.memory_summary is not None
    stored_text = " ".join(
        [
            record.result.memory_summary.role_title,
            *record.result.memory_summary.missing_keywords,
        ],
    )
    assert "jane@example.com" not in stored_text
    assert "555-123-4567" not in stored_text
    assert "C:\\Users\\Jane" not in stored_text
    assert any(
        event.boundary == RuntimeBoundary.MEMORY_WRITE
        and event.decision == RuntimePolicyDecision.REDACTED
        for event in record.enforcement_events
    )


def test_execute_tool_call_denies_unsafe_network_fetch_target_before_runner() -> None:
    # Given: a network fetch aimed at a loopback target.
    runner = SpyRunner()
    call = ToolCall(
        name=ToolName.FETCH_JD,
        arguments=FetchJDInput(url="http://127.0.0.1/admin"),
    )

    # When: the fetch request reaches the runtime boundary.
    record = execute_tool_call(
        call=call,
        context=AgentToolContext(prompt_dir=Path("prompts")),
        runner=runner,
        options=ToolExecutionOptions(
            execution_policy=AgentExecutionPolicy(),
            recovery_decider=RuleRecoveryDecider(),
            runtime_policy=RuntimePolicy(),
        ),
    )

    # Then: the unsafe network target is blocked without touching the runner.
    assert runner.call_count == 0
    assert record.step.status == AgentStepStatus.SKIPPED
    assert record.enforcement_events[0].boundary == RuntimeBoundary.NETWORK_FETCH
    assert record.enforcement_events[0].decision == RuntimePolicyDecision.DENIED


def test_runtime_policy_denies_disallowed_external_actions() -> None:
    # Given: a model-proposed external action outside the local analysis boundary.
    policy = RuntimePolicy()

    # When: the external action request is checked directly.
    event = policy.enforce_external_action("send_email")

    # Then: the action is denied with a trace-compatible enforcement event.
    assert event.boundary == RuntimeBoundary.EXTERNAL_ACTION
    assert event.decision == RuntimePolicyDecision.DENIED
    assert event.policy_version == "policy-v1"
    assert "send_email" in event.reason


def test_execute_tool_call_records_allowed_pre_and_post_events() -> None:
    # Given: a valid analyzer tool call.
    call = ToolCall(
        name=ToolName.ANALYZE_CAREER_FIT,
        arguments=AnalyzeCareerFitInput(resume_text="Python SQL", jd_text="Python SQL"),
    )

    # When: the tool call completes through the runtime boundary.
    record = execute_tool_call(
        call=call,
        context=AgentToolContext(prompt_dir=Path("prompts")),
        runner=default_tool_registry(),
        options=ToolExecutionOptions(
            execution_policy=AgentExecutionPolicy(),
            recovery_decider=RuleRecoveryDecider(),
            runtime_policy=RuntimePolicy(),
        ),
    )

    # Then: enforcement events are suitable for trace serialization.
    assert record.step.status == AgentStepStatus.COMPLETED
    assert [
        (event.boundary, event.decision)
        for event in record.enforcement_events
    ] == [
        (RuntimeBoundary.PRE_TOOL_CALL, RuntimePolicyDecision.ALLOWED),
        (RuntimeBoundary.POST_TOOL_CALL, RuntimePolicyDecision.ALLOWED),
    ]
    assert record.enforcement_events[0].model_dump(mode="json") == {
        "policy_version": "policy-v1",
        "boundary": "pre-tool-call",
        "decision": "allowed",
        "reason": "analyze_career_fit passed runtime pre-tool checks.",
        "tool_name": "analyze_career_fit",
    }


class SpyRunner:
    def __init__(self) -> None:
        self.call_count: int = 0

    def run(self, call: ToolCall, context: AgentToolContext) -> ToolResult:
        self.call_count += 1
        return ToolResult(
            name=call.name,
            status=ToolStatus.SUCCESS,
            message=f"ran with {context.prompt_dir}",
        )
