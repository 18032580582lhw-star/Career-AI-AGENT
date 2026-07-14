from enum import StrEnum, unique
from typing import ClassVar

from pydantic import ConfigDict, JsonValue

from career_ai.models import FrozenModel

type LLMContentValue = JsonValue | list[str]


@unique
class ModelProvider(StrEnum):
    """Supported model provider families."""

    FAKE = "fake"
    OPENAI_COMPATIBLE = "openai-compatible"
    DEEPSEEK_COMPATIBLE = "deepseek-compatible"


class LLMCapabilities(FrozenModel):
    """Model features detected or configured at runtime."""

    supports_tool_calling: bool
    supports_structured_output: bool
    supports_streaming: bool


class LLMRequest(FrozenModel):
    """Structured request sent through the model-neutral client."""

    system_prompt: str
    user_prompt: str


class LLMResponse(FrozenModel):
    """Structured response returned by an LLM client."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    provider: ModelProvider
    content: dict[str, LLMContentValue]
