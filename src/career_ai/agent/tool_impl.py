from career_ai.agent.tool_models import (
    AgentToolContext,
    AnalyzeCareerFitInput,
    ComparePromptStrategiesInput,
    ExportDocxInput,
    ExtractResumeInput,
    FetchJDInput,
    SaveMemorySummaryInput,
    ToolArguments,
    ToolName,
    ToolResult,
    ToolStatus,
)
from career_ai.analysis import analyze_career_fit
from career_ai.exporters import build_cover_letter_docx, build_resume_docx
from career_ai.jd_fetcher import FetchFailure, FetchSuccess, fetch_job_description_from_url
from career_ai.prompt_harness import compare_prompt_strategies
from career_ai.text_processing import extract_resume_text


def tool_failure(name: ToolName, message: str) -> ToolResult:
    """Create a recoverable local tool failure."""
    return ToolResult(
        name=name,
        status=ToolStatus.FAILURE,
        message=message,
        recoverable=True,
    )


def run_fetch_jd(arguments: ToolArguments) -> ToolResult:
    """Fetch JD text from a public URL."""
    match arguments:
        case FetchJDInput(url=url):
            result = fetch_job_description_from_url(url)
            match result:
                case FetchSuccess(text=text):
                    return ToolResult(
                        name=ToolName.FETCH_JD,
                        status=ToolStatus.SUCCESS,
                        message="Fetched JD text.",
                        text=text,
                    )
                case FetchFailure(message=message):
                    return tool_failure(ToolName.FETCH_JD, message)
        case _:
            return tool_failure(ToolName.FETCH_JD, "expected FetchJDInput")


def run_extract_resume(arguments: ToolArguments) -> ToolResult:
    """Extract resume text from a local file."""
    match arguments:
        case ExtractResumeInput(path=path):
            text = extract_resume_text(path)
            if text:
                return ToolResult(
                    name=ToolName.EXTRACT_RESUME,
                    status=ToolStatus.SUCCESS,
                    message="Extracted resume text.",
                    text=text,
                )
            return tool_failure(ToolName.EXTRACT_RESUME, "Resume text was empty.")
        case _:
            return tool_failure(ToolName.EXTRACT_RESUME, "expected ExtractResumeInput")


def run_analyze_career_fit(arguments: ToolArguments) -> ToolResult:
    """Run the deterministic career-fit analyzer."""
    match arguments:
        case AnalyzeCareerFitInput(resume_text=resume_text, jd_text=jd_text):
            report = analyze_career_fit(resume_text=resume_text, jd_text=jd_text)
            return ToolResult(
                name=ToolName.ANALYZE_CAREER_FIT,
                status=ToolStatus.SUCCESS,
                message="Analyzed career fit.",
                report=report,
            )
        case _:
            return tool_failure(ToolName.ANALYZE_CAREER_FIT, "expected AnalyzeCareerFitInput")


def run_compare_prompt_strategies(arguments: ToolArguments) -> ToolResult:
    """Compare prompt strategies with the deterministic harness."""
    match arguments:
        case ComparePromptStrategiesInput(
            resume_text=resume_text,
            jd_text=jd_text,
            prompt_dir=prompt_dir,
        ):
            prompt_result = compare_prompt_strategies(
                prompt_dir=prompt_dir,
                resume_text=resume_text,
                jd_text=jd_text,
            )
            if not prompt_result.strategies:
                return tool_failure(
                    ToolName.COMPARE_PROMPT_STRATEGIES,
                    "Strategy profile is unavailable.",
                )
            return ToolResult(
                name=ToolName.COMPARE_PROMPT_STRATEGIES,
                status=ToolStatus.SUCCESS,
                message="Graded tailoring strategies.",
                prompt_result=prompt_result,
            )
        case _:
            return tool_failure(
                ToolName.COMPARE_PROMPT_STRATEGIES,
                "expected ComparePromptStrategiesInput",
            )


def run_export_resume_docx(
    arguments: ToolArguments,
    context: AgentToolContext,
) -> ToolResult:
    """Export a tailored resume DOCX from an existing report."""
    match arguments:
        case ExportDocxInput(output_path=output_path):
            if context.report is None:
                return tool_failure(ToolName.EXPORT_RESUME_DOCX, "Career report is required.")
            path = build_resume_docx(context.report, output_path)
            return ToolResult(
                name=ToolName.EXPORT_RESUME_DOCX,
                status=ToolStatus.SUCCESS,
                message="Exported tailored resume.",
                path=path,
            )
        case _:
            return tool_failure(ToolName.EXPORT_RESUME_DOCX, "expected ExportDocxInput")


def run_export_cover_letter_docx(
    arguments: ToolArguments,
    context: AgentToolContext,
) -> ToolResult:
    """Export a cover letter DOCX from an existing report."""
    match arguments:
        case ExportDocxInput(output_path=output_path):
            if context.report is None:
                return tool_failure(
                    ToolName.EXPORT_COVER_LETTER_DOCX,
                    "Career report is required.",
                )
            path = build_cover_letter_docx(context.report, output_path)
            return ToolResult(
                name=ToolName.EXPORT_COVER_LETTER_DOCX,
                status=ToolStatus.SUCCESS,
                message="Exported cover letter.",
                path=path,
            )
        case _:
            return tool_failure(ToolName.EXPORT_COVER_LETTER_DOCX, "expected ExportDocxInput")


def run_save_memory_summary(arguments: ToolArguments) -> ToolResult:
    """Prepare a privacy-preserving memory summary result."""
    match arguments:
        case SaveMemorySummaryInput() as summary:
            return ToolResult(
                name=ToolName.SAVE_MEMORY_SUMMARY,
                status=ToolStatus.SUCCESS,
                message="Prepared memory summary.",
                memory_summary=summary,
            )
        case _:
            return tool_failure(ToolName.SAVE_MEMORY_SUMMARY, "expected SaveMemorySummaryInput")
