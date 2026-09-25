r"""
pc_act14.py — Step 1 of the move to a PHYSICAL robot: the real 5-DOF arm in MuJoCo,
with real 3-D gravity, contact physics, lighting/shadows/textures and an overhead camera.

This stage establishes the simulation FOUNDATION (it does NOT yet wire the PC net):

  * `BracketArmSim` loads assets/bracket_arm.xml — a faithful MJCF replica of the real
    arm (ba_arduino_controller_moveit_config): joints joint_0..joint_4 (+ gripper joint_5),
    exact link lengths/axes, [0,pi] servo limits, the measured overhead camera.
  * Position actuators hold the arm against gravity; objects rest/collide on the table.
  * A demo reaches the gripper to a target object in 3-D using MuJoCo's site Jacobian
    (damped least-squares) — a closed-loop 3-D reach under gravity.  In later steps the
    agent's LEARNED kinematics + the camera image replace the analytic Jacobian and the
    synthetic scene (Step 2 = overhead camera as the net's input).

Run:  python pc_act14.py                 (live overview-camera window + scripted reach)
      ACT14_CAM=top python ...            (top-down camera instead)
      ACT14_HEADLESS=1 python ...         (no window; saves a few frames + prints metrics)
"""

from __future__ import annotations

import io
import math
import os
import sys

import numpy as np
import mujoco

ASSET = os.path.join(os.path.dirname(__file__), "assets", "bracket_arm.xml")

# ---------------------------------------------------------------------------------------------
# UMBAUBARE FINGERGEOMETRIE (Nutzerwunsch 2026-08-28).  Der Greifer ist HARDWARE, kein
# Erkennungsalgorithmus -- diese Knoepfe aendern die WELT, nicht das Netz.
#
# DER BEFUND, DER DAZU GEFUEHRT HAT: das Scharnier sitzt am Fingerfuss und der Schaft ist GERADE,
# also ist die Klaue ein nach unten offenes V, dessen Halboeffnung exakt dem Gelenkwinkel j5
# entspricht.  Bei j5=0.18 (Wuerfelgriff) betraegt die lichte Weite 14.7 mm bei z=60 und 24.8 mm
# bei z=88 -- der 24-mm-Wuerfel passt NUR ganz vorn hinein und beruehrt jede Backe an einer
# einzigen KANTE statt auf einer Flaeche.  Dazu passt [[act23-langlauf-1109]]: in 60-87% aller
# Fehlschlaege hat die Klaue nie etwas getragen.
#
# ACT14_FINGER_KNICK   Grad, die die letzten Millimeter des Schafts nach INNEN abknicken.
#                      Bezugsgroesse ist NICHT der 57.3-Grad-Nagel, sondern der Arbeitswinkel des
#                      Gelenks von ~10 Grad -- 5 Grad halbieren den V-Splay auf dem Endstueck.
# ACT14_FINGER_KNICK_Z Abstand des Knicks vom Schaftende in mm (Vorgabe 15).
# ACT14_FINGER_NAGEL   Grad, um die der Nagel ZURUECKGENOMMEN wird.  Leer = gleich dem Knick,
#                      dann behaelt der Nagel seine absolute Neigung von 57.3 Grad (sonst wandert
#                      er mit dem Endstueck auf 57.3+Knick).
#
# IST DIE VARIABLE NICHT GESETZT, wird die XML unveraendert von der Platte geladen -- der alte
# Greifer ist dann bitgleich der alte Greifer.  IST SIE GESETZT (auch auf 0), wird der Schaft in
# ZWEI Klotze geteilt.  Der Wert 0 ist deshalb der KONTROLLARM, der die Teilung allein misst:
# zwei buendige Klotze erzeugen andere Kontaktpunkte als einer, und dieser Effekt darf nicht dem
# Knick zugeschrieben werden.
# VORGABE seit 2026-08-30 (Nutzerentscheidung: der gelernte Zustand act23_state.pkl wurde ueber
# 1053 Episoden MIT diesem Greifer trainiert, die Vorgabe soll dazu passen).  Nagel 20 Grad =
# 57,2958 - 37,2958.  ACHTUNG, ehrlich dazugesagt: das saubere act23-A/B vom 2026-08-29 fand
# KEINEN Nutzen (-2,0 Punkte, p=0,76) -- die Vorgabe steht fuer die Uebereinstimmung mit dem
# Zustand, NICHT weil sie messbar besser waere.  Sie entfernt den Greifer ausserdem von der
# ECHTEN Hardware, der die XML nachgebildet ist.  Zurueck zum Original: ACT14_FINGER_KNICK
# hier wieder auf None setzen (eine Zeile).  Siehe [[act23-nagelneigung]].
_KNICK_ENV = os.environ.get("ACT14_FINGER_KNICK", "0")


def _finger_xml(knick_grad, knick_z_mm, nagel_grad):
    """Baut die beiden Finger-Bloecke.  Rahmen: Fingerursprung = Scharnier, +z entlang Schaft,
    +x nach INNEN fuer den linken Finger (der rechte ist daran gespiegelt)."""
    L, LB = 0.060, knick_z_mm / 1000.0                   # Schaftlaenge, Laenge des Endstuecks
    ZB = L - LB                                          # Hoehe des Knicks ueber dem Scharnier
    th = math.radians(knick_grad)
    c, s_ = math.cos(th), math.sin(th)
    # Endstueck: Mitte auf der gedrehten Achse ab dem Knickpunkt
    mx, mz = s_ * LB / 2.0, ZB + c * LB / 2.0
    # Nagel: sitzt starr auf dem Endstueck, also mitgedreht; Eigenwinkel um `nagel_grad` zurueck
    nx = s_ * LB + c * 0.009
    nz = ZB + c * LB - s_ * 0.009
    ne = 1.0 + th - math.radians(nagel_grad)

    def einer(seite, sp):                                # sp = +1 links, -1 rechts
        gelenk = ('<joint name="joint_5" type="hinge" axis="0 -1 0" range="0 3.1416"/>' if sp > 0
                  else '<joint name="joint_5_mimic" type="hinge" axis="0 -1 0" range="-3.1416 0"/>')
        return f'''                <body name="finger_{seite}" pos="{-0.01 * sp:g} 0.01 0.03">
                  {gelenk}
                  <geom name="finger_{seite}" size="0.008 0.005 {ZB / 2:.6f}" pos="0 0 {ZB / 2:.6f}" material="lightgray"/>
                  <geom name="finger_{seite}_tip" size="0.008 0.005 {LB / 2:.6f}" pos="{sp * mx:.6f} 0 {mz:.6f}" euler="0 {sp * th:.6f} 0" material="lightgray"/>
                  <geom name="claw_{seite}" type="box" size="0.004 0.006 0.006" pos="{sp * nx:.6f} 0 {nz:.6f}"
                        euler="0 {sp * ne:.6f} 0" material="lightgray"/>
                </body>'''

    return einer("left", +1) + chr(10) + einer("right", -1)


