from enum import StrEnum, unique
from pathlib import Path

from pydantic import Field

from career_ai.models import CareerFitReport, FrozenModel, PromptHarnessResult


@unique
class ToolName(StrEnum):
    """Stable tool names exposed to the agent runtime."""

    FETCH_JD = "fetch_jd"
    EXTRACT_RESUME = "extract_resume"
    ANALYZE_CAREER_FIT = "analyze_career_fit"
    COMPARE_PROMPT_STRATEGIES = "compare_prompt_strategies"
    EXPORT_RESUME_DOCX = "export_resume_docx"
    EXPORT_COVER_LETTER_DOCX = "export_cover_letter_docx"
    SAVE_MEMORY_SUMMARY = "save_memory_summary"


@unique
class ToolStatus(StrEnum):
    """Final status for a tool invocation."""

    SUCCESS = "success"
    FAILURE = "failure"


class FetchJDInput(FrozenModel):
    """Input for fetching readable JD text from a URL."""

    url: str


class ExtractResumeInput(FrozenModel):
    """Input for extracting resume text from a local file."""

    path: Path


class AnalyzeCareerFitInput(FrozenModel):
    """Input for the core career-fit analyzer."""

    resume_text: str
    jd_text: str


class ComparePromptStrategiesInput(FrozenModel):
    """Input for deterministic prompt strategy comparison."""

    resume_text: str
    jd_text: str
    prompt_dir: Path


class ExportDocxInput(FrozenModel):
    """Input for DOCX export tools."""

    output_path: Path


class SaveMemorySummaryInput(FrozenModel):
    """Input for storing a privacy-preserving memory summary."""

    role_title: str
    match_score: int
    missing_keywords: list[str] = Field(default_factory=list)


type ToolArguments = (
    FetchJDInput
    | ExtractResumeInput
    | AnalyzeCareerFitInput
    | ComparePromptStrategiesInput
    | ExportDocxInput
    | SaveMemorySummaryInput
)


class ToolCall(FrozenModel):
    """A validated tool request from planner to executor."""

    name: ToolName
    arguments: ToolArguments


class AgentToolContext(FrozenModel):
    """Read-only execution context shared across tool calls."""

    prompt_dir: Path
    report: CareerFitReport | None = None


class ToolResult(FrozenModel):
    """Normalized result returned by every agent tool."""

    name: ToolName
    status: ToolStatus
    message: str
    recoverable: bool = False
    text: str = ""
    path: Path | None = None
    report: CareerFitReport | None = None
    prompt_result: PromptHarnessResult | None = None
    memory_summary: SaveMemorySummaryInput | None = None
