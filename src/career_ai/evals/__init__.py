"""Evaluation case loading and grading primitives."""

from career_ai.evals.graders import (
    EvalCaseResult,
    EvalCheckResult,
    grade_case,
    grade_forbidden_claims,
    grade_missing_keywords,
    grade_prompt_strategy_count,
    grade_role_title,
)
from career_ai.evals.loader import EvalCaseLoadError, load_eval_case, load_eval_cases
from career_ai.evals.model_harness_matrix import (
    HarnessConfiguration,
    ModelHarnessMatrixResult,
    ModelHarnessRow,
    ModelHarnessRowResult,
    default_model_harness_rows,
    run_model_harness_matrix,
)
from career_ai.evals.models import CareerEvalCase, EvalCaseInput, ExpectedCareerSignals
from career_ai.evals.runner import EvalSuiteResult, run_eval_suite

__all__ = [
    "CareerEvalCase",
    "EvalCaseInput",
    "EvalCaseLoadError",
    "EvalCaseResult",
    "EvalCheckResult",
    "EvalSuiteResult",
    "ExpectedCareerSignals",
    "HarnessConfiguration",
    "ModelHarnessMatrixResult",
    "ModelHarnessRow",
    "ModelHarnessRowResult",
    "default_model_harness_rows",
    "grade_case",
    "grade_forbidden_claims",
    "grade_missing_keywords",
    "grade_prompt_strategy_count",
    "grade_role_title",
    "load_eval_case",
    "load_eval_cases",
    "run_eval_suite",
    "run_model_harness_matrix",
]
