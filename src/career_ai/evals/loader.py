from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import override

from career_ai.evals.models import CareerEvalCase


@unique
class EvalCaseLoadReason(StrEnum):
    """Reasons an eval case directory cannot be loaded."""

    EMPTY = "empty"
    MISSING = "missing"
    NOT_DIRECTORY = "not_directory"


@dataclass(frozen=True, slots=True)
class EvalCaseLoadError(Exception):
    """Raised when an eval case directory cannot produce a runnable suite."""

    directory: Path
    reason: EvalCaseLoadReason

    @override
    def __str__(self) -> str:
        """Return a user-facing load failure message."""
        match self.reason:
            case EvalCaseLoadReason.MISSING:
                return f"Eval case directory does not exist: {self.directory}"
            case EvalCaseLoadReason.NOT_DIRECTORY:
                return f"Eval case path is not a directory: {self.directory}"
            case EvalCaseLoadReason.EMPTY:
                return f"No eval case JSON files found in: {self.directory}"


def load_eval_case(path: Path) -> CareerEvalCase:
    """Load and validate one JSON eval case from disk."""
    return CareerEvalCase.model_validate_json(path.read_text(encoding="utf-8"))


def load_eval_cases(directory: Path) -> list[CareerEvalCase]:
    """Load JSON eval cases from a directory in deterministic filename order."""
    if not directory.exists():
        raise EvalCaseLoadError(directory=directory, reason=EvalCaseLoadReason.MISSING)
    if not directory.is_dir():
        raise EvalCaseLoadError(
            directory=directory,
            reason=EvalCaseLoadReason.NOT_DIRECTORY,
        )
    case_paths = sorted(directory.glob("*.json"))
    if not case_paths:
        raise EvalCaseLoadError(directory=directory, reason=EvalCaseLoadReason.EMPTY)
    return [load_eval_case(path) for path in case_paths]
