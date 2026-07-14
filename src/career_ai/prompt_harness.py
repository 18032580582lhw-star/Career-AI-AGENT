from pathlib import Path
from typing import Final

from career_ai.models import PromptHarnessResult, PromptStrategyScore
from career_ai.tailoring.generation_context import build_generation_context
from career_ai.tailoring.generation_models import ProposalOutcome
from career_ai.tailoring.generation_workflow import run_local_strategy_workflow

_ACCEPTED_SCORE: Final = 100


def compare_prompt_strategies(
    prompt_dir: Path,
    resume_text: str,
    jd_text: str,
) -> PromptHarnessResult:
    """Run real evidence-only proposal strategies through local outcome grading."""
    if not resume_text.strip() or not jd_text.strip() or not any(prompt_dir.glob("*.md")):
        return PromptHarnessResult(strategies=[], best_strategy_name="")
    result = run_local_strategy_workflow(
        build_generation_context(
            resume_text=resume_text,
            jd_text=jd_text,
            run_id="run-legacy-prompt-harness",
        )
    )
    strategies = [_as_legacy_score(item) for item in result.outcomes]
    return PromptHarnessResult(
        strategies=strategies,
        best_strategy_name=result.best_strategy.value if result.best_strategy else "",
    )


def _as_legacy_score(item: ProposalOutcome) -> PromptStrategyScore:
    findings = item.decision.decision.findings
    strengths = (
        ["Passed local safety and adequacy harnesses."]
        if item.score == _ACCEPTED_SCORE
        else []
    )
    risks = [finding.code for finding in findings]
    return PromptStrategyScore(
        name=item.proposal.strategy.value,
        score=item.score,
        strengths=strengths,
        risks=risks,
    )