def _y_arm_xml(breite_mm):
    """obj_Y mit anderer ARMBREITE.  Nur die Breite aendert sich -- Armlaenge, Winkel (120 Grad),
    Hoehe und Farbe bleiben, damit die Messung EINE Variable isoliert.

    WOZU (2026-09-02): das Y wurde beim ALLERERSTEN Griffversuch geliefert und blieb flach bei
    60-73%, waehrend die etablierten Formen im selben Lauf bei 30-48% lagen -- die Greiffaehigkeit
    hat also SOFORT uebertragen, ohne Lernkurve.  Aber das Y besteht aus denselben 14-mm-Balken wie
    L/U/T/X.  Uebertragen hat sich damit "eine neue ANORDNUNG vertrauter Teile".  Ob es auch ueber
    die BAUTEILE traegt, ist offen -- und eine aeltere OOD-Messung sagte Nein (Engpass: die auf
    Wuerfel getrimmte Greifgeometrie).  Diese Variante prueft genau das, OHNE eine neue Form zu
    verbrauchen."""
    import math as _m
    hb = breite_mm / 2000.0
    teile = []
    for w in (90, 210, 330):
        r = _m.radians(w)
        px, py = 0.013 * _m.cos(r), 0.013 * _m.sin(r)
        teile.append(f'      <geom type="box" pos="{px:.5f} {py:.5f} 0" size="{hb:.5f} 0.013 0.012" '
                     f'euler="0 0 {_m.radians(w - 90):.5f}" rgba="0.85 0.1 0.45 1" '
                     f'density="700" friction="1.4 0.05 0.001"/>')
    kopf = '    <body name="obj_Y" pos="0.66 -0.6 0.012">'
    return (kopf + chr(10) + "      <freejoint/>" + chr(10)
            + chr(10).join(teile) + chr(10) + "    </body>")


# NEUE KOERPER FUER DIE LERNGESCHWINDIGKEIT (2026-09-25).  NICHT in der XML-Datei, sondern nur
# eingefuegt, wenn ein Lauf sie braucht: gemessen veraendern schon drei zusaetzliche, geparkte
# Koerper den Ablauf (Seed 11, Episode 2: 31 gegen 40 mm).  Eingefuegt wird, wenn ACT14_NEUE_KOERPER=1
# gesetzt ist oder ACT23_NOVEL_BODY auf einen von ihnen zeigt.
NEUE_KOERPER = ("obj_Zyl", "obj_V", "obj_Stern")
_NEUE_KOERPER_XML = """    <!-- NEUE KOERPER FUER DIE LERNGESCHWINDIGKEIT (2026-09-25, wiki/befunde/lerngeschwindigkeit-neuer-koerper.md).
         obj_Y ist fuer den heutigen Zustand NICHT mehr neu: die T-Klasse (neu-9) beansprucht es in
         10 von 12 Lagen.  Drei Kandidaten, die sich von allen achsparallelen Balkenformen absetzen;
         welcher wirklich neu ist, entscheidet eine Sonde, nicht diese Beschreibung.  Farben fest
         (die Farbmischung wuerfelt nur _FARB_KOERPER um).  Alle starten GEPARKT.
           obj_Zyl    Zylinder, 34 mm Durchmesser -- die erste RUNDE Silhouette
           obj_V      zwei Arme 14 x 30 mm im 60-Grad-Winkel, offen und asymmetrisch
           obj_Stern  sechs Arme: drei Balken 14 x 44 mm zu je 60 Grad, massive Mitte -->
    <body name="obj_Zyl" pos="0.58 -0.75 0.012">
      <freejoint/>
      <geom type="cylinder" size="0.017 0.012" rgba="0.95 0.55 0.1 1" density="700" friction="1.4 0.05 0.001"/>
    </body>
    <body name="obj_V" pos="0.62 -0.75 0.012">
      <freejoint/>
      <geom type="box" pos="-0.0075 0.0130 0" size="0.007 0.015 0.012" euler="0 0 0.52360" rgba="0.65 0.95 0.15 1" density="700" friction="1.4 0.05 0.001"/>
      <geom type="box" pos="0.0075 0.0130 0" size="0.007 0.015 0.012" euler="0 0 -0.52360" rgba="0.65 0.95 0.15 1" density="700" friction="1.4 0.05 0.001"/>
    </body>
    <body name="obj_Stern" pos="0.66 -0.75 0.012">
      <freejoint/>
      <geom type="box" size="0.007 0.022 0.012" euler="0 0 0.00000" rgba="0.45 0.12 0.9 1" density="700" friction="1.4 0.05 0.001"/>
      <geom type="box" size="0.007 0.022 0.012" euler="0 0 1.04720" rgba="0.45 0.12 0.9 1" density="700" friction="1.4 0.05 0.001"/>
      <geom type="box" size="0.007 0.022 0.012" euler="0 0 2.09440" rgba="0.45 0.12 0.9 1" density="700" friction="1.4 0.05 0.001"/>
    </body>

"""


def _modell_laden():
    """Vorgabe: XML unveraendert von der Platte.  Nur wenn ACT14_FINGER_KNICK oder ACT23_Y_ARM_W
    gesetzt ist, wird die betreffende Geometrie ersetzt."""
    _yw = os.environ.get("ACT23_Y_ARM_W", "")
    _neu = (os.environ.get("ACT14_NEUE_KOERPER", "0") == "1"
            or os.environ.get("ACT23_NOVEL_BODY", "") in NEUE_KOERPER)
    if _KNICK_ENV is None and not _yw and not _neu:
        return mujoco.MjModel.from_xml_path(ASSET)
    # KOMMA ALS DEZIMALTRENNER ZULASSEN: `$env:X=37.2958` weist in PowerShell eine ZAHL zu, und
    # beim Umwandeln in die Umgebungsvariable greift die Locale -- unter deutschem Windows kommt
    # "37,2958" an und float() bricht ab.  Das ist dem Nutzer 2026-08-28 genau so passiert.
    def _zahl(t, vorgabe):
        t = str(t).strip().replace(",", ".")
        return vorgabe if t == "" else float(t)

    knick = _zahl(_KNICK_ENV, 0.0)
    knick_z = _zahl(os.environ.get("ACT14_FINGER_KNICK_Z", ""), 15.0)   # Vorgabe 15 mm
    nagel = _zahl(os.environ.get("ACT14_FINGER_NAGEL", ""), 37.2958)  # Vorgabe: Nagel 20 Grad
    with io.open(ASSET, encoding="utf-8") as f:
        xml = f.read()
    if _KNICK_ENV is not None:
        a = xml.index('                <body name="finger_left"')
        b = xml.index("</body>", xml.index('name="claw_right"')) + len("</body>")
        xml = xml[:a] + _finger_xml(knick, knick_z, nagel) + xml[b:]
    if _yw:
        a = xml.index('    <body name="obj_Y"')
        b = xml.index("</body>", a) + len("</body>")
        xml = xml[:a] + _y_arm_xml(_zahl(_yw, 14.0)) + xml[b:]
    if _neu:
        a = xml.index('    <!-- SOCKEL: eine breite flache Platte')
        xml = xml[:a] + _NEUE_KOERPER_XML + xml[a:]
    return mujoco.MjModel.from_xml_string(xml)

