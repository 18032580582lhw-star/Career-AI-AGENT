from pathlib import Path
from typing import final, override

from career_ai.agent.executor import run_career_agent
from career_ai.agent.quality import (
    MISSING_PROMPT_STRATEGY_MESSAGE,
    UNSUPPORTED_FACT_MESSAGE,
    CareerQualityOptimizerOptions,
    assess_career_quality,
    evaluate_career_quality,
)
from career_ai.analysis import analyze_career_fit, get_sample_inputs
from career_ai.llm.client import FakeLLMClient
from career_ai.llm.models import LLMCapabilities, LLMRequest, LLMResponse, ModelProvider
from career_ai.models import PromptHarnessResult, PromptStrategyScore
from career_ai.workflows.models import CareerFitWorkflowResult


def test_quality_report_passes_for_existing_sample_workflow() -> None:
    resume_text, jd_text = get_sample_inputs()
    workflow = _sample_workflow(resume_text=resume_text, jd_text=jd_text)

    report = assess_career_quality(
        workflow=workflow,
        resume_text=resume_text,
        jd_text=jd_text,
    )

    assert report.passed is True
    assert [check.name for check in report.checks] == [
        "factual_consistency",
        "jd_alignment",
        "prompt_strategy_available",
        "missing_keywords_present",
        "document_export_ready",
    ]
    assert all(check.passed for check in report.checks)
    assert report.summary == "quality=passed checks=5/5"


def test_quality_report_fails_when_rewritten_resume_adds_unsupported_claims() -> None:
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

    report = assess_career_quality(
        workflow=workflow.model_copy(update={"report": unsafe_report}),
        resume_text=resume_text,
        jd_text=jd_text,
    )

    assert report.passed is False
    assert report.summary == "quality=failed checks=4/5"
    assert report.failed_messages == [UNSUPPORTED_FACT_MESSAGE]


def test_quality_report_messages_are_actionable_when_prompt_harness_is_missing() -> None:
    resume_text, jd_text = get_sample_inputs()
    workflow = _sample_workflow(resume_text=resume_text, jd_text=jd_text).model_copy(
        update={
            "prompt_result": PromptHarnessResult(
                strategies=[],
                best_strategy_name="",
            ),
        },
    )

    report = assess_career_quality(
        workflow=workflow,
        resume_text=resume_text,
        jd_text=jd_text,
    )

    assert report.passed is False
    assert report.failed_messages == [MISSING_PROMPT_STRATEGY_MESSAGE]


def test_agent_run_includes_compact_quality_report() -> None:
    resume_text, jd_text = get_sample_inputs()

    result = run_career_agent(
        resume_text=resume_text,
        jd_text=jd_text,
        prompt_dir=Path("prompts"),
        llm_client=FakeLLMClient(),
    )

    assert result.quality_report.passed is True
    assert result.quality_report.summary == "quality=passed checks=5/5"


def test_evaluator_optimizer_stops_after_two_model_evaluations() -> None:
    resume_text, jd_text = get_sample_inputs()
    workflow = _workflow_with_unsupported_claim(
        resume_text=resume_text,
        jd_text=jd_text,
    )
    llm_client = RecordingQualityEvaluatorClient()

    report = evaluate_career_quality(
        workflow=workflow,
        resume_text=resume_text,
        jd_text=jd_text,
        llm_client=llm_client,
        options=CareerQualityOptimizerOptions(enabled=True, max_iterations=2),
    )

    assert report.passed is False
    assert report.optimizer_iterations == 2
    assert llm_client.evaluator_call_count == 2
    assert report.failed_messages == [UNSUPPORTED_FACT_MESSAGE]


def test_evaluator_optimizer_keeps_fake_provider_on_deterministic_path() -> None:
    resume_text, jd_text = get_sample_inputs()
    workflow = _workflow_with_unsupported_claim(
        resume_text=resume_text,
        jd_text=jd_text,
    )
    llm_client = RecordingFakeLLMClient()

    report = evaluate_career_quality(
        workflow=workflow,
        resume_text=resume_text,
        jd_text=jd_text,
        llm_client=llm_client,
        options=CareerQualityOptimizerOptions(enabled=True, max_iterations=2),
    )

    assert report.optimizer_iterations == 0
    assert llm_client.evaluator_call_count == 0
    assert report.failed_messages == [UNSUPPORTED_FACT_MESSAGE]


def _sample_workflow(*, resume_text: str, jd_text: str) -> CareerFitWorkflowResult:
    return CareerFitWorkflowResult(
        report=analyze_career_fit(resume_text=resume_text, jd_text=jd_text),
        prompt_result=PromptHarnessResult(
            strategies=[
                PromptStrategyScore(name="baseline", score=70, strengths=[], risks=[]),
                PromptStrategyScore(name="structured-agent", score=85, strengths=[], risks=[]),
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


def _workflow_with_unsupported_claim(
    *,
    resume_text: str,
    jd_text: str,
) -> CareerFitWorkflowResult:
    workflow = _sample_workflow(resume_text=resume_text, jd_text=jd_text)
    unsafe_report = workflow.report.model_copy(
        update={
            "rewritten_resume": (
                f"{workflow.report.rewritten_resume}\n"
                "- Led Kubernetes migration at Stripe in 2025 with 40% cost savings."
            ),
        },
    )
    return workflow.model_copy(update={"report": unsafe_report})


@final
class RecordingQualityEvaluatorClient:
    def __init__(self) -> None:
        self.evaluator_call_count: int = 0

    @property
    def provider(self) -> ModelProvider:
        return ModelProvider.OPENAI_COMPATIBLE

    @property
    def capabilities(self) -> LLMCapabilities:
        return LLMCapabilities(
            supports_tool_calling=False,
            supports_structured_output=True,
            supports_streaming=False,
        )

    def complete_structured(self, request: LLMRequest) -> LLMResponse:
        self.evaluator_call_count += 1
        assert "career quality evaluator" in request.system_prompt.lower()
        return LLMResponse(
            provider=self.provider,
            content={"passed": False, "feedback": ["Strengthen factual support."]},
        )


@final
class RecordingFakeLLMClient(FakeLLMClient):
    def __init__(self) -> None:
        self.evaluator_call_count: int = 0

    @override
    def complete_structured(self, request: LLMRequest) -> LLMResponse:
        self.evaluator_call_count += 1
        return super().complete_structured(request)
