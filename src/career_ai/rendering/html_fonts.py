"""Bundled font assets for HTML/CSS PDF rendering."""

from __future__ import annotations

import re
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Final

_FONT_PACKAGE: Final = "career_ai.rendering"
_FONT_DIR: Final = "assets/fonts"
_NOTO_SANS_FILE: Final = "NotoSans-Regular.woff2"
_NOTO_SANS_SC_CSS: Final = "NotoSansSC.css"
_SC_FONT_PATTERN: Final = re.compile(r"SC-[0-9]+\.woff2")


@dataclass(frozen=True, slots=True)
class FontBundleStatus:
    """Local bundled font availability for HTML/CSS PDF rendering."""

    available: bool
    font_dir: Path
    missing_files: tuple[str, ...]


def html_font_css() -> str:
    """Return local font CSS that never references network font providers."""
    font_dir = bundled_font_dir()
    noto_sans = (font_dir / _NOTO_SANS_FILE).as_uri()
    noto_sans_sc_css = (font_dir / _NOTO_SANS_SC_CSS).as_uri()
    return (
        "@font-face {\n"
        "  font-family: 'Noto Sans';\n"
        f"  src: url('{noto_sans}') format('woff2');\n"
        "  font-weight: 400;\n"
        "  font-style: normal;\n"
        "  font-display: swap;\n"
        "}\n"
        f"@import url('{noto_sans_sc_css}');\n"
    )


def check_font_bundle() -> FontBundleStatus:
    """Check that the required bundled Noto font assets are present."""
    font_dir = bundled_font_dir()
    missing = tuple(
        file_name
        for file_name in _required_font_files(font_dir)
        if not (font_dir / file_name).is_file()
    )
    return FontBundleStatus(
        available=not missing,
        font_dir=font_dir,
        missing_files=missing,
    )


def bundled_font_dir() -> Path:
    """Return the package-local font directory."""
    resource = files(_FONT_PACKAGE).joinpath(_FONT_DIR)
    return Path(str(resource))


def _required_font_files(font_dir: Path) -> tuple[str, ...]:
    css_path = font_dir / _NOTO_SANS_SC_CSS
    if not css_path.is_file():
        return (_NOTO_SANS_FILE, _NOTO_SANS_SC_CSS)
    css = css_path.read_text(encoding="utf-8-sig")
    sc_files = tuple(sorted(set(_SC_FONT_PATTERN.findall(css))))
    return (_NOTO_SANS_FILE, _NOTO_SANS_SC_CSS, *sc_files)
