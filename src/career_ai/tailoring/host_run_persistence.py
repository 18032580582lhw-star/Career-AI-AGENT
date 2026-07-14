"""Persistence helpers for host-proposal run artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from pydantic import TypeAdapter

from career_ai.tailoring.contract_base import canonical_json_hash
from career_ai.tailoring.document_contracts import StructuredResumeTailoringProposal
from career_ai.tailoring.generation_models import TailoringGenerationContext
from career_ai.tailoring.host_run_models import HostRunRequest
from career_ai.tailoring.manifest_contracts import OutputArtifact
from career_ai.tailoring.models import CandidateFact
from career_ai.tailoring.proposal_contracts import ResumeTailoringProposal
from career_ai.tailoring.state_machine import ValidationStateResult
from career_ai.workspace import resolve_workspace_path

RUNS_DIR = Path(".career_ai/runs")
REQUEST_FILE = "request.json"
CONTEXT_FILE = "context.json"
PROPOSAL_FILE = "proposal.json"
VALIDATION_FILE = "validation.json"
DRAFT_FILE = "draft.json"
FACTS_FILE = "candidate-facts.json"
RUN_MANIFEST_FILE = "run-manifest.json"
RENDER_DIR = "rendered"
_CANDIDATE_FACTS_ADAPTER: TypeAdapter[tuple[CandidateFact, ...]] = TypeAdapter(
    tuple[CandidateFact, ...],
)


def load_run_context(workspace: Path, run_id: str) -> TailoringGenerationContext:
    """Load the trusted generation context for a prepared run."""
    return TailoringGenerationContext.model_validate_json(
        run_path(workspace, run_id, CONTEXT_FILE).read_text(encoding="utf-8-sig"),
    )


def load_request(workspace: Path, run_id: str) -> HostRunRequest:
    """Load a prepared host-run request."""
    return HostRunRequest.model_validate_json(
        run_path(workspace, run_id, REQUEST_FILE).read_text(encoding="utf-8-sig"),
    )


def load_proposal(workspace: Path, run_id: str) -> ResumeTailoringProposal:
    """Load a generic proposal for validation-only workflows."""
    return ResumeTailoringProposal.model_validate_json(
        run_path(workspace, run_id, PROPOSAL_FILE).read_text(encoding="utf-8-sig"),
    )


def load_structured_proposal(
    workspace: Path,
    run_id: str,
) -> StructuredResumeTailoringProposal:
    """Load a render-ready structured proposal."""
    return StructuredResumeTailoringProposal.model_validate_json(
        run_path(workspace, run_id, PROPOSAL_FILE).read_text(encoding="utf-8-sig"),
    )


def load_validation(workspace: Path, run_id: str) -> ValidationStateResult:
    """Load a persisted validation decision."""
    return ValidationStateResult.model_validate_json(
        run_path(workspace, run_id, VALIDATION_FILE).read_text(encoding="utf-8-sig"),
    )


def load_candidate_facts(workspace: Path, run_id: str) -> tuple[CandidateFact, ...]:
    """Load persisted candidate facts."""
    return _CANDIDATE_FACTS_ADAPTER.validate_json(
        run_path(workspace, run_id, FACTS_FILE).read_text(encoding="utf-8-sig"),
    )


def write_candidate_facts(path: Path, facts: tuple[CandidateFact, ...]) -> None:
    """Serialize candidate facts for a run."""
    encoded = _CANDIDATE_FACTS_ADAPTER.dump_json(facts).decode("utf-8")
    _ = path.write_text(encoded, encoding="utf-8")


def ensure_run_dir(workspace: Path, run_id: str) -> Path:
    """Create and return the run directory inside a workspace."""
    run_dir = resolve_workspace_path(workspace, RUNS_DIR / run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def run_path(workspace: Path, run_id: str, filename: str) -> Path:
    """Resolve one run-local artifact path."""
    return resolve_workspace_path(workspace, RUNS_DIR / run_id / filename)


def artifact_name(run_id: str, filename: str) -> str:
    """Return a portable run artifact name for CLI output."""
    return f".career_ai/runs/{run_id}/{filename}"


def new_run_id() -> str:
    """Create a run id accepted by the protocol contract."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"run-{timestamp}-{uuid4().hex[:8]}"


def read_text(path: Path) -> str:
    """Read UTF-8 text at a trust boundary."""
    return path.read_text(encoding="utf-8-sig")


def hash_text(text: str) -> str:
    """Hash text exactly as UTF-8 source material."""
    return sha256(text.encode("utf-8")).hexdigest()


def request_hash(request: HostRunRequest) -> str:
    """Hash one request artifact canonically."""
    return canonical_json_hash(request.model_dump(mode="json"))


def output_artifact(path: Path, relative_path: str, media_type: str) -> OutputArtifact:
    """Build output metadata from a rendered file."""
    return OutputArtifact(
        path=relative_path,
        sha256=sha256(path.read_bytes()).hexdigest(),
        media_type=media_type,
    )
