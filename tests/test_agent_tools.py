from pathlib import Path

from career_ai.agent.tools import (
    AgentToolContext,
    AnalyzeCareerFitInput,
    ComparePromptStrategiesInput,
    ToolCall,
    ToolName,
    ToolStatus,
    default_tool_registry,
)
from career_ai.analysis import get_sample_inputs


def test_default_tool_registry_contains_core_career_tools() -> None:
    registry = default_tool_registry()

    assert registry.names() == [
        ToolName.FETCH_JD,
        ToolName.EXTRACT_RESUME,
        ToolName.ANALYZE_CAREER_FIT,
        ToolName.COMPARE_PROMPT_STRATEGIES,
        ToolName.EXPORT_RESUME_DOCX,
        ToolName.EXPORT_COVER_LETTER_DOCX,
        ToolName.SAVE_MEMORY_SUMMARY,
    ]


def test_tool_registry_runs_analysis_and_prompt_tools() -> None:
    resume_text, jd_text = get_sample_inputs()
    registry = default_tool_registry()
    context = AgentToolContext(prompt_dir=Path("prompts"))

    analysis_result = registry.run(
        ToolCall(
            name=ToolName.ANALYZE_CAREER_FIT,
            arguments=AnalyzeCareerFitInput(
                resume_text=resume_text,
                jd_text=jd_text,
            ),
        ),
        context,
    )
    prompt_result = registry.run(
        ToolCall(
            name=ToolName.COMPARE_PROMPT_STRATEGIES,
            arguments=ComparePromptStrategiesInput(
                resume_text=resume_text,
                jd_text=jd_text,
                prompt_dir=Path("prompts"),
            ),
        ),
        context,
    )

    assert analysis_result.status == ToolStatus.SUCCESS
    assert analysis_result.report is not None
    assert analysis_result.report.jd_analysis.role_title == "AI Product Analyst"
    assert prompt_result.status == ToolStatus.SUCCESS
    assert prompt_result.prompt_result is not None
    assert prompt_result.prompt_result.best_strategy_name in {
        "conservative",
        "ats-aligned",
        "impact-narrative",
    }


def test_tool_registry_rejects_mismatched_arguments() -> None:
    registry = default_tool_registry()

    result = registry.run(
        ToolCall(
            name=ToolName.ANALYZE_CAREER_FIT,
            arguments=ComparePromptStrategiesInput(
                resume_text="resume",
                jd_text="jd",
                prompt_dir=Path("prompts"),
            ),
        ),
        AgentToolContext(prompt_dir=Path("prompts")),
    )

    assert result.status == ToolStatus.FAILURE
    assert result.recoverable
    assert "expected AnalyzeCareerFitInput" in result.message


def test_tool_registry_reports_a_missing_strategy_profile_as_recoverable(
    tmp_path: Path,
) -> None:
    resume_text, jd_text = get_sample_inputs()

    result = default_tool_registry().run(
        ToolCall(
            name=ToolName.COMPARE_PROMPT_STRATEGIES,
            arguments=ComparePromptStrategiesInput(
                resume_text=resume_text,
                jd_text=jd_text,
                prompt_dir=tmp_path,
            ),
        ),
        AgentToolContext(prompt_dir=tmp_path),
    )

    assert result.status is ToolStatus.FAILURE
    assert result.recoverable
    assert result.message == "Strategy profile is unavailable."
