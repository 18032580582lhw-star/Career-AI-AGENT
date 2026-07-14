"""Text and scoring helpers for optimization adequacy."""

from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from career_ai.tailoring.models import JDRequirement

_WORD_PATTERN: Final[re.Pattern[str]] = re.compile(r"[\w+#.]+", re.UNICODE)
_STOP_WORDS: Final = frozenset(
    {"and", "capability", "experience", "for", "required", "the", "with"}
)
_KEYWORD_REPEAT_LIMIT: Final = 4
_KEYWORD_DENSITY_LIMIT: Final = 0.20
_READABILITY_LINE_WORD_LIMIT: Final = 60
_MIN_MEANINGFUL_TERM_LENGTH: Final = 3


def coverage_score(covered: int, total: int) -> int:
    """Return a display-only integer coverage score."""
    return 100 if total == 0 else round((covered / total) * 100)


def is_material_change(before: str, after: str) -> bool:
    """Reject whitespace/case-only changes as substantive optimization."""
    return _words(before) != _words(after)


def has_keyword_stuffing(text: str, requirements: tuple[JDRequirement, ...]) -> bool:
    """Detect excessive density of meaningful JD terms in the whole output."""
    words = _words(text)
    if not words:
        return False
    requirement_terms = {
        word
        for requirement in requirements
        for word in _words(requirement.statement)
        if len(word) >= _MIN_MEANINGFUL_TERM_LENGTH
        and word not in _STOP_WORDS
        and not word.isdigit()
    }
    counts = Counter(word for word in words if word in requirement_terms)
    return any(
        count >= _KEYWORD_REPEAT_LIMIT and count / len(words) >= _KEYWORD_DENSITY_LIMIT
        for count in counts.values()
    )


def has_readability_regression(baseline: str, projected: str) -> bool:
    """Reject a newly introduced overlong line while preserving legacy input."""
    return (
        _max_line_words(projected) > _READABILITY_LINE_WORD_LIMIT
        and _max_line_words(baseline) <= _READABILITY_LINE_WORD_LIMIT
    )


def _max_line_words(text: str) -> int:
    return max((len(_words(line)) for line in text.splitlines()), default=0)


def _words(text: str) -> tuple[str, ...]:
    return tuple(match.group(0).strip(".").casefold() for match in _WORD_PATTERN.finditer(text))