ARM_JOINTS = ["joint_0", "joint_1", "joint_2", "joint_3", "joint_4"]   # 5 DOF (gripper = joint_5)
HOME = {"joint_0": 1.5708, "joint_1": 0.0, "joint_2": 0.0,
        "joint_3": 3.14, "joint_4": 1.5708, "joint_5": 0.76}
# the POSITIONING motors: base-yaw + shoulder + elbow ("3 motors with height", the act14 default),
# optionally + joint_3 (ACT14_DOF=4, act23): the second pitch was LOCKED at HOME=3.14 (fully folded,
# range end!) everywhere, which is THE reason for the small ~16x10cm workspace vs the arm's ~0.27m
# reach (user diagnosis).  Freeing it makes the arm REDUNDANT for a 3-D position -- reach control
# then also needs the learned CLAW-DIRECTION objective (see ArmBodyModel3D.reach_velocity), else the
# claw orientation drifts and grasping breaks.  j4/gripper stay separately controlled.
DOF = int(os.environ.get("ACT14_DOF", "3"))
ARM3 = ["joint_0", "joint_1", "joint_2"] + (["joint_3"] if DOF >= 4 else [])
WDIR = float(os.environ.get("ACT14_WDIR", "0.02"))   # claw-direction weight in the 4-DOF reach LS.
# 0.05 -> 0.02 am 2026-08-06, GEMESSEN (2 Seeds x 40 Ziele auf z=20mm, gepaart):
#   |z|-Fehler   14.6/9.4 mm  ->  8.9/5.3 mm   (p<0.0001 auf beiden Seeds)
#   Ausreisser >30mm  15%/8%  ->  8%/5%
#   seitlich      7.8/6.7 mm  ->  6.7/6.6 mm   (p=0.002 / p=0.72)
#   PREIS: Klauenabweichung 35.3/34.0 Grad -> 36.2/35.1, also +1.1 Grad (p<0.001, aber gegen eine
#   Grundabweichung von 34-36 Grad vernachlaessigbar).
# DER EIGENTLICHE BEFUND: das Gewicht steuert die Klauenhaltung im Bereich 0..0.05 KAUM (35.8 Grad
# bei 0.00 gegen 34.2 bei 0.05) -- die Neigung ist bei diesem Arm kinematisch erzwungen und waechst
# mit dem Radius (s. natural_tilt in world_model).  0.05 kostete also Position, ohne Orientierung zu
# kaufen.  Oberhalb 0.05 kippt es schnell: 0.10 -> 38mm Mittelfehler, 0.20 -> 105mm, 100% Ausreisser.
# ANLASS: der Arm griff systematisch ZU HOCH (+6.5mm Median, 100% der Ziele nach oben) und damit bei
# 12mm Wuerfel-Halbbreite an der Kante -- Drucksignatur der Fehlgriffe: zufassen 3.2 N, heben 0.04 N.
# OFFEN: das ist eine REICHGENAUIGKEITS-Messung, kein Liefernachweis.  Ob die Lieferquote steigt,
# muss ein GUI-Lauf zeigen.


