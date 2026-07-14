from career_ai.llm.capabilities import (
    CapabilityName,
    ProviderCapabilityProfile,
    build_provider_capability_profile,
    unsupported_capability_error,
)
from career_ai.llm.models import ModelProvider
from career_ai.llm.settings import LLMSettings


def test_fake_provider_declares_deterministic_local_behavior() -> None:
    settings = LLMSettings(provider=ModelProvider.FAKE)

    profile = build_provider_capability_profile(settings)

    assert profile.provider_name == ModelProvider.FAKE
    assert profile.model_name == "local-fake"
    assert profile.supports_structured_output is True
    assert profile.supports_single_turn_tool_calls is False
    assert profile.supports_multi_turn_tool_calls is False
    assert profile.supports_reasoning_mode is False
    assert profile.supports_streaming is False
    assert profile.tool_calls.deterministic_local_only is True


def test_openai_compatible_profile_declares_configured_tool_call_support() -> None:
    settings = LLMSettings(
        provider=ModelProvider.OPENAI_COMPATIBLE,
        model="gpt-compatible",
        supports_tool_calling=True,
        supports_provider_tracing=True,
    )

    profile = build_provider_capability_profile(settings)

    assert profile.provider_name == ModelProvider.OPENAI_COMPATIBLE
    assert profile.model_name == "gpt-compatible"
    assert profile.supports_structured_output is True
    assert profile.supports_single_turn_tool_calls is True
    assert profile.supports_multi_turn_tool_calls is True
    assert profile.supports_provider_tracing is True


def test_deepseek_profile_declares_reasoning_state_requirements() -> None:
    settings = LLMSettings(
        provider=ModelProvider.DEEPSEEK_COMPATIBLE,
        model="deepseek-reasoner",
    )

    profile = build_provider_capability_profile(settings)

    assert profile.provider_name == ModelProvider.DEEPSEEK_COMPATIBLE
    assert profile.supports_reasoning_mode is True
    assert profile.requires_reasoning_state_replay is True
    assert profile.reasoning.requires_state_replay is True
    assert profile.supports_streaming is True


def test_unsupported_feature_returns_explicit_capability_error() -> None:
    profile = ProviderCapabilityProfile.fake()

    error = unsupported_capability_error(profile, CapabilityName.MULTI_TURN_TOOL_CALLS)

    assert error.capability == CapabilityName.MULTI_TURN_TOOL_CALLS
    assert "fake" in error.reason
    assert "multi_turn_tool_calls" in error.reason
