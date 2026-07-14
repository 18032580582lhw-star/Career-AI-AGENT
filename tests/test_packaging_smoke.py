from __future__ import annotations

import subprocess
import sys
from pathlib import Path  # noqa: TC003 - pytest tmp_path uses concrete Path.
from zipfile import ZipFile


def test_wheel_contains_cli_entrypoint_and_runtime_resources(tmp_path: Path) -> None:
    # Given: the repository packaging metadata.
    wheel_dir = tmp_path / "wheelhouse"
    wheel_dir.mkdir()

    # When: a no-dependency wheel is built from the local source tree.
    completed = subprocess.run(  # noqa: S603 - constant Python module invocation.
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            ".",
            "--no-deps",
            "--wheel-dir",
            str(wheel_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    # Then: the wheel carries the CLI entrypoint and non-Python runtime assets.
    assert completed.returncode == 0
    wheel_path = next(wheel_dir.glob("ai_career_intelligence_suite-*.whl"))
    with ZipFile(wheel_path) as wheel:
        names = set(wheel.namelist())
        entry_points = next(name for name in names if name.endswith(".dist-info/entry_points.txt"))
        assert "career_ai/skills/career_resume_tailor/SKILL.md" in names
        assert "career_ai/skills/career_resume_tailor/references/workflow.md" in names
        assert "career_ai/rendering/latex/assets/system_resume.tex" in names
        assert "career_ai/rendering/assets/fonts/NotoSans-Regular.woff2" in names
        assert "career-ai-agent = career_ai.cli:app" in wheel.read(entry_points).decode("utf-8")
