r"""pc_act20.py — restore the 1D PCModule architecture on the MuJoCo arm + the PLANNER.

act14-19 had drifted to loose classes; this assembles the agent back into the 1D-style module
split — VisualCortex / BodyModel / Planner / Motor — as self-contained `ArmModule`s with
declared, typed PORTS, wired by an `ArmAgent` ("zusammengesteckt").  The new PLANNER dreams the
place target ABOVE a GoalModule2D (the 2-layer "Planner over goal module" structure):

    VisualCortex --object_xy--> Planner --goal_xy--> (place target the arm delivers to)
         |                         ^ conditioning_flag (0=mirror, 1=centre)
         +--object_xy--> Motor <-- state --> subgoal --> BodyModel --joint_dq--> arm

`run_combined` (pc_act16) stays the low-level executor, driven THROUGH the module interfaces:
perceive=VisualCortex, goal=Planner.dream (new `goal_fn` hook), policy=Motor, body=BodyModel.
The dreamed goal is committed AND scored against (honest `rested` scoring).

Env:  ACT20_HEADLESS  ACT20_EPISODES  ACT20_COLLECT  ACT20_RES  ACT20_CAM
      ACT20_FLAG (0=mirror, 1=centre)  ACT20_GM_STEPS  ACT20_PLAN_STEPS
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from pc.pc_act14 import BracketArmSim
import pc.pc_act16 as act16
from pc.arm_modules import (ArmAgent, VisualCortexModule, BodyModelModule,
                            GoalModule2D, PlannerModule, MotorModule, rule_mirror, rule_centre)
from pc.arm_modules.planner import LO, HI, SPAN


def main():
    HEADLESS = os.environ.get("ACT20_HEADLESS", "0") == "1"
    CAM = os.environ.get("ACT20_CAM", "overview").lower()
    COLLECT = int(os.environ.get("ACT20_COLLECT", "18"))
    EPISODES = int(os.environ.get("ACT20_EPISODES", "10"))
    RES = int(os.environ.get("ACT20_RES", "240"))
    FLAG = float(os.environ.get("ACT20_FLAG", "0"))           # 0 -> mirror, 1 -> centre
    GM_STEPS = int(os.environ.get("ACT20_GM_STEPS", "8000"))
    PLAN_STEPS = int(os.environ.get("ACT20_PLAN_STEPS", "12000"))
    rule_name = "centre" if FLAG >= 0.5 else "mirror"

    print("act20 — PCModule architecture restored (VisualCortex/BodyModel/Planner/Motor) + 2-layer Planner")
    sim = BracketArmSim(render_wh=(RES, RES)); sim.set_reach_site("contact")

    # ---- build the modules ----
    bm = BodyModelModule(rng=np.random.default_rng(5)); bm.babble(sim, 4000)
    gm = GoalModule2D(rng=np.random.default_rng(7)); gm.pretrain(GM_STEPS)
    planner = PlannerModule(gm, n_flags=1, rng=np.random.default_rng(1))
    motor = MotorModule(rng=np.random.default_rng(2))

    # ---- train the Planner on the conditioned rule (faithful 1D experiment) ----
    prng = np.random.default_rng(0)

    def rand_obj():
        return np.array([prng.uniform(LO[0] + 0.05 * SPAN[0], HI[0] - 0.05 * SPAN[0]),
                         prng.uniform(LO[1] + 0.05 * SPAN[1], HI[1] - 0.05 * SPAN[1])])

    def cond_sample():
        o = rand_obj(); f = int(prng.integers(0, 2))
        return o, (float(f),), (rule_mirror(o) if f == 0 else rule_centre(o))

    print(f"  training Planner (GoalModule pretrain {GM_STEPS}, planner {PLAN_STEPS}) ...")
    planner.train(cond_sample, PLAN_STEPS)

    # ---- train the Motor by imitation of the reactive teacher (act19 recipe) ----
    Xs, Ys = [], []

    def log(state, aim, j5):
        Xs.append(state.copy()); Ys.append(np.array([aim[0], aim[1], aim[2], j5]))

    print(f"  collecting reactive-teacher demos ({COLLECT} eps) ...")
    act16.run_combined(sim, bm.body, None, CAM, episodes=COLLECT, policy_fn=act16.reactive_subgoal, log_fn=log)
    motor.fit(np.array(Xs), np.array(Ys))

    # ---- (a) LEARNED inverse kinematics: replaces the analytic Jacobian reach controller ----
    LEARNED_IK = os.environ.get("ACT20_LEARNED_IK", "1") == "1"
    if LEARNED_IK:
        print("  training the LEARNED inverse kinematics (replaces the analytic Jacobian) ...")
        rec = bm.learn_inverse(sim, rng=np.random.default_rng(11))
        print(f"    IK babble reconstruction: {rec:.2f} mm")
    reach_body = bm if LEARNED_IK else bm.body          # `bm` routes reach through the LEARNED IK

    # ---- assemble the agent: declare the modules and wire their ports ----
    agent = ArmAgent("arm-agent")
    for m in (planner, motor, bm):
        agent.add(m)

    def goal_fn(cmd, obj_xy):
        """Planner dreams the place target from the (perceived) object — over its ports."""
        planner.set_in("object_xy", obj_xy); planner.set_in("conditioning_flag", [FLAG])
        planner.step()
        return planner.get_out("goal_xy")

    # -------- headless: privileged perception, metrics only --------
    if HEADLESS:
        print(f"  conditioning flag={FLAG:.0f} -> rule '{rule_name}'")
        print(agent.summary())
        print("  [VisualCortex runs privileged in headless]")
        if LEARNED_IK:                                  # honest A/B: analytic Jacobian vs learned IK
            da, ma = act16.run_combined(sim, bm.body, None, CAM, episodes=EPISODES,
                                        policy_fn=motor.predict, goal_fn=goal_fn)
            print(f"  [analytic Jacobian DLS] delivered {da}/{ma}")
        d, m = act16.run_combined(sim, reach_body, None, CAM, episodes=EPISODES,
                                  policy_fn=motor.predict, goal_fn=goal_fn)
        bm.note_surprise(sim.arm3_angles(), sim.grasp_pos())
        label = "LEARNED inverse kinematics" if LEARNED_IK else "analytic Jacobian DLS"
        print(f"  [{label}] delivered {d}/{m} of the commanded cube to the DREAMED goal")
        print("  per-module surprise:", {k: v for k, v in agent.surprises().items()})
        return

    # -------- coupled: VisualCortex perception + live views --------
    print("  (coupling VisualCortex perception + Planner + Motor; live fovea + surprise views)")
    try:
        from pc.pc_act18 import SurpriseViz
        vc, P = VisualCortexModule.from_sim(sim, CAM, RES, headless=False)
        agent.add(vc)
        agent.wire("VisualCortex", "object_xy", "Planner", "object_xy")
        print(f"  conditioning flag={FLAG:.0f} -> rule '{rule_name}'")
        print(agent.summary())
        sviz = SurpriseViz()

        def perceive(cmd):
            return vc.perceive(cmd), None, "grasp"             # object only; Planner sets the target

        def track_and_plot():
            vc.track()
            bmm = bm.note_surprise(sim.arm3_angles(), sim.grasp_pos())
            d = vc.surprise(); ps = planner.surprise()
            if d is not None:
                sviz.push(d["sensor"], d["state"], d["total"], d["relax"], bmm,
                          planner=(ps["sensor"] if ps else None))

        d, m = act16.run_combined(sim, reach_body, None, CAM, episodes=EPISODES,
                                  policy_fn=motor.predict, goal_fn=goal_fn,
                                  perceive_fn=perceive, track_fn=track_and_plot)
        print(f"  delivered {d}/{m} of the commanded cube to the DREAMED goal ('{rule_name}')")
        try:
            out_png = os.path.join(os.path.dirname(__file__), "act20_surprise.png")
            sviz.save(out_png); print(f"  [viz] surprise curves saved -> {out_png}")
        except Exception as e:
            print(f"  [viz] could not save surprise plot: {e}")
        print("  [viz] close the windows to exit.")
        (vc.viz or sviz).hold()
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"  [viz/perception] {e}; falling back to privileged run")
        d, m = act16.run_combined(sim, reach_body, None, CAM, episodes=EPISODES,
                                  policy_fn=motor.predict, goal_fn=goal_fn)
        print(f"  delivered {d}/{m} to the dreamed goal")


if __name__ == "__main__":
    main()
