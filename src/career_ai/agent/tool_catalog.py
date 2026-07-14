from career_ai.agent.tool_catalog_defaults import build_default_tool_specs
from career_ai.agent.tool_catalog_models import (
    ToolCatalog,
    ToolInputField,
    ToolSpec,
    ToolSpecNotFoundError,
)

__all__ = [
    "ToolCatalog",
    "ToolInputField",
    "ToolSpec",
    "ToolSpecNotFoundError",
    "default_tool_catalog",
    "render_tool_catalog_for_prompt",
]


def default_tool_catalog() -> ToolCatalog:
    """Return the default model-visible local tool catalog."""
    return ToolCatalog(tools=build_default_tool_specs())


def render_tool_catalog_for_prompt(catalog: ToolCatalog) -> str:
    """Render a compact model-facing tool catalog."""
    lines = ["Tool catalog:"]
    for spec in catalog.tools:
        critical = "yes" if spec.is_critical else "no"
        lines.append(f"- {spec.display_name}: {spec.description}")
        lines.append(f"  critical: {critical}")
        for field in spec.input_schema:
            required = "required" if field.required else "optional"
            lines.append(
                f"  input: {field.name} {field.type_name} {required} - {field.description}",
            )
        lines.append(f"  output: {', '.join(spec.output_schema)}")
        lines.append(f"  input_examples: {'; '.join(spec.input_examples)}")
        lines.append(f"  response_modes: {'; '.join(spec.response_modes)}")
        lines.append(f"  failure_categories: {', '.join(spec.failure_categories)}")
        lines.append(f"  retryable_errors: {', '.join(spec.retryable_errors)}")
        lines.append(f"  safety_rules: {'; '.join(spec.safety_rules)}")
    return "\n".join(lines)
