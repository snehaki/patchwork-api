# Responder Module

The `patchwork.responder` module is responsible for turning a validated route
definition (plus any path parameters captured by the matcher) into a concrete
HTTP response that the server can send back to the client.

## Public API

### `build_response(definition, params) -> dict`

Builds a response dictionary from a route definition and a dict of matched
path parameters.

**Arguments**

| Name | Type | Description |
|------|------|-------------|
| `definition` | `dict` | A validated route definition loaded from a YAML file. |
| `params` | `dict` | Path parameters extracted by `matcher.match_route`. |

**Returns** a `dict` with three keys:

| Key | Type | Description |
|-----|------|-------------|
| `status` | `int` | HTTP status code (defaults to `200`). |
| `headers` | `dict` | Response headers. `Content-Type` is set automatically unless overridden. |
| `body` | `bytes` | Encoded response body. |

### `_substitute_params(template, params) -> Any`

Internal helper that recursively walks `template` (string, dict, or list) and
replaces `{param}` placeholders with values from `params`.

## Body serialisation rules

- If the YAML `body` value is a **dict** or **list** it is serialised as
  pretty-printed JSON and `Content-Type` defaults to `application/json`.
- Any other value is coerced to a string and `Content-Type` defaults to
  `text/plain`.
- An explicit `Content-Type` in the definition's `headers` block always wins.

## Example YAML definition

```yaml
method: GET
path: /users/{id}
status: 200
body:
  id: "{id}"
  name: Ada
headers:
  X-Powered-By: patchwork
```

When a request arrives for `GET /users/42` the responder produces:

```json
{
  "id": "42",
  "name": "Ada"
}
```

with headers `Content-Type: application/json` and `X-Powered-By: patchwork`.
