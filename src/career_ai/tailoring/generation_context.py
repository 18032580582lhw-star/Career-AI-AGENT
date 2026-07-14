"""Build trusted generation context from legacy resume and JD text inputs."""

from __future__ import annotations

from hashlib import sha256
from typing import assert_never

from career_ai.tailoring.candidate_extractor import extract_candidate_facts
from career_ai.tailoring.extraction_shared import ArtifactPrefix, stable_artifact_id
from career_ai.tailoring.extraction_types import ResumeFactSource
from career_ai.tailoring.generation_models import TailoringGenerationContext
from career_ai.tailoring.jd_extractor import extract_jd_requirements
from career_ai.tailoring.models import (
    CandidateFact,
    EvidenceProvenance,
    EvidenceRequirementMatch,
    FactRequirementMatchId,
    JDRequirement,
    MatchStatus,
    RequirementPriority,
    SourceArtifactId,
    UserConfirmationProvenance,
)
from career_ai.text_processing import extract_keywords


def build_generation_context(
    *,
    resume_text: str,
    jd_text: str,
    run_id: str,
) -> TailoringGenerationContext:
    """Convert legacy text inputs into provenance-bound strategy inputs."""
    resume_id = SourceArtifactId("legacy-resume")
    jd_id = SourceArtifactId("legacy-jd")
    fact_extraction = extract_candidate_facts(
        resume_text,
        ResumeFactSource(artifact_id=resume_id),
    )
    requirement_extraction = extract_jd_requirements(jd_text, jd_id)
    facts = tuple(item.fact for item in fact_extraction.facts)
    requirements = tuple(item.requirement for item in requirement_extraction.requirements)
    matches = _evidence_matches(facts, requirements)
    return TailoringGenerationContext(
        run_id=run_id,
        source_hashes={"resume": _sha256(resume_text), "jd": _sha256(jd_text)},
        baseline_resume_text=resume_text,
        candidate_facts=facts,
        requirements=requirements,
        evidence_matches=matches,
        baseline_covered_requirement_ids=frozenset(
            str(item.requirement_id)
            for item in matches
            if _is_required_requirement(item.requirement_id, requirements)
        ),
    )


def _evidence_matches(
    facts: tuple[CandidateFact, ...],
    requirements: tuple[JDRequirement, ...],
) -> tuple[EvidenceRequirementMatch, ...]:
    matches: list[EvidenceRequirementMatch] = []
    for requirement in requirements:
        requirement_terms = set(extract_keywords(requirement.statement))
        for fact in facts:
            if not requirement_terms & set(extract_keywords(fact.statement)):
                continue
            match fact.provenance:
                case EvidenceProvenance(evidence_span_ids=evidence_span_ids):
                    match_id = FactRequirementMatchId(
                        stable_artifact_id(
                            ArtifactPrefix("match"),
                            requirement.id,
                            fact.id,
                        )
                    )
                    matches.append(
                        EvidenceRequirementMatch(
                            id=match_id,
                            requirement_id=requirement.id,
                            candidate_fact_id=fact.id,
                            evidence_span_ids=evidence_span_ids,
                            status=MatchStatus.SUPPORTED,
                        )
                    )
                case UserConfirmationProvenance():
                    continue
                case _:
                    assert_never(fact.provenance)
    return tuple(matches)


def _is_required_requirement(
    requirement_id: str,
    requirements: tuple[JDRequirement, ...],
) -> bool:
    return any(
        str(item.id) == requirement_id and item.priority is RequirementPriority.REQUIRED
        for item in requirements
    )


def _sha256(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()
