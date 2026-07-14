from career_ai.agent.tool_catalog import default_tool_catalog, render_tool_catalog_for_prompt
from career_ai.agent.tools import ToolName


def test_default_tool_catalog_describes_core_tool_schema() -> None:
    # Given: the built-in catalog exposed to the planner.
    catalog = default_tool_catalog()

    # When: the core analysis tool is selected.
    analyze_tool = catalog.require(ToolName.ANALYZE_CAREER_FIT)

    # Then: its existing execution schema remains available.
    assert analyze_tool.name == ToolName.ANALYZE_CAREER_FIT
    assert analyze_tool.is_critical
    assert [field.name for field in analyze_tool.input_schema] == [
        "resume_text",
        "jd_text",
    ]
    assert all(field.required for field in analyze_tool.input_schema)
    assert "Do not invent resume facts." in analyze_tool.safety_rules


def test_default_tool_catalog_provides_v2_model_guidance_for_every_tool() -> None:
    # Given: the default catalog.
    catalog = default_tool_catalog()

    # When: each model-visible tool specification is inspected.
    tools = catalog.tools

    # Then: every tool has namespaced, actionable, and recoverable guidance.
    assert all(tool.display_name.startswith("career_ai.") for tool in tools)
    assert all(tool.input_examples for tool in tools)
    assert all(tool.response_modes for tool in tools)
    assert all(tool.failure_categories for tool in tools)
    assert all(tool.retryable_errors for tool in tools)
    assert all(tool.safety_rules for tool in tools)


def test_render_tool_catalog_for_prompt_includes_tool_constraints() -> None:
    # Given: the default model-visible catalog.
    prompt_text = render_tool_catalog_for_prompt(default_tool_catalog())

    # When: the catalog is rendered for a planner prompt.

    # Then: the compact output carries the v2 operating contract.
    assert "career_ai.analyze_career_fit" in prompt_text
    assert "input: resume_text str required" in prompt_text
    assert "input_examples:" in prompt_text
    assert "response_modes:" in prompt_text
    assert "failure_categories:" in prompt_text
    assert "critical: yes" in prompt_text
    assert "Do not invent resume facts." in prompt_text
