import os
import tempfile
from pathlib import Path

from pydantic import BaseModel

from career_ai.workspace.errors import WorkspaceWriteError


def write_json_atomic(path: Path, model: BaseModel) -> None:
    """Durably serialize a Pydantic model, then atomically replace its target."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            _ = temporary_file.write(f"{model.model_dump_json(indent=2)}\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        _ = temporary_path.replace(path)
    except OSError as exc:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise WorkspaceWriteError(path=path, reason=str(exc)) from exc
