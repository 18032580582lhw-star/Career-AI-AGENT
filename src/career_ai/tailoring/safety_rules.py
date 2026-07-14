"""Deterministic text-level factual safety rules."""

import re
from typing import Final

from career_ai.tailoring.models import CandidateFact
from career_ai.tailoring.safety_models import SafetyViolationCode

_TECHNOLOGY_NAMES: Final = (
    "Python|Java|JavaScript|TypeScript|Go|Rust|SQL|Kubernetes|Docker|"
    "Spark|Airflow|AWS|Azure|GCP|React|Node\\.js"
)
_TECHNOLOGY_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"\b(?:{_TECHNOLOGY_NAMES})\b",
    re.IGNORECASE,
)
_METRIC_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<!\w)\d+(?:\.\d+)?(?:\+|[%\uFF05])?(?!\w)"
)
_RESPONSIBILITY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b(?:own(?:ed|ership)?|directed|accountable for|responsible for)\b",
    re.IGNORECASE,
)
_SENIORITY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b(?:senior|lead|led|managed a team|headed|principal)\b",
    re.IGNORECASE,
)
_WORD_PATTERN: Final[re.Pattern[str]] = re.compile(r"[\w+#.]+", re.UNICODE)
_STOP_WORDS: Final = frozenset({"a", "an", "and", "for", "in", "of", "the", "to", "with"})
_NEGATIONS: Final = frozenset({"no", "not", "without", "never"})
_RELATION_FILLERS: Final = _STOP_WORDS | frozenset(
    {"about", "approximately", "at", "by", "from"}
)
_CLAUSE_BOUNDARY: Final[re.Pattern[str]] = re.compile(
    r"[.!?;\n]|\b(?:but|however)\b",
    re.IGNORECASE,
)
_CONTROL_INJECTION: Final = (
    r"\b(?:ignore|disregard|override|forget)\s+(?:all\s+)?"
    r"(?:previous|prior|earlier|above)\s+(?:instructions|rules|guidance)\b"
)
_ROLE_PREFIX_INJECTION: Final = (
    r"\b(?:system|developer|assistant)\s*:\s*"
    r"(?:obey|follow|ignore|reveal|print|show|exfiltrate)\b"
)
_ROLE_REASSIGNMENT_INJECTION: Final = (
    r"\byou\s+are\s+now\s+the\s+(?:system|developer|assistant)\b"
)
_SENSITIVE_DATA_ACTION_INJECTION: Final = (
    r"\b(?:reveal|print|show|exfiltrate)\s+(?:the\s+)?"
    r"(?:system\s+(?:prompt|instructions)|hidden\s+instructions|credentials?)\b"
)
_HIDDEN_INSTRUCTION_INJECTION: Final = (
    r"\b(?:obey|follow)\s+(?:my|the|these|following)\s+"
    r"(?:hidden\s+)?instructions\b"
)
_PROMPT_INJECTION_ALTERNATIVES: Final = (
    _CONTROL_INJECTION,
    _ROLE_PREFIX_INJECTION,
    _ROLE_REASSIGNMENT_INJECTION,
    _SENSITIVE_DATA_ACTION_INJECTION,
    _HIDDEN_INSTRUCTION_INJECTION,
)
_PROMPT_INJECTION_SOURCE: Final = (
    rf"(?:{'|'.join(_PROMPT_INJECTION_ALTERNATIVES)})"
)
_PROMPT_INJECTION_PATTERN: Final[re.Pattern[str]] = re.compile(
    _PROMPT_INJECTION_SOURCE,
    re.IGNORECASE,
)


