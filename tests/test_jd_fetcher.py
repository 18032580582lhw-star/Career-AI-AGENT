import socket

from _pytest.monkeypatch import MonkeyPatch
from pydantic import BaseModel

from career_ai.jd_fetcher import FetchFailure, FetchSuccess, fetch_job_description_from_url


def test_fetch_job_description_from_url_extracts_visible_html_text() -> None:
    html_url = (
        "data:text/html,"
        "<html><title>Hidden</title><body><h1>AI Analyst</h1>"
        "<p>Python SQL LLM evaluation</p></body></html>"
    )
    result = fetch_job_description_from_url(
        html_url,
    )

    assert isinstance(result, FetchSuccess)
    assert "AI Analyst" in result.text
    assert "Python SQL LLM evaluation" in result.text


def test_fetch_job_description_from_url_rejects_non_http_and_non_data_urls() -> None:
    result = fetch_job_description_from_url("ftp://example.com/job")

    assert isinstance(result, FetchFailure)
    assert result.reason == "unsupported_scheme"


def test_fetch_job_description_from_url_blocks_loopback_hosts_before_network() -> None:
    result = fetch_job_description_from_url("http://127.0.0.1/admin")

    assert isinstance(result, FetchFailure)
    assert result.reason == "blocked_host"


def test_fetch_job_description_from_url_rejects_oversized_data_urls() -> None:
    result = fetch_job_description_from_url(f"data:text/html,{'x' * 200_001}")

    assert isinstance(result, FetchFailure)
    assert result.reason == "content_too_large"


def test_fetch_results_are_pydantic_models() -> None:
    result = fetch_job_description_from_url("ftp://example.com/job")

    assert isinstance(result, BaseModel)


def test_fetch_job_description_from_url_returns_failure_for_unresolvable_host(
    monkeypatch: MonkeyPatch,
) -> None:
    def fail_resolution(
        _host: str,
        _port: int | None,
        **kwargs: socket.SocketKind,
    ) -> list[tuple[socket.AddressFamily, socket.SocketKind, int, str, tuple[str, int]]]:
        assert kwargs["type"] == socket.SOCK_STREAM
        message = "forced DNS failure"
        raise socket.gaierror(message)

    monkeypatch.setattr(socket, "getaddrinfo", fail_resolution)

    result = fetch_job_description_from_url("http://missing.example/job")

    assert isinstance(result, FetchFailure)
    assert result.reason == "network_error"


def test_fetch_job_description_from_url_connects_to_pinned_resolved_address(
    monkeypatch: MonkeyPatch,
) -> None:
    connected_addresses: list[tuple[str, int]] = []

    class FakeSocket:
        def __init__(self) -> None:
            self._chunks: list[bytes] = [
                b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<p>Pinned JD text</p>",
                b"",
            ]

        def sendall(self, data: bytes) -> None:
            assert b"Host: careers.example" in data

        def recv(self, size: int) -> bytes:
            _ = size
            return self._chunks.pop(0)

        def close(self) -> None:
            return None

    def resolve_public_address(
        host: str,
        port: int | None,
        **kwargs: socket.SocketKind,
    ) -> list[tuple[socket.AddressFamily, socket.SocketKind, int, str, tuple[str, int]]]:
        assert host == "careers.example"
        assert port == 80
        assert kwargs["type"] == socket.SOCK_STREAM
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))]

    def connect_to_pinned_address(
        address: tuple[str, int],
        timeout: float,
    ) -> FakeSocket:
        assert timeout == 10.0
        connected_addresses.append(address)
        return FakeSocket()

    monkeypatch.setattr(socket, "getaddrinfo", resolve_public_address)
    monkeypatch.setattr(socket, "create_connection", connect_to_pinned_address)

    result = fetch_job_description_from_url("http://careers.example/job")

    assert isinstance(result, FetchSuccess)
    assert result.text == "Pinned JD text"
    assert connected_addresses == [("93.184.216.34", 80)]
