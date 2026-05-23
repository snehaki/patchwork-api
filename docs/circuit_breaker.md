# Circuit Breaker

Patchwork includes a lightweight **circuit breaker** that protects proxy
upstreams from cascading failures.  When an upstream accumulates too many
consecutive errors the circuit *opens*, and further requests are rejected
immediately rather than waiting for a slow or dead server.

## States

| State | Meaning |
|------------|----------------------------------------------------------|
| `closed` | Normal operation – all requests pass through. |
| `open` | Upstream is unhealthy – requests are blocked. |
| `half-open`| Timeout elapsed – one probe request is allowed through. |

## API

```python
from patchwork.circuit_breaker import (
    record_success, record_failure, is_allowed, get_state, reset
)

key = "payments-service"  # arbitrary string identifying the upstream

# Before forwarding a request
if not is_allowed(key, timeout=30.0):
    # return 503 immediately
    ...

try:
    response = forward_request(...)
    record_success(key)
except Exception:
    record_failure(key, threshold=3)
```

## Parameters

### `record_failure(key, threshold=3)`

Increment the failure counter for `key`.  When the counter reaches
`threshold` the circuit transitions from `closed` → `open`.

### `record_success(key)`

Reset the failure counter and return the circuit to `closed` regardless
of its current state.

### `is_allowed(key, timeout=30.0)`

Return `True` when the circuit is `closed` or `half-open`.  A circuit
moves from `open` → `half-open` once `timeout` seconds have elapsed
since it was opened.

### `reset(key)` / `reset_all()`

Fully reset one or all circuits.  Mainly useful in tests.

## YAML integration (coming soon)

A future release will allow per-route circuit-breaker configuration:

```yaml
method: GET
path: /orders
proxy:
  upstream: http://orders-service
  circuit_breaker:
    threshold: 5
    timeout: 60
status: 200
body: {}
```
