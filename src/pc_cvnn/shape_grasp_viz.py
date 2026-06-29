r"""shape_grasp_viz.py — WATCH the form-commanded grasp live (MuJoCo overview camera window).

Wires the shape perception into a physical grasp and SHOWS it: for each shape command (cube / L / U) the
ShapeClassifier select()s the matching object by FORM (colour-agnostic), hands its grasp point to the
reactive teacher via run_combined, and the arm grasps + carries it to a fixed target -- all rendered live
so you can SEE where a grasp goes wrong (approach? close? carry?).

Trains first (arm babble + classifier, ~1-2 min) THEN opens the window.  Close the window to exit.

Run (needs a display):
    python src/pc_cvnn/shape_grasp_viz.py
Env: SHAPE_VIZ_CYCLES (default 1 pass over cube/L/U).
"""
import os
os.environ.setdefault("ACT16_PERSIST", "1")
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import mujoco

from pc_cvnn.pc_act14 import BracketArmSim, CamViz
from pc_cvnn.arm_modules.body_model import BodyModelModule
from pc_cvnn.arm_modules.shape_classifier import ShapeClassifierModule, SHAPES
import pc_cvnn.pc_act16 as act16

CAM = "overview"
BODY = {"cube": "obj_red", "L": "obj_L", "U": "obj_U"}
ALL = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U"]
# a FIXED, well-spaced scene (>= ~3 block widths apart) + a clear central target, so the view is consistent
SCENE = {"cube": np.array([-0.07, 0.12]), "L": np.array([0.07, 0.12]), "U": np.array([0.0, 0.175])}
TARGET = np.array([0.0, 0.10])


def setup_scene(sim):
    sim.reset_home()
    for o in ALL:
        sim.set_object(o, [0.5, -0.6], z=0.008)
    sim.m.geom_size[sim.m.body_geomadr[mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, "obj_red")]] = np.array([0.012] * 3)
    for shp, p in SCENE.items():
        sim.set_object(BODY[shp], p, z=0.012 if shp == "cube" else 0.008, yaw=0.4)
    mujoco.mj_forward(sim.m, sim.d); sim.step(60)


def main():
    print("shape_grasp_viz — training (arm babble + shape classifier), ~1-2 min ...")
    sim = BracketArmSim(render_wh=(240, 240)); sim.set_reach_site("contact")
    bm = BodyModelModule(rng=np.random.default_rng(5)); bm.babble(sim, 4000)
    clf = ShapeClassifierModule(cam=CAM, rng=np.random.default_rng(0))
    clf.calibrate(sim); clf.train(sim, steps=3500, rng=np.random.default_rng(1))

    viz = CamViz(CAM)
    act16.run_combined._quiet = True                          # live updates across episodes; one hold at the end

    for _ in range(int(os.environ.get("SHAPE_VIZ_CYCLES", "1"))):
        for cmd in SHAPES:
            setup_scene(sim)
            sel = clf.select(sim, cmd)
            if sel is None:
                print(f"  [{cmd}] NOT detected"); continue
            gxy = np.asarray(sel["grasp_xy"], float)
            true = sim.obj_pos(BODY[cmd])[:2]
            print(f"  command '{cmd}': perceived shape={sel['shape']} prob={sel['prob']:.2f}  "
                  f"grasp_xy={np.round(gxy, 3)}  true={np.round(true, 3)}  err={np.linalg.norm(gxy - true) * 1000:.0f}mm")

            def pf(c, g=gxy):
                return (g, None, "grasp")
            d, m = act16.run_combined(sim, bm.body, viz, CAM, episodes=1, cmd_fixed=BODY[cmd], force="grasp",
                                      perceive_fn=pf, goal_fn=lambda c, o, T=TARGET: T, rescatter=False)
            placed = sim.obj_pos(BODY[cmd])[:2]
            print(f"           -> delivered {d}/{m}   object now at {np.round(placed, 3)}  "
                  f"(target {np.round(TARGET, 3)}, dist {np.linalg.norm(placed - TARGET) * 1000:.0f}mm)")

    print("  [viz] close the window to exit.")
    viz.hold()


if __name__ == "__main__":
    main()
