import re
from dataclasses import dataclass
from hashlib import sha256
from typing import NewType

from career_ai.tailoring.models import EvidenceSpan, EvidenceSpanId, SourceArtifactId

ArtifactPrefix = NewType("ArtifactPrefix", str)


@dataclass(frozen=True, slots=True)
class SourceLine:
    """One non-empty source line with exact character offsets."""

    text: str
    start_offset: int
    end_offset: int
    evidence_span: EvidenceSpan


def stable_artifact_id(prefix: ArtifactPrefix, *parts: str) -> str:
    """Build a stable, schema-safe identifier from deterministic inputs."""
    digest = sha256("\x1f".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}-{digest}"


def extract_source_lines(
    source_text: str,
    source_artifact_id: SourceArtifactId,
) -> tuple[SourceLine, ...]:
    """Split source text into non-empty lines and retain exact evidence ranges."""
    lines: list[SourceLine] = []
    for match in re.finditer(r"(?m)^[^\r\n]*\S[^\r\n]*$", source_text):
        raw_text = match.group(0)
        leading = len(raw_text) - len(raw_text.lstrip())
        text = raw_text.strip()
        start_offset = match.start() + leading
        end_offset = start_offset + len(text)
        span_id = EvidenceSpanId(
            stable_artifact_id(
                ArtifactPrefix("evidence"),
                source_artifact_id,
                str(start_offset),
                str(end_offset),
                text,
            )
        )
        lines.append(
            SourceLine(
                text=text,
                start_offset=start_offset,
                end_offset=end_offset,
                evidence_span=EvidenceSpan(
                    id=span_id,
                    source_artifact_id=source_artifact_id,
                    text=text,
                    start_offset=start_offset,
                    end_offset=end_offset,
                ),
            )
        )
    return tuple(lines)
