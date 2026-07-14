"""Immutable contracts for LaTeX rendering, inspection, and compilation."""

from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from career_ai.tailoring.document_contracts import ResumeSection
from career_ai.tailoring.manifest_contracts import RenderBackend


class FrozenLatexModel(BaseModel):
    """Base for immutable LaTeX boundary models."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)


@unique
class LatexContext(StrEnum):
    """The syntactic context receiving escaped untrusted text."""

    TEXT = "text"
    URL = "url"
    EMAIL = "email"
    SECTION_TITLE = "section_title"
    BULLET = "bullet"
    DATE = "date"
    COMMAND_ARGUMENT = "command_argument"
    CUSTOM_MACRO_ARGUMENT = "custom_macro_argument"


@unique
class LatexFindingCode(StrEnum):
    """Stable codes for source constructs that are unsafe to compile."""

    SHELL_ESCAPE = "latex_shell_escape"
    SHELL_ESCAPE_PACKAGE = "latex_shell_escape_package"
    LUA_EXECUTION = "latex_lua_execution"
    FILE_WRITE = "latex_file_write"
    FILE_READ = "latex_file_read"
    OUT_OF_ROOT_INPUT = "latex_input_outside_root"
    DYNAMIC_INPUT_PATH = "latex_dynamic_input_path"


class LatexFinding(FrozenLatexModel):
    """One unsafe LaTeX source construct."""

    code: LatexFindingCode
    command: str
    line: int
    column: int
    target: str | None = None


@unique
class LatexStructureErrorCode(StrEnum):
    """Stable malformed-document boundary codes."""

    MISSING_BEGIN_DOCUMENT = "latex_missing_begin_document"
    MISSING_END_DOCUMENT = "latex_missing_end_document"
    DUPLICATE_BEGIN_DOCUMENT = "latex_duplicate_begin_document"
    DUPLICATE_END_DOCUMENT = "latex_duplicate_end_document"
    REVERSED_DOCUMENT_BOUNDARY = "latex_reversed_document_boundary"


class LatexSection(FrozenLatexModel):
    """A top-level section marker found in the document body."""

    title: str
    starred: bool
    source_offset: int


class LatexStructure(FrozenLatexModel):
    """Pure structural inspection of one complete LaTeX document."""

    body: str
    body_start: int
    body_end: int
    sections: tuple[LatexSection, ...]


@unique
class LatexCompileErrorCode(StrEnum):
    """Stable failure codes for local LaTeX compilation."""

    NO_ENGINE = "latex_no_engine"
    ENGINE_FAILED = "latex_engine_failed"
    TIMEOUT = "latex_engine_timeout"
    OUTPUT_MISSING = "latex_output_missing"


@dataclass(frozen=True, slots=True)
class LatexCompilerConfig:
    """Optional engine commands for deterministic tests and local overrides.

    ``None`` means discover the engine on PATH. An empty tuple disables that engine.
    """

    tectonic_command: tuple[str, ...] | None = None
    xelatex_command: tuple[str, ...] | None = None
    timeout_seconds: int = 120


class LatexCompilationSuccess(FrozenLatexModel):
    """Successful local LaTeX compilation metadata."""

    backend: RenderBackend
    pdf_path: Path
    engine_version: str


class LatexCompilationFailure(FrozenLatexModel):
    """Expected local LaTeX compilation failure."""

    code: LatexCompileErrorCode
    backend: RenderBackend | None = None
    message: str
    first_error: str | None = None


type LatexCompilationResult = LatexCompilationSuccess | LatexCompilationFailure


class LatexSectionMapping(FrozenLatexModel):
    """One approved writable source range in a user-owned template."""

    section: ResumeSection
    begin_marker: int
    end_marker: int
    content_start: int
    content_end: int
    confirmed: bool = True


class LatexTemplateProfile(FrozenLatexModel):
    """Static profile for a user-owned LaTeX template."""

    template_hash: str
    documentclass: str
    preamble_hash: str
    body_start: int
    body_end: int
    custom_commands: tuple[str, ...]
    sections: tuple[LatexSection, ...]
    section_mappings: tuple[LatexSectionMapping, ...]
    packages: tuple[str, ...]
    fonts: tuple[str, ...]
    unsafe_findings: tuple[LatexFinding, ...]
    requires_mapping_confirmation: bool
