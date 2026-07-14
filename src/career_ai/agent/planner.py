from __future__ import annotations

from typing import TYPE_CHECKING, assert_never

from career_ai.agent.models import AgentAutonomyPolicy, AgentMode, ValidatedAgentPlan
from career_ai.agent.tool_catalog import (
    ToolCatalog,
    default_tool_catalog,
    render_tool_catalog_for_prompt,
)
from career_ai.llm.models import LLMContentValue, LLMRequest

if TYPE_CHECKING:
    from career_ai.agent.tool_models import ToolName
    from career_ai.llm.client import LLMClient


def select_agent_mode(llm_client: LLMClient) -> AgentMode:
    """Choose the strongest supported local runtime mode."""
    capabilities = llm_client.capabilities
    if capabilities.supports_tool_calling:
        return AgentMode.TOOL_CALLING
    if capabilities.supports_structured_output:
        return AgentMode.DETERMINISTIC_FALLBACK
    return AgentMode.DETERMINISTIC_FALLBACK


def agent_mode_label(mode: AgentMode) -> str:
    """Return a display label for an agent mode."""
    match mode:
        case AgentMode.DETERMINISTIC_FALLBACK:
            return "deterministic fallback"
        case AgentMode.STRUCTURED_PLAN:
            return "structured plan"
        case AgentMode.TOOL_CALLING:
            return "tool calling"
        case _:
            assert_never(mode)


def request_agent_plan(
    llm_client: LLMClient,
    tool_catalog: ToolCatalog | None = None,
    autonomy_policy: AgentAutonomyPolicy | None = None,
) -> ValidatedAgentPlan:
    """Ask the configured model for a structured career-agent plan."""
    catalog = tool_catalog or default_tool_catalog()
    policy = autonomy_policy or AgentAutonomyPolicy()
    response = llm_client.complete_structured(
        LLMRequest(
            system_prompt=(
                "You are a local career intelligence planner. "
                "Use only tools from the provided catalog. "
                "Use their namespaced display names and obey their response, failure, "
                "retry, and safety guidance. "
                "Return JSON with a steps array only."
            ),
            user_prompt=(
                "Plan a career fit workflow for one resume and one job description.\n\n"
                f"{render_tool_catalog_for_prompt(catalog)}"
            ),
        ),
    )
    return validate_agent_plan(
        planned_steps=_steps_from_content(response.content.get("steps")),
        tool_catalog=catalog,
        autonomy_policy=policy,
    )


def validate_agent_plan(
    *,
    planned_steps: list[str],
    tool_catalog: ToolCatalog,
    autonomy_policy: AgentAutonomyPolicy,
) -> ValidatedAgentPlan:
    """Normalize a model plan into allowed catalog tools and record denials."""
    catalog_tools = {
        spec.name.value: spec.name
        for spec in tool_catalog.tools
    } | {
        spec.display_name: spec.name
        for spec in tool_catalog.tools
    }
    allowed_tools = set(autonomy_policy.allowed_tools)
    accepted_tools: list[ToolName] = []
    rejected_steps: list[str] = []
    for step in planned_steps:
        normalized_step = step.strip()
        if _is_forbidden_step(normalized_step, autonomy_policy):
            rejected_steps.append(normalized_step)
            continue
        tool_name = catalog_tools.get(normalized_step)
        if tool_name is None or tool_name not in allowed_tools:
            rejected_steps.append(normalized_step)
            continue
        if tool_name in accepted_tools:
            continue
        if len(accepted_tools) >= autonomy_policy.max_model_planned_steps:
            rejected_steps.append(normalized_step)
            continue
        accepted_tools.append(tool_name)
    repaired_tools = [
        required_tool
        for required_tool in autonomy_policy.required_tools
        if required_tool in allowed_tools and required_tool in catalog_tools.values()
    ]
    repaired_tools.extend(tool for tool in accepted_tools if tool not in repaired_tools)
    return ValidatedAgentPlan(
        planned_steps=[tool.value for tool in repaired_tools],
        rejected_steps=rejected_steps,
    )


def _is_forbidden_step(step: str, policy: AgentAutonomyPolicy) -> bool:
    normalized_step = step.casefold()
    return any(
        pattern.casefold() in normalized_step
        for pattern in policy.forbidden_tool_patterns
    )


def _steps_from_content(value: LLMContentValue | None) -> list[str]:
    match value:
        case list() as steps:
            return [step.strip() for step in steps if isinstance(step, str) and step.strip()]
        case str() as step:
            return [step] if step.strip() else []
        case None | bool() | int() | float() | dict():
            return []
