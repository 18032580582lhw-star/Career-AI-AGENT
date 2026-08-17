from typing import Final

from career_ai.models import FrozenModel
from career_ai.text_processing import extract_keywords
from career_ai.workflows.factual_boundary import (
    BoundaryViolationCode,
    check_career_fit_report,
)
from career_ai.workflows.models import CareerFitWorkflowResult

FACTUAL_CONSISTENCY: Final[str] = "factual_consistency"
JD_ALIGNMENT: Final[str] = "jd_alignment"
PROMPT_STRATEGY_AVAILABLE: Final[str] = "prompt_strategy_available"
MISSING_KEYWORDS_PRESENT: Final[str] = "missing_keywords_present"
DOCUMENT_EXPORT_READY: Final[str] = "document_export_ready"
UNSUPPORTED_FACT_MESSAGE: Final[str] = (
    "Rewritten resume includes unsupported factual markers; "
    "remove claims not present in the resume or JD."
)
MISSING_PROMPT_STRATEGY_MESSAGE: Final[str] = (
    "No prompt strategy result is available; "
    "run compare_prompt_strategies before trusting the report."
)


class CareerQualityCheck(FrozenModel):
    """One deterministic quality check."""

    name: str
    passed: bool
    message: str


class CareerQualityReport(FrozenModel):
    """Deterministic quality gate summary."""

    checks: list[CareerQualityCheck]

    @property
    def passed(self) -> bool:
        """Return whether all checks passed."""
        return all(check.passed for check in self.checks)

    @property
    def failed_messages(self) -> list[str]:
        """Return actionable messages for failed checks."""
        return [check.message for check in self.checks if not check.passed]

    @property
    def summary(self) -> str:
        """Return a compact deterministic status summary."""
        passed_count = sum(check.passed for check in self.checks)
        status = "passed" if self.passed else "failed"
        return f"quality={status} checks={passed_count}/{len(self.checks)}"


def assess_career_quality(
    *, workflow: CareerFitWorkflowResult, resume_text: str, jd_text: str
) -> CareerQualityReport:
    """Assess deterministic trust signals for a workflow result."""
    boundary = check_career_fit_report(
        raw_output=workflow.report.model_dump_json(),
        resume_text=resume_text,
        jd_text=jd_text,
    )
    unsupported = any(
        violation.code == BoundaryViolationCode.UNSUPPORTED_FACT
        for violation in boundary.violations
    )
    expected_keywords = set(extract_keywords(jd_text))
    observed_keywords = {
        *workflow.report.match.matched_keywords,
        *workflow.report.match.missing_keywords,
    }
    missing_alignment = sorted(expected_keywords - observed_keywords)
    strategy_names = {item.name for item in workflow.prompt_result.strategies}
    strategy_available = (
        bool(strategy_names) and workflow.prompt_result.best_strategy_name in strategy_names
    )
    match_missing = set(workflow.report.match.missing_keywords)
    gap_missing = set(workflow.report.skill_gap.missing_skills)
    gap_omissions = sorted(match_missing - gap_missing)
    export_ready = bool(workflow.report.cover_letter_draft.strip()) and bool(
        workflow.report.rewritten_resume.strip()
    )
    return CareerQualityReport(
        checks=[
            CareerQualityCheck(
                name=FACTUAL_CONSISTENCY,
                passed=not unsupported,
                message=(
                    "Generated materials preserve resume/JD factual markers."
                    if not unsupported
                    else UNSUPPORTED_FACT_MESSAGE
                ),
            ),
            CareerQualityCheck(
                name=JD_ALIGNMENT,
                passed=not missing_alignment,
                message=(
                    "Report accounts for all extracted JD keywords."
                    if not missing_alignment
                    else f"Report did not account for JD keywords: {', '.join(missing_alignment)}."
                ),
            ),
            CareerQualityCheck(
                name=PROMPT_STRATEGY_AVAILABLE,
                passed=strategy_available,
                message=(
                    "Prompt strategy comparison is available."
                    if strategy_available
                    else MISSING_PROMPT_STRATEGY_MESSAGE
                ),
            ),
            CareerQualityCheck(
                name=MISSING_KEYWORDS_PRESENT,
                passed=not gap_omissions,
                message=(
                    "Missing JD keywords are reflected in the skill gap."
                    if not gap_omissions
                    else f"Skill gap omits missing keywords: {', '.join(gap_omissions)}."
                ),
            ),
            CareerQualityCheck(
                name=DOCUMENT_EXPORT_READY,
                passed=export_ready,
                message=(
                    "Cover letter and rewritten resume text are ready for DOCX export."
                    if export_ready
                    else (
                        "Cover letter and rewritten resume must both be non-empty "
                        "before DOCX export."
                    )
                ),
            ),
        ]
    )
