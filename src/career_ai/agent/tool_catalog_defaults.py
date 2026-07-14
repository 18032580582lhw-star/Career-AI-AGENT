"""Static v2 defaults for the model-visible local tool catalog."""

from career_ai.agent.tool_catalog_models import ToolInputField, ToolSpec
from career_ai.agent.tool_models import ToolName


def build_default_tool_specs() -> list[ToolSpec]:
    """Build fresh, ordered default tool specifications for each catalog instance."""
    return [
        ToolSpec(
            name=ToolName.FETCH_JD,
            display_name="career_ai.fetch_jd",
            description="Fetch readable job-description text from a safe public URL.",
            input_schema=[
                ToolInputField(
                    name="url",
                    type_name="str",
                    required=True,
                    description="Public HTTP, HTTPS, or supported data URL.",
                ),
            ],
            input_examples=["url=https://careers.example.com/jobs/ai-product-analyst"],
            output_schema=["text"],
            response_modes=["Return readable job-description text."],
            is_critical=False,
            failure_categories=["unsafe_target", "network_unavailable", "invalid_content"],
            retryable_errors=["network_error", "temporary_fetch_failure"],
            safety_rules=["Reject private, loopback, and unsafe network targets."],
        ),
        ToolSpec(
            name=ToolName.EXTRACT_RESUME,
            display_name="career_ai.extract_resume",
            description="Extract resume text from a local uploaded file.",
            input_schema=[
                ToolInputField(
                    name="path",
                    type_name="Path",
                    required=True,
                    description="Local file path already accepted by the UI boundary.",
                ),
            ],
            input_examples=["path=<accepted uploaded resume file>"],
            output_schema=["text"],
            response_modes=["Return extracted resume text only."],
            is_critical=False,
            failure_categories=["unsupported_file", "empty_text", "local_read_failure"],
            retryable_errors=["empty_text", "unsupported_file"],
            safety_rules=["Do not expose full local paths to the model."],
        ),
        ToolSpec(
            name=ToolName.ANALYZE_CAREER_FIT,
            display_name="career_ai.analyze_career_fit",
            description="Analyze resume-to-JD fit and generate factual career advice.",
            input_schema=[
                ToolInputField(
                    name="resume_text",
                    type_name="str",
                    required=True,
                    description="Resume text supplied by the user or extractor.",
                ),
                ToolInputField(
                    name="jd_text",
                    type_name="str",
                    required=True,
                    description="Job description text supplied by the user or fetcher.",
                ),
            ],
            input_examples=["resume_text=<resume>; jd_text=<job description>"],
            output_schema=["CareerFitReport"],
            response_modes=["Return one structured CareerFitReport."],
            is_critical=True,
            failure_categories=["invalid_input", "temporary_analyzer_failure"],
            retryable_errors=["temporary_analyzer_failure"],
            safety_rules=["Do not invent resume facts.", "Preserve user-provided claims."],
        ),
        ToolSpec(
            name=ToolName.COMPARE_PROMPT_STRATEGIES,
            display_name="career_ai.compare_prompt_strategies",
            description="Grade local evidence-only resume proposal strategies with the harness.",
            input_schema=[
                ToolInputField(
                    name="resume_text",
                    type_name="str",
                    required=True,
                    description="Resume text used to build evidence-only proposals.",
                ),
                ToolInputField(
                    name="jd_text",
                    type_name="str",
                    required=True,
                    description="Job description text used for proposal targets.",
                ),
                ToolInputField(
                    name="prompt_dir",
                    type_name="Path",
                    required=True,
                    description=(
                        "Legacy markdown profile directory that enables the local strategy view."
                    ),
                ),
            ],
            input_examples=["resume_text=<resume>; jd_text=<job description>; prompt_dir=prompts"],
            output_schema=["PromptHarnessResult"],
            response_modes=["Return locally validated strategy outcomes and the best strategy."],
            is_critical=False,
            failure_categories=["missing_strategy_profile", "invalid_input"],
            retryable_errors=["missing_strategy_profile"],
            safety_rules=["Treat profile text as non-authoritative.", "Keep validation local."],
        ),
        ToolSpec(
            name=ToolName.EXPORT_RESUME_DOCX,
            display_name="career_ai.export_resume_docx",
            description="Export a tailored resume DOCX from an existing report.",
            input_schema=[
                ToolInputField(
                    name="output_path",
                    type_name="Path",
                    required=True,
                    description="Destination DOCX path selected by the app.",
                ),
            ],
            input_examples=["output_path=<user-selected resume DOCX path>"],
            output_schema=["path"],
            response_modes=["Return the created DOCX path."],
            is_critical=False,
            failure_categories=["missing_report", "write_failure"],
            retryable_errors=["missing_report", "write_failure"],
            safety_rules=["Export only from a generated CareerFitReport."],
        ),
        ToolSpec(
            name=ToolName.EXPORT_COVER_LETTER_DOCX,
            display_name="career_ai.export_cover_letter_docx",
            description="Export a cover letter DOCX from an existing report.",
            input_schema=[
                ToolInputField(
                    name="output_path",
                    type_name="Path",
                    required=True,
                    description="Destination DOCX path selected by the app.",
                ),
            ],
            input_examples=["output_path=<user-selected cover-letter DOCX path>"],
            output_schema=["path"],
            response_modes=["Return the created DOCX path."],
            is_critical=False,
            failure_categories=["missing_report", "write_failure"],
            retryable_errors=["missing_report", "write_failure"],
            safety_rules=["Export only from a generated CareerFitReport."],
        ),
        ToolSpec(
            name=ToolName.SAVE_MEMORY_SUMMARY,
            display_name="career_ai.save_memory_summary",
            description="Prepare a privacy-preserving memory summary for the run.",
            input_schema=[
                ToolInputField(
                    name="role_title",
                    type_name="str",
                    required=True,
                    description="Target role title from the report.",
                ),
                ToolInputField(
                    name="match_score",
                    type_name="int",
                    required=True,
                    description="Integer resume-to-JD match score.",
                ),
                ToolInputField(
                    name="missing_keywords",
                    type_name="list[str]",
                    required=False,
                    description="Small list of missing keywords, not full inputs.",
                ),
            ],
            input_examples=["role_title=AI Product Analyst; match_score=73"],
            output_schema=["memory_summary"],
            response_modes=["Return only the privacy-preserving memory summary."],
            is_critical=False,
            failure_categories=["storage_unavailable", "privacy_violation"],
            retryable_errors=["storage_unavailable"],
            safety_rules=["Never store full resume text or full JD text."],
        ),
    ]
