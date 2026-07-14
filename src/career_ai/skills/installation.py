"""Idempotent installation for the packaged resume-tailoring host skill."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Final, Literal, assert_never

from pydantic import Field

from career_ai.models import FrozenModel
from career_ai.workspace import create_workspace, write_json_atomic

SKILL_NAME: Final = "career-resume-tailor"
INSTALL_RECORD: Final = Path(".career_ai") / "skill-installations.json"


@unique
class HostAgent(StrEnum):
    """Supported host adapters for the canonical skill."""

    CODEX = "codex"
    CLAUDE = "claude"
    OPENCODE = "opencode"
    ALL = "all"


class SkillPackageResources(FrozenModel):
    """Resource classes shipped with the installable package."""

    skill: tuple[str, ...]
    prompts: tuple[str, ...]
    schemas: tuple[str, ...]
    html_css: tuple[str, ...]
    latex_templates: tuple[str, ...]
    fonts: tuple[str, ...]
    licenses: tuple[str, ...]


class HostSkillInstallation(FrozenModel):
    """One host-specific installation result."""

    agent: HostAgent
    protocol: Annotated[str, Field(pattern=r"^(openai-agents|claude-plugin)$")]
    template: str
    target: str
    status: Literal["installed", "present", "exists-different"]
    installed_hash: str | None = None


class SkillInstallationResult(FrozenModel):
    """Machine-readable init result for workspace and host Skill setup."""

    workspace: str
    package: str
    skill_name: str
    skill_hash: str
    package_resources: SkillPackageResources
    installations: tuple[HostSkillInstallation, ...]


@dataclass(frozen=True, slots=True)
class _InstallTarget:
    agent: HostAgent
    protocol: str
    template: str
    path: Path


def canonical_skill_root() -> Path:
    """Return the packaged canonical Skill directory."""
    return Path(__file__).parent / "career_resume_tailor"


def canonical_skill_digest() -> str:
    """Hash all canonical skill files in stable relative-path order."""
    digest = sha256()
    root = canonical_skill_root()
    for file_path in _canonical_skill_files():
        relative = file_path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def install_host_skills(*, workspace: Path, agent: HostAgent) -> SkillInstallationResult:
    """Install host adapters without overwriting existing user-owned files."""
    manifest = create_workspace(workspace)
    del manifest
    root = workspace.resolve(strict=False)
    targets = _targets_for(root, agent)
    installations = tuple(_install_target(target) for target in targets)
    result = SkillInstallationResult(
        workspace=str(root),
        package="ai-career-intelligence-suite",
        skill_name=SKILL_NAME,
        skill_hash=canonical_skill_digest(),
        package_resources=_package_resources(),
        installations=installations,
    )
    write_json_atomic(root / INSTALL_RECORD, result)
    return result


def _targets_for(root: Path, agent: HostAgent) -> tuple[_InstallTarget, ...]:
    shared = root / ".agents" / "skills" / SKILL_NAME
    claude = root / ".claude" / "plugins" / SKILL_NAME
    match agent:
        case HostAgent.CODEX:
            return (_InstallTarget(agent, "openai-agents", "shared-skill", shared),)
        case HostAgent.OPENCODE:
            return (_InstallTarget(agent, "openai-agents", "shared-skill", shared),)
        case HostAgent.CLAUDE:
            return (_InstallTarget(agent, "claude-plugin", "claude-bundle", claude),)
        case HostAgent.ALL:
            return (
                _InstallTarget(HostAgent.CODEX, "openai-agents", "shared-skill", shared),
                _InstallTarget(HostAgent.OPENCODE, "openai-agents", "shared-skill", shared),
                _InstallTarget(HostAgent.CLAUDE, "claude-plugin", "claude-bundle", claude),
            )
        case _:
            assert_never(agent)


def _install_target(target: _InstallTarget) -> HostSkillInstallation:
    source_root = canonical_skill_root()
    target.path.mkdir(parents=True, exist_ok=True)
    statuses = tuple(
        _copy_file(file_path, source_root, target.path)
        for file_path in _canonical_skill_files()
    )
    installed_hash = _tree_digest(target.path)
    return HostSkillInstallation(
        agent=target.agent,
        protocol=target.protocol,
        template=target.template,
        target=str(target.path),
        status=_combined_status(statuses),
        installed_hash=installed_hash,
    )


def _copy_file(file_path: Path, source_root: Path, target_root: Path) -> str:
    relative = file_path.relative_to(source_root)
    destination = target_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        _ = destination.write_bytes(file_path.read_bytes())
        return "installed"
    if destination.read_bytes() == file_path.read_bytes():
        return "present"
    return "exists-different"


def _combined_status(
    statuses: tuple[str, ...],
) -> Literal["installed", "present", "exists-different"]:
    if "exists-different" in statuses:
        return "exists-different"
    if "installed" in statuses:
        return "installed"
    return "present"


def _tree_digest(root: Path) -> str:
    digest = sha256()
    for file_path in sorted(path for path in root.rglob("*") if path.is_file()):
        relative = file_path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _canonical_skill_files() -> tuple[Path, ...]:
    root = canonical_skill_root()
    return tuple(sorted(path for path in root.rglob("*") if path.is_file()))


def _package_resources() -> SkillPackageResources:
    return SkillPackageResources(
        skill=("SKILL.md", "references/workflow.md", "agents/openai.yaml"),
        prompts=("prompts/*.md",),
        schemas=("ResumeTailoringProposal.model_json_schema", "WorkspaceManifest.schema_version"),
        html_css=("static/app_theme.css", "career_ai.rendering.html_template"),
        latex_templates=("career_ai.rendering.latex/assets/system_resume.tex",),
        fonts=("career_ai.rendering/assets/fonts/NotoSans*",),
        licenses=("README.md",),
    )
