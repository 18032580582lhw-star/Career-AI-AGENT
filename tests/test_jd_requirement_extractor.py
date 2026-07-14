from career_ai.tailoring.extraction_types import JDRequirementCategory
from career_ai.tailoring.jd_extractor import extract_jd_requirements
from career_ai.tailoring.models import RequirementPriority, SourceArtifactId


def test_extract_jd_requirements_classifies_categories_and_priorities() -> None:
    # Given
    jd = """Responsibilities: Build reliable data platforms.
Required skills: Python and Kubernetes.
Preferred: Experience with Spark.
Seniority: 5+ years of engineering experience.
Industry: Fintech domain knowledge.
Outcomes: Improve platform reliability.
ATS keywords: SQL, Airflow."""

    # When
    extraction = extract_jd_requirements(jd, SourceArtifactId("jd-source"))

    # Then
    categories = {item.category for item in extraction.requirements}
    assert categories == {
        JDRequirementCategory.RESPONSIBILITY,
        JDRequirementCategory.REQUIRED_SKILL,
        JDRequirementCategory.PREFERRED_SKILL,
        JDRequirementCategory.SENIORITY,
        JDRequirementCategory.INDUSTRY_LANGUAGE,
        JDRequirementCategory.OUTCOME,
        JDRequirementCategory.ATS_KEYWORD,
    }
    priorities = {item.category: item.requirement.priority for item in extraction.requirements}
    assert priorities[JDRequirementCategory.REQUIRED_SKILL] is RequirementPriority.REQUIRED
    assert priorities[JDRequirementCategory.PREFERRED_SKILL] is RequirementPriority.PREFERRED
    assert priorities[JDRequirementCategory.INDUSTRY_LANGUAGE] is RequirementPriority.CONTEXTUAL


def test_extract_jd_requirements_supports_chinese_cues() -> None:
    # Given
    jd = """岗位职责: 建设稳定的数据平台。
必须技能: Python、SQL。
优先条件: 有 Spark 经验。
成果预期: 提升平台可靠性。"""

    # When
    extraction = extract_jd_requirements(jd, SourceArtifactId("jd-source"))

    # Then
    categories = [item.category for item in extraction.requirements]
    assert categories == [
        JDRequirementCategory.RESPONSIBILITY,
        JDRequirementCategory.REQUIRED_SKILL,
        JDRequirementCategory.PREFERRED_SKILL,
        JDRequirementCategory.OUTCOME,
    ]


def test_jd_only_technology_remains_a_requirement_not_a_candidate_fact() -> None:
    # Given
    jd = "Required skills: Kubernetes."

    # When
    extraction = extract_jd_requirements(jd, SourceArtifactId("jd-source"))

    # Then
    assert len(extraction.requirements) == 1
    assert extraction.requirements[0].requirement.statement == jd
    assert extraction.requirements[0].category is JDRequirementCategory.REQUIRED_SKILL


def test_jd_requirement_ids_are_stable() -> None:
    # Given
    jd = "Required skills: Python and Kubernetes."

    # When
    first = extract_jd_requirements(jd, SourceArtifactId("jd-source"))
    second = extract_jd_requirements(jd, SourceArtifactId("jd-source"))

    # Then
    assert first == second
