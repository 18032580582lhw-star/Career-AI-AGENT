"""Shared tailoring application service used by CLI, Skills, and Streamlit."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from career_ai.llm.client import build_llm_client
from career_ai.llm.settings import LLMSettings
from career_ai.rendering.latex import inspect_user_latex_template
from career_ai.tailoring.host_run_persistence import (
    RUN_MANIFEST_FILE,
    RUNS_DIR,
    load_request,
    read_text,
    run_path,
)
from career_ai.tailoring.host_run_store import (
    confirm_host_fact,
    prepare_host_run,
    render_host_run,
    tailor_with_api,
    validate_host_draft,
)
from career_ai.tailoring.manifest_contracts import RenderManifest, RunManifest
from career_ai.workspace import create_workspace, resolve_workspace_path

if TYPE_CHECKING:
    from pathlib import Path

    from career_ai.llm.client import LLMClient
    from career_ai.rendering.latex import LatexTemplateProfile
    from career_ai.tailoring.host_run_models import (
        HostPrepareResult,
        HostRenderFormat,
        HostRenderResult,
        HostValidationResult,
    )

RENDER_MANIFESTS_ADAPTER: TypeAdapter[tuple[RenderManifest, ...]] = TypeAdapter(
    tuple[RenderManifest, ...],
)


class WorkspaceRunSummary(RunManifest):
    """Replay-ready run summary with optional render provenance."""

    template_type: str | None = None
    render_manifests: tuple[RenderManifest, ...] = ()


class TailoringApplicationService:
    """Coordinate one workspace through the canonical tailoring workflow."""

    def __init__(self, *, workspace: Path, llm_client: LLMClient | None = None) -> None:
        """Create a service bound to one workspace root."""
        self._workspace: Path = workspace
        self._llm_client: LLMClient | None = llm_client

    @property
    def workspace(self) -> Path:
        """Return the service workspace root."""
        return self._workspace

    def initialize(self) -> None:
        """Create the workspace manifest and owned directories."""
        _ = create_workspace(self._workspace)

    def prepare(
        self,
        *,
        resume_file: Path,
        jd_file: Path,
        latex_template: Path | None = None,
        language: str = "en",
    ) -> HostPrepareResult:
        """Prepare immutable sources and return the host proposal package."""
        return prepare_host_run(
            workspace=self._workspace,
            resume_file=resume_file,
            jd_file=jd_file,
            latex_template=latex_template,
            language=language,
        )

    def validate(self, *, run_id: str, proposal_file: Path) -> HostValidationResult:
        """Validate a host-authored proposal through the local harnesses."""
        return validate_host_draft(
            workspace=self._workspace,
            run_id=run_id,
            proposal_file=proposal_file,
        )

    def confirm(self, *, run_id: str, confirmation_file: Path) -> HostValidationResult:
        """Apply one explicit confirmation response and rerun validation."""
        return confirm_host_fact(
            workspace=self._workspace,
            run_id=run_id,
            confirmation_file=confirmation_file,
        )

    def tailor_with_api(self, *, run_id: str) -> HostValidationResult:
        """Request provider proposals, then validate locally."""
        return tailor_with_api(
            workspace=self._workspace,
            run_id=run_id,
            client=self._resolved_llm_client(),
        )

    def render(
        self,
        *,
        run_id: str,
        render_format: HostRenderFormat,
        disable_latex_engines: bool = False,
    ) -> HostRenderResult:
        """Render an accepted current run through shared renderer services."""
        return render_host_run(
            workspace=self._workspace,
            run_id=run_id,
            render_format=render_format,
            disable_latex_engines=disable_latex_engines,
        )

    def inspect_latex_template(self, template_file: Path) -> LatexTemplateProfile:
        """Inspect a user-owned LaTeX template without modifying it."""
        return inspect_user_latex_template(read_text(template_file))

    def list_workspace_runs(self) -> tuple[WorkspaceRunSummary, ...]:
        """Read workspace run manifests newest-first; invalid partial runs are skipped."""
        runs_root = resolve_workspace_path(self._workspace, RUNS_DIR)
        if not runs_root.exists():
            return ()
        summaries: list[WorkspaceRunSummary] = []
        for manifest_path in sorted(runs_root.glob(f"*/{RUN_MANIFEST_FILE}"), reverse=True):
            summary = self._load_run_summary(manifest_path)
            if summary is not None:
                summaries.append(summary)
        return tuple(summaries)

    def _load_run_summary(self, manifest_path: Path) -> WorkspaceRunSummary | None:
        try:
            manifest = RunManifest.model_validate_json(
                manifest_path.read_text(encoding="utf-8-sig"),
            )
            request = load_request(self._workspace, manifest.run_id)
        except (OSError, ValueError):
            return None
        render_manifests = self._load_render_manifests(manifest.run_id)
        payload = manifest.model_dump(mode="json")
        payload["template_type"] = request.template_type.value
        payload["render_manifests"] = RENDER_MANIFESTS_ADAPTER.dump_python(
            render_manifests,
            mode="json",
        )
        return WorkspaceRunSummary.model_validate(payload)

    def _load_render_manifests(self, run_id: str) -> tuple[RenderManifest, ...]:
        render_dir = run_path(self._workspace, run_id, "rendered")
        manifests: list[RenderManifest] = []
        for manifest_path in sorted(render_dir.glob("*.render-manifest.json")):
            try:
                manifests.append(
                    RenderManifest.model_validate_json(
                        manifest_path.read_text(encoding="utf-8-sig"),
                    ),
                )
            except (OSError, ValueError):
                continue
        return tuple(manifests)

    def _resolved_llm_client(self) -> LLMClient:
        if self._llm_client is not None:
            return self._llm_client
        return build_llm_client(LLMSettings())
