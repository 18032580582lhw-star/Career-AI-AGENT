from pathlib import Path

import pytest
from typer.testing import CliRunner

from career_ai.cli import app
from career_ai.evals.failure_corpus import (
    FailureCorpusConversionError,
    FailureCorpusReviewState,
    create_failure_candidate,
    failure_record_to_eval_case_draft,
    sanitize_failure_record,
)
from career_ai.workflows.run_record import (
    CareerFitRunRecord,
    RunInputSummary,
    RunQualityCheckRecord,
)


def test_failed_run_record_creates_sanitized_regression_candidate() -> None:
    # Given: a neutral failed workflow run record and sensitive reviewer feedback.
    run_record = _failed_run_record()

    candidate = create_failure_candidate(
        run_record,
        feedback=(
            "User Jane Candidate jane@example.com at +1 415 555 1212 saw "
            "C:\\Users\\Jane\\resume.docx fail with api_key=secret-token."
        ),
    )

    # When: the candidate is serialized after sanitization.
    record_json = candidate.model_dump_json()

    # Then: only neutral workflow metadata remains and sensitive text is removed.
    assert candidate.review_state == FailureCorpusReviewState.CANDIDATE
    assert candidate.failure_category == "failed_quality_check"
    assert candidate.operation == "career_fit_analysis"
    assert candidate.step_names == ["analyze_career_fit", "compare_prompt_strategies"]
    assert candidate.quality_checks[0].code == "factual_grounding"
    assert candidate.expected_behavior == (
        "Recover from transient analyzer failures without inventing resume facts."
    )
    assert "Jane Candidate" not in record_json
    assert "jane@example.com" not in record_json
    assert "415 555 1212" not in record_json
    assert "C:\\Users\\Jane\\resume.docx" not in record_json
    assert "secret-token" not in record_json
    assert "provider" not in record_json
    assert "agent_mode" not in record_json
    assert "retry_budget" not in record_json


def test_failure_candidate_review_state_moves_forward() -> None:
    # Given: an unreviewed workflow failure candidate.
    candidate = create_failure_candidate(_failed_run_record())

    # When: each supported review transition is requested.
    accepted = candidate.move_to(FailureCorpusReviewState.ACCEPTED)
    rejected = candidate.move_to(FailureCorpusReviewState.REJECTED)
    converted = accepted.move_to(FailureCorpusReviewState.CONVERTED_TO_EVAL)

    # Then: transitions return immutable copies and preserve the original.
    assert accepted.review_state == FailureCorpusReviewState.ACCEPTED
    assert rejected.review_state == FailureCorpusReviewState.REJECTED
    assert converted.review_state == FailureCorpusReviewState.CONVERTED_TO_EVAL
    assert candidate.review_state == FailureCorpusReviewState.CANDIDATE


def test_accepted_candidate_converts_to_redacted_eval_case_draft() -> None:
    # Given: an accepted neutral workflow failure candidate.
    candidate = create_failure_candidate(_failed_run_record()).move_to(
        FailureCorpusReviewState.ACCEPTED,
    )

    # When: the candidate is converted to an eval draft.
    draft = failure_record_to_eval_case_draft(candidate)

    # Then: only size placeholders and expected behavior reach the eval case.
    assert draft.id == "failure-run-failure-001"
    assert draft.name == "Regression draft for run-failure-001"
    assert draft.input.resume_text == "[REDACTED_RESUME: 1200 characters]"
    assert draft.input.jd_text == "[REDACTED_JD: 800 characters]"
    assert draft.expected.prompt_strategy_count_min == 3
    assert "transient analyzer failures" in draft.expected.forbidden_new_claims[0]


def test_unaccepted_candidate_cannot_convert_to_eval_case_draft() -> None:
    # Given: a candidate that has not received explicit acceptance.
    candidate = create_failure_candidate(_failed_run_record())

    # When/Then: conversion is blocked by the typed review-state error.
    with pytest.raises(FailureCorpusConversionError):
        _ = failure_record_to_eval_case_draft(candidate)


