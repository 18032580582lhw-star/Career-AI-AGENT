"""LaTeX source output for host-run rendering."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - renderer writes concrete paths.

from career_ai.rendering.latex import (
    find_unsafe_latex_commands,
    patch_user_latex_template,
    render_latex_body,
    render_system_latex,
)
from career_ai.rendering.latex.user_template import inspect_user_latex_template
from career_ai.tailoring.document_contracts import AcceptedResumeDocument  # noqa: TC001
from career_ai.tailoring.host_run_models import HostRunError, HostRunRequest
from career_ai.tailoring.host_run_persistence import output_artifact
from career_ai.tailoring.manifest_contracts import OutputArtifact, TemplateType


def write_latex_source(
    request: HostRunRequest,
    accepted: AcceptedResumeDocument,
    output_dir: Path,
) -> OutputArtifact:
    """Write bound system or user-template LaTeX source."""
    tex_path = output_dir / "resume.tex"
    if request.template_type is TemplateType.SYSTEM or request.template_source is None:
        tex = render_system_latex(accepted)
    elif "@@RESUME_BODY@@" in request.template_source:
        tex = request.template_source.replace("@@RESUME_BODY@@", render_latex_body(accepted))
    else:
        profile = inspect_user_latex_template(request.template_source)
        tex = patch_user_latex_template(
            source=request.template_source,
            profile=profile,
            document=accepted,
        )
    if find_unsafe_latex_commands(tex):
        message = "rendered LaTeX contains unsafe commands"
        raise HostRunError(message)
    _ = tex_path.write_text(tex, encoding="utf-8")
    return output_artifact(tex_path, "resume.tex", "application/x-tex")
