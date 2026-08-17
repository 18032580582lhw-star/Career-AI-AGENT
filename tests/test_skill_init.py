from __future__ import annotations

from importlib import resources
from typing import TYPE_CHECKING

from pydantic import TypeAdapter
from typer.testing import CliRunner

from career_ai.cli import app
from career_ai.skills.installation import (
    HostAgent,
    SkillInstallationResult,
    canonical_skill_digest,
    canonical_skill_root,
)

if TYPE_CHECKING:
    from pathlib import Path

RESULT_ADAPTER = TypeAdapter(SkillInstallationResult)
REFERENCE_FILES = (
    "references/fact-policy.md",
    "references/proposal-contract.md",
    "references/rendering.md",
    "references/workflow.md",
)
REQUIRED_COMMANDS = ("init", "prepare", "validate-draft", "confirm", "render")
REQUIRED_STOP_CONDITIONS = (
    "validation fails",
    "evidence is missing",
    "exceeds its source",
    "stale",
    "rejects",
    "repair limit",
)


def _frontmatter_fields(skill_text: str) -> dict[str, str]:
    lines = skill_text.splitlines()
    assert lines[0] == "---"
    closing_index = lines.index("---", 1)
    fields: dict[str, str] = {}
    for line in lines[1:closing_index]:
        key, delimiter, value = line.partition(":")
        assert delimiter
        assert key
        assert value.strip()
        fields[key] = value.strip().strip('"')
    return fields


def test_canonical_skill_uses_valid_minimal_frontmatter_and_metadata() -> None:
    # Given: the packaged canonical Agent Skill.
    skill_root = canonical_skill_root()
    skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    metadata_text = (skill_root / "agents" / "openai.yaml").read_text(encoding="utf-8")

    # When: host discovery metadata is inspected.
    fields = _frontmatter_fields(skill_text)

    # Then: only portable Skill fields and the accepted Codex interface schema are used.
    assert fields.keys() == {"name", "description"}
    assert fields["name"] == "career-resume-tailor"
    assert "resume" in fields["description"].lower()
    assert "when" in fields["description"].lower()
    assert metadata_text.startswith("interface:\n")
    assert "  display_name:" in metadata_text
    assert "  short_description:" in metadata_text
    assert "  default_prompt:" in metadata_text
    assert "protocol:" not in metadata_text
    assert "commands:" not in metadata_text


def test_host_agent_contract_contains_only_supported_values() -> None:
    # Given: the public host selector enum.
    # When: its serialized values are enumerated.
    values = {host.value for host in HostAgent}

    # Then: only the two current hosts and their combined selector remain.
    assert values == {"codex", "claude", "all"}


def test_init_agent_all_installs_exactly_two_hosts_idempotently(tmp_path: Path) -> None:
    # Given: a fresh workspace.
    runner = CliRunner()

    # When: both supported host Skills are initialized twice.
    first = runner.invoke(app, ["init", "--workspace", str(tmp_path), "--agent", "all"])
    second = runner.invoke(app, ["init", "--workspace", str(tmp_path), "--agent", "all"])

    # Then: exactly Codex and Claude use their official project discovery paths.
    assert first.exit_code == 0
    assert second.exit_code == 0
    first_payload = RESULT_ADAPTER.validate_json(first.stdout)
    payload = RESULT_ADAPTER.validate_json(second.stdout)
    assert len(payload.installations) == 2
    assert {item.agent for item in payload.installations} == {
        HostAgent.CLAUDE,
        HostAgent.CODEX,
    }
    assert {item.status for item in first_payload.installations} == {"installed"}
    assert {item.status for item in payload.installations} == {"present"}
    assert payload.skill_hash == canonical_skill_digest()
    codex_skill = tmp_path / ".agents" / "skills" / "career-resume-tailor"
    claude_skill = tmp_path / ".claude" / "skills" / "career-resume-tailor"
    assert (codex_skill / "SKILL.md").is_file()
    assert (claude_skill / "SKILL.md").is_file()
    assert not (tmp_path / ".claude" / "plugins").exists()