class BracketArmSim:
    """Thin wrapper around the MuJoCo model of the real arm."""

    def __init__(self, render_wh=(360, 360)):
        self.m = _modell_laden()
        self.d = mujoco.MjData(self.m)
        self._renderer = mujoco.Renderer(self.m, height=render_wh[0], width=render_wh[1])
        self.grasp_sid = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_SITE, "grasp")
        self.reach_sid = self.grasp_sid                          # which site the FK/reach controls
        # qpos / dof addresses of the controllable arm joints (gripper handled separately)
        self.jqadr = {j: self.m.jnt_qposadr[self._jid(j)] for j in HOME}
        self.jdof = [self.m.jnt_dofadr[self._jid(j)] for j in ARM_JOINTS]
        self.act = {j: mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_ACTUATOR, "m" + j[-1]) for j in HOME}
        self.reset_home()

    def _jid(self, name):
        return mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_JOINT, name)

    def reset_home(self):
        mujoco.mj_resetData(self.m, self.d)
        for j, v in HOME.items():
            self.d.qpos[self.jqadr[j]] = v
            self.d.ctrl[self.act[j]] = v
        mujoco.mj_forward(self.m, self.d)

    def arm_home(self):
        """Return ONLY the arm to its home pose (objects keep their positions) — for
        continual episodes where the scene persists and just the target/cube changes."""
        for j, v in HOME.items():
            self.d.qpos[self.jqadr[j]] = v
            self.d.qvel[self.m.jnt_dofadr[self._jid(j)]] = 0.0
            self.d.ctrl[self.act[j]] = v
        mujoco.mj_forward(self.m, self.d)

    # ---- control ----
    def target(self, joint, value):
        self.d.ctrl[self.act[joint]] = float(value)

    def arm_targets(self):
        return np.array([self.d.ctrl[self.act[j]] for j in ARM_JOINTS])

    def set_arm_targets(self, q):
        for j, v in zip(ARM_JOINTS, q):
            lo, hi = self.m.jnt_range[self._jid(j)]
            self.d.ctrl[self.act[j]] = float(np.clip(v, lo, hi))

    def step(self, n=1):
        for _ in range(n):
            mujoco.mj_step(self.m, self.d)

    # ---- 3-motor subset (base+shoulder+elbow); wrist j3=pi (down), j4/gripper at home ----
    def arm_angles_full(self):
        """ARM3-Winkel + die Zusatzgelenke (Wrist, Greifer), wie das Koerpermodell sie erwartet."""
        return np.array([self.d.qpos[self.jqadr[j]] for j in ARM3]
                        + [self.d.qpos[self.jqadr["joint_4"]], self.d.qpos[self.jqadr["joint_5"]]])

    def arm3_angles(self):
        return np.array([self.d.qpos[self.jqadr[j]] for j in ARM3])

    def set_arm3_targets(self, q3):
        j3 = q3[3] if len(ARM3) >= 4 else HOME["joint_3"]
        self.set_arm_targets([q3[0], q3[1], q3[2], j3, HOME["joint_4"]])

    def arm3_range(self):
        return np.array([self.m.jnt_range[self._jid(j)] for j in ARM3])   # (3,2)

    def set_object(self, name, xy, z=0.008, yaw=0.0):
        bid = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, name)
        jadr = self.m.body_jntadr[bid]; qadr = self.m.jnt_qposadr[jadr]; vadr = self.m.jnt_dofadr[jadr]
        self.d.qpos[qadr:qadr + 3] = [xy[0], xy[1], z]
        self.d.qpos[qadr + 3:qadr + 7] = [np.cos(yaw / 2), 0.0, 0.0, np.sin(yaw / 2)]   # z-rotation
        self.d.qvel[vadr:vadr + 6] = 0.0

    def obj_pose7(self, name):
        """Die VOLLE Freikoerper-Pose [x,y,z,qw,qx,qy,qz] als Kopie.

        set_object() schreibt eine reine z-Drehung und richtet damit ein umgekipptes Objekt
        stillschweigend wieder auf.  Fuer eine Wiederholungsmessung (ACT23_EXV) muss die Szene
        exakt so zurueckkommen, wie sie war -- auch schraeg."""
        bid = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, name)
        qadr = self.m.jnt_qposadr[self.m.body_jntadr[bid]]
        return self.d.qpos[qadr:qadr + 7].copy()

    def set_obj_pose7(self, name, q7):
        """Gegenstueck zu obj_pose7: Pose exakt zuruecksetzen, Geschwindigkeit auf null."""
        bid = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, name)
        jadr = self.m.body_jntadr[bid]; qadr = self.m.jnt_qposadr[jadr]; vadr = self.m.jnt_dofadr[jadr]
        self.d.qpos[qadr:qadr + 7] = np.asarray(q7, float)
        self.d.qvel[vadr:vadr + 6] = 0.0

    def obj_yaw(self, name):
        """The object's z-rotation (radians) from its body quaternion (long-axis orientation in the table)."""
        q = self.d.xquat[mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, name)]
        return float(np.arctan2(2.0 * (q[0] * q[3] + q[1] * q[2]), 1.0 - 2.0 * (q[2] ** 2 + q[3] ** 2)))

    def set_object_size(self, name, half):
        """Set a box object's half-extents at runtime (cube vs wide block) for affordances."""
        bid = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, name)
        self.m.geom_size[self.m.body_geomadr[bid]] = np.asarray(half, float)

    def joint_range(self, name):
        jid = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_JOINT, name)
        return np.asarray(self.m.jnt_range[jid], float)

    def fk_truth(self, q3):
        """Eye-hand 'observation': set the joints, forward kinematics -> grasp position.
        q3 = ARM3-Winkel, optional gefolgt von joint_4/joint_5 (die das Koerpermodell seit
        2026-08-08 als EINGANG kennt -- vorher standen sie hier fest auf HOME, weshalb der Wrist
        fuer die gelernte Kinematik unsichtbar war, obwohl er den Reichpunkt um 21mm verschiebt)."""
        q3 = np.asarray(q3, float)
        for j, v in zip(ARM3, q3):
            self.d.qpos[self.jqadr[j]] = float(v)
        if "joint_3" not in ARM3:
            self.d.qpos[self.jqadr["joint_3"]] = HOME["joint_3"]
        _extra = q3[len(ARM3):]
        self.d.qpos[self.jqadr["joint_4"]] = float(_extra[0]) if len(_extra) > 0 else HOME["joint_4"]
        if len(_extra) > 1:
            self.d.qpos[self.jqadr["joint_5"]] = float(_extra[1])
        mujoco.mj_forward(self.m, self.d)
        return self.grasp_pos()

    def grip_pressure(self, finger="left"):
        """DRUCKMESSSTREIFEN an der INNENSEITE EINES Fingers -- ein Skalar (Newton), wie ihn der
        geplante echte Aufbau liefert (ein Streifen, ein Finger, Innenflaeche).

        Bewusst NICHT beidseitig und nicht als Vektor: der reale Sensor sitzt auf der Greifflaeche
        eines Fingers und misst die Normalkraft, mit der dieser gegen etwas drueckt.  Genau diese
        Einschraenkung macht das Signal aussagekraeftig -- ein Objekt ZWISCHEN den Fingern drueckt
        auf die Innenflaeche, ein Finger der beim Zufahren seitlich gegen das Objekt stoesst (der
        diagonale Griff, den der User beobachtet) erzeugt dort wenig oder nichts.

        Gefiltert wird ueber die Kontakt-POSITION im Finger-Frame (robuster als die Normalen-
        Richtung): nur Kontakte auf der zur Gegenklaue zeigenden Seite zaehlen.  Summe der
        Normalkraefte aller solchen Kontakte."""
        import mujoco
        key = f"_press_{finger}"
        if not hasattr(self, key):
            pad = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_GEOM, f"claw_{finger}")
            shaft = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_GEOM, f"finger_{finger}")
            bid = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, f"finger_{finger}")
            #   claw_left sitzt bei +x im linken Finger-Frame, claw_right bei -x im rechten:
            #   die Innenseite ist also die Richtung, in der die Klauenflaeche sitzt.
            inner = +1.0 if finger == "left" else -1.0
            # EIGENKONTAKTE ausschliessen: beim Schliessen ohne Objekt beruehren sich die Klauen und
            # erzeugten 7.67 N (gemessen) -- das haette jedes Objektsignal ueberdeckt.  Ein realer
            # Streifen auf der GREIFFLAECHE misst, was der Finger gegen die UMWELT drueckt, nicht was
            # der eigene Greifer an seinen Kanten tut.
            own = set()
            # bei umgebauter Fingergeometrie (ACT14_FINGER_KNICK) gehoert das abgeknickte Endstueck
            # ZUR GREIFFLAECHE -- es muss also messen UND als Eigenkontakt ausgeschlossen sein.
            tip = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_GEOM, f"finger_{finger}_tip")
            for nm in ("claw_left", "claw_right", "finger_left", "finger_right",
                       "finger_left_tip", "finger_right_tip", "gripper_base"):
                gi = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_GEOM, nm)
                if gi >= 0:
                    own.add(gi)
            gids = {pad, shaft} | ({tip} if tip >= 0 else set())
            setattr(self, key, (gids, bid, inner, own))
        gids, bid, inner, own = getattr(self, key)
        total, f = 0.0, np.zeros(6)
        for c in range(int(self.d.ncon)):
            con = self.d.contact[c]
            if con.geom1 not in gids and con.geom2 not in gids:
                continue
            other = con.geom2 if con.geom1 in gids else con.geom1
            if other in own:                          # Finger gegen Finger -> kein Umweltkontakt
                continue
            R = self.d.xmat[bid].reshape(3, 3)
            loc = R.T @ (np.asarray(con.pos, float) - np.asarray(self.d.xpos[bid], float))
            if loc[0] * inner <= 0.0:                 # Kontakt auf der AUSSENseite -> Streifen spuert nichts
                continue
            mujoco.mj_contactForce(self.m, self.d, c, f)
            total += abs(float(f[0]))                 # Normalkraft im Kontaktframe
        return float(total)

    def grasp_dir(self):
        """World direction the CLAW points along (the gripper body's +z at the grasp site) --
        the orientation the 4-DOF reach must PRESERVE (learned alongside the FK by babbling)."""
        return self.d.site_xmat[self.grasp_sid].reshape(3, 3)[:, 2].copy()

    def set_reach_site(self, name):
        self.reach_sid = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_SITE, name)

    def jaw_mid(self):
        """Weltposition der BACKENMITTE (Mittelpunkt der beiden Klauenbacken).

        Das ist der Punkt, zwischen dem ein gegriffenes Objekt sitzen SOLL -- nicht der Reichpunkt
        (site "contact"), der 4-9mm dahinter liegt (s. claw_fwd)."""
        import mujoco as _mj
        if getattr(self, "_claw_gid", None) is None:
            self._claw_gid = tuple(_mj.mj_name2id(self.m, _mj.mjtObj.mjOBJ_GEOM, n)
                                   for n in ("claw_left", "claw_right"))
        a, b = self._claw_gid
        return 0.5 * (self.d.geom_xpos[a] + self.d.geom_xpos[b])

    def in_claw(self, obj_xy):
        """Lage eines Objekts RELATIV ZUR BACKENMITTE, im Klauenrahmen (mm): (quer, tief).

        quer = entlang der Finger-Trennachse; 0 = mittig zwischen den Backen.
        tief = entlang der Klauen-Vorwaertsachse; 0 = auf Hoehe der Backenmitte, + = weiter vorn.
        WOZU (2026-08-14): gemessen kostet ein naher Nachbar 13 Prozentpunkte Lieferung, OHNE dass
        der Griff scheitert (100% Kontakt, 100% gehalten) -- die Vermutung ist, dass der verschmolzene
        Blob den Greifpunkt verschiebt, das Objekt AUSSERMITTIG in der Klaue sitzt und dieser Versatz
        bis zur Ablage durchwandert.

        GEMESSEN 2026-08-14 (44 Episoden) -- die Vermutung traegt NICHT, und die Groesse ist nur
        halb verlaesslich:
          * naher Nachbar verschiebt die Lage nicht (quer p=0.50, tief p=0.33)
          * die Lage sagt den Ablagefehler nicht vorher (rho +0.14, p=0.45)
          * sie trennt Erfolg nicht von Fehlschlag (p=0.28 / p=0.67)
        VALIDIERUNG der Groesse selbst (Versatz muesste den Zufassdruck senken):
          |tief| -> Druck  rho=-0.31 p=0.044   (richtige Richtung, schwach)
          |quer| -> Druck  rho=-0.01 p=0.93    (KEIN Zusammenhang)
        Die Querachse misst also vermutlich den falschen MOMENT: der Aufzeichnungspunkt haengt an
        _attempted, das mit 30mm seitlicher Toleranz ausloest, waehrend die Klaue noch zufaehrt --
        die Lage ist da noch nicht eingeschwungen.  Wer die Querachse braucht, muss den Moment
        zuerst nach hinten legen (z.B. auf das Druckmaximum)."""
        import numpy as _np
        e = _np.asarray(obj_xy, float)[:2] - _np.asarray(self.jaw_mid(), float)[:2]
        f = _np.asarray(self.claw_fwd(), float)[:2]
        n = float(_np.linalg.norm(f))
        f = f / n if n > 1e-9 else _np.array([0.0, 1.0])
        q = _np.array([-f[1], f[0]])                      # Trennachse = quer zur Vorwaertsachse
        return 1000.0 * float(e @ q), 1000.0 * float(e @ f)

    def claw_fwd(self):
        """Einheitsvektor (Welt), in dessen Richtung die BACKENMITTE vor dem Reichpunkt liegt.

        GEMESSEN 2026-08-07: der Reichpunkt (site "contact") ist NICHT die Backenmitte.  Die liegt
        bei geoeffneter Klaue 4.4mm davor und wandert beim SCHLIESSEN auf 8.6mm -- bei einer
        Backentiefe von nur +-6mm schliessen die Backen also VOR dem Objekt und erwischen
        bestenfalls dessen Hinterkante.  Genau das erzeugt die Fehlgriff-Signatur aus den Logs:
        viel Druck beim Zufassen (die Backen druecken an der Kante), null beim Heben.
        Der Versatz liegt im SITE-Rahmen konstant auf der lokalen z-Achse, dreht also mit dem
        Wrist mit -- ein weltfester xy-Offset (wie die Greifpunkt-Kandidaten) kann ihn NICHT
        ausgleichen, was rueckblickend erklaert, warum jene Linie nichts brachte."""
        R = self.d.site_xmat[self.reach_sid].reshape(3, 3)
        v = R[:, 2].copy(); v[2] = 0.0                       # in der Tischebene, die Hoehe regelt aim_z
        n = float(np.linalg.norm(v))
        return v / n if n > 1e-9 else np.array([0.0, 1.0, 0.0])

    def set_target_marker(self, xy, z=0.001):
        bid = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, "target_marker")
        self.d.mocap_pos[self.m.body_mocapid[bid]] = [xy[0], xy[1], z]

    # ---- state ----
    def grasp_pos(self):
        return self.d.site_xpos[self.reach_sid].copy()

    def obj_pos(self, name):
        return self.d.xpos[mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, name)].copy()

    def claw_yaw(self):
        """Table-plane YAW (radians) of the finger-separation axis (the gripper's local x in world).
        This is what joint_4 (wrist-roll) controls in the grasp pose; the orientation the claws grip along."""
        x = self.d.site_xmat[self.grasp_sid].reshape(3, 3)[:, 0]    # finger-separation axis in world
        return float(np.arctan2(x[1], x[0]))

    def set_arm_wrist_targets(self, q3, j4, j3=None):
        """Command the positioning motors + the wrist-ROLL joint_4 (j3 = wrist-pitch; defaults to
        q3[3] at 4 DOF, else HOME)."""
        if j3 is None:
            j3 = q3[3] if len(ARM3) >= 4 else HOME["joint_3"]
        self.set_arm_targets([q3[0], q3[1], q3[2], j3, j4])

    def site_jacobian(self):
        """3x5 position Jacobian of the grasp site w.r.t. the 5 arm joints."""
        jacp = np.zeros((3, self.m.nv))
        mujoco.mj_jacSite(self.m, self.d, jacp, None, self.grasp_sid)
        return jacp[:, self.jdof]

    def render(self, cam="overview"):
        self._renderer.update_scene(self.d, camera=cam)
        return self._renderer.render()


