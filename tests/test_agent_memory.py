from career_ai.agent.memory import (
    redact_memory_unsafe_text,
    summarize_workflow_for_memory,
)
from career_ai.analysis import analyze_career_fit, get_sample_inputs
from career_ai.models import PromptHarnessResult
from career_ai.workflows.models import CareerFitWorkflowResult


def test_summarize_workflow_for_memory_creates_privacy_preserving_career_profile() -> None:
    # Given: the deterministic workflow output and its original sensitive source texts.
    resume_text, jd_text = get_sample_inputs()
    report = analyze_career_fit(resume_text=resume_text, jd_text=jd_text)
    workflow = CareerFitWorkflowResult(
        report=report,
        prompt_result=PromptHarnessResult(strategies=[], best_strategy_name=""),
        steps=["analyze_career_fit"],
    )

    # When: a reusable career profile is derived for memory.
    profile = summarize_workflow_for_memory(workflow)

    # Then: it stores only high-signal career fields, never the raw source texts.
    assert profile.target_role_title == "AI Product Analyst"
    assert profile.target_role_family == "product"
    assert profile.confirmed_skills == [
        "dashboard",
        "llm",
        "product",
        "prompt engineering",
        "python",
        "sql",
        "stakeholder",
        "streamlit",
    ]
    assert profile.recurring_missing_keywords == [
        "ai",
        "dashboard storytelling",
        "data analysis",
    ]
    assert profile.preferred_output_language == "en"
    assert profile.last_match_score == 62
    serialized_profile = profile.model_dump_json()
    assert resume_text not in serialized_profile
    assert jd_text not in serialized_profile


def test_redact_memory_unsafe_text_removes_contacts_secrets_and_local_paths() -> None:
    # Given: text that includes contact details, a secret, and local path fragments.
    unsafe_text = (
        "Candidate jane@example.com +852 5555 1234 token=private-value "
        "C:\\Users\\Jane\\resume.pdf /home/jane/private.txt"
    )

    # When: the text crosses the career-memory boundary.
    redacted_text = redact_memory_unsafe_text(unsafe_text)

    # Then: none of the unsafe fragments remain available for persistence.
    assert "jane@example.com" not in redacted_text
    assert "+852 5555 1234" not in redacted_text
    assert "private-value" not in redacted_text
    assert "C:\\Users\\Jane" not in redacted_text
    assert "/home/jane" not in redacted_text
