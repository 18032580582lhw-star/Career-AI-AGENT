"""Model-neutral LLM client abstractions."""

from career_ai.llm.boundary_harness import (
    BoundaryCheckResult,
    BoundaryGuardResult,
    BoundaryViolation,
    BoundaryViolationCode,
    check_career_fit_report,
    guard_career_fit_report,
)
from career_ai.llm.capabilities import (
    CapabilityError,
    CapabilityName,
    ProviderCapabilityProfile,
    ReasoningCapability,
    ToolCallCapability,
    TraceCapability,
    build_provider_capability_profile,
    unsupported_capability_error,
)
from career_ai.llm.client import FakeLLMClient, LLMClient, OpenAICompatibleClient
from career_ai.llm.models import LLMCapabilities, LLMRequest, LLMResponse, ModelProvider
from career_ai.llm.settings import LLMSettings

__all__ = [
    "BoundaryCheckResult",
    "BoundaryGuardResult",
    "BoundaryViolation",
    "BoundaryViolationCode",
    "CapabilityError",
    "CapabilityName",
    "FakeLLMClient",
    "LLMCapabilities",
    "LLMClient",
    "LLMRequest",
    "LLMResponse",
    "LLMSettings",
    "ModelProvider",
    "OpenAICompatibleClient",
    "ProviderCapabilityProfile",
    "ReasoningCapability",
    "ToolCallCapability",
    "TraceCapability",
    "build_provider_capability_profile",
    "check_career_fit_report",
    "guard_career_fit_report",
    "unsupported_capability_error",
]
