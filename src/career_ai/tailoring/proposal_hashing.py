"""Canonical hashing for resume-tailoring proposals."""

from collections.abc import Mapping

from pydantic import JsonValue

from career_ai.tailoring.contract_base import canonical_json_hash


def calculate_proposal_hash(payload: Mapping[str, JsonValue]) -> str:
    """Hash proposal data while always excluding any supplied hash field."""
    hash_payload = {key: value for key, value in payload.items() if key != "proposal_hash"}
    return canonical_json_hash(hash_payload)
