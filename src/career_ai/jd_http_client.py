import ipaddress
import socket
import ssl
from typing import Final, Literal
from urllib.parse import ParseResult, urljoin, urlparse

from bs4 import BeautifulSoup

from career_ai.fetch_models import FetchFailure, HttpTextResult, HttpTextSuccess
from career_ai.models import FrozenModel

MAX_JD_BYTES: Final[int] = 200_000
MAX_REDIRECTS: Final[int] = 5
HTTP_TIMEOUT_SECONDS: Final[float] = 10.0
USER_AGENT: Final[str] = "AI-Career-Intelligence-Suite/0.1"
DEFAULT_HTTP_PORT: Final[int] = 80
DEFAULT_HTTPS_PORT: Final[int] = 443
REDIRECT_STATUS_MIN: Final[int] = 300
REDIRECT_STATUS_MAX: Final[int] = 399
ERROR_STATUS_MIN: Final[int] = 400
MIN_STATUS_PARTS: Final[int] = 2


class ResolvedEndpoint(FrozenModel):
    """Network endpoint whose address has already passed SSRF checks."""

    hostname: str
    address: str
    port: int
    scheme: Literal["http", "https"]


class HttpResponse(FrozenModel):
    """Minimal HTTP response representation for JD fetching."""

    status_code: int
    headers: dict[str, str]
    body: bytes


class RedirectTarget(FrozenModel):
    """Validated redirect target URL."""

    url: str


type ResolveResult = ResolvedEndpoint | FetchFailure
type SingleFetchResult = HttpResponse | FetchFailure
type SocketConnection = socket.socket | ssl.SSLSocket
type HandledResponse = HttpTextSuccess | RedirectTarget | FetchFailure


def fetch_http_text_with_redirects(url: str) -> HttpTextResult:
    """Fetch URL text while pinning DNS resolution to the actual connection."""
    current_url = url
    for _ in range(MAX_REDIRECTS + 1):
        result = _fetch_redirect_step(current_url)
        match result:
            case RedirectTarget(url=next_url):
                current_url = next_url
                continue
            case HttpTextSuccess() as success:
                return success
            case FetchFailure() as failure:
                return failure
    return FetchFailure(reason="network_error", message="The JD page redirected too many times.")


def _fetch_redirect_step(current_url: str) -> HandledResponse:
    parsed_url = urlparse(current_url)
    endpoint = _resolve_endpoint(parsed_url)
    match endpoint:
        case FetchFailure() as failure:
            return failure
        case ResolvedEndpoint() as resolved:
            response = _fetch_once(parsed_url.geturl(), resolved)
    match response:
        case FetchFailure() as failure:
            return failure
        case HttpResponse() as http_response:
            return _handle_http_response(current_url=current_url, response=http_response)


def _resolve_endpoint(parsed_url: ParseResult) -> ResolveResult:
    if parsed_url.scheme not in {"http", "https"}:
        return FetchFailure(reason="unsupported_scheme", message="Use an http or https URL.")
    if parsed_url.hostname is None:
        return FetchFailure(reason="blocked_host", message="This URL host is not allowed.")
    port = parsed_url.port or _default_port(parsed_url.scheme)
    hostname = parsed_url.hostname.strip().lower().rstrip(".")
    if _is_localhost_name(hostname):
        return FetchFailure(reason="blocked_host", message="This URL host is not allowed.")
    return _resolve_hostname(hostname=hostname, port=port, scheme=parsed_url.scheme)


def _resolve_hostname(*, hostname: str, port: int, scheme: str) -> ResolveResult:
    literal = _literal_ip_address(hostname)
    if literal is not None:
        return _endpoint_from_address(
            hostname=hostname,
            address=str(literal),
            port=port,
            scheme=scheme,
        )
    try:
        infos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return FetchFailure(reason="network_error", message="Could not resolve the JD page host.")
    addresses = sorted({str(info[4][0]) for info in infos})
    if not addresses:
        return FetchFailure(reason="network_error", message="Could not resolve the JD page host.")
    if any(_is_blocked_address(ipaddress.ip_address(address)) for address in addresses):
        return FetchFailure(reason="blocked_host", message="This URL host is not allowed.")
    return _endpoint_from_address(hostname=hostname, address=addresses[0], port=port, scheme=scheme)


def _endpoint_from_address(*, hostname: str, address: str, port: int, scheme: str) -> ResolveResult:
    ip_address = ipaddress.ip_address(address)
    if _is_blocked_address(ip_address):
        return FetchFailure(reason="blocked_host", message="This URL host is not allowed.")
    if scheme == "http":
        return ResolvedEndpoint(hostname=hostname, address=address, port=port, scheme="http")
    if scheme == "https":
        return ResolvedEndpoint(hostname=hostname, address=address, port=port, scheme="https")
    return FetchFailure(reason="unsupported_scheme", message="Use an http or https URL.")


