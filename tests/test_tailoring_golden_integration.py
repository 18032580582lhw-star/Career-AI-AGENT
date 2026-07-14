"""Execute release golden data through the typed validation lifecycle."""

from pathlib import Path
from typing import TYPE_CHECKING

from career_ai.tailoring.adequacy import evaluate_optimization_adequacy
from career_ai.tailoring.adequacy_models import AdequacyContext
from career_ai.tailoring.models import (
    CandidateFact,
    CandidateFactId,
    EvidenceProvenance,
    EvidenceSpanId,
)
from career_ai.tailoring.proposal_contracts import (
    ResumeTailoringProposal,
    calculate_proposal_hash,
)
from career_ai.tailoring.safety import evaluate_factual_safety
from career_ai.tailoring.state_machine import ValidationContext, decide_validation_state
from tests.test_tailoring_golden_fixtures import TailoringGoldenFixture

if TYPE_CHECKING:
    from pydantic import JsonValue


def test_no_op_golden_fixture_runs_through_real_validation_lifecycle() -> None:
    fixture_path = Path("evals/tailoring_cases/no_op_conservative_output.json")
    fixture = TailoringGoldenFixture.model_validate_json(
        fixture_path.read_text(encoding="utf-8")
    )
    fact = CandidateFact(
        id=CandidateFactId("fact-golden-resume"),
        statement=fixture.resume_text,
        provenance=EvidenceProvenance(
            evidence_span_ids=(EvidenceSpanId("span-golden-resume"),)
        ),
    )
    payload: dict[str, JsonValue] = {
        "protocol_version": "1.0",
        "schema_version": 1,
        "run_id": "run-golden-no-op",
        "source_hashes": {"resume": "a" * 64, "jd": "b" * 64},
        "template_hash": None,
        "strategy": "conservative",
        "rewritten_resume": fixture.proposal.rewritten_resume,
        "changes": [],
        "proposed_claims": [],
    }
    payload["proposal_hash"] = calculate_proposal_hash(payload)
    proposal = ResumeTailoringProposal.model_validate(payload)
    safety = evaluate_factual_safety(proposal, (fact,))
    adequacy = evaluate_optimization_adequacy(
        proposal,
        AdequacyContext(
            candidate_facts=(fact,),
            requirements=(),
            evidence_matches=(),
            baseline_covered_requirement_ids=frozenset(),
            baseline_resume_text=fixture.resume_text,
        ),
    )

    result = decide_validation_state(
        proposal,
        safety,
        adequacy,
        ValidationContext(current_source_hashes=dict(proposal.source_hashes)),
    )

    assert result.decision.outcome.value == fixture.expected_decision
    assert tuple(item.code for item in result.decision.findings) == fixture.expected_codes
    assert result.render_allowed
