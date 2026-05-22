# Response Body Templating

Patchwork supports lightweight `{{ variable }}` templating in response bodies
defined in YAML fixtures.  At request time the placeholders are replaced with
values derived from the incoming request.

## Available Variables

| Placeholder | Description |
|---|---|
| `{{ request.method }}` | HTTP method in upper-case (e.g. `GET`) |
| `{{ request.path }}` | Request path (e.g. `/users/42`) |
| `{{ request.params.NAME }}` | URL path parameter captured by the route |

## Example Fixture

```yaml
method: GET
path: /users/{id}
status: 200
body:
  message: "Fetched user {{ request.params.id }} via {{ request.method }}"
  path: "{{ request.path }}"
```

### Response

```json
{
  "message": "Fetched user 42 via GET",
  "path": "/users/42"
}
```

## Unknown Placeholders

If a placeholder cannot be resolved it is left **unchanged** in the output so
you can spot typos easily during development.

## Nested Structures

Templating works recursively inside nested dicts and lists:

```yaml
body:
  data:
    items:
      - "{{ request.method }}"
      - static value
```

## Integration

Templating is applied automatically by `build_response` in `responder.py`
after path-parameter substitution.  No extra configuration is required.
