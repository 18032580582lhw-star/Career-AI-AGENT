"""Shared primitives for versioned tailoring protocol artifacts."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import TYPE_CHECKING, Annotated, ClassVar, Final

from pydantic import BaseModel, ConfigDict, Field, JsonValue
from pydantic_core import PydanticCustomError

if TYPE_CHECKING:
    from collections.abc import Mapping

PROTOCOL_VERSION: Final = "1.0"
SCHEMA_VERSION: Final = 1
SHA256_PATTERN: Final = r"^[0-9a-f]{64}$"
RUN_ID_PATTERN: Final = r"^run-[a-z0-9]+(?:-[a-z0-9]+)*$"
ENTITY_ID_PATTERN: Final = r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$"

Sha256 = Annotated[str, Field(pattern=SHA256_PATTERN)]
RunId = Annotated[str, Field(pattern=RUN_ID_PATTERN)]
EntityId = Annotated[str, Field(pattern=ENTITY_ID_PATTERN)]
NonEmptyText = Annotated[str, Field(min_length=1)]


class FrozenContractModel(BaseModel):
    """Immutable strict model for JSON protocol boundaries."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")


class VersionedContract(FrozenContractModel):
    """Common protocol and schema version envelope."""

    protocol_version: Annotated[str, Field(pattern=r"^1\.0$")] = PROTOCOL_VERSION
    schema_version: Annotated[int, Field(ge=1, le=1)] = SCHEMA_VERSION


def canonical_json_hash(payload: Mapping[str, JsonValue]) -> str:
    """Return the SHA-256 of a stable canonical JSON representation."""
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def require_unique(values: tuple[str, ...], *, field_name: str) -> None:
    """Raise a stable validation error when identifiers repeat."""
    if len(values) != len(set(values)):
        error_code = "duplicate_ids"
        error_message = "{field_name} must be unique"
        raise PydanticCustomError(
            error_code,
            error_message,
            {"field_name": field_name},
        )
