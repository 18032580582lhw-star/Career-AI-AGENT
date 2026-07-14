"""Evidence-joined optimization adequacy harness."""

from __future__ import annotations

from hashlib import sha256

from career_ai.tailoring.adequacy_models import (
    AdequacyContext,
    AdequacyHarnessResult,
    AdequacyViolationCode,
)
from career_ai.tailoring.adequacy_rules import (
    coverage_score,
    has_keyword_stuffing,
    has_readability_regression,
    is_material_change,
)
from career_ai.tailoring.models import EvidenceRequirementMatch, MatchStatus, RequirementPriority
from career_ai.tailoring.proposal_contracts import (
    ResumeTailoringProposal,
    ValidationFinding,
    ValidationSeverity,
)

_MIN_RELEVANT_FACTS = 2


def evaluate_optimization_adequacy(
    proposal: ResumeTailoringProposal,
    context: AdequacyContext,
) -> AdequacyHarnessResult:
    """Measure only coverage gains proven by fact-to-requirement matches."""
    findings: list[ValidationFinding] = []
    fact_ids = tuple(str(fact.id) for fact in context.candidate_facts)
    requirement_ids = tuple(str(requirement.id) for requirement in context.requirements)
    match_ids = tuple(str(item.id) for item in context.evidence_matches)
    _append_duplicate_findings(findings, fact_ids, requirement_ids, match_ids)
    facts = set(fact_ids)
    known_requirements = set(requirement_ids)
    required_ids = {
        str(requirement.id)
        for requirement in context.requirements
        if requirement.priority is RequirementPriority.REQUIRED
    }
    if context.baseline_covered_requirement_ids - required_ids:
        _append_finding(findings, AdequacyViolationCode.INVALID_BASELINE_REFERENCE)
    _append_unknown_change_requirement_findings(
        findings,
        proposal,
        known_requirements,
    )
    valid_matches = tuple(
        item
        for item in context.evidence_matches
        if _match_is_valid(item, facts, known_requirements, findings)
    )
    opportunity_facts = _opportunity_facts(valid_matches, required_ids)
    baseline = context.baseline_covered_requirement_ids & required_ids
    uncovered_opportunities = set(opportunity_facts) - baseline
    projected = baseline | _projected_coverage(proposal, opportunity_facts)
    total = len(required_ids)
    baseline_score = coverage_score(len(baseline), total)
    projected_score = coverage_score(len(projected), total)
    high_coverage = total == 0 or 10 * len(baseline) >= 9 * total
    optimization_required = not high_coverage and bool(uncovered_opportunities)
    gain_sufficient = total == 0 or 10 * total <= 100 * (len(projected) - len(baseline))
    if optimization_required and not gain_sufficient:
        _append_finding(
            findings, AdequacyViolationCode.INSUFFICIENT_REQUIRED_COVERAGE_GAIN
        )
    if optimization_required and gain_sufficient and not _has_substantive_joined_change(
        proposal, opportunity_facts, uncovered_opportunities
    ):
        _append_finding(findings, AdequacyViolationCode.SUBSTANTIVE_REWRITE_REQUIRED)
    if has_keyword_stuffing(proposal.rewritten_resume, context.requirements):
        _append_finding(findings, AdequacyViolationCode.KEYWORD_STUFFING)
    if has_readability_regression(context.baseline_resume_text, proposal.rewritten_resume):
        _append_finding(findings, AdequacyViolationCode.READABILITY_REGRESSION)
    return AdequacyHarnessResult(
        run_id=proposal.run_id,
        proposal_hash=proposal.proposal_hash,
        passed=not findings,
        baseline_score=baseline_score,
        projected_score=projected_score,
        findings=tuple(findings),
    )


def _append_duplicate_findings(
    findings: list[ValidationFinding],
    fact_ids: tuple[str, ...],
    requirement_ids: tuple[str, ...],
    match_ids: tuple[str, ...],
) -> None:
    for ids, code in (
        (fact_ids, AdequacyViolationCode.DUPLICATE_CANDIDATE_FACT),
        (requirement_ids, AdequacyViolationCode.DUPLICATE_REQUIREMENT),
        (match_ids, AdequacyViolationCode.DUPLICATE_MATCH),
    ):
        if len(ids) != len(set(ids)):
            _append_finding(findings, code)


def _match_is_valid(
    item: EvidenceRequirementMatch,
    fact_ids: set[str],
    requirement_ids: set[str],
    findings: list[ValidationFinding],
) -> bool:
    valid = True
    if str(item.requirement_id) not in requirement_ids:
        _append_finding(findings, AdequacyViolationCode.UNKNOWN_REQUIREMENT_REFERENCE)
        valid = False
    if item.candidate_fact_id is None or str(item.candidate_fact_id) not in fact_ids:
        _append_finding(findings, AdequacyViolationCode.UNKNOWN_FACT_REFERENCE)
        valid = False
    return valid


def _append_unknown_change_requirement_findings(
    findings: list[ValidationFinding],
    proposal: ResumeTailoringProposal,
    known_requirements: set[str],
) -> None:
    for change in proposal.changes:
        if any(item not in known_requirements for item in change.target_requirement_ids):
            _append_finding(findings, AdequacyViolationCode.UNKNOWN_REQUIREMENT_REFERENCE)


def _opportunity_facts(
    matches: tuple[EvidenceRequirementMatch, ...],
    required_ids: set[str],
) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for item in matches:
        if (
            str(item.requirement_id) in required_ids
            and item.candidate_fact_id is not None
            and item.status in {MatchStatus.SUPPORTED, MatchStatus.CONFIRMED}
        ):
            result.setdefault(str(item.requirement_id), set()).add(
                str(item.candidate_fact_id)
            )
    return result


def _projected_coverage(
    proposal: ResumeTailoringProposal,
    opportunity_facts: dict[str, set[str]],
) -> set[str]:
    covered: set[str] = set()
    for change in proposal.changes:
        change_facts = set(change.source_fact_ids)
        for requirement_id in change.target_requirement_ids:
            if opportunity_facts.get(requirement_id, set()) & change_facts:
                covered.add(requirement_id)
    return covered


def _has_substantive_joined_change(
    proposal: ResumeTailoringProposal,
    opportunity_facts: dict[str, set[str]],
    uncovered_opportunities: set[str],
) -> bool:
    for change in proposal.changes:
        if not is_material_change(change.before, change.after):
            continue
        joined_facts = {
            fact_id
            for requirement_id in set(change.target_requirement_ids) & uncovered_opportunities
            for fact_id in opportunity_facts.get(requirement_id, set())
            if fact_id in change.source_fact_ids
        }
        if len(joined_facts) >= _MIN_RELEVANT_FACTS:
            return True
    return False


def _append_finding(
    findings: list[ValidationFinding],
    code: AdequacyViolationCode,
) -> None:
    if any(item.code == code.value for item in findings):
        return
    digest = sha256(code.value.encode()).hexdigest()[:12]
    findings.append(
        ValidationFinding(
            id=f"adequacy-{digest}",
            code=code.value,
            severity=ValidationSeverity.ERROR,
            message=code.value.replace("_", " "),
        )
    )