def test_host_copies_are_byte_identical_and_metadata_is_accurate(tmp_path: Path) -> None:
    # Given: a fresh workspace initialized for all supported hosts.
    result = CliRunner().invoke(
        app,
        ["init", "--workspace", str(tmp_path), "--agent", "all"],
    )

    # When: installed policy bytes and the machine-readable result are inspected.
    payload = RESULT_ADAPTER.validate_json(result.stdout)
    codex_skill = tmp_path / ".agents" / "skills" / "career-resume-tailor"
    claude_skill = tmp_path / ".claude" / "skills" / "career-resume-tailor"

    # Then: hosts share one policy bundle and report format, host, and exact target.
    assert result.exit_code == 0
    for relative in ("SKILL.md", *REFERENCE_FILES):
        assert (codex_skill / relative).read_bytes() == (claude_skill / relative).read_bytes()
    expected_targets = {
        HostAgent.CODEX: str(codex_skill.resolve(strict=False)),
        HostAgent.CLAUDE: str(claude_skill.resolve(strict=False)),
    }
    for installation in payload.installations:
        assert installation.format == "agent-skill"
        assert installation.target == expected_targets[installation.agent]
        assert not hasattr(installation, "protocol")
        assert not hasattr(installation, "template")


def test_init_preserves_differing_user_files_for_each_host(tmp_path: Path) -> None:
    # Given: differing user-owned Skill files at both supported discovery paths.
    targets = {
        HostAgent.CODEX: tmp_path / ".agents" / "skills" / "career-resume-tailor" / "SKILL.md",
        HostAgent.CLAUDE: tmp_path / ".claude" / "skills" / "career-resume-tailor" / "SKILL.md",
    }
    original = b"user-owned skill\n"
    for target in targets.values():
        target.parent.mkdir(parents=True)
        _ = target.write_bytes(original)

    # When: each host initializer encounters the conflict.
    results = {
        host: CliRunner().invoke(
            app,
            ["init", "--workspace", str(tmp_path), "--agent", host.value],
        )
        for host in targets
    }

    # Then: neither user file changes and each conflict is reported.
    for host, result in results.items():
        assert result.exit_code == 0
        payload = RESULT_ADAPTER.validate_json(result.stdout)
        assert targets[host].read_bytes() == original
        assert payload.installations[0].status == "exists-different"


def test_install_record_matches_machine_readable_result(tmp_path: Path) -> None:
    # Given: a successful all-host initialization.
    result = CliRunner().invoke(
        app,
        ["init", "--workspace", str(tmp_path), "--agent", "all"],
    )

    # When: stdout and the atomically written installation record are decoded.
    stdout_payload = RESULT_ADAPTER.validate_json(result.stdout)
    record_payload = RESULT_ADAPTER.validate_json(
        (tmp_path / ".career_ai" / "skill-installations.json").read_text(encoding="utf-8")
    )

    # Then: persistent metadata is exactly the reported schema.
    assert result.exit_code == 0
    assert record_payload == stdout_payload


def test_skill_references_every_required_command_and_stop_condition() -> None:
    # Given: the canonical Skill bundle.
    skill_root = canonical_skill_root()
    corpus = "\n".join(
        (skill_root / path).read_text(encoding="utf-8")
        for path in ("SKILL.md", *REFERENCE_FILES)
    ).lower()

    # Then: every required command and stop condition is referenced verbatim.
    for command in REQUIRED_COMMANDS:
        assert command in corpus, command
    for condition in REQUIRED_STOP_CONDITIONS:
        assert condition in corpus, condition


def test_packaged_resources_are_importable_for_clean_install_smoke() -> None:
    # Given: package data expected by host Skills and renderers.
    skill_files = resources.files("career_ai.skills")
    rendering_files = resources.files("career_ai.rendering")

    # When: resources are resolved through importlib instead of source-relative paths.
    skill_entrypoint = skill_files.joinpath("career_resume_tailor", "SKILL.md")
    openai_metadata = skill_files.joinpath("career_resume_tailor", "agents", "openai.yaml")
    system_template = rendering_files.joinpath("latex", "assets", "system_resume.tex")
    noto_font = rendering_files.joinpath("assets", "fonts", "NotoSans-Regular.woff2")

    # Then: clean wheel installs can discover the complete canonical Skill bundle.
    assert skill_entrypoint.is_file()
    assert openai_metadata.is_file()
    assert system_template.is_file()
    assert noto_font.is_file()
    for relative in REFERENCE_FILES:
        assert skill_files.joinpath("career_resume_tailor", *relative.split("/")).is_file()
