from pathlib import Path

from career_ai.analysis import get_sample_inputs
from career_ai.prompt_harness import compare_prompt_strategies


def test_compare_prompt_strategies_loads_three_markdown_prompts() -> None:
    resume_text, jd_text = get_sample_inputs()

    result = compare_prompt_strategies(
        prompt_dir=Path("prompts"),
        resume_text=resume_text,
        jd_text=jd_text,
    )

    assert len(result.strategies) >= 3
    assert result.best_strategy_name in {strategy.name for strategy in result.strategies}
    assert all(strategy.score >= 0 for strategy in result.strategies)
