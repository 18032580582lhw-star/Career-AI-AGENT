from pathlib import Path

from career_ai.analysis import get_sample_inputs
from career_ai.workflows.career_fit import run_career_fit_workflow


def test_run_career_fit_workflow_returns_report_and_prompt_result() -> None:
    resume_text, jd_text = get_sample_inputs()

    result = run_career_fit_workflow(
        resume_text=resume_text,
        jd_text=jd_text,
        prompt_dir=Path("prompts"),
    )

    assert result.report.jd_analysis.role_title == "AI Product Analyst"
    assert result.prompt_result.best_strategy_name in {
        "conservative",
        "ats-aligned",
        "impact-narrative",
    }
    assert result.steps == [
        "analyze_job_description",
        "score_resume_match",
        "compare_prompt_strategies",
    ]
