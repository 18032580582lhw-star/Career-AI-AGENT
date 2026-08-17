from career_ai.models import FrozenModel


class ProviderStatus(FrozenModel):
    """Provider diagnostics used by the doctor command."""

    provider: str
    model: str
    supports_structured_output: bool
    supports_single_turn_tools: bool
    supports_multi_turn_tools: bool
    supports_reasoning: bool
    supports_streaming: bool
    supports_tracing: bool


def read_provider_status() -> ProviderStatus:
    """Read provider diagnostics outside the CLI composition module."""
    from career_ai.llm.settings import LLMSettings  # noqa: PLC0415

    settings = LLMSettings()
    profile = settings.capability_profile
    return ProviderStatus(
        provider=settings.provider.value,
        model=profile.model_name,
        supports_structured_output=profile.supports_structured_output,
        supports_single_turn_tools=profile.supports_single_turn_tool_calls,
        supports_multi_turn_tools=profile.supports_multi_turn_tool_calls,
        supports_reasoning=profile.supports_reasoning_mode,
        supports_streaming=profile.supports_streaming,
        supports_tracing=profile.supports_provider_tracing,
    )
