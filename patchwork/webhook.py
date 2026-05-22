"""Webhook support: fire outbound HTTP requests when a route is matched."""

import json
import threading
import urllib.request
import urllib.error
from typing import Any, Dict, Optional


class WebhookError(Exception):
    """Raised when a webhook definition is invalid."""


def parse_webhook(definition: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract and validate the optional 'webhook' block from a route definition.

    Returns the webhook config dict, or None if no webhook is defined.
    Raises WebhookError for invalid configurations.
    """
    webhook = definition.get("webhook")
    if webhook is None:
        return None

    if not isinstance(webhook, dict):
        raise WebhookError("'webhook' must be a mapping")

    url = webhook.get("url")
    if not url:
        raise WebhookError("'webhook.url' is required")
    if not isinstance(url, str):
        raise WebhookError("'webhook.url' must be a string")
    if not url.startswith(("http://", "https://")):
        raise WebhookError("'webhook.url' must start with http:// or https://")

    method = webhook.get("method", "POST").upper()
    if method not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        raise WebhookError(f"'webhook.method' unsupported value: {method!r}")

    return {
        "url": url,
        "method": method,
        "headers": webhook.get("headers") or {},
        "body": webhook.get("body"),
        "async": bool(webhook.get("async", True)),
    }


def _fire(config: Dict[str, Any], context: Dict[str, Any]) -> None:
    """Perform the outbound HTTP request (runs in the calling thread or a daemon thread)."""
    url = config["url"]
    method = config["method"]
    body = config.get("body")

    data: Optional[bytes] = None
    headers = {k: str(v) for k, v in (config.get("headers") or {}).items()}

    if body is not None:
        payload = body if isinstance(body, str) else json.dumps(body)
        data = payload.encode()
        headers.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5):
            pass
    except urllib.error.URLError:
        pass  # fire-and-forget; errors are silently swallowed


def fire_webhook(config: Dict[str, Any], context: Dict[str, Any]) -> None:
    """Dispatch the webhook, optionally in a background thread."""
    if config.get("async", True):
        t = threading.Thread(target=_fire, args=(config, context), daemon=True)
        t.start()
    else:
        _fire(config, context)
