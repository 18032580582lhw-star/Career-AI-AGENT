from pathlib import Path
from typing import ClassVar, Final, Literal

from pydantic import BaseModel, ConfigDict, field_validator

WORKSPACE_SCHEMA_VERSION: Final = 1


class WorkspacePaths(BaseModel):
    """Root-relative locations owned by a career workspace."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    sources: str = ".career_ai/sources"
    tasks: str = ".career_ai/tasks"
    artifacts: str = ".career_ai/artifacts"

    @field_validator("sources", "tasks", "artifacts")
    @classmethod
    def require_safe_relative_path(cls, value: str) -> str:
        """Reject absolute and parent-traversing persisted locations."""
        candidate = Path(value)
        if candidate.is_absolute() or not value.strip() or ".." in candidate.parts:
            msg = "workspace locations must be non-empty relative paths without '..'"
            raise ValueError(msg)
        return value


class WorkspaceManifest(BaseModel):
    """Versioned, immutable workspace configuration persisted as JSON."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1] = WORKSPACE_SCHEMA_VERSION
    paths: WorkspacePaths = WorkspacePaths()


class ManifestVersionEnvelope(BaseModel):
    """Minimal boundary model used to distinguish stale schemas."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore")

    schema_version: int
