from pathlib import Path

from career_ai.agent.recovery import ModelRecoveryDecider, RecoveryAction
from career_ai.agent.tools import (
    ComparePromptStrategiesInput,
    ToolCall,
    ToolName,
    ToolResult,
    ToolStatus,
)
from career_ai.llm.models import LLMCapabilities, LLMRequest, LLMResponse, ModelProvider


def test_model_recovery_decider_requests_structured_decision() -> None:
    llm_client = RecoveryDecisionLLMClient(
        decision_action="skip",
        decision_reason="Prompt directory is unavailable.",
    )
    decider = ModelRecoveryDecider(llm_client)

    decision = decider.decide(
        call=ToolCall(
            name=ToolName.COMPARE_PROMPT_STRATEGIES,
            arguments=ComparePromptStrategiesInput(
                resume_text="resume",
                jd_text="jd",
                prompt_dir=Path("missing-prompts"),
            ),
        ),
        result=ToolResult(
            name=ToolName.COMPARE_PROMPT_STRATEGIES,
            status=ToolStatus.FAILURE,
            message="prompt directory unavailable",
            recoverable=True,
        ),
        attempt=1,
        max_attempts=3,
    )

    assert decision.action == RecoveryAction.SKIP
    assert decision.reason == "Prompt directory is unavailable."
    assert llm_client.last_request is not None
    assert "compare_prompt_strategies" in llm_client.last_request.user_prompt
    assert "prompt directory unavailable" in llm_client.last_request.user_prompt


class RecoveryDecisionLLMClient:
    def __init__(self, *, decision_action: str, decision_reason: str) -> None:
        self._decision_action: str = decision_action
        self._decision_reason: str = decision_reason
        self.last_request: LLMRequest | None = None

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
            content={
                "action": self._decision_action,
                "reason": self._decision_reason,
            },
        )
