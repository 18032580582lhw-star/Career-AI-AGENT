from pathlib import Path

from career_ai.evals.models import CareerEvalCase


def load_eval_case(path: Path) -> CareerEvalCase:
    """Load and validate one JSON eval case from disk."""
    return CareerEvalCase.model_validate_json(path.read_text(encoding="utf-8"))


def load_eval_cases(directory: Path) -> list[CareerEvalCase]:
    """Load JSON eval cases from a directory in deterministic filename order."""
    return [load_eval_case(path) for path in sorted(directory.glob("*.json"))]
