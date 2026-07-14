"""Access to the bundled, user-independent LaTeX template."""

from importlib.resources import files


def load_system_template() -> str:
    """Load the minimal CJK-capable system resume template as UTF-8 text."""
    template = files("career_ai.rendering.latex").joinpath("assets/system_resume.tex")
    return template.read_text(encoding="utf-8")