def _fetch_once(url: str, endpoint: ResolvedEndpoint) -> SingleFetchResult:
    try:
        connection = _open_connection(endpoint)
        try:
            connection.sendall(_build_http_request(url, endpoint.hostname, endpoint.port))
            return _read_http_response(connection)
        finally:
            connection.close()
    except (OSError, ssl.SSLError):
        return FetchFailure(reason="network_error", message="Could not fetch the JD page.")


def _open_connection(endpoint: ResolvedEndpoint) -> SocketConnection:
    raw_socket = socket.create_connection(
        (endpoint.address, endpoint.port),
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    if endpoint.scheme == "https":
        context = ssl.create_default_context()
        return context.wrap_socket(raw_socket, server_hostname=endpoint.hostname)
    return raw_socket


def _build_http_request(url: str, hostname: str, port: int) -> bytes:
    parsed_url = urlparse(url)
    target = parsed_url.path or "/"
    if parsed_url.query:
        target = f"{target}?{parsed_url.query}"
    host_header = _host_header(hostname=hostname, port=port, scheme=parsed_url.scheme)
    request = (
        f"GET {target} HTTP/1.1\r\n"
        f"Host: {host_header}\r\n"
        f"User-Agent: {USER_AGENT}\r\n"
        "Accept: text/html, text/plain;q=0.9, */*;q=0.1\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    return request.encode("ascii")


def _host_header(*, hostname: str, port: int, scheme: str) -> str:
    if scheme == "http" and port == DEFAULT_HTTP_PORT:
        return hostname
    if scheme == "https" and port == DEFAULT_HTTPS_PORT:
        return hostname
    return f"{hostname}:{port}"


def _read_http_response(connection: SocketConnection) -> SingleFetchResult:
    response = bytearray()
    while True:
        chunk = connection.recv(8192)
        if not chunk:
            break
        response.extend(chunk)
        if len(response) > MAX_JD_BYTES:
            return FetchFailure(reason="content_too_large", message="The JD content is too large.")
    if not response:
        return FetchFailure(
            reason="empty_content",
            message="The page did not contain readable text.",
        )
    return _parse_http_response(bytes(response))


def _parse_http_response(raw_response: bytes) -> SingleFetchResult:
    header_bytes, separator, body = raw_response.partition(b"\r\n\r\n")
    if not separator:
        return FetchFailure(reason="network_error", message="Could not parse the JD page response.")
    header_lines = header_bytes.decode("iso-8859-1", errors="replace").split("\r\n")
    status_code = _status_code(header_lines[0])
    if status_code is None:
        return FetchFailure(reason="network_error", message="Could not parse the JD page response.")
    return HttpResponse(
        status_code=status_code,
        headers=_headers_from_lines(header_lines[1:]),
        body=body,
    )


def _status_code(status_line: str) -> int | None:
    parts = status_line.split()
    if len(parts) < MIN_STATUS_PARTS:
        return None
    try:
        return int(parts[1])
    except ValueError:
        return None


def _headers_from_lines(lines: list[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in lines:
        if ":" in line:
            key, value = line.split(":", maxsplit=1)
            headers[key.strip().lower()] = value.strip()
    return headers


def _handle_http_response(current_url: str, response: HttpResponse) -> HandledResponse:
    if REDIRECT_STATUS_MIN <= response.status_code <= REDIRECT_STATUS_MAX:
        return _handle_redirect(current_url=current_url, headers=response.headers)
    if response.status_code >= ERROR_STATUS_MIN:
        return FetchFailure(reason="network_error", message="Could not fetch the JD page.")
    text = _extract_html_text(response.body.decode("utf-8", errors="replace"))
    if text:
        return HttpTextSuccess(text=text)
    return FetchFailure(reason="empty_content", message="The page did not contain readable text.")


def _handle_redirect(*, current_url: str, headers: dict[str, str]) -> RedirectTarget | FetchFailure:
    next_url = _redirect_target(current_url, headers)
    if next_url is None:
        return FetchFailure(
            reason="network_error",
            message="Could not follow the JD page redirect.",
        )
    return RedirectTarget(url=next_url)


def _redirect_target(current_url: str, headers: dict[str, str]) -> str | None:
    location = headers.get("location")
    if location is None:
        return None
    return urljoin(current_url, location)


def _default_port(scheme: str) -> int:
    if scheme == "https":
        return DEFAULT_HTTPS_PORT
    return DEFAULT_HTTP_PORT


def _literal_ip_address(hostname: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(hostname.strip("[]"))
    except ValueError:
        return None


def _is_localhost_name(hostname: str) -> bool:
    return hostname in {"localhost", "0"} or hostname.endswith(".localhost")


def _is_blocked_address(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_unspecified
        or address.is_multicast
        or address.is_reserved
    )


def _extract_html_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "title", "nav", "footer"]):
        element.decompose()
    text = soup.get_text(separator=" ")
    return " ".join(text.split())
