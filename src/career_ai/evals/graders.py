from typing import Final

from pydantic import Field

from career_ai.evals.models import CareerEvalCase
from career_ai.models import BulletSuggestion, FrozenModel
from career_ai.workflows.models import CareerFitWorkflowResult

ROLE_TITLE_CHECK: Final[str] = "role_title"
MISSING_KEYWORDS_CHECK: Final[str] = "missing_keywords"
FORBIDDEN_CLAIMS_CHECK: Final[str] = "forbidden_claims"
PROMPT_STRATEGY_COUNT_CHECK: Final[str] = "prompt_strategy_count"


class EvalCheckResult(FrozenModel):
    """Result for one deterministic eval check."""

    name: str = Field(min_length=1)
    passed: bool
    message: str = Field(min_length=1)


class EvalCaseResult(FrozenModel):
    """Aggregate result for one career eval case."""

    case_id: str = Field(min_length=1)
    passed: bool
    checks: list[EvalCheckResult]


def grade_role_title(
    case: CareerEvalCase,
    workflow_result: CareerFitWorkflowResult,
) -> EvalCheckResult:
    """Check whether the workflow extracted the expected role title."""
    expected = case.expected.role_title
    actual = workflow_result.report.jd_analysis.role_title
    passed = _normalize_text(actual) == _normalize_text(expected)
    return EvalCheckResult(
        name=ROLE_TITLE_CHECK,
        passed=passed,
        message=f"Expected role title '{expected}', observed '{actual}'.",
    )


def grade_missing_keywords(
    case: CareerEvalCase,
    workflow_result: CareerFitWorkflowResult,
) -> EvalCheckResult:
    """Check whether required missing keywords are present in the report."""
    observed_keywords = [
        *workflow_result.report.match.missing_keywords,
        *workflow_result.report.skill_gap.missing_skills,
    ]
    missing_required = _missing_expected_items(
        expected=case.expected.required_missing_keywords,
        observed=observed_keywords,
    )
    passed = not missing_required
    return EvalCheckResult(
        name=MISSING_KEYWORDS_CHECK,
        passed=passed,
        message=_coverage_message(
            label="missing keywords",
            expected=case.expected.required_missing_keywords,
            missing=missing_required,
        ),
    )


def grade_forbidden_claims(
    case: CareerEvalCase,
    workflow_result: CareerFitWorkflowResult,
) -> EvalCheckResult:
    """Check whether generated application materials avoid forbidden new claims."""
    generated_text = _render_generated_text(workflow_result)
    generated_normalized = _normalize_text(generated_text)
    detected_claims = [
        claim
        for claim in case.expected.forbidden_new_claims
        if _normalize_text(claim) in generated_normalized
    ]
    passed = not detected_claims
    return EvalCheckResult(
        name=FORBIDDEN_CLAIMS_CHECK,
        passed=passed,
        message=_forbidden_claims_message(detected_claims),
    )


def grade_prompt_strategy_count(
    case: CareerEvalCase,
    workflow_result: CareerFitWorkflowResult,
) -> EvalCheckResult:
    """Check whether the prompt harness evaluated enough strategies."""
    actual_count = len(workflow_result.prompt_result.strategies)
    expected_minimum = case.expected.prompt_strategy_count_min
    passed = actual_count >= expected_minimum
    return EvalCheckResult(
        name=PROMPT_STRATEGY_COUNT_CHECK,
        passed=passed,
        message=f"Prompt strategies observed: {actual_count}/{expected_minimum}.",
    )


def grade_case(
    case: CareerEvalCase,
    workflow_result: CareerFitWorkflowResult,
) -> EvalCaseResult:
    """Run every deterministic grader for one eval case."""
    checks = [
        grade_role_title(case, workflow_result),
        grade_missing_keywords(case, workflow_result),
        grade_forbidden_claims(case, workflow_result),
        grade_prompt_strategy_count(case, workflow_result),
    ]
    return EvalCaseResult(
        case_id=case.id,
        passed=all(check.passed for check in checks),
        checks=checks,
    )


def _missing_expected_items(*, expected: list[str], observed: list[str]) -> list[str]:
    observed_normalized = {_normalize_text(item) for item in observed}
    return [
        item
        for item in expected
        if _normalize_text(item) not in observed_normalized
    ]


def _coverage_message(*, label: str, expected: list[str], missing: list[str]) -> str:
    if not expected:
        return f"No required {label} configured."
    if not missing:
        return f"All required {label} were reported."
    return f"Missing required {label}: {', '.join(missing)}."


def _forbidden_claims_message(detected_claims: list[str]) -> str:
    if not detected_claims:
        return "No forbidden claims found."
    return f"Forbidden claims found: {', '.join(detected_claims)}."


def _render_generated_text(workflow_result: CareerFitWorkflowResult) -> str:
    report = workflow_result.report
    suggestion_text = "\n".join(
        _render_bullet_suggestion(suggestion)
        for suggestion in report.bullet_suggestions
    )
    return "\n".join(
        [
            report.match.summary,
            *report.skill_gap.notes,
            suggestion_text,
            report.cover_letter_draft,
            report.rewritten_resume,
        ],
    )


def _render_bullet_suggestion(suggestion: BulletSuggestion) -> str:
    return "\n".join(
        [
            suggestion.original,
            suggestion.improved,
            *suggestion.jd_keywords_used,
            suggestion.factual_consistency_note,
        ],
    )


def _normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())
