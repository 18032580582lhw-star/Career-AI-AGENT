from pathlib import Path

from career_ai.agent.executor import run_career_agent
from career_ai.agent.models import AgentMode, AgentStateStatus, AgentStepStatus
from career_ai.agent.tools import (
    AgentExecutionPolicy,
    AgentRuntimeOptions,
    AgentToolContext,
    ToolCall,
    ToolName,
    ToolRegistry,
    ToolResult,
    ToolStatus,
    default_tool_registry,
)
from career_ai.analysis import get_sample_inputs
from career_ai.llm.client import FakeLLMClient
from career_ai.llm.models import LLMCapabilities, LLMRequest, LLMResponse, ModelProvider


def test_run_career_agent_executes_deterministic_workflow_with_fake_model() -> None:
    resume_text, jd_text = get_sample_inputs()

    result = run_career_agent(
        resume_text=resume_text,
        jd_text=jd_text,
        prompt_dir=Path("prompts"),
        llm_client=FakeLLMClient(),
    )

    assert result.mode == AgentMode.DETERMINISTIC_FALLBACK
    assert result.workflow.report.match.score == 62
    assert "dashboard storytelling" in result.workflow.report.match.missing_keywords
    assert "stakeholder communication" in result.workflow.report.match.missing_keywords
    assert [step.status for step in result.steps] == [
        AgentStepStatus.COMPLETED,
        AgentStepStatus.COMPLETED,
    ]
    assert [step.name for step in result.steps] == [
        "analyze_career_fit",
        "compare_prompt_strategies",
    ]
    assert result.memory_summary.role_title == "AI Product Analyst"
    assert result.trace.provider == "fake"


def test_run_career_agent_records_structured_model_plan() -> None:
    resume_text, jd_text = get_sample_inputs()
    llm_client = RecordingLLMClient(
        planned_steps=["analyze_career_fit", "export_application_docs"],
    )

    result = run_career_agent(
        resume_text=resume_text,
        jd_text=jd_text,
        prompt_dir=Path("prompts"),
        llm_client=llm_client,
    )

    assert llm_client.last_request is not None
    assert "career fit" in llm_client.last_request.user_prompt.lower()
    assert "Tool catalog:" in llm_client.last_request.user_prompt
    assert "analyze_career_fit" in llm_client.last_request.user_prompt
    assert "resume_text str required" in llm_client.last_request.user_prompt
    assert result.planned_steps == ["analyze_career_fit"]


def test_run_career_agent_rejects_unknown_planned_tool() -> None:
    # Given: a model plan that includes an action outside the local tool catalog.
    resume_text, jd_text = get_sample_inputs()
    llm_client = RecordingLLMClient(
        planned_steps=["analyze_career_fit", "unknown_local_action"],
    )

    # When: the agent normalizes the model plan before executing local tools.
    result = run_career_agent(
        resume_text=resume_text,
        jd_text=jd_text,
        prompt_dir=Path("prompts"),
        llm_client=llm_client,
    )

    # Then: the unknown action is denied and never becomes an executable planned step.
    assert result.planned_steps == ["analyze_career_fit"]
    assert any(
        event.status == AgentStateStatus.TOOL_SKIPPED
        and event.tool_name == "unknown_local_action"
        for event in result.state.events
    )


def test_run_career_agent_denies_unsafe_action_and_traces_the_decision() -> None:
    # Given: a model plan that attempts an external side effect and omits core analysis.
    resume_text, jd_text = get_sample_inputs()
    llm_client = RecordingLLMClient(
        planned_steps=["send_email", "compare_prompt_strategies"],
    )

    # When: the controlled-autonomy policy prepares the executable plan.
    result = run_career_agent(
        resume_text=resume_text,
        jd_text=jd_text,
        prompt_dir=Path("prompts"),
        llm_client=llm_client,
    )

    # Then: the unsafe action is traced and the required local analysis is restored first.
    assert result.planned_steps == ["analyze_career_fit", "compare_prompt_strategies"]
    assert any(
        event.status == AgentStateStatus.TOOL_SKIPPED and event.tool_name == "send_email"
        for event in result.state.events
    )
    assert any(
        event.tool_name == "send_email" and event.decision.value == "denied"
        for event in result.trace.enforcement_events
    )


