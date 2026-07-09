from typing import Final

from career_ai.models import BulletSuggestion, CareerFitReport, JDAnalysis, SkillGap
from career_ai.text_processing import (
    extract_keywords,
    match_keywords,
    normalize_text,
    split_resume_bullets,
)

SAMPLE_RESUME: Final[str] = """
Product analyst with 3 years of experience building Streamlit dashboards for hiring teams.
- Built a Streamlit dashboard for weekly hiring funnel reporting.
- Analyzed interview conversion trends using Python and SQL.
- Evaluated LLM workflow quality and prompt engineering tradeoffs for candidate tools.
- Presented product insights to stakeholders and improved reporting workflows.
"""

SAMPLE_JD: Final[str] = """
Role: AI Product Analyst
We are hiring an AI Product Analyst to evaluate LLM-powered workflows for job seekers.
Requirements include Python, SQL, Streamlit, prompt engineering, data analysis, dashboard
storytelling, stakeholder communication, and LLM evaluation.
"""


def get_sample_inputs() -> tuple[str, str]:
    """Return deterministic sample inputs for demos and tests."""
    return SAMPLE_RESUME.strip(), SAMPLE_JD.strip()


def analyze_career_fit(resume_text: str, jd_text: str) -> CareerFitReport:
    """Build the complete career fit report for one resume and JD."""
    jd_analysis = analyze_job_description(jd_text)
    match = match_keywords(resume_text=resume_text, jd_keywords=jd_analysis.keywords)
    gap = SkillGap(
        missing_skills=match.missing_keywords,
        priority_skills=match.missing_keywords[:3],
        notes=_build_gap_notes(match.missing_keywords),
    )
    bullets = split_resume_bullets(resume_text)
    suggestions = improve_resume_bullets(
        bullets=bullets[:5],
        jd_keywords=jd_analysis.keywords,
        full_resume_text=resume_text,
    )
    rewritten_resume = _build_rewritten_resume(resume_text, suggestions)
    return CareerFitReport(
        jd_analysis=jd_analysis,
        match=match,
        skill_gap=gap,
        bullet_suggestions=suggestions,
        cover_letter_draft=_build_cover_letter(jd_analysis),
        rewritten_resume=rewritten_resume,
    )


def analyze_job_description(jd_text: str) -> JDAnalysis:
    """Extract role metadata and keywords from JD text."""
    keywords = extract_keywords(jd_text)
    return JDAnalysis(
        role_title=_extract_role_title(jd_text),
        seniority=_extract_seniority(jd_text),
        requirements=_extract_requirements(jd_text, keywords),
        keywords=keywords,
    )


def improve_resume_bullets(
    bullets: list[str],
    jd_keywords: list[str],
    full_resume_text: str,
) -> list[BulletSuggestion]:
    """Rewrite bullets using only facts evidenced by the original resume."""
    _ = full_resume_text
    suggestions: list[BulletSuggestion] = []
    for bullet in bullets:
        bullet_normalized = normalize_text(bullet)
        evidenced_keywords = [
            keyword
            for keyword in jd_keywords
            if keyword in bullet_normalized
        ]
        improved = _rewrite_bullet(bullet, evidenced_keywords)
        suggestions.append(
            BulletSuggestion(
                original=bullet,
                improved=improved,
                jd_keywords_used=evidenced_keywords,
                factual_consistency_note="Preserves original resume facts.",
            ),
        )
    return suggestions


def _extract_role_title(jd_text: str) -> str:
    for line in jd_text.splitlines():
        clean = line.strip()
        lowered = clean.lower()
        if lowered.startswith("role:"):
            return clean.split(":", maxsplit=1)[1].strip()
        if "ai product analyst" in lowered:
            return "AI Product Analyst"
    return "Target Role"


def _extract_seniority(jd_text: str) -> str:
    lowered = jd_text.lower()
    if "senior" in lowered or "lead" in lowered:
        return "Senior"
    if "intern" in lowered or "junior" in lowered:
        return "Early career"
    return "Mid-level"


def _extract_requirements(jd_text: str, keywords: list[str]) -> list[str]:
    lines = [line.strip(" -") for line in jd_text.splitlines() if line.strip()]
    requirement_lines = [
        line
        for line in lines
        if any(keyword in line.lower() for keyword in keywords)
    ]
    return requirement_lines[:6] or keywords[:6]


def _build_gap_notes(missing_keywords: list[str]) -> list[str]:
    if not missing_keywords:
        return ["Resume covers the major JD keywords."]
    return [f"Add evidence for {keyword} if it is truthful." for keyword in missing_keywords[:4]]


def _rewrite_bullet(bullet: str, evidenced_keywords: list[str]) -> str:
    clean = bullet.rstrip(".")
    if not evidenced_keywords:
        return f"{clean}."
    keyword_text = ", ".join(
        keyword.upper() if keyword in {"ai", "llm", "sql"} else keyword
        for keyword in evidenced_keywords[:2]
    )
    return f"{clean}, emphasizing {keyword_text} experience."


def _build_rewritten_resume(resume_text: str, suggestions: list[BulletSuggestion]) -> str:
    replacements = {suggestion.original: suggestion.improved for suggestion in suggestions}
    rewritten_lines = [
        replacements.get(line.strip(" -•\t"), line)
        for line in resume_text.splitlines()
    ]
    return "\n".join(rewritten_lines).strip()


def _build_cover_letter(jd_analysis: JDAnalysis) -> str:
    return (
        "Dear Hiring Team,\n\n"
        f"I am excited to apply for the {jd_analysis.role_title} role. My background aligns with "
        "the role's emphasis on analytical product thinking, practical AI workflows, and "
        "stakeholder-ready communication. I would bring a careful, evidence-based approach "
        "to translating job requirements "
        "into measurable improvements for candidates and teams.\n\n"
        "Sincerely,\nCandidate"
    )
