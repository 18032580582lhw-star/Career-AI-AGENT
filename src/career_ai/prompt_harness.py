from pathlib import Path

from career_ai.models import PromptHarnessResult, PromptStrategyScore
from career_ai.text_processing import extract_keywords

FACT_SAFETY_BONUS: int = 20


def compare_prompt_strategies(
    prompt_dir: Path,
    resume_text: str,
    jd_text: str,
) -> PromptHarnessResult:
    """Compare prompt markdown files with deterministic rubric scoring."""
    prompt_paths = sorted(prompt_dir.glob("*.md"))
    strategies = [
        _score_prompt(path=path, resume_text=resume_text, jd_text=jd_text)
        for path in prompt_paths
    ]
    best = max(strategies, key=lambda strategy: strategy.score) if strategies else None
    return PromptHarnessResult(
        strategies=strategies,
        best_strategy_name=best.name if best else "",
    )


def _score_prompt(path: Path, resume_text: str, jd_text: str) -> PromptStrategyScore:
    prompt = path.read_text(encoding="utf-8")
    prompt_lower = prompt.lower()
    jd_keywords = extract_keywords(jd_text)
    resume_keywords = extract_keywords(resume_text)
    overlap = len(set(jd_keywords) & set(resume_keywords))
    structure_bonus = 15 if "json" in prompt_lower or "structured" in prompt_lower else 0
    has_fact_guardrail = "do not invent" in prompt_lower or "fact" in prompt_lower
    safety_bonus = FACT_SAFETY_BONUS if has_fact_guardrail else 0
    score = min(100, 40 + (overlap * 5) + structure_bonus + safety_bonus)
    strengths = _strengths(prompt_lower)
    risks = (
        ["May need human review before final submission."]
        if safety_bonus < FACT_SAFETY_BONUS
        else []
    )
    return PromptStrategyScore(
        name=path.stem,
        score=score,
        strengths=strengths,
        risks=risks,
    )


def _strengths(prompt_lower: str) -> list[str]:
    strengths: list[str] = []
    if "structured" in prompt_lower or "json" in prompt_lower:
        strengths.append("Structured output control")
    if "fact" in prompt_lower or "do not invent" in prompt_lower:
        strengths.append("Fact preservation")
    if "cover letter" in prompt_lower:
        strengths.append("Application material coverage")
    return strengths or ["Baseline career analysis"]
