from typing import Final
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

from career_ai.fetch_models import FetchFailure, FetchResult, FetchSuccess, HttpTextSuccess
from career_ai.jd_http_client import MAX_JD_BYTES, fetch_http_text_with_redirects

DATA_SOURCE_URL: Final[str] = "data:job-description"

__all__ = [
    "FetchFailure",
    "FetchResult",
    "FetchSuccess",
    "fetch_job_description_from_url",
]


def fetch_job_description_from_url(url: str) -> FetchResult:
    """Fetch and extract readable JD text from a supported URL."""
    parsed_url = urlparse(url)
    if parsed_url.scheme == "data":
        return _fetch_from_data_url(data_path=parsed_url.path)
    if parsed_url.scheme not in {"http", "https"}:
        return FetchFailure(reason="unsupported_scheme", message="Use an http or https URL.")
    result = fetch_http_text_with_redirects(url)
    match result:
        case HttpTextSuccess(text=text):
            return FetchSuccess(text=text, source_url=url)
        case FetchFailure() as failure:
            return failure


def _fetch_from_data_url(data_path: str) -> FetchResult:
    if len(data_path.encode("utf-8")) > MAX_JD_BYTES:
        return FetchFailure(reason="content_too_large", message="The JD content is too large.")
    payload = data_path.split(",", maxsplit=1)[1] if "," in data_path else data_path
    text = _extract_html_text(unquote(payload))
    if text:
        return FetchSuccess(text=text, source_url=DATA_SOURCE_URL)
    return FetchFailure(reason="empty_content", message="The URL did not contain readable text.")


def _extract_html_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "title", "nav", "footer"]):
        element.decompose()
    text = soup.get_text(separator=" ")
    return " ".join(text.split())
