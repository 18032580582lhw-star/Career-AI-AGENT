from pathlib import Path

from career_ai.agent.executor import run_career_agent
from career_ai.agent.models import AgentStateStatus, AgentStepStatus
from career_ai.agent.recovery import ModelRecoveryDecider
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
from career_ai.llm.models import LLMCapabilities, LLMRequest, LLMResponse, ModelProvider


def test_run_career_agent_uses_model_recovery_decision_to_skip_tool() -> None:
    resume_text, jd_text = get_sample_inputs()
    llm_client = RecoveryAwareLLMClient()
    registry = AlwaysFailPromptRegistry()

    result = run_career_agent(
        resume_text=resume_text,
        jd_text=jd_text,
        prompt_dir=Path("prompts"),
        llm_client=llm_client,
        runtime_options=AgentRuntimeOptions(
            tool_runner=registry,
            execution_policy=AgentExecutionPolicy(max_tool_attempts=3),
            recovery_decider=ModelRecoveryDecider(llm_client),
        ),
    )

    assert registry.prompt_attempts == 1
    assert result.state.status == AgentStateStatus.COMPLETED_WITH_RECOVERY
    assert result.steps[1].status == AgentStepStatus.SKIPPED
    assert AgentStateStatus.RECOVERY_DECIDED in [
        event.status for event in result.state.events
    ]
    assert "Model decided to skip" in result.steps[1].message


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


class RecoveryAwareLLMClient:
    def __init__(self) -> None:
        self.requests: list[LLMRequest] = []

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
        self.requests.append(request)
        if "recovery decision" in request.system_prompt.lower():
            return LLMResponse(
                provider=ModelProvider.FAKE,
                content={
                    "action": "skip",
                    "reason": "Prompt comparison is optional.",
                },
            )
        return LLMResponse(
            provider=ModelProvider.FAKE,
            content={"steps": ["analyze_career_fit", "compare_prompt_strategies"]},
        )
