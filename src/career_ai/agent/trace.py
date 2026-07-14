from pathlib import Path
from typing import Final

from pydantic import Field

from career_ai.agent.enforcement_models import RuntimeEnforcementEvent
from career_ai.llm.models import LLMCapabilities
from career_ai.models import FrozenModel

DEFAULT_TRACE_EXPECTED_BEHAVIOR: Final[str] = (
    "Produce a factual, privacy-preserving career fit analysis without inventing resume facts."
)
DEFAULT_TOOL_CATALOG_VERSION: Final[str] = "tool-catalog-v1"
DEFAULT_POLICY_VERSION: Final[str] = "policy-v1"


class InputTraceSummary(FrozenModel):
    """Privacy-preserving summary of user inputs for one run."""

    resume_character_count: int
    jd_character_count: int

    @classmethod
    def from_inputs(cls, *, resume_text: str, jd_text: str) -> "InputTraceSummary":
        """Create a trace-safe input summary without retaining source text."""
        return cls(
            resume_character_count=len(resume_text),
            jd_character_count=len(jd_text),
        )


class ToolTraceEvent(FrozenModel):
    """Trace-safe event emitted for one tool lifecycle transition."""

    tool_name: str
    status: str
    message: str = ""


class ProviderCapabilityTraceSummary(FrozenModel):
    """Trace-safe summary of provider capabilities used by one run."""

    supports_tool_calling: bool
    supports_structured_output: bool
    supports_streaming: bool

    @classmethod
    def from_capabilities(cls, capabilities: LLMCapabilities) -> "ProviderCapabilityTraceSummary":
        """Create a compact provider-capability summary."""
        return cls(
            supports_tool_calling=capabilities.supports_tool_calling,
            supports_structured_output=capabilities.supports_structured_output,
            supports_streaming=capabilities.supports_streaming,
        )


class HarnessTraceConfiguration(FrozenModel):
    """Trace-safe local harness configuration for one run."""

    prompt_set: str = Field(min_length=1)
    tool_catalog_version: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    retry_budget: int = Field(ge=0)

    @classmethod
    def from_runtime(
        cls,
        *,
        prompt_dir: Path,
        retry_budget: int,
    ) -> "HarnessTraceConfiguration":
        """Create a compact harness summary without local paths."""
        return cls(
            prompt_set=_prompt_set_name(prompt_dir),
            tool_catalog_version=DEFAULT_TOOL_CATALOG_VERSION,
            policy_version=DEFAULT_POLICY_VERSION,
            retry_budget=retry_budget,
        )


class CareerRunTrace(FrozenModel):
    """Structured, privacy-preserving trace for one local agent run."""

    run_id: str
    provider: str
    agent_mode: str
    final_status: str
    planned_steps: list[str]
    input_summary: InputTraceSummary
    tool_events: list[ToolTraceEvent]
    provider_capabilities: ProviderCapabilityTraceSummary
    harness: HarnessTraceConfiguration
    enforcement_events: list[RuntimeEnforcementEvent] = Field(default_factory=list)
    expected_behavior: str = Field(default=DEFAULT_TRACE_EXPECTED_BEHAVIOR, min_length=1)


def _prompt_set_name(prompt_dir: Path) -> str:
    name = prompt_dir.name
    if name == "prompts":
        return "default"
    return name or "default"
