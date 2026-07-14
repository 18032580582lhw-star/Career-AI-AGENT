from urllib.parse import urlparse

from pydantic import Field

from career_ai.agent.enforcement_boundaries import (
    is_blocked_fetch_target,
    is_suspicious_export_path,
)
from career_ai.agent.enforcement_events import (
    allowed_check,
    denied_check,
    external_action_event,
    make_event,
    post_fetch_event,
)
from career_ai.agent.enforcement_models import (
    DEFAULT_RUNTIME_POLICY_VERSION,
    RuntimeBoundary,
    RuntimeEnforcementEvent,
    RuntimePolicyCheck,
    RuntimePolicyDecision,
)
from career_ai.agent.enforcement_redaction import redact_memory_summary
from career_ai.agent.tool_models import (
    AgentToolContext,
    AnalyzeCareerFitInput,
    ComparePromptStrategiesInput,
    ExportDocxInput,
    ExtractResumeInput,
    FetchJDInput,
    SaveMemorySummaryInput,
    ToolCall,
    ToolName,
    ToolResult,
)
from career_ai.models import FrozenModel


class RuntimePolicy(FrozenModel):
    """Default execution-time policy for local career-agent boundaries."""

    policy_version: str = Field(default=DEFAULT_RUNTIME_POLICY_VERSION, min_length=1)

    def enforce_pre_tool_call(
        self,
        *,
        call: ToolCall,
        context: AgentToolContext,
    ) -> RuntimePolicyCheck:
        """Check and sanitize a tool call before any implementation executes."""
        match call.name:
            case ToolName.FETCH_JD:
                return self._enforce_fetch_jd(call)
            case ToolName.EXTRACT_RESUME:
                return self._enforce_extract_resume(call)
            case ToolName.ANALYZE_CAREER_FIT:
                return self._enforce_analyze_career_fit(call)
            case ToolName.COMPARE_PROMPT_STRATEGIES:
                return self._enforce_compare_prompt_strategies(call)
            case ToolName.EXPORT_RESUME_DOCX | ToolName.EXPORT_COVER_LETTER_DOCX:
                return self._enforce_document_export(call=call, context=context)
            case ToolName.SAVE_MEMORY_SUMMARY:
                return self._enforce_save_memory_summary(call)

    def enforce_post_tool_call(
        self,
        *,
        call: ToolCall,
        result: ToolResult,
    ) -> RuntimeEnforcementEvent:
        """Record the post-tool boundary decision for a completed tool result."""
        match call.name:
            case ToolName.FETCH_JD:
                return self._post_fetch_event(call=call, result=result)
            case (
                ToolName.EXTRACT_RESUME
                | ToolName.ANALYZE_CAREER_FIT
                | ToolName.COMPARE_PROMPT_STRATEGIES
                | ToolName.EXPORT_RESUME_DOCX
                | ToolName.EXPORT_COVER_LETTER_DOCX
                | ToolName.SAVE_MEMORY_SUMMARY
            ):
                return make_event(
                    policy_version=self.policy_version,
                    boundary=RuntimeBoundary.POST_TOOL_CALL,
                    decision=RuntimePolicyDecision.ALLOWED,
                    reason=f"{call.name.value} completed runtime post-tool checks.",
                    tool_name=call.name,
                )

    def enforce_external_action(self, action_name: str) -> RuntimeEnforcementEvent:
        """Deny model-proposed external actions outside local analysis."""
        return external_action_event(policy_version=self.policy_version, action_name=action_name)

    def _enforce_fetch_jd(self, call: ToolCall) -> RuntimePolicyCheck:
        match call.arguments:
            case FetchJDInput(url=url):
                return self._enforce_network_fetch(call=call, url=url)
            case _:
                return self._denied_check(
                    call=call,
                    boundary=RuntimeBoundary.PRE_TOOL_CALL,
                    reason="fetch_jd expected FetchJDInput.",
                )

    def _enforce_extract_resume(self, call: ToolCall) -> RuntimePolicyCheck:
        match call.arguments:
            case ExtractResumeInput():
                return self._allowed_check(call, RuntimeBoundary.PRE_TOOL_CALL)
            case _:
                return self._denied_check(
                    call=call,
                    boundary=RuntimeBoundary.PRE_TOOL_CALL,
                    reason="extract_resume expected ExtractResumeInput.",
                )

    def _enforce_analyze_career_fit(self, call: ToolCall) -> RuntimePolicyCheck:
        match call.arguments:
            case AnalyzeCareerFitInput():
                return self._allowed_check(call, RuntimeBoundary.PRE_TOOL_CALL)
            case _:
                return self._denied_check(
                    call=call,
                    boundary=RuntimeBoundary.PRE_TOOL_CALL,
                    reason="analyze_career_fit expected AnalyzeCareerFitInput.",
                )

    def _enforce_compare_prompt_strategies(self, call: ToolCall) -> RuntimePolicyCheck:
        match call.arguments:
            case ComparePromptStrategiesInput():
                return self._allowed_check(call, RuntimeBoundary.PRE_TOOL_CALL)
            case _:
                return self._denied_check(
                    call=call,
                    boundary=RuntimeBoundary.PRE_TOOL_CALL,
                    reason="compare_prompt_strategies expected ComparePromptStrategiesInput.",
                )

    def _enforce_document_export(
        self,
        *,
        call: ToolCall,
        context: AgentToolContext,
    ) -> RuntimePolicyCheck:
        match call.arguments:
            case ExportDocxInput(output_path=output_path):
                if context.report is None:
                    return self._denied_check(
                        call=call,
                        boundary=RuntimeBoundary.DOCUMENT_EXPORT,
                        reason=f"{call.name.value} requires a generated report.",
                    )
                if is_suspicious_export_path(output_path):
                    return self._denied_check(
                        call=call,
                        boundary=RuntimeBoundary.DOCUMENT_EXPORT,
                        reason=f"{call.name.value} output path is not allowed.",
                    )
                return self._allowed_check(call, RuntimeBoundary.DOCUMENT_EXPORT)
            case _:
                return self._denied_check(
                    call=call,
                    boundary=RuntimeBoundary.DOCUMENT_EXPORT,
                    reason=f"{call.name.value} expected ExportDocxInput.",
                )

    def _enforce_save_memory_summary(self, call: ToolCall) -> RuntimePolicyCheck:
        match call.arguments:
            case SaveMemorySummaryInput() as summary:
                redacted = redact_memory_summary(summary)
                if redacted == summary:
                    return self._allowed_check(call, RuntimeBoundary.MEMORY_WRITE)
                redacted_call = call.model_copy(update={"arguments": redacted})
                return RuntimePolicyCheck(
                    call=redacted_call,
                    event=make_event(
                        policy_version=self.policy_version,
                        boundary=RuntimeBoundary.MEMORY_WRITE,
                        decision=RuntimePolicyDecision.REDACTED,
                        reason="save_memory_summary had sensitive fragments redacted.",
                        tool_name=call.name,
                    ),
                    allowed_to_run=True,
                )
            case _:
                return self._denied_check(
                    call=call,
                    boundary=RuntimeBoundary.MEMORY_WRITE,
                    reason="save_memory_summary expected SaveMemorySummaryInput.",
                )

    def _enforce_network_fetch(self, *, call: ToolCall, url: str) -> RuntimePolicyCheck:
        parsed_url = urlparse(url)
        match parsed_url.scheme:
            case "data":
                return self._allowed_check(call, RuntimeBoundary.NETWORK_FETCH)
            case "http" | "https":
                hostname = parsed_url.hostname
                if hostname is None:
                    return self._denied_check(
                        call=call,
                        boundary=RuntimeBoundary.NETWORK_FETCH,
                        reason="fetch_jd URL host is not allowed.",
                    )
                if is_blocked_fetch_target(url):
                    return self._denied_check(
                        call=call,
                        boundary=RuntimeBoundary.NETWORK_FETCH,
                        reason="fetch_jd URL host is not allowed.",
                    )
                return self._allowed_check(call, RuntimeBoundary.NETWORK_FETCH)
            case "":
                return self._denied_check(
                    call=call,
                    boundary=RuntimeBoundary.NETWORK_FETCH,
                    reason="fetch_jd requires an http, https, or data URL.",
                )
            case _:
                return self._denied_check(
                    call=call,
                    boundary=RuntimeBoundary.NETWORK_FETCH,
                    reason="fetch_jd URL scheme is not supported.",
                )

    def _post_fetch_event(self, *, call: ToolCall, result: ToolResult) -> RuntimeEnforcementEvent:
        return post_fetch_event(policy_version=self.policy_version, call=call, result=result)

    def _allowed_check(self, call: ToolCall, boundary: RuntimeBoundary) -> RuntimePolicyCheck:
        return allowed_check(
            policy_version=self.policy_version,
            call=call,
            boundary=boundary,
        )

    def _denied_check(
        self,
        *,
        call: ToolCall,
        boundary: RuntimeBoundary,
        reason: str,
    ) -> RuntimePolicyCheck:
        return denied_check(
            policy_version=self.policy_version,
            call=call,
            boundary=boundary,
            reason=reason,
        )