def unsupported_text_codes(
    statement: str,
    referenced: tuple[CandidateFact, ...],
) -> tuple[SafetyViolationCode, ...]:
    """Return stable unsupported-fact categories in deterministic order."""
    source_text = "\n".join(fact.statement for fact in referenced)
    codes: list[SafetyViolationCode] = []
    if _PROMPT_INJECTION_PATTERN.search(statement):
        codes.append(SafetyViolationCode.PROMPT_INJECTION_CONTENT)
    proposed_technologies = {
        match.group(0).casefold() for match in _TECHNOLOGY_PATTERN.finditer(statement)
    }
    source_technologies = {
        match.group(0).casefold() for match in _TECHNOLOGY_PATTERN.finditer(source_text)
    }
    if not proposed_technologies <= source_technologies:
        codes.append(SafetyViolationCode.UNSUPPORTED_TECHNOLOGY)
    if _new_pattern_claim(_RESPONSIBILITY_PATTERN, statement, source_text):
        codes.append(SafetyViolationCode.UNSUPPORTED_RESPONSIBILITY)
    if _new_pattern_claim(_SENIORITY_PATTERN, statement, source_text):
        codes.append(SafetyViolationCode.UNSUPPORTED_SENIORITY)
    proposed_metrics = set(_METRIC_PATTERN.findall(statement))
    source_metrics = set(_METRIC_PATTERN.findall(source_text))
    if not proposed_metrics <= source_metrics:
        codes.append(SafetyViolationCode.UNSUPPORTED_METRIC)
    if not codes and not statement_is_supported(statement, referenced):
        codes.append(SafetyViolationCode.UNSUPPORTED_CLAIM)
    return tuple(codes)


def has_prompt_injection_content(statement: str) -> bool:
    """Return whether text contains a known instruction-control pattern."""
    return _PROMPT_INJECTION_PATTERN.search(statement) is not None


def statement_is_supported(statement: str, referenced: tuple[CandidateFact, ...]) -> bool:
    """Require every significant proposed token to come from cited facts."""
    return text_is_covered(statement, tuple(fact.statement for fact in referenced))


def text_is_covered(statement: str, source_texts: tuple[str, ...]) -> bool:
    """Require authorized tokens, polarity, and metric-to-subject bindings."""
    proposed_words = _significant_words(statement)
    source_text = "\n".join(source_texts)
    source_words = _significant_words(source_text)
    if not proposed_words or not proposed_words <= source_words:
        return False
    unsupported_positive = _positive_words(statement) & (
        _negated_words(source_text) - _positive_words(source_text)
    )
    return not unsupported_positive and _metric_bindings(statement) <= _metric_bindings(
        source_text
    )


def _significant_words(text: str) -> set[str]:
    words = (match.group(0).strip(".") for match in _WORD_PATTERN.finditer(text.casefold()))
    return {word for word in words if word and word not in _STOP_WORDS}


def _negated_words(text: str) -> set[str]:
    negated: set[str] = set()
    for clause in _CLAUSE_BOUNDARY.split(text.casefold()):
        tokens = [match.group(0).strip(".") for match in _WORD_PATTERN.finditer(clause)]
        negation_indexes = [
            index for index, token in enumerate(tokens) if token in _NEGATIONS
        ]
        if negation_indexes:
            negated.update(tokens[min(negation_indexes) + 1 :])
    return negated


def _positive_words(text: str) -> set[str]:
    return _significant_words(text) - _negated_words(text)


def _metric_bindings(text: str) -> set[tuple[str, str]]:
    tokens = [match.group(0).strip(".") for match in _WORD_PATTERN.finditer(text.casefold())]
    bindings: set[tuple[str, str]] = set()
    for index, token in enumerate(tokens):
        if _METRIC_PATTERN.fullmatch(token) is None:
            continue
        subjects = [
            item
            for item in tokens[:index]
            if item.isalpha() and item not in _RELATION_FILLERS
        ]
        if subjects:
            bindings.add((subjects[-1], token))
    return bindings


def _new_pattern_claim(pattern: re.Pattern[str], statement: str, source_text: str) -> bool:
    return pattern.search(statement) is not None and pattern.search(source_text) is None