def test_run_career_agent_records_state_machine_events() -> None:
    resume_text, jd_text = get_sample_inputs()

    result = run_career_agent(
        resume_text=resume_text,
        jd_text=jd_text,
        prompt_dir=Path("prompts"),
        llm_client=FakeLLMClient(),
    )

    assert result.state.status == AgentStateStatus.COMPLETED
    assert [event.status for event in result.state.events] == [
        AgentStateStatus.INITIALIZED,
        AgentStateStatus.PLANNED,
        AgentStateStatus.RUNNING_TOOL,
        AgentStateStatus.TOOL_COMPLETED,
        AgentStateStatus.RUNNING_TOOL,
        AgentStateStatus.TOOL_COMPLETED,
        AgentStateStatus.COMPLETED,
    ]
    assert result.state.events[2].tool_name == "analyze_career_fit"


def test_run_career_agent_retries_recoverable_tool_failure() -> None:
    resume_text, jd_text = get_sample_inputs()
    registry = FlakyAnalysisRegistry()

    result = run_career_agent(
        resume_text=resume_text,
        jd_text=jd_text,
        prompt_dir=Path("prompts"),
        llm_client=FakeLLMClient(),
        runtime_options=AgentRuntimeOptions(
            tool_runner=registry,
            execution_policy=AgentExecutionPolicy(max_tool_attempts=2),
        ),
    )

    assert registry.analysis_attempts == 2
    assert result.state.status == AgentStateStatus.COMPLETED
    assert result.steps[0].status == AgentStepStatus.COMPLETED
    assert "Recovered after 2 attempts" in result.steps[0].message
    assert [event.status for event in result.state.events[:6]] == [
        AgentStateStatus.INITIALIZED,
        AgentStateStatus.PLANNED,
        AgentStateStatus.RUNNING_TOOL,
        AgentStateStatus.FAILED_RECOVERABLE,
        AgentStateStatus.RECOVERY_DECIDED,
        AgentStateStatus.RECOVERING,
    ]


def test_run_career_agent_skips_noncritical_tool_after_retries() -> None:
    resume_text, jd_text = get_sample_inputs()

    result = run_career_agent(
        resume_text=resume_text,
        jd_text=jd_text,
        prompt_dir=Path("prompts"),
        llm_client=FakeLLMClient(),
        runtime_options=AgentRuntimeOptions(
            tool_runner=AlwaysFailPromptRegistry(),
            execution_policy=AgentExecutionPolicy(max_tool_attempts=2),
        ),
    )

    assert result.state.status == AgentStateStatus.COMPLETED_WITH_RECOVERY
    assert [step.status for step in result.steps] == [
        AgentStepStatus.COMPLETED,
        AgentStepStatus.SKIPPED,
    ]
    assert result.workflow.prompt_result.best_strategy_name == ""
    assert AgentStateStatus.TOOL_SKIPPED in [
        event.status for event in result.state.events
    ]


class RecordingLLMClient:
    def __init__(self, *, planned_steps: list[str]) -> None:
        self.last_request: LLMRequest | None = None
        self._planned_steps: list[str] = planned_steps

    @property
    def provider(self) -> ModelProvider:
        return ModelProvider.FAKE

    @property
    def capabilities(self) -> LLMCapabilities:
        return LLMCapabilities(
            supports_tool_calling=False,
            supports_structured_output=True,
            supports_streaming=False,
        )

    def complete_structured(self, request: LLMRequest) -> LLMResponse:
        self.last_request = request
        return LLMResponse(
            provider=ModelProvider.FAKE,
            content={"steps": self._planned_steps},
        )


class FlakyAnalysisRegistry:
    def __init__(self) -> None:
        self._default_registry: ToolRegistry = default_tool_registry()
        self.analysis_attempts: int = 0

    def run(self, call: ToolCall, context: AgentToolContext) -> ToolResult:
        match call.name:
            case ToolName.ANALYZE_CAREER_FIT:
                self.analysis_attempts += 1
                if self.analysis_attempts == 1:
                    return ToolResult(
                        name=call.name,
                        status=ToolStatus.FAILURE,
                        message="temporary analyzer failure",
                        recoverable=True,
                    )
                return self._default_registry.run(call, context)
            case _:
                return self._default_registry.run(call, context)


class AlwaysFailPromptRegistry:
    def __init__(self) -> None:
        self._default_registry: ToolRegistry = default_tool_registry()
        self.prompt_attempts: int = 0

    def run(self, call: ToolCall, context: AgentToolContext) -> ToolResult:
        match call.name:
            case ToolName.COMPARE_PROMPT_STRATEGIES:
                self.prompt_attempts += 1
                return ToolResult(
                    name=call.name,
                    status=ToolStatus.FAILURE,
                    message="prompt directory unavailable",
                    recoverable=True,
                )
            case _:
                return self._default_registry.run(call, context)
