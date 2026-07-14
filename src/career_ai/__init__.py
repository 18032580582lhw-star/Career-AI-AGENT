"""Public API for the AI Career Intelligence Suite domain package."""

from career_ai.analysis import analyze_career_fit, get_sample_inputs, improve_resume_bullets
from career_ai.exporters import build_cover_letter_docx, build_resume_docx
from career_ai.jd_fetcher import fetch_job_description_from_url
from career_ai.prompt_harness import compare_prompt_strategies
from career_ai.workflows.career_fit import run_career_fit_workflow

__all__ = [
    "analyze_career_fit",
    "build_cover_letter_docx",
    "build_resume_docx",
    "compare_prompt_strategies",
    "fetch_job_description_from_url",
    "get_sample_inputs",
    "improve_resume_bullets",
    "run_career_fit_workflow",
]
