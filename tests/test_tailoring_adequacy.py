from __future__ import annotations

import pytest
from pydantic import ValidationError

from career_ai.tailoring.adequacy_models import AdequacyContext
from career_ai.tailoring.models import MatchStatus
from tests.adequacy_helpers import (
    ProposalSpec,
)
from tests.adequacy_helpers import (
    context as _context,
)
from tests.adequacy_helpers import (
    evaluate as _evaluate,
)
from tests.adequacy_helpers import (
    evidence_match as _match,
)
from tests.adequacy_helpers import (
    facts as _facts,
)
from tests.adequacy_helpers import (
    proposal as _proposal,
)
from tests.adequacy_helpers import (
    requirements as _requirements,
)


def test_evidence_join_can_prove_ten_point_required_coverage_gain() -> None:
    result = _evaluate(
        _proposal(),
        _context(
            2,
            10,
            (_match(6, 1), _match(6, 2)),
            frozenset(f"requirement-{index}" for index in range(1, 6)),
        ),
    )

    assert result == (True, 50, 60, ())


def test_arbitrary_target_label_cannot_manufacture_coverage_gain() -> None:
    result = _evaluate(
        _proposal(),
        _context(
            2,
            10,
            (_match(7, 1), _match(7, 2)),
            frozenset(f"requirement-{index}" for index in range(1, 6)),
        ),
    )

    assert result[3] == ("insufficient_required_coverage_gain",)


def test_optimization_requires_two_relevant_facts_when_opportunity_exists() -> None:
    result = _evaluate(
        _proposal(ProposalSpec(fact_ids=("fact-1",))),
        _context(
            2,
            10,
            (_match(6, 1), _match(6, 2)),
            frozenset(f"requirement-{index}" for index in range(1, 6)),
        ),
    )

    assert result[3] == ("substantive_rewrite_required",)


def test_high_coverage_allows_accepted_no_op_proposal() -> None:
    proposal = _proposal(
        ProposalSpec(
            include_change=False,
            rewritten_resume="Engineer\nBuilt Python workflow 1.",
        )
    )
    result = _evaluate(
        proposal,
        _context(
            2,
            10,
            (_match(10, 1),),
            frozenset(f"requirement-{index}" for index in range(1, 10)),
        ),
    )

    assert result == (True, 90, 90, ())


def test_no_evidence_backed_gap_does_not_force_rewrite() -> None:
    result = _evaluate(
        _proposal(ProposalSpec(include_change=False)),
        _context(
            2,
            10,
            (),
            frozenset(f"requirement-{index}" for index in range(1, 6)),
        ),
    )

    assert result[3] == ()


def test_meaningful_jd_keyword_stuffing_is_rejected() -> None:
    result = _evaluate(
        _proposal(ProposalSpec(rewritten_resume="Python Python Python Python Python Python")),
        _context(
            2,
            10,
            (_match(6, 1), _match(6, 2)),
            frozenset(f"requirement-{index}" for index in range(1, 6)),
        ),
    )

    assert result[3] == ("keyword_stuffing",)


def test_readability_regression_is_rejected() -> None:
    unreadable = "Engineer\n" + ("word " * 70)
    result = _evaluate(
        _proposal(ProposalSpec(rewritten_resume=unreadable)),
        _context(
            2,
            10,
            (_match(6, 1), _match(6, 2)),
            frozenset(f"requirement-{index}" for index in range(1, 6)),
        ),
    )

    assert result[3] == ("readability_regression",)


def test_unknown_match_reference_is_rejected() -> None:
    result = _evaluate(
        _proposal(),
        _context(
            2,
            10,
            (_match(11, 1),),
            frozenset(f"requirement-{index}" for index in range(1, 6)),
        ),
    )

    assert result[3][0] == "unknown_requirement_reference"


def test_needs_confirmation_match_cannot_count_as_coverage() -> None:
    result = _evaluate(
        _proposal(),
        _context(
            2,
            10,
            (
                _match(6, 1, MatchStatus.NEEDS_CONFIRMATION),
                _match(6, 2, MatchStatus.NEEDS_CONFIRMATION),
            ),
            frozenset(f"requirement-{index}" for index in range(1, 6)),
        ),
    )

    assert result[3] == ()
    assert result[2] == 50


def test_eight_of_nine_is_below_exact_ninety_percent_threshold() -> None:
    result = _evaluate(
        _proposal(ProposalSpec(include_change=False)),
        _context(
            2,
            9,
            (_match(9, 1), _match(9, 2)),
            frozenset(f"requirement-{index}" for index in range(1, 9)),
        ),
    )

    assert result[3] == ("insufficient_required_coverage_gain",)


def test_two_arbitrary_facts_do_not_satisfy_relevant_fact_requirement() -> None:
    result = _evaluate(
        _proposal(),
        _context(
            2,
            10,
            (_match(6, 1), _match(7, 2)),
            frozenset(f"requirement-{index}" for index in range(1, 6)),
        ),
    )

    assert result[3] == ("substantive_rewrite_required",)


def test_duplicate_candidate_fact_ids_are_rejected() -> None:
    duplicate = (_facts(1)[0], _facts(1)[0])
    context = AdequacyContext(
        candidate_facts=duplicate,
        requirements=_requirements(10),
        evidence_matches=(_match(6, 1),),
        baseline_covered_requirement_ids=frozenset(
            f"requirement-{index}" for index in range(1, 6)
        ),
        baseline_resume_text="Engineer\nBuilt Python workflow 1.",
    )

    assert _evaluate(_proposal(), context)[3][0] == "duplicate_candidate_fact"


def test_whitespace_only_rewritten_resume_is_rejected_at_boundary() -> None:
    with pytest.raises(ValidationError, match="rewritten_resume"):
        _ = _proposal(ProposalSpec(rewritten_resume="   "))
