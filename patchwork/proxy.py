"""Proxy fallback support: forward unmatched requests to an upstream URL."""

from __future__ import annotations

import http.client
import urllib.parse
from typing import Optional


class ProxyError(Exception):
    """Raised when the proxy request cannot be completed."""


def _parse_upstream(upstream: str) -> tuple[str, str, bool]:
    """Return (host, base_path, use_ssl) from an upstream URL string."""
    parsed = urllib.parse.urlparse(upstream)
    if parsed.scheme not in ("http", "https"):
        raise ProxyError(f"Unsupported scheme '{parsed.scheme}'; expected http or https")
    use_ssl = parsed.scheme == "https"
    host = parsed.netloc
    if not host:
        raise ProxyError(f"Missing host in upstream URL: {upstream!r}")
    base_path = parsed.path.rstrip("/")
    return host, base_path, use_ssl


def forward_request(
    upstream: str,
    method: str,
    path: str,
    headers: dict[str, str],
    body: Optional[bytes] = None,
    timeout: float = 10.0,
) -> tuple[int, dict[str, str], bytes]:
    """Forward *method* + *path* to *upstream* and return (status, headers, body).

    Parameters
    ----------
    upstream:  Base URL of the upstream server, e.g. ``"https://api.example.com"``.
    method:    HTTP method (GET, POST, …).
    path:      Request path including query string.
    headers:   Request headers to forward (hop-by-hop headers are stripped).
    body:      Optional request body bytes.
    timeout:   Socket timeout in seconds.
    """
    host, base_path, use_ssl = _parse_upstream(upstream)
    target = base_path + path

    # Strip hop-by-hop headers that must not be forwarded.
    _HOP_BY_HOP = {"connection", "keep-alive", "proxy-authenticate",
                   "proxy-authorization", "te", "trailers",
                   "transfer-encoding", "upgrade"}
    safe_headers = {k: v for k, v in headers.items()
                    if k.lower() not in _HOP_BY_HOP}

    try:
        conn_cls = http.client.HTTPSConnection if use_ssl else http.client.HTTPConnection
        conn = conn_cls(host, timeout=timeout)
        conn.request(method.upper(), target, body=body, headers=safe_headers)
        resp = conn.getresponse()
        resp_body = resp.read()
        resp_headers = {k: v for k, v in resp.getheaders()}
        return resp.status, resp_headers, resp_body
    except OSError as exc:
        raise ProxyError(f"Connection to upstream '{host}' failed: {exc}") from exc
    finally:
        conn.close()