def test_cli_converts_accepted_failure_candidate_to_eval_draft(tmp_path: Path) -> None:
    candidate = create_failure_candidate(_failed_run_record()).move_to(
        FailureCorpusReviewState.ACCEPTED,
    )
    record_path = tmp_path / "candidate.json"
    output_path = tmp_path / "eval-draft.json"
    _ = record_path.write_text(candidate.model_dump_json(indent=2), encoding="utf-8")
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "failure-to-eval",
            "--record-file",
            str(record_path),
            "--output-file",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert "Wrote eval draft:" in result.stdout
    output = output_path.read_text(encoding="utf-8")
    assert "failure-run-failure-001" in output
    assert "resume.docx" not in output


def test_cli_accepts_utf8_bom_failure_candidate_file(tmp_path: Path) -> None:
    candidate = create_failure_candidate(_failed_run_record()).move_to(
        FailureCorpusReviewState.ACCEPTED,
    )
    record_path = tmp_path / "candidate-bom.json"
    output_path = tmp_path / "eval-draft.json"
    _ = record_path.write_text(
        f"\ufeff{candidate.model_dump_json(indent=2)}",
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "failure-to-eval",
            "--record-file",
            str(record_path),
            "--output-file",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.exists()


def test_sanitize_failure_record_redacts_late_review_feedback() -> None:
    candidate = create_failure_candidate(_failed_run_record()).model_copy(
        update={
            "feedback": "Token Bearer abc.secret.value and /Users/jane/private.txt leaked.",
        },
    )

    sanitized = sanitize_failure_record(candidate)

    assert "Bearer abc.secret.value" not in sanitized.feedback
    assert "/Users/jane/private.txt" not in sanitized.feedback


def test_failure_conversion_redacts_every_free_text_run_record_field() -> None:
    # Given: sensitive text is present outside reviewer feedback.
    unsafe = _failed_run_record().model_copy(
        update={
            "expected_behavior": (
                "Notify jane@example.com at +1 415 555 1212 using api_key=secret-token "
                "from C:\\Users\\Jane\\resume.docx."
            ),
            "step_names": ["read /Users/jane/private.txt"],
            "quality_checks": [
                RunQualityCheckRecord(
                    name="Bearer abc.secret.value",
                    code="jane@example.com",
                    status="failed",
                ),
            ],
        },
    )

    # When: the record is accepted and converted.
    candidate = create_failure_candidate(unsafe).move_to(FailureCorpusReviewState.ACCEPTED)
    draft = failure_record_to_eval_case_draft(candidate)
    serialized = candidate.model_dump_json() + draft.model_dump_json()

    # Then: no sensitive source survives candidate storage or eval conversion.
    for secret in (
        "jane@example.com",
        "415 555 1212",
        "secret-token",
        "C:\\Users\\Jane\\resume.docx",
        "/Users/jane/private.txt",
        "Bearer abc.secret.value",
    ):
        assert secret not in serialized


def test_sanitize_failure_record_redacts_failure_category() -> None:
    # Given: a record loaded from disk has a sensitive category value.
    candidate = create_failure_candidate(_failed_run_record()).model_copy(
        update={"failure_category": "api_key=secret-token at /Users/jane/private.txt"},
    )

    # When: the loaded record is sanitized.
    sanitized = sanitize_failure_record(candidate)

    # Then: the persisted category cannot retain credentials or local paths.
    assert "secret-token" not in sanitized.failure_category
    assert "/Users/jane/private.txt" not in sanitized.failure_category


def _failed_run_record() -> CareerFitRunRecord:
    return CareerFitRunRecord(
        run_id="run-failure-001",
        operation="career_fit_analysis",
        final_status="failed-quality",
        input_summary=RunInputSummary(
            resume_character_count=1200,
            jd_character_count=800,
        ),
        step_names=["analyze_career_fit", "compare_prompt_strategies"],
        quality_checks=[
            RunQualityCheckRecord(
                name="Factual grounding",
                code="factual_grounding",
                status="failed",
            ),
        ],
        expected_behavior=(
            "Recover from transient analyzer failures without inventing resume facts."
        ),
    )
