import httpx

from career_ai.llm import BoundaryViolationCode, check_career_fit_report
from career_ai.llm.client import FakeLLMClient, OpenAICompatibleClient, build_llm_client
from career_ai.llm.models import LLMCapabilities, LLMRequest, ModelProvider
from career_ai.llm.settings import LLMSettings


def test_fake_llm_client_returns_structured_plan_without_api_key() -> None:
    client = FakeLLMClient()

    response = client.complete_structured(
        LLMRequest(
            system_prompt="Plan a career fit workflow.",
            user_prompt="Analyze a resume against a JD.",
        ),
    )

    assert response.provider == ModelProvider.FAKE
    assert response.content["steps"] == [
        "analyze_career_fit",
        "compare_prompt_strategies",
    ]


def test_llm_settings_defaults_to_fake_provider() -> None:
    settings = LLMSettings()

    assert settings.provider == ModelProvider.FAKE
    assert settings.capabilities == LLMCapabilities(
        supports_tool_calling=False,
        supports_structured_output=True,
        supports_streaming=False,
    )


def test_build_llm_client_uses_openai_compatible_provider() -> None:
    settings = LLMSettings(
        provider=ModelProvider.OPENAI_COMPATIBLE,
        base_url="http://models.local/v1",
        api_key="test-key",
        model="career-test-model",
    )

    client = build_llm_client(settings)

    assert isinstance(client, OpenAICompatibleClient)
    assert client.provider == ModelProvider.OPENAI_COMPATIBLE


def test_openai_compatible_client_parses_structured_json_response() -> None:
    captured_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_paths.append(request.url.path)
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"steps":["analyze_career_fit"]}',
                        },
                    },
                ],
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = OpenAICompatibleClient(
        base_url="http://models.local/v1",
        api_key="test-key",
        model="career-test-model",
        http_client=http_client,
    )

    response = client.complete_structured(
        LLMRequest(
            system_prompt="Return JSON.",
            user_prompt="Plan a workflow.",
        ),
    )

    assert captured_paths == ["/v1/chat/completions"]
    assert response.content == {"steps": ["analyze_career_fit"]}


def test_llm_package_exports_boundary_harness_api() -> None:
    assert callable(check_career_fit_report)
    assert BoundaryViolationCode.INVALID_JSON == "invalid_json"
