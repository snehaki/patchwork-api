# Scenario Support

Scenarios let a single route return **different responses** on successive calls,
enabling stateful mock workflows without changing YAML files at runtime.

## YAML definition

```yaml
method: POST
path: /cart/checkout
scenario:
  name: checkout_flow
  initial: pending
  states:
    pending:
      status: 202
      body:
        message: Order is being processed
    complete:
      status: 200
      body:
        message: Order confirmed
        order_id: 42
    failed:
      status: 500
      body:
        error: Payment declined
```

### Fields

| Field     | Required | Description                                          |
|-----------|----------|------------------------------------------------------|
| `name`    | yes      | Unique identifier for this scenario                  |
| `initial` | no       | State to start from (defaults to first key)          |
| `states`  | yes      | Mapping of state name → response object              |

Each **state value** is a standard response object (`status`, `body`,
`headers`, `delay`) identical to a top-level route response.

## Advancing states

Patchwork exposes a built-in management endpoint:

```
POST /_patchwork/scenario/{name}/advance
```

This moves the named scenario to its next state (wrapping back to the first
state after the last one).

You can also jump to a specific state:

```
POST /_patchwork/scenario/{name}/state
Content-Type: application/json

{"state": "failed"}
```

And reset to the initial state:

```
POST /_patchwork/scenario/{name}/reset
```

## Python API

```python
from patchwork.scenario import advance_scenario, set_state, reset_scenario

advance_scenario("checkout_flow")   # move to next state
set_state("checkout_flow", "failed") # jump to a specific state
reset_scenario("checkout_flow")     # back to initial
```

## Notes

- State is **in-process** and not persisted across server restarts.
- Multiple routes can share the same scenario name — they will all reflect
  the same current state.
- When the file watcher reloads definitions, scenario state is **preserved**
  unless the scenario block itself changes.
