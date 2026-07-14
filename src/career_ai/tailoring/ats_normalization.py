"""Semantic-preserving ATS normalization for accepted resume documents."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Final, assert_never
from urllib.parse import urlsplit, urlunsplit

from career_ai.tailoring.document_contracts import (
    AcceptedResumeDocument,
    CandidateIdentity,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    ResumeBullet,
    ResumeLink,
)

_EMAIL: Final = re.compile(r"^(?P<local>[^@\s]+)@(?P<domain>[^@\s]+)$")
_IGNORABLE_CHARACTERS: Final = str.maketrans(
    "",
    "",
    "\u061c\u200b\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2060\u2066\u2067\u2068\u2069\ufeff",
)
_ASCII_PUNCTUATION: Final = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
        "\u2022": "-",
    },
)


@unique
class AtsPunctuationStyle(StrEnum):
    """Supported punctuation policies for ATS-facing text."""

    PRESERVE = "preserve"
    ASCII_COMPATIBLE = "ascii-compatible"


@dataclass(frozen=True, slots=True)
class AtsNormalizationOptions:
    """Configuration for semantic-preserving ATS normalization."""

    punctuation: AtsPunctuationStyle = AtsPunctuationStyle.PRESERVE


DEFAULT_ATS_OPTIONS: Final = AtsNormalizationOptions()


def normalize_ats_text(
    value: str,
    *,
    options: AtsNormalizationOptions = DEFAULT_ATS_OPTIONS,
) -> str:
    """Normalize Unicode and whitespace while retaining semantic characters."""
    composed = unicodedata.normalize("NFC", value)
    width_normalized = "".join(
        chr(ord(character) - 0xFEE0)
        if "\uFF01" <= character <= "\uFF5E"
        else " "
        if character == "\u3000"
        else character
        for character in composed
    )
    normalized = width_normalized.translate(_IGNORABLE_CHARACTERS)
    without_controls = "".join(
        " " if character.isspace() else character
        for character in normalized
        if unicodedata.category(character) != "Cc" or character.isspace()
    )
    match options.punctuation:
        case AtsPunctuationStyle.PRESERVE:
            punctuated = without_controls
        case AtsPunctuationStyle.ASCII_COMPATIBLE:
            punctuated = without_controls.translate(_ASCII_PUNCTUATION)
        case _:
            assert_never(options.punctuation)
    return " ".join(punctuated.split())


def normalize_ats_email(
    value: str,
    *,
    options: AtsNormalizationOptions = DEFAULT_ATS_OPTIONS,
) -> str:
    """Normalize an email domain without changing the local part."""
    normalized = normalize_ats_text(value, options=options)
    match = _EMAIL.fullmatch(normalized)
    if match is None:
        return normalized
    return f"{match.group('local')}@{match.group('domain').casefold()}"


def normalize_ats_url(
    value: str,
    *,
    options: AtsNormalizationOptions = DEFAULT_ATS_OPTIONS,
) -> str:
    """Normalize a URL scheme and host while preserving path/query case."""
    normalized = normalize_ats_text(value, options=options)
    try:
        parsed = urlsplit(normalized)
    except ValueError:
        return normalized
    if not parsed.scheme or not parsed.netloc:
        return normalized
    userinfo, separator, host_port = parsed.netloc.rpartition("@")
    if host_port.startswith("["):
        closing = host_port.find("]")
        normalized_host_port = host_port
        if closing >= 0:
            normalized_host_port = (
                host_port[: closing + 1].casefold() + host_port[closing + 1 :]
            )
    else:
        host, port_separator, port = host_port.partition(":")
        normalized_host_port = host.casefold() + port_separator + port
    normalized_netloc = (
        f"{userinfo}{separator}{normalized_host_port}"
        if separator
        else normalized_host_port
    )
    return urlunsplit(
        (
            parsed.scheme.casefold(),
            normalized_netloc,
            parsed.path,
            parsed.query,
            parsed.fragment,
        ),
    )


def normalize_ats_contact(
    value: str,
    *,
    options: AtsNormalizationOptions = DEFAULT_ATS_OPTIONS,
) -> str:
    """Normalize a standalone email or URL contact line when recognized."""
    normalized = normalize_ats_text(value, options=options)
    if _EMAIL.fullmatch(normalized) is not None:
        return normalize_ats_email(normalized, options=options)
    try:
        parsed = urlsplit(normalized)
    except ValueError:
        return normalized
    if parsed.scheme.casefold() in {"http", "https"} and parsed.netloc:
        return normalize_ats_url(normalized, options=options)
    return normalized


def normalize_accepted_resume_document(
    document: AcceptedResumeDocument,
    *,
    options: AtsNormalizationOptions = DEFAULT_ATS_OPTIONS,
) -> AcceptedResumeDocument:
    """Return one canonical ATS-normalized copy without changing provenance."""
    def normalize(value: str) -> str:
        return normalize_ats_text(value, options=options)

    def normalize_bullet(item: ResumeBullet) -> ResumeBullet:
        return ResumeBullet(
            text=normalize(item.text),
            source_fact_ids=item.source_fact_ids,
        )

    return AcceptedResumeDocument(
        protocol_version=document.protocol_version,
        schema_version=document.schema_version,
        run_id=document.run_id,
        proposal_hash=document.proposal_hash,
        validation_hash=document.validation_hash,
        identity=CandidateIdentity(
            name=normalize(document.identity.name),
            headline=(
                None
                if document.identity.headline is None
                else normalize(document.identity.headline)
            ),
            contact_lines=tuple(
                normalize_ats_contact(item, options=options)
                for item in document.identity.contact_lines
            ),
            source_fact_ids=document.identity.source_fact_ids,
        ),
        professional_summary=tuple(
            normalize_bullet(item) for item in document.professional_summary
        ),
        skills=tuple(normalize_bullet(item) for item in document.skills),
        experience=tuple(
            ExperienceEntry(
                organization=normalize(item.organization),
                title=normalize(item.title),
                date_range=normalize(item.date_range),
                location=None if item.location is None else normalize(item.location),
                bullets=tuple(normalize_bullet(entry) for entry in item.bullets),
                source_fact_ids=item.source_fact_ids,
            )
            for item in document.experience
        ),
        projects=tuple(
            ProjectEntry(
                name=normalize(item.name),
                subtitle=None if item.subtitle is None else normalize(item.subtitle),
                bullets=tuple(normalize_bullet(entry) for entry in item.bullets),
                source_fact_ids=item.source_fact_ids,
            )
            for item in document.projects
        ),
        education=tuple(
            EducationEntry(
                institution=normalize(item.institution),
                credential=normalize(item.credential),
                date_range=None if item.date_range is None else normalize(item.date_range),
                details=tuple(normalize_bullet(entry) for entry in item.details),
                source_fact_ids=item.source_fact_ids,
            )
            for item in document.education
        ),
        links=tuple(
            ResumeLink(
                label=normalize(item.label),
                url=normalize_ats_url(item.url, options=options),
                source_fact_ids=item.source_fact_ids,
            )
            for item in document.links
        ),
        output_language=normalize(document.output_language),
        section_order=document.section_order,
    )
