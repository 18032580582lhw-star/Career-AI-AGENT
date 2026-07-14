from pathlib import Path

from career_ai.evals.model_harness_matrix import (
    HarnessConfiguration,
    ModelHarnessRow,
    run_model_harness_matrix,
)
from career_ai.llm.capabilities import CapabilityName, ProviderCapabilityProfile


def test_model_harness_matrix_runs_fake_provider_row_without_credentials() -> None:
    # Given: a deterministic fake-provider matrix row.
    row = ModelHarnessRow(
        name="fake-default",
        capability_profile=ProviderCapabilityProfile.fake(),
        harness=HarnessConfiguration(
            prompt_set="default",
            tool_catalog_version="tool-catalog-v1",
            policy_version="policy-v1",
            retry_budget=1,
            optimizer_enabled=False,
        ),
    )

    # When: the model-harness matrix runs against the golden eval cases.
    result = run_model_harness_matrix(
        case_dir=Path("evals/career_cases"),
        prompt_dir=Path("prompts"),
        rows=[row],
    )

    # Then: the row runs locally and records its full harness configuration.
    assert result.total_rows == 1
    assert result.passed_rows == 1
    assert result.failed_rows == 0
    assert result.skipped_rows == 0
    assert result.unsupported_capability_count == 0
    row_result = result.row_results[0]
    assert row_result.name == "fake-default"
    assert row_result.status == "passed"
    assert row_result.provider == "fake"
    assert row_result.model == "local-fake"
    assert row_result.harness.prompt_set == "default"
    assert row_result.harness.tool_catalog_version == "tool-catalog-v1"
    assert row_result.harness.policy_version == "policy-v1"
    assert row_result.harness.retry_budget == 1
    assert row_result.harness.optimizer_enabled is False
    assert row_result.eval_result is not None
    assert row_result.eval_result.total_cases >= 1
    assert row_result.failed_checks == []


def test_model_harness_matrix_reports_skips_and_unsupported_capabilities() -> None:
    # Given: skipped and unsupported rows that must not call external providers.
    explicit_skip = ModelHarnessRow(
        name="manual-skip",
        capability_profile=ProviderCapabilityProfile.fake(),
        harness=HarnessConfiguration(
            prompt_set="default",
            tool_catalog_version="tool-catalog-v1",
            policy_version="policy-v1",
            retry_budget=0,
            optimizer_enabled=False,
        ),
        skip_reason="credentials not configured",
    )
    unsupported_tools = ModelHarnessRow(
        name="fake-tools-required",
        capability_profile=ProviderCapabilityProfile.fake(),
        harness=HarnessConfiguration(
            prompt_set="default",
            tool_catalog_version="tool-catalog-v2",
            policy_version="policy-v1",
            retry_budget=0,
            optimizer_enabled=True,
        ),
        required_capabilities=[CapabilityName.SINGLE_TURN_TOOL_CALLS],
    )

    # When: the matrix evaluates rows with unavailable configurations.
    result = run_model_harness_matrix(
        case_dir=Path("evals/career_cases"),
        prompt_dir=Path("prompts"),
        rows=[explicit_skip, unsupported_tools],
    )

    # Then: skips and unsupported capabilities are separated in the aggregate.
    assert result.total_rows == 2
    assert result.passed_rows == 0
    assert result.failed_rows == 0
    assert result.skipped_rows == 2
    assert result.unsupported_capability_count == 1
    assert result.row_results[0].status == "skipped"
    assert result.row_results[0].skip_reason == "credentials not configured"
    assert result.row_results[1].status == "skipped"
    assert result.row_results[1].unsupported_capabilities == ["single_turn_tool_calls"]