def reach_step(sim, target_xyz, gain=2.0, max_dq=0.03):
    """One damped-least-squares step of the grasp site toward target_xyz (analytic Jacobian)."""
    err = np.asarray(target_xyz) - sim.grasp_pos()
    J = sim.site_jacobian()
    dq = J.T @ np.linalg.solve(J @ J.T + 0.02 * np.eye(3), gain * err)
    m = float(np.max(np.abs(dq)))
    if m > max_dq:
        dq *= max_dq / m
    sim.set_arm_targets(sim.arm_targets() + dq)
    return float(np.linalg.norm(err))


class ArmBodyModel3D:
    """The agent's LEARNED 3-D kinematics for the positioning motors.  The forward kinematics is
    exactly LINEAR in the lifted feature set  Φ(θ) = [cosθ0·g, sinθ0·g, g]  (base-yaw rotates the
    pitch plane; g = cos/sin of the CUMULATIVE pitch angles with both signs, so least-squares picks
    the true chain combo), learned by babbling -- the 3-D analogue of act12's linear-in-features
    body model.  At 4 DOF (joint_3 freed) the SAME babble additionally learns the CLAW DIRECTION
    (Wd, also exactly linear in Φ): the arm is then REDUNDANT for a 3-D position and the reach
    solves a weighted stacked least-squares [position; soft claw-direction], else the claw
    orientation would drift with the null space and grasping breaks."""

    def __init__(self, rng=None, dof=None, aux=None):
        self.rng = rng or np.random.default_rng(0)
        self.dof = int(dof) if dof is not None else len(ARM3)
        # ZUSATZGELENKE als EINGANG: joint_4 (Wrist) und joint_5 (Greifer) werden nicht vom
        # Reichregler gestellt, verschieben den Reichpunkt aber -- GEMESSEN: joint_4 um 21.2mm
        # ueber seinen Bereich, joint_5 um 0.0mm.  Weil das Babbeln sie auf HOME liess, war der
        # Wrist fuer das Modell unsichtbares Rauschen: Vorhersagefehler 7.7mm bei HOME-Wrist gegen
        # 10.0mm bei zufaelligem (p=6.6e-07).  Als cos/sin-Paar (zirkulaer, wie ueberall im Projekt)
        # in die Merkmalsbasis; reach_velocity liefert weiterhin NUR dq fuer ARM3.
        # joint_5 traegt fuer den KONTAKTPUNKT nachweislich nichts -- es ist mit drin, weil es die
        # BACKENMITTE verschiebt (4.1mm offen -> 8.6mm geschlossen, s. CLAW_OFF) und das Koerpermodell
        # damit spaeter lernen kann, wo die Backen stehen, statt es aus einer Konstante zu nehmen.
        self.aux = tuple(aux) if aux is not None else ("joint_4", "joint_5")
        self.NF = 3 * (7 if self.dof == 3 else 15) + 1 + 2 * len(self.aux)
        self.W = np.zeros((self.NF, 3)); self.Wd = np.zeros((self.NF, 3))
        self.dir_ref = None                              # claw direction to PRESERVE (from babble poses)
        self.last_surprise = None

    def _feat(self, q):
        """q = ARM3-Winkel, optional gefolgt von den aux-Gelenken (Wrist, Greifer).

        ALTLAST-FEST: ein VOR 2026-08-08 gespeichertes Modell hat kein `aux`-Attribut.  getattr
        liefert dann () und das Modell verhaelt sich exakt wie frueher -- wichtig, weil sonst schon
        der Persistenz-Funktionstest scheitert und der GESAMTE Zustand verworfen wird (genau das ist
        beim Bauen passiert, und es ist derselbe Fehlertyp wie die fest verdrahtete Zustandsbreite
        im Funktionstest).  Die eigentliche Umstellung uebernimmt danach die NF-Pruefung in
        pc_act23, die das Modell mit der neuen Merkmalsbasis neu babbelt."""
        aux_names = getattr(self, "aux", ())
        q = np.asarray(q, float)
        aux = q[self.dof:self.dof + len(aux_names)] if len(q) > self.dof else np.zeros(len(aux_names))
        t0, t1, t2 = float(q[0]), float(q[1]), float(q[2])
        # the elbow axis is reversed + 90deg offsets, so include BOTH (θ1+θ2) and (θ1-θ2) —
        # least-squares picks the right combo; at 4 DOF likewise all (θ1±θ2±θ3) combos.
        g = [1.0, np.cos(t1), np.sin(t1),
             np.cos(t1 + t2), np.sin(t1 + t2), np.cos(t1 - t2), np.sin(t1 - t2)]
        if self.dof >= 4:
            t3 = float(q[3])
            for s in (t1 + t2 + t3, t1 + t2 - t3, t1 - t2 + t3, t1 - t2 - t3):
                g += [np.cos(s), np.sin(s)]
        g = np.array(g)
        return np.concatenate([np.cos(t0) * g, np.sin(t0) * g, g,
                               np.cos(aux), np.sin(aux)])

    def _aug(self, q):
        return np.append(self._feat(q), 1.0)                          # +bias

    def fk(self, q):
        return self._aug(q) @ self.W

    def claw_dir(self, q):
        """Predicted world direction the claw points along (unit; the learned Wd readout)."""
        d = self._aug(q) @ self.Wd
        n = float(np.linalg.norm(d))
        return d / n if n > 1e-9 else d

    def babble(self, sim, steps):
        rng3 = sim.arm3_range()
        # AUCH die Zusatzgelenke bebabbeln: sie standen bisher auf HOME, weshalb das Modell den
        # Wrist nie zu sehen bekam.  Ohne Streuung hier bleibt die neue Merkmalsspalte konstant und
        # traegt nichts.
        arng = np.array([sim.joint_range(j) for j in self.aux], float) if self.aux else np.zeros((0, 2))
        X = np.empty((steps, self.NF)); Y = np.empty((steps, 3)); D = np.empty((steps, 3))
        for i in range(steps):
            q3 = self.rng.uniform(rng3[:, 0], rng3[:, 1])
            qa = self.rng.uniform(arng[:, 0], arng[:, 1]) if len(arng) else np.zeros(0)
            q = np.concatenate([q3, qa])
            X[i] = self._aug(q); Y[i] = sim.fk_truth(q); D[i] = sim.grasp_dir()
        G = np.linalg.inv(X.T @ X + 1e-6 * np.eye(self.NF))           # ridge least squares
        self.W = G @ (X.T @ Y); self.Wd = G @ (X.T @ D)
        # the claw direction to PRESERVE at 4 DOF: MEASURED as the mean claw direction over LOW
        # (table-level) poses with joint_3 at its classic HOME, then reduced to its VERTICAL
        # component.  The measured mean has a small (~4 deg) lean IN THE ARM'S PLANE -- as a
        # WORLD-frame reference that lean is only right straight ahead and TWISTS the reach at
        # large bearings (measured: all |x|=0.125 slot grasps failed, centre slots fine); the
        # vertical part is bearing-invariant by construction.
        ref = []
        for _ in range(200):
            q = self.rng.uniform(rng3[:, 0], rng3[:, 1])
            if self.dof >= 4:
                q[3] = HOME["joint_3"]
            if sim.fk_truth(q)[2] < 0.06:
                ref.append(sim.grasp_dir().copy())
        d = np.mean(ref, axis=0) if ref else sim.grasp_dir().copy()
        self.dir_ref = np.array([0.0, 0.0, np.sign(d[2]) if abs(d[2]) > 1e-9 else -1.0])

    def observe(self, q, hand_obs, lr=0.05):            # lifelong / vision refinement
        a = self._aug(q); err = a @ self.W - np.asarray(hand_obs, float)
        s = float(np.linalg.norm(err))
        self.last_surprise = s if self.last_surprise is None else 0.9 * self.last_surprise + 0.1 * s
        self.W -= lr * np.outer(a, err)

    def jacobian(self, q, eps=1e-4, W=None):
        W = self.W if W is None else W
        q = np.asarray(q, float)
        J = np.zeros((3, self.dof))
        for i in range(self.dof):
            dq = np.zeros(len(q)); dq[i] = eps      # nur die STELLGELENKE variieren; die
            #   Zusatzgelenke (Wrist/Greifer) sind Eingang, keine Stellgroesse
            J[:, i] = (self._aug(q + dq) @ W - self._aug(q - dq) @ W) / (2 * eps)
        return J

    def reach_velocity(self, q, target, gain=2.0, max_dq=0.03, damp=0.04):
        err = np.asarray(target, float) - self.fk(q)
        J = self.jacobian(q)
        if self.dof >= 4 and self.dir_ref is not None:
            # REDUNDANT arm: solve [position error; SOFT claw-direction error] as one weighted
            # stacked least-squares.  UNITS matter (measured: 0.35 made every grasp fail): the
            # position residual is gain*metres (~0.02-0.2), the direction residual is O(1), so the
            # direction weight must be SMALL for position to win wherever the two conflict -- the
            # extra DOF then only spends its null space on keeping the claw in grasp orientation.
            wd = WDIR
            #   (an endgame-boosted adaptive weight was TRIED against the mid-band envelope hole --
            #   no effect, 0/24: the hole is not a weight issue but likely the reach settling into an
            #   elbow BRANCH whose vertical-claw solution is unreachable by gradient; open work item)
            derr = self.dir_ref - self.claw_dir(q)
            A = np.vstack([J, wd * self.jacobian(q, W=self.Wd)])
            e = np.concatenate([gain * err, wd * derr])
            dq = A.T @ np.linalg.solve(A @ A.T + damp * np.eye(6), e)
        else:
            dq = J.T @ np.linalg.solve(J @ J.T + damp * np.eye(3), gain * err)
        m = float(np.max(np.abs(dq)))
        if m > max_dq:
            dq *= max_dq / m
        return dq


