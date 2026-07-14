from pathlib import Path

from career_ai.evals.graders import EvalCaseResult, EvalCheckResult
from career_ai.evals.runner import EvalSuiteResult, collect_failed_check_messages, run_eval_suite
from career_ai.llm.client import FakeLLMClient


def test_run_eval_suite_runs_fake_provider_cases_and_summarizes_results() -> None:
    # Given: the repository golden eval cases and deterministic fake provider.
    case_dir = Path("evals/career_cases")
    prompt_dir = Path("prompts")

    # When: the eval suite runs through the harness.
    result = run_eval_suite(case_dir=case_dir, prompt_dir=prompt_dir, llm_client=FakeLLMClient())

    # Then: every case has check results and the aggregate counts balance.
    assert result.total_cases >= 1
    assert len(result.case_results) == result.total_cases
    assert all(case_result.checks for case_result in result.case_results)
    assert result.passed_cases + result.failed_cases == result.total_cases
    assert result.failed_cases == 0


def test_collect_failed_check_messages_reports_only_failed_checks() -> None:
    # Given: an eval suite result with one failed check and one passing check.
    result = EvalSuiteResult(
        total_cases=1,
        passed_cases=0,
        failed_cases=1,
        case_results=[
            EvalCaseResult(
                case_id="case-1",
                passed=False,
                checks=[
                    EvalCheckResult(name="role_title", passed=True, message="ok"),
                    EvalCheckResult(
                        name="missing_keywords",
                        passed=False,
                        message="Missing required keywords: SQL.",
                    ),
                ],
            ),
        ],
    )

    # When: report messages are collected for matrix output.
    messages = collect_failed_check_messages(result)

    # Then: only failed checks are rendered with stable case context.
    assert messages == ["case-1:missing_keywords: Missing required keywords: SQL."]
