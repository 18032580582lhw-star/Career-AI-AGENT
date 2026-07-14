from pathlib import Path
from typing import ClassVar, Final, Literal

import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

FIXTURE_DIR: Final = Path("evals/tailoring_cases")
EXPECTED_CASE_IDS: Final = {
    "safe_substantial_rewrite",
    "multi_evidence_merge",
    "jd_only_kubernetes",
    "responsibility_seniority_metric_inflation",
    "needs_confirmation_inference",
    "chinese_resume_english_jd",
    "no_op_conservative_output",
    "system_latex",
    "user_template_latex",
    "cjk_latex",
    "malicious_latex",
    "missing_latex_engine",
    "stale_user_template",
}


class FixtureModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)


class ProposalChange(FixtureModel):
    change_id: str = Field(min_length=1)
    proposed_text: str = Field(min_length=1)
    evidence: tuple[str, ...]
    requires_confirmation: bool


class Proposal(FixtureModel):
    strategy: Literal["conservative", "substantial", "evidence_merge"]
    rewritten_resume: str = Field(min_length=1)
    changes: tuple[ProposalChange, ...]


class RenderingExpectations(FixtureModel):
    mode: Literal["none", "system_latex", "user_latex"]
    template_text: str
    engine: str
    engine_available: bool
    template_hash_matches: bool
    expected_status: Literal["not_requested", "rendered", "blocked", "stale"]
    must_contain: tuple[str, ...]
    must_not_contain: tuple[str, ...]


class TailoringGoldenFixture(FixtureModel):
    case_id: str = Field(min_length=1)
    resume_text: str = Field(min_length=1)
    jd_text: str = Field(min_length=1)
    proposal: Proposal
    expected_decision: Literal["accepted", "needs_confirmation", "rejected", "stale"]
    expected_codes: tuple[str, ...]
    rendering_expectations: RenderingExpectations


def _load_fixtures() -> dict[str, TailoringGoldenFixture]:
    fixtures = (
        TailoringGoldenFixture.model_validate_json(path.read_text(encoding="utf-8"))
        for path in sorted(FIXTURE_DIR.glob("*.json"))
    )
    return {fixture.case_id: fixture for fixture in fixtures}


def test_repository_tailoring_fixtures_match_the_release_contract() -> None:
    # Given: the release-quality tailoring fixture directory.
    # When: every JSON document is parsed through the strict typed boundary.
    fixtures = _load_fixtures()

    # Then: all required factual, multilingual, and rendering cases are present exactly once.
    assert set(fixtures) == EXPECTED_CASE_IDS
    assert len(fixtures) == len(EXPECTED_CASE_IDS)
    assert len(list(FIXTURE_DIR.glob("*.json"))) == len(EXPECTED_CASE_IDS)


def test_factual_safety_cases_pin_decisions_and_codes() -> None:
    # Given: proposals that distinguish supported edits from unsafe candidate claims.
    fixtures = _load_fixtures()

    # When: their golden outcomes are inspected.
    outcomes = {
        case_id: (fixture.expected_decision, fixture.expected_codes)
        for case_id, fixture in fixtures.items()
    }

    # Then: each boundary has a stable decision and machine-readable violation code.
    assert outcomes["safe_substantial_rewrite"] == ("accepted", ())
    assert outcomes["multi_evidence_merge"] == ("accepted", ())
    assert outcomes["jd_only_kubernetes"] == ("rejected", ("unsupported_technology",))
    assert outcomes["responsibility_seniority_metric_inflation"] == (
        "rejected",
        ("unsupported_responsibility", "unsupported_seniority", "unsupported_metric"),
    )
    assert outcomes["needs_confirmation_inference"] == (
        "needs_confirmation",
        ("inference_requires_confirmation",),
    )


def test_rendering_cases_pin_success_blocked_and_stale_outcomes() -> None:
    # Given: system, user-owned, multilingual, unsafe, unavailable, and stale render cases.
    fixtures = _load_fixtures()

    # When: their expected render status is selected.
    statuses = {
        case_id: fixture.rendering_expectations.expected_status
        for case_id, fixture in fixtures.items()
    }

    # Then: render success cannot be confused with safety blocks or stale artifacts.
    assert statuses["system_latex"] == "rendered"
    assert statuses["user_template_latex"] == "rendered"
    assert statuses["cjk_latex"] == "rendered"
    assert statuses["malicious_latex"] == "blocked"
    assert statuses["missing_latex_engine"] == "blocked"
    assert statuses["stale_user_template"] == "stale"
    assert fixtures["malicious_latex"].expected_codes == ("unsafe_latex_command",)
    assert "\\write18" in fixtures["malicious_latex"].rendering_expectations.template_text
    assert not fixtures["missing_latex_engine"].rendering_expectations.engine_available
    assert not fixtures["stale_user_template"].rendering_expectations.template_hash_matches


def test_prompt_injection_is_preserved_as_inert_job_description_data() -> None:
    # Given: an adversarial instruction embedded in JD text.
    fixture = _load_fixtures()["jd_only_kubernetes"]

    # When: the fixture is parsed as data.
    jd_text = fixture.jd_text

    # Then: it remains inert text and does not change the pinned rejection outcome.
    assert "Ignore previous instructions" in jd_text
    assert fixture.expected_decision == "rejected"
    assert fixture.expected_codes == ("unsupported_technology",)


def test_no_op_case_keeps_the_resume_byte_for_byte() -> None:
    # Given: a resume that is already adequate for the JD.
    fixture = _load_fixtures()["no_op_conservative_output"]

    # When: the conservative proposal is inspected.
    proposal = fixture.proposal

    # Then: it records no speculative change and preserves the original text exactly.
    assert proposal.changes == ()
    assert proposal.rewritten_resume == fixture.resume_text


def test_multilingual_fixtures_preserve_unicode_content() -> None:
    # Given: Chinese evidence and CJK LaTeX content.
    fixtures = _load_fixtures()

    # When: UTF-8 JSON is parsed.
    chinese_case = fixtures["chinese_resume_english_jd"]
    cjk_case = fixtures["cjk_latex"]

    # Then: Chinese candidate facts and rendering markers survive intact.
    assert "数据分析师" in chinese_case.resume_text
    assert "候选人" in cjk_case.proposal.rewritten_resume
    assert cjk_case.rendering_expectations.engine == "xelatex"


def test_malformed_fixture_json_is_rejected_at_the_boundary() -> None:
    # Given: truncated JSON that cannot represent a golden fixture.
    malformed_json = '{"case_id": "truncated"'

    # When/Then: the typed JSON boundary rejects it instead of returning partial data.
    with pytest.raises(ValidationError):
        _ = TailoringGoldenFixture.model_validate_json(malformed_json)
