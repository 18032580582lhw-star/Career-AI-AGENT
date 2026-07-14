from pathlib import Path

from career_ai.analysis import get_sample_inputs
from career_ai.prompt_harness import compare_prompt_strategies


def test_compare_prompt_strategies_runs_three_real_proposal_strategies() -> None:
    resume_text, jd_text = get_sample_inputs()

    result = compare_prompt_strategies(
        prompt_dir=Path("prompts"),
        resume_text=resume_text,
        jd_text=jd_text,
    )

    assert len(result.strategies) >= 3
    assert result.best_strategy_name in {strategy.name for strategy in result.strategies}
    assert all(strategy.score >= 0 for strategy in result.strategies)
    assert {strategy.name for strategy in result.strategies} == {
        "conservative",
        "ats-aligned",
        "impact-narrative",
    }


def test_compare_prompt_strategies_returns_no_result_without_a_legacy_profile(
    tmp_path: Path,
) -> None:
    resume_text, jd_text = get_sample_inputs()

    result = compare_prompt_strategies(
        prompt_dir=tmp_path,
        resume_text=resume_text,
        jd_text=jd_text,
    )

    assert result.strategies == []
    assert result.best_strategy_name == ""