class CamViz:
    def __init__(self, cam):
        import matplotlib.pyplot as plt
        self.plt = plt; plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(5.2, 5.2))
        self.ax.set_title(f"act14 — MuJoCo {cam} camera"); self.ax.axis("off")
        self.im = self.ax.imshow(np.zeros((10, 10, 3), np.uint8))

    def update(self, frame, txt=""):
        self.im.set_data(frame)
        self.ax.set_xlabel(txt)
        self.fig.canvas.draw_idle(); self.fig.canvas.flush_events()

    def hold(self):
        self.plt.ioff(); self.plt.show()


def run_learned_reach(sim, viz, CAM, HEADLESS):
    """3-motor arm driven by the agent's LEARNED 3-D kinematics (babbled MLP FK + Jacobian).
    Validates that the net can do the coupled base+shoulder+elbow kinematics WITH height by
    reaching the grasp point to each cube on the table."""
    body = ArmBodyModel3D(rng=np.random.default_rng(5))
    print("  babbling the arm to learn its 3-D kinematics (linear-in-features, 4000 poses) ...")
    body.babble(sim, 4000)
    # FK accuracy on fresh random poses
    rng3 = sim.arm3_range(); errs = []
    for _ in range(400):
        q = np.random.default_rng().uniform(rng3[:, 0], rng3[:, 1])
        errs.append(np.linalg.norm(body.fk(q) - sim.fk_truth(q)))
    print(f"  learned FK error: mean {np.mean(errs)*1000:.1f} mm  max {np.max(errs)*1000:.1f} mm")

    results = []
    for nm in ("obj_red", "obj_green", "obj_blue"):
        sim.reset_home(); sim.target("joint_3", HOME["joint_3"]); sim.step(250)
        tgt = sim.obj_pos(nm) + np.array([0.0, 0.0, 0.03])     # 3 cm above the cube
        for k in range(700):
            q3 = sim.arm3_angles()                              # joint encoders (felt)
            dq = body.reach_velocity(q3, tgt)
            sim.set_arm3_targets(q3 + dq); sim.step(2)
            if viz is not None and k % 4 == 0:
                e = np.linalg.norm(tgt - sim.grasp_pos())
                viz.update(sim.render(CAM), f"reach {nm}  learned-kin  {e*1000:.0f} mm")
        err_mm = np.linalg.norm(tgt - sim.grasp_pos()) * 1000
        results.append((nm, err_mm)); print(f"  reach {nm}: {err_mm:.0f} mm  (grasp {np.round(sim.grasp_pos(),3)})")
    print(f"  == learned-kinematics reach: mean {np.mean([r for _,r in results]):.0f} mm over {len(results)} cubes ==")
    if viz is not None:
        print("  [viz] close the window to exit."); viz.hold()


