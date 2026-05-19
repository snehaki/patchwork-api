# Middleware

Patchwork supports a lightweight middleware system that lets you inspect or
short-circuit requests **before** they reach the route registry.

## Concepts

| Class | Purpose |
|---|---|
| `RequestContext` | Immutable-ish bag of request data (method, path, headers, body, meta) |
| `ResponseContext` | Bag of response data (status, headers, body) |
| `MiddlewareChain` | Ordered list of middleware callables |

A **middleware callable** has the signature:

```python
def my_middleware(ctx: RequestContext) -> Optional[ResponseContext]:
    ...
```

Return `None` to let the request continue. Return a `ResponseContext` to
short-circuit the chain and send that response immediately.

## Built-in middleware

### `logging_middleware`

Logs every request at `DEBUG` level and records `request_start` in `ctx.meta`.

```python
from patchwork.builtin_middleware import logging_middleware
chain.add(logging_middleware)
```

### `cors_middleware`

Handles `OPTIONS` pre-flight requests with a `204 No Content` response and
broad CORS headers.

```python
from patchwork.builtin_middleware import cors_middleware
chain.add(cors_middleware)
```

### `make_api_key_middleware(valid_keys, header="X-Api-Key")`

Factory that returns a middleware enforcing a static API key.

```python
from patchwork.builtin_middleware import make_api_key_middleware
chain.add(make_api_key_middleware({"my-secret-key"}))
```

Requests missing or supplying an invalid key receive `401 Unauthorized`.

## Example: composing middleware

```python
from patchwork.middleware import MiddlewareChain
from patchwork.builtin_middleware import logging_middleware, cors_middleware

chain = MiddlewareChain()
chain.add(logging_middleware)
chain.add(cors_middleware)

# Inside a request handler:
early_resp = chain.process_request(ctx)
if early_resp:
    # send early_resp to client
    ...
```

## Writing custom middleware

```python
def require_json(ctx):
    ct = ctx.headers.get("Content-Type", "")
    if ctx.method in ("POST", "PUT") and "application/json" not in ct:
        from patchwork.middleware import ResponseContext
        return ResponseContext(415, {}, '{"error": "Unsupported Media Type"}')

chain.add(require_json)
```
