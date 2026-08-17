import re
from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Final, override

from pydantic import Field

from career_ai.evals.models import CareerEvalCase, EvalCaseInput, ExpectedCareerSignals
from career_ai.models import FrozenModel
from career_ai.workflows.run_record import (
    CareerFitRunRecord,
    RunQualityCheckRecord,
)

RECOVERABLE_FAILURE_STATUS: Final[str] = "failed-recoverable"
COMPLETED_WITH_RECOVERY_STATUS: Final[str] = "completed-with-recovery"
DEFAULT_DRAFT_PROMPT_STRATEGY_MIN: Final[int] = 3
CONTACT_NAME_PATTERN_PREFIX: Final[str] = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\s+"
CONTACT_NAME_PATTERN_SUFFIX: Final[str] = r"(?=[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"
CONTACT_NAME_PATTERN: Final[str] = f"{CONTACT_NAME_PATTERN_PREFIX}{CONTACT_NAME_PATTERN_SUFFIX}"
CREDENTIAL_PATTERN_PREFIX: Final[str] = r"\b(?:sk-[A-Za-z0-9_-]{8,}|Bearer\s+[A-Za-z0-9._-]+|"
CREDENTIAL_PATTERN_SUFFIX: Final[str] = r"api[_-]?key\s*=\s*[A-Za-z0-9._-]+)"
CREDENTIAL_PATTERN: Final[str] = f"{CREDENTIAL_PATTERN_PREFIX}{CREDENTIAL_PATTERN_SUFFIX}"


@unique
class FailureCorpusReviewState(StrEnum):
    """Review lifecycle for a run-record-derived regression candidate."""

    CANDIDATE = "candidate"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CONVERTED_TO_EVAL = "converted_to_eval"


class FailureCorpusInputSummary(FrozenModel):
    """Sanitized input-size summary copied from a failed trace."""

    resume_character_count: int = Field(ge=0)
    jd_character_count: int = Field(ge=0)


class FailureCorpusRecord(FrozenModel):
    """Sanitized workflow candidate for future regression coverage."""

    id: str = Field(min_length=1)
    source_run_id: str = Field(min_length=1)
    review_state: FailureCorpusReviewState
    failure_category: str = Field(min_length=1)
    operation: str = Field(min_length=1)
    final_status: str = Field(min_length=1)
    input_summary: FailureCorpusInputSummary
    expected_behavior: str = Field(min_length=1)
    step_names: list[str] = Field(default_factory=list)
    quality_checks: list[RunQualityCheckRecord] = Field(default_factory=list)
    feedback: str = ""

    def move_to(self, state: FailureCorpusReviewState) -> "FailureCorpusRecord":
        """Return a copy with the review state advanced."""
        return self.model_copy(update={"review_state": state})


@dataclass(frozen=True, slots=True)
class FailureCorpusConversionError(Exception):
    """Raised when a candidate cannot become an eval draft yet."""

    record_id: str
    state: FailureCorpusReviewState

    @override
    def __str__(self) -> str:
        """Return a concise conversion failure message."""
        return f"failure corpus record {self.record_id} is {self.state.value}, not accepted"


def create_failure_candidate(
    run_record: CareerFitRunRecord,
    feedback: str | None = None,
) -> FailureCorpusRecord:
    """Create a sanitized regression candidate from a workflow run record."""
    record = FailureCorpusRecord(
        id=f"failure-{_slugify(run_record.run_id)}",
        source_run_id=run_record.run_id,
        review_state=FailureCorpusReviewState.CANDIDATE,
        failure_category=_failure_category(run_record.final_status),
        operation=run_record.operation,
        final_status=run_record.final_status,
        input_summary=FailureCorpusInputSummary(
            resume_character_count=run_record.input_summary.resume_character_count,
            jd_character_count=run_record.input_summary.jd_character_count,
        ),
        expected_behavior=run_record.expected_behavior,
        step_names=run_record.step_names,
        quality_checks=run_record.quality_checks,
        feedback=feedback or "",
    )
    return sanitize_failure_record(record)


def sanitize_failure_record(record: FailureCorpusRecord) -> FailureCorpusRecord:
    """Redact sensitive strings from a failure-corpus record."""
    return record.model_copy(
        update={
            "id": _sanitize_text(record.id),
            "source_run_id": _sanitize_text(record.source_run_id),
            "failure_category": _sanitize_text(record.failure_category),
            "operation": _sanitize_text(record.operation),
            "final_status": _sanitize_text(record.final_status),
            "expected_behavior": _sanitize_text(record.expected_behavior),
            "step_names": [_sanitize_text(name) for name in record.step_names],
            "quality_checks": [
                check.model_copy(
                    update={
                        "name": _sanitize_text(check.name),
                        "code": _sanitize_text(check.code),
                    },
                )
                for check in record.quality_checks
            ],
            "feedback": _sanitize_text(record.feedback),
        },
    )


def failure_record_to_eval_case_draft(record: FailureCorpusRecord) -> CareerEvalCase:
    """Convert an accepted failure candidate into a redacted eval-case draft."""
    record = sanitize_failure_record(record)
    match record.review_state:
        case FailureCorpusReviewState.ACCEPTED:
            return CareerEvalCase(
                id=record.id,
                name=f"Regression draft for {record.source_run_id}",
                input=EvalCaseInput(
                    resume_text=(
                        f"[REDACTED_RESUME: "
                        f"{record.input_summary.resume_character_count} characters]"
                    ),
                    jd_text=(
                        f"[REDACTED_JD: {record.input_summary.jd_character_count} characters]"
                    ),
                ),
                expected=ExpectedCareerSignals(
                    role_title="Redacted target role",
                    required_missing_keywords=[],
                    forbidden_new_claims=[
                        f"Do not repeat failure: {record.expected_behavior}",
                    ],
                    prompt_strategy_count_min=DEFAULT_DRAFT_PROMPT_STRATEGY_MIN,
                ),
            )
        case (
            FailureCorpusReviewState.CANDIDATE
            | FailureCorpusReviewState.REJECTED
            | FailureCorpusReviewState.CONVERTED_TO_EVAL
        ):
            raise FailureCorpusConversionError(
                record_id=record.id,
                state=record.review_state,
            )


def _failure_category(final_status: str) -> str:
    if final_status == "failed-quality":
        return "failed_quality_check"
    if final_status == RECOVERABLE_FAILURE_STATUS:
        return "recoverable_tool_failure"
    if final_status == COMPLETED_WITH_RECOVERY_STATUS:
        return "recovered_tool_failure"
    return "failed_run"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "unknown-run"


def _sanitize_text(value: str) -> str:
    sanitized = value
    for pattern, replacement in REDACTION_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


REDACTION_PATTERNS: Final[tuple[tuple[re.Pattern[str], str], ...]] = (
    (
        re.compile(CONTACT_NAME_PATTERN),
        "[contact-name] ",
    ),
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[contact-email]",
    ),
    (
        re.compile(r"\b(?:\+?\d[\d .()\-]{7,}\d)\b"),
        "[contact-phone]",
    ),
    (
        re.compile(r"\b[A-Za-z]:\\[^\s,;]+"),
        "[local-path]",
    ),
    (
        re.compile(r"(?:/Users|/home|/tmp|/var)/[^\s,;]+"),
        "[local-path]",
    ),
    (
        re.compile(CREDENTIAL_PATTERN, flags=re.IGNORECASE),
        "[credential]",
    ),
)
