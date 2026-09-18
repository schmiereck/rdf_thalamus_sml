"""Deterministic unit test for D0 training-credit filtering and wrist coverage."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pc_cvnn.act23_d0_training_runner import credit_summary, wrist_bin


def main() -> None:
    assert wrist_bin(-22.5) == 7
    assert wrist_bin(180.0) == 0
    records = [
        {"action_source": "Selbst", "label_source": "Selbst", "weight": 1.0,
         "route": "Griff am Objekt fehlgeschlagen (Aktion)", "relative_wrist_deg": 0.0},
        {"action_source": "Selbst", "label_source": "Selbst", "weight": 1.0,
         "route": "Griff hielt nicht (Drucksensor)", "relative_wrist_deg": 45.0},
        {"action_source": "Selbst", "label_source": "Welt", "weight": 1.0,
         "route": "Griff am Objekt fehlgeschlagen (Aktion)", "relative_wrist_deg": 90.0},
        {"action_source": "Selbst", "label_source": "Selbst", "weight": 0.5,
         "route": "Griff am Objekt fehlgeschlagen (Aktion)", "relative_wrist_deg": 135.0},
    ]
    summary = credit_summary(records)
    assert summary["all_records"] == 4
    assert summary["eligible_records"] == 2
    assert summary["wrist_bins"] == [0, 2]
    print("D0 training runner: OK")


if __name__ == "__main__":
    main()
