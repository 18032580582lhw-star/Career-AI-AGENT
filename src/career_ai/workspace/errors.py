from dataclasses import dataclass
from pathlib import Path
from typing import override


class WorkspaceError(Exception):
    """Base class for workspace boundary failures."""


@dataclass(frozen=True, slots=True)
class WorkspaceNotFoundError(WorkspaceError):
    """Report a root that has not been initialized."""

    root: Path

    @override
    def __str__(self) -> str:
        return f"workspace manifest not found under {self.root}"


@dataclass(frozen=True, slots=True)
class WorkspaceManifestError(WorkspaceError):
    """Report malformed or structurally invalid manifest data."""

    path: Path
    reason: str

    @override
    def __str__(self) -> str:
        return f"invalid workspace manifest {self.path}: {self.reason}"


@dataclass(frozen=True, slots=True)
class WorkspaceSchemaVersionError(WorkspaceError):
    """Report a manifest schema that this runtime cannot load."""

    path: Path
    actual: int
    supported: int

    @override
    def __str__(self) -> str:
        return (
            f"workspace manifest {self.path} uses schema {self.actual}; "
            f"supported schema is {self.supported}"
        )


@dataclass(frozen=True, slots=True)
class WorkspacePathError(WorkspaceError):
    """Report a path that is not contained by its workspace root."""

    root: Path
    requested: Path

    @override
    def __str__(self) -> str:
        return f"workspace path {self.requested} escapes root {self.root}"


@dataclass(frozen=True, slots=True)
class WorkspaceWriteError(WorkspaceError):
    """Report an operating-system failure during an atomic write."""

    path: Path
    reason: str

    @override
    def __str__(self) -> str:
        return f"could not atomically write {self.path}: {self.reason}"
