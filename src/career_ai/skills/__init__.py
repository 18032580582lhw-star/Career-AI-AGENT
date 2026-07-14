"""Packaged host skills for Career AI workflows."""

from career_ai.skills.installation import (
    HostAgent,
    SkillInstallationResult,
    canonical_skill_digest,
    canonical_skill_root,
    install_host_skills,
)

__all__ = [
    "HostAgent",
    "SkillInstallationResult",
    "canonical_skill_digest",
    "canonical_skill_root",
    "install_host_skills",
]
