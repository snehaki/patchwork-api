# Webhook Support

Patchwork can fire outbound HTTP requests whenever a matched route returns a
response. This is useful for testing systems that expect callbacks or event
notifications.

## Defining a webhook

Add a `webhook` block to any route definition:

```yaml
- method: POST
  path: /orders
  status: 201
  body:
    id: 42
    status: created
  webhook:
    url: https://hooks.example.com/order-created
    method: POST          # default
    async: true           # default – fires in background thread
    headers:
      X-Source: patchwork
    body:
      event: order_created
      order_id: 42
```

## Fields

| Field     | Type    | Required | Default | Description                                      |
|-----------|---------|----------|---------|--------------------------------------------------|
| `url`     | string  | yes      | –       | Full URL to call (`http://` or `https://`)       |
| `method`  | string  | no       | `POST`  | HTTP method (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) |
| `headers` | mapping | no       | `{}`    | Extra request headers                            |
| `body`    | any     | no       | `null`  | Request body; mappings are JSON-encoded          |
| `async`   | bool    | no       | `true`  | When `true`, fires in a daemon thread            |

## Synchronous mode

Set `async: false` to block until the webhook completes (or times out after
5 seconds). Errors from the remote server are silently ignored — the mock
route response is always returned to the caller regardless.

## Parsing & validation

`parse_webhook(definition)` is called automatically by the registry when
loading route definitions. A `WebhookError` is raised for invalid configs and
will prevent the server from starting.

```python
from patchwork.webhook import parse_webhook, fire_webhook

config = parse_webhook(route_definition)  # returns dict or None
if config:
    fire_webhook(config, context)
```
