from career_ai.workflows.run_record import (
    CareerFitRunRecord,
    RunInputSummary,
    RunQualityCheckRecord,
)


def test_run_record_serializes_only_neutral_workflow_metadata() -> None:
    # Given
    record = CareerFitRunRecord(
        run_id="run-123",
        operation="career_fit_analysis",
        final_status="failed",
        input_summary=RunInputSummary(
            resume_character_count=42,
            jd_character_count=27,
        ),
        step_names=["analyze_job_description", "score_resume_match"],
        quality_checks=[
            RunQualityCheckRecord(
                name="factual_consistency",
                code="unsupported_fact",
                status="failed",
            ),
        ],
        expected_behavior=(
            "Produce factual career-fit analysis without retaining personal input text."
        ),
    )

    # When
    payload = record.model_dump(mode="json")

    # Then
    assert payload == {
        "run_id": "run-123",
        "operation": "career_fit_analysis",
        "final_status": "failed",
        "input_summary": {
            "resume_character_count": 42,
            "jd_character_count": 27,
        },
        "step_names": ["analyze_job_description", "score_resume_match"],
        "quality_checks": [
            {
                "name": "factual_consistency",
                "code": "unsupported_fact",
                "status": "failed",
            },
        ],
        "expected_behavior": (
            "Produce factual career-fit analysis without retaining personal input text."
        ),
    }


def test_input_summary_retains_counts_without_input_bodies() -> None:
    # Given
    resume_text = "Secret resume body"
    jd_text = "Private job description"

    # When
    summary = RunInputSummary.from_inputs(resume_text=resume_text, jd_text=jd_text)
    serialized = summary.model_dump_json()

    # Then
    assert summary.resume_character_count == len(resume_text)
    assert summary.jd_character_count == len(jd_text)
    assert resume_text not in serialized
    assert jd_text not in serialized
