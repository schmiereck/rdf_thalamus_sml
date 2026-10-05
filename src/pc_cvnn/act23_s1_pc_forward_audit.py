"""Isolated complex-PC forward-model audit for S1 direct-servo transitions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pc_cvnn.connection import ConnType
from pc_cvnn.network import PCNetwork
from pc_cvnn.node import PCNode, SensorNode


def _rows(run_dir: Path) -> list[dict]:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    for key in ("pressure_sensor_used", "teacher_or_ik_used", "object_or_contact_observed"):
        if manifest.get(key) is not False:
            raise ValueError(f"invalid S1 source: {key} is not false")
    rows = [json.loads(line) for line in (run_dir / "transitions.jsonl").read_text(encoding="utf-8").splitlines()]
    if len(rows) != 3000:
        raise ValueError(f"expected 3000 rows, got {len(rows)}")
    return rows


def _arrays(rows: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    x = np.array([r["q_rad"] + r["qvel_rad_s"] + r["ctrl_next_rad"] for r in rows], dtype=float)
    y = np.array([r["q_next_rad"] for r in rows], dtype=float)
    rollout = np.array([r["rollout_id"] for r in rows], dtype=int)
    split = np.array([r["split"] for r in rows])
    return x, y, rollout, split


class PCForward:
    def __init__(self, input_dim: int, output_dim: int, latent_dim: int, seed: int) -> None:
        self.net = PCNetwork(eta_inf=0.08, n_relax=16, eps_tol=1e-5, eta_learn=0.004,
                             eta_temporal=0.0, gamma=0.3, w_clip=3.0,
                             rng=np.random.default_rng(seed))
        self.context = self.net.add(SensorNode("s1_context", input_dim))
        self.next_q = self.net.add(SensorNode("s1_next_q", output_dim))
        self.latent = self.net.add(PCNode("s1_latent", latent_dim, activation="tanh", eta_temporal=0.0,
                                          rng=np.random.default_rng(seed + 1)))
        self.net.connect("s1_latent", "s1_context", ConnType.UP, pressure_scale=1.0)
        self.net.connect("s1_latent", "s1_next_q", ConnType.UP, pressure_scale=1.0)

    def reset(self) -> None:
        # PCNetwork owns no aggregate reset; node.reset retains learned W/V but clears the
        # transient latent and temporal state between independent rollouts.
        rng = np.random.default_rng(0)
        for node in self.net._nodes.values():
            node.reset(rng=rng)

    def train_row(self, x: np.ndarray, y: np.ndarray) -> None:
        self.context.set_input(x)
        self.next_q.set_input(y)
        self.net.step(learn=True)
        self.net.commit_step()

    def predict(self, x: np.ndarray) -> np.ndarray:
        self.context.set_input(x)
        self.next_q.unclamp()
        self.net.step(learn=False)
        return np.real(self.next_q.mu).copy()


def _mse(y: np.ndarray, pred: np.ndarray) -> tuple[float, list[float]]:
    per = np.mean((y - pred) ** 2, axis=0)
    return float(np.mean(per)), [float(v) for v in per]


def audit(run_dir: Path, epochs: int, latent_dim: int, seed: int) -> dict:
    rows = _rows(run_dir)
    x, y, rollout, split = _arrays(rows)
    train, test = split == "train", split == "test"
    if set(rollout[train]) & set(rollout[test]):
        raise ValueError("trajectory split leaks rollout ids")
    x_mean, x_std = x[train].mean(0), x[train].std(0)
    y_mean, y_std = y[train].mean(0), y[train].std(0)
    x_std = np.maximum(x_std, 1e-6); y_std = np.maximum(y_std, 1e-6)
    xn, yn = (x - x_mean) / x_std, (y - y_mean) / y_std
    model = PCForward(x.shape[1], y.shape[1], latent_dim, seed)
    for _ in range(epochs):
        for rollout_id in sorted(set(rollout[train])):
            model.reset()
            for index in np.where(rollout == rollout_id)[0]:
                if train[index]:
                    model.train_row(xn[index], yn[index])
    predn = np.empty_like(yn[test])
    test_indices = np.where(test)[0]
    for rollout_id in sorted(set(rollout[test])):
        model.reset()
        for index in test_indices[rollout[test_indices] == rollout_id]:
            predn[np.where(test_indices == index)[0][0]] = model.predict(xn[index])
    pred = predn * y_std + y_mean
    persistence = x[test, :5]
    constant = np.broadcast_to(y_mean, y[test].shape)
    model_mse, model_per = _mse(y[test], pred)
    persist_mse, persist_per = _mse(y[test], persistence)
    constant_mse, constant_per = _mse(y[test], constant)
    return {
        "schema": "act23-s1-pc-forward-audit-v1",
        "source": str(run_dir), "epochs": epochs, "latent_dim": latent_dim, "seed": seed,
        "train_rows": int(train.sum()), "test_rows": int(test.sum()),
        "train_rollouts": sorted(int(v) for v in set(rollout[train])),
        "test_rollouts": sorted(int(v) for v in set(rollout[test])),
        "mse_rad2": {"pc_forward": model_mse, "persistence": persist_mse, "constant": constant_mse},
        "per_joint_mse_rad2": {"pc_forward": model_per, "persistence": persist_per, "constant": constant_per},
        "pc_vs_persistence_fraction": None if persist_mse == 0 else model_mse / persist_mse,
        "better_joints_than_persistence": int(sum(a < b for a, b in zip(model_per, persist_per))),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--latent-dim", type=int, default=24)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    result = audit(args.run_dir, args.epochs, args.latent_dim, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
