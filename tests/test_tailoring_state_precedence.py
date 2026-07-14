"""Cross-harness validation-state precedence regressions."""

from career_ai.tailoring.manifest_contracts import RunState
from career_ai.tailoring.proposal_contracts import ValidationOutcome
from tests.test_tailoring_state_machine import (
    adequacy_result,
    decide,
    finding,
    safety_result,
)


def test_adequacy_error_takes_precedence_over_confirmation_warning() -> None:
    state, outcome, repair_allowed, _ = decide(
        safety_result(finding(warning=True)),
        adequacy_result(finding()),
    )

    assert (state, outcome, repair_allowed) == (
        RunState.REJECTED,
        ValidationOutcome.REJECTED,
        True,
    )