_RX0 = float(os.environ.get("ACT_REACH_X0", "-0.11"))          # x edges back to the ORIGINAL small patch:
_RX1 = float(os.environ.get("ACT_REACH_X1", "0.11"))           #   the LEFT extension to -0.17 was measured to
_RY0 = float(os.environ.get("ACT_REACH_Y0", "0.07"))           #   HALVE the learned policy (pc_act21 A 50%->
_RY1 = float(os.environ.get("ACT_REACH_Y1", "0.21"))           #   14%): the policy can't generalize over the
REACH_XY = (np.array([_RX0, _RY0]), np.array([_RX1, _RY1]))    #   bigger state space with its training budget.
#   The parallel camera + homography are KEPT; only the placement region is back to the proven size.
#   (env-overridable: ACT_REACH_X0/X1/Y0/Y1 to re-extend for experiments.)


def _rand_xy(rng):
    return rng.uniform(REACH_XY[0], REACH_XY[1])


J5_OPEN, J5_CLOSED = 1.8, 0.0      # gripper: OPEN = fingers spread+raised; CLOSED = together+low


def run_carry_task(sim, body, viz, CAM, HEADLESS, episodes=12, cmd_name="obj_red"):
    """Manipulation on the 3-motor arm + gripper with REAL contact physics: GRASP the COMMANDED
    cube and CARRY it to a target on the table.  Reach uses the LEARNED kinematics; grasping is
    genuine MuJoCo contact (the gripper squeezes the cube and friction holds it).  A small phase
    machine: go above -> lower -> close -> lift -> carry -> place -> release.  Perception is
    privileged sim state for now (camera = Step 2)."""
    rng = np.random.default_rng(1)
    objs = ["obj_red", "obj_green", "obj_blue"]
    OVER_Z, GRIP_Z, CARRY_Z, NEAR, TOL, CAP = 0.07, 0.02, 0.11, 0.012, 0.030, 1600
    deliveries = 0
    for ep in range(episodes):
        sim.reset_home(); sim.target("joint_3", HOME["joint_3"]); sim.target("joint_5", J5_OPEN)
        pts = []
        for nm in objs:
            p = _rand_xy(rng)
            while any(np.linalg.norm(p - q) < 0.07 for q in pts):
                p = _rand_xy(rng)
            pts.append(p); sim.set_object(nm, p)
        c0 = pts[objs.index(cmd_name)]
        tgt = _rand_xy(rng)
        while np.linalg.norm(tgt - c0) < 0.06:
            tgt = _rand_xy(rng)
        mujoco.mj_forward(sim.m, sim.d); sim.step(150)
        phase, dwell = "over", 0
        for k in range(CAP):
            c = sim.obj_pos(cmd_name)[:2]; h = sim.grasp_pos(); hxy = h[:2]; hz = h[2]
            closed = phase in ("close", "lift", "carry", "place")
            if phase == "over":
                aim = np.array([c[0], c[1], OVER_Z])
                if np.linalg.norm(hxy - c) < NEAR:
                    phase = "lower"
            elif phase == "lower":
                aim = np.array([c[0], c[1], GRIP_Z])
                if hz < GRIP_Z + 0.012:
                    phase, dwell = "close", 0
            elif phase == "close":
                aim = np.array([c[0], c[1], GRIP_Z]); dwell += 1
                if dwell > 90:
                    phase = "lift"
            elif phase == "lift":
                aim = np.array([c[0], c[1], CARRY_Z])
                if hz > CARRY_Z - 0.015:
                    phase = "carry"
            elif phase == "carry":
                aim = np.array([tgt[0], tgt[1], CARRY_Z])
                if np.linalg.norm(hxy - tgt) < NEAR:
                    phase = "place"
            elif phase == "place":
                aim = np.array([tgt[0], tgt[1], GRIP_Z])
                if hz < GRIP_Z + 0.015:
                    phase, dwell = "release", 0
            else:  # release
                aim = np.array([tgt[0], tgt[1], GRIP_Z]); dwell += 1
                if dwell > 60:
                    break
            sim.target("joint_5", J5_CLOSED if closed else J5_OPEN)
            q3 = sim.arm3_angles(); sim.set_arm3_targets(q3 + body.reach_velocity(q3, aim)); sim.step(2)
            if viz is not None and k % 5 == 0:
                viz.update(sim.render(CAM), f"ep {ep} carry {cmd_name} [{phase}]"
                                            f"  obj->tgt {np.linalg.norm(c-tgt)*1000:.0f}mm")
        err = np.linalg.norm(sim.obj_pos(cmd_name)[:2] - tgt)
        ok = err < TOL
        deliveries += ok
        print(f"  ep {ep:2d}: {'OK ' if ok else 'no '} obj->tgt {err*1000:.0f} mm")
    print(f"  == carry task (real grasp+carry, learned 3-D kinematics): DELIVERED {deliveries}/{episodes} ==")
    if viz is not None:
        print("  [viz] close the window to exit."); viz.hold()


