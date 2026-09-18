"""D0 integrity primitives for disposable ACT23 evaluations.

This module deliberately has no dependency on MuJoCo or the ACT23 control loop.  A runner can
snapshot the actual learner objects before an evaluation, run on a disposable copy, and reject
the result when any declared component changed.  The same module writes one structured credit
record per action without making the human-readable ACT23 log a data interface.
"""

from __future__ import annotations

import hashlib
import json
import os
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np


# All items stored by ACT23's save_state plus the in-process fovea when present.  Callers pass
# the actual objects; an absent optional component is recorded explicitly rather than ignored.
D0_COMPONENTS = (
    "bm", "shape_clf", "world", "runtime", "colours", "fovea", "latent_goal",
    "latent_dynamics", "dream_seen", "self_eval",
)


def _json_value(value: Any) -> Any:
    """Convert scalar/array values used in a credit line to JSON without lossy string parsing."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    raise TypeError(f"not JSON serialisable: {type(value).__name__}")


def component_fingerprints(components: Mapping[str, Any], *, names=D0_COMPONENTS) -> dict[str, str]:
    """Return a content fingerprint for every D0-relevant component.

    Pickle is also ACT23's persistence representation.  Hashing each component separately makes
    a failed frozen evaluation diagnosable (for example, only ``world`` changed) instead of
    emitting one opaque state hash.  This function serialises but never mutates its input.
    """
    result: dict[str, str] = {}
    for name in names:
        if name not in components or components[name] is None:
            result[name] = "absent"
            continue
        raw = pickle.dumps(components[name], protocol=pickle.HIGHEST_PROTOCOL)
        result[name] = hashlib.sha256(raw).hexdigest()
    return result


def snapshot(components: Mapping[str, Any], *, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Create a portable manifest for a frozen-evaluation boundary."""
    return {
        "schema": "act23-d0-integrity-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "components": component_fingerprints(components),
        "context": _json_value(dict(context or {})),
    }


def changed_components(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    """Return every changed component in two manifests created by :func:`snapshot`."""
    old = before.get("components", {})
    new = after.get("components", {})
    names = sorted(set(old) | set(new))
    return {name: {"before": old.get(name, "missing"), "after": new.get(name, "missing")}
            for name in names if old.get(name) != new.get(name)}


def assert_unchanged(before: Mapping[str, Any], after: Mapping[str, Any]) -> None:
    """Raise when a supposedly frozen evaluation changed a declared learner component."""
    changed = changed_components(before, after)
    if changed:
        detail = ", ".join(changed)
        raise RuntimeError(f"D0 frozen evaluation mutated: {detail}")


def write_manifest(path: str | os.PathLike[str], manifest: Mapping[str, Any]) -> None:
    """Atomically write one snapshot manifest so a killed run cannot leave partial JSON."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(_json_value(dict(manifest)), sort_keys=True, indent=2) + "\n",
                   encoding="utf-8")
    os.replace(tmp, target)


def append_credit(path: str | os.PathLike[str], record: Mapping[str, Any]) -> None:
    """Append exactly one machine-readable D0 credit record.

    ``record`` is intentionally supplied by the control loop.  This keeps the logger neutral:
    it neither decides the credit route nor accidentally reimplements a control rule.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = _json_value(dict(record))
    data.setdefault("schema", "act23-d0-credit-v1")
    data.setdefault("recorded_at", datetime.now(timezone.utc).isoformat())
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n")

