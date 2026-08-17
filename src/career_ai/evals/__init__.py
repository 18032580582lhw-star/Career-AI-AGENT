"""Evaluation case loading and grading primitives."""

from typing import TYPE_CHECKING

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
from career_ai.evals.models import CareerEvalCase, EvalCaseInput, ExpectedCareerSignals
from career_ai.evals.runner import EvalSuiteResult, run_eval_suite

if TYPE_CHECKING:
    from career_ai.evals.model_harness_matrix import (
        HarnessConfiguration,
        ModelHarnessMatrixResult,
        ModelHarnessRow,
        ModelHarnessRowResult,
        default_model_harness_rows,
        run_model_harness_matrix,
    )

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

def __getattr__(name: str) -> object:
    """Load provider-matrix compatibility exports only on demand."""
    if name == "HarnessConfiguration":
        from career_ai.evals import model_harness_matrix  # noqa: PLC0415

        return model_harness_matrix.HarnessConfiguration
    if name == "ModelHarnessMatrixResult":
        from career_ai.evals import model_harness_matrix  # noqa: PLC0415

        return model_harness_matrix.ModelHarnessMatrixResult
    if name == "ModelHarnessRow":
        from career_ai.evals import model_harness_matrix  # noqa: PLC0415

        return model_harness_matrix.ModelHarnessRow
    if name == "ModelHarnessRowResult":
        from career_ai.evals import model_harness_matrix  # noqa: PLC0415

        return model_harness_matrix.ModelHarnessRowResult
    if name == "default_model_harness_rows":
        from career_ai.evals import model_harness_matrix  # noqa: PLC0415

        return model_harness_matrix.default_model_harness_rows
    if name == "run_model_harness_matrix":
        from career_ai.evals import model_harness_matrix  # noqa: PLC0415

        return model_harness_matrix.run_model_harness_matrix
    raise AttributeError(name)
