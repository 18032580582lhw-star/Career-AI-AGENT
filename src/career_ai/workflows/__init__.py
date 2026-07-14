"""Shared workflow entrypoints for UI, CLI, and agent runtime."""

from career_ai.workflows.career_fit import run_career_fit_workflow
from career_ai.workflows.models import CareerFitWorkflowResult

__all__ = ["CareerFitWorkflowResult", "run_career_fit_workflow"]
