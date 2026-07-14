from enum import StrEnum, unique
from typing import Protocol

from career_ai.llm.models import ModelProvider
from career_ai.models import FrozenModel


@unique
class CapabilityName(StrEnum):
    """Named provider features that can be required by harness layers."""

    STRUCTURED_OUTPUT = "structured_output"
    SINGLE_TURN_TOOL_CALLS = "single_turn_tool_calls"
    MULTI_TURN_TOOL_CALLS = "multi_turn_tool_calls"
    REASONING_MODE = "reasoning_mode"
    STREAMING = "streaming"
    PROVIDER_TRACING = "provider_tracing"


class ToolCallCapability(FrozenModel):
    """Tool-call behavior declared by a model provider boundary."""

    supports_single_turn: bool
    supports_multi_turn: bool
    deterministic_local_only: bool = False


class ReasoningCapability(FrozenModel):
    """Reasoning or thinking-mode behavior declared by a provider."""

    supports_reasoning_mode: bool
    requires_state_replay: bool = False


class TraceCapability(FrozenModel):
    """Provider-native tracing behavior declared by a provider."""

    supports_provider_tracing: bool


class ProviderCapabilityProfile(FrozenModel):
    """Complete capability contract for one provider/model/harness boundary."""

    provider_name: ModelProvider
    model_name: str
    supports_structured_output: bool
    supports_single_turn_tool_calls: bool
    supports_multi_turn_tool_calls: bool
    supports_reasoning_mode: bool
    requires_reasoning_state_replay: bool
    supports_streaming: bool
    supports_provider_tracing: bool
    unsupported_reason: str
    tool_calls: ToolCallCapability
    reasoning: ReasoningCapability
    trace: TraceCapability

    @classmethod
    def fake(cls) -> "ProviderCapabilityProfile":
        """Return the deterministic no-key fake provider profile."""
        return cls(
            provider_name=ModelProvider.FAKE,
            model_name="local-fake",
            supports_structured_output=True,
            supports_single_turn_tool_calls=False,
            supports_multi_turn_tool_calls=False,
            supports_reasoning_mode=False,
            requires_reasoning_state_replay=False,
            supports_streaming=False,
            supports_provider_tracing=False,
            unsupported_reason="fake provider uses deterministic local fallback behavior",
            tool_calls=ToolCallCapability(
                supports_single_turn=False,
                supports_multi_turn=False,
                deterministic_local_only=True,
            ),
            reasoning=ReasoningCapability(supports_reasoning_mode=False),
            trace=TraceCapability(supports_provider_tracing=False),
        )

    @classmethod
    def openai_compatible(
        cls,
        *,
        model_name: str,
        supports_tool_calling: bool,
        supports_provider_tracing: bool,
    ) -> "ProviderCapabilityProfile":
        """Return an OpenAI-compatible boundary profile from explicit settings."""
        resolved_model = model_name or "openai-compatible"
        return cls(
            provider_name=ModelProvider.OPENAI_COMPATIBLE,
            model_name=resolved_model,
            supports_structured_output=True,
            supports_single_turn_tool_calls=supports_tool_calling,
            supports_multi_turn_tool_calls=supports_tool_calling,
            supports_reasoning_mode=False,
            requires_reasoning_state_replay=False,
            supports_streaming=True,
            supports_provider_tracing=supports_provider_tracing,
            unsupported_reason="capability must be declared by OpenAI-compatible settings",
            tool_calls=ToolCallCapability(
                supports_single_turn=supports_tool_calling,
                supports_multi_turn=supports_tool_calling,
            ),
            reasoning=ReasoningCapability(supports_reasoning_mode=False),
            trace=TraceCapability(supports_provider_tracing=supports_provider_tracing),
        )

    @classmethod
    def deepseek_compatible(cls, *, model_name: str) -> "ProviderCapabilityProfile":
        """Return a DeepSeek-compatible profile with reasoning state requirements."""
        resolved_model = model_name or "deepseek-reasoner"
        return cls(
            provider_name=ModelProvider.DEEPSEEK_COMPATIBLE,
            model_name=resolved_model,
            supports_structured_output=True,
            supports_single_turn_tool_calls=False,
            supports_multi_turn_tool_calls=False,
            supports_reasoning_mode=True,
            requires_reasoning_state_replay=True,
            supports_streaming=True,
            supports_provider_tracing=False,
            unsupported_reason="DeepSeek-compatible reasoning requires state replay",
            tool_calls=ToolCallCapability(
                supports_single_turn=False,
                supports_multi_turn=False,
            ),
            reasoning=ReasoningCapability(
                supports_reasoning_mode=True,
                requires_state_replay=True,
            ),
            trace=TraceCapability(supports_provider_tracing=False),
        )


class CapabilityError(FrozenModel):
    """Explicit unsupported-capability result for planner and harness gates."""

    capability: CapabilityName
    reason: str


def build_provider_capability_profile(settings: "CapabilitySettings") -> ProviderCapabilityProfile:
    """Build a capability profile from environment-backed settings."""
    match settings.provider:
        case ModelProvider.FAKE:
            return ProviderCapabilityProfile.fake()
        case ModelProvider.OPENAI_COMPATIBLE:
            return ProviderCapabilityProfile.openai_compatible(
                model_name=settings.model,
                supports_tool_calling=settings.supports_tool_calling,
                supports_provider_tracing=settings.supports_provider_tracing,
            )
        case ModelProvider.DEEPSEEK_COMPATIBLE:
            return ProviderCapabilityProfile.deepseek_compatible(model_name=settings.model)


def unsupported_capability_error(
    profile: ProviderCapabilityProfile,
    capability: CapabilityName,
) -> CapabilityError:
    """Return a compact explicit error for an unsupported provider feature."""
    return CapabilityError(
        capability=capability,
        reason=(
            f"{profile.provider_name.value} provider does not support "
            f"{capability.value}: {profile.unsupported_reason}"
        ),
    )


class CapabilitySettings(Protocol):
    """Structural subset required to construct a capability profile."""

    provider: ModelProvider
    model: str
    supports_tool_calling: bool
    supports_provider_tracing: bool
