from typing import Final, assert_never

from career_ai.tailoring.extraction_shared import (
    ArtifactPrefix,
    extract_source_lines,
    stable_artifact_id,
)
from career_ai.tailoring.extraction_types import (
    ExtractedJDRequirement,
    JDRequirementCategory,
    JDRequirementExtraction,
)
from career_ai.tailoring.models import (
    JDRequirement,
    JDRequirementId,
    RequirementPriority,
    SourceArtifactId,
)

_ATS_CUES: Final = ("ats keyword", "keywords:", "关键词\uFF1A", "关键词:")
_PREFERRED_CUES: Final = ("preferred", "nice to have", "优先", "加分")
_REQUIRED_CUES: Final = ("required", "must", "必须", "需要", "任职要求")
_SENIORITY_CUES: Final = ("seniority", "years of", "year of", "职级", "年经验", "年以上")
_INDUSTRY_CUES: Final = ("industry", "domain knowledge", "行业", "领域知识")
_OUTCOME_CUES: Final = ("outcome", "results", "成果", "结果", "提升", "改善")
_RESPONSIBILITY_CUES: Final = ("responsibilities", "responsibility", "职责", "负责")
_CATEGORY_CUES: Final = (
    (JDRequirementCategory.ATS_KEYWORD, _ATS_CUES),
    (JDRequirementCategory.PREFERRED_SKILL, _PREFERRED_CUES),
    (JDRequirementCategory.SENIORITY, _SENIORITY_CUES),
    (JDRequirementCategory.INDUSTRY_LANGUAGE, _INDUSTRY_CUES),
    (JDRequirementCategory.OUTCOME, _OUTCOME_CUES),
    (JDRequirementCategory.REQUIRED_SKILL, _REQUIRED_CUES),
    (JDRequirementCategory.RESPONSIBILITY, _RESPONSIBILITY_CUES),
)


def extract_jd_requirements(
    jd_text: str,
    source_artifact_id: SourceArtifactId,
) -> JDRequirementExtraction:
    """Extract categorized JD requirements without authorizing candidate claims."""
    lines = extract_source_lines(jd_text, source_artifact_id)
    requirements: list[ExtractedJDRequirement] = []
    for line in lines:
        category = _classify_requirement(line.text)
        priority = _priority_for_category(category)
        requirement_id = JDRequirementId(
            stable_artifact_id(
                ArtifactPrefix("requirement"),
                line.evidence_span.id,
                category,
                priority,
                line.text,
            )
        )
        requirements.append(
            ExtractedJDRequirement(
                requirement=JDRequirement(
                    id=requirement_id,
                    statement=line.text,
                    priority=priority,
                    evidence_span_ids=(line.evidence_span.id,),
                ),
                category=category,
            )
        )
    return JDRequirementExtraction(
        evidence_spans=tuple(line.evidence_span for line in lines),
        requirements=tuple(requirements),
    )


def _classify_requirement(statement: str) -> JDRequirementCategory:
    normalized = statement.casefold()
    for category, cues in _CATEGORY_CUES:
        if any(cue in normalized for cue in cues):
            return category
    return JDRequirementCategory.RESPONSIBILITY


def _priority_for_category(category: JDRequirementCategory) -> RequirementPriority:
    match category:
        case JDRequirementCategory.REQUIRED_SKILL | JDRequirementCategory.SENIORITY:
            return RequirementPriority.REQUIRED
        case JDRequirementCategory.PREFERRED_SKILL:
            return RequirementPriority.PREFERRED
        case (
            JDRequirementCategory.RESPONSIBILITY
            | JDRequirementCategory.INDUSTRY_LANGUAGE
            | JDRequirementCategory.OUTCOME
            | JDRequirementCategory.ATS_KEYWORD
        ):
            return RequirementPriority.CONTEXTUAL
        case _:
            assert_never(category)
