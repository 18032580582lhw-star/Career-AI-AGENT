from pathlib import Path

from career_ai.history import (
    HistoryEntry,
    append_history_entry,
    build_history_entry,
    load_history,
)
from career_ai.models import (
    CareerFitReport,
    JDAnalysis,
    PromptHarnessResult,
    PromptStrategyScore,
    ResumeMatch,
    SkillGap,
)


def test_load_history_returns_empty_list_when_file_is_missing(tmp_path: Path) -> None:
    # Given a history path that has not been created.
    history_path = tmp_path / "history.json"

    # When history is loaded.
    entries = load_history(history_path)

    # Then the app starts with no saved history.
    assert entries == []


def test_build_history_entry_uses_report_metadata_without_full_text() -> None:
    # Given a completed report and long source texts.
    report = _report()
    resume_text = "Resume " + ("private resume details " * 20)
    jd_text = "JD " + ("confidential job details " * 20)

    # When a history entry is built.
    entry = build_history_entry(
        report=report,
        prompt_result=_prompt_result(),
        resume_text=resume_text,
        jd_text=jd_text,
        created_at="2026-07-09T12:30:00+08:00",
    )

    # Then only compact metadata and previews are persisted.
    assert entry.created_at == "2026-07-09T12:30:00+08:00"
    assert entry.role_title == "AI Product Analyst"
    assert entry.match_score == 73
    assert entry.missing_keywords == ["stakeholder communication", "llm evaluation"]
    assert len(entry.resume_preview) < len(resume_text)
    assert len(entry.jd_preview) < len(jd_text)
    assert entry.resume_preview.endswith("...")
    assert entry.jd_preview.endswith("...")
    assert entry.report == report
    assert entry.prompt_result == _prompt_result()


def test_append_history_entry_prepends_newest_and_caps_entries(tmp_path: Path) -> None:
    # Given an existing history file with one entry.
    history_path = tmp_path / ".career_ai" / "history.json"
    older = HistoryEntry(
        created_at="2026-07-08T10:00:00+08:00",
        role_title="Older Role",
        match_score=50,
        missing_keywords=[],
        resume_preview="old resume",
        jd_preview="old jd",
    )
    newest = HistoryEntry(
        created_at="2026-07-09T10:00:00+08:00",
        role_title="Newest Role",
        match_score=90,
        missing_keywords=["sql"],
        resume_preview="new resume",
        jd_preview="new jd",
    )
    _ = append_history_entry(older, history_path, limit=2)

    # When a newer entry is appended.
    entries = append_history_entry(newest, history_path, limit=1)

    # Then newest entries are shown first and the stored list is capped.
    assert entries == [newest]
    assert load_history(history_path) == [newest]


def test_load_history_keeps_legacy_summary_entries_without_replay_data(tmp_path: Path) -> None:
    # Given a history file from the summary-only version.
    history_path = tmp_path / "history.json"
    _ = history_path.write_text(
        """
        [
          {
            "created_at": "2026-07-09T10:00:00+08:00",
            "role_title": "Legacy Role",
            "match_score": 64,
            "missing_keywords": ["sql"],
            "resume_preview": "resume",
            "jd_preview": "jd"
          }
        ]
        """,
        encoding="utf-8",
    )

    # When history is loaded.
    entries = load_history(history_path)

    # Then legacy entries remain visible but are not replayable.
    assert len(entries) == 1
    assert entries[0].role_title == "Legacy Role"
    assert entries[0].report is None
    assert entries[0].prompt_result is None


def _report() -> CareerFitReport:
    return CareerFitReport(
        jd_analysis=JDAnalysis(
            role_title="AI Product Analyst",
            seniority="Mid-level",
            requirements=["Python", "SQL"],
            keywords=["python", "sql"],
        ),
        match=ResumeMatch(
            score=73,
            matched_keywords=["python", "sql"],
            missing_keywords=["stakeholder communication", "llm evaluation"],
            summary="Good match with focused gaps.",
        ),
        skill_gap=SkillGap(
            missing_skills=["stakeholder communication", "llm evaluation"],
            priority_skills=["stakeholder communication"],
            notes=[],
        ),
        bullet_suggestions=[],
        cover_letter_draft="Draft",
        rewritten_resume="Resume",
    )


def _prompt_result() -> PromptHarnessResult:
    return PromptHarnessResult(
        strategies=[
            PromptStrategyScore(
                name="baseline",
                score=80,
                strengths=["Simple"],
                risks=["Less structured"],
            ),
        ],
        best_strategy_name="baseline",
    )
