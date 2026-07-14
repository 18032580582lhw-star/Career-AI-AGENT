from enum import StrEnum, unique
from typing import Protocol

from career_ai.agent.tool_models import ToolCall, ToolResult
from career_ai.llm.client import LLMClient
from career_ai.llm.models import LLMContentValue, LLMRequest
from career_ai.models import FrozenModel


@unique
class RecoveryAction(StrEnum):
    """Model-selected recovery action for a failed tool call."""

    RETRY = "retry"
    SKIP = "skip"
    ABORT = "abort"


class RecoveryDecision(FrozenModel):
    """Typed recovery decision returned by a local rule or model."""

    action: RecoveryAction
    reason: str


class RecoveryDecider(Protocol):
    """Decides what the execution loop should do after a tool failure."""

    def decide(
        self,
        *,
        call: ToolCall,
        result: ToolResult,
        attempt: int,
        max_attempts: int,
    ) -> RecoveryDecision:
        """Return a retry, skip, or abort decision."""
        raise NotImplementedError


class ModelRecoveryDecider:
    """LLM-backed recovery decider for failed local tool calls."""

    def __init__(self, llm_client: LLMClient) -> None:
        """Create a recovery decider backed by the configured LLM client."""
        self._llm_client: LLMClient = llm_client

    def decide(
        self,
        *,
        call: ToolCall,
        result: ToolResult,
        attempt: int,
        max_attempts: int,
    ) -> RecoveryDecision:
        """Ask the configured model how to recover from a tool failure."""
        response = self._llm_client.complete_structured(
            LLMRequest(
                system_prompt=(
                    "You are a career-agent recovery decision maker. "
                    "Return JSON with action and reason only. "
                    "Allowed action values are retry, skip, abort."
                ),
                user_prompt=(
                    f"Choose a recovery action for tool {call.name.value}. "
                    f"Failure message: {result.message}. "
                    f"Attempt {attempt} of {max_attempts}. "
                    "Use retry for transient failures, skip for optional tools, "
                    "and abort for critical unrecoverable failures."
                ),
            ),
        )
        return RecoveryDecision(
            action=_action_from_content(response.content.get("action")),
            reason=_reason_from_content(response.content.get("reason")),
        )


class RuleRecoveryDecider:
    """Deterministic fallback recovery decider matching v2 behavior."""

    def decide(
        self,
        *,
        call: ToolCall,
        result: ToolResult,
        attempt: int,
        max_attempts: int,
    ) -> RecoveryDecision:
        """Return a local deterministic recovery decision."""
        _ = call
        if result.recoverable and attempt < max_attempts:
            return RecoveryDecision(
                action=RecoveryAction.RETRY,
                reason="Recoverable failure can be retried.",
            )
        return RecoveryDecision(
            action=RecoveryAction.ABORT,
            reason="No retry attempts remain.",
        )


def _action_from_content(value: LLMContentValue | None) -> RecoveryAction:
    match value:
        case "skip":
            return RecoveryAction.SKIP
        case "abort":
            return RecoveryAction.ABORT
        case "retry":
            return RecoveryAction.RETRY
        case str():
            return RecoveryAction.RETRY
        case _:
            return RecoveryAction.RETRY


def _reason_from_content(value: LLMContentValue | None) -> str:
    match value:
        case str() as reason:
            return reason.strip() or "Model did not provide a reason."
        case _:
            return "Model did not provide a reason."
