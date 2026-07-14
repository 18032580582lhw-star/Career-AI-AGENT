import re
from typing import Final

from career_ai.tailoring.extraction_shared import (
    ArtifactPrefix,
    SourceLine,
    extract_source_lines,
    stable_artifact_id,
)
from career_ai.tailoring.extraction_types import (
    CandidateFactExtraction,
    CandidateFactKind,
    ExtractedCandidateFact,
    ResumeFactSource,
)
from career_ai.tailoring.models import (
    CandidateFact,
    CandidateFactId,
    EvidenceProvenance,
    UserConfirmationProvenance,
)

_BULLET_PREFIX: Final = re.compile(r"^\s*[-*•]\s+")
_DATE_START: Final = r"\b(?:19|20)\d{2}(?:\s*[-\u2013\u2014/]\s*"
_DATE_END: Final = r"(?:(?:19|20)\d{2}|present|current|至今))?\b"
_DATE_PATTERN: Final = re.compile(f"{_DATE_START}{_DATE_END}", re.IGNORECASE)
_NUMBER_PATTERN: Final = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?:\+|[%\uFF05])?(?!\w)")
_TECH_START: Final = r"(?<![\w+#])(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|Go|Rust|SQL|"
_TECH_END: Final = r"Kubernetes|Docker|Spark|Airflow|AWS|Azure|GCP|React|Node\.js)(?![\w+#])"
_TECHNOLOGY_PATTERN: Final = re.compile(f"{_TECH_START}{_TECH_END}", re.IGNORECASE)
_ORG_START: Final = r"(?:\b[A-Z][\w&.-]*(?:\s+[A-Z][\w&.-]*){0,3}\s+"
_ORG_MIDDLE: Final = r"(?:Corp(?:oration)?|Inc|Ltd|LLC|Company)\b|"
_ORG_END: Final = r"[\u4e00-\u9fffA-Za-z0-9·&]{2,}(?:科技)?有限公司)"
_ORGANIZATION_PATTERN: Final = re.compile(f"{_ORG_START}{_ORG_MIDDLE}{_ORG_END}")
_ROLE_PREFIX: Final = r"\b(?:Senior |Staff |Lead |Principal )?"
_ROLE_DISCIPLINE: Final = r"(?:Data |Software |Machine Learning |AI )?"
_ROLE_ENGLISH: Final = r"(?:Engineer|Developer|Architect|Manager|Analyst|Scientist)\b|"
_ROLE_CHINESE_PREFIX: Final = r"(?:高级|资深|首席|数据|软件|算法|机器学习|AI)*"
_ROLE_CHINESE: Final = r"(?:工程师|开发者|架构师|经理|分析师|科学家)"
_ROLE_PATTERN: Final = re.compile(
    f"{_ROLE_PREFIX}{_ROLE_DISCIPLINE}{_ROLE_ENGLISH}{_ROLE_CHINESE_PREFIX}{_ROLE_CHINESE}",
    re.IGNORECASE,
)
_RESULT_ENGLISH: Final = (
    r"\b(?:reduced|increased|improved|saved|grew|delivered|accelerated|cut)\b|"
)
_RESULT_CHINESE: Final = r"(?:提升|提高|降低|减少|缩短|增长|节省|交付)"
_RESULT_CUE_PATTERN: Final = re.compile(
    f"{_RESULT_ENGLISH}{_RESULT_CHINESE}",
    re.IGNORECASE,
)


def extract_candidate_facts(
    resume_text: str,
    source: ResumeFactSource,
) -> CandidateFactExtraction:
    """Extract only resume-backed facts; JD text is deliberately not accepted."""
    lines = extract_source_lines(resume_text, source.artifact_id)
    extracted: list[ExtractedCandidateFact] = []
    seen: set[tuple[CandidateFactKind, str, str]] = set()
    for line in lines:
        base_kind = (
            CandidateFactKind.BULLET
            if _BULLET_PREFIX.match(line.text)
            else CandidateFactKind.PARAGRAPH
        )
        _append_fact(extracted, seen, line, base_kind, line.text)
        _append_matches(extracted, seen, line, CandidateFactKind.DATE, _DATE_PATTERN)
        _append_matches(extracted, seen, line, CandidateFactKind.NUMBER, _NUMBER_PATTERN)
        _append_matches(extracted, seen, line, CandidateFactKind.TECHNOLOGY, _TECHNOLOGY_PATTERN)
        _append_matches(
            extracted,
            seen,
            line,
            CandidateFactKind.ORGANIZATION,
            _ORGANIZATION_PATTERN,
        )
        _append_matches(extracted, seen, line, CandidateFactKind.ROLE, _ROLE_PATTERN)
        if _RESULT_CUE_PATTERN.search(line.text):
            _append_fact(extracted, seen, line, CandidateFactKind.RESULT, line.text)
    return CandidateFactExtraction(
        evidence_spans=tuple(line.evidence_span for line in lines),
        facts=tuple(extracted),
    )


def create_confirmed_candidate_fact(
    statement: str,
    *,
    confirmation: str,
) -> CandidateFact:
    """Create a stable candidate fact from an explicit user confirmation."""
    fact_id = CandidateFactId(
        stable_artifact_id(
            ArtifactPrefix("fact"),
            "user_confirmation",
            statement,
            confirmation,
        )
    )
    return CandidateFact(
        id=fact_id,
        statement=statement,
        provenance=UserConfirmationProvenance(confirmation=confirmation),
    )


def _append_matches(
    target: list[ExtractedCandidateFact],
    seen: set[tuple[CandidateFactKind, str, str]],
    line: SourceLine,
    kind: CandidateFactKind,
    pattern: re.Pattern[str],
) -> None:
    for match in pattern.finditer(line.text):
        _append_fact(target, seen, line, kind, match.group(0))


def _append_fact(
    target: list[ExtractedCandidateFact],
    seen: set[tuple[CandidateFactKind, str, str]],
    line: SourceLine,
    kind: CandidateFactKind,
    statement: str,
) -> None:
    normalized_statement = statement.strip()
    key = (kind, normalized_statement.casefold(), line.evidence_span.id)
    if key in seen:
        return
    seen.add(key)
    fact_id = CandidateFactId(
        stable_artifact_id(
            ArtifactPrefix("fact"),
            line.evidence_span.id,
            kind,
            normalized_statement,
        )
    )
    target.append(
        ExtractedCandidateFact(
            fact=CandidateFact(
                id=fact_id,
                statement=normalized_statement,
                provenance=EvidenceProvenance(evidence_span_ids=(line.evidence_span.id,)),
            ),
            kind=kind,
        )
    )
