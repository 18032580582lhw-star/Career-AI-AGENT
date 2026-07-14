from enum import StrEnum, unique

from pydantic import Field

from career_ai.agent.quality import CareerQualityReport
from career_ai.agent.tool_models import ToolName
from career_ai.agent.trace import CareerRunTrace
from career_ai.models import FrozenModel
from career_ai.workflows.models import CareerFitWorkflowResult


@unique
class AgentMode(StrEnum):
    """Execution mode selected from model capabilities."""

    DETERMINISTIC_FALLBACK = "deterministic-fallback"
    STRUCTURED_PLAN = "structured-plan"
    TOOL_CALLING = "tool-calling"


@unique
class AgentStepStatus(StrEnum):
    """Lifecycle status for one local agent step."""

    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED_RECOVERABLE = "failed-recoverable"


@unique
class AgentStateStatus(StrEnum):
    """State-machine statuses for one agent run."""

    INITIALIZED = "initialized"
    PLANNED = "planned"
    RUNNING_TOOL = "running-tool"
    TOOL_COMPLETED = "tool-completed"
    RECOVERING = "recovering"
    RECOVERY_DECIDED = "recovery-decided"
    FAILED_RECOVERABLE = "failed-recoverable"
    TOOL_SKIPPED = "tool-skipped"
    COMPLETED = "completed"
    COMPLETED_WITH_RECOVERY = "completed-with-recovery"


class AgentExecutionPolicy(FrozenModel):
    """Execution-loop policy for retries and recoverable failures."""

    max_tool_attempts: int = Field(default=2, ge=1)


class AgentAutonomyPolicy(FrozenModel):
    """Bound the local tool choices that a model may place in a run plan."""

    allowed_tools: list[ToolName] = Field(
        default_factory=lambda: [
            ToolName.ANALYZE_CAREER_FIT,
            ToolName.COMPARE_PROMPT_STRATEGIES,
        ],
    )
    required_tools: list[ToolName] = Field(
        default_factory=lambda: [ToolName.ANALYZE_CAREER_FIT],
    )
    forbidden_tool_patterns: list[str] = Field(
        default_factory=lambda: [
            "apply",
            "credential",
            "email",
            "environment",
            "git",
            "send_",
            "shell",
        ],
    )
    max_model_planned_steps: int = Field(default=2, ge=1)


class ValidatedAgentPlan(FrozenModel):
    """Model plan after local policy validation and critical-tool repair."""

    planned_steps: list[str]
    rejected_steps: list[str] = Field(default_factory=list)


class AgentStep(FrozenModel):
    """One executable agent step and its final status."""

    name: str
    status: AgentStepStatus
    message: str = ""


class AgentStateEvent(FrozenModel):
    """One state transition recorded by the executor."""

    status: AgentStateStatus
    tool_name: str = ""
    message: str = ""


class AgentState(FrozenModel):
    """Final state and event log for one agent run."""

    status: AgentStateStatus
    events: list[AgentStateEvent]


class CareerProfileMemory(FrozenModel):
    """Privacy-preserving career profile retained between local runs."""

    target_role_title: str
    target_role_family: str
    confirmed_skills: list[str]
    recurring_missing_keywords: list[str]
    preferred_output_language: str
    last_match_score: int

    @property
    def role_title(self) -> str:
        """Provide the previous summary name without serializing a duplicate field."""
        return self.target_role_title

    @property
    def match_score(self) -> int:
        """Provide the previous summary name without serializing a duplicate field."""
        return self.last_match_score

    @property
    def missing_keywords(self) -> list[str]:
        """Provide the previous summary name without serializing a duplicate field."""
        return self.recurring_missing_keywords


MemorySummary = CareerProfileMemory


class AgentRun(FrozenModel):
    """Complete local agent run result."""

    mode: AgentMode
    planned_steps: list[str]
    state: AgentState
    steps: list[AgentStep]
    workflow: CareerFitWorkflowResult
    memory_summary: CareerProfileMemory
    trace: CareerRunTrace
    quality_report: CareerQualityReport
