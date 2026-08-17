from career_ai.analysis import analyze_career_fit, get_sample_inputs
from career_ai.models import PromptHarnessResult, PromptStrategyScore
from career_ai.workflows.models import CareerFitWorkflowResult
from career_ai.workflows.quality import (
    MISSING_PROMPT_STRATEGY_MESSAGE,
    UNSUPPORTED_FACT_MESSAGE,
    assess_career_quality,
)


def test_quality_report_passes_for_existing_sample_workflow() -> None:
    # Given
    resume_text, jd_text = get_sample_inputs()
    workflow = _sample_workflow(resume_text=resume_text, jd_text=jd_text)

    # When
    report = assess_career_quality(
        workflow=workflow,
        resume_text=resume_text,
        jd_text=jd_text,
    )

    # Then
    assert report.passed is True
    assert [check.name for check in report.checks] == [
        "factual_consistency",
        "jd_alignment",
        "prompt_strategy_available",
        "missing_keywords_present",
        "document_export_ready",
    ]
    assert report.summary == "quality=passed checks=5/5"


def test_quality_report_fails_when_rewritten_resume_adds_unsupported_claims() -> None:
    # Given
    resume_text, jd_text = get_sample_inputs()
    workflow = _sample_workflow(resume_text=resume_text, jd_text=jd_text)
    unsafe_report = workflow.report.model_copy(
        update={
            "rewritten_resume": (
                f"{workflow.report.rewritten_resume}\n"
                "- Led Kubernetes migration at Stripe in 2025 with 40% cost savings."
            ),
        },
    )

    # When
    report = assess_career_quality(
        workflow=workflow.model_copy(update={"report": unsafe_report}),
        resume_text=resume_text,
        jd_text=jd_text,
    )

    # Then
    assert report.passed is False
    assert report.summary == "quality=failed checks=4/5"
    assert report.failed_messages == [UNSUPPORTED_FACT_MESSAGE]


def test_quality_report_explains_missing_prompt_strategy() -> None:
    # Given
    resume_text, jd_text = get_sample_inputs()
    workflow = _sample_workflow(resume_text=resume_text, jd_text=jd_text).model_copy(
        update={"prompt_result": PromptHarnessResult(strategies=[], best_strategy_name="")},
    )

    # When
    report = assess_career_quality(
        workflow=workflow,
        resume_text=resume_text,
        jd_text=jd_text,
    )

    # Then
    assert report.failed_messages == [MISSING_PROMPT_STRATEGY_MESSAGE]


def _sample_workflow(*, resume_text: str, jd_text: str) -> CareerFitWorkflowResult:
    return CareerFitWorkflowResult(
        report=analyze_career_fit(resume_text=resume_text, jd_text=jd_text),
        prompt_result=PromptHarnessResult(
            strategies=[
                PromptStrategyScore(name="baseline", score=70, strengths=[], risks=[]),
                PromptStrategyScore(
                    name="fact-preserving-rewriter",
                    score=90,
                    strengths=[],
                    risks=[],
                ),
            ],
            best_strategy_name="fact-preserving-rewriter",
        ),
        steps=["analyze_career_fit", "compare_prompt_strategies"],
    )
