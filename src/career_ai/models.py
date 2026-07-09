from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class FrozenModel(BaseModel):
    """Base class for immutable public response models."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)


class JDAnalysis(FrozenModel):
    """Structured summary of the target job description."""

    role_title: str
    seniority: str
    requirements: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class ResumeMatch(FrozenModel):
    """Keyword-level resume-to-JD match result."""

    score: int
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    summary: str


class SkillGap(FrozenModel):
    """Skills and keywords missing from the resume."""

    missing_skills: list[str] = Field(default_factory=list)
    priority_skills: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class BulletSuggestion(FrozenModel):
    """Fact-preserving rewrite suggestion for one resume bullet."""

    original: str
    improved: str
    jd_keywords_used: list[str] = Field(default_factory=list)
    factual_consistency_note: str


class PromptStrategyScore(FrozenModel):
    """Deterministic score for one prompt strategy."""

    name: str
    score: int
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class PromptHarnessResult(FrozenModel):
    """Prompt strategy comparison result."""

    strategies: list[PromptStrategyScore] = Field(default_factory=list)
    best_strategy_name: str


class CareerFitReport(FrozenModel):
    """Complete career intelligence report for one resume and JD."""

    jd_analysis: JDAnalysis
    match: ResumeMatch
    skill_gap: SkillGap
    bullet_suggestions: list[BulletSuggestion] = Field(default_factory=list)
    cover_letter_draft: str
    rewritten_resume: str
