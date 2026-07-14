from career_ai.agent.memory import redact_memory_unsafe_text
from career_ai.agent.tool_models import SaveMemorySummaryInput


def redact_memory_summary(summary: SaveMemorySummaryInput) -> SaveMemorySummaryInput:
    """Remove sensitive fragments from allowed memory fields."""
    return SaveMemorySummaryInput(
        role_title=redact_memory_unsafe_text(summary.role_title),
        match_score=summary.match_score,
        missing_keywords=[
            redact_memory_unsafe_text(keyword) for keyword in summary.missing_keywords
        ],
    )
