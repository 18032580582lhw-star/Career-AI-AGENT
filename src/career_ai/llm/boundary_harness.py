import re
from enum import StrEnum, unique
from typing import Final

from pydantic import Field, ValidationError

from career_ai.models import CareerFitReport, FrozenModel
from career_ai.text_processing import extract_keywords, split_resume_bullets

YEAR_PATTERN: Final[re.Pattern[str]] = re.compile(r"\b(?:19|20)\d{2}\b")
PERCENT_PATTERN: Final[re.Pattern[str]] = re.compile(r"\b\d+(?:\.\d+)?%\b")
CAPITALIZED_PATTERN: Final[re.Pattern[str]] = re.compile(r"\b[A-Z][a-zA-Z0-9+#.-]{2,}\b")
ACRONYM_PATTERN: Final[re.Pattern[str]] = re.compile(r"\b[A-Z]{2,}\b")
MIN_MATCH_SCORE: Final[int] = 0
MAX_MATCH_SCORE: Final[int] = 100

COMMON_SENTENCE_STARTS: Final[frozenset[str]] = frozenset(
    {
        "analyzed",
        "built",
        "candidate",
        "dear",
        "evaluated",
        "presented",
        "product",
        "role",
    },
)


@unique
class BoundaryViolationCode(StrEnum):
    """Stable codes for model boundary violations."""

    INVALID_JSON = "invalid_json"
    SCHEMA_ERROR = "schema_error"
    SCORE_OUT_OF_RANGE = "score_out_of_range"
    ORIGINAL_NOT_IN_RESUME = "original_not_in_resume"
    KEYWORD_NOT_IN_JD = "keyword_not_in_jd"
    UNSUPPORTED_FACT = "unsupported_fact"


class BoundaryViolation(FrozenModel):
    """One reason an LLM output cannot enter the agent as trusted data."""

    code: BoundaryViolationCode
    field_path: str
    message: str


class BoundaryCheckResult(FrozenModel):
    """Result of checking an LLM-generated career report."""

    report: CareerFitReport | None = None
    violations: list[BoundaryViolation] = Field(default_factory=list)

    @property
    def accepted(self) -> bool:
        """Return whether the model output is safe to use."""
        return self.report is not None and not self.violations


class BoundaryGuardResult(FrozenModel):
    """Trusted report selected after applying the model boundary."""

    report: CareerFitReport
    used_fallback: bool
    violations: list[BoundaryViolation] = Field(default_factory=list)


def check_career_fit_report(
    *,
    raw_output: str,
    resume_text: str,
    jd_text: str,
) -> BoundaryCheckResult:
    """Parse and check a model-generated CareerFitReport."""
    try:
        report = CareerFitReport.model_validate_json(raw_output)
    except ValidationError as error:
        return BoundaryCheckResult(violations=[_parse_violation(error)])

    violations = _collect_report_violations(
        report=report,
        resume_text=resume_text,
        jd_text=jd_text,
    )
    if violations:
        return BoundaryCheckResult(violations=violations)
    return BoundaryCheckResult(report=report)


def guard_career_fit_report(
    *,
    raw_output: str,
    resume_text: str,
    jd_text: str,
    fallback_report: CareerFitReport,
) -> BoundaryGuardResult:
    """Return a model report only when it passes the boundary checks."""
    result = check_career_fit_report(
        raw_output=raw_output,
        resume_text=resume_text,
        jd_text=jd_text,
    )
    if result.report is not None and not result.violations:
        return BoundaryGuardResult(
            report=result.report,
            used_fallback=False,
            violations=[],
        )
    return BoundaryGuardResult(
        report=fallback_report,
        used_fallback=True,
        violations=result.violations,
    )


def _parse_violation(error: ValidationError) -> BoundaryViolation:
    message = str(error)
    if "json_invalid" in message:
        return BoundaryViolation(
            code=BoundaryViolationCode.INVALID_JSON,
            field_path="$",
            message="Model output must be valid JSON.",
        )
    return BoundaryViolation(
        code=BoundaryViolationCode.SCHEMA_ERROR,
        field_path="$",
        message="Model output must match CareerFitReport.",
    )


def _collect_report_violations(
    *,
    report: CareerFitReport,
    resume_text: str,
    jd_text: str,
) -> list[BoundaryViolation]:
    violations: list[BoundaryViolation] = []
    if report.match.score < MIN_MATCH_SCORE or report.match.score > MAX_MATCH_SCORE:
        violations.append(
            BoundaryViolation(
                code=BoundaryViolationCode.SCORE_OUT_OF_RANGE,
                field_path="match.score",
                message="Match score must be between 0 and 100.",
            ),
        )
    violations.extend(_bullet_anchor_violations(report=report, resume_text=resume_text))
    violations.extend(_keyword_violations(report=report, jd_text=jd_text))
    violations.extend(
        _unsupported_fact_violations(report=report, resume_text=resume_text, jd_text=jd_text),
    )
    return violations


def _bullet_anchor_violations(
    *,
    report: CareerFitReport,
    resume_text: str,
) -> list[BoundaryViolation]:
    source_bullets = {_normalize_bullet(bullet) for bullet in split_resume_bullets(resume_text)}
    violations: list[BoundaryViolation] = []
    for index, suggestion in enumerate(report.bullet_suggestions):
        if _normalize_bullet(suggestion.original) not in source_bullets:
            violations.append(
                BoundaryViolation(
                    code=BoundaryViolationCode.ORIGINAL_NOT_IN_RESUME,
                    field_path=f"bullet_suggestions[{index}].original",
                    message="Suggestion original must come from the source resume.",
                ),
            )
    return violations


def _keyword_violations(
    *,
    report: CareerFitReport,
    jd_text: str,
) -> list[BoundaryViolation]:
    jd_keywords = set(extract_keywords(jd_text))
    violations: list[BoundaryViolation] = []
    for index, suggestion in enumerate(report.bullet_suggestions):
        invalid_keywords = [
            keyword
            for keyword in suggestion.jd_keywords_used
            if keyword.lower() not in jd_keywords
        ]
        if invalid_keywords:
            violations.append(
                BoundaryViolation(
                    code=BoundaryViolationCode.KEYWORD_NOT_IN_JD,
                    field_path=f"bullet_suggestions[{index}].jd_keywords_used",
                    message="JD keywords used by a suggestion must come from the JD.",
                ),
            )
    return violations


def _unsupported_fact_violations(
    *,
    report: CareerFitReport,
    resume_text: str,
    jd_text: str,
) -> list[BoundaryViolation]:
    allowed_terms = _fact_terms(f"{resume_text}\n{jd_text}")
    rewritten_terms = _fact_terms(report.rewritten_resume)
    unsupported_terms = rewritten_terms - allowed_terms
    if not unsupported_terms:
        return []
    return [
        BoundaryViolation(
            code=BoundaryViolationCode.UNSUPPORTED_FACT,
            field_path="rewritten_resume",
            message="Rewritten resume includes unsupported factual markers.",
        ),
    ]


def _normalize_bullet(text: str) -> str:
    cleaned = text.strip().strip("-").strip().rstrip(".")
    return " ".join(cleaned.lower().split())


def _fact_terms(text: str) -> set[str]:
    terms = {
        match.group(0).lower()
        for pattern in (YEAR_PATTERN, PERCENT_PATTERN, ACRONYM_PATTERN)
        for match in pattern.finditer(text)
    }
    capitalized_terms = {
        match.group(0).lower()
        for match in CAPITALIZED_PATTERN.finditer(text)
        if match.group(0).lower() not in COMMON_SENTENCE_STARTS
    }
    return terms | capitalized_terms
