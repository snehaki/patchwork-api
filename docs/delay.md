# Response Delay

Patchwork supports simulating slow responses by adding a `delay` field to any
route definition. This is useful for testing timeout handling and loading states
in client applications.

## Usage

Add a `delay` key (in seconds) to a YAML response definition:

```yaml
method: GET
path: /slow-endpoint
status: 200
delay: 1.5
body:
  message: "This response was delayed by 1.5 seconds"
```

## Rules

- `delay` is optional. Omitting it (or setting it to `0`) means no delay.
- The value must be a non-negative number (`int` or `float`).
- Negative values or non-numeric types raise a `DelayError` at load time.

## Examples

### No delay (default)

```yaml
method: GET
path: /fast
status: 200
body:
  ok: true
```

### 500 ms delay

```yaml
method: POST
path: /submit
status: 202
delay: 0.5
body:
  queued: true
```

### 3 second delay (simulate timeout scenario)

```yaml
method: GET
path: /timeout-test
status: 200
delay: 3
body:
  result: "finally"
```

## Integration

The delay is applied inside `build_response` via `apply_delay` before the
response bytes are returned to the server handler. The delay value is extracted
from the definition using `get_response_delay`.
