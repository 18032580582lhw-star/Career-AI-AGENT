from typing import Final, Protocol

import httpx
from pydantic import TypeAdapter

from career_ai.llm.models import (
    LLMCapabilities,
    LLMContentValue,
    LLMRequest,
    LLMResponse,
    ModelProvider,
)
from career_ai.llm.settings import LLMSettings
from career_ai.models import FrozenModel

DEFAULT_AGENT_STEPS: Final[list[str]] = [
    "analyze_career_fit",
    "compare_prompt_strategies",
]

CONTENT_ADAPTER: Final[TypeAdapter[dict[str, LLMContentValue]]] = TypeAdapter(
    dict[str, LLMContentValue],
)


class LLMClient(Protocol):
    """Model-neutral client contract used by the agent runtime."""

    @property
    def provider(self) -> ModelProvider:
        """Return the configured provider family."""
        raise NotImplementedError

    @property
    def capabilities(self) -> LLMCapabilities:
        """Return detected or configured model capabilities."""
        raise NotImplementedError

    def complete_structured(self, request: LLMRequest) -> LLMResponse:
        """Return structured model output for the supplied request."""
        raise NotImplementedError


class FakeLLMClient:
    """Deterministic local client for tests and no-key demos."""

    @property
    def provider(self) -> ModelProvider:
        """Return the fake provider marker."""
        return ModelProvider.FAKE

    @property
    def capabilities(self) -> LLMCapabilities:
        """Return deterministic fake-model capabilities."""
        return LLMCapabilities(
            supports_tool_calling=False,
            supports_structured_output=True,
            supports_streaming=False,
        )

    def complete_structured(self, request: LLMRequest) -> LLMResponse:
        """Return a deterministic JSON-like plan."""
        _ = request
        return LLMResponse(
            provider=ModelProvider.FAKE,
            content={"steps": DEFAULT_AGENT_STEPS},
        )


class OpenAIMessage(FrozenModel):
    """Minimal OpenAI-compatible chat message response."""

    content: str


class OpenAIChoice(FrozenModel):
    """Minimal OpenAI-compatible choice response."""

    message: OpenAIMessage


class OpenAIChatResponse(FrozenModel):
    """Minimal OpenAI-compatible chat completion response."""

    choices: list[OpenAIChoice]


class OpenAICompatibleClient:
    """OpenAI-compatible structured-output client."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        provider: ModelProvider = ModelProvider.OPENAI_COMPATIBLE,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Create an OpenAI-compatible client."""
        self._base_url: str = base_url.rstrip("/")
        self._api_key: str = api_key
        self._model: str = model
        self._provider: ModelProvider = provider
        self._http_client: httpx.Client = http_client or httpx.Client(timeout=30.0)

    @property
    def provider(self) -> ModelProvider:
        """Return the provider marker."""
        return self._provider

    @property
    def capabilities(self) -> LLMCapabilities:
        """Return conservative OpenAI-compatible capabilities."""
        return LLMCapabilities(
            supports_tool_calling=False,
            supports_structured_output=True,
            supports_streaming=True,
        )

    def complete_structured(self, request: LLMRequest) -> LLMResponse:
        """Call an OpenAI-compatible chat endpoint and parse JSON content."""
        response = self._http_client.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": request.system_prompt},
                    {"role": "user", "content": request.user_prompt},
                ],
                "response_format": {"type": "json_object"},
            },
        )
        _ = response.raise_for_status()
        parsed_response = OpenAIChatResponse.model_validate(response.json())
        content = parsed_response.choices[0].message.content
        return LLMResponse(
            provider=self._provider,
            content=CONTENT_ADAPTER.validate_json(content),
        )


def build_llm_client(settings: LLMSettings) -> LLMClient:
    """Build a model-neutral client from environment settings."""
    match settings.provider:
        case ModelProvider.FAKE:
            return FakeLLMClient()
        case ModelProvider.OPENAI_COMPATIBLE:
            return OpenAICompatibleClient(
                base_url=settings.base_url,
                api_key=settings.api_key,
                model=settings.model,
            )
        case ModelProvider.DEEPSEEK_COMPATIBLE:
            return OpenAICompatibleClient(
                base_url=settings.base_url,
                api_key=settings.api_key,
                model=settings.model,
                provider=ModelProvider.DEEPSEEK_COMPATIBLE,
            )
