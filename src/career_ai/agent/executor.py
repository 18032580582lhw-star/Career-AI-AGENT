from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from career_ai.agent.execution_loop import AgentRuntimeOptions, execute_tool_call
from career_ai.agent.memory import summarize_workflow_for_memory
from career_ai.agent.models import (
    AgentRun,
    AgentState,
    AgentStateEvent,
    AgentStateStatus,
    AgentStep,
    AgentStepStatus,
)
from career_ai.agent.planner import request_agent_plan, select_agent_mode
from career_ai.agent.quality import evaluate_career_quality
from career_ai.agent.tools import (
    AgentToolContext,
    AnalyzeCareerFitInput,
    ComparePromptStrategiesInput,
    ToolCall,
    ToolName,
    ToolResult,
    default_tool_registry,
)
from career_ai.agent.trace import (
    CareerRunTrace,
    HarnessTraceConfiguration,
    InputTraceSummary,
    ProviderCapabilityTraceSummary,
    ToolTraceEvent,
)
from career_ai.models import PromptHarnessResult
from career_ai.workflows.models import CareerFitWorkflowResult

if TYPE_CHECKING:
    from pathlib import Path

    from career_ai.agent.enforcement_models import RuntimeEnforcementEvent
    from career_ai.llm.client import LLMClient


def run_career_agent(
    *,
    resume_text: str,
    jd_text: str,
    prompt_dir: Path,
    llm_client: LLMClient,
    runtime_options: AgentRuntimeOptions | None = None,
) -> AgentRun:
    """Run the local model-neutral career agent."""
    mode = select_agent_mode(llm_client)
    events = [
        AgentStateEvent(status=AgentStateStatus.INITIALIZED, message="Agent run initialized."),
    ]
    options = runtime_options or AgentRuntimeOptions()
    registry = options.tool_runner or default_tool_registry()
    validated_plan = request_agent_plan(
        llm_client,
        options.tool_catalog,
        options.autonomy_policy,
    )
    planned_steps = validated_plan.planned_steps
    events.append(
        AgentStateEvent(
            status=AgentStateStatus.PLANNED,
            message=f"Planned {len(planned_steps)} model steps.",
        ),
    )
    enforcement_events: list[RuntimeEnforcementEvent] = []
    for rejected_step in validated_plan.rejected_steps:
        events.append(
            AgentStateEvent(
                status=AgentStateStatus.TOOL_SKIPPED,
                tool_name=rejected_step,
                message="Model-planned action denied by controlled-autonomy policy.",
            ),
        )
        enforcement_events.append(options.runtime_policy.enforce_external_action(rejected_step))
    policy = options.execution_policy
    calls = _tool_calls_from_plan(
        planned_steps=planned_steps,
        resume_text=resume_text,
        jd_text=jd_text,
        prompt_dir=prompt_dir,
    )
    context = AgentToolContext(prompt_dir=prompt_dir)
    steps: list[AgentStep] = []
    results: list[ToolResult] = []
    for call in calls:
        record = execute_tool_call(
            call=call,
            context=context,
            runner=registry,
            options=options.tool_execution_options(),
        )
        steps.append(record.step)
        events.extend(record.events)
        enforcement_events.extend(record.enforcement_events)
        if record.result is not None:
            results.append(record.result)
            if record.result.report is not None:
                context = context.model_copy(update={"report": record.result.report})
    workflow = _workflow_from_results(results)
    final_state = _final_state_from_steps(steps)
    events.append(AgentStateEvent(status=final_state, message="Agent run finished."))
    quality_report = evaluate_career_quality(
        workflow=workflow,
        resume_text=resume_text,
        jd_text=jd_text,
        llm_client=llm_client,
        options=options.quality_optimizer,
    )
    trace = CareerRunTrace(
        run_id=str(uuid4()),
        provider=llm_client.provider.value,
        agent_mode=mode.value,
        final_status=final_state.value,
        planned_steps=planned_steps,
        input_summary=InputTraceSummary.from_inputs(
            resume_text=resume_text,
            jd_text=jd_text,
        ),
        tool_events=[
            ToolTraceEvent(
                tool_name=event.tool_name,
                status=event.status.value,
                message=event.message,
            )
            for event in events
            if event.tool_name
        ],
        provider_capabilities=ProviderCapabilityTraceSummary.from_capabilities(
            llm_client.capabilities,
        ),
        harness=HarnessTraceConfiguration.from_runtime(
            prompt_dir=prompt_dir,
            retry_budget=policy.max_tool_attempts - 1,
        ),
        enforcement_events=enforcement_events,
    )
    return AgentRun(
        mode=mode,
        planned_steps=planned_steps,
        state=AgentState(status=final_state, events=events),
        steps=steps,
        workflow=workflow,
        memory_summary=summarize_workflow_for_memory(workflow),
        trace=trace,
        quality_report=quality_report,
    )


def _tool_calls_from_plan(
    *,
    planned_steps: list[str],
    resume_text: str,
    jd_text: str,
    prompt_dir: Path,
) -> list[ToolCall]:
    supported_steps = set(planned_steps)
    calls: list[ToolCall] = []
    if not supported_steps or "analyze_career_fit" in supported_steps:
        calls.append(
            ToolCall(
                name=ToolName.ANALYZE_CAREER_FIT,
                arguments=AnalyzeCareerFitInput(
                    resume_text=resume_text,
                    jd_text=jd_text,
                ),
            ),
        )
    if not supported_steps or "compare_prompt_strategies" in supported_steps:
        calls.append(
            ToolCall(
                name=ToolName.COMPARE_PROMPT_STRATEGIES,
                arguments=ComparePromptStrategiesInput(
                    resume_text=resume_text,
                    jd_text=jd_text,
                    prompt_dir=prompt_dir,
                ),
            ),
        )
    if not any(call.name == ToolName.ANALYZE_CAREER_FIT for call in calls):
        calls.insert(
            0,
            ToolCall(
                name=ToolName.ANALYZE_CAREER_FIT,
                arguments=AnalyzeCareerFitInput(
                    resume_text=resume_text,
                    jd_text=jd_text,
                ),
            ),
        )
    return calls


def _workflow_from_results(results: list[ToolResult]) -> CareerFitWorkflowResult:
    report = next(result.report for result in results if result.report is not None)
    prompt_result = next(
        (result.prompt_result for result in results if result.prompt_result is not None),
        PromptHarnessResult(strategies=[], best_strategy_name=""),
    )
    return CareerFitWorkflowResult(
        report=report,
        prompt_result=prompt_result,
        steps=[result.name.value for result in results],
    )


def _final_state_from_steps(steps: list[AgentStep]) -> AgentStateStatus:
    if any(step.status == AgentStepStatus.SKIPPED for step in steps):
        return AgentStateStatus.COMPLETED_WITH_RECOVERY
    if any(step.status == AgentStepStatus.FAILED_RECOVERABLE for step in steps):
        return AgentStateStatus.FAILED_RECOVERABLE
    return AgentStateStatus.COMPLETED
