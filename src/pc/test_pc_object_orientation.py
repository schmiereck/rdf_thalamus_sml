r"""test_pc_object_orientation.py — STEP 2a: LEARN an elongated object's long-axis orientation from the camera.

To grip an elongated object the claws align to its narrow axis -> the agent must PERCEIVE the object's
orientation (the user's choice: learned, not the privileged simulator angle).  A colour-filtered saliency
principal axis gives the signal; the LEARNED part is the perspective correction from the angled overhead
camera (image axis + position -> table long-axis double-angle).  Validated honestly on HELD-OUT poses as an
axis-angle error in DEGREES (modulo 180, since a long axis is undirected).

  python src/pc/test_pc_object_orientation.py            headless: fit + held-out error + plot
  ORI_CAM=top python src/pc/test_pc_object_orientation.py   use the straight-down camera instead
"""
from __future__ import annotations

import os
import sys

import numpy as np
import mujoco

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pc.pc_act14 import BracketArmSim
from pc.arm_modules.object_orientation import ObjectOrientationModule


def main():
    cam = os.environ.get("ORI_CAM", "overview").lower()
    cmd = os.environ.get("ORI_OBJ", "obj_red")
    res = int(os.environ.get("ORI_RES", "480"))
    sim = BracketArmSim(render_wh=(res, res))
    sim.set_target_marker([0.0, -0.6], z=-0.05)                  # park the magenta marker out of the scene
    ori = ObjectOrientationModule()

    print(f"object-orientation — STEP 2a: LEARNED long-axis perception ({cmd}, cam={cam})")
    print("  fitting the perspective correction (image axis -> table yaw) on rendered random poses ...")
    tr = ori.train(sim, cmd=cmd, cam=cam, steps=int(os.environ.get("ORI_STEPS", "2500")),
                   rng=np.random.default_rng(0))
    print(f"    train-set axis error {tr:.1f} deg")

    # held-out validation: new random poses, perceive -> compare to the true long-axis (mod 180)
    rng = np.random.default_rng(7); n = 300
    errs = []; pairs = []
    for _ in range(n):
        xy = [rng.uniform(-0.10, 0.10), rng.uniform(0.10, 0.20)]; yaw = rng.uniform(0, np.pi)
        sim.set_object(cmd, xy, z=0.012, yaw=yaw); mujoco.mj_forward(sim.m, sim.d); sim.step(2)
        _, long_axis = ori.perceive(sim, cmd, cam=cam)
        errs.append(float(ObjectOrientationModule._axis_err(np.array([yaw]), np.array([long_axis]))[0]))
        pairs.append((np.degrees(yaw % np.pi), np.degrees(long_axis % np.pi)))
    errs = np.array(errs); pairs = np.array(pairs)
    print(f"  HELD-OUT: long-axis error  mean {errs.mean():.1f} deg  median {np.median(errs):.1f} deg  "
          f"<=15deg: {100*np.mean(errs < 15):.0f}%")
    print("  Read: the agent PERCEIVES the elongated object's orientation (learned perspective correction,")
    print("  no privileged angle).  Next (2b): align the claws via wrist_for_yaw and grip the object.")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
        ax[0].scatter(pairs[:, 0], pairs[:, 1], s=7, alpha=0.4)
        ax[0].plot([0, 180], [0, 180], "r--", lw=1)
        ax[0].set_xlabel("true long-axis (deg, mod 180)"); ax[0].set_ylabel("perceived (deg, mod 180)")
        ax[0].set_title(f"learned orientation (mean err {errs.mean():.1f} deg)")
        ax[1].hist(errs, bins=40, color="tab:purple", alpha=0.8)
        ax[1].set_xlabel("axis error (deg)"); ax[1].set_ylabel("count")
        ax[1].set_title("held-out long-axis error")
        fig.suptitle(f"Wrist-roll STEP 2a — LEARNED object orientation from the camera ({cam})")
        fig.tight_layout()
        out = os.path.join(os.path.dirname(__file__), "object_orientation.png")
        fig.savefig(out, dpi=110); print(f"  [viz] saved {out}")
    except Exception as e:
        print(f"  [viz] plot skipped: {e}")


if __name__ == "__main__":
    main()
