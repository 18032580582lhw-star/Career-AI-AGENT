from typing import Final

from pydantic import Field

from career_ai.llm.boundary_harness import BoundaryViolationCode, check_career_fit_report
from career_ai.llm.client import LLMClient
from career_ai.llm.models import LLMRequest, ModelProvider
from career_ai.models import FrozenModel
from career_ai.text_processing import extract_keywords
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
    """One deterministic quality check for a career workflow result."""

    name: str
    passed: bool
    message: str


class CareerQualityReport(FrozenModel):
    """Deterministic quality gate summary for one career agent run."""

    checks: list[CareerQualityCheck]
    optimizer_iterations: int = Field(default=0, ge=0, le=2)
    model_feedback: list[str] = Field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Return whether every quality check passed."""
        return all(check.passed for check in self.checks)

    @property
    def failed_messages(self) -> list[str]:
        """Return only actionable messages for failed checks."""
        return [check.message for check in self.checks if not check.passed]

    @property
    def summary(self) -> str:
        """Return a compact quality status for CLI and Streamlit surfaces."""
        passed_count = sum(1 for check in self.checks if check.passed)
        status = "passed" if self.passed else "failed"
        return f"quality={status} checks={passed_count}/{len(self.checks)}"


class CareerQualityOptimizerOptions(FrozenModel):
    """Bounded settings for optional model-assisted quality evaluation."""

    enabled: bool = False
    max_iterations: int = Field(default=2, ge=1, le=2)


class ModelQualityEvaluation(FrozenModel):
    """Structured advisory returned by an optional model quality evaluator."""

    passed: bool = False
    feedback: list[str] = Field(default_factory=list)


def assess_career_quality(
    *,
    workflow: CareerFitWorkflowResult,
    resume_text: str,
    jd_text: str,
) -> CareerQualityReport:
    """Assess deterministic trust signals for a career workflow result."""
    return CareerQualityReport(
        checks=[
            _check_factual_consistency(
                workflow=workflow,
                resume_text=resume_text,
                jd_text=jd_text,
            ),
            _check_jd_alignment(workflow=workflow, jd_text=jd_text),
            _check_prompt_strategy_available(workflow),
            _check_missing_keywords_present(workflow),
            _check_document_export_ready(workflow),
        ],
    )


def evaluate_career_quality(
    *,
    workflow: CareerFitWorkflowResult,
    resume_text: str,
    jd_text: str,
    llm_client: LLMClient,
    options: CareerQualityOptimizerOptions,
) -> CareerQualityReport:
    """Return deterministic quality findings plus bounded optional model feedback.

    The evaluator never rewrites career materials. It only supplies actionable
    advisory for a caller that explicitly opts into a later revision workflow.
    """
    report = assess_career_quality(
        workflow=workflow,
        resume_text=resume_text,
        jd_text=jd_text,
    )
    if not _can_run_model_evaluator(
        report=report,
        llm_client=llm_client,
        options=options,
    ):
        return report
    feedback: list[str] = []
    iterations = 0
    for _ in range(options.max_iterations):
        evaluation = _request_model_quality_evaluation(
            llm_client=llm_client,
            report=report,
        )
        iterations += 1
        feedback.extend(evaluation.feedback)
        if evaluation.passed:
            break
    return report.model_copy(
        update={
            "optimizer_iterations": iterations,
            "model_feedback": feedback,
        },
    )


def _can_run_model_evaluator(
    *,
    report: CareerQualityReport,
    llm_client: LLMClient,
    options: CareerQualityOptimizerOptions,
) -> bool:
    return (
        options.enabled
        and not report.passed
        and llm_client.capabilities.supports_structured_output
        and not _is_fake_provider(llm_client.provider)
    )


def _is_fake_provider(provider: ModelProvider) -> bool:
    match provider:
        case ModelProvider.FAKE:
            return True
        case ModelProvider.OPENAI_COMPATIBLE | ModelProvider.DEEPSEEK_COMPATIBLE:
            return False


def _request_model_quality_evaluation(
    *,
    llm_client: LLMClient,
    report: CareerQualityReport,
) -> ModelQualityEvaluation:
    response = llm_client.complete_structured(
        LLMRequest(
            system_prompt=(
                "You are a career quality evaluator. Return JSON with passed (boolean) "
                "and feedback (array of short actionable strings). Do not invent resume "
                "facts or rewrite user materials."
            ),
            user_prompt=(
                "Review these deterministic quality findings and identify only safe, "
                "actionable next improvements.\n\n"
                f"{report.summary}\n"
                f"Failed checks: {report.failed_messages}"
            ),
        ),
    )
    return ModelQualityEvaluation.model_validate(response.content)


def _check_factual_consistency(
    *,
    workflow: CareerFitWorkflowResult,
    resume_text: str,
    jd_text: str,
) -> CareerQualityCheck:
    boundary_result = check_career_fit_report(
        raw_output=workflow.report.model_dump_json(),
        resume_text=resume_text,
        jd_text=jd_text,
    )
    unsupported_violations = [
        violation
        for violation in boundary_result.violations
        if violation.code == BoundaryViolationCode.UNSUPPORTED_FACT
    ]
    passed = not unsupported_violations
    return CareerQualityCheck(
        name=FACTUAL_CONSISTENCY,
        passed=passed,
        message=(
            "Generated materials preserve resume/JD factual markers."
            if passed
            else UNSUPPORTED_FACT_MESSAGE
        ),
    )


def _check_jd_alignment(
    *,
    workflow: CareerFitWorkflowResult,
    jd_text: str,
) -> CareerQualityCheck:
    expected_keywords = set(extract_keywords(jd_text))
    observed_keywords = {
        *workflow.report.match.matched_keywords,
        *workflow.report.match.missing_keywords,
    }
    missing_keywords = sorted(expected_keywords - observed_keywords)
    passed = not missing_keywords
    return CareerQualityCheck(
        name=JD_ALIGNMENT,
        passed=passed,
        message=(
            "Report accounts for all extracted JD keywords."
            if passed
            else f"Report did not account for JD keywords: {', '.join(missing_keywords)}."
        ),
    )


def _check_prompt_strategy_available(workflow: CareerFitWorkflowResult) -> CareerQualityCheck:
    strategy_names = {strategy.name for strategy in workflow.prompt_result.strategies}
    passed = bool(strategy_names) and workflow.prompt_result.best_strategy_name in strategy_names
    return CareerQualityCheck(
        name=PROMPT_STRATEGY_AVAILABLE,
        passed=passed,
        message=(
            "Prompt strategy comparison is available."
            if passed
            else MISSING_PROMPT_STRATEGY_MESSAGE
        ),
    )


def _check_missing_keywords_present(workflow: CareerFitWorkflowResult) -> CareerQualityCheck:
    match_missing = set(workflow.report.match.missing_keywords)
    gap_missing = set(workflow.report.skill_gap.missing_skills)
    missing_from_gap = sorted(match_missing - gap_missing)
    passed = not missing_from_gap
    return CareerQualityCheck(
        name=MISSING_KEYWORDS_PRESENT,
        passed=passed,
        message=(
            "Missing JD keywords are reflected in the skill gap."
            if passed
            else f"Skill gap omits missing keywords: {', '.join(missing_from_gap)}."
        ),
    )


def _check_document_export_ready(workflow: CareerFitWorkflowResult) -> CareerQualityCheck:
    report = workflow.report
    passed = bool(report.cover_letter_draft.strip()) and bool(report.rewritten_resume.strip())
    return CareerQualityCheck(
        name=DOCUMENT_EXPORT_READY,
        passed=passed,
        message=(
            "Cover letter and rewritten resume text are ready for DOCX export."
            if passed
            else "Cover letter and rewritten resume must both be non-empty before DOCX export."
        ),
    )
