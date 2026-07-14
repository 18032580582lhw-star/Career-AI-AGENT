from career_ai.agent.tool_catalog import ToolCatalog, default_tool_catalog
from career_ai.agent.tool_impl import (
    run_analyze_career_fit,
    run_compare_prompt_strategies,
    run_export_cover_letter_docx,
    run_export_resume_docx,
    run_extract_resume,
    run_fetch_jd,
    run_save_memory_summary,
)
from career_ai.agent.tool_models import AgentToolContext, ToolCall, ToolName, ToolResult


class ToolRegistry:
    """Registry and dispatcher for local career-agent tools."""

    def __init__(self, catalog: ToolCatalog) -> None:
        """Create a registry with stable tool ordering."""
        self._catalog: ToolCatalog = catalog

    def names(self) -> list[ToolName]:
        """Return registered tool names in deterministic order."""
        return [spec.name for spec in self._catalog.tools]

    def catalog(self) -> ToolCatalog:
        """Return model-visible tool metadata."""
        return self._catalog

    def run(self, call: ToolCall, context: AgentToolContext) -> ToolResult:
        """Execute one validated tool call."""
        match call.name:
            case ToolName.FETCH_JD:
                result = run_fetch_jd(call.arguments)
            case ToolName.EXTRACT_RESUME:
                result = run_extract_resume(call.arguments)
            case ToolName.ANALYZE_CAREER_FIT:
                result = run_analyze_career_fit(call.arguments)
            case ToolName.COMPARE_PROMPT_STRATEGIES:
                result = run_compare_prompt_strategies(call.arguments)
            case ToolName.EXPORT_RESUME_DOCX:
                result = run_export_resume_docx(call.arguments, context)
            case ToolName.EXPORT_COVER_LETTER_DOCX:
                result = run_export_cover_letter_docx(call.arguments, context)
            case ToolName.SAVE_MEMORY_SUMMARY:
                result = run_save_memory_summary(call.arguments)
        return result


def default_tool_registry() -> ToolRegistry:
    """Build the default local career-agent tool registry."""
    return ToolRegistry(catalog=default_tool_catalog())
