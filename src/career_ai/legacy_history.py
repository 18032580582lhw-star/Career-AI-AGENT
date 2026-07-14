from pathlib import Path
from typing import Final, Literal

from pydantic import TypeAdapter, ValidationError

from career_ai.history import DEFAULT_HISTORY_PATH, HistoryEntry


class LegacyHistoryRecord(HistoryEntry):
    """Read-only compatibility view of one pre-workspace history entry."""

    record_kind: Literal["legacy"] = "legacy"


LEGACY_HISTORY_ADAPTER: Final[TypeAdapter[list[LegacyHistoryRecord]]] = TypeAdapter(
    list[LegacyHistoryRecord],
)


def load_legacy_history(
    path: Path = DEFAULT_HISTORY_PATH,
) -> list[LegacyHistoryRecord]:
    """Read legacy history without migrating, repairing, or rewriting its source."""
    if not path.exists():
        return []
    try:
        raw_history = path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError:
        return []
    if not raw_history:
        return []
    try:
        return LEGACY_HISTORY_ADAPTER.validate_json(raw_history)
    except ValidationError:
        return []