def main():
    HEADLESS = os.environ.get("ACT14_HEADLESS", "0") == "1"
    CAM = os.environ.get("ACT14_CAM", "overview").lower()
    STEPS = int(os.environ.get("ACT14_STEPS", "1200"))
    TARGET = os.environ.get("ACT14_TARGET", "obj_red")
    MODE = os.environ.get("ACT14_MODE", "demo").lower()        # demo (analytic) | learn (learned kin)

    print("act14 — real 5-DOF arm in MuJoCo (3-D gravity + contacts + overhead camera)")
    sim = BracketArmSim()
    print(f"  model: nq={sim.m.nq} actuators={sim.m.nu} cameras={sim.m.ncam}  mode={MODE}")

    viz = None
    if not HEADLESS:
        try:
            import matplotlib  # noqa
            viz = CamViz(CAM)
        except Exception as e:
            print(f"  [viz] matplotlib unavailable ({e}); running headless"); HEADLESS = True

    if MODE == "learn":
        run_learned_reach(sim, viz, CAM, HEADLESS)
        return
    if MODE in ("carry", "task", "push"):
        body = ArmBodyModel3D(rng=np.random.default_rng(5))
        print("  babbling the arm to learn its 3-D kinematics ..."); body.babble(sim, 4000)
        run_carry_task(sim, body, viz, CAM, HEADLESS,
                       episodes=int(os.environ.get("ACT14_EPISODES", "12")), cmd_name=TARGET)
        return

    print(f"  analytic-Jacobian reach demo toward '{TARGET}'")
    sim.step(300)                                  # let the arm settle at home under gravity
    last = 1e9
    for k in range(STEPS):
        tgt = sim.obj_pos(TARGET) + np.array([0.0, 0.0, 0.04])   # pre-grasp: 4 cm above the cube
        last = reach_step(sim, tgt)
        sim.step(2)
        if viz is not None and k % 4 == 0:
            viz.update(sim.render(CAM), f"step {k}/{STEPS}  grasp->target {last*1000:.0f} mm")
        elif HEADLESS and k in (0, STEPS // 2, STEPS - 1):
            import matplotlib.image as mpimg
            mpimg.imsave(f"act14_reach_{k}.png", sim.render(CAM))

    print(f"  final grasp->target distance: {last*1000:.1f} mm  (grasp {np.round(sim.grasp_pos(),3)},"
          f" target {np.round(sim.obj_pos(TARGET),3)})")
    print("  arm joints (rad):", np.round([sim.d.qpos[sim.jqadr[j]] for j in ARM_JOINTS], 3))
    if viz is not None:
        print("  [viz] close the window to exit."); viz.hold()


if __name__ == "__main__":
    main()
