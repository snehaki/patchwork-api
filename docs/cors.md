# CORS Support

Patchwork can automatically attach Cross-Origin Resource Sharing (CORS) headers
to any route response.  Add a `cors` block to your YAML definition and the
server will include the appropriate headers on every response for that route,
including preflight `OPTIONS` requests.

## Minimal example

```yaml
method: GET
path: /api/users
status: 200
body: {"users": []}
cors:
  origins:
    - "https://app.example.com"
```

## Full configuration

```yaml
method: GET
path: /api/items
status: 200
body: {"items": []}
cors:
  origins:
    - "https://app.example.com"
    - "https://staging.example.com"
  methods:
    - GET
    - POST
    - OPTIONS
  headers:
    - Content-Type
    - Authorization
    - X-Request-ID
  allow_credentials: true
  max_age: 600
```

## Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `origins` | list of strings | `["*"]` | Allowed origins. Use `"*"` to permit any origin. |
| `methods` | list of strings | common HTTP verbs | Allowed HTTP methods (case-insensitive, stored uppercased). |
| `headers` | list of strings | `["Content-Type", "Authorization"]` | Headers the browser is allowed to send. |
| `allow_credentials` | boolean | `false` | Set `Access-Control-Allow-Credentials: true`. |
| `max_age` | number | *(absent)* | Seconds the browser may cache a preflight response. |

## Wildcard vs. explicit origins

When `origins` contains `"*"` the response header is always
`Access-Control-Allow-Origin: *`.

When specific origins are listed the server reflects the request's `Origin`
header if it appears in the allow-list, otherwise the first listed origin is
used.  This is the correct behaviour required when `allow_credentials: true` is
set (browsers reject a wildcard origin in that case).

## Preflight requests

The server automatically responds to `OPTIONS` requests on any route that has a
`cors` block with `204 No Content` and the full set of CORS headers — no
separate `OPTIONS` definition is needed.
