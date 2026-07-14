from pathlib import Path

from career_ai.workspace.errors import WorkspacePathError


def resolve_workspace_path(root: Path, relative_path: str | Path) -> Path:
    """Resolve a path and prove it remains contained by the workspace root."""
    resolved_root = root.resolve(strict=False)
    requested = Path(relative_path)
    if requested.is_absolute():
        raise WorkspacePathError(root=resolved_root, requested=requested)
    resolved_candidate = (resolved_root / requested).resolve(strict=False)
    try:
        _ = resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise WorkspacePathError(root=resolved_root, requested=requested) from exc
    return resolved_candidate
