from pathlib import Path


def test_streamlit_theme_css_contains_requested_visual_direction() -> None:
    # Given the app theme stylesheet.
    css = Path("static/app_theme.css").read_text(encoding="utf-8")

    # When the visual design tokens are inspected.
    has_warm_background = "#f5efe3" in css
    has_soft_gray_surface = "#f1f1ef" in css
    has_black_button = "#111111" in css
    has_white_button = "#ffffff" in css
    has_rounded_buttons = "border-radius: 999px" in css
    has_depth_shadow = "box-shadow" in css
    has_motion = "@keyframes" in css

    # Then the requested warm, minimal, dimensional style is encoded.
    assert has_warm_background
    assert has_soft_gray_surface
    assert has_black_button
    assert has_white_button
    assert has_rounded_buttons
    assert has_depth_shadow
    assert has_motion


def test_button_descendant_text_keeps_contrast_on_3d_buttons() -> None:
    # Given Streamlit renders button text inside nested inline elements.
    css = Path("static/app_theme.css").read_text(encoding="utf-8")

    # When button typography rules are inspected.
    has_default_descendant_rule = ".stButton button *" in css
    has_default_white_text = "color: #ffffff !important;" in css
    has_hover_descendant_rule = ".stButton button:hover *" in css
    has_hover_black_text = "color: #111111 !important;" in css

    # Then nested button labels should keep contrast with the 3D button states.
    assert has_default_descendant_rule
    assert has_default_white_text
    assert has_hover_descendant_rule
    assert has_hover_black_text


def test_app_loads_custom_theme_css() -> None:
    # Given the Streamlit app source.
    source = Path("src/career_ai/streamlit_app/main.py").read_text(encoding="utf-8")

    # When the app starts.
    loads_theme = "_render_theme_css()" in source
    references_theme_file = "static/app_theme.css" in source

    # Then the custom visual layer should be injected.
    assert loads_theme
    assert references_theme_file
