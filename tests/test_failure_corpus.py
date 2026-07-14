from pathlib import Path

from typer.testing import CliRunner

from career_ai.agent.trace import (
    CareerRunTrace,
    HarnessTraceConfiguration,
    InputTraceSummary,
    ProviderCapabilityTraceSummary,
    ToolTraceEvent,
)
from career_ai.cli import app
from career_ai.evals.failure_corpus import (
    FailureCorpusReviewState,
    create_failure_candidate,
    failure_record_to_eval_case_draft,
    sanitize_failure_record,
)


def test_failed_trace_creates_sanitized_regression_candidate() -> None:
    trace = _failed_trace()

    candidate = create_failure_candidate(
        trace,
        feedback=(
            "User Jane Candidate jane@example.com at +1 415 555 1212 saw "
            "C:\\Users\\Jane\\resume.docx fail with api_key=secret-token."
        ),
    )

    record_json = candidate.model_dump_json()
    assert candidate.review_state == FailureCorpusReviewState.CANDIDATE
    assert candidate.failure_category == "recoverable_tool_failure"
    assert candidate.provider_capabilities.supports_structured_output
    assert candidate.harness.retry_budget == 1
    assert candidate.expected_behavior == (
        "Recover from transient analyzer failures without inventing resume facts."
    )
    assert "Jane Candidate" not in record_json
    assert "jane@example.com" not in record_json
    assert "415 555 1212" not in record_json
    assert "C:\\Users\\Jane\\resume.docx" not in record_json
    assert "secret-token" not in record_json


def test_failure_candidate_review_state_moves_forward() -> None:
    candidate = create_failure_candidate(_failed_trace())

    accepted = candidate.move_to(FailureCorpusReviewState.ACCEPTED)
    rejected = candidate.move_to(FailureCorpusReviewState.REJECTED)
    converted = accepted.move_to(FailureCorpusReviewState.CONVERTED_TO_EVAL)

    assert accepted.review_state == FailureCorpusReviewState.ACCEPTED
    assert rejected.review_state == FailureCorpusReviewState.REJECTED
    assert converted.review_state == FailureCorpusReviewState.CONVERTED_TO_EVAL
    assert candidate.review_state == FailureCorpusReviewState.CANDIDATE


def test_accepted_candidate_converts_to_redacted_eval_case_draft() -> None:
    candidate = create_failure_candidate(_failed_trace()).move_to(
        FailureCorpusReviewState.ACCEPTED,
    )

    draft = failure_record_to_eval_case_draft(candidate)

    assert draft.id == "failure-run-failure-001"
    assert draft.name == "Regression draft for run-failure-001"
    assert draft.input.resume_text == "[REDACTED_RESUME: 1200 characters]"
    assert draft.input.jd_text == "[REDACTED_JD: 800 characters]"
    assert draft.expected.prompt_strategy_count_min == 3
    assert "transient analyzer failures" in draft.expected.forbidden_new_claims[0]


def test_cli_converts_accepted_failure_candidate_to_eval_draft(tmp_path: Path) -> None:
    candidate = create_failure_candidate(_failed_trace()).move_to(
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
    candidate = create_failure_candidate(_failed_trace()).move_to(
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
    candidate = create_failure_candidate(_failed_trace()).model_copy(
        update={
            "feedback": "Token Bearer abc.secret.value and /Users/jane/private.txt leaked.",
        },
    )

    sanitized = sanitize_failure_record(candidate)

    assert "Bearer abc.secret.value" not in sanitized.feedback
    assert "/Users/jane/private.txt" not in sanitized.feedback


def _failed_trace() -> CareerRunTrace:
    return CareerRunTrace(
        run_id="run-failure-001",
        provider="fake",
        agent_mode="deterministic-fallback",
        final_status="failed-recoverable",
        planned_steps=["analyze_career_fit", "compare_prompt_strategies"],
        input_summary=InputTraceSummary(
            resume_character_count=1200,
            jd_character_count=800,
        ),
        tool_events=[
            ToolTraceEvent(
                tool_name="analyze_career_fit",
                status="failed-recoverable",
                message="Analyzer failed for C:\\Users\\Jane\\resume.docx.",
            ),
        ],
        provider_capabilities=ProviderCapabilityTraceSummary(
            supports_tool_calling=False,
            supports_structured_output=True,
            supports_streaming=False,
        ),
        harness=HarnessTraceConfiguration(
            prompt_set="default",
            tool_catalog_version="tool-catalog-v1",
            policy_version="policy-v1",
            retry_budget=1,
        ),
        expected_behavior=(
            "Recover from transient analyzer failures without inventing resume facts."
        ),
    )
