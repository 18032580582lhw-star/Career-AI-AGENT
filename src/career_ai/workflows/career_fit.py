from pathlib import Path
from typing import Final

from career_ai.analysis import analyze_career_fit
from career_ai.prompt_harness import compare_prompt_strategies
from career_ai.workflows.models import CareerFitWorkflowResult

WORKFLOW_STEPS: Final[list[str]] = [
    "analyze_job_description",
    "score_resume_match",
    "compare_prompt_strategies",
]


def run_career_fit_workflow(
    *,
    resume_text: str,
    jd_text: str,
    prompt_dir: Path,
) -> CareerFitWorkflowResult:
    """Run the local deterministic career-fit workflow."""
    report = analyze_career_fit(resume_text=resume_text, jd_text=jd_text)
    prompt_result = compare_prompt_strategies(
        prompt_dir=prompt_dir,
        resume_text=resume_text,
        jd_text=jd_text,
    )
    return CareerFitWorkflowResult(
        report=report,
        prompt_result=prompt_result,
        steps=WORKFLOW_STEPS,
    )
