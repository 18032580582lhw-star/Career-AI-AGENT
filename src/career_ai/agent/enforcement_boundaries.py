import ipaddress
from pathlib import Path
from urllib.parse import urlparse

from career_ai.agent.enforcement_models import RuntimeBoundary


def is_blocked_fetch_target(url: str) -> bool:
    """Return whether a public JD fetch target is locally unsafe."""
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    if hostname is None:
        return True
    return _is_blocked_host_name(hostname) or _is_blocked_literal_address(hostname)


def is_suspicious_export_path(path: Path) -> bool:
    """Return whether a document export path targets sensitive locations."""
    path_text = str(path).lower()
    return ".." in path.parts or ".ssh" in path_text or "credentials" in path_text


def reason_boundary_label(boundary: RuntimeBoundary) -> str:
    """Return compact policy-event reason text for a boundary."""
    match boundary:
        case RuntimeBoundary.PRE_TOOL_CALL:
            return "pre-tool"
        case RuntimeBoundary.POST_TOOL_CALL:
            return "post-tool"
        case (
            RuntimeBoundary.MEMORY_WRITE
            | RuntimeBoundary.NETWORK_FETCH
            | RuntimeBoundary.DOCUMENT_EXPORT
            | RuntimeBoundary.EXTERNAL_ACTION
        ):
            return boundary.value


def _is_blocked_host_name(hostname: str) -> bool:
    normalized = hostname.strip().lower().rstrip(".")
    return normalized in {"localhost", "0"} or normalized.endswith(".localhost")


def _is_blocked_literal_address(hostname: str) -> bool:
    try:
        address = ipaddress.ip_address(hostname.strip("[]"))
    except ValueError:
        return False
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_unspecified
        or address.is_multicast
        or address.is_reserved
    )
