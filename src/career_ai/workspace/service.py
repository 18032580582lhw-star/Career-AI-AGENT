from pathlib import Path
from typing import Final

from pydantic import ValidationError

from career_ai.workspace.errors import (
    WorkspaceManifestError,
    WorkspaceNotFoundError,
    WorkspaceSchemaVersionError,
)
from career_ai.workspace.models import (
    WORKSPACE_SCHEMA_VERSION,
    ManifestVersionEnvelope,
    WorkspaceManifest,
)
from career_ai.workspace.paths import resolve_workspace_path
from career_ai.workspace.storage import write_json_atomic

MANIFEST_RELATIVE_PATH: Final = Path(".career_ai/manifest.json")


def create_workspace(root: Path) -> WorkspaceManifest:
    """Create a workspace once, preserving an existing valid manifest and history."""
    resolved_root = root.resolve(strict=False)
    resolved_root.mkdir(parents=True, exist_ok=True)
    manifest_path = resolve_workspace_path(resolved_root, MANIFEST_RELATIVE_PATH)
    if manifest_path.exists():
        manifest = load_workspace(resolved_root)
    else:
        manifest = WorkspaceManifest()
        write_json_atomic(manifest_path, manifest)
    for relative_path in (
        manifest.paths.sources,
        manifest.paths.tasks,
        manifest.paths.artifacts,
    ):
        resolve_workspace_path(resolved_root, relative_path).mkdir(parents=True, exist_ok=True)
    return manifest


def load_workspace(root: Path) -> WorkspaceManifest:
    """Parse and validate the workspace manifest at an untrusted file boundary."""
    resolved_root = root.resolve(strict=False)
    manifest_path = resolve_workspace_path(resolved_root, MANIFEST_RELATIVE_PATH)
    if not manifest_path.is_file():
        raise WorkspaceNotFoundError(root=resolved_root)
    try:
        payload = manifest_path.read_text(encoding="utf-8")
        envelope = ManifestVersionEnvelope.model_validate_json(payload)
    except (OSError, ValidationError) as exc:
        raise WorkspaceManifestError(path=manifest_path, reason=str(exc)) from exc
    if envelope.schema_version != WORKSPACE_SCHEMA_VERSION:
        raise WorkspaceSchemaVersionError(
            path=manifest_path,
            actual=envelope.schema_version,
            supported=WORKSPACE_SCHEMA_VERSION,
        )
    try:
        return WorkspaceManifest.model_validate_json(payload)
    except ValidationError as exc:
        raise WorkspaceManifestError(path=manifest_path, reason=str(exc)) from exc


def validate_workspace(root: Path) -> WorkspaceManifest:
    """Validate the schema and containment of every configured workspace path."""
    manifest = load_workspace(root)
    for relative_path in (
        manifest.paths.sources,
        manifest.paths.tasks,
        manifest.paths.artifacts,
    ):
        _ = resolve_workspace_path(root, relative_path)
    return manifest
