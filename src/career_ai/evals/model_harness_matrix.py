from pathlib import Path
from typing import Literal

from pydantic import Field

from career_ai.evals.runner import EvalSuiteResult, collect_failed_check_messages, run_eval_suite
from career_ai.llm.capabilities import CapabilityName, ProviderCapabilityProfile
from career_ai.llm.client import FakeLLMClient, LLMClient
from career_ai.llm.models import ModelProvider
from career_ai.models import FrozenModel

type MatrixRowStatus = Literal["passed", "failed", "skipped"]


class HarnessConfiguration(FrozenModel):
    """Versioned harness policy settings for one matrix row."""

    prompt_set: str = Field(min_length=1)
    tool_catalog_version: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    retry_budget: int = Field(ge=0)
    optimizer_enabled: bool


class ModelHarnessRow(FrozenModel):
    """Provider/model/harness combination to benchmark."""

    name: str = Field(min_length=1)
    capability_profile: ProviderCapabilityProfile
    harness: HarnessConfiguration
    required_capabilities: list[CapabilityName] = Field(default_factory=list)
    skip_reason: str = ""


class ModelHarnessRowResult(FrozenModel):
    """Observed eval result for one model-harness matrix row."""

    name: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    harness: HarnessConfiguration
    status: MatrixRowStatus
    passed_cases: int = Field(ge=0)
    failed_cases: int = Field(ge=0)
    failed_checks: list[str] = Field(default_factory=list)
    unsupported_capabilities: list[str] = Field(default_factory=list)
    skip_reason: str = ""
    eval_result: EvalSuiteResult | None = None


class ModelHarnessMatrixResult(FrozenModel):
    """Aggregate benchmark result across model-harness rows."""

    total_rows: int = Field(ge=0)
    passed_rows: int = Field(ge=0)
    failed_rows: int = Field(ge=0)
    skipped_rows: int = Field(ge=0)
    unsupported_capability_count: int = Field(ge=0)
    row_results: list[ModelHarnessRowResult] = Field(default_factory=list)


def run_model_harness_matrix(
    *,
    case_dir: Path,
    prompt_dir: Path,
    rows: list[ModelHarnessRow],
) -> ModelHarnessMatrixResult:
    """Run eval cases across provider/model/harness configurations."""
    row_results = [
        _run_matrix_row(case_dir=case_dir, prompt_dir=prompt_dir, row=row)
        for row in rows
    ]
    return ModelHarnessMatrixResult(
        total_rows=len(row_results),
        passed_rows=sum(1 for row_result in row_results if row_result.status == "passed"),
        failed_rows=sum(1 for row_result in row_results if row_result.status == "failed"),
        skipped_rows=sum(1 for row_result in row_results if row_result.status == "skipped"),
        unsupported_capability_count=sum(
            len(row_result.unsupported_capabilities)
            for row_result in row_results
        ),
        row_results=row_results,
    )


def default_model_harness_rows() -> list[ModelHarnessRow]:
    """Return the no-key default matrix used by the local CLI."""
    return [
        ModelHarnessRow(
            name="fake-default",
            capability_profile=ProviderCapabilityProfile.fake(),
            harness=HarnessConfiguration(
                prompt_set="default",
                tool_catalog_version="tool-catalog-v1",
                policy_version="policy-v1",
                retry_budget=1,
                optimizer_enabled=False,
            ),
        ),
    ]


def _run_matrix_row(
    *,
    case_dir: Path,
    prompt_dir: Path,
    row: ModelHarnessRow,
) -> ModelHarnessRowResult:
    unsupported = _unsupported_capabilities(row)
    if row.skip_reason:
        return _skipped_row(row=row, skip_reason=row.skip_reason, unsupported_capabilities=[])
    if unsupported:
        return _skipped_row(
            row=row,
            skip_reason=f"unsupported capabilities: {', '.join(unsupported)}",
            unsupported_capabilities=unsupported,
        )
    client = _client_for_profile(row.capability_profile)
    if client is None:
        return _skipped_row(
            row=row,
            skip_reason="provider credentials or live client are not configured",
            unsupported_capabilities=[],
        )
    eval_result = run_eval_suite(
        case_dir=case_dir,
        prompt_dir=prompt_dir,
        llm_client=client,
    )
    status: MatrixRowStatus = "passed" if eval_result.failed_cases == 0 else "failed"
    return ModelHarnessRowResult(
        name=row.name,
        provider=row.capability_profile.provider_name.value,
        model=row.capability_profile.model_name,
        harness=row.harness,
        status=status,
        passed_cases=eval_result.passed_cases,
        failed_cases=eval_result.failed_cases,
        failed_checks=collect_failed_check_messages(eval_result),
        eval_result=eval_result,
    )


def _skipped_row(
    *,
    row: ModelHarnessRow,
    skip_reason: str,
    unsupported_capabilities: list[str],
) -> ModelHarnessRowResult:
    return ModelHarnessRowResult(
        name=row.name,
        provider=row.capability_profile.provider_name.value,
        model=row.capability_profile.model_name,
        harness=row.harness,
        status="skipped",
        passed_cases=0,
        failed_cases=0,
        unsupported_capabilities=unsupported_capabilities,
        skip_reason=skip_reason,
    )


def _client_for_profile(profile: ProviderCapabilityProfile) -> LLMClient | None:
    match profile.provider_name:
        case ModelProvider.FAKE:
            return FakeLLMClient()
        case ModelProvider.OPENAI_COMPATIBLE | ModelProvider.DEEPSEEK_COMPATIBLE:
            return None


def _unsupported_capabilities(row: ModelHarnessRow) -> list[str]:
    return [
        capability.value
        for capability in row.required_capabilities
        if not _capability_supported(row.capability_profile, capability)
    ]


def _capability_supported(
    profile: ProviderCapabilityProfile,
    capability: CapabilityName,
) -> bool:
    match capability:
        case CapabilityName.STRUCTURED_OUTPUT:
            return profile.supports_structured_output
        case CapabilityName.SINGLE_TURN_TOOL_CALLS:
            return profile.supports_single_turn_tool_calls
        case CapabilityName.MULTI_TURN_TOOL_CALLS:
            return profile.supports_multi_turn_tool_calls
        case CapabilityName.REASONING_MODE:
            return profile.supports_reasoning_mode
        case CapabilityName.STREAMING:
            return profile.supports_streaming
        case CapabilityName.PROVIDER_TRACING:
            return profile.supports_provider_tracing
