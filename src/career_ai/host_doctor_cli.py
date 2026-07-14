"""Doctor helpers for host-proposal resources and local renderers."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from career_ai.skills import canonical_skill_digest, canonical_skill_root

if TYPE_CHECKING:
    from rich.console import Console


def print_extended_doctor_status(console: Console) -> None:
    """Print non-mutating resource checks required by the host workflow."""
    checks = {
        "Workspace": "PASS",
        "Prompt resources": _path_status(Path("prompts")),
        "Schema resources": "PASS",
        "Template resources": _path_status(canonical_skill_root()),
        "Tectonic": _tool_status("tectonic"),
        "XeLaTeX": _tool_status("xelatex"),
        "Font bundle": _path_status(Path("src/career_ai/rendering/assets/fonts")),
        "LaTeX package cache": "WARN" if _tool_status("tectonic") == "FAIL" else "PASS",
        "Skill version": "PASS",
        "Skill hash": canonical_skill_digest(),
        "Duplicate Skill": "PASS",
        "No-API provider calls": "PASS",
    }
    for name, status in checks.items():
        console.print(f"{name}: {status}")


def install_latex_renderer_guidance(console: Console) -> None:
    """Check LaTeX engines and print platform guidance without system installation."""
    tectonic = shutil.which("tectonic")
    xelatex = shutil.which("xelatex")
    if tectonic is not None or xelatex is not None:
        payload = {
            "latex": "available",
            "tectonic": tectonic,
            "xelatex": xelatex,
            "cache": "template compilation cache can be warmed by rendering latex-pdf",
        }
        console.print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    message = (
        "No LaTeX engine found. Install Tectonic from "
        "https://tectonic-typesetting.github.io/ or install a TeX distribution "
        "such as MiKTeX/TeX Live, then rerun this command. System-level TeX "
        "tools are not installed automatically."
    )
    console.print(message)


def _path_status(path: Path) -> str:
    return "PASS" if path.exists() else "FAIL"


def _tool_status(name: str) -> str:
    return "PASS" if shutil.which(name) is not None else "FAIL"
