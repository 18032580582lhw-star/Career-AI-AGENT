from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict

from career_ai.llm.capabilities import ProviderCapabilityProfile, build_provider_capability_profile
from career_ai.llm.models import LLMCapabilities, ModelProvider


class LLMSettings(BaseSettings):
    """Environment-backed model settings for local agent runs."""

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="CAREER_AI_",
        env_file=".env",
    )

    provider: ModelProvider = ModelProvider.FAKE
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    supports_tool_calling: bool = False
    supports_provider_tracing: bool = False

    @property
    def capability_profile(self) -> ProviderCapabilityProfile:
        """Return the active provider/model capability contract."""
        return build_provider_capability_profile(self)

    @property
    def capabilities(self) -> LLMCapabilities:
        """Return conservative capabilities for the configured provider."""
        profile = self.capability_profile
        return LLMCapabilities(
            supports_tool_calling=profile.supports_single_turn_tool_calls,
            supports_structured_output=profile.supports_structured_output,
            supports_streaming=profile.supports_streaming,
        )
