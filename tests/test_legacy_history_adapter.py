from hashlib import sha256
from pathlib import Path

from career_ai.legacy_history import load_legacy_history


def test_load_legacy_history_labels_records_without_v2_provenance(
    tmp_path: Path,
) -> None:
    # Given a valid summary-only history file from the legacy application.
    history_path = tmp_path / ".career_ai" / "history.json"
    history_path.parent.mkdir(parents=True)
    _ = history_path.write_text(
        """
        [{
          "created_at": "2026-07-09T10:00:00+08:00",
          "role_title": "Legacy Role",
          "match_score": 64,
          "missing_keywords": ["sql"],
          "resume_preview": "resume",
          "jd_preview": "jd"
        }]
        """,
        encoding="utf-8",
    )

    # When the compatibility adapter reads the file.
    records = load_legacy_history(history_path)

    # Then the record is explicitly legacy and has no invented v2 metadata.
    assert len(records) == 1
    assert records[0].record_kind == "legacy"
    assert records[0].role_title == "Legacy Role"
    serialized = records[0].model_dump(mode="json")
    assert "run_id" not in serialized
    assert "provenance" not in serialized
    assert "latex" not in serialized
    assert "render_manifest" not in serialized


def test_load_legacy_history_does_not_modify_source_bytes(tmp_path: Path) -> None:
    # Given a valid legacy history file and its content identity.
    history_path = tmp_path / "history.json"
    _ = history_path.write_text("[]\n", encoding="utf-8")
    before = sha256(history_path.read_bytes()).hexdigest()

    # When the compatibility adapter reads it.
    _ = load_legacy_history(history_path)

    # Then its byte identity is unchanged.
    assert sha256(history_path.read_bytes()).hexdigest() == before


def test_load_legacy_history_returns_empty_for_missing_file(tmp_path: Path) -> None:
    # Given a path that has never existed.
    history_path = tmp_path / "history.json"

    # When it is read through the compatibility adapter.
    records = load_legacy_history(history_path)

    # Then the legacy view is empty and no file is created.
    assert records == []
    assert not history_path.exists()


def test_load_legacy_history_returns_empty_for_malformed_file(tmp_path: Path) -> None:
    # Given malformed local compatibility data.
    history_path = tmp_path / "history.json"
    _ = history_path.write_text("{not-json", encoding="utf-8")
    before = history_path.read_bytes()

    # When it is read through the compatibility adapter.
    records = load_legacy_history(history_path)

    # Then malformed state is ignored without attempting a repair write.
    assert records == []
    assert history_path.read_bytes() == before


def test_load_legacy_history_returns_empty_for_invalid_utf8(tmp_path: Path) -> None:
    # Given bytes that cannot be decoded as the legacy UTF-8 contract.
    history_path = tmp_path / "history.json"
    _ = history_path.write_bytes(b"[\xff]")
    before = history_path.read_bytes()

    # When it is read through the compatibility adapter.
    records = load_legacy_history(history_path)

    # Then unreadable state is ignored without attempting a repair write.
    assert records == []
    assert history_path.read_bytes() == before
