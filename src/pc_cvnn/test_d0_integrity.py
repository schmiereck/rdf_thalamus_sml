"""Small deterministic test for D0 integrity manifests and JSONL credit records."""

from __future__ import annotations

import json
import sys
import tempfile
from types import SimpleNamespace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pc_cvnn.arm_modules.d0_integrity import (
    append_credit, assert_unchanged, changed_components, snapshot, write_manifest,
)


def main() -> None:
    components = {"world": {"weights": np.array([1.0, 2.0])}, "runtime": {"rows": [1, 2]}}
    before = snapshot(components, context={"seed": 1703})
    after = snapshot(components, context={"seed": 1703})
    assert_unchanged(before, after)

    components["world"]["weights"][0] = 3.0
    changed = changed_components(before, snapshot(components))
    assert set(changed) == {"world"}, changed

    # A frozen execution may advance a generator/diagnostic state.  It is visible in the full
    # audit, but must not be mistaken for a changed learning buffer or weight.
    world = SimpleNamespace(members=[np.array([1.0])], _X=[], _Y=[], _W=[], _G=[],
                            feat_dim=3, off_max=0.01, wrist_grid=8, rng=np.random.default_rng(1))
    frozen_before = snapshot({"world": world})
    world.rng.random()
    frozen_after = snapshot({"world": world})
    assert "world" in changed_components(frozen_before, frozen_after)
    assert not changed_components(frozen_before, frozen_after, learning_only=True)
    world.members[0][0] = 2.0
    assert "world" in changed_components(frozen_before, snapshot({"world": world}), learning_only=True)

    # Keep the disposable artifact inside the worktree: the shared Windows venv can be denied
    # access to the system temp directory while another worker has an ACT23 process open.
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
        root = Path(directory)
        write_manifest(root / "before.json", before)
        append_credit(root / "credit.jsonl", {
            "episode": 1, "label_source": "Selbst", "route": "Griff hielt nicht",
            "outcome": False, "wrist_deg": 22.5, "weight": 1.0,
        })
        manifest = json.loads((root / "before.json").read_text(encoding="utf-8"))
        credit = json.loads((root / "credit.jsonl").read_text(encoding="utf-8"))
        assert manifest["context"]["seed"] == 1703
        assert credit["schema"] == "act23-d0-credit-v1"
        assert credit["label_source"] == "Selbst"
    print("D0 integrity: OK")


if __name__ == "__main__":
    main()
