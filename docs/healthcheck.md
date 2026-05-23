# Health-Check Endpoint

Patchwork exposes a built-in management route at:

```
GET /__patchwork/health
```

This endpoint requires **no YAML definition** — it is handled automatically by
the server before route matching occurs.

---

## Response

```json
{
  "status": "ok",
  "uptime_seconds": 42.7,
  "route_count": 15
}
```

| Field | Type | Description |
|---|---|---|
| `status` | string | Always `"ok"` while the server is running. |
| `uptime_seconds` | float | Seconds since the server process started. |
| `route_count` | int | Number of routes currently registered. |

---

## Usage

Query the endpoint with any HTTP client:

```bash
curl http://localhost:8080/__patchwork/health
```

Or use it as a liveness probe in Docker / Kubernetes:

```yaml
# docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/__patchwork/health"]
  interval: 10s
  timeout: 3s
  retries: 3
```

---

## Error Responses

| Status | Reason |
|---|---|
| `405 Method Not Allowed` | Any method other than `GET` was used. |

---

## Integration with `server.py`

The handler is invoked inside `_handle_request` **before** the registry lookup,
so it always responds even when no YAML files are loaded:

```python
from patchwork.healthcheck import handle_health_request

response = handle_health_request(method, path, registry=self.registry)
if response is not None:
    # send response and return
```
