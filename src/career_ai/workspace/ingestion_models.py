from enum import StrEnum, unique
from typing import Annotated, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field

_Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
_RelativePath = Annotated[str, Field(min_length=1)]


@unique
class SourceKind(StrEnum):
    """Supported immutable source roles."""

    RESUME = "resume"
    JOB_DESCRIPTION = "job_description"
    LATEX_TEMPLATE = "latex_template"


@unique
class SourceOrigin(StrEnum):
    """How a source entered the workspace."""

    FILE = "file"
    TEXT = "text"
    URL = "url"


class IngestedSource(BaseModel):
    """Immutable metadata for one extracted, content-addressed source."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1] = 1
    artifact_id: _Sha256
    kind: SourceKind
    origin: SourceOrigin
    sha256: _Sha256
    media_type: str
    extraction_status: Literal["extracted"] = "extracted"
    content_path: _RelativePath
    extracted_text_path: _RelativePath
    original_name: str | None = None
    source_url: str | None = None
