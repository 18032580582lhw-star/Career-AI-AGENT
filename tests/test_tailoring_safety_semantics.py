"""Adversarial semantic safety regressions."""

from career_ai.tailoring.models import MatchStatus
from tests.test_tailoring_safety import evaluate, fact, proposal


def test_negated_evidence_cannot_be_rewritten_as_positive_claim() -> None:
    source_fact = fact("fact-aws", "No AWS experience.")
    candidate = proposal(
        after="AWS experience.",
        fact_ids=("fact-aws",),
        claim_status=MatchStatus.SUPPORTED,
    )

    assert evaluate(candidate, (source_fact,)) == (False, ("unsupported_claim",))


def test_metrics_cannot_be_swapped_between_business_outcomes() -> None:
    source_fact = fact("fact-metrics", "Reduced latency 10% and costs 50%.")
    candidate = proposal(
        after="Reduced latency 50% and costs 10%.",
        fact_ids=("fact-metrics",),
        claim_status=MatchStatus.SUPPORTED,
    )

    assert evaluate(candidate, (source_fact,)) == (False, ("unsupported_claim",))


def test_long_negation_scope_cannot_be_dropped() -> None:
    source_fact = fact("fact-aws-long", "No hands-on production AWS experience.")
    candidate = proposal(
        after="AWS experience.",
        fact_ids=("fact-aws-long",),
        claim_status=MatchStatus.SUPPORTED,
    )

    assert evaluate(candidate, (source_fact,)) == (False, ("unsupported_claim",))


def test_metric_bindings_ignore_by_phrases() -> None:
    source_fact = fact(
        "fact-metrics-by",
        "Reduced API latency by 10% and infrastructure costs by 50%.",
    )
    candidate = proposal(
        after="Reduced API latency by 50% and infrastructure costs by 10%.",
        fact_ids=("fact-metrics-by",),
        claim_status=MatchStatus.SUPPORTED,
    )

    assert evaluate(candidate, (source_fact,)) == (False, ("unsupported_claim",))
