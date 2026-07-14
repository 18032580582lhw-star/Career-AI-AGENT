import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from pydantic import Field, TypeAdapter, ValidationError

from career_ai.models import CareerFitReport, FrozenModel, PromptHarnessResult

DEFAULT_HISTORY_PATH: Final[Path] = Path(".career_ai") / "history.json"
MAX_HISTORY_ENTRIES: Final[int] = 12
PREVIEW_CHARS: Final[int] = 160

class HistoryEntry(FrozenModel):
    """Compact analysis history item safe for local persistence."""

    created_at: str
    role_title: str
    match_score: int
    missing_keywords: list[str] = Field(default_factory=list)
    resume_preview: str
    jd_preview: str
    report: CareerFitReport | None = None
    prompt_result: PromptHarnessResult | None = None


HISTORY_ADAPTER: Final[TypeAdapter[list[HistoryEntry]]] = TypeAdapter(
    list[HistoryEntry],
)


def build_history_entry(
    report: CareerFitReport,
    prompt_result: PromptHarnessResult,
    resume_text: str,
    jd_text: str,
    created_at: str | None = None,
) -> HistoryEntry:
    """Build a privacy-preserving history entry from an analysis result."""
    timestamp = created_at or datetime.now(UTC).astimezone().isoformat(timespec="seconds")
    return HistoryEntry(
        created_at=timestamp,
        role_title=report.jd_analysis.role_title,
        match_score=report.match.score,
        missing_keywords=report.match.missing_keywords[:4],
        resume_preview=_preview(resume_text),
        jd_preview=_preview(jd_text),
        report=report,
        prompt_result=prompt_result,
    )


def load_history(path: Path = DEFAULT_HISTORY_PATH) -> list[HistoryEntry]:
    """Load saved analysis history, returning an empty list for invalid local state."""
    if not path.exists():
        return []
    raw_history = path.read_text(encoding="utf-8").strip()
    if not raw_history:
        return []
    try:
        return HISTORY_ADAPTER.validate_json(raw_history)
    except ValidationError:
        return []


def append_history_entry(
    entry: HistoryEntry,
    path: Path = DEFAULT_HISTORY_PATH,
    limit: int = MAX_HISTORY_ENTRIES,
) -> list[HistoryEntry]:
    """Persist a new entry first and return the capped history list."""
    entries = [entry, *load_history(path)][:limit]
    save_history(entries, path)
    return entries


def save_history(entries: list[HistoryEntry], path: Path = DEFAULT_HISTORY_PATH) -> None:
    """Write typed history entries as UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [entry.model_dump(mode="json") for entry in entries]
    _ = path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _preview(text: str, limit: int = PREVIEW_CHARS) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 3].rstrip()}..."
