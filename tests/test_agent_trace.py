from pathlib import Path

from career_ai.agent.executor import run_career_agent
from career_ai.agent.models import AgentMode
from career_ai.analysis import get_sample_inputs
from career_ai.llm.client import FakeLLMClient


def test_run_trace_records_run_metadata_plan_and_tool_events() -> None:
    resume_text, jd_text = get_sample_inputs()

    result = run_career_agent(
        resume_text=resume_text,
        jd_text=jd_text,
        prompt_dir=Path("prompts"),
        llm_client=FakeLLMClient(),
    )

    assert result.trace.run_id
    assert result.trace.provider == "fake"
    assert result.trace.agent_mode == AgentMode.DETERMINISTIC_FALLBACK.value
    assert result.trace.planned_steps == [
        "analyze_career_fit",
        "compare_prompt_strategies",
    ]
    assert [(event.tool_name, event.status) for event in result.trace.tool_events] == [
        ("analyze_career_fit", "running-tool"),
        ("analyze_career_fit", "tool-completed"),
        ("compare_prompt_strategies", "running-tool"),
        ("compare_prompt_strategies", "tool-completed"),
    ]


def test_run_trace_serializes_to_json() -> None:
    resume_text, jd_text = get_sample_inputs()

    result = run_career_agent(
        resume_text=resume_text,
        jd_text=jd_text,
        prompt_dir=Path("prompts"),
        llm_client=FakeLLMClient(),
    )

    trace_json = result.trace.model_dump_json()

    assert '"provider":"fake"' in trace_json
    assert '"agent_mode":"deterministic-fallback"' in trace_json
    assert '"tool_events"' in trace_json


def test_run_trace_excludes_full_sensitive_inputs() -> None:
    resume_text = (
        "Jane Candidate\n"
        "Secret internal migration project with private resume payload."
    )
    jd_text = (
        "Private Product Role\n"
        "Requires confidential stakeholder roadmap ownership."
    )

    result = run_career_agent(
        resume_text=resume_text,
        jd_text=jd_text,
        prompt_dir=Path("prompts"),
        llm_client=FakeLLMClient(),
    )

    trace_json = result.trace.model_dump_json()
    assert result.trace.input_summary.resume_character_count == len(resume_text)
    assert result.trace.input_summary.jd_character_count == len(jd_text)
    assert resume_text not in trace_json
    assert jd_text not in trace_json
    assert "Secret internal migration project" not in trace_json
    assert "confidential stakeholder roadmap" not in trace_json


def test_run_trace_records_capability_and_harness_summaries() -> None:
    resume_text, jd_text = get_sample_inputs()

    result = run_career_agent(
        resume_text=resume_text,
        jd_text=jd_text,
        prompt_dir=Path("prompts"),
        llm_client=FakeLLMClient(),
    )

    assert not result.trace.provider_capabilities.supports_tool_calling
    assert result.trace.provider_capabilities.supports_structured_output
    assert not result.trace.provider_capabilities.supports_streaming
    assert result.trace.harness.prompt_set == "default"
    assert result.trace.harness.tool_catalog_version == "tool-catalog-v1"
    assert result.trace.harness.policy_version == "policy-v1"
    assert result.trace.harness.retry_budget == 1
