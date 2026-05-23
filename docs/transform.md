# Response Transforms

Patchwork can apply a **transform pipeline** to the response body before
it is sent to the client.  Declare a `transforms` list in your YAML
definition to enable this feature.

## Example

```yaml
- method: GET
  path: /users/1
  status: 200
  body:
    id: 1
    secret: "hunter2"
    name: "Alice"
  transforms:
    - type: omit_keys
      keys:
        - secret
    - type: wrap
```

The client receives:

```json
{"data": {"id": 1, "name": "Alice"}}
```

## Available Transforms

### `uppercase`

Converts every string value in the body to upper-case.  Non-string values
(numbers, booleans, …) are left untouched.

```yaml
transforms:
  - type: uppercase
```

### `lowercase`

Same as `uppercase` but converts to lower-case.

### `wrap`

Wraps the entire body inside a `{"data": …}` envelope.

```yaml
transforms:
  - type: wrap
```

### `omit_keys`

Removes the listed keys from a mapping body.  If the body is not a
mapping the transform is a no-op.

```yaml
transforms:
  - type: omit_keys
    keys:
      - password
      - internal_id
```

## Pipeline order

Transforms are applied **in the order they are listed**.  The output of
one transform becomes the input of the next.

## Error handling

If a transform definition is invalid (unknown `type`, wrong structure)
a `TransformError` is raised during server start-up so you catch
mis-configurations before any request is served.
