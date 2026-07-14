from importlib import resources
from pathlib import Path

from pydantic import TypeAdapter
from typer.testing import CliRunner

from career_ai.cli import app
from career_ai.skills.installation import (
    HostAgent,
    SkillInstallationResult,
    canonical_skill_digest,
    canonical_skill_root,
)

RESULT_ADAPTER = TypeAdapter(SkillInstallationResult)


def test_canonical_skill_documents_required_workflow_and_latex_policy() -> None:
    # Given: the packaged canonical host skill.
    skill_root = canonical_skill_root()
    skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    rendering_text = (skill_root / "references" / "rendering.md").read_text(encoding="utf-8")

    # When: the skill policy is inspected.
    required_terms = (
        "prepare",
        "host proposal",
        "validate",
        "confirm/repair",
        "render",
        "DOCX",
        "PDF",
        "Overleaf .tex",
        "resume.tex",
        "LaTeX PDF",
    )

    # Then: orchestration and LaTeX safety are explicit and host-neutral.
    assert (skill_root / "agents" / "openai.yaml").is_file()
    for term in required_terms:
        assert term in skill_text
    assert "Do not patch user source files" in rendering_text
    assert "Do not compile arbitrary .tex files" in rendering_text
    assert "Do not put raw LaTeX commands in proposals" in rendering_text


def test_init_agent_all_installs_three_hosts_and_records_skill_hash(tmp_path: Path) -> None:
    # Given: a fresh workspace.
    runner = CliRunner()

    # When: all host adapters are initialized twice.
    first = runner.invoke(app, ["init", "--workspace", str(tmp_path), "--agent", "all"])
    second = runner.invoke(app, ["init", "--workspace", str(tmp_path), "--agent", "all"])

    # Then: initialization is idempotent and records package/protocol/template/hash metadata.
    assert first.exit_code == 0
    assert second.exit_code == 0
    payload = RESULT_ADAPTER.validate_json(second.stdout)
    assert {item.agent for item in payload.installations} == {
        HostAgent.CLAUDE,
        HostAgent.CODEX,
        HostAgent.OPENCODE,
    }
    assert payload.skill_hash == canonical_skill_digest()
    assert payload.package_resources.skill
    assert payload.package_resources.prompts
    assert payload.package_resources.schemas
    assert payload.package_resources.html_css
    assert payload.package_resources.latex_templates
    assert payload.package_resources.fonts
    assert payload.package_resources.licenses
    assert (tmp_path / ".agents" / "skills" / "career-resume-tailor" / "SKILL.md").is_file()
    assert (tmp_path / ".claude" / "plugins" / "career-resume-tailor" / "SKILL.md").is_file()
    assert (tmp_path / ".career_ai" / "skill-installations.json").is_file()


def test_packaged_resources_are_importable_for_clean_install_smoke() -> None:
    # Given: package data expected by Skills and renderers.
    skill_files = resources.files("career_ai.skills")
    rendering_files = resources.files("career_ai.rendering")

    # When: resources are resolved through importlib instead of source-relative paths.
    skill_entrypoint = skill_files.joinpath("career_resume_tailor", "SKILL.md")
    system_template = rendering_files.joinpath("latex", "assets", "system_resume.tex")
    noto_font = rendering_files.joinpath("assets", "fonts", "NotoSans-Regular.woff2")

    # Then: clean wheel installs can find the same bundled assets.
    assert skill_entrypoint.is_file()
    assert system_template.is_file()
    assert noto_font.is_file()
    assert "career-resume-tailor" in skill_entrypoint.read_text(encoding="utf-8")


def test_host_installation_fixtures_keep_policy_identical_across_hosts(tmp_path: Path) -> None:
    # Given: a fresh workspace initialized for every supported host.
    runner = CliRunner()

    # When: the all-host adapter install runs.
    result = runner.invoke(app, ["init", "--workspace", str(tmp_path), "--agent", "all"])

    # Then: Codex/OpenCode and Claude receive the same policy bundle content.
    assert result.exit_code == 0
    shared_skill = tmp_path / ".agents" / "skills" / "career-resume-tailor"
    claude_skill = tmp_path / ".claude" / "plugins" / "career-resume-tailor"
    for relative in (
        "SKILL.md",
        "references/fact-policy.md",
        "references/proposal-contract.md",
        "references/rendering.md",
        "references/workflow.md",
    ):
        assert (shared_skill / relative).read_bytes() == (claude_skill / relative).read_bytes()


def test_init_preserves_existing_user_skill_file(tmp_path: Path) -> None:
    # Given: a user-owned Codex/OpenCode skill with the same name.
    target = tmp_path / ".agents" / "skills" / "career-resume-tailor" / "SKILL.md"
    target.parent.mkdir(parents=True)
    _ = target.write_text("user-owned skill\n", encoding="utf-8")
    runner = CliRunner()

    # When: Codex initialization runs.
    result = runner.invoke(app, ["init", "--workspace", str(tmp_path), "--agent", "codex"])

    # Then: user content is preserved and the conflict is reported.
    assert result.exit_code == 0
    payload = RESULT_ADAPTER.validate_json(result.stdout)
    assert target.read_text(encoding="utf-8") == "user-owned skill\n"
    assert payload.installations[0].status == "exists-different"
