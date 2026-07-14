import json
import shutil
from pathlib import Path
from typing import Final

import pytest
from pydantic import JsonValue, TypeAdapter

from career_ai.workspace import (
    WORKSPACE_SCHEMA_VERSION,
    WorkspaceManifest,
    WorkspaceManifestError,
    WorkspacePathError,
    WorkspaceSchemaVersionError,
    create_workspace,
    load_workspace,
    resolve_workspace_path,
    validate_workspace,
    write_json_atomic,
)

HISTORY_JSON_ADAPTER: Final = TypeAdapter(list[JsonValue])


def test_legacy_history_fixture_remains_readable_and_byte_identical(tmp_path: Path) -> None:
    # Given the repository's current legacy history copied into an isolated workspace.
    repository_history = Path(__file__).parents[1] / ".career_ai" / "history.json"
    workspace_history = tmp_path / ".career_ai" / "history.json"
    workspace_history.parent.mkdir(parents=True)
    _ = shutil.copyfile(repository_history, workspace_history)
    original_bytes = workspace_history.read_bytes()

    # When the legacy JSON is read without workspace migration.
    parsed_history = HISTORY_JSON_ADAPTER.validate_json(
        workspace_history.read_text(encoding="utf-8"),
    )

    # Then it remains readable and has not been rewritten.
    assert parsed_history
    assert workspace_history.read_bytes() == original_bytes


def test_workspace_module_exposes_versioned_manifest_contract() -> None:
    # Given the versioned workspace contract.
    # When its current manifest is constructed.
    manifest = WorkspaceManifest()

    # Then schema version 1 is explicit and stable.
    assert WORKSPACE_SCHEMA_VERSION == 1
    assert manifest.schema_version == 1


def test_create_workspace_is_idempotent_and_preserves_legacy_history(tmp_path: Path) -> None:
    # Given a workspace containing legacy compatibility history.
    history_path = tmp_path / ".career_ai" / "history.json"
    history_path.parent.mkdir(parents=True)
    _ = history_path.write_text('[{"role_title":"Legacy"}]\n', encoding="utf-8")
    original_history = history_path.read_bytes()

    # When initialization is invoked twice.
    first = create_workspace(tmp_path)
    manifest_path = tmp_path / ".career_ai" / "manifest.json"
    original_manifest = manifest_path.read_bytes()
    second = create_workspace(tmp_path)

    # Then the manifest is stable and legacy history is untouched.
    assert first == second == WorkspaceManifest()
    assert manifest_path.read_bytes() == original_manifest
    assert history_path.read_bytes() == original_history


def test_load_workspace_rejects_malformed_manifest(tmp_path: Path) -> None:
    # Given malformed JSON at the manifest boundary.
    manifest_path = tmp_path / ".career_ai" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    _ = manifest_path.write_text('{"schema_version":', encoding="utf-8")

    # When the workspace is loaded, then the corruption is reported explicitly.
    with pytest.raises(WorkspaceManifestError):
        _ = load_workspace(tmp_path)


def test_load_workspace_rejects_stale_schema(tmp_path: Path) -> None:
    # Given a well-formed manifest from an unsupported schema.
    manifest_path = tmp_path / ".career_ai" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    _ = manifest_path.write_text('{"schema_version":0,"paths":{}}', encoding="utf-8")

    # When the workspace is loaded, then callers receive the typed version error.
    with pytest.raises(WorkspaceSchemaVersionError) as captured:
        _ = load_workspace(tmp_path)
    assert captured.value.actual == 0
    assert captured.value.supported == 1


@pytest.mark.parametrize("unsafe_path", ["../outside.json", "nested/../../outside.json"])
def test_resolve_workspace_path_rejects_traversal(tmp_path: Path, unsafe_path: str) -> None:
    # Given a caller-controlled path that leaves the workspace.
    # When it is resolved, then containment enforcement rejects it.
    with pytest.raises(WorkspacePathError):
        _ = resolve_workspace_path(tmp_path, unsafe_path)


def test_manifest_rejects_traversal_in_configured_paths(tmp_path: Path) -> None:
    # Given a manifest that attempts to redirect sources outside the workspace.
    manifest_path = tmp_path / ".career_ai" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    _ = manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "paths": {
                    "sources": "../escape",
                    "tasks": "tasks",
                    "artifacts": "artifacts",
                },
            },
        ),
        encoding="utf-8",
    )

    # When it is validated, then unsafe persisted configuration is rejected.
    with pytest.raises(WorkspaceManifestError):
        _ = validate_workspace(tmp_path)


def test_stale_partial_temp_file_does_not_replace_manifest(tmp_path: Path) -> None:
    # Given a valid manifest and debris from an interrupted prior write.
    expected = create_workspace(tmp_path)
    stale_temp = tmp_path / ".career_ai" / ".manifest.json.interrupted.tmp"
    _ = stale_temp.write_text('{"schema_version":', encoding="utf-8")

    # When the exact manifest path is loaded.
    loaded = load_workspace(tmp_path)

    # Then only the committed manifest is authoritative.
    assert loaded == expected
    assert stale_temp.exists()


def test_atomic_json_write_replaces_complete_document(tmp_path: Path) -> None:
    # Given an existing invalid target document.
    target = tmp_path / "manifest.json"
    _ = target.write_text("partial", encoding="utf-8")

    # When a validated manifest is atomically written.
    write_json_atomic(target, WorkspaceManifest())

    # Then readers observe one complete parseable document.
    loaded = WorkspaceManifest.model_validate_json(target.read_text(encoding="utf-8"))
    assert loaded.schema_version == 1
