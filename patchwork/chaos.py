"""Chaos engineering helpers: inject random faults into responses."""

from __future__ import annotations

import random
from typing import Optional


class ChaosError(Exception):
    """Raised when a chaos configuration is invalid."""


# Fault modes supported by the chaos module.
_VALID_FAULTS = {"error", "delay", "empty"}


def parse_chaos(definition: dict) -> Optional[dict]:
    """Extract and validate the ``chaos`` block from a route definition.

    Returns ``None`` when no chaos block is present.
    """
    chaos = definition.get("chaos")
    if chaos is None:
        return None
    if not isinstance(chaos, dict):
        raise ChaosError("'chaos' must be a mapping")

    probability = chaos.get("probability", 1.0)
    if not isinstance(probability, (int, float)):
        raise ChaosError("'chaos.probability' must be a number")
    if not (0.0 <= float(probability) <= 1.0):
        raise ChaosError("'chaos.probability' must be between 0.0 and 1.0")

    fault = chaos.get("fault", "error")
    if fault not in _VALID_FAULTS:
        raise ChaosError(
            f"'chaos.fault' must be one of {sorted(_VALID_FAULTS)}, got {fault!r}"
        )

    result = {"probability": float(probability), "fault": fault}

    if fault == "error":
        result["status"] = int(chaos.get("status", 500))
        result["body"] = chaos.get("body", "chaos fault injected")

    if fault == "delay":
        seconds = chaos.get("seconds", 1.0)
        if not isinstance(seconds, (int, float)) or float(seconds) < 0:
            raise ChaosError("'chaos.seconds' must be a non-negative number")
        result["seconds"] = float(seconds)

    return result


def apply_chaos(chaos: Optional[dict], rng: random.Random = random) -> Optional[dict]:
    """Decide whether to trigger a fault and return an action descriptor.

    Returns ``None`` when chaos should not be applied (either no config or the
    random roll did not hit the configured probability).

    The returned dict has the shape::

        {"fault": "error", "status": 500, "body": "..."}
        {"fault": "delay", "seconds": 2.0}
        {"fault": "empty"}
    """
    if chaos is None:
        return None
    if rng.random() > chaos["probability"]:
        return None

    fault = chaos["fault"]
    if fault == "error":
        return {"fault": "error", "status": chaos["status"], "body": chaos["body"]}
    if fault == "delay":
        return {"fault": "delay", "seconds": chaos["seconds"]}
    # fault == "empty"
    return {"fault": "empty"}
