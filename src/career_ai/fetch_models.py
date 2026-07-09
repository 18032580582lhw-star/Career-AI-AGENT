from typing import Literal

from career_ai.models import FrozenModel

type FetchFailureReason = Literal[
    "unsupported_scheme",
    "blocked_host",
    "network_error",
    "empty_content",
    "content_too_large",
]


class FetchSuccess(FrozenModel):
    """Successful JD URL extraction."""

    text: str
    source_url: str


class FetchFailure(FrozenModel):
    """Expected JD fetch failure for UI fallback."""

    reason: FetchFailureReason
    message: str


class HttpTextSuccess(FrozenModel):
    """Successful low-level HTTP text extraction."""

    text: str


type FetchResult = FetchSuccess | FetchFailure
type HttpTextResult = HttpTextSuccess | FetchFailure

