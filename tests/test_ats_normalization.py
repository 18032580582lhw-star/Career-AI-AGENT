from __future__ import annotations

from career_ai.rendering.ats_normalization import (
    AtsNormalizationOptions,
    AtsPunctuationStyle,
    normalize_accepted_resume_document,
    normalize_ats_email,
    normalize_ats_text,
    normalize_ats_url,
)
from tests.resume_document_helpers import accepted_resume_document


def test_ats_text_normalizes_unicode_spacing_and_zero_width_without_losing_cjk() -> None:
    # Given
    raw = "\uFF21da\u200b\u3000中文\t工程师"

    # When
    normalized = normalize_ats_text(raw)

    # Then
    assert normalized == "Ada 中文 工程师"


def test_ats_punctuation_normalization_is_configurable() -> None:
    # Given
    raw = "“AI”—工程师…"

    # When
    preserved = normalize_ats_text(
        raw,
        options=AtsNormalizationOptions(punctuation=AtsPunctuationStyle.PRESERVE),
    )
    compatible = normalize_ats_text(
        raw,
        options=AtsNormalizationOptions(punctuation=AtsPunctuationStyle.ASCII_COMPATIBLE),
    )

    # Then
    assert preserved == raw
    assert compatible == '"AI"-工程师...'


def test_ats_text_removes_bom_bidi_and_illegal_control_characters() -> None:
    # Given
    raw = "Ada\ufeff\u202e\x00中文"

    # When
    normalized = normalize_ats_text(raw)

    # Then
    assert normalized == "Ada中文"


def test_ats_email_and_url_normalization_preserve_semantic_components() -> None:
    # Given / When
    email = normalize_ats_email("Ada@Example.COM")
    url = normalize_ats_url("HTTPS://Example.COM/Ada?Q=One#Top")

    # Then
    assert email == "Ada@example.com"
    assert url == "https://example.com/Ada?Q=One#Top"


def test_document_normalization_preserves_hashes_provenance_and_cjk() -> None:
    # Given
    document = accepted_resume_document()
    payload = document.model_dump(mode="json")
    payload["professional_summary"][0]["text"] = "Built\u200b typed APIs — 中文。"
    document_with_ats_noise = type(document).model_validate(payload)

    # When
    normalized = normalize_accepted_resume_document(
        document_with_ats_noise,
        options=AtsNormalizationOptions(
            punctuation=AtsPunctuationStyle.ASCII_COMPATIBLE,
        ),
    )

    # Then
    assert normalized.professional_summary[0].text == "Built typed APIs - 中文。"
    assert normalized.identity.contact_lines == (
        "Ada@example.com",
        "https://example.com/Ada",
    )
    assert normalized.links[0].url == "https://example.com/Ada"
    assert normalized.proposal_hash == document.proposal_hash
    assert normalized.validation_hash == document.validation_hash
    assert normalized.professional_summary[0].source_fact_ids == ("fact-1",)
    assert normalize_accepted_resume_document(normalized) == normalized
