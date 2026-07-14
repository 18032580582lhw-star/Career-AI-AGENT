import re
from typing import Final

from career_ai.agent.models import CareerProfileMemory
from career_ai.workflows.models import CareerFitWorkflowResult

REDACTION_TEXT: Final[str] = "[redacted]"
SENSITIVE_MEMORY_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)\b"),
    re.compile(r"\b[A-Za-z]:\\[^\s]+"),
    re.compile(r"/(?:Users|home|tmp|var)/[^\s]+"),
    re.compile(r"\b(?:api[_-]?key|token|secret|password)\s*[:=]\s*\S+", re.IGNORECASE),
)
ROLE_FAMILY_KEYWORDS: Final[tuple[tuple[str, str], ...]] = (
    ("product", "product"),
    ("data", "data"),
    ("engineer", "engineering"),
    ("design", "design"),
    ("market", "marketing"),
    ("sales", "sales"),
)


def redact_memory_unsafe_text(value: str) -> str:
    """Remove contact, credential, and local-path fragments before memory persistence."""
    redacted = value
    for pattern in SENSITIVE_MEMORY_PATTERNS:
        redacted = pattern.sub(REDACTION_TEXT, redacted)
    return " ".join(redacted.split())


def summarize_workflow_for_memory(workflow: CareerFitWorkflowResult) -> CareerProfileMemory:
    """Build a redacted, high-signal career profile from deterministic workflow output."""
    report = workflow.report
    target_role_title = redact_memory_unsafe_text(report.jd_analysis.role_title)
    return CareerProfileMemory(
        target_role_title=target_role_title,
        target_role_family=_target_role_family(target_role_title),
        confirmed_skills=_redacted_unique_values(report.match.matched_keywords),
        recurring_missing_keywords=_redacted_unique_values(
            report.skill_gap.priority_skills or report.match.missing_keywords,
        ),
        preferred_output_language="en",
        last_match_score=report.match.score,
    )


def _redacted_unique_values(values: list[str]) -> list[str]:
    return list(dict.fromkeys(redact_memory_unsafe_text(value) for value in values if value))


def _target_role_family(target_role_title: str) -> str:
    normalized_title = target_role_title.lower()
    for keyword, family in ROLE_FAMILY_KEYWORDS:
        if keyword in normalized_title:
            return family
    return "general"
