from pathlib import Path

from career_ai.analysis import get_sample_inputs
from career_ai.application.career_fit_service import CareerFitApplicationService


def test_service_returns_deterministic_workflow_quality_and_run_record() -> None:
    # Given
    resume_text, jd_text = get_sample_inputs()
    service = CareerFitApplicationService(prompt_dir=Path("prompts"))

    # When
    first = service.run(resume_text=resume_text, jd_text=jd_text)
    second = service.run(resume_text=resume_text, jd_text=jd_text)

    # Then
    assert first.workflow == second.workflow
    assert first.quality == second.quality
    assert first.quality.passed is True
    assert first.run_record.operation == "career_fit_analysis"
    assert first.run_record.final_status == "passed"


def test_service_run_record_is_privacy_safe() -> None:
    # Given
    resume_text = "Jane Candidate\nSecret internal migration project."
    jd_text = "Private Product Role\nConfidential stakeholder roadmap ownership."
    service = CareerFitApplicationService(prompt_dir=Path("prompts"))

    # When
    result = service.run(resume_text=resume_text, jd_text=jd_text)
    serialized = result.run_record.model_dump_json()

    # Then
    assert result.run_record.input_summary.resume_character_count == len(resume_text)
    assert result.run_record.input_summary.jd_character_count == len(jd_text)
    assert resume_text not in serialized
    assert jd_text not in serialized
    assert str(Path.cwd().resolve()) not in serialized


def test_service_run_record_excludes_agent_autonomy_metadata() -> None:
    # Given
    resume_text, jd_text = get_sample_inputs()
    service = CareerFitApplicationService(prompt_dir=Path("prompts"))

    # When
    result = service.run(resume_text=resume_text, jd_text=jd_text)
    serialized = result.run_record.model_dump()

    # Then
    assert set(serialized).isdisjoint(
        {
            "provider",
            "agent_mode",
            "planned_steps",
            "tool_events",
            "provider_capabilities",
            "harness",
            "retry_budget",
        },
    )
