import ast
from pathlib import Path
from typing import override

_CORE_DIRECTORIES = (
    Path("src/career_ai/tailoring"),
    Path("src/career_ai/workspace"),
    Path("src/career_ai/rendering"),
)
_SKILL_DIRECTORY = Path("src/career_ai/skills")
_SOURCE_ROOT = Path("src/career_ai")


class _ImportCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: list[tuple[int, str]] = []

    @override
    def visit_Import(self, node: ast.Import) -> None:
        self.imports.extend((node.lineno, alias.name) for alias in node.names)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module is not None:
            self.imports.append((node.lineno, node.module))


def _python_files(*roots: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for root in roots for path in root.rglob("*.py")))


def _find_prohibited_imports(
    files: tuple[Path, ...],
    prohibited_modules: tuple[str, ...],
) -> tuple[str, ...]:
    violations: list[str] = []
    for path in files:
        collector = _ImportCollector()
        collector.visit(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
        for line_number, imported_module in collector.imports:
            if any(
                imported_module == prohibited or imported_module.startswith(f"{prohibited}.")
                for prohibited in prohibited_modules
            ):
                violations.append(f"{path}:{line_number} imports {imported_module}")
    return tuple(violations)


def test_core_layers_do_not_depend_on_ui_or_legacy_agent_runtime() -> None:
    # Given: the domain, workspace, and rendering implementation modules.
    protected_files = _python_files(*_CORE_DIRECTORIES)

    # When: their static imports are checked against forbidden outer layers.
    violations = _find_prohibited_imports(
        protected_files,
        ("streamlit", "career_ai.agent"),
    )

    # Then: core behavior remains independent of the UI and legacy agent runtime.
    assert violations == ()


def test_skill_and_harness_modules_do_not_depend_on_streamlit() -> None:
    # Given: every Python Skill module and every source module named as a harness.
    skill_files = _python_files(_SKILL_DIRECTORY)
    harness_files = tuple(sorted(_SOURCE_ROOT.rglob("*harness*.py")))

    # When: their static imports are checked against the optional web UI.
    violations = _find_prohibited_imports(skill_files + harness_files, ("streamlit",))

    # Then: host-facing workflows remain usable without Streamlit.
    assert violations == ()


def test_no_production_file_imports_removed_agent_or_llm_runtime() -> None:
    # Given: every production Python source file under the domain package.
    production_files = _python_files(_SOURCE_ROOT)

    # When: static imports are checked against the removed runtime namespaces.
    violations = _find_prohibited_imports(
        production_files,
        ("career_ai.agent", "career_ai.llm"),
    )

    # Then: the embedded agent and model runtime are fully removed.
    assert violations == ()


def test_no_production_file_imports_streamlit() -> None:
    # Given: every production Python source file under the domain package.
    production_files = _python_files(_SOURCE_ROOT)

    # When: static imports are checked against the removed web UI.
    violations = _find_prohibited_imports(production_files, ("streamlit",))

    # Then: no product surface depends on Streamlit.
    assert violations == ()


def test_boundary_scanner_reports_prohibited_import_when_source_violates_boundary(
    tmp_path: Path,
) -> None:
    # Given: a synthetic protected module that imports a forbidden UI dependency.
    module = tmp_path / "protected.py"
    _ = module.write_text("import streamlit\n", encoding="utf-8")

    # When: the architecture scanner checks that module.
    violations = _find_prohibited_imports((module,), ("streamlit",))

    # Then: the scanner exposes the exact dependency violation instead of passing.
    assert violations == (f"{module}:1 imports streamlit",)
