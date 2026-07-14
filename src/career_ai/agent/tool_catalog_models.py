"""Typed contracts for the model-visible tool catalog."""

from career_ai.agent.tool_models import ToolName
from career_ai.models import FrozenModel


class ToolSpecNotFoundError(LookupError):
    """Raised when a requested tool spec is missing from a catalog."""

    def __init__(self, name: ToolName) -> None:
        """Create a missing-tool error."""
        self.name: ToolName = name
        super().__init__(f"Tool spec not found: {name.value}")


class ToolInputField(FrozenModel):
    """One model-visible input field for a local tool."""

    name: str
    type_name: str
    required: bool
    description: str


class ToolSpec(FrozenModel):
    """Model-visible schema and operating constraints for one tool."""

    name: ToolName
    display_name: str
    description: str
    input_schema: list[ToolInputField]
    input_examples: list[str]
    output_schema: list[str]
    response_modes: list[str]
    is_critical: bool
    failure_categories: list[str]
    retryable_errors: list[str]
    safety_rules: list[str]


class ToolCatalog(FrozenModel):
    """Model-visible catalog for all local career-agent tools."""

    tools: list[ToolSpec]

    def require(self, name: ToolName) -> ToolSpec:
        """Return a tool spec or raise if it is absent."""
        for spec in self.tools:
            if spec.name == name:
                return spec
        raise ToolSpecNotFoundError(name)
