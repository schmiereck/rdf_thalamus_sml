r"""pc_act23.py — a SELF-LEARNING grasper: a self-supervised world/outcome model + uncertainty-aware acting.

The user's overarching goal is an architecture that LEARNS new shapes/positions ITSELF (no scripted
teacher); beating the teacher is NOT the criterion (see the memory note user-goal-self-learning).  This
driver builds that loop on the arm:

  * the agent TRIES grasp actions (grasp-point offset + wrist) in perceived situations and observes whether
    the object is DELIVERED -> the only training signal is its OWN outcome (self-supervised);
  * a WorldModelModule (ensemble) learns P(deliver | perceived situation, action) with UNCERTAINTY;
  * it ACTS on the lower confidence bound (mu - lam*sigma), so it deviates from a safe default only where it
    is CONFIDENT -> it never underperforms the default (the fix for the naive-argmax model exploitation that
    made an earlier attempt WORSE than the teacher).

Four honest checks (success here = self-acquisition + generalisation + improvement + safety, NOT > teacher):
  1. model AUC for P(deliver) on held-out trials;
  2. SAFETY: LCB acting >= the WRIST_ALIGN default, and clearly better than naive argmax (lam=0);
  3. GENERALISATION: trained on cube+L only -> does it help / not hurt on the HELD-OUT U;
  4. LEARNING CURVE: U delivery as the agent collects more of its OWN U experience.

ACT23_MODE = "diag" (default) runs the SIGNAL-RICH validation -- a diagonally-oriented ELONGATED object whose
delivery genuinely depends on the wrist.  The teacher's wrist heuristic is DISABLED (a fixed wrist as the
no-privilege default); the world model learns -- from its OWN outcomes -- which wrist delivers as a function
of the PERCEIVED long-axis orientation (ObjectOrientationModule, camera, not the privileged sim yaw).  It
recovers / beats the privileged-yaw teacher WITHOUT privilege (the clean architecture demonstration).
ACT23_MODE = "shapes" runs the near-ceiling cube/L/U grasp checks (honest: too little signal to self-improve).

Env: ACT23_MODE ACT23_NPOS ACT23_NTRIAL ACT23_HOLD ACT23_TEST ACT23_LAM ACT23_K ACT23_NCAND ACT23_CURVE_STEPS
"""
from __future__ import annotations

import os
import sys
import json
import time as _time_mod

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import mujoco

# WER hat welchen Schalter gesetzt?  VOR den setdefault-Aufrufen festhalten, welche ACT*-Variablen
# aus der UMGEBUNG kamen -- sonst meldet _print_run_settings die von act23 selbst gesetzten Werte als
# "Abweichung" und der Nutzer sucht in seinem Startbefehl nach etwas, das dort nie stand (genau das
# ist am 2026-08-03 passiert: ACT_GOAL_ROPE und ACT_REACH_* wurden faelschlich ihm zugeschrieben).
_ENV_AT_IMPORT = {k for k in os.environ if k.startswith("ACT")}

os.environ.setdefault("ACT14_DOF", "4")   # act23 runs the 4-DOF arm: joint_3 freed (user request) --
#   it was LOCKED at HOME=3.14 everywhere and is THE reason for the small workspace; the learned
#   kinematics babbles all 4 positioning joints and the reach keeps the CLAW DIRECTION (redundancy).
#   ACT14_DOF=3 restores the classic arm.  Must be set BEFORE pc_act14 is imported (ARM3 is built then).
# WORKSPACE enlarged toward the 4-DOF reach (user request), bounded by the MEASURED GRASP ENVELOPE:
# the panned physical-rig camera localises 0-5mm over the whole table and straight-ahead grasps work
# to r=0.32, BUT the teacher choreography fails at combined |x|>~0.09 with y>~0.15 (probes: (+-0.115,
# 0.16) 0/4, (+-0.095,0.20) 0/3 -- ALSO at 3 DOF, a PRE-EXISTING envelope hole the old probes never
# sampled; 4 DOF adds claw TILT there, 30-42deg vs 14-19).  So: y extended 0.21->0.24 (centre column +
# narrow top verified), x kept at ~old size.  The envelope hole is an open work item (fits stage 2:
# a learned policy could learn its own envelope).
for _k, _v in (("ACT_REACH_X0", "-0.12"), ("ACT_REACH_X1", "0.12"),
               ("ACT_REACH_Y0", "0.07"), ("ACT_REACH_Y1", "0.24")):
    os.environ.setdefault(_k, _v)
# SELBST LOSLASSEN IN DER STEUER-GUI (Nutzerentscheid 2026-10-06, wiki/befunde/loslassen.md):
#   Teacher-Korrektur + Loslass-Kopf + Lernen aus dem eigenen Ergebnis + Halte-Fenster.  Gemessen
#   nach der Lernphase 102/200 gegen 102/200, eigenes Loslassen gelingt 81 statt 72 %.  NUR in der
#   GUI (dort persistiert der Zustand, die Lernphase faellt einmal an); kopflose Messlaeufe behalten
#   die alten Vorgaben, damit fruehere A/Bs vergleichbar bleiben.
if os.environ.get("ACT23_VIZ", "0") == "1" and os.environ.get("ACT23_VIZ_HEADLESS", "0") != "1":
    for _k, _v in (("ACT16_ABLAGE_FIX", "1"), ("ACT23_LOSLASS_KOPF", "1"),
                   ("ACT23_LOSLASS_SELBST", "1"), ("ACT16_ENDE_HALTEN", "30")):
        os.environ.setdefault(_k, _v)
os.environ.setdefault("ACT16_ENDE_SELBST", "1")   # DAS EPISODENENDE ENTSCHEIDET DER AGENT (seit 2026-10-05):
#   getragen + Hand ueber dem EIGENEN Ziel auf Ablagehoehe statt Orakel aus der wahren Objektlage.
#   Gemessen (wiki/befunde/episodenende-selbst.md, 8 Seeds x 50): Orakel 53,1 %, selbst 60,7 %,
#   Seeds 7:1, Intervall [+0,7, +14,4].  Nur in act23 gesetzt -- andere act16-Nutzer bleiben beim
#   Orakel.  ACT16_ENDE_SELBST=0 stellt es her.
os.environ.setdefault("ACT_GOAL_ROPE", "1")   # STAGE 4a: RoPE goal-latent (near-linear in position ->
#   the learned latent-inverse is near-exact; measured in act21: servo isolated ~0mm vs 4.4mm blob)
from pc_cvnn.pc_act14 import BracketArmSim, HOME, ARM3, ArmBodyModel3D
from pc_cvnn.arm_modules import shape_classifier as _SC
from pc_cvnn.pc_act18 import (F as HEX_F, warp_gaze_delta, fovea_gradient,
                              ZOOM as FOVEA_ZOOM, ZOOM_MIN, ZOOM_MAX)
from pc_cvnn.test_pc_act10 import com2d
from pc_cvnn.arm_modules.body_model import BodyModelModule
from pc_cvnn.arm_modules.shape_classifier import ShapeClassifierModule
from pc_cvnn.arm_modules.object_orientation import ObjectOrientationModule
from pc_cvnn.arm_modules.world_model import (WorldModelModule, feats_from, action_vec, wrist_of,
                                             quality as wm_quality, tilt_of as wm_tilt_of,
                                             TILT_ACTION, TILT_CURIOSITY)
from pc_cvnn.arm_modules.runtime_policy import RuntimePolicyModule
from pc_cvnn.arm_modules import colour_openset
from pc_cvnn.arm_modules.colour_openset import ColourOpenSetModule
from pc_cvnn.arm_modules.planner import GoalModule2D, LO as GOAL_LO, HI as GOAL_HI
from pc_cvnn.arm_modules.latent_goal import LatentGoalServo, LatentGoalLanguage
from pc_cvnn.arm_modules.latent_dynamics import LatentDynamicsModule
from pc_cvnn.arm_modules.latent_attractor import LatentAttractorController
from pc_cvnn.arm_modules.curiosity import DistanceNovelty
from pc_cvnn.arm_modules.self_eval import SelfEvalModule
from pc_cvnn.arm_modules.object_memory import ObjectMemoryModule
from pc_cvnn.arm_modules.d0_integrity import (
    append_credit as _d0_append_credit,
    changed_components as _d0_changed_components,
    snapshot as _d0_snapshot,
    write_manifest as _d0_write_manifest,
)
import pc_cvnn.pc_act16 as act16

CAM = "overview"
# FOVEA-DRIVEN SERVO (this branch's goal): the approach corrections come from the NET's own gaze
# belief instead of the algorithmic detector (perceive_all stays as fallback + identity re-anchor
# only) -- the first load-bearing de-crutching of the detector.  Modes: "1" = while the fovea's
# IDENTITY lock holds its belief IS the servo obs, "shadow" = compute + log |net - detector| but let
# the detector keep driving (measurement mode), "0" = main behaviour (gaze = attention only).
# Requires the learned gaze, so any mode != "0" forces FOVEA_NET on.
FOVEA_SERVO = os.environ.get("ACT23_FOVEA_SERVO", "1")
# LEARNED FOVEA GAZE (opt-in): the net's own active-inference centering drives the gaze of the form/
# class tracker, the detector only re-anchors identity every FOVEA_ANCHOR frames.  Without FOVEA_SERVO
# the gaze is attention only (grasp target comes from the detector regardless), so this cannot regress
# delivery; it makes "where to look" a net decision (the user's goal).  ACT23_FOVEA_NET=1 enables.
FOVEA_NET = os.environ.get("ACT23_FOVEA_NET", "0") == "1" or FOVEA_SERVO != "0"
FOVEA_ANCHOR = int(os.environ.get("ACT23_FOVEA_ANCHOR", "6"))
# PREDICTIVE OBJECT MEMORY: replaces the detector re-anchor with a proprioceptive belief so the
# net-driven gaze follows the object through grasp OCCLUSION + CARRY with NO detector.  Default ON
# when the learned gaze is active (itself opt-in).  ACT23_FOVEA_MEM=0 falls back to the detector anchor.
FOVEA_MEM = FOVEA_NET and os.environ.get("ACT23_FOVEA_MEM", "1") == "1"
BODY = {"cube": "obj_red", "L": "obj_L", "U": "obj_U"}
ALL = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U"]
TARGET = np.array([0.0, 0.10])
# ALLE DREI ZUSATZBLOECKE STEHEN SEIT 2026-08-06 AUF AUS.  Gemessen am 686-Ep-Lauf (623 Zeilen mit
# gueltigen Bloecken, 5-fach kreuzvalidiert): die Bloecke WEGZULASSEN sagt besser vorher als sie zu
# fuehren -- MSE 0.1110 ohne gegen 0.1147 mit (p=0.034).  Nicht wegen Redundanz (nur d_hand war aus
# den alten Merkmalen ableitbar, R^2=0.74; die uebrigen tragen echte neue Information, R^2 0.09-0.26)
# und nicht wegen der Dimensionszahl (die Kompression der 10 |top|-Dim auf ihre Mittelamplitude aendert
# NICHTS: 0.1149 gegen 0.1147, p=0.89).  Es ist eine STICHPROBENFRAGE: die Effekte sind echt, aber mit
# rho~0.15 (R^2~2%) zu klein, als dass sich das Schaetzen ihrer Gewichte bei 623 Zeilen und 56
# augmentierten Spalten lohnt.  Schema und Code BLEIBEN, damit die 623 gesammelten Zeilen nicht
# verloren sind und das Experiment bei deutlich groesserem Puffer fortsetzbar ist -- die Abschaltung
# schreibt nur konstant neutrale Werte, sie entfernt keine Spalten.
# NACHBAR-INFORMATION als Situations-Feature (s. _neighbour_feats).  ACT23_NEIGHBOURS=0 schaltet sie
# ab -- die Dimensionen BLEIBEN dann im Schema (sonst passte der Puffer nicht mehr), sie tragen nur
# konstant den neutralen Wert.  NB_DMAX = ab welchem Abstand ein Objekt nicht mehr als Nachbar zaehlt;
# 0.12m deckt Schieben beim Schliessen, Rammen beim Tragen und das Blob-Verschmelzen (~40mm) ab.
# FOVEA-ZUSTAND als Situations-Feature (s. _fovea_feats).  Der Nutzer hat in der ModulViz-Grafik
# bemerkt, dass es KEINE Kante VisualCortex -> WorldModel gibt -- zu Recht: die Situation kam bisher
# vollstaendig aus dem UEBERSICHTS-Pfad (perceive_all), das gelernte Fovea-Netz beeinflusste nur, wohin
# der Arm waehrend des Anfahrens zielt.  Folge: eine bessere Fovea konnte die GRIFFWAHL gar nicht
# erreichen (siehe den zurueckgenommenen Aufloesungsversuch), und schwankende Servo-Qualitaet erschien
# dem Welt-Modell als unerklaerliches Rauschen bei identischen Merkmalen.
# FOV_SETTLE: so viele Fovea-Schritte auf dem AKTUELLEN Bild, bevor der Zustand gelesen wird.  Gesucht
# werden muss dabei NICHT -- perceive_all hat das Objekt schon lokalisiert, die Fovea wird nur
# dorthin gerichtet und schwingt ein.  learn=False: das ist ein LESEN, keine Erfahrung.
# ARMSTELLUNG als Situations-Feature (s. _body_feats).  Die letzte gestrichelte Kante der
# ModulViz-Grafik: das Koerpermodell kennt die Armstellung, das Welt-Modell erfuhr sie nie.
# WARUM DAS ZAEHLT: run_combined laeuft mit arm_reset=False, der Arm startet also NICHT bit-identisch,
# sondern dort, wo drive_home ihn gelassen hat (~0.05 rad je Gelenk daneben).  Der Nutzer hat genau
# daraus ein Problem beobachtet: "Der Greifer richtet sich manchmal beim Start einer Episode schon in
# Ruheposition aus, oft in eine extreme 90-Grad-Position ... dann kollidiert er beim Anfahren mit
# einem Finger mit der Base."  Fuer das Welt-Modell sahen solche Episoden bisher aus wie jede andere.
BODY_FEATS = os.environ.get("ACT23_BODY_FEATS", "0") == "1"
BD_DMAX = float(os.environ.get("ACT23_BD_DMAX", "0.4"))   # Deckel fuer den Hand-Ziel-Abstand (m)
BD_DIM = 7                                             # [gueltig, FK-Surprise, cos2w0, sin2w0, d, cos, sin]
BD_NEUTRAL = np.zeros(BD_DIM)
FOVEA_FEATS = os.environ.get("ACT23_FOVEA_FEATS", "0") == "1"
FOV_SETTLE = int(os.environ.get("ACT23_FOV_SETTLE", "4"))
FOV_DIM = 12                                           # [gueltig, Surprise, |top|(10)]
FOV_NEUTRAL = np.zeros(FOV_DIM)                        # "nie gemessen" -- gueltig-Flag 0
NEIGHBOURS = os.environ.get("ACT23_NEIGHBOURS", "0") == "1"
NB_DMAX = float(os.environ.get("ACT23_NB_DMAX", "0.12"))
NB_DIM = 5
NB_NEUTRAL = np.array([0.0, NB_DMAX, 1.0, 0.0, 0.0])   # "nie gemessen" -- gueltig-Flag 0

# WELT-FIT JE EPISODE (ACT23_WORLD_FULL_EVERY).  `world.train(600)` laeuft nach JEDER Episode
# ueber den vollen Puffer (~11000 Zeilen), um EINE neue Zeile einzuarbeiten -- rund die Haelfte
# der Episodendauer (gemessen 57 s von 77 s Lernphase).  Am Pruefstand (Kopie des 11273-Zeilen-
# Zustands) gemessen:
#   * `Policy.fit` setzt die Gewichte NIE zurueck -- der Fit ist bereits ein Warmstart.
#   * Die MSE steht nach EINER Epoche (0.0854 -> 0.0844); die restlichen 599 wandern um +-0.001.
#   * mu und sigma weichen bei 5..200 Epochen WENIGER vom 600er-Fit ab als zwei 600er-Fits mit
#     verschiedenen Seeds voneinander -- und sigma steuert Aktionswahl (mu - lam*sigma) und
#     Neugier, dort haette ein Schaden zuerst auftreten muessen.
#   * Was die 600 Epochen ALS EINZIGES kaufen, ist AUFNAHMEKRAFT fuer WIDERSPRECHENDE Erfahrung:
#     rund dreifach (0.576 -> 0.531 gegen -> 0.556 bei 50 Epochen ueber 8 Episoden).
# Deshalb ein PLAN statt einer festen Zahl: jede n-te Episode voll, dazwischen kurz.
# VORGABE n=4 SEIT DEM A/B (2026-09-07, Nutzerentscheid).  Je 200 Episoden im vollen kopflosen
# Steuerungslauf, beide Arme gleichzeitig aus demselben Zustand:
#     Lieferquote      105/200 = 52,5 % (n=1) gegen 103/200 = 51,5 % (n=4), Fisher p = 0,92
#     Selbst-Aneignung ununterscheidbar; BEIDE Arme gebaeren in 200 Episoden keine neue Klasse
#     Laufzeit         4,74 h gegen 2,95 h -- 61 % mehr Episoden je Stunde bei 155 gegen 157 Fits
# Damit ist die Pruefstandsvorhersage ausnahmsweise auf act23-Ebene bestaetigt.  Aufloesung
# ehrlich: n=200 je Arm schliesst Unterschiede ueber ~10 Punkte aus, kleinere bleiben offen.
# EINZIGER Wert, der gegen den Plan lehnt: "Griff hielt nicht" 11,0 gegen 17,0 % (p = 0,11) --
# nicht signifikant, aber das, was ein zweiter Lauf zuerst nachpruefen sollte.
# ZURUECK auf das alte Verhalten: ACT23_WORLD_FULL_EVERY=1.  Dann kehrt welt_fit_epochen() sofort
# zurueck, der kurze Zweig wird nie betreten und WORLD_EPOCHS_SHORT nie gelesen -- zifferngenau
# der Stand vor fec6c98.  Zahlen und Vorbehalte: wiki/befunde/welt-fit-plan-ab.md.
# KEIM-DIAGNOSE (ACT23_KEIMDIAG=1, Vorgabe AUS).  Frage aus
# wiki/befunde/ablenker-bindung-gemessen.md: entsteht die Ablenker-Bindung beim AUFSETZEN des
# Trackers?  Meldet einmal je Episode, ob der Tracker seinen Keim bekommen hat oder blind mit
# dem wahrscheinlichsten gleichklassigen Blob gestartet ist -- und auf welchem Koerper er dabei
# landet.  Die wahren Lagen dienen AUSSCHLIESSLICH der Zaehlung, wie bei ACT16_ABLENKDIAG.
KEIMDIAG = os.environ.get("ACT23_KEIMDIAG", "0") == "1"
# KEIM-REPARATUR.  VORGABE 1 SEIT DEM A/B (2026-09-09, Nutzerentscheid).  Der Eigenschafts-Pfad
# veroeffentlicht die Erst-Wahrnehmung unter `eig:{body}` (pc_act23.py:2986), der Tracker fragt
# sie unter der FORMKLASSE ab (:3129) -- die beiden treffen sich nie, gemessen 120 von 120
# Episoden ohne Keim.  Ohne Keim startet make_shape_track blind auf dem wahrscheinlichsten
# gleichklassigen Blob; bei mehreren Kandidaten (14,2 % der Episoden) sind das 41,2 % Fehlstarts,
# und KEIN Fehlstart wurde je geliefert (0/8 gegen 67/112, Fisher p = 0,0011).
# Belege: wiki/befunde/keim-erreicht-tracker-nicht.md.
# WARUM NICHT einfach unter der Formklasse veroeffentlichen: `"cube"` waere mehrdeutig, sobald
# zwei Koerper dieselbe Formklasse tragen -- und genau das ist der Fall, der schiefgeht.  Nur
# `eig:{body}` benennt den gemeinten Koerper.
# GEMESSEN als gepaarter Seed-Sweep, 4 Laeufe je 120 Episoden aus einem Schnappschuss
# (wiki/befunde/keim-fix-ab.md).  Direkte Zielgroesse -- Fehlstart unter MEHRDEUTIGEN Szenen:
#     Seed  7   aus  7/17 = 41,2 %   an 1/14 =  7,1 %   p = 0,0454
#     Seed 23   aus 10/16 = 62,5 %   an 1/16 =  6,2 %   p = 0,0021
#     gepoolt   aus 17/33 = 51,5 %   an 2/30 =  6,7 %   p = 0,00010
# Keim greift 0 % -> 95/97 %; an keiner Nebengroesse ist Schaden messbar.  Die LIEFERQUOTE ist
# dagegen NICHT belegt (gepoolt 50,4 -> 52,9 %, p = 0,65) -- wer hier einen Quotengewinn zitiert,
# zitiert falsch.
# ZURUECK auf das alte Verhalten: ACT23_KEIM_FIX=0.  Dann faellt _kkey auf `key` zurueck und der
# Keim wird wieder unter der Formklasse gesucht -- zifferngenau der Stand vor d85250b.
KEIM_FIX = os.environ.get("ACT23_KEIM_FIX", "1") == "1"
_WIE_KEY = object()          # Vorgabe-Markierung fuer make_shape_track(seed_key=...): "nimm key"
# KEIM AUCH IM PRIVILEGIERTEN RUECKFALL (ACT23_KEIM_RUECKFALL).  VORGABE 0 -- GEBAUT, GEMESSEN,
# WIEDER ABGESCHALTET (2026-09-09, Nutzerentscheid).  Trifft die Eigenschafts-Adressierung nichts,
# gibt perceive() die WAHRE Lage als Greifziel zurueck und veroeffentlicht KEINEN Keim; der
# Tracker startet dort blind (3-5 % der Episoden, im Protokoll als `__unset__`).
# MIT dem Schalter schliesst sich diese Luecke vollstaendig -- Episoden ohne Keim 10 -> 0 -- aber
# GEMESSEN bringt es nichts: Fehlstart 2,9 -> 4,2 % (p = 0,47), Lieferquote 52,9 -> 53,6 %
# (p = 0,93), je ~120 Episoden ueber zwei Seeds.  Der Grund ist der Ertrag der Messung: die
# Rueckfall-Episoden sind VERSCHMELZUNGSFAELLE (gewaehlter Blob 21 gegen 23 mm bzw. 19 gegen
# 23 mm, also fast genau zwischen zwei Koerpern).  Gegen einen verschmolzenen Blob hilft kein
# Ortsanker -- der Keim zeigt richtig, die Wahrnehmung hat nichts Richtiges anzubieten.
# WARUM AUS: der Keim kaeme aus sim.obj_pos(), also aus dem PRIVILEG.  Das Greifziel ist es in
# diesem Zweig ohnehin, aber das Privileg zusaetzlich in den BLICK-Regelkreis zu lassen widerspricht
# dem Projektziel (wiki/ziel.md) -- und bezahlt hat es sich nicht.  Der Schalter bleibt stehen,
# weil die Messung reproduzierbar bleiben soll; eingeschaltet markiert perception.seed_priv den
# Keim, und die [Keim]-Zeile druckt "Keim JA (PRIVILEGIERT)".
# Der lohnendere Weg fuehrt ueber die Ursache: waeren die Blobs getrennt, fiele der Rueckfall gar
# nicht erst an.  Belege: wiki/befunde/keim-im-rueckfall.md.
KEIM_RUECKFALL = os.environ.get("ACT23_KEIM_RUECKFALL", "0") == "1"
# KONTINUITAET STATT NEUKLASSIFIKATION.  VORGABE 1 SEIT DEM A/B (2026-09-10, Nutzerentscheid).
# Der Form-Tracker verlangt in JEDEM Bild erneut `d["shape"] == key`.  Bei verschmolzenem Blob
# faellt die Formklasse aber aus -- gemessen behaelt der Farb-Split nur 31-58 % der Pixel, und
# der Deskriptor dieser halben Silhouette landet bei 0,94-1,55 x novel_th, also knapp jenseits.
# resolve() antwortet dann in 55 von 58 Faellen mit "neuartig" (Enthaltung, keine Verwechslung),
# der Tracker findet null Kandidaten und der Servo ist fuer dieses Bild blind.
# Belege: wiki/befunde/formsplit-warum.md, wiki/befunde/verschmelzung-abstandskurve.md.
# DIE IDEE: die IDENTITAET steht laengst fest -- sie kommt aus der Adressierung und seit d85250b
# aus dem Keim.  Je Bild wird nur die POSITION gebraucht, und die rettet der Farb-Split ab 35 mm
# vollstaendig.  Faellt die Klasse aus, folgt der Tracker deshalb dem naechstgelegenen Farb-Teil
# -- OHNE Formforderung -- und die bestehende 5-cm-Sprungschranke bleibt die Sicherung.
# ZWEI WACHEN, ohne die es die Ablenker-Bindung zurueckholen wuerde:
#   * nur wenn schon ein Glaube besteht (mem["xy"] is not None).  Beim ERSTEN Blick wird nicht
#     geraten -- dort entscheidet der Keim, sonst waere es genau der Muenzwurf aus
#     wiki/befunde/keim-erreicht-tracker-nicht.md.
#   * die Zuversicht kommt aus der FARBE (wie im ckey-Zweig), nicht aus einer erfundenen
#     Klassenwahrscheinlichkeit: wir wissen wo, nicht was.  Faellt sie unter act16.SERVO_CONF,
#     ignoriert der Servo die Beobachtung von selbst.
# GEMESSEN, gepaarter Seed-Sweep, 4 Laeufe je 120 Episoden (wiki/befunde/
# kontinuitaet-statt-neuklassifikation.md):
#     Gegenprobe fremder Belief   8,8 -> 9,2 %   Fisher p = 1,0000  (beide Seeds)
#     Detektor-Obs je Anfahrschritt (Median)  0,312 -> 0,325 bzw. 0,319 -> 0,322
#     Kontinuitaets-Anteil 1,3 bzw. 2,2 % der Anfahrschritte, in 22-28 % der Episoden
#     Lieferquote gepoolt 52,9 -> 57,1 %, p = 0,41 -- die Seeds WIDERSPRECHEN einander
# EHRLICH ZUR GROESSE: kein Lauf war je GANZ blind (0/120 in allen vier Armen), und der Servo
# hatte auch vorher in 31-32 % der Anfahrschritte eine Beobachtung.  Das hier fuellt 1-2 %.
# Ein QUOTENGEWINN ist NICHT belegt -- wer die Umstellung so zitiert, zitiert falsch.
# Wofuer sie steht: Identitaet einmal feststellen und dann verfolgen, statt sie in jedem Bild
# neu zu erkennen.  ZURUECK: ACT23_TRACK_KONTINUITAET=0.
KONTINUITAET = os.environ.get("ACT23_TRACK_KONTINUITAET", "1") == "1"
# FARBE UND FORM ENTKOPPELN.  VORGABE 1 SEIT 2026-09-10 (Nutzerentscheid).  Nutzerbeobachtung
# 2026-09-10, nachgezaehlt und bestaetigt: der Wuerfel gibt es in DREI Farben, jede andere Form in
# GENAU EINER, und in 5 von 6 Farbklassen bestimmt die Farbe die Form eindeutig.  Ein Netz, das
# "orange -> L" lernt, liegt in dieser Welt zu 100 % richtig -- das trifft wiki/ziel.md (neue
# Farben, Formen UND KOMBINATIONEN selbst lernen) an der Wurzel.
# WAS DER RUECKHALTE-TEST DAZU SAGT (wiki/befunde/farbe-form-rueckhalt.md): die WAHRNEHMUNG kuerzt
# nicht ab -- umgefaerbt haelt die Formklasse bei allen trainierten Formen zu 100 %, der
# Deskriptor rechnet auf der Belegungsmaske.  Die Entkopplung bricht also nichts; sie DECKT AUF,
# was der Farbpfad heute traegt (obj_X haelt seine Klasse schon solo nur in 4 von 8 Lagen).
# WIE: die sieben VORHANDENEN Koerperfarben werden je Episode unter den Koerpern PERMUTIERT.
# Bewusst keine neuen Farben -- eine neue Farbe gebiert eine neue Farbklasse, und das waere ein
# anderes Experiment.  So bleibt die Palette genau so wahrnehmbar wie heute, nur die Zuordnung
# Farbe<->Form faellt weg.  INNERHALB einer Episode bleibt die Farbe fest (Nutzervorgabe), damit
# Keim, Tracker und Split weiterarbeiten.
# GEMESSEN, gepaarter Seed-Sweep, 4 Laeufe je ~112 Episoden
# (wiki/befunde/farb-mischung.md).  DIE EIGENTLICHE FRAGE WAR "haelt die Maschinerie", und sie
# haelt: Adressierung Median 1,0-1,4 mm in allen vier Armen, Eindeutigkeit unveraendert,
# privilegierter Rueckfall 4-5 -> 6 %.
# DIE LIEFERQUOTE FAELLT (gepoolt 57,5 -> 47,6 %, p = 0,039) UND DAS IST KEIN DEFEKT: das hier
# ist ein WELT-Wechsel, kein Eingriff -- die gemischte Welt ist schwerer, weil der Farbpfad die
# Identitaet nicht mehr mittraegt.  Dazu widersprechen die Seeds einander (-1,3 gegen -18,3
# Punkte), und der Vergleichsarm lag mit 63,8 % weit ueber dem sonst ueblichen ~52 %.
# WER DIESE VORGABE RUECKGAENGIG MACHT, WEIL "DIE QUOTE GEFALLEN IST", MISST DAS SZENARIO, NICHT
# EINEN FEHLER.  Nach wiki/ziel.md ist die Quote hier ohnehin nicht das Kriterium: erst in einer
# Welt, in der Farbe und Form unabhaengig sind, ist Generalisierung ueberhaupt messbar.
# ZURUECK auf die gekoppelte Welt: ACT23_FARB_MISCHUNG=0.
FARB_MISCHUNG = os.environ.get("ACT23_FARB_MISCHUNG", "1") == "1"
# KOMMANDIERT IST KOMMANDIERT (ACT23_EIG_SCHUETZT, Vorgabe 0 bis gemessen).  Der Schutz vorm
# Verhungern liest `protect=set(state.SHAPE_KEY.values())` -- also NUR Klassen mit einem KNOPF.
# Eine Klasse, die ueber das EIGENSCHAFTS-Kommando adressiert wird, ist ungeschuetzt und stirbt
# nach STARVE_N Blicken, egal wie oft sie kommandiert wurde.  Gemessen im Langlauf vom 10.09.:
# 'neu-373' wurde FUENFMAL adressiert ([Auto 409] neu-373 + mittel, [Auto 511] farbe-4 +
# neu-373, ...) und verhungerte trotzdem; sechs der dreizehn geborenen Klassen erreichten
# 50-75 % Wiedererkennung und starben ebenfalls.
# Das ist dieselbe Luecke wie beim Aneignungs-Zaehler, nur wirkt sie nicht auf die MESSUNG,
# sondern auf das VERHALTEN: die Aufraeum-Mechanik entfernt genau die Klassen, die der Agent
# gerade benutzt.  Belege: wiki/befunde/langlauf-entkoppelt.md.
# BEWUSST ENG: geschuetzt wird nur die FORMACHSE eines Tripels, das wirklich in state.EIGENSCHAFT
# steht -- nicht jede je gesehene Klasse.  Sonst waere der Schutz wertlos (nichts verhungerte mehr)
# und der Klassenbestand liefe in den MAX_OPEN-Deckel.
# GEMESSEN UND WIRKUNGSLOS (2026-09-11, wiki/befunde/eig-schuetzt-null.md): zwei Arme zu je 400
# Episoden, Schalter 0 gegen 1, sind BITGLEICH -- keine einzige Entscheidung aendert sich.
# URSACHE, ein Konstruktionsfehler dieses Entwurfs: state.EIGENSCHAFT ist ein Verzeichnis
# Koerper -> Tripel, und add_eigenschaft ueberschreibt den Eintrag, sobald derselbe Koerper neu
# gewuerfelt wird (bei sieben Koerpern alle ~7 Episoden).  Der Schutz liest damit einen
# SCHNAPPSCHUSS, keine Historie -- und er haelt genau so lange, wie das Tripel aktuell ist, also
# waehrend die Klasse ohnehin zu jung zum Sterben ist (STARVE_N = 25).
#     Ep 54  [Auto 54] farbe-3 + neu-384   -> geschuetzt
#     Ep ~61 Koerper neu gewuerfelt        -> Tripel ueberschrieben, Schutz weg
#     Ep ~66 verhungert nach 26 Ep
# WER EINEN ZWEITEN ANLAUF NIMMT, braucht ein GEDAECHTNIS statt eines Schnappschusses --
# acq[c]["cmd"] fuehrt das bereits.  Aber erst pruefen, ob der Aufraeumer ueberhaupt das Problem
# ist: gemessen werden die sterbenden Klassen schlicht NICHT BENUTZT (5 Kommandos auf 5 junge
# Klassen gegen 107 auf die vier etablierten), und laenger leben macht sie nicht nuetzlicher.
EIG_SCHUETZT = os.environ.get("ACT23_EIG_SCHUETZT", "0") == "1"
WORLD_EPOCHS = max(1, int(os.environ.get("ACT23_WORLD_EPOCHS", "600")))
WORLD_EPOCHS_SHORT = max(1, int(os.environ.get("ACT23_WORLD_EPOCHS_SHORT", "20")))
WORLD_FULL_EVERY = max(1, int(os.environ.get("ACT23_WORLD_FULL_EVERY", "4")))
_world_fits = [0]                  # gezaehlte Welt-Fits je Episode; [0] = Liste, damit die
                                   # verschachtelte run_one() sie ohne `global` fortschreiben kann


def welt_fit_epochen():
    """Epochen fuer den Fit NACH DIESER Episode -- jede n-te voll, dazwischen kurz.

    Zaehlt selbst mit, damit der Plan unabhaengig davon greift, aus welcher der beiden
    Auto-Schleifen (kopflos / GUI) gefahren wird -- der Riss, an dem hier schon zweimal ein
    Schalter nur in einer Haelfte gewirkt hat (s. wiki/mechanismen/invarianten.md)."""
    if WORLD_FULL_EVERY <= 1:
        return WORLD_EPOCHS                       # Vorgabe: unveraendert, ohne Nebenwirkung
    voll = (_world_fits[0] % WORLD_FULL_EVERY) == 0
    _world_fits[0] += 1
    return WORLD_EPOCHS if voll else WORLD_EPOCHS_SHORT


# AUSFUEHRUNGS-VARIANZ (ACT23_EXV=M): dieselbe Szene M-mal fahren, um zu trennen, wieviel des
# Ausgangs an der WAHL haengt und wieviel an der AUSFUEHRUNG.  Damit die M Wiederholungen wirklich
# dieselbe Entscheidung treffen, friert die Messung das Lernen ein -- sonst haette Wiederholung 2
# ein Welt-Modell gesehen, das aus Wiederholung 1 gelernt hat, und die Aktion koennte kippen.
# Nebeneffekt (erwuenscht): eine Messung verschmutzt den ueber Wochen gewachsenen Zustand nicht.
EXV_N = max(1, int(os.environ.get("ACT23_EXV", "1")))
EXV_FREEZE = EXV_N > 1 and os.environ.get("ACT23_EXV_FREEZE", "1") == "1"
D0_FREEZE = os.environ.get("ACT23_D0_FREEZE", "0") == "1"
# D0 writes structured credit lines only when an explicit disposable artifact path is supplied.
# The normal human-readable log and all default behaviour remain unchanged.
D0_CREDIT_JSONL = os.environ.get("ACT23_D0_CREDIT_JSONL", "")
# One immutable record per executed D0 episode.  Unlike credit.jsonl this also retains the
# action for an intentional abstention, so evaluation can measure the selected wrist rather
# than only the subset that the world model was allowed to learn from.
D0_EPISODE_JSONL = os.environ.get("ACT23_D0_EPISODE_JSONL", "")
D0_MANIFEST_DIR = os.environ.get("ACT23_D0_MANIFEST_DIR", "")
# D0b stores only the agent-visible Fovea/hand time series.  It never reads simulator pose,
# contact or weld state; those remain an external evaluation channel.
D0B_TRACE_JSONL = os.environ.get("ACT23_D0B_TRACE_JSONL", "")
D0B_LIFT_PROBE = os.environ.get("ACT23_D0B_LIFT_PROBE", "0") == "1"
# Separate ground-truth channel for evaluating a prospective D0b self-label.  It must never be
# read by the trace consumer or a learner; keeping a distinct file makes that boundary auditable.
D0B_EVAL_JSONL = os.environ.get("ACT23_D0B_EVAL_JSONL", "")
# MuJoCo selbst ist deterministisch: bleibt das Objekt liegen und der Arm kehrt in dieselbe
# Ruhelage zurueck, wiederholt sich eine Episode BIS AUF DEN MILLIMETER (im Rauchtest gemessen:
# 63+-0 mm ueber drei Laeufe).  Der einzige natuerliche Streukanal ist die ARMSTELLUNG beim Start
# -- run_combined faehrt mit arm_reset=False, der Arm beginnt dort, wo drive_home ihn liess.
# ACT23_EXV_JITTER=<rad> stoert die Gelenke vor jeder Wiederholung gezielt um diesen Betrag und
# macht aus "wiederholt es sich?" eine DOSIS-WIRKUNGS-Kurve: wie empfindlich ist der Ausgang
# gegen die Startpose?  0 (Vorgabe) misst nur die natuerlich auftretende Streuung.
EXV_JITTER = float(os.environ.get("ACT23_EXV_JITTER", "0.0"))
# Neugier auf DIREKT GEMESSENER Abdeckung statt auf der Ensemble-Uneinigkeit (s. curious_pick).
NOVELTY_DIRECT = os.environ.get("ACT23_NOVELTY_DIRECT", "1") == "1"


def _auc(y, s):
    y = np.asarray(y).ravel(); s = np.asarray(s).ravel()
    pos = s[y > 0.5]; neg = s[y <= 0.5]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    return float((pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean())


class Env:
    def __init__(self):
        self.sim = BracketArmSim(render_wh=(240, 240)); self.sim.set_reach_site("contact")
        self.bm = BodyModelModule(rng=np.random.default_rng(5)); self.bm.babble(self.sim, 4000)
        self.clf = ShapeClassifierModule(cam=CAM, rng=np.random.default_rng(0))
        self.clf.calibrate(self.sim); self.clf.train(self.sim, steps=3000, rng=np.random.default_rng(1))
        act16.run_combined._quiet = True
        self._rid = mujoco.mj_name2id(self.sim.m, mujoco.mjtObj.mjOBJ_BODY, "obj_red")

    def setup(self, shape, p, yaw):
        self.sim.reset_home()
        for o in ALL:
            self.sim.set_object(o, [0.5, -0.6], z=0.012)
        self.sim.m.geom_size[self.sim.m.body_geomadr[self._rid]] = np.array([0.012] * 3)
        self.sim.set_object(BODY[shape], p, z=0.012, yaw=yaw)
        mujoco.mj_forward(self.sim.m, self.sim.d); self.sim.step(60)

    def select(self, shape):
        return self.clf.select(self.sim, shape)

    def grasp(self, shape, grasp_xy, wrist):
        gc = 0.3 if shape == "U" else None
        wf = None if wrist is None else (lambda s, _w=wrist: _w)
        d, m = act16.run_combined(self.sim, self.bm.body, None, CAM, episodes=1, cmd_fixed=BODY[shape],
                                  force="grasp", perceive_fn=lambda c, g=grasp_xy: (g, None, "grasp"),
                                  policy_fn=None, servo=False, goal_fn=lambda c, o: TARGET, rescatter=False,
                                  grip_close=gc, carry_gentle=(shape == "U"), wrist_fn=wf)
        return int(d)


def rand_pos(rng):
    return np.array([rng.uniform(-0.10, 0.10), rng.uniform(0.09, 0.22)])   # inside the enlarged workspace


def collect(env, world, shapes, npos, ntrial, rng, into_world=True):
    """Self-supervised: try random (offset, wrist) grasps, observe delivery. Returns (X,Y) tuples."""
    Xh, Yh = [], []
    for shape in shapes:
        for _ in range(npos):
            p = rand_pos(rng); yaw = rng.uniform(0, 2 * np.pi)
            env.setup(shape, p, yaw); sel = env.select(shape)
            if sel is None:
                continue
            g0 = np.asarray(sel["grasp_xy"], float); fe = feats_from(sel, shape)
            for _ in range(ntrial):
                dx, dy = rng.uniform(-world.off_max, world.off_max, 2); w = rng.uniform(0, np.pi)
                env.setup(shape, p, yaw)
                d = env.grasp(shape, g0 + np.array([dx, dy]), w)
                a = action_vec(dx, dy, w)
                if into_world:
                    world.observe(fe, a, d)
                Xh.append(np.concatenate([fe, a])); Yh.append(d)
    return np.array(Xh), np.array(Yh)


def deliver_rate(env, world, shape, positions, mode, lam):
    """mode: 'default' (WRIST_ALIGN), 'lcb' (uncertainty-aware), 'argmax' (lam=0 naive)."""
    d = 0; n = 0
    for p, yaw in positions:
        env.setup(shape, p, yaw); sel = env.select(shape)
        if sel is None:
            continue
        g0 = np.asarray(sel["grasp_xy"], float); n += 1
        if mode == "default":
            env.setup(shape, p, yaw); d += env.grasp(shape, g0, None); continue
        fe = feats_from(sel, shape)
        a, _, _ = world.select_action(fe, n=int(os.environ.get("ACT23_NCAND", "40")),
                                      lam=(0.0 if mode == "argmax" else lam))
        env.setup(shape, p, yaw)
        d += env.grasp(shape, g0 + a[:2], wrist_of(a))
    return d, max(1, n)


def main():
    NPOS = int(os.environ.get("ACT23_NPOS", "10"))
    NTRIAL = int(os.environ.get("ACT23_NTRIAL", "6"))
    HOLD = int(os.environ.get("ACT23_HOLD", "5"))
    TEST = int(os.environ.get("ACT23_TEST", "12"))
    LAM = float(os.environ.get("ACT23_LAM", "1.0"))
    K = int(os.environ.get("ACT23_K", "5"))
    CURVE_STEPS = int(os.environ.get("ACT23_CURVE_STEPS", "3"))

    print("act23 — SELF-LEARNING grasper: self-supervised world model + uncertainty-aware acting")
    env = Env()
    world = WorldModelModule(k=K, rng=np.random.default_rng(2))
    rng = np.random.default_rng(7)

    # (1) self-supervised collection on cube + L (NOT U), train, AUC on held-out trials
    print(f"  collecting OWN trials on cube+L ({NPOS} pos x {NTRIAL} trials/shape) ...")
    collect(env, world, ["cube", "L"], NPOS, NTRIAL, rng, into_world=True)
    Xh, Yh = collect(env, world, ["cube", "L"], HOLD, NTRIAL, rng, into_world=False)
    world.train(epochs=600)
    auc = _auc(Yh, [world.predict(x[:7], x[7:][None])[0][0] for x in Xh]) if len(Xh) else float("nan")
    print(f"  [1] model trained on {world.n()} own trials; held-out P(deliver) AUC = {auc:.2f}  "
          f"(deliver rate {np.mean(Yh) if len(Yh) else float('nan'):.2f})", flush=True)

    # fixed test positions per shape (paired across methods)
    tpos = {s: [(rand_pos(rng), rng.uniform(0, 2 * np.pi)) for _ in range(TEST)] for s in ("cube", "L", "U")}

    # (2) SAFETY + (3) GENERALISATION (U is held-out): default vs LCB vs naive-argmax
    print("  [2/3] default(WRIST_ALIGN) vs LCB(uncertainty-aware) vs argmax(naive) "
          "[U = generalisation, never collected]:")
    for s in ("cube", "L", "U"):
        dd, n = deliver_rate(env, world, s, tpos[s], "default", LAM)
        dl, _ = deliver_rate(env, world, s, tpos[s], "lcb", LAM)
        da, _ = deliver_rate(env, world, s, tpos[s], "argmax", LAM)
        tag = "  <- held-out (generalisation)" if s == "U" else ""
        print(f"    {s}: default {dd}/{n}   LCB {dl}/{n}   naive-argmax {da}/{n}{tag}", flush=True)

    # (4) LEARNING CURVE: acquire the U from its OWN experience
    print(f"  [4] U learning curve (self-acquisition, {CURVE_STEPS} steps of own U trials):")
    d0, n0 = deliver_rate(env, world, "U", tpos["U"], "lcb", LAM)
    curve = [d0 / n0]
    print(f"    U after 0 own U-trials: LCB {d0}/{n0}", flush=True)
    for it in range(CURVE_STEPS):
        collect(env, world, ["U"], NPOS, NTRIAL, rng, into_world=True)
        world.train(epochs=600)
        du, nu = deliver_rate(env, world, "U", tpos["U"], "lcb", LAM)
        curve.append(du / nu)
        print(f"    U after {(it + 1) * NPOS * NTRIAL} own U-trials: LCB {du}/{nu}  (model {world.n()} trials)",
              flush=True)
    try:
        _plot(curve, NPOS * NTRIAL, os.path.join(os.path.dirname(__file__), "act23_learning.png"))
    except Exception as e:
        print(f"  [viz] could not save the learning curve: {e}")


def _plot(curve, per, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x = np.arange(len(curve)) * per
    fig, ax = plt.subplots(figsize=(7, 4)); fig.patch.set_facecolor("#0e0e12")
    ax.set_facecolor("#0e0e12"); ax.grid(True, color="#333", lw=0.4); ax.tick_params(colors="w")
    [s.set_color("#555") for s in ax.spines.values()]
    ax.plot(x, curve, "-o", color="#33ccff")
    ax.set_xlabel("own U trials collected", color="w"); ax.set_ylabel("U delivery (LCB)", color="w")
    ax.set_title("act23: self-acquisition of the held-out U from own experience", color="w", fontsize=10)
    fig.tight_layout(); fig.savefig(path, dpi=110, facecolor=fig.get_facecolor())
    print(f"  [viz] learning curve saved -> {path}")


def main_diag():
    """SIGNAL-RICH validation: a diagonally-oriented elongated object whose delivery depends on the wrist.
    The world model learns -- from its OWN outcomes -- which wrist delivers given the PERCEIVED long-axis
    orientation (no privileged sim yaw), and recovers/beats the privileged-yaw teacher without privilege."""
    NPOS = int(os.environ.get("ACT23_NPOS", "14"))
    NTRIAL = int(os.environ.get("ACT23_NTRIAL", "6"))
    TEST = int(os.environ.get("ACT23_TEST", "16"))
    LAM = float(os.environ.get("ACT23_LAM", "1.0"))
    K = int(os.environ.get("ACT23_K", "5"))
    CURVE_STEPS = int(os.environ.get("ACT23_CURVE_STEPS", "3"))
    CMD = "obj_red"; HALF = (0.028, 0.010, 0.012)

    print("act23 [diag] — SELF-LEARNING the grip wrist for a diagonal ELONGATED object (no privileged yaw)")
    sim = BracketArmSim(render_wh=(240, 240)); sim.set_reach_site("contact")
    bm = BodyModelModule(rng=np.random.default_rng(5)); bm.babble(sim, 4000)
    oo = ObjectOrientationModule()
    err = oo.train(sim, cmd=CMD, cam=CAM, steps=2500, half=HALF, rng=np.random.default_rng(0))
    print(f"  perceived long-axis train err: {err:.1f} deg  (self-supervised, camera -- NOT privileged)")
    act16.run_combined._quiet = True
    bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, CMD)

    def setup(p, yaw):
        sim.reset_home()
        for o in ("obj_green", "obj_blue", "obj_L", "obj_U"):
            sim.set_object(o, [0.5, -0.6], z=0.012)
        sim.set_target_marker([0.0, -0.6], z=-0.05)
        sim.m.geom_size[sim.m.body_geomadr[bid]] = np.asarray(HALF, float)
        sim.set_object(CMD, p, z=float(HALF[2]), yaw=yaw); mujoco.mj_forward(sim.m, sim.d); sim.step(40)
        sim.set_target_marker(TARGET, z=0.001)

    def feats():
        _, la = oo.perceive(sim, CMD, CAM); p = sim.obj_pos(CMD)[:2]   # PERCEIVED long axis (camera)
        return np.array([p[0], p[1], np.cos(2 * la), np.sin(2 * la), 1.0, 0.0, 0.0])

    def grasp(wrist):
        wf = None if wrist == "priv" else (lambda s, _w=wrist: _w)     # "priv" -> run_combined's privileged yaw
        d, _ = act16.run_combined(sim, bm.body, None, CAM, episodes=1, cmd_fixed=CMD, force="grasp",
                                  perceive_fn=lambda c: (sim.obj_pos(CMD)[:2], None, "grasp"),
                                  policy_fn=None, servo=False, goal_fn=lambda c, o: TARGET, rescatter=False,
                                  wrist_fn=wf)
        return int(d)

    world = WorldModelModule(k=K, off_max=0.0, rng=np.random.default_rng(2))   # off_max=0 -> pure wrist search
    rng = np.random.default_rng(7)

    def collect(npos, ntr):
        for _ in range(npos):
            p = rand_pos(rng); yaw = rng.uniform(0, np.pi)
            setup(p, yaw); fe = feats()
            for _ in range(ntr):
                w = rng.uniform(0, np.pi); setup(p, yaw)
                world.observe(fe, action_vec(0, 0, w), grasp(w))

    collect(NPOS, NTRIAL); world.train(epochs=600)
    # held-out AUC
    Xh, Yh = [], []
    for _ in range(8):
        p = rand_pos(rng); yaw = rng.uniform(0, np.pi); setup(p, yaw); fe = feats()
        for _ in range(4):
            w = rng.uniform(0, np.pi); setup(p, yaw); Yh.append(grasp(w)); Xh.append((fe, action_vec(0, 0, w)))
    auc = _auc(Yh, [world.predict(f, a[None])[0][0] for f, a in Xh])
    print(f"  [1] held-out P(deliver) AUC = {auc:.2f}  (deliver rate {np.mean(Yh):.2f})", flush=True)

    tpos = [(rand_pos(rng), rng.uniform(0, np.pi)) for _ in range(TEST)]

    def rate(mode):
        d = 0
        for p, yaw in tpos:
            setup(p, yaw)
            if mode == "fixed":
                w = 0.0
            elif mode == "priv":
                w = "priv"
            else:
                a, _, _ = world.select_action(feats(), n=0, lam=LAM); w = wrist_of(a)
            setup(p, yaw); d += grasp(w)
        return d

    print("  [2/3] self-learned wrist vs baselines (no privileged yaw for the agent):")
    print(f"    fixed wrist=0 (no privilege)    : {rate('fixed')}/{TEST}")
    print(f"    privileged obj_yaw (upper bound): {rate('priv')}/{TEST}")
    print(f"    SELF-LEARNED (LCB)              : {rate('self')}/{TEST}", flush=True)
    print(f"  [4] learning curve (self-learned, +{NPOS * NTRIAL}/step):")
    for it in range(CURVE_STEPS):
        collect(NPOS, NTRIAL); world.train(epochs=600)
        print(f"    after {(it + 1) * NPOS * NTRIAL} more own trials (model {world.n()}): self {rate('self')}/{TEST}",
              flush=True)


# ---------------------------------------------------------------------------------------------
# AUSWAHL NACH EIGENSCHAFTEN statt nach Objektnamen (Nutzeridee 2026-09-03/04).
#
# WARUM: bisher waehlt die GUI einen KOERPERNAMEN, und damit ein Objekt nur adressierbar ist,
# muss zuvor eine eigene Formklasse entstanden sein ("Geburt") und einen Knopf bekommen haben.
# Genau dort ist jeder Versuch dieser Sitzung gescheitert -- vier Eingriffe am Anspruchstor,
# alle gemessen wirkungslos oder schaedlich (s. [[act23-faktorisierung]]).  Der Nutzer hat
# vorgeschlagen, den Umweg ganz zu lassen: ein Objekt IST eine Kombination aus Farbe, Form und
# Groesse, und genau so soll es benannt werden.
#
# MESSTECHNISCH GEDECKT: die drei Eigenschaften liegen je Detektion bereits vor
# (colours.classify(chroma) | det["shape"] | det["dicke"]), und ueber die acht heutigen Koerper
# sind die Tripel EINDEUTIG -- 8 verschiedene Tripel fuer 8 Koerper.
# EHRLICH DAZU: die Eindeutigkeit kommt heute fast ganz aus der FARBE (7 Klassen fuer 8 Koerper,
# die einzige Kollision farbe-4 loest die Form auf).  Die Dicke trennt unter den bestehenden
# Koerpern NICHTS (8,06-8,74 px) -- alle Balken sind 14 mm breit.  Sie zahlt sich erst aus, wenn
# Objekte Farbe UND Form teilen; bei den Y-Varianten trennte sie mit dem 6- bis 40-fachen der
# Streuung.
# Bandgrenzen GEMESSEN in auflaesungsunabhaengigen Einheiten (px_scale-normiert, Bezug 240):
#   Y10 5,00 +-0,00 | L 5,39 +-0,33 | U 5,83 +-0,09 | X 5,83 +-0,14 | Y14 5,83 +-0,08
#   T 6,00 +-0,08 | red 6,03 +-0,15 | Y20 7,07 +-0,03
# EHRLICH: alle HEUTIGEN Koerper liegen zwischen 5,39 und 6,03 -- die Groesse trennt unter ihnen
# NICHTS (alle Balken sind 14 mm breit).  Sie trennt erst absichtlich verschiedene Varianten:
# Y10 und Y20 fallen klar heraus.  Die Achse ist also vorbereitet, nicht heute schon nuetzlich.
GROESSEN_BAENDER = [("duenn", 0.0, 5.2), ("mittel", 5.2, 6.5), ("dick", 6.5, 99.0)]

# SIEBTER ANLAUF ZUR GROESSENACHSE (ACT23_GROESSE_SPANNE, Vorgabe 0 bis gemessen).
# ANLASS: wiki/befunde/relrings-split-zielkonflikt.md -- groessen-invariante Klassen tragen mehr
# Koerper, und das Eigenschafts-Tripel trifft dann oefter den falschen.  Die Groesse soll die
# verlorene Trennschaerfe zurueckholen ("die Faktorisierung gehoert NEBEN den Deskriptor").
# BEFUND, der die Aufgabe verschiebt: die heutige Achse ist nicht zu GROB, sie ist die FALSCHE.
# Gemessen ueber 7 Koerper x 10 Lagen:
#     Dicke  (heute)   obj_L 5,61 | obj_X 5,70 | obj_U 5,83 | obj_T 5,91 | cube 6,04
#                      -> alle sieben im Band "mittel" (5,2-6,5), Trennung 0,3-0,7 Streuungen
#     Spanne           cube 20,0 | obj_X 24,4 | obj_T 28,3 | obj_L 34,5 | obj_U 37,4 mm
#                      -> Trennung 2,2 bis 4,8 Streuungen
# Die DICKE misst die Materialbreite -- und alle Balken sind 14 mm breit, deshalb trennt sie
# nichts.  Die SPANNE (95.-Perzentil des Abstands vom Schwerpunkt) misst die Ausdehnung und
# trennt alle fuenf Formen.  Sie wird in perceive_all bereits gerechnet (Feld "span"), war aber
# nie als Adressachse herausgefuehrt.
# Die Baender liegen auf einem gleichmaessigen 5-mm-Raster, nicht auf den gemessenen Koerpern:
# koerpergenaue Grenzen waeren auf diese sieben ueberfittet und trennten nichts Neues.
GROESSE_SPANNE = os.environ.get("ACT23_GROESSE_SPANNE", "0") == "1"
# EINDEUTIG IST NICHT RICHTIG (ACT23_EIG_IDENT, Vorgabe 0 bis gemessen).  Die Wuerfelei in
# _auto_eig_umschreiben legt Achsen nach, bis `finde_nach_eigenschaften` genau EINEN Treffer
# meldet -- sie prueft aber nur die ANZAHL, nicht die IDENTITAET.  Trifft das Tripel genau eine
# Detektion, und ist das die FALSCHE, gilt die Adresse als eindeutig und ist trotzdem falsch.
# Genau das ist gemessen: im Split-Lauf meldeten 316 von 318 Adressen "genau ein Treffer", und
# 8,8 % lagen ueber 20 mm daneben (wiki/befunde/relrings-split-zielkonflikt.md).
# MIT dem Schalter muss der eine Treffer DERSELBE sein wie die Detektion auf dem gemeinten
# Koerper -- sonst werden weiter Achsen nachgelegt, und notfalls gar nicht umgeschrieben.
EIG_IDENT = os.environ.get("ACT23_EIG_IDENT", "0") == "1"
# STETIGE ADRESSIERUNG (ACT23_EIG_STETIG, Vorgabe 0 bis gemessen).
# NUTZERIDEE (wiki/fragen/stetige-adressierung.md): nicht das ETIKETT adressieren, sondern das
# GEMESSENE -- Chromatizitaet, Formeinbettung, Ausdehnung.  Der Vektor existiert fuer jedes Objekt,
# auch fuer nie gesehene, und hat keinen Lebenszyklus: er wird nicht geboren und verhungert nicht.
# ERSTER SCHRITT GEMESSEN (wiki/befunde/stetige-adressierung-erster-schritt.md): ueber fuenf
# Toleranzen bleiben die groben Adressierungsfehler flach (4,9-6,7 %) und sind vom Klassennamen
# nicht zu unterscheiden -- die stetige Achse ist trennscharf genug.  Sie ist aber auch nicht
# besser, sondern ein anderer Punkt auf derselben Tauschkurve (Genauigkeit gegen Rueckfall).
# WAS HIER GEBAUT IST, ist bewusst ADDITIV: die Namen bleiben in state.EIGENSCHAFT und tragen
# Anzeige und Protokoll weiter, denn ein Vektor laesst sich nicht in eine Statuszeile schreiben.
# Gematcht wird auf den Messwerten aus state.EIG_MESS -- die Namen sagen nur noch, WELCHE Achsen
# genannt sind.
EIG_STETIG = os.environ.get("ACT23_EIG_STETIG", "0") == "1"
# Formtoleranz RELATIV zum typischen Abstand zweier Klassen im Einbettungsraum (s. _eig_bezug):
# 0,5 = "halb so weit, wie zwei verschiedene Formen typischerweise auseinanderliegen".  Relativ,
# weil der Deskriptor sich mit dem Lernen verschiebt und eine nackte Zahl veralten wuerde.
EIG_TOL_FORM = float(os.environ.get("ACT23_EIG_TOL_FORM", "0.5"))
EIG_TOL_SPAN = float(os.environ.get("ACT23_EIG_TOL_SPAN", "0.005"))    # Groessentoleranz in METERN
# ADRESSE AUS EINER SICHTUNG, FUER EINEN KOERPER OHNE KLASSE (ACT23_EIG_DIREKT, Vorgabe 0).
# DER SCHRITT, DEN wiki/befunde/stetige-adressierung-im-lauf.md als naechsten benennt.  Der
# Einbau von EIG_STETIG war ADDITIV: er adressiert das Gemessene, aber die Klassen entstehen
# daneben weiter, also konnte der erhoffte Gewinn -- der aus ihrem WEGFALL kommen soll -- gar
# nicht auftreten.  Hier faellt der Lebenszyklus zum ersten Mal WEG:
#
#     bisher   3 Sichtungen -> Klassengeburt -> 3 von 6 Blicken -> Knopf -> kommandierbar
#     hier     1 Sichtung   -> Adresse       -> kommandierbar
#
# WARUM DAS OHNE KLASSE NUR STETIG GEHT: resolve() liefert fuer eine unbekannte Form (None, d) --
# es gibt schlicht keinen Namen, den die Formachse nennen koennte.  Die Chromatizitaet, die
# Formeinbettung und die Spanne liegen dagegen in JEDER Detektion vor, auch in der allerersten.
# Ohne ACT23_EIG_STETIG traegt die Adresse deshalb nur Farbe und Groesse (s. Meldung unten).
#
# WAS DAMIT GEGENSTANDSLOS WIRD, wenn es traegt: Geburt, Bestaetigung, Knopfvergabe, der
# Verhungerungsschutz und die Vergabe-Engstelle (wiki/befunde/vergabe-engstelle-diagnose.md).
# Die Aneignungskette brauchte dafuer 29 Episoden und drei Schalter
# (wiki/befunde/kette-haelt-30-episoden.md).
#
# WAS DAMIT AUCH WEGFAELLT, und das ist die Gegenrechnung: die Bestaetigung war ein FILTER.  Sie
# hat verschmolzene Blobs und Eintagsdetektionen aussortiert -- genau der Fehlermodus, der die
# Phantom-Farbklassen erzeugt hat (wiki/befunde/geburtenrate-chroma-phantome.md).  Eine Adresse
# aus einer einzigen Sichtung kann auf einem Blob entstehen, der zwei Koerper enthaelt, und
# zeigt dann dauerhaft daneben.  Dagegen stehen hier nur die BEREITS GEMESSENEN Tore, keine
# neuen: die Verschmelzungsschranke `area_hi` (dieselbe, die die Farbstufe schuetzt), der
# kalibrierte Arbeitsraum und die Identitaetspruefung der Wuerfelei (ACT23_EIG_IDENT).
# Ob das reicht, ist die eigentliche Messfrage dieses Schalters.
#
# WORAUF DER SCHALTER ANGEWIESEN IST, und das ist keine Nebensache: es muss ueberhaupt ein
# Koerper OHNE Eintrag in der Szene stehen.  Die Szene wird aus state.OBJECTS gebaut, also ist
# das heute genau einer -- der Probe-Koerper des Neuheits-Erzeugers, und auch der nur, solange
# er unentdeckt ist.  Im geladenen Zustand des Nutzers ist obj_T (die Vorgabe fuer NOVEL_BODY)
# laengst gebunden; OHNE ACT23_NOVEL_WEITER=1 findet EIG_DIREKT deshalb NICHTS vor und tut
# nichts.  Der Vergleich, fuer den er gebaut ist, lautet also:
#     Arm A   NOVEL_WEITER=1 FREIE_VERGABE=1                  der bekannte Weg ueber Klasse+Knopf
#     Arm B   NOVEL_WEITER=1 EIG_DIREKT=1 EIG_STETIG=1        eine Sichtung statt der Kette
EIG_DIREKT = os.environ.get("ACT23_EIG_DIREKT", "0") == "1"
# DIE FORMACHSE ZUERST (ACT23_EIG_DIREKT_FORM, Vorgabe 0).
# DER ENTSCHEIDENDE SCHRITT aus wiki/befunde/adresse-ohne-klasse-gemessen.md.  Dort loesten die
# beiden Direkt-Adressen voellig verschieden auf:
#     obj_T   (None, ~gesehen, None)    16 von 22 = 72,7 %    5,0 mm Median, 0 grobe Fehler
#     obj_X   (farbe-1, None, dick)      1 von 18 =  5,6 %    141 mm beim einzigen Treffer
# Die eine nennt NUR die Formachse, die andere nennt sie GAR NICHT -- aber es ist auch ein anderer
# Koerper, und die Messung trennt beides nicht.  Der Schalter trennt es: die Direkt-Adresse
# beginnt bei der Formachse ALLEIN und legt weitere nur nach, solange sie nicht eindeutig ist.
#
# WARUM NICHT EINFACH "Formachse zusaetzlich erzwingen": _eig_passt verknuepft alle genannten
# Achsen mit UND.  Eine Formachse ZU einer kaputten Farb-Groessen-Adresse dazuzulegen macht sie
# strenger, nicht besser -- der Gewinn kann nur entstehen, wenn die schlechten Achsen WEGFALLEN.
# Deshalb ersetzt der Schalter die Wuerfelei durch einen festen Startpunkt, statt sie zu ergaenzen.
#
# WAS DAGEGEN SPRICHT, und es ist ein echter Einwand: die Wuerfelei uebt ABSICHTLICH
# unvollstaendige Angaben ("das duenne Ding" statt "das duenne violette Kreuz").  Ein fester
# Startpunkt nimmt der Adressierung diese Vielfalt.  Fuer die Direkt-Adresse ist das vertretbar --
# sie steht den ganzen Lauf und wird nicht geuebt, sondern benutzt -- fuer _auto_eig_umschreiben
# waere es das nicht, und dort greift der Schalter deshalb NICHT.
EIG_DIREKT_FORM = os.environ.get("ACT23_EIG_DIREKT_FORM", "0") == "1"
# PLATZHALTER FUER EINE GENANNTE ACHSE OHNE KLASSENNAMEN.  _eig_passt liest `namen[i] is not
# None` als "diese Achse ist genannt" und vergleicht dann den MESSWERT -- der Name selbst wird
# beim stetigen Matchen nirgends gelesen.  Fuer eine Form ohne Klasse braucht es also nur
# irgendeinen Eintrag, der kein Klassenname ist.  Er steht in der Anzeige ("~gesehen + mittel")
# und sagt dort das Richtige: die Form ist genannt, aber sie hat keinen Namen.
# ER DARF NIRGENDS ALS KLASSE GELESEN WERDEN -- die eine Stelle, die das taete, ist der
# Fovea-Tracker (s. eig_servo); dort wird er ausdruecklich uebersprungen.
EIG_GESEHEN = "~gesehen"
# DIE DAUERHAFTE ADRESSE (ACT23_EIG_DAUERHAFT, Vorgabe 0 bis gemessen).  Befund
# wiki/befunde/direkt-adresse-verkuerzt-aneignung.md: obj_V bekam die Direkt-Adresse 'cube' und
# wurde in 15 Kommandos nie getroffen, mit 'cube + dick' (anderer Seed) in 7 von 16.  Zwei Teile:
#   (1) ANLEGEN.  _adresse_wuerfeln sucht die KUERZESTE Adresse, die in DIESER Szene eindeutig
#       ist.  Fuer ein Kommando, das jede Episode neu gewuerfelt wird, ist das richtig; eine
#       Direkt-Adresse steht aber den ganzen Lauf und muss auch in Szenen tragen, die sie nie
#       gesehen hat.  Sie nennt deshalb ALLE gemessenen Koerpereigenschaften (Form UND Groesse;
#       die Farbe bleibt draussen, solange die Welt umfaerbt).
#   (2) AUFLOESEN.  Passen mehrere Detektionen, gewinnt bisher die FLAECHENGROESSTE -- bei 'cube'
#       also irgendein Wuerfel.  Mit dem Schalter gewinnt bei einer stetigen Adresse die, die dem
#       GESPEICHERTEN MESSWERT am naechsten liegt.
# VORGABE 1 seit 2026-09-26 (Nutzerentscheidung nach der Messung: V/11 0/15 -> 5/16 geliefert,
# Klaue am richtigen Koerper 38 -> 51 von 59).  Wirkt nur mit ACT23_EIG_STETIG bzw. EIG_DIREKT.
EIG_DAUERHAFT = os.environ.get("ACT23_EIG_DAUERHAFT", "1") == "1"
# DIE ADRESSE NACHFUEHREN (ACT23_EIG_NACHFUEHREN, Vorgabe 0 bis gemessen).  Eine Direkt-Adresse
# stammt aus EINER Sichtung, und ein asymmetrischer Koerper sieht in jeder Lage anders aus
# (gemessen: 9 von 56 Aufloesungen > 40 mm daneben, 26 von 56 mehrdeutig).  Nachgefuehrt wird
# nach dem Muster von _streuung: hat der Agent den Koerper SELBST getragen, ist das Ding am
# Loslass-Punkt dasselbe wie vorher -- Objektkonstanz aus der eigenen Handlung, kein Etikett.
# Zwei Sicherungen gegen Verwechslung: die Adresse muss in DIESER Episode EINDEUTIG aufgeloest
# haben (sonst kann der Arm etwas Fremdes getragen haben), und am Loslass-Punkt muss genau EIN
# sauberer Fleck liegen.  Gespeichert werden BEISPIELE (hoechstens EIG_NACH_MAX), kein Mittelwert:
# ein Mittel laege zwischen den Lagen.  Ein Treffer zaehlt, wenn er zu irgendeinem Beispiel passt.
EIG_NACHFUEHREN = os.environ.get("ACT23_EIG_NACHFUEHREN", "0") == "1"
EIG_NACH_MAX = int(os.environ.get("ACT23_EIG_NACH_MAX", "10"))
# GEGENBEISPIELE (ACT23_EIG_GEGEN, Vorgabe 0 bis gemessen).  Das Nachfuehren zeigte: die
# Fehlaufloesungen entstehen, weil FREMDE Koerper in die Toleranz fallen, nicht weil der eigene
# herausfaellt.  Also lernt die Adresse, was sie NICHT treffen darf.  Ohne Etikett: was im
# SELBEN Blick raeumlich getrennt neben dem Koerper liegt, ist per Anschauung ein anderes Ding.
# Quellen: (1) beim Anlegen der Direkt-Adresse die uebrigen sauberen Flecken im Bild, (2) beim
# Aufloesen die unterlegenen Mitbewerber, wenn der beste Treffer KLAR vorn liegt (hoechstens
# EIG_GEGEN_MARGE mal so weit vom Messwert wie der naechste).  Ein Fleck passt dann nur, wenn er
# innerhalb der Toleranz liegt UND dem eigenen Messwert naeher ist als jedem Gegenbeispiel.
EIG_GEGEN = os.environ.get("ACT23_EIG_GEGEN", "0") == "1"
EIG_GEGEN_MARGE = float(os.environ.get("ACT23_EIG_GEGEN_MARGE", "0.5"))
EIG_GEGEN_MAX = int(os.environ.get("ACT23_EIG_GEGEN_MAX", "20"))
# LAUT SAGEN, WAS FEHLT -- nicht still mitschalten (s. AUGMENT/NEIGHBOURS oben: ein Schalter, der
# einen zweiten heimlich umlegt, macht jedes A/B mehrdeutig).  Ohne EIG_STETIG ist EIG_DIREKT
# nicht wirkungslos, aber verstuemmelt: die Formachse faellt weg, weil es fuer eine unbekannte
# Form keinen Namen gibt, und die Adresse traegt nur Farbe und Groesse.
if EIG_DIREKT and not EIG_STETIG:
    print("  [Eig-Direkt] ACT23_EIG_DIREKT ist gesetzt, ACT23_EIG_STETIG aber NICHT -- eine "
          "Adresse ohne Klasse kann die FORMACHSE dann nicht nennen (resolve() liefert None) "
          "und traegt nur Farbe und Groesse.  Das ist genau der Vergleichsarm, wenn er "
          "beabsichtigt ist.", flush=True)
# =========================================================================================
# DAS ABLAGEZIEL ALS ADRESSE (ACT23_ZIEL_ADRESSE, Vorgabe 0).
#
# NUTZERIDEE 2026-09-17, Stufe 1 von wiki/fragen/stapeln-als-aufgabe.md: "als Ziel andere
# Objekte angeben koennen".  Die Sprache waechst dabei NICHT um ein Verb, sondern um einen TYP --
# der Zielplatz bekommt denselben Typ, den das Objekt schon hat:
#
#     heute      BEFEHL   := ADRESSE  AKTION  ORT
#     mit dem    BEFEHL   := ADRESSE  AKTION  BEZUG
#     Schalter   BEZUG    := ORT | RELATION ADRESSE
#                RELATION := an        (Stufe 1; "auf" waere Stufe 2 und braucht eine Hoehe)
#
# STUFE 1 IST BEWUSST OHNE HOEHE.  Ein Ziel AUF einem Koerper ist mit der heutigen Wahrnehmung
# nicht beurteilbar: die Homographie ist eine EBENEN-Abbildung, ein gestapelter Wuerfel liest
# gemessen 15,9 mm daneben (wiki/befunde/stapeln-bricht-die-tischebene.md), und der Erfolgsbegriff
# heisst woertlich "liegt auf dem Tisch".  "an" laesst beides unveraendert -- gemessen wird
# ausschliesslich die SPRACHAENDERUNG.
#
# WAS DIE AENDERUNG WERT IST, unabhaengig von jeder Quote: das Ablageziel ist heute das EINZIGE
# Stueck des Befehls, das der Agent NICHT wahrnimmt.  state.goal_fn liefert marker_xy(), und das
# liest sim.d.mocap_pos -- eine privilegierte Designer-Koordinate.  Eine Zieladresse wird dagegen
# ueber finde_nach_eigenschaften aus der eigenen Kamera aufgeloest, genau wie das Objekt.  Der
# Schalter nimmt dem Kommando also sein letztes Privileg (wiki/ziel.md).
#
# WARUM NEBEN UND NICHT AUF, im Abstand ZIEL_ABSTAND: 0,05 m ist keine neue Zahl, sondern
# dieselbe, mit der run_combined seit jeher jedes Ziel von jedem Koerper wegschiebt
# (pc_act16: clear(tgt, OBJS, 0.05)).  Damit bleibt die Saeuberung wirkungslos statt zu stoeren,
# und ein geliefertes Objekt beruehrt den Bezugskoerper nicht.
#
# DIE PEILUNG WIRD GEWUERFELT, nicht gesetzt: acht Richtungen ab einem zufaelligen Winkel, die
# erste erreichbare gewinnt.  Ein fester Versatz waere eine geskriptete Konvention ("immer
# oestlich"); der Wurf ist dasselbe, was die Marker-Vorgabe mit place_selected_random ohnehin tut.
#
# DIE ADRESSE WIRD JEDE EPISODE NEU GEWUERFELT -- wie in _auto_eig_umschreiben und anders als
# eine Direkt-Adresse.  Deshalb darf sie die FARBE nennen, obwohl ACT23_FARB_MISCHUNG jede Episode
# umfaerbt: gewuerfelt wird NACH _farbe_wuerfeln, die Adresse gilt genau fuer diese eine Episode.
# Der Befund wiki/befunde/dauer-adresse-vertraegt-keine-farbe.md trifft nur DAUERHAFTE Adressen.
ZIEL_ADRESSE = os.environ.get("ACT23_ZIEL_ADRESSE", "0") == "1"
ZIEL_ABSTAND = float(os.environ.get("ACT23_ZIEL_ABSTAND", "0.05"))
# =========================================================================================
# DIE RELATION (ACT23_ZIEL_RELATION, Vorgabe "an").  Stufe 2 von
# wiki/fragen/stapeln-als-aufgabe.md.
#
#     an    das Objekt kommt NEBEN den Bezugskoerper, ZIEL_ABSTAND entfernt (Stufe 1)
#     auf   das Objekt kommt AUF ihn -- das Ziel ist seine Stelle, und die Ablagehoehe steigt
#
# WARUM "auf" DER LEICHTERE FALL IST, entgegen der urspruenglichen Stufenfolge: die gemessene
# Sperre ist LATERAL.  Der Arm kommt einem Koerper nicht naeher als ~37 mm, weil die Klaue NEBEN
# ihm absenken muss und dabei in 64 % der Faelle gegen ihn stoesst -- der untrainierte Teacher
# genauso wenig wie die Policy (wiki/befunde/nahe-ablage-ist-mechanik.md).  Beim Stapeln liegt der
# Bezugskoerper UNTER dem getragenen Objekt und gar nicht im Absenkweg.
#
# WOHER DIE HOEHE KOMMT, und das ist die einzige Stelle, an der hier ein Privileg sitzt:
# `GRASP_Z + Oberkante des Bezugskoerpers`.  Die Oberkante kommt aus dem Simulator, weil die
# Wahrnehmung sie nicht hergibt (die Homographie ist eine Ebenen-Abbildung).  Das ist nach
# wiki/mechanismen/laufzeit-regeln.md als TEACHER-Geruest zulaessig -- wie WRIST_ALIGN -, und es
# muss zur Testzeit verschwinden: die Policy hat die Hoehe ab ACT16_GOAL_Z im Zustandsvektor und
# soll sie lernen.  Solange sie das nicht kann, ist ein "auf"-Lauf ein Teacher-Lauf.
# WARUM GRASP_Z + Oberkante die richtige Formel ist: GRASP_Z (0,014) ist die HANDhoehe, bei der ein
# Koerper mit Ruhemitte 0,012 abgelegt wird, also Handhoehe = Ruhemitte + 0,002.  Steht der Koerper
# auf einer Auflage der Hoehe h, liegt seine Ruhemitte bei h + 0,012, die Hand also bei
# GRASP_Z + h.  Alle Koerper dieser Welt sind 24 mm hoch (0,012 Halbmass), der Aufschlag ist
# deshalb fuer alle derselbe.
ZIEL_RELATION = os.environ.get("ACT23_ZIEL_RELATION", "an").strip().lower()
if ZIEL_RELATION not in ("an", "auf", "richtung", "alle"):
    raise SystemExit(f"ACT23_ZIEL_RELATION muss 'an', 'auf', 'richtung' oder 'alle' sein, "
                     f"nicht {ZIEL_RELATION!r}")
# "alle" (Nutzerwunsch 2026-09-24): je Episode wird die Relation gewuerfelt -- "auf" mit 1/5,
# sonst eines der vier Richtungswoerter.  Zusammen mit den zufaelligen Farb-/Formkombinationen
# der Szene ist das das weite Spielfeld, auf dem Generalisierung auf NIE geuebte Kombinationen
# beobachtbar wird (wiki/fragen/stapeln-als-aufgabe.md).
# =========================================================================================
# AUF BELIEBIGE KOERPER (ACT23_AUF_ALLE, Vorgabe 0).  Nutzerwunsch 2026-09-24.  Bisher nimmt
# "auf" nur die STUETZEN (Platten), weil ein 24-mm-Wuerfel auf einem Wuerfel unter 12 mm Versatz
# verlangt und die Ablage im Median 19-25 mm daneben liegt.  Der Nutzer will die Ablage AUF
# anderen Koerpern trotzdem ueben -- das Ziel und das Hinlegen, nicht das Liegenbleiben.
AUF_ALLE = os.environ.get("ACT23_AUF_ALLE", "0") == "1"
# ERFOLG BEIM LOSLASSEN (ACT23_AUF_LOSLASSEN, Vorgabe 0).  Nutzervorgabe: "Wenn es beim
# Loslassen herunter rutscht, finde ich das nicht schlimm ... verbesserungswuerdig, aber nicht
# als Fehler."  Bei einer "auf"-Ablage zaehlt dann als geliefert, was im LETZTEN gehaltenen
# Augenblick seitlich innerhalb der Liefertoleranz ueber dem Ziel stand und mit der Unterkante auf
# Hoehe der Oberkante des Zielkoerpers war.  Ob es danach oben bleibt, steht getrennt im Protokoll.
# EIGENER Schalter, nicht an AUF_ALLE gehaengt: er aendert das Erfolgsetikett, aus dem gelernt
# wird, und muss einzeln abschaltbar sein.
AUF_LOSLASSEN = os.environ.get("ACT23_AUF_LOSLASSEN", "0") == "1"
# DAS ZIEL NOCHMAL ANSCHAUEN (ACT23_ZIEL_NACHSEHEN, Vorgabe 0 bis gemessen).  Nutzeridee
# 2026-09-26 (wiki/fragen/aufmerksamkeit-objekt-ziel.md): das Ziel wird heute EINMAL je Episode
# gesehen.  Mit dem Schalter loest der Agent die Zieladresse ein zweites Mal ueber die Kamera auf,
# sobald er traegt und die Hand in ACT16_NACHSEH_R um das Ziel steht.  Nur fuer wahrgenommene Ziele
# ("an" und Richtungswoerter); ein Marker ist eine exakte Koordinate, dort gibt es nichts zu sehen.
ZIEL_NACHSEHEN = os.environ.get("ACT23_ZIEL_NACHSEHEN", "0") == "1"
# DAS OBJEKT IN DER HAND ANSCHAUEN (ACT23_OBJ_SEHEN, Vorgabe 0).  Kurz vor dem Ablegen schaut der
# Agent das GETRAGENE Objekt an: die Detektion naechst der eigenen Hand (innerhalb 40 mm).  Ohne
# ACT16_OBJ_VERSATZ nur Messung.
OBJ_SEHEN = os.environ.get("ACT23_OBJ_SEHEN", "0") == "1"
# DEN BLICK AUF DAS OBJEKT IN DER HAND SELBST KORRIGIEREN LERNEN (ACT23_BLICK_LERNEN, Vorgabe 0).
# Aus 34 mm Hoehe sieht die Kamera das gehaltene Objekt 7-9 mm falsch (Parallaxe: die Homographie
# bildet auf die Tischebene ab).  Nach dem Ablegen liegt es auf dem Tisch und wird DORT genau gesehen.
# Das Etikett kommt also aus Kamera und eigener Hand, ohne Teacher und ohne Simulator-Wahrheit:
#     Merkmale  gesehener Versatz Objekt-minus-Hand, Handlage und -hoehe beim Blick
#     Etikett   gesehene Ruhelage nach dem Ablegen minus Hand beim Loslassen
# Gelernt wird "wo landet das Objekt relativ zur Hand" -- Parallaxe UND die typische Drift nach dem
# Loslassen in einem.  1 = lernen und vorhersagen, aber nicht benutzen (Schatten); 2 = benutzen,
# sobald BLICK_MIN Beispiele da sind.  Die Beispiele werden im Zustand gespeichert.
# DAS GETRAGENE OBJEKT UEBER SEINE EIGENSCHAFT SUCHEN (ACT23_OBJ_EIG, Vorgabe 0).  Gemessen 2026-09-29:
# der Blick auf das Objekt in der Hand nahm den naechsten Fleck im 40-mm-Umkreis -- nahe am Ziel
# manchmal den BEZUGSKOERPER, und die Nachfuehrung schob das Objekt weg.  Mit dem Schalter zaehlen im
# 60-mm-Umkreis nur Flecken, deren Farbe (Chromatizitaet) zur eigenen Sichtung des Objekts zu Beginn
# der Episode passt (situation_feats.last_det); passt keiner, gilt es als nicht gesehen.
OBJ_EIG = int(os.environ.get("ACT23_OBJ_EIG", "0"))
# 2 = die Referenzfarbe aus einer Sichtung IN DER HAND (2026-09-29): gemessen fand die Farbe der
#     Tischsichtung zu Episodenbeginn das gehaltene Objekt kaum (18 statt 51 Sichtungen).  Gemerkt
#     wird sie, sobald die Klaue geschlossen ist und das Objekt noch steht (objekt_merken_fn) -- dieselbe
#     Sichtlage wie beim Ablegen, und die Nachbarn stehen dann weit weg (Szene: >= 131 mm).
OBJ_EIG_TOL = float(os.environ.get("ACT23_OBJ_EIG_TOL", "0.05"))
BLICK_LERNEN = int(os.environ.get("ACT23_BLICK_LERNEN", "0"))
BLICK_MIN = int(os.environ.get("ACT23_BLICK_MIN", "12"))
BLICK_MAX = 400
# ERLAUBTE ZELLEN (ACT23_ZIEL_ZELLEN, Vorgabe leer = alle).  Fuer die Generalisierungsmessung
# (wiki/befunde/generalisierung-relation-zielart.md): eine Zelle ist WORT:ZIELART, WORT aus
# auf/links/rechts/vor/hinter, ZIELART aus platte/wuerfel/balken.  Ist die Liste gesetzt, wird je
# Episode zuerst ein erlaubtes Wort gewuerfelt, dann ein Bezugskoerper einer dafuer erlaubten Art.
# So lassen sich Kombinationen im Training AUSLASSEN und im Test gezielt abfragen.  Das ist
# Aufgabenerzeugung (welche Uebung gestellt wird), keine Laufzeitregel.
ZIEL_ZELLEN = {tuple(z.strip().lower().split(":")) for z in
               os.environ.get("ACT23_ZIEL_ZELLEN", "").split(",") if z.strip()}
for _z in ZIEL_ZELLEN:
    if len(_z) != 2 or _z[0] not in ("auf", "links", "rechts", "vor", "hinter")             or _z[1] not in ("platte", "wuerfel", "balken"):
        raise SystemExit(f"ACT23_ZIEL_ZELLEN: '{':'.join(_z)}' ist keine Zelle WORT:ZIELART")


def zielart(body):
    """Die Art eines Bezugskoerpers fuer ACT23_ZIEL_ZELLEN -- Aufgabenerzeugung, nicht Wahrnehmung."""
    if body.startswith("sockel"):
        return "platte"
    return "wuerfel" if body in ("obj_red", "obj_green", "obj_blue") else "balken"
# =========================================================================================
# RICHTUNGS-RELATIONEN (ACT23_ZIEL_RELATION=richtung).  Nutzeridee 2026-09-24,
# wiki/fragen/richtungs-relationen.md: "lege es LINKS / RECHTS / VOR / HINTER Y".
#
# DAS BEZUGSSYSTEM IST DAS KAMERABILD (Nutzerentscheidung): "links" heisst links im Bild, das
# der Agent sieht.  Das Wort ist die Sprache selbst und muss von aussen kommen -- die einzige
# Vorgabe.  Was es in der Welt bedeutet, in der der Arm handelt, gibt es auf zwei Wegen:
#
#   kamera   GERUEST.  Die Bildachse wird an der Stelle des Bezugs ueber die EIGENE Homographie
#            der Wahrnehmung in eine Weltrichtung uebersetzt.  Kein Simulator-Wissen, aber eine
#            gerechnete Bedeutung.
#   gelernt  Die Weltrichtung, die der Agent aus seinen EIGENEN Ablagen gesammelt hat: nach jeder
#            Ablage neben einem Bezug (auch bei "an" mit zufaelliger Peilung, also beim Spielen)
#            sieht er, in welcher Bildrichtung sein Koerper vom Bezug liegt, und merkt sich die
#            Weltverschiebung unter DIESEM Wort (Etikett im Nachhinein, wie beim Tastetikett).
#            Solange ein Wort weniger als RICHTUNG_MIN Beispiele hat: Rueckfall auf kamera, laut.
#
# Gemessen vor dem Bau (Sonde, 9 Stellen): die vier Bildachsen liegen hier auf Weltachsen, bis
# 3 Grad genau -- links = +y, rechts = -y, hinter = +x (weg von der Kamera), vor = -x.
RICHTUNG_QUELLE = os.environ.get("ACT23_RICHTUNG_QUELLE", "kamera").strip().lower()
if RICHTUNG_QUELLE not in ("kamera", "gelernt"):
    raise SystemExit(f"ACT23_RICHTUNG_QUELLE muss 'kamera' oder 'gelernt' sein, "
                     f"nicht {RICHTUNG_QUELLE!r}")
RICHTUNG_MIN = int(os.environ.get("ACT23_RICHTUNG_MIN", "3"))
# Wort -> Richtung im BILD (px: x nach rechts, y nach unten, wie shape_clf "px").
RICHTUNGS_WOERTER = {"links": (-1.0, 0.0), "rechts": (1.0, 0.0),
                     "hinter": (0.0, -1.0), "vor": (0.0, 1.0)}
# =========================================================================================
# DIE HOEHE SEHEN STATT WISSEN (ACT23_HOEHE_SEHEN, Vorgabe 0).
#
# `_ziel_aufloesen` rechnet die Ablagehoehe als GRASP_Z + Oberkante, und die Oberkante kommt
# heute aus `sim.m.geom_size` -- das LETZTE Privileg auf dem Stapelpfad.  Nach
# wiki/mechanismen/laufzeit-regeln.md darf ein Geruest die Trainingsdaten stuetzen und muss zur
# Testzeit verschwinden.
#
# DASS ES GEHT, IST GEMESSEN (wiki/befunde/hoehe-steckt-in-der-wahrnehmung.md): die scheinbare
# FLAECHE der Auflage steigt an 30 von 30 Stellen streng monoton mit der Hoehe.  Allein taugt sie
# nichts -- der Ort streut 2,7-mal so stark wie der Hoehenhub --, zusammen mit dem wahrgenommenen
# ORT und der Materialdicke aber: 1,31 mm Fehler und 77 % richtige Stufe gegen 4,00 mm und 33 %
# Grundrate, stellenweise gehalten.
#
#   0 = wie bisher, die Oberkante kommt aus geom_size (der Schaetzer lernt trotzdem mit und
#       schreibt seinen Fehler in die Zeile -- so misst EIN Lauf, was er koennte)
#   1 = die Oberkante kommt aus dem Schaetzer.  Solange er zu wenige Zeilen hat, faellt er
#       LAUT auf das Privileg zurueck; ein stiller Rueckfall waere genau die Verwechslung,
#       die der Schalter aufdecken soll.
HOEHE_SEHEN = os.environ.get("ACT23_HOEHE_SEHEN", "0") == "1"
# DIE HOEHE ERTASTEN STATT SIE GESAGT ZU BEKOMMEN (ACT23_HOEHE_TASTEN, Vorgabe 0).
# Nutzerwunsch 2026-09-21: "weniger Teacher ist immer besser".  Mit diesem Schalter labelt der
# HoehenSchaetzer NICHT mehr mit `sim.m.geom_size`, sondern mit der Hoehe, bei der die Hand das
# getragene Objekt hat AUFSETZEN fuehlen (ACT16_TASTEN, dort steht die Mechanik).  Damit faellt
# das letzte Privileg auch aus dem TRAINING, nicht nur aus der Laufzeit.
# Der Schalter zieht ACT16_TASTEN NICHT heimlich mit -- der Start sagt, wenn es fehlt.
HOEHE_TASTEN = os.environ.get("ACT23_HOEHE_TASTEN", "0") == "1"
# DIE GROESSE DES GREIFOBJEKTS SEHEN STATT WISSEN (ACT23_GROESSE_SEHEN, Vorgabe 1 seit 2026-10-03).
# Der Policy-Zustand traegt obj_h und obj_fp (halbe Hoehe, halbe Kurzachse), und beide kamen aus
# MuJoCo (pc_act16 run_combined: geom_half).  Hoehe ist heute fuer alle Koerper 12 mm, die
# Kurzachse aber 12 (Wuerfel) / 9 (Balken) / 6-7 mm (Formen) -- die Policy bekam die Kategorie
# also gesagt.  Der GroessenSchaetzer liest beides aus der Detektion (Flaeche, Dicke, Spanne, Ort).
#   0 = Privileg wie bisher; der Schaetzer lernt mit und schreibt seinen Fehler ins Protokoll
#   1 = die Policy sieht die Schaetzung.  Zu wenige Zeilen oder keine Detektion -> LAUTER Rueckfall.
# GEMESSEN (wiki/befunde/groesse-sehen-ab.md, 8 Seeds x 50, gepaart): Privileg 52,2 %, Schaetzung
# 53,8 %, Seeds 3:3:2 -- das Privileg faellt ohne Verlust.  Hat der Schaetzer beim Start weniger
# als 200 Zeilen, sammelt act23 selbst 200 Szenen ohne Arm (~40 s, s. _groesse_sammeln).
# Etiketten: privilegierte Geometrie (Geruest, s. laufzeit-regeln.md).  Ersetzt wird nur, was die
# POLICY sieht -- Buchhaltung, Kredit und Riegel bleiben, s. pc_act16.GROESSE_FN.
GROESSE_SEHEN = os.environ.get("ACT23_GROESSE_SEHEN", "1") == "1"
# DER PRIVILEGIERTE WAHRNEHMUNGS-RUECKFALL (ACT23_RUECKFALL, Vorgabe "aufgeben" seit 2026-10-03).  Findet perceive
# das kommandierte Objekt nicht (Formklasse/Farbklasse/Eigenschaften treffen nichts), nahm es bisher
# still die WAHRE Lage aus MuJoCo.  Schritt 2 aus wiki/mechanismen/laufzeit-regeln.md.
#   privileg = wie bisher, aber jetzt IMMER protokolliert ("[Rueckfall] ...")
#   aufgeben = nicht gefunden heisst: kein Versuch.  Der Arm bewegt sich nicht, gelernt wird nichts,
#              die Episode zaehlt als nicht geliefert.  Die Differenz der beiden Arme ist genau das,
#              was das Privileg heute einbringt.
# Die Wahrnehmung laeuft dafuer in BEIDEN Faellen einmal VOR run_combined (s. run_one, _vorblick)
# und wird dort wiederverwendet -- sonst haette nur ein Arm einen zusaetzlichen Blick.
# GEMESSEN (wiki/befunde/rueckfall-privileg-gemessen.md): im Namensbetrieb 1 Rueckfall in 400
# Episoden (er rettete 1 Lieferung), im Eigenschaftsbetrieb 2 Rueckfall-Episoden in 200, beide auch
# mit Privileg gescheitert (Quote 111 gegen 114 von 200).  Das Privileg rettet praktisch nichts.
RUECKFALL = os.environ.get("ACT23_RUECKFALL", "aufgeben").strip().lower()
# RIEGEL UND REFLEX NUR NOCH IM TRAINING (ACT23_REGELN_NETZ, Vorgabe 0 seit 2026-10-04).
# Mit Choreo "netz" faehrt die gelernte Policy allein -- CLOSE_GUARD und REFLEX sind aus.  Mit
# Choreo "fsm" (der Teacher, der die Trainingsdaten erzeugt) bleiben sie als Geruest an.  Das
# ist das act21-Prinzip ACT21_RULES_TRAIN_ONLY, das act23 nie mitgemacht hatte.
# GEMESSEN (wiki/befunde/riegel-reflex-entfernt.md, 8 Seeds x 50, gepaart): an 196/400, aus
# 196/400, 95 %-Intervall der Differenz [-7, +7] -- das vorab festgelegte Kriterium (Schaden
# > 10 Punkte ausgeschlossen) ist erfuellt.  ACT23_REGELN_NETZ=1 = altes Verhalten.
REGELN_NETZ = os.environ.get("ACT23_REGELN_NETZ", "0") == "1"
# NEUE OBJEKTHOEHEN (ACT23_HOEHEN, z. B. "16,24,32" in mm; Vorgabe leer = alle 24 mm wie bisher).
# Jede neue Szene wuerfelt fuer jedes STEHENDE Objekt eine Hoehe aus der Liste; ALLE Teile eines
# Koerpers werden gemeinsam gestreckt (Grundriss unveraendert, Masse unveraendert -- MuJoCo
# rechnet Masse und Traegheit beim Kompilieren).  Die Probe auf das Projektziel nach Schritt 1
# (wiki/befunde/groesse-sehen-ab.md): bis hierhin war die Hoehe eine Konstante, und die Policy
# hat sie nie gebraucht (Spalte 9 stumm).  Jetzt muss sie aus der Wahrnehmung kommen.
# DER LOSLASS-KOPF (ACT23_LOSLASS_KOPF, Vorgabe 0 bis gemessen).  Ein eigener kleiner Lerner fuer
# EINEN Aspekt -- "jetzt loslassen?" -- aus Einzelaspekten (s. arm_modules/loslass_kopf.py).  Im
# Netzbetrieb setzt er den Greiferwunsch der Policy auf "offen", wenn er drei Schritte in Folge
# "loslassen" sagt.  Gelernt aus den Teacher-Etiketten; braucht ACT16_ABLAGE_FIX=1, sonst sind die
# Etiketten am Ziel widerspruechlich (der Start sagt es).  Mit ACT16_ABLAGE_FIX=1 werden die alten
# Pufferzeilen, deren Etikett sich dadurch aendert, beim Laden einmal neu etikettiert.
LOSLASS_KOPF = os.environ.get("ACT23_LOSLASS_KOPF", "0") == "1"
# AUS DEM EIGENEN ERGEBNIS (ACT23_LOSLASS_SELBST, Vorgabe 0).  Jede Episode, in der getragen wurde,
# liefert eine Zeile: die Haltepose beim Loslassen (vom Kopf, oder die letzte vor der
# Aufraeumbewegung) -> Selbst-Urteil der Kamera.  Gesammelt wird auch OHNE ACT23_LOSLASS_KOPF; mit
# ihm entscheidet das Erfolgsnetz, sobald es bereit ist (s. LoslassKopf.erfolg_bereit).
LOSLASS_SELBST = os.environ.get("ACT23_LOSLASS_SELBST", "0") == "1"
LOSLASS_RUHIG = int(os.environ.get("ACT23_LOSLASS_RUHIG", "5"))
# AUFGEBEN AUS EIGENER ERFAHRUNG (ACT23_AUFGEBEN, Vorgabe 0 bis gemessen).  Alle AUFGEBEN_TAKT
# Schritte eine Momentaufnahme aus Einzelaspekten (s. arm_modules/aufgeben_kopf.py); nach der
# Episode bekommen alle das Selbst-Urteil als Etikett.  Sobald der Kopf bereit ist: aufgeben, wenn
# er ab AUFGEBEN_AB Schritten zweimal in Folge weniger als AUFGEBEN_P Erfolg erwartet.
# KEINE SELBSTBESTAETIGUNG: aufgegebene Episoden lernen NICHT mit -- ihr "nicht geliefert" waere
# die Folge des Aufgebens, nicht des Zustands, und der Kopf gaebe immer frueher auf.
# ZUFASSEN AUS DEM EIGENEN ERGEBNIS, STUFE 1 (ACT23_GRIFF_SELBST, Vorgabe 0): jeder Greifversuch
# im Netzbetrieb wird mit seinen Einzelaspekten im Moment des Zufassens und dem eigenen Tastsinn-
# Ergebnis protokolliert ("[Griff-Versuch] ..."), zum Pruefen, ob die Aspekte trennen.  Noch kein
# Eingriff (s. arm_modules/griff_kopf.py).
GRIFF_SELBST = os.environ.get("ACT23_GRIFF_SELBST", "0") == "1"
AUFGEBEN = os.environ.get("ACT23_AUFGEBEN", "0") == "1"
AUFGEBEN_TAKT = 50
AUFGEBEN_AB = int(os.environ.get("ACT23_AUFGEBEN_AB", "300"))
AUFGEBEN_P = float(os.environ.get("ACT23_AUFGEBEN_P", "0.05"))   # Schritte ruhige Hand vor dem Urteil (0 = aus)
HOEHEN = [float(v) / 1000.0 for v in os.environ.get("ACT23_HOEHEN", "").split(",") if v.strip()]
if RUECKFALL not in ("privileg", "aufgeben"):
    raise SystemExit(f"ACT23_RUECKFALL={RUECKFALL!r}: erlaubt sind privileg | aufgeben")

# =========================================================================================
# STUFE 4: DIE RELATION AUCH IN DER ADRESSE (ACT23_ADR_RELATION, Vorgabe 0).
#
#     bis Stufe 3   BEZUG   := ORT | RELATION ADRESSE
#     Stufe 4       ADRESSE := (Farbe?, Form?, Groesse?) | RELATION ADRESSE
#
# Damit ist "nimm das, was auf Y liegt" sagbar und die Sprache wird REKURSIV -- derselbe
# "Typ statt Verb"-Schnitt wie in Stufe 1, nur eine Ebene weiter.  Das Umstapeln faellt daraus
# heraus, ohne dass ein Verb dazukommt.
#
# WIE AUFGELOEST WIRD, ohne Privileg: `perceive_all` liefert mit
# ACT_SHAPE_CHROMA_KONZENTRISCH=1 fuer einen Stapel ZWEI Detektionen statt einer
# (wiki/befunde/stapel-wird-sichtbar.md, 24 von 25).  Zwei Detektionen naeher als
# ADR_REL_NAH beieinander sind ein Stapel; die GROESSERE ist die Auflage, die kleinere das,
# was darauf liegt.  Die Greifhoehe kommt aus derselben Quelle wie die Ablagehoehe in Stufe 2.
#
# ER ZIEHT CHROMA_KONZENTRISCH NICHT HEIMLICH MIT -- der Start sagt, wenn es fehlt.
ADR_RELATION = os.environ.get("ACT23_ADR_RELATION", "0") == "1"
# WANN LIEGT ETWAS AUFEINANDER?  Nicht "nah beieinander" -- das war die erste Fassung mit einem
# festen 45-mm-Abstand, und sie meldete in einer vollen Szene FUENF Stapel.  Ein gestapelter
# Koerper liegt nicht neben der Auflage, sondern INNERHALB ihrer Umrisslinie; genau deshalb
# verwirft ihn die raeumliche Wache des Chroma-Schnitts (wiki/befunde/stapel-wird-sichtbar.md).
# Das Kriterium ist also das exakte GEGENSTUECK dieser Wache und wie sie MASSSTABSRELATIV: der
# Abstand der beiden Schwerpunkte, gemessen an der Halbspanne des GROESSEREN Teils.  Keine Laenge
# in Millimetern, die an eine Plattengroesse gebunden waere.
ADR_REL_ANTEIL = float(os.environ.get("ACT23_ADR_REL_ANTEIL", "0.5"))
# UND DER GROESSENUNTERSCHIED: was getragen wird, ist kleiner als das, was traegt.  Zwei etwa
# gleich grosse Teile sind eher ein schattierter Einzelkoerper als ein Stapel.
ADR_REL_KLEINER = float(os.environ.get("ACT23_ADR_REL_KLEINER", "1.5"))
# ABSTAPELN (ACT23_ABSTAPELN, Vorgabe 0): die Szene baut den Stapel, der Befehl holt ihn
# herunter.  Das ist die Aufgabe, an der Stufe 4 gemessen wird -- ohne sie gaebe es nie einen
# gestapelten Koerper zu adressieren, weil die Episode ihn erst am ENDE erzeugt.
ABSTAPELN = os.environ.get("ACT23_ABSTAPELN", "0") == "1"
# DER STAPEL AUSSERHALB DER MITTE (ACT23_ABSTAPELN_VERSATZ, in m, Vorgabe 0).
# Der Abstapel-Aufbau stellte den Koerper GENAU in die Plattenmitte.  Dann liegt der Schwerpunkt
# des verschmolzenen Flecks auf ihm, und auch ein Arm, fuer den der Stapel unsichtbar ist, trifft
# ihn: gemessen greift er ihn in 51 von 90 Episoden (wiki/befunde/stufe4-drei-arme-gepaart.md).
# Der Test machte die Relation ueberfluessig.  Mit Versatz zielt die gewoehnliche Adresse daneben
# (Sonde: 18 mm bei 16 mm Versatz), waehrend der Chroma-Schnitt den Koerper weiter auf ~7 mm trifft.
# DIE RICHTUNG kommt aus crng -- mit ACT23_SZENE_JE_EPISODE also fuer alle Arme dieselbe.
ABSTAPELN_VERSATZ = float(os.environ.get("ACT23_ABSTAPELN_VERSATZ", "0"))
# =========================================================================================
# DIE SZENE JE EPISODE AUS (SEED, EPISODENNUMMER) (ACT23_SZENE_JE_EPISODE, Vorgabe 0).
#
# WARUM, gemessen im gepaarten Sweep (wiki/befunde/stufe4-sweep-widerlegt.md): zwei Arme mit
# demselben Seed sahen nur in 88 von 200 Episoden dieselbe Szene, meist trennten sie sich ab
# Episode 2 oder 3.  Die ganze Streuung zwischen den Szenen landete damit im Vergleich -- Arm A
# schwankte ueber die Seeds zwischen 20 und 60 %, und ein Unterschied von 10 Punkten war mit
# acht Seeds nicht aufzuloesen.
#
# DREI QUELLEN, und der Schalter behebt die zwei, die zur Szene gehoeren:
#   (1) DER GENERATOR.  `crng` laeuft ueber alle Episoden durch; jede abweichende Entscheidung
#       verschiebt alle spaeteren Ziehungen.  -> wird zu Beginn jeder Episode auf
#       default_rng([SEED, ep]) zurueckgesetzt (im Platz, damit alle Closures es sehen).
#   (2) DER WELTZUSTAND.  Zwischen zwei Szenenneubauten bleibt das kommandierte Objekt dort
#       liegen, wo der jeweilige Arm es hingelegt hat.  -> die Szene wird JEDE Episode neu
#       gebaut.  Das ist keine heimliche Nebenwirkung, sondern die Bedeutung des Schalters:
#       "jede Episode bekommt ihre Szene aus Seed und Episodennummer".
#   (3) DIE NEUGIER.  `curious_pick()` waehlt das Objekt nach GELERNTEN Werten, und die
#       unterscheiden sich zwischen den Armen.  Das ist Verhalten des Agenten, nicht Szene --
#       es wird NICHT umgeschaltet, sondern der Start meldet es.  Fuer eine gepaarte Messung
#       ACT23_AUTO_CURIOUS=0 setzen.
#
# DAS MESSINSTRUMENT: mit dem Schalter schreibt jede Episode einen [Szenen-Abdruck] -- eine
# Pruefsumme ueber Objektwahl, Ziel, alle Koerperlagen, Farben und Sockel.  Zwei Arme sind genau
# dann episodenweise gepaart, wenn ihre Abdruecke Zeile fuer Zeile uebereinstimmen.  Behauptet
# wird die Paarung nicht, sie wird nachgezaehlt.
SZENE_JE_EPISODE = os.environ.get("ACT23_SZENE_JE_EPISODE", "0") == "1"
# DEN SCHAETZER AUCH AUF DER BELEGTEN AUFLAGE LERNEN (ACT23_HOEHE_BELEGT, Vorgabe 0).
#
# WARUM, und es ist gemessen: der Hoehenschaetzer lernt beim Adressieren, also an der LEEREN
# Auflage (Flaeche rund 1424 px).  Gefragt wird er beim Abstapeln nach der BELEGTEN -- und die
# zerfaellt durch den Konzentrisch-Schnitt, die Auflage ist dann nur noch der groessere Rest
# (1160 px).  Der Versatz ist 264 px, der Hoehenhub nur 127-145: die Eingabe liegt weit
# ausserhalb von allem, was er kennt, und seine staerkste Achse ist ausgerechnet die Flaeche.
# Im Stufe-4-Lauf las er deshalb 6/10/14 mm als 11,1/6,0/9,2 -- die Reihenfolge zerstoert.
#
#     trainiert auf   geprueft auf   |Fehler|   richtige Stufe
#     NUR leer        leer            0,57 mm       96 %
#     NUR leer        belegt          6,00 mm       34 %   <- der Fall aus dem Lauf
#     NUR belegt      belegt          0,95 mm       74 %
#     beiden          leer            0,60 mm       97 %
#     beiden          belegt          0,91 mm       78 %
#
# Auf BEIDEN zu lernen ist also die Abhilfe und kostet auf der leeren Auflage nichts.  Dafuer
# braucht es keine zweite Messung: die Episode legt den Koerper ohnehin auf die Auflage, und das
# Tast-Etikett gilt unveraendert weiter -- die Oberkante der Auflage aendert sich nicht dadurch,
# dass etwas darauf steht.  Es ist dieselbe Zahl, nur ein zweites Aussehen dazu.
HOEHE_BELEGT = os.environ.get("ACT23_HOEHE_BELEGT", "0") == "1"

# DER SOCKEL IN DIE SZENE (ACT23_SOCKEL, Vorgabe 0).  Eine 70-mm-Platte als Stapelziel: die
# geometrische Toleranz (35 - 12 = 23 mm) passt damit zur gemessenen Ablagegenauigkeit von
# 21-25 mm, waehrend ein Wuerfel auf einem Wuerfel unter 12 mm verlangt.
# ER IST KEIN OBJEKT, sondern MOEBEL: er steht nicht in state.OBJECTS, wird nie kommandiert und
# nie gegriffen, sondern in state.STUETZEN gefuehrt.  Sonst koennte die Neugier ihn zum Greifen
# auswaehlen -- 70 mm breit und schwer.
SOCKEL = os.environ.get("ACT23_SOCKEL", "0") == "1"
# DIE VORGABESTELLE IST GESUCHT, NICHT GERATEN.  Sie maximiert den Abstand zu den
# Objekt-Slots der Vorgabe-Szenengroesse (ACT23_SCENE_N=4) und liefert 86 mm Freiraum gegen
# die gemessenen 80 mm, die es braucht.  Mit SCENE_N=5 oder 6 ist der Arbeitsraum zu klein:
# dort bleiben nur 72 bzw. 62 mm, und der Sockel verschmilzt mit einem Nachbarn.  Der
# Startcheck rechnet das nach und nennt die beste Stelle fuer die eingestellte Slot-Zahl.
SOCKEL_XY = [float(v) for v in os.environ.get("ACT23_SOCKEL_XY", "-0.018,0.149").split(",")]
# =========================================================================================
# LERNEN, OHNE ZU VERLERNEN -- drei Schalter aus wiki/befunde/policy-lernt-hoehe-als-ort.md.
# Der erste Lernlauf zum Stapeln hatte zwei Konstruktionsfehler, und beide sind hier behoben:
#
# (1) AUFGABEN MISCHEN (ACT23_ZIEL_MISCH=p, Vorgabe aus).  100 % Stapel-Episoden haben alle
#     Tisch-Erfahrung ausser dem geschuetzten Kern aus dem Puffer verdraengt, und die gewoehnliche
#     Ablage lag danach 12-15 mm zu hoch.  Mit p wird je Episode gewuerfelt: mit Wahrscheinlichkeit
#     p "auf den Sockel", sonst die Marker-Ablage.  Ein Kind, das stapeln lernt, hoert nicht auf,
#     Dinge auf den Tisch zu legen.
# (2) DER SOCKEL WANDERT (ACT23_SOCKEL_WANDERT=1).  Er stand immer an derselben Stelle, und damit
#     war die Ablagehoehe vollstaendig mit dem Zielort verwechselt: die Policy lernte "dort hoeher
#     ablegen", nicht "so hoch wie die Auflage" (+25 mm statt +8 in der kontrafaktischen Probe).
#     Mit jeder neuen Szene bekommt er eine neue Stelle mit >= 80 mm Freiraum zu den stehenden
#     Objekten (gemessene Verschmelzungsschranke, wiki/befunde/sockel-braucht-80mm-freiraum.md).
#     BRAUCHT ACT23_SCENE_N=3: mit vier Objekten bleiben nur +-12 mm Spielraum -- weniger als die
#     Wahrnehmung ohnehin streut --, mit dreien +-85 mm in x und 100 mm in y.
# (3) SOCKELHOEHEN (ACT23_SOCKEL_HOEHEN="6,10,14" in mm, Vorgabe "8").  Mit EINER Hoehe kennt die
#     14. Zustandsspalte nur zwei Werte, Tisch oder Sockel -- sie ist ein Schalter, keine Groesse,
#     und "Ablagehoehe = Auflagenhoehe" ist als Funktion gar nicht lernbar.  Mit mehreren Hoehen
#     wird die Probe scharf: gelernt heisst, die Zielhoehe steigt mit Steigung 1 in der Hoehe.
_zm = os.environ.get("ACT23_ZIEL_MISCH", "").strip()
ZIEL_MISCH = float(_zm) if _zm else None
# DAS STAPEL-SELBSTURTEIL (ACT23_SELBST_STAPEL, Vorgabe 0).  Der Agent beurteilt seinen eigenen
# Stapel aus der Farbstreuung des Auflagen-Blobs statt aus einer zweiten Detektion, die es
# nicht gibt (s. _selbst_stapel).  Vorgabe 0, bis die Uebereinstimmung mit dem privilegierten
# Urteil gemessen ist -- eine Selbstbewertung, der man zu frueh traut, vergiftet die
# Selbst-Imitation.
SELBST_STAPEL = os.environ.get("ACT23_SELBST_STAPEL", "0") == "1"
SOCKEL_WANDERT = os.environ.get("ACT23_SOCKEL_WANDERT", "0") == "1"
# DIE PLATTE AUSGEBLENDET STARTEN (ACT23_SOCKEL_AUS, Vorgabe 0) -- derselbe Zustand wie
# "Platte: ausgeblendet" in der GUI.  1 = geparkt, der Platz ist frei.  2 = geparkt, aber die
# Marker-Ziele meiden die Plattenstelle WEITER wie mit Platte: das ist der Messarm fuer das A/B
# "verwirrt die Platte das Netz?" (wiki/befunde/platte-ausblenden-ab.md).  Ohne die 2 saehe der
# Arm ohne Platte andere Ziele (bis zu 10 cm um die Platte), und man maesse die Zielverteilung.
SOCKEL_AUS = int(os.environ.get("ACT23_SOCKEL_AUS", "0"))
# ZWEI GRUNDRISSE (ACT23_SOCKEL2, Vorgabe 0).  Die 50-mm-Platte `sockel2` kommt dazu, und je
# Szene steht EINE der beiden in der Welt.  Sie ist die Bewaehrungsprobe fuer den
# HoehenSchaetzer: der liest die Oberkante aus der scheinbaren Flaeche, und die haengt am
# Grundriss 7,5-mal so stark wie an der Hoehe (gemessen 685 gegen 91,
# wiki/befunde/zweiter-grundriss-bricht-die-hoehe.md).  Der globale lineare Schaetzer der
# ersten Fassung faellt damit auf die Grundrate; der lokale kommt auf 92 %.
SOCKEL2 = os.environ.get("ACT23_SOCKEL2", "0") == "1"
# WIE VIELE AUFLAGENFORMEN im Wechsel (ACT23_SOCKEL_N, Vorgabe 1).  2 ist gleichbedeutend mit
# ACT23_SOCKEL2=1 (der aeltere Schalter bleibt, die Rezepte im Wiki nennen ihn).  3 nimmt die
# 60-mm-Platte dazu.
# GEMESSEN (wiki/befunde/dritte-auflage-bricht-die-nachbarschaft.md): mit DREI Formen faellt die
# SCHAETZUNG auf 62 % richtige Stufe und auf der neuen Platte auf 48 %, und eigene Zeilen fuer sie
# helfen NICHT -- die Ursache sind fremde Nachbarn, nicht fehlende Daten.
# ABER DIE AUFGABE MERKT ES NICHT (wiki/befunde/drei-auflagen-im-lauf.md): im act23-Lauf 85 gegen
# 88 % gestapelt, die neue Platte 7 von 7.  Die Fehlschlaege sind SEITLICH (Versatz 65 gegen
# 15 mm), der Hoehenfehler ist bei gelungenen und misslungenen Stapeln gleich gross.  Von
# ACT23_HOEHE_SEHEN wird deshalb NICHT abgeraten -- ein frueherer Entwurf tat das, gestuetzt allein
# auf die Sonde.
SOCKEL_N = max(1, min(3, int(os.environ.get("ACT23_SOCKEL_N", "2" if SOCKEL2 else "1"))))
SOCKEL_FORMEN = ["sockel", "sockel2", "sockel3"][:SOCKEL_N]
SOCKEL_HOEHEN = [float(v) / 1000.0 for v in os.environ.get("ACT23_SOCKEL_HOEHEN", "8").split(",")]
# LAUT SAGEN, WAS FEHLT -- nicht still mitschalten.  Ein Schalter, der einen zweiten heimlich
# umlegt, macht jedes A/B mehrdeutig (dieselbe Regel wie bei AUGMENT/NEIGHBOURS und EIG_DIREKT).
# "auf" braucht DREI fremde Schalter, und ohne sie ist es nicht wirkungslos, sondern STILL FALSCH:
if ZIEL_RELATION in ("auf", "alle"):
    _fehlt = []
    if not act16.GOAL_Z:
        _fehlt.append("ACT16_GOAL_Z=1 -- sonst wird die dritte Zielgroesse verworfen und die Klaue "
                      "faehrt auf Greifhoehe IN den Bezugskoerper")
    if act16.ZIEL_SAEUBERN:
        _fehlt.append("ACT16_ZIEL_SAEUBERN=0 -- sonst schiebt run_combined das Ziel um 0,05 m vom "
                      "Bezugskoerper WEG, und aus 'auf' wird 'daneben'")
    if not act16.ERFOLG_RUHT:
        _fehlt.append("ACT16_ERFOLG_RUHT=1 -- sonst heisst 'geliefert' woertlich 'liegt auf dem "
                      "Tisch' und JEDER gelungene Stapel zaehlt als Fehlschlag")
    if HOEHE_TASTEN and not act16.TASTEN:
        _fehlt.append("ACT16_TASTEN=1 -- ACT23_HOEHE_TASTEN labelt aus der ERTASTETEN "
                      "Aufsetzhoehe, und die entsteht nur, wenn die Ablagephase wirklich tastet; "
                      "sonst faellt kein einziges Lernbeispiel")
    if ADR_RELATION:
        from pc_cvnn.arm_modules import shape_classifier as _sc
        if not _sc.CHROMA_SPLIT or not _sc.CHROMA_KONZENTRISCH:
            _fehlt.append("ACT_SHAPE_CHROMA_SPLIT=1 ACT_SHAPE_CHROMA_KONZENTRISCH=1 -- ohne sie "
                          "bekommt ein gestapelter Koerper KEINE eigene Detektion (gemessen 0 von "
                          "25), und die Relation in der Adresse findet nie etwas")
        if not act16.GRIFF_Z:
            _fehlt.append("ACT16_GRIFF_Z=1 -- sonst wird die Greifhoehe verworfen und die Klaue "
                          "faehrt auf Tischhoehe UNTER den gestapelten Koerper")
    if not EIG_DIREKT:
        # DER FUENFTE SCHALTER, und er war bis 2026-09-20 nicht in dieser Liste.  Eine STUETZE
        # steht in state.STUETZEN und NICHT in state.OBJECTS -- die Farbbindung laeuft aber ueber
        # `bodies` aus OBJECTS, und die Formbindung schliesst STUETZEN ausdruecklich aus (Moebel
        # bekommt keinen Knopf).  Eine Auflage kann deshalb NIE eine gebundene Klasse bekommen,
        # und ohne Klasse hat ihre Adresse keine verfolgbare Achse: "keine verfolgbare Achse
        # (Farbe None, Form None, Groesse dick)" in JEDER Episode, Rueckfall auf den Marker.
        # Gemessen im Rauchtest: 0 von 4 Adressen ohne den Schalter, 4 von 4 mit ihm.
        _fehlt.append("ACT23_EIG_DIREKT=1 -- eine STUETZE kann per Bauart keine Klasse bekommen "
                      "(sie steht nicht in state.OBJECTS), also braucht ihre Adresse den "
                      "klassenlosen Weg; sonst faellt JEDE Episode auf den Marker zurueck")
    if _fehlt:
        print(f"  [Ziel-Relation] ACT23_ZIEL_RELATION={ZIEL_RELATION} ist gesetzt, aber es fehlt:",
              flush=True)
        for _m in _fehlt:
            print(f"      {_m}", flush=True)
    if not SOCKEL and not AUF_ALLE:
        print("  [Ziel-Relation] ACT23_SOCKEL ist NICHT gesetzt -- dann gibt es keine Stuetze in "
              "der Szene, auf die 'auf' zeigen koennte, und jede Episode faellt auf den Marker "
              "zurueck.", flush=True)
if ZIEL_RELATION in ("richtung", "alle") and not ZIEL_ADRESSE:
    print("  [Ziel-Relation] ACT23_ZIEL_RELATION=richtung ohne ACT23_ZIEL_ADRESSE=1 -- ohne "
          "Zieladresse gibt es keinen Bezugskoerper, jede Episode legt am Marker ab.", flush=True)


# Der Lerner selbst liegt in arm_modules/hoehen_schaetzer.py -- NICHT hier.  Eine Klasse,
# die in pc_act23.py steht, wird als `__main__.HoehenSchaetzer` gepickelt; jedes andere
# Skript koennte den Zustand dann nicht mehr laden, und ein Ladefehler schiebt die ganze
# Datei nach .bak (s. _validate_loaded).  Genau dieselbe Trennung wie bei den vier
# anderen Lernern.
from pc_cvnn.arm_modules.hoehen_schaetzer import HoehenSchaetzer
from pc_cvnn.arm_modules.groessen_schaetzer import GroessenSchaetzer
from pc_cvnn.arm_modules.loslass_kopf import LoslassKopf
from pc_cvnn.arm_modules.aufgeben_kopf import AufgebenKopf
from pc_cvnn.arm_modules.griff_kopf import GriffKopf


# ABSTUFUNG STATT PRIVILEG (ACT23_EIG_ABSTUFUNG, Vorgabe 0 bis gemessen).  Trifft das
# Eigenschafts-Tripel nichts, griff bisher der PRIVILEGIERTE Rueckfall: die wahre Lage aus dem
# Simulator.  Das ist der Preis der Groessenachse -- sie traf gemessen 10,0 statt 4,7 % der
# Episoden nicht (wiki/befunde/groessenachse-spanne.md), und ein groeberes Raster senkt ihn nicht
# (wiki/befunde/spannen-raster-7mm.md).
# STATTDESSEN: die GROESSENACHSE fallen lassen und mit (Farbe, Form, beliebig) erneut suchen.  Die
# Adresse wird dadurch UNSCHAERFER, nicht unbrauchbar -- und bleibt eine Wahrnehmung.  Warum
# ausgerechnet die Groesse zuerst: sie ist die einzige Achse, die sich je Bild aendert, ohne dass
# sich das Objekt aendert (Bandgrenze, Verschmelzung, Perspektive).  Farbe und Form sind
# Klassenzuweisungen und fallen als Ganzes aus, wenn sie falsch sind.
# ZWEI FASSUNGEN, weil der Handel nicht offensichtlich ist: ohne die Groesse koennen MEHRERE
# Detektionen passen, und dann adressiert die Abstufung womoeglich den falschen Koerper.  Ein
# unprivilegierter Fehlgriff ist nicht in jedem Fall besser als ein privilegierter Treffer.
#   1 = fallen lassen, besten Treffer nehmen (groesste Flaeche -- wie finde_nach_eigenschaften)
#   2 = fallen lassen, aber NUR uebernehmen, wenn genau EINER uebrig bleibt (sonst wie bisher)
# GEMESSEN und auf 0 belassen (wiki/befunde/abstufung-statt-privileg.md): 1 und 2 sind BITGLEICH --
# die Sicherung greift nie, weil der mehrdeutige Fall "1 Treffer" meldet (die anderen Wuerfel kamen
# gar nicht erst als eigene Detektion an).  Eindeutigkeit ist nicht Richtigkeit, zum dritten Mal.
# Beim SCHREIBEN einer Adresse loest EIG_IDENT das; beim LESEN nicht -- die Identitaetspruefung
# vergleicht gegen die wahre Lage und waere hier genau das Privileg, das entfallen soll.
# Ausserdem klein: nur 11 der 15 Rueckfaelle tragen ueberhaupt ein Band, Rueckfall faellt 15 -> 11
# (p = 0,54), und einer von drei Faellen adressierte einen fremden Wuerfel 65 mm daneben.
# Der Schalter bleibt fuer den Tag, an dem die Verschmelzung geloest ist
# (wiki/befunde/adressfehler-sind-verschmelzung.md).
EIG_ABSTUFUNG = int(os.environ.get("ACT23_EIG_ABSTUFUNG", "0"))
# FORM-SPLIT AUF DEM EIGENSCHAFTS-PFAD (ACT23_EIG_SPLIT, Vorgabe 0 bis gemessen).
# GRUND (gemessen, wiki/befunde/adressfehler-sind-verschmelzung.md): 26 von 26 groben
# Adressierungsfehlern liegen im obersten Groessenband, 0 von 266 in allen anderen zusammen.
# Das oberste Band ist faktisch das Band der VERSCHMOLZENEN Blobs -- der groesste einzelne
# Koerper, obj_U, misst 37,4 mm.  Die Adressierung hat also kein Groessen-, sondern ein
# Verschmelzungsproblem.
# Die Rettung dafuer EXISTIERT schon, aber nur auf dem FORM-Pfad (FORM_SPLIT, s. perceive/shape):
# perceive_colour trennt die Belegung auf PIXEL-Ebene nach Farbklasse und klassifiziert die Form
# auf dem farbreinen Teil.  Der Eigenschafts-Pfad ist juenger und hat sie nie bekommen.
#
# WARUM DER AUSLOESER EIN ANDERER SEIN MUSS: auf dem Form-Pfad meldet select() bei Verschmelzung
# None -- der Split springt bei MISSERFOLG ein.  Auf dem Eigenschafts-Pfad gibt es keinen
# Misserfolg: der verschmolzene Blob hat eine Farbe, eine (auf Verschmelzung geborene) Formklasse
# und ein Band, die Adresse "gelingt" also und liegt 20-30 mm daneben.  Es braucht ein Indiz.
#
# DAS INDIZ, MASSSTABSRELATIV STATT MIT FESTER SCHRANKE: liegt das farbreine Material weiter vom
# Schwerpunkt des Blobs entfernt, als das Teil selbst gross ist, dann IST der Blob nicht dieses
# Objekt -- er enthaelt es nur.  Gemessen ueber 480 Lagen: der Quotient liegt bei getrennten Blobs
# im Median bei 0,30, bei verschmolzenen bei 1,12.
#
# WORAUF ES ANKOMMT, und es war nicht vorhergesehen: auf WELCHER Farbklasse getrennt wird.
# Die Farbachse des TRIPELS hat die Wuerfelei aus der Verschmelzung geschrieben -- sie ist die
# Mischchroma-Klasse, und ein Split darauf holt das falsche Material heraus (Median 33,2 mm, ueber
# 20 mm in 98,4 % der Faelle -- schlechter als gar nichts zu tun).  Gebraucht wird die GEBUNDENE
# Klasse aus colour_of_body, die verschmolzene Blobs bei der Bindung ueberspringt: damit 6,7 mm und
# 1,4 %.  Genau diese Quelle nutzt auch der Form-Pfad.  Siehe wiki/befunde/eig-split-farbquelle.md.
#   1 = nur bei Verschmelzungs-Indiz trennen (Quotient, s. oben)
#   2 = IMMER trennen, sobald der Koerper eine gebundene Farbklasse hat
# Gemessen ueber 480 Lagen (wiki/befunde/eig-split-farbquelle.md): immer zu trennen ist
# in Median UND Ausreisser besser als der heutige Pfad (8,5 -> 5,8 mm, ueber 20 mm
# 11,9 -> 1,5 %).  Fassung 1 bleibt, weil der Pruefstand die Lagenverteilung des Laufs
# nicht trifft -- er ueberwiegt nahe Nachbarn.  Welche Fassung traegt, entscheidet das A/B.
# GEMESSEN und auf 0 belassen (wiki/befunde/eig-split-im-lauf.md): beide Fassungen sind im Lauf
# SCHLECHTER (grobe Adressierungsfehler 3,1 -> 9,9 bzw. 8,7 %).  Fassung 1 hat einen
# Konstruktionsfehler: das Indiz prueft einen ABSTAND, und weit weg liegt das farbreine
# Material aus zwei Gruenden -- Verschmelzung ODER ein falsch gewaehltes Objekt derselben
# Farbklasse.  Das falsche Objekt liegt WEITER weg (215 gegen 20-30 mm), der Schwellwert siebt
# also bevorzugt die Verwechslungen heraus.  Alle fuenf Splits erzeugten einen groben Fehler,
# jeweils genau so gross wie die Verschiebung des Splits.
# Fassung 2 ist gutartig, kostet aber Feinheit (Median 5,8 statt 1,4 mm) und greift nicht, wo
# sie gebraucht wird: sie braucht colour_of_body, und _farbbindung_neu ueberspringt
# verschmolzene Blobs per Bauart -- die Rettung fehlt genau in den Episoden, fuer die sie
# gebaut wurde.  Ein naechster Anlauf braucht einen Ausloeser ueber die FLAECHE statt den
# Abstand, oder eine Farbbindung, die aus der letzten sauberen Episode nachgehalten wird.
EIG_SPLIT = int(os.environ.get("ACT23_EIG_SPLIT", "0"))
# Schnitt fuer Fassung 1.  Gemessen: 0,8 faengt 72 % der Verschmelzungen bei 10 %
# Fehlalarm auf getrennten Blobs -- und ein Fehlalarm ist billig, weil der Split auch
# dort nicht schadet.  Keine absolute Laenge, damit der Schnitt nicht an die heutigen
# sieben Koerper gebunden ist.
EIG_SPLIT_FAKTOR = float(os.environ.get("ACT23_EIG_SPLIT_FAKTOR", "0.8"))
# FARBBINDUNG AUCH FUER VERSCHMOLZENE KOERPER (ACT23_BINDUNG_SPLIT, Vorgabe 0 bis gemessen).
# GRUND (gemessen, wiki/befunde/eig-split-im-lauf.md): _farbbindung_neu ueberspringt Blobs ueber
# area_hi, weil deren Mittel-Chroma eine Mischung ist.  Damit fehlt colour_of_body genau in den
# Episoden mit Verschmelzung -- und das sind die Episoden, in denen die darauf aufbauenden
# Rettungswege (Form-Split, Eig-Split, ckey-Tracker) gebraucht wuerden.  Eine Catch-22: die
# Rettung ist per Bauart dort nicht verfuegbar, wo sie gebaut wurde.  Gemessen kostete das im
# Immer-Split-Arm 30,3 % grobe Adressierungsfehler auf den ungesplitteten Adressen gegen 3,1 %
# auf den gesplitteten.
#
# NICHT GEBAUT: die Bindung aus der letzten sauberen Episode nachhalten.  Das war der erste
# Vorschlag und es kann unter FARB_MISCHUNG nicht funktionieren -- _faerbe_neu permutiert JEDE
# Episode alle sieben Farben, eine uebernommene Klasse ist also nicht bloss veraltet, sondern
# systematisch falsch.  Es waere ausserdem wieder die Tabelle, die _farbbindung_neu bewusst
# abgeloest hat.
#
# STATTDESSEN, aus derselben Wahrnehmung derselben Episode: die Mischung loest sich PIXELWEISE
# auf.  Jedes Pixel gehoert zu genau einer Farbklasse, auch wenn die Komponente zwei Koerper
# enthaelt.  colour_parts_all trennt alle Klassen in EINEM Rendern; der Zuordnungsschritt bleibt
# unveraendert (Teil -> naechster Koerper, Schranke 40 mm, eine Klasse je Koerper).
# Der Komponenten-Durchgang laeuft ZUERST und behaelt das letzte Wort: wo die Chroma sauber ist,
# ist das Komponentenmittel genauer als der Pixelschnitt (gemessen 0,8 gegen 5,5 mm).
# GEMESSEN und auf 0 belassen (wiki/befunde/farbbindung-pixelweise.md): der Durchgang bindet
# JEDEN erreichbaren Koerper, den der erste auslaesst (34 von 34 und 53 von 53) -- und die
# Zielgroesse bewegt sich nicht (grobe Adressierungsfehler 3,1 -> 3,8 %, p = 1,00).  Der
# Eig-Split wird dadurch AUCH NICHT brauchbar (6,1 %): die fehlende Bindung war beschrieben,
# aber nicht der Engpass.  Der Schalter bleibt, weil er die einzige Fassung ist, die
# verschmolzene Koerper ueberhaupt bindet.
# ACHTUNG BEIM LESEN DER MELDUNG: `len(_offen)` zaehlt die drei je Episode GEPARKTEN Koerper
# mit, die ausserhalb des Bildes liegen und nie bindbar sind -- "34 von 127" heisst 34 von 34.
BINDUNG_SPLIT = os.environ.get("ACT23_BINDUNG_SPLIT", "0") == "1"
# LATENTE AUGMENTIERUNG (ACT23_AUGMENT = Anzahl vorgestellter Lagen je Episode, 0 = aus).
# Begruendung und Bauregeln stehen bei `augmentiere` weiter unten.
AUGMENT = int(os.environ.get("ACT23_AUGMENT", "0"))
# Deckel fuer |delta|.  Gemessen traegt die Aequivarianz frei stehend bis 40 mm, aber bei
# 20 mm liegt die Formdrift noch bei ~19 % der Klassentrennung und der Lagerest unter
# 0,5 mm -- darueber steigt beides spuerbar, ohne dass mehr Vielfalt entstuende.
AUGMENT_MAX = float(os.environ.get("ACT23_AUGMENT_MAX", "0.020"))
# Verschmelzungsschwelle: naeher als das an einen Nachbarn darf die Vorstellung nicht
# fuehren (wiki/befunde/verschmelzung-abstandskurve.md, bestaetigt in der Daempfungsmessung).
AUGMENT_FREI = float(os.environ.get("ACT23_AUGMENT_FREI", "0.040"))
# HARTE VORAUSSETZUNG: ACT23_NEIGHBOURS=1.  Die Zulaessigkeitsschranke liest den
# Nachbarabstand aus dem NB-Block des Merkmalsvektors; steht NEIGHBOURS auf 0 (Vorgabe), ist
# der Block auf JEDER Zeile ungueltig und es wird nie augmentiert -- gemessen 11640 von
# 12330 Pufferzeilen ohne gueltigen Block (wiki/befunde/merkmale-kommen-zu-spaet.md).
# NICHT still mitgeschaltet: ein Schalter, der einen zweiten heimlich umlegt, macht jedes
# A/B mehrdeutig.  Stattdessen eine laute Meldung -- ein Schalter, der unbemerkt nichts tut,
# hat dieses Projekt schon zweimal einen Lauf gekostet (wiki/mechanismen/invarianten.md).
if AUGMENT and not NEIGHBOURS:
    print("  [Augment] ACT23_AUGMENT ist gesetzt, ACT23_NEIGHBOURS aber NICHT -- die "
          "Augmentierung braucht den Nachbarabstand und bleibt WIRKUNGSLOS. "
          "Beide Arme eines A/B mit ACT23_NEIGHBOURS=1 fahren.", flush=True)
# RASTERWEITE (ACT23_SPANNE_RASTER, Vorgabe 5.0 mm).  Feinere Baender trennen schaerfer, lassen
# aber haeufiger GAR KEINE Adresse passen -- und dann greift der privilegierte Rueckfall.
# Gemessen im siebten Anlauf: mit 5 mm verdoppelt sich der Rueckfall von 4,7 auf 10,0 % der
# Episoden (wiki/befunde/groessenachse-spanne.md).  Der Raster ist deshalb einstellbar.
# 7 mm GEMESSEN und verworfen (wiki/befunde/spannen-raster-7mm.md): die Trennkraft bleibt wie
# vorab gerechnet (grobe Adressierungsfehler 2,6 gegen 3,1 %), aber der Rueckfall steigt auf 20
# statt 15.  Ursache ist NICHT die Weite, sondern die Bandzahl: das gleichmaessige Raster haengt
# ein siebtes Band "gewaltig" an (ab 52,5 mm).  So gross wird kein einzelner Koerper -- obj_U, der
# groesste, misst 37,4 mm --, dort landet also nur ein VERSCHMOLZENER Blob.  Einmal ins Tripel
# geschrieben, passt "gewaltig" im naechsten Bild nie wieder; 6 der 20 Rueckfaelle gehen darauf
# zurueck.  Das offene oberste Band der gemessenen Liste ("riesig" ab 36,0, ohne Obergrenze) ist
# deshalb keine Nachlaessigkeit -- es haelt den Ausreisser im adressierbaren Bereich.
# Vorgabe 0 = die im siebten Anlauf GEMESSENE Liste unveraendert lassen.  Sie ist leicht
# ungleichmaessig (22,5-26,5 sind 4 mm, 31,5-36,0 sind 4,5), und genau so wurde sie gemessen --
# ein "aufgeraeumtes" 5-mm-Raster waere ein ANDERER Stand und truege die Messung nicht mehr.
SPANNE_RASTER = float(os.environ.get("ACT23_SPANNE_RASTER", "0"))
SPANNE_START = float(os.environ.get("ACT23_SPANNE_START", "17.5"))


def _spannen_baender(weite=None, start=None):
    """Gleichmaessiges Raster ab `start`, Schrittweite `weite` -- bewusst NICHT koerpergenau:
    Grenzen auf die sieben heutigen Koerper gelegt waeren auf sie ueberfittet und truegen
    nichts fuer eine achte Form."""
    w = float(weite if weite is not None else SPANNE_RASTER)
    s0 = float(start if start is not None else SPANNE_START)
    nm = ["winzig", "klein", "mittelklein", "mittel", "gross", "riesig", "gewaltig"]
    out = [(nm[0], 0.0, s0)]
    for i in range(1, len(nm) - 1):
        out.append((nm[i], s0 + (i - 1) * w, s0 + i * w))
    out.append((nm[-1], s0 + (len(nm) - 2) * w, 999.0))
    return out


SPANNEN_BAENDER = (_spannen_baender() if SPANNE_RASTER > 0 else
                   # die gemessene Liste (wiki/befunde/groessenachse-spanne.md)
                   [("winzig", 0.0, 17.5), ("klein", 17.5, 22.5), ("mittelklein", 22.5, 26.5),
                    ("mittel", 26.5, 31.5), ("gross", 31.5, 36.0), ("riesig", 36.0, 999.0)])


def groessen_band(dicke, span=None):
    """Groessenband einer Detektion -> Bandname, oder None ohne Messwert.

    Zwei Achsen, s. GROESSE_SPANNE oben:
      Vorgabe             Materialdicke (px_scale-normiert, Bezug 240), Grenzen GROESSEN_BAENDER
      GROESSE_SPANNE=1    Ausdehnung in mm (Feld "span" aus perceive_all), Grenzen SPANNEN_BAENDER
    `span` kommt in METERN (so liefert es perceive_all) und wird hier auf mm gebracht."""
    if GROESSE_SPANNE:
        if span is None:
            return None
        _mm = 1000.0 * float(span)
        for nm, lo, hi in SPANNEN_BAENDER:
            if lo <= _mm < hi:
                return nm
        return None
    if dicke is None:
        return None
    for nm, lo, hi in GROESSEN_BAENDER:
        if lo <= float(dicke) < hi:
            return nm
    return None


_EIG_BEZUG = {"wert": None}          # Bezugsabstand im Einbettungsraum, einmal je Lauf gemessen


def eig_bezug(shape_clf):
    """Typischer Abstand ZWEIER KLASSEN im desc_embed-Raum -- der Massstab der Formtoleranz.

    Gemessen aus dem, was der Agent selbst gelernt hat: die Exemplarwolken seiner offenen Klassen
    (`shape_clf.open`), je Klasse gemittelt, dann der Median ueber alle Paare.  Keine privilegierte
    Information, kein zusaetzliches Rendern - und er wandert mit, wenn sich der Deskriptor durch
    Weiterlernen verschiebt.

    RUECKFALL 1,86, falls weniger als zwei offene Klassen existieren (frischer Zustand): das ist
    der auf ad9d768c gemessene Median-Abstand zweier verschiedener KOERPER
    (wiki/befunde/stetige-adressierung-erster-schritt.md).  Eine nackte Zahl, aber nur als
    Notnagel - sobald zwei Klassen leben, zaehlt das Gemessene.

    DER RUECKFALL WIRD NICHT GEMERKT, und das war zuerst falsch gebaut.  Der Cache stand vor der
    Fallunterscheidung, also fror der ERSTE Aufruf den Wert ein - im frischen Lauf passiert der,
    WAEHREND noch keine zwei Klassenwolken existieren, und dann galt 1,86 fuer den ganzen Lauf.
    Gemessen im ersten frischen Arm: nach 46 Episoden lag das echte Bezugsmass bei 2,257, benutzt
    wurde weiter 1,86 - die Formtoleranz war damit dauerhaft 21 % zu eng, genau in der einzigen
    Konfiguration, in der die Direkt-Adressierung ueberhaupt arbeitet.  Der Satz "sobald zwei
    Klassen leben, zaehlt das Gemessene" stand schon hier; der Code hielt ihn nicht ein."""
    if _EIG_BEZUG["wert"] is not None:
        return _EIG_BEZUG["wert"]
    mittel = []
    for nm in getattr(shape_clf, "open_names", []):
        ex = (getattr(shape_clf, "open", {}) or {}).get(nm) or []
        if not ex:
            continue
        E = np.asarray(ex, float)
        mittel.append(E.reshape(len(E), len(shape_clf.RW), shape_clf.NH).mean(1).mean(0))
    if len(mittel) >= 2:
        d = [float(np.linalg.norm(mittel[i] - mittel[j]))
             for i in range(len(mittel)) for j in range(i + 1, len(mittel))]
        _EIG_BEZUG["wert"] = float(np.median(d)) or 1.86
        return _EIG_BEZUG["wert"]
    return 1.86              # NICHT merken -- s. oben: der Notnagel darf den Lauf nicht praegen


def _eig_abstand(det, namen, emb, span, shape_clf):
    """Abstand einer Detektion zu (einem oder mehreren) Messwerten, je genannter Achse auf ihre
    Toleranz normiert und summiert.  None, wenn keine genannte Achse vergleichbar ist."""
    _s, _n = 0.0, 0
    if namen[1] is not None and emb is not None and det.get("desc") is not None:
        _e = np.asarray(shape_clf.desc_embed(det["desc"]), float)
        _s += float(np.min(np.linalg.norm(np.atleast_2d(np.asarray(emb, float)) - _e, axis=1))) / (
            EIG_TOL_FORM * eig_bezug(shape_clf)); _n += 1
    if namen[2] is not None and span is not None and det.get("span") is not None:
        _s += float(np.min(np.abs(np.atleast_1d(np.asarray(span, float)) - float(det["span"]))))             / EIG_TOL_SPAN; _n += 1
    return _s if _n else None


def _eig_passt(det, namen, mess, shape_clf):
    """Passt eine Detektion auf eine STETIGE Adresse?  Eine Achse ohne Namen ist 'beliebig'.

    `namen` sagt, welche Achsen genannt sind (die Wuerfelei entscheidet das wie bisher), `mess`
    traegt die Werte: (Chromatizitaet, Formeinbettung, Spanne in Metern)."""
    from pc_cvnn.arm_modules.colour_openset import TH as _CTH
    if namen[0] is not None and mess[0] is not None:
        if det.get("chroma") is None:
            return False
        if float(np.linalg.norm(np.asarray(det["chroma"], float)
                                - np.asarray(mess[0], float))) > _CTH:
            return False
    if namen[1] is not None and mess[1] is not None:
        if det.get("desc") is None:
            return False
        _e = np.asarray(shape_clf.desc_embed(det["desc"]), float)
        # mess[1] darf mehrere Beispiele tragen (Zeilen, s. EIG_NACHFUEHREN): das naechste zaehlt
        if float(np.min(np.linalg.norm(np.atleast_2d(np.asarray(mess[1], float)) - _e, axis=1))) >                 EIG_TOL_FORM * eig_bezug(shape_clf):
            return False
    if namen[2] is not None and mess[2] is not None:
        if det.get("span") is None:
            return False
        if float(np.min(np.abs(np.atleast_1d(np.asarray(mess[2], float)) - float(det["span"]))))                 > EIG_TOL_SPAN:
            return False
    if len(mess) > 3 and mess[3]:
        # GEGENBEISPIELE (s. EIG_GEGEN): naeher an einem bekannten ANDEREN Ding als am eigenen
        # Messwert -> kein Treffer, auch wenn die Toleranz passt.
        _dp = _eig_abstand(det, namen, mess[1], mess[2], shape_clf)
        if _dp is not None:
            for _ge, _gs in mess[3]:
                _dn = _eig_abstand(det, namen, _ge, _gs, shape_clf)
                if _dn is not None and _dn < _dp:
                    return False
    return True


def finde_nach_eigenschaften(sim, shape_clf, colours, farbe=None, form=None, groesse=None,
                             min_area=200.0, mess=None):
    """Sucht die Detektion, die auf das Tripel passt.  Jede Angabe darf None sein = 'beliebig'.

    Gibt (pos, det, treffer) zurueck: die Weltposition, die Detektion und ALLE passenden
    Detektionen (damit der Aufrufer Mehrdeutigkeit erkennen kann, statt sie zu verschlucken).
    Ohne Treffer (None, None, []).  KEINE privilegierte Information -- nur was die Kamera liefert.
    """
    treffer = []
    for det in shape_clf.perceive_all(sim):
        if det.get("pos") is None or float(det.get("area", 0.0)) < min_area:
            continue
        if mess is not None:
            # STETIG: die Namen sagen nur, WELCHE Achsen genannt sind; verglichen wird das
            # Gemessene.  Die Farbschwelle ist NICHT geraten, sondern die schon kalibrierte des
            # Farb-Offenmengen-Moduls -- dieselbe Zahl, die entscheidet, ob zwei Chromatizitaeten
            # dieselbe Klasse waeren.
            if not _eig_passt(det, (farbe, form, groesse), mess, shape_clf):
                continue
            treffer.append(det)
            continue
        f = None
        if colours is not None and det.get("chroma") is not None:
            f = colours.classify(det["chroma"])[0]
        g = groessen_band(det.get("dicke"), det.get("span"))
        if farbe is not None and f != farbe:
            continue
        if form is not None and str(det.get("shape")) != str(form):
            continue
        if groesse is not None and g != groesse:
            continue
        treffer.append(det)
    if not treffer:
        return None, None, []
    if EIG_DAUERHAFT and mess is not None and len(treffer) > 1:
        # DER NAECHSTE ZUM MESSWERT, nicht der groesste (s. EIG_DAUERHAFT, Teil 2).  Abstand je
        # genannter Achse auf ihre eigene Toleranz normiert, damit Form und Groesse vergleichbar
        # zaehlen.
        def _abst(det):
            _a = _eig_abstand(det, (farbe, form, groesse), mess[1], mess[2], shape_clf)
            return 0.0 if _a is None else _a
        best = min(treffer, key=_abst)
    else:
        best = max(treffer, key=lambda d: float(d.get("area", 0.0)))
    return np.asarray(best["pos"], float), best, treffer


def augmentiere(fe, nh, anzahl, rng, max_delta=None, frei=None):
    """LATENTE AUGMENTIERUNG: aus EINER Erfahrung mehrere vorgestellte Lagen.

    Nutzeridee (wiki/fragen/latente-augmentierung.md): *"Wenn der Greifer ein Objekt erfolgreich
    gegriffen hat, koennen wir gleich zig Szenen fuer leicht verschobene Objekte erzeugen."*
    Gebaut wird sie nach der GEMESSENEN Daempfungsfunktion
    (wiki/befunde/daempfungsfunktion.md), nicht nach der urspruenglichen Annahme:

      * KEINE Daempfung nach dem Betrag.  Frei stehend ist die Aequivarianz bis 40 mm auf unter
        1 % genau -- ein Gewicht, das mit |delta| faellt, wuerde das Falsche daempfen.
      * Die Schranke ist der NACHBARABSTAND: eine Verschiebung traegt genau so lange, wie sie den
        Koerper nicht in Verschmelzungsnaehe bringt.  Gemessen bricht dort nicht der Median,
        sondern der Schwanz (p90 bis 17 mm) -- also eine Minderheit VOLLSTAENDIG falscher
        Vorstellungen, und die sind schlimmer als viele leicht schiefe.
      * NUR VERSCHIEBUNG.  Die Drehung ist gemessen teurer (20 Grad kosten so viel Formdrift wie
        40 mm Verschiebung), sie bewegt den Schwerpunkt, und nur einer ihrer beiden Winkelkanaele
        traegt sie -- mit umgekehrtem Vorzeichen.  Das ist ein eigener Bau.

    WORAUF SICH DIE SCHRANKE STUETZT: der Nachbarabstand steht bereits IM Merkmalsvektor
    (NB-Block `[gueltig, d_nah, cos phi, sin phi, n_nah]`, ab 6+NH).  Es braucht also keine
    zusaetzliche Wahrnehmung und keine privilegierte Information -- die Regel liest, was der Agent
    ohnehin gesehen hat.  Ohne gueltigen NB-Block wird NICHT augmentiert: eine Vorstellung ohne
    Kenntnis der Nachbarschaft ist genau der Fall, den die Messung als gefaehrlich ausweist.

    WARUM DER NEUE ABSTAND KONSERVATIV GESETZT WIRD: die Richtung phi steht nur im Objektrahmen und
    der yaw nur mod pi -- die Weltrichtung zum Nachbarn ist also um pi mehrdeutig.  Statt zu raten
    wird der schlimmste Fall angenommen (die Verschiebung ging genau auf den Nachbarn zu):
    d_nah_neu = d_nah - |delta|.  Das ist eine untere Schranke, und mit ihr gilt die
    Zulaessigkeitsbedingung garantiert.

    WAS SICH AENDERT und was nicht:
        pos        + delta          (die einzige Groesse, die sich aendert)
        Winkel     unveraendert     (Verschiebung dreht nicht)
        desc_embed unveraendert     (verschiebungsinvariant; gemessen auf 13 % genau, nicht exakt)
        NB.d_nah   konservativ verringert, uebriger Block unveraendert
        FOV, BD    unveraendert     -- Blickpfad und Armstellung gehoeren zur AUSFUEHRUNG, nicht
                   zur vorgestellten Objektlage; sie zu faelschen waere eine Erfindung.

    Die AKTION bleibt unveraendert, und das ist kein Versehen: `action_vec` traegt den Greifpunkt
    als OFFSET gegen den wahrgenommenen Bezug, nicht als Weltkoordinate -- unter einer Verschiebung
    ist sie damit invariant.

    Gibt eine Liste von Merkmalsvektoren zurueck (kann leer sein)."""
    _mx = AUGMENT_MAX if max_delta is None else float(max_delta)
    _fr = AUGMENT_FREI if frei is None else float(frei)
    nb0 = 6 + int(nh)
    fe = np.asarray(fe, float)
    if len(fe) < nb0 + 5 or fe[nb0] < 0.5:
        return []                                    # kein gueltiger Nachbar-Block -> nicht raten
    spielraum = min(_mx, float(fe[nb0 + 1]) - _fr)
    if spielraum <= 0.002:                           # unter 2 mm lohnt keine Vorstellung
        return []
    aus = []
    for _ in range(int(anzahl)):
        r = float(rng.uniform(0.002, spielraum))
        w = float(rng.uniform(0, 2 * np.pi))
        g = fe.copy()
        g[0] += r * np.cos(w)
        g[1] += r * np.sin(w)
        g[nb0 + 1] = max(_fr, float(fe[nb0 + 1]) - r)   # schlimmster Fall, s. oben
        aus.append(g)
    return aus


def eig_split_teil(sim, shape_clf, colours, ckey, form, groesse, det_blob):
    """Verschmolzenen Blob auf dem EIGENSCHAFTS-Pfad trennen -- dieselbe Rettung, die der
    FORM-Pfad seit dem Form-Split hat (s. EIG_SPLIT oben).

    `ckey` ist die GEBUNDENE Farbklasse des Koerpers (colour_of_body), NICHT die Farbachse des
    Tripels.  Das ist der Kern des Einbaus und gemessen der Unterschied zwischen Rettung und
    Verschlimmerung (wiki/befunde/eig-split-farbquelle.md):

        verschmolzener Blob, nichts tun     Median 18,2 mm   ueber 20 mm  38,5 %
        Split auf der TRIPEL-Farbe          Median 33,2 mm   ueber 20 mm  98,4 %
        Split auf der GEBUNDENEN Farbe      Median  6,7 mm   ueber 20 mm   1,4 %

    Der Grund: die Farbachse des Tripels wurde von der Wuerfelei AUS DER VERSCHMELZUNG
    geschrieben -- sie ist die Mischchroma-Klasse und trennt genau das falsche Material heraus.
    colour_of_body dagegen ueberspringt verschmolzene Blobs bei der Bindung (s. _farbbindung_neu:
    `area > area_hi` -> nicht binden), ist also per Bauart eine saubere Zuordnung.  Sie ist
    buchhalterisch koerper-indiziert wie SHAPE_KEY und EIGENSCHAFT, nicht privilegiert: die Klasse
    kommt aus der gerenderten Chroma.

    Gibt die Detektion des farbreinen TEILS zurueck, sonst None.  KEINE privilegierte Information.
    """
    if ckey is None or det_blob is None:
        return None
    teile = shape_clf.perceive_colour(sim, colours, ckey, with_form=True)
    if not teile:
        return None
    # GESTUFT filtern: erst das ganze Tripel, dann ohne Groesse, dann nur die Farbe.  Form- und
    # Groessenachse des Tripels stammen vom VERSCHMOLZENEN Blob und treffen auf dem getrennten
    # Teil oft nicht mehr zu -- dann ist die Lage das, was gebraucht wird, nicht die Klasse.
    for _f, _g in ((form, groesse), (form, None), (None, None)):
        _k = [d for d in teile
              if (_f is None or str(d.get("shape")) == str(_f))
              and (_g is None or groessen_band(d.get("dicke"), d.get("span")) == _g)]
        if _k:
            break
    if not _k:
        return None
    best = max(_k, key=lambda d: float(d.get("area", 0.0)))
    if EIG_SPLIT >= 2:
        return best                                    # Fassung 2: immer trennen, kein Indiz
    _sp = float(best.get("span") or 0.0)
    if _sp <= 0.0:
        return None
    _d = float(np.linalg.norm(np.asarray(best["pos"], float)
                              - np.asarray(det_blob["pos"], float)))
    return best if _d > EIG_SPLIT_FAKTOR * _sp else None


# NUR ANZEIGE (s. CommandState23.farbname): die Palette, die FARB_MISCHUNG permutiert, und
# farbneutrale Koerpernamen fuer den Beobachter.
FARB_NAMEN = [((0.9, 0.1, 0.1), "rot"), ((0.1, 0.85, 0.1), "grün"), ((0.15, 0.3, 0.95), "blau"),
              ((0.95, 0.55, 0.1), "orange"), ((0.1, 0.8, 0.85), "türkis"), ((0.45, 0.12, 0.9), "violett"),
              ((0.65, 0.95, 0.15), "gelbgrün"), ((0.05, 0.05, 1.0), "tiefblau")]
# PLATTENFARBEN fuer die GUI (Nutzerwunsch 2026-10-01: die Platte umfaerben).  Alle GESAETTIGT --
# eine graue Platte faellt durch die Saettigungsmaske der Wahrnehmung (SAT_TH=0,15) und waere fuer
# den Agenten unsichtbar, also kein Stapelziel mehr.  Die Zahl ist der Mindestabstand in der
# normierten Chroma zu den sieben Objektfarben (Rechnung auf der RGBA; was zaehlt, ist die
# GERENDERTE Chroma, s. obj_Y).  Unter 0,12 (= colour_openset.TH) teilt die Platte die Farbklasse
# eines Objekts -- das ist erlaubt, aber dann ein anderes Experiment.
PLATTEN_FARBEN = [((0.05, 0.05, 1.0), "tiefblau"), ((0.3, 1.0, 0.6), "mint"),
                  ((1.0, 0.5, 0.4), "lachs"), ((0.5, 0.5, 0.0), "oliv"),
                  ((0.3, 0.65, 1.0), "himmelblau")]
# GELB (1,0.85,0) STAND HIER UND FLOG RAUS: auf der RGBA 0,14 von Orange entfernt, GERENDERT aber
# von der orangen L-Form kaum zu unterscheiden (GUI-Probe 2026-10-01, Bild nebeneinander).
FARB_NAMEN = FARB_NAMEN + [f for f in PLATTEN_FARBEN if f not in FARB_NAMEN]
KOERPER_NAME = {"obj_red": "Würfel A", "obj_green": "Würfel B", "obj_blue": "Balken", "obj_L": "L-Form",
                "obj_U": "U-Form", "obj_T": "T-Form", "obj_X": "Kreuz", "obj_Zyl": "Zylinder",
                "obj_V": "V-Form", "obj_Stern": "Stern", "sockel": "Platte 70",
                "sockel2": "Platte 50", "sockel3": "Platte 60"}


# EIN MARKER STATT VIER (ACT23_EIN_MARKER, Vorgabe 1; Nutzerbefund 2026-10-01).  Bisher lagen
# immer alle drei waehlbaren Zielscheiben target_sel_1..3 halbtransparent auf dem Tisch und dazu
# die helle aktive Scheibe target_marker -- drei magentafarbene Flecken, von denen einer gilt.
# Jetzt ist nur die AKTIVE sichtbar; die drei waehlbaren liegen unter dem Tisch und behalten ihre
# xy als Ortsgedaechtnis.  Bei Koerper-Ziel ist vor dem Start gar keine sichtbar.
# FUER DIE WAHRNEHMUNG AENDERT SICH WENIG: perceive_all/select parken die Marker ohnehin vor
# jedem Blick (_park_markers).  Sichtbar bleiben sie dort, wo nicht geparkt wird -- im
# Kamerabild der GUI und in der Fovea-Anzeige.  ACT23_EIN_MARKER=0 stellt das alte Bild her.
# GEMESSEN (wiki/befunde/ein-marker-ab.md, 8 Seeds x 50): KEIN Effekt auf die Quote (vier
# sichtbar 58,2 %, einer 55,8 %, Seeds 5:3, p = 0,73).  Vorgabe bleibt 1 -- der Lesbarkeit wegen.
EIN_MARKER = os.environ.get("ACT23_EIN_MARKER", "1") == "1"
MARKER_UNTER = -0.05                       # dieselbe Tiefe wie _park_markers


class CommandState23:
    """Unified command state for the act23 GUI.  ONE coherent object list (no colour/form mode), plus a
    grasp-policy toggle (teacher WRIST_ALIGN <-> SELF-learned world-model wrist).  Exposes the cmd/force/goal
    hooks run_combined consumes."""

    # one button per CONCRETE object; field 3 = how the net LOCALISES it (colour via vc / form via shape_clf /
    # long = the elongated obj_blue, localised by colour, wrist by the self-learned world model)
    # FARBNEUTRALE NAMEN (2026-09-30).  Bis dahin hiessen die Wuerfel "Rotes/Gruenes Wuerfel" --
    # seit FARB_MISCHUNG (Vorgabe 1) die Farben je Szene permutiert, log der Name: "[Auto 83]
    # Gruenes Wuerfel" war ein blauer Wuerfel (Nutzerbefund).  Die AKTUELLE Farbe zeigt anzeige().
    OBJECTS = [("Würfel A", "obj_red", "color"), ("Würfel B", "obj_green", "color"),
               ("L-Form", "obj_L", "shape"), ("U-Form", "obj_U", "shape"), ("Langes Objekt", "obj_blue", "long")]
    SHAPE_KEY = {"obj_L": "L", "obj_U": "U"}
    MARKERS = ["target_sel_1", "target_sel_2", "target_sel_3"]
    OBJ_COL = {"obj_red": "#d23030", "obj_green": "#2fae40", "obj_blue": "#3358d2",
               "obj_L": "#d98a2b", "obj_U": "#27b3b3", "obj_T": "#7a3fd0"}

    def __init__(self, sim):
        self.sim = sim; self.sel = 0; self.action = "grasp"; self.target_idx = 0
        if EIN_MARKER:
            self._marker_verstecken()
        self.policy = "self"          # "self" -> world-model wrist (long obj); "teacher" -> WRIST_ALIGN
        self.choreo = "fsm"           # "fsm" -> scripted choreography (collects DAgger data);
        #                               "netz" -> the LEARNED runtime policy drives the sub-goals (Stufe 2)
        self.goalmode = os.environ.get("ACT23_GOAL", "latent")   # STAGE 4a: "latent" -> the place target
        #   is a GOAL LATENT, executed by the latent-difference servo; "koord" -> classic coordinate place
        self.go = False; self.exit = False
        self.auto = False             # AUTO-Lauf: random object + random target per episode (self-training)
        self.busy = False             # an episode is RUNNING: matplotlib fires button callbacks inside the
        #   run's flush_events -- scene-mutating actions must be DEFERRED to after the episode (a mid-run
        #   "Objekt hinzufügen" grew the object list past the pose snapshot + moved objects under the claw)
        # INSTANCE copies: OPEN-SET discovery appends objects at runtime (a self-labelled class becomes a
        # commandable button) -- the class-level lists stay the pristine trained set.
        self.OBJECTS = list(CommandState23.OBJECTS)
        self.SHAPE_KEY = dict(CommandState23.SHAPE_KEY)
        self.EIGENSCHAFT = {}      # Koerper -> (Farbklasse, Formklasse, Groessenband); s. add_eigenschaft
        # DAS ABLAGEZIEL ALS ADRESSE (s. ZIEL_ADRESSE oben).  "ort" = der gewaehlte Marker wie
        # bisher, "koerper" = ein BEZUG auf einen anderen Koerper, aufgeloest aus der Wahrnehmung.
        # ziel_bezug traegt den Wurf DIESER Episode, ziel_loeser die Aufloesung (sie braucht
        # shape_clf und colours und kann deshalb nicht hier stehen).
        self.ziel_modus = "koerper" if ZIEL_ADRESSE else "ort"
        self.ziel_art = None       # GUI: None = wie ACT23_ZIEL_RELATION; "an"/"auf"/Richtungswort fest
        self.ziel_body_fix = None  # GUI: fest gewaehlter Bezugskoerper (None = wuerfeln)
        self.ziel_bezug = None
        self.ziel_loeser = None
        # STUETZEN sind MOEBEL, keine Objekte: Koerper, auf die etwas gestellt werden kann, die aber
        # nie kommandiert und nie gegriffen werden (s. SOCKEL oben).  Sie stehen deshalb NICHT in
        # OBJECTS -- sonst koennte die Neugier sie zum Greifen auswaehlen -, werden aber von der
        # Szene aufgebaut und nach jeder Episode wiederhergestellt wie jeder andere Koerper.
        self.STUETZEN = []
        self.ZIEL_SPERRE = []      # zusaetzliche Stellen, die Marker-Ziele meiden (s. SOCKEL_AUS=2)
        self.EIG_NEG = {}          # Koerper -> [(Formeinbettung, Spanne), ...] Gegenbeispiele (EIG_GEGEN)
        self.EIG_MESS_EX = {}      # Koerper -> [(Formeinbettung, Spanne), ...] nachgefuehrt (EIG_NACHFUEHREN)
        self.EIG_EINDEUTIG = {}    # Koerper -> loeste die Adresse in DIESER Episode eindeutig auf?
        self.EIG_MESS = {}         # Koerper -> (Chromatizitaet, Formeinbettung, Spanne) -- die
        #   GEMESSENEN Werte derselben drei Achsen (ACT23_EIG_STETIG).  Die Namen oben bleiben fuer
        #   Anzeige und Protokoll, gematcht wird auf diesen hier.  Wird wie EIGENSCHAFT NICHT
        #   persistiert: ein Messwert von gestern beschreibt die heutige Szene nicht.

    def add_object(self, label, body, shape_key):
        """Register a SELF-DISCOVERED object: commandable like L/U, localised by its self-labelled open
        class (`shape_key`, e.g. 'neu-1').  The body handle is GUI plumbing only -- perception (select /
        track) runs purely on the class name."""
        self.OBJECTS = self.OBJECTS + [(label, body, "shape")]
        self.SHAPE_KEY[body] = shape_key

    def add_eigenschaft(self, body, farbe=None, form=None, groesse=None):
        """Ein Objekt ueber EIGENSCHAFTEN kommandierbar machen -- ohne dass eine Formklasse
        entstanden sein muss.

        WARUM (Nutzeridee 2026-09-04): `add_object` verlangt einen `shape_key`, also eine geborene
        und bestaetigte Formklasse.  Genau daran ist in dieser Sitzung jeder Versuch gescheitert
        (vier Eingriffe am Anspruchstor, alle gemessen wirkungslos, s. [[act23-faktorisierung]]).
        Ein Objekt IST aber eine Kombination aus Farbe, Form und Groesse -- und die drei liegen je
        Detektion schon vor.  Wer so adressiert, braucht die Geburt nicht.
        Jede Angabe darf None sein = 'beliebig'.  Der Koerper dient nur der Buchfuehrung und der
        Bewertung; die LOKALISIERUNG laeuft rein ueber die Eigenschaften (s. perceive, Zweig
        'eigenschaft')."""
        self.EIGENSCHAFT[body] = (farbe, form, groesse)
        teile = [t for t in (farbe, form, groesse) if t is not None]
        label = " + ".join(str(t) for t in teile) or "beliebig"
        vorhanden = [i for i, (_l, b, m) in enumerate(self.OBJECTS) if b == body and m == "eigenschaft"]
        if vorhanden:
            self.OBJECTS[vorhanden[0]] = (label, body, "eigenschaft")
            return vorhanden[0]
        self.OBJECTS = self.OBJECTS + [(label, body, "eigenschaft")]
        return len(self.OBJECTS) - 1

    def selected(self):
        return self.OBJECTS[self.sel]

    def _mocap(self, name):
        return self.sim.m.body_mocapid[mujoco.mj_name2id(self.sim.m, mujoco.mjtObj.mjOBJ_BODY, name)]

    def marker_xy(self, idx):
        return self.sim.d.mocap_pos[self._mocap(self.MARKERS[idx])][:2].copy()

    def set_marker_xy(self, idx, xy):
        self.sim.d.mocap_pos[self._mocap(self.MARKERS[idx])][:2] = xy

    def _marker_verstecken(self):
        """Die drei waehlbaren Marker UNTER DEN TISCH (s. EIN_MARKER).  Nur z: ihre xy bleiben die
        Ortsgedaechtnisse, aus denen marker_xy liest.  Auch im MODELL (body_pos), weil
        reset_home -> mj_resetData die mocap_pos aus body_pos neu laedt."""
        for nm in self.MARKERS:
            _b = mujoco.mj_name2id(self.sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)
            self.sim.m.body_pos[_b][2] = MARKER_UNTER
            self.sim.d.mocap_pos[self.sim.m.body_mocapid[_b]][2] = MARKER_UNTER
        mujoco.mj_forward(self.sim.m, self.sim.d)

    def sync_active(self):
        _tm = self.sim.d.mocap_pos[self._mocap("target_marker")]
        _tm[:2] = self.marker_xy(self.target_idx)
        if EIN_MARKER:
            # MIT KOERPER-ZIEL zeigt die Scheibe vor dem Start NICHTS Gueltiges -- sie stuende auf
            # dem zuletzt gewaehlten Ort.  Darum unter den Tisch; run_combined holt sie beim
            # Festlegen des Ziels (set_target_marker, z=0,001) auf die aufgeloeste Stelle.
            _tm[2] = MARKER_UNTER if self.ziel_modus == "koerper" else 0.001
            for nm in self.MARKERS:                    # reset_home hat sie ggf. hochgeholt
                self.sim.d.mocap_pos[self._mocap(nm)][2] = MARKER_UNTER
        mujoco.mj_forward(self.sim.m, self.sim.d)

    def place_selected_random(self, rng):
        from pc_cvnn.pc_act14 import _rand_xy
        from pc_cvnn.pc_act16 import BASE_CLEAR
        bodies = [nm for _l, nm, _m in self.OBJECTS]
        # STUETZEN BRAUCHEN MEHR ABSTAND ALS OBJEKTE.  Ein Marker-Ziel, das auf dem Sockel landet,
        # laesst den Arm dort ABLEGEN -- in einem Arm, der gar nicht stapeln soll.  Genau dieser
        # Konfounder haette das Stapel-A/B unbrauchbar gemacht.  0,05 m ist fuer 24-mm-Koerper
        # bemessen; die 70-mm-Platte braucht ihre Halbdiagonale obendrauf.
        p = _rand_xy(rng)
        for _ in range(200):
            if (float(np.linalg.norm(p)) >= BASE_CLEAR
                    and all(float(np.linalg.norm(p - self.sim.obj_pos(o)[:2])) > 0.05 for o in bodies)
                    and all(float(np.linalg.norm(p - self.sim.obj_pos(o)[:2])) > 0.10
                            for o in self.STUETZEN)
                    and all(float(np.linalg.norm(p - np.asarray(q, float))) > 0.10
                            for q in self.ZIEL_SPERRE)):
                break
            p = _rand_xy(rng)
        self.set_marker_xy(self.target_idx, p); self.sync_active()

    # run_combined hooks
    def cmd_fn(self, ep):
        return self.selected()[1]

    def force_fn(self, cmd):
        return self.action

    def goal_fn(self, cmd, obj_xy):
        """Das Ablageziel, wie run_combined es abholt und auf das es sich festlegt.

        MIT EINER ZIELADRESSE (s. ZIEL_ADRESSE) kommt es aus der WAHRNEHMUNG statt aus
        mocap_pos.  Der Rueckfall ist NICHT still: der Aufloeser sagt im Protokoll, ob er nichts
        gefunden hat oder mehrdeutig war -- eine Zieladresse, die heimlich zum Marker wird, waere
        in der Auswertung von einer geloesten nicht zu unterscheiden."""
        if self.ziel_bezug is not None and self.ziel_loeser is not None:
            p = self.ziel_loeser(self.ziel_bezug)
            if p is not None:
                return p
        return self.marker_xy(self.target_idx)

    # ---- ANZEIGE FUER DEN MENSCHEN (Log + GUI).  Die Farbnamen kommen aus der RGBA des Koerpers,
    #      also privilegiert -- sie sind NUR Beschriftung fuer den Beobachter und gehen in keine
    #      Entscheidung ein.  Der Agent selbst kennt nur seine Farbklassen ("farbe-4").
    def farbname(self, body):
        try:
            _b = mujoco.mj_name2id(self.sim.m, mujoco.mjtObj.mjOBJ_BODY, body)
            rgb = np.asarray(self.sim.m.geom_rgba[self.sim.m.body_geomadr[_b]][:3], float)
        except Exception:
            return "?"
        return min(FARB_NAMEN, key=lambda fn: float(np.linalg.norm(rgb - np.asarray(fn[0]))))[1]

    def koerper_hinweis(self, body):
        return f"{KOERPER_NAME.get(body, body)}, {self.farbname(body)}"

    def anzeige(self, i=None):
        """Name eines Eintrags fuer Log und GUI: der Befehl, wie der Agent ihn traegt, plus in
        Klammern, welcher Koerper das gerade ist und welche Farbe er hat."""
        lbl, body, modus = self.OBJECTS[self.sel if i is None else i]
        if modus == "eigenschaft":
            return f"'{lbl}' ({self.koerper_hinweis(body)})"
        if lbl == KOERPER_NAME.get(body):
            return f"{lbl} ({self.farbname(body)})"
        return f"{lbl} ({self.koerper_hinweis(body)})"

    def ziel_hinweis(self):
        if self.ziel_modus != "koerper":
            return f"Ort: Marker {self.target_idx + 1}"
        if self.ziel_bezug is None:
            if self.ziel_body_fix is not None:
                return f"Bezug {self.koerper_hinweis(self.ziel_body_fix)}; Adresse beim Start"
            return "Bezug wird beim Start gewürfelt"
        return f"'{self.ziel_bezug['label']}' -> {self.koerper_hinweis(self.ziel_bezug['body'])}"

    def aufgabe(self):
        """EIN Satz: was wird womit wohin gebracht."""
        obj = self.anzeige()
        if self.ziel_modus != "koerper":
            wo = f"bei Marker {self.target_idx + 1}"
        elif self.ziel_bezug is None:
            _art = {None: "Relation zufällig", "an": "neben", "auf": "auf", "vor": "vor",
                    "hinter": "hinter"}.get(self.ziel_art, f"{self.ziel_art} von")
            wo = (f"{_art} {KOERPER_NAME.get(self.ziel_body_fix, self.ziel_body_fix)} "
                  f"({self.farbname(self.ziel_body_fix)})" if self.ziel_body_fix is not None
                  else f"{_art} einem Körper (wird gewürfelt)")
        else:
            _bz = self.ziel_bezug
            ref = f"{KOERPER_NAME.get(_bz['body'], _bz['body'])} ({self.farbname(_bz['body'])})"
            _r = _bz.get("relation", "an")
            _w = _bz.get("wort")
            wo = (f"auf {ref}" if _r == "auf"
                  else f"{_w if _w in ('vor', 'hinter') else str(_w) + ' von'} {ref}" if _w
                  else f"neben {ref}")
        if self.action == "push":
            return f"{obj} schieben -> {wo}"
        return f"{obj} greifen -> {'stapeln ' if 'auf ' in wo[:4] else 'ablegen '}{wo}"

    def betrieb(self):
        ch = {"netz": "Netz", "attractor": "Attraktor"}.get(self.choreo, "FSM (Teacher)")
        pol = "selbst-gelernt" if self.policy == "self" else "Teacher"
        return (f"Choreo {ch}  |  Greifer {pol}  |  Zielkodierung "
                f"{'Latent' if self.goalmode == 'latent' else 'Koordinate'}  |  Auto {'an' if self.auto else 'aus'}")

    def label(self):
        act = "Greifen" if self.action == "grasp" else "Schieben"
        pol = "Selbst-gelernt" if self.policy == "self" else "Teacher"
        ch = {"netz": "Netz", "attractor": "Attraktor"}.get(self.choreo, "FSM")
        zl = " (latent)" if self.goalmode == "latent" else ""
        if self.ziel_bezug is not None:
            # das Label traegt die Relation schon ("auf ..."), fuer "an" steht sie hier davor
            _r = self.ziel_bezug.get("relation", "an")         # "richtung": "links von ..."
            zt = (f"Ziel: {'an ' if _r == 'an' else ''}{self.ziel_bezug['label']}"
                  f" [= {self.koerper_hinweis(self.ziel_bezug['body'])}]")
        elif self.ziel_modus == "koerper":
            zt = f"Ziel: {ZIEL_RELATION} <kein Bezug>"
        else:
            zt = f"Ziel {self.target_idx + 1}"
        return f"{self.anzeige()} | {act} | Greifer: {pol} | Choreo: {ch} | {zt}{zl}"


EIG_ONLY = os.environ.get("ACT23_EIG_ONLY", "0") != "0"   # alte Objektzeile ausblenden


MARK = "● "   # Auswahlpunkt in den Klapplisten


class _Auswahl:
    """Eine KLAPPLISTE aus matplotlib-Knoepfen (Nutzerwunsch 2026-09-30: "Auswahl ueber Dropdowns
    besser als das Durchwechseln bei Druck").  matplotlib hat kein Dropdown; ein Klick oeffnet
    darueber eine Spalte mit allen Werten, ein Klick auf einen Wert setzt ihn und schliesst sie.

    optionen() -> [(schluessel, text), ...], wert() -> schluessel, setzen(schluessel).
    farbe(schluessel) -> RGB oder None faerbt die Eintraege (Farbklassen)."""

    def __init__(self, panel, rect, titel, optionen, wert, setzen, farbe=None, fontsize=7.5):
        from matplotlib.widgets import Button
        self.p, self.rect, self.titel = panel, rect, titel
        self.optionen, self.wert, self.setzen, self.farbe = optionen, wert, setzen, farbe
        self.fontsize = fontsize
        ax = panel.fig.add_axes(rect)
        self.b = Button(ax, "", color="#2b3b4a", hovercolor="#3a5060")
        self.b.label.set_fontsize(fontsize)
        self.b.on_clicked(self._klick)
        self.aktiv = True
        self._popup = []

    def _text(self):
        k = self.wert()
        for s, t in self.optionen():
            if s == k:
                return t
        return "-"

    def refresh(self):
        self.b.label.set_text(f"{self.titel}: {self._text()}  ▾" if self.aktiv else f"{self.titel}: -")
        self.b.label.set_alpha(1.0 if self.aktiv else 0.4)
        rgb = self.farbe(self.wert()) if (self.farbe is not None and self.aktiv) else None
        self._faerben(self.b, rgb, "#2b3b4a")

    @staticmethod
    def _faerben(b, rgb, grund):
        if rgb is None:
            b.color = grund; b.hovercolor = "#3a5060"; b.label.set_color("w")
        else:
            b.color = rgb; b.hovercolor = rgb
            hell = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
            b.label.set_color("#101014" if hell > 0.55 else "w")
        b.ax.set_facecolor(b.color)

    def _klick(self, _e):
        if not self.aktiv:
            return
        offen = bool(self._popup)
        self.p._popups_schliessen()
        if not offen:
            self._oeffnen()

    def _oeffnen(self):
        from matplotlib.widgets import Button
        opts = self.optionen()
        x, y, w, h = self.rect
        hh = 0.03
        pro_spalte = max(1, int((0.93 - (y + h)) / hh))    # nach oben ins Bild, bis unter den Rand
        k0 = self.wert()
        self.p._texte_zeigen(False)                        # sonst scheinen die Zeilen durch die Liste
        for j, (s, t) in enumerate(opts):
            sp, zl = divmod(j, pro_spalte)
            ax = self.p.fig.add_axes([x + sp * (w + 0.004), y + h + 0.003 + zl * hh, w, hh - 0.002])
            ax.set_zorder(50)
            b = Button(ax, (MARK if s == k0 else "") + t, color="#2a3644", hovercolor="#46607e")
            b.label.set_fontsize(max(self.fontsize, 7.5))
            b.label.set_color("w")                         # Nutzerbefund: schwarz auf dunkel unlesbar
            if self.farbe is not None:
                self._faerben(b, self.farbe(s), "#2a3644")
            b.on_clicked(lambda _e, s=s: self._waehlen(s))
            self._popup.append(b)
        self.p.fig.canvas.draw_idle()

    def _waehlen(self, s):
        self.p._popups_schliessen()
        self.setzen(s)
        self.p._refresh()

    def schliessen(self):
        for b in self._popup:
            b.disconnect_events()
            self.p.fig.delaxes(b.ax)
        self._popup = []


class CommandPanel23:
    """Die act23-Steuer-GUI: Armkamera + Fovea + Ueberraschung oben, darunter DREI GRUPPEN
    (Nutzerwunsch 2026-09-30):
      1 Objekt     WAS transportiert wird -- per Name (Klappliste) ODER per Eigenschaften
      2 Ziel       WOHIN -- ein Ort (Marker) oder eine Relation zu einem Koerper (an/auf/links ...)
      3 Ausfuehrung WIE -- Aktion, Choreographie, Greifer, Zielkodierung
    und eine AUFGABENZEILE, die in einem Satz sagt, was gerade gilt.  Alle Wahlen sind
    Klapplisten statt Durchschalt-Knoepfe."""

    CH_LBL = {"fsm": "Choreo: FSM", "netz": "Choreo: Netz", "attractor": "Choreo: Attraktor"}
    CH_COL = {"fsm": "#5a3a3a", "netz": "#2a5a7a", "attractor": "#5a2a7a"}
    ZIEL_ARTEN = [("ort", "Ort (Marker)"), ("zufall", "Körper, Relation zufällig"),
                  ("an", "an Körper"), ("auf", "auf Körper"), ("links", "links von Körper"),
                  ("rechts", "rechts von Körper"), ("vor", "vor Körper"),
                  ("hinter", "hinter Körper")]

    def __init__(self, state, cam, res, rng=None, randomize_fn=None):
        import matplotlib.pyplot as plt
        from matplotlib.widgets import Button
        from matplotlib.patches import FancyBboxPatch
        from pc_cvnn.pc_act18 import HexFoveaViz, SurpriseViz
        self.plt = plt; self.state = state; self._cam = cam; self._randomize_fn = randomize_fn
        self._rng = rng if rng is not None else np.random.default_rng(0); plt.ion()
        fw, fh = (float(x) for x in os.environ.get("ACT23_FIGSIZE", "12.0,7.5").split(","))
        self.fig = plt.figure(figsize=(fw, fh)); self.fig.patch.set_facecolor("#0e0e12")
        self.fig.canvas.manager.set_window_title("act23 — Selbst-lernender Greifer (Netz steuern)")
        self.axCam = self.fig.add_axes([0.035, 0.36, 0.38, 0.59]); self.axCam.axis("off")
        self.axCam.set_title(f"Arm — {cam} Kamera", color="w", fontsize=10)
        self.imCam = self.axCam.imshow(np.zeros((res, res, 3), np.uint8))
        axFovI = self.fig.add_axes([0.44, 0.66, 0.24, 0.29]); axFovC = self.fig.add_axes([0.44, 0.36, 0.21, 0.25])
        self.fov_viz = HexFoveaViz(cam, res, axI=axFovI, axC=axFovC)
        axE = self.fig.add_axes([0.715, 0.67, 0.27, 0.275]); axR = self.fig.add_axes([0.715, 0.36, 0.27, 0.235])
        self.surp_viz = SurpriseViz(axE=axE, axR=axR, show_readout=False)
        # AUFGABENZEILE (zwei Zeilen) und die Live-Meldung
        self.status = self.fig.text(0.5, 0.318, "", ha="center", color="w", fontsize=10.5,
                                    family="monospace")
        self.status2 = self.fig.text(0.5, 0.292, "", ha="center", color="#9fb4c8", fontsize=8,
                                     family="monospace")
        self.live = self.fig.text(0.225, 0.345, "", ha="center", color="#9fb4c8", fontsize=8.5,
                                  family="monospace")
        self._auswahlen = []

        def gruppe(x0, x1, titel):
            self.fig.patches.append(FancyBboxPatch((x0, 0.095), x1 - x0, 0.175,
                                                   boxstyle="round,pad=0.004", transform=self.fig.transFigure,
                                                   facecolor="#15181f", edgecolor="#3a4656", lw=1.0,
                                                   zorder=-1))
            self.fig.text(x0 + 0.008, 0.255, titel, color="#c8d6e5", fontsize=8.5, weight="bold")

        # ---------------- 1 OBJEKT ----------------
        gruppe(0.02, 0.365, "1  Objekt  (wird transportiert)")
        self._eig = [None, None, None]          # (Farbklasse, Formklasse, Groessenband)
        self._eig_werte = ([], [], [])
        self._eig_fn = None
        self._farb_rgb = None
        self._eig_da = [None, None, None]
        self._obj_btns = {}                      # (Altlast: add_discovered pflegt sie nicht mehr)
        self.aObj = self._auswahl([0.028, 0.195, 0.33, 0.042], "per Name",
                                  lambda: [(i, self.state.anzeige(i)
                                            + ("" if self.state.OBJECTS[i][1] in self._tisch()
                                               else "  – nicht auf dem Tisch"))
                                           for i in range(len(self.state.OBJECTS))],
                                  lambda: self.state.sel, self._set_obj)
        self.aEig = []
        for i, titel in enumerate(("Farbe", "Form", "Größe")):
            a = self._auswahl([0.028 + 0.083 * i, 0.145, 0.079, 0.036], titel,
                              lambda k=i: [(None, "beliebig")] + [(v, str(v)) for v in self._eig_werte[k]],
                              lambda k=i: self._eig[k], lambda v, k=i: self._eig_setzen_feld(k, v),
                              farbe=(lambda v: self._farb_rgb(v) if (self._farb_rgb and v) else None)
                              if i == 0 else None, fontsize=6.5)
            self.aEig.append(a)
        axEig = self.fig.add_axes([0.28, 0.145, 0.078, 0.036])
        self.bEig = Button(axEig, "per Eigensch.", color="#3a5a44", hovercolor="#4a7256")
        self.bEig.label.set_fontsize(6.5); self.bEig.on_clicked(self._eig_anwenden)
        self.obj_info = self.fig.text(0.028, 0.115, "", color="#9fb4c8", fontsize=7, family="monospace")
        self.eig_status = self.obj_info                  # Rueckmeldung der Eigenschaftswahl
        # ---------------- 2 ZIEL ----------------
        gruppe(0.375, 0.655, "2  Ziel  (wohin)")
        self.aArt = self._auswahl([0.383, 0.195, 0.14, 0.042], "Art", lambda: self.ZIEL_ARTEN,
                                  self._ziel_art_wert, self._ziel_art_setzen)
        self.aBezug = self._auswahl([0.527, 0.195, 0.121, 0.042], "Bezug", self._bezug_optionen,
                                    lambda: self.state.ziel_body_fix, self._bezug_setzen)
        self.aMarker = self._auswahl([0.515, 0.145, 0.133, 0.036], "Ort",
                                     lambda: [(i, f"Marker {i + 1}") for i in range(len(self.state.MARKERS))],
                                     lambda: self.state.target_idx, self._set_tgt)
        axZN = self.fig.add_axes([0.383, 0.145, 0.127, 0.036])
        self.bZN = Button(axZN, "Ziel neu würfeln", color="#5a4a7a", hovercolor="#7a64a0")
        self.bZN.label.set_fontsize(7); self.bZN.on_clicked(self._ziel_neu)
        self.ziel_info = self.fig.text(0.383, 0.115, "", color="#9fb4c8", fontsize=7, family="monospace")
        # ---------------- 3 AUSFUEHRUNG ----------------
        gruppe(0.665, 0.98, "3  Ausführung  (wie)")
        self.aAkt = self._auswahl([0.673, 0.195, 0.148, 0.042], "Aktion",
                                  lambda: [("grasp", "Greifen + Ablegen"), ("push", "Schieben")],
                                  lambda: self.state.action, lambda v: setattr(self.state, "action", v))
        self.aCh = self._auswahl([0.826, 0.195, 0.148, 0.042], "Choreo",
                                 lambda: [("fsm", "FSM (Teacher)"), ("netz", "Netz"), ("attractor", "Attraktor")],
                                 lambda: self.state.choreo, lambda v: setattr(self.state, "choreo", v))
        self.aPol = self._auswahl([0.673, 0.145, 0.148, 0.036], "Greifer",
                                  lambda: [("self", "Selbst-gelernt"), ("teacher", "Teacher")],
                                  lambda: self.state.policy, lambda v: setattr(self.state, "policy", v))
        self.aLG = self._auswahl([0.826, 0.145, 0.148, 0.036], "Zielkodierung",
                                 lambda: [("latent", "Latent"), ("koord", "Koordinate")],
                                 lambda: self.state.goalmode, lambda v: setattr(self.state, "goalmode", v))
        # ---------------- UNTERE LEISTE ----------------
        self._introduce_fn = None
        self._ziel_fn = None
        self._pix2welt = None          # Kamerapixel (Spalte, Zeile) -> Tisch xy (von aussen verdrahtet)
        self._auf_tisch = None         # -> Koerper, die gerade auf dem Tisch stehen (von aussen)
        self._pending_introduce = False; self._pending_randomize = False   # deferred mid-episode clicks
        # DIE PLATTE (Stapelauflage, ACT23_SOCKEL=1) VON HAND: ein-/ausblenden, versetzen, umfaerben
        # (Nutzerwunsch 2026-10-01).  _platte_fn(aktion, **kw) -> Meldung wird von aussen verdrahtet;
        # ohne Sockel bleiben beide Klapplisten grau.  Waehrend einer Episode wird vorgemerkt.
        self._platte_fn = None
        self._platte_zustand = None    # -> {"aus": bool, "farbe": rgb}
        self._platte_klick = False     # der naechste Klick ins Kamerabild setzt die Platte
        self._pending_platte = []
        # KLICK INS KAMERABILD (Nutzerwunsch 2026-09-30): links = zu transportierendes Objekt,
        # rechts = Ziel (Koerper, oder bei "Art: Ort" die Stelle), Mitte = Platte hierher.
        self.axCam.set_title(f"{cam} Kamera  (links: Objekt · rechts: Ziel · Mitte: Platte)",
                             color="w", fontsize=9)
        self.fig.canvas.mpl_connect("button_press_event", self._kamera_klick)
        axAuto = self.fig.add_axes([0.02, 0.02, 0.105, 0.06])
        self.bAuto = Button(axAuto, "Auto: aus", color="#3a3a5a", hovercolor="#50507a")
        self.bAuto.on_clicked(self._toggle_auto)
        axO = self.fig.add_axes([0.13, 0.02, 0.105, 0.06])
        self.bO = Button(axO, "Objekte neu", color="#5c7aae", hovercolor="#78a0d0"); self.bO.on_clicked(self._objects)
        axN = self.fig.add_axes([0.24, 0.02, 0.135, 0.06])
        self.bN = Button(axN, "Objekt hinzufügen", color="#8a7430", hovercolor="#a89040")
        self.bN.on_clicked(self._introduce)
        self.aPlatte = self._auswahl([0.38, 0.02, 0.11, 0.06], "Platte",
                                     lambda: [("an", "sichtbar"), ("aus", "ausgeblendet"),
                                              ("wuerfeln", "an neue Stelle"), ("klick", "per Klick setzen")],
                                     lambda: (None if self._platte_zustand is None
                                              else ("aus" if self._platte_zustand()["aus"] else "an")),
                                     self._platte_waehlen)
        self.aPlattenFarbe = self._auswahl([0.495, 0.02, 0.08, 0.06], "Farbe",
                                           lambda: [(rgb, n) for rgb, n in PLATTEN_FARBEN],
                                           lambda: (None if self._platte_zustand is None
                                                    else self._platte_zustand()["farbe"]),
                                           lambda rgb: self._platte("farbe", rgb=rgb),
                                           farbe=lambda rgb: rgb)
        axG = self.fig.add_axes([0.58, 0.02, 0.2, 0.06])
        self.bG = Button(axG, "Ausführen", color="#1f8a5b", hovercolor="#27a96f"); self.bG.on_clicked(self._go)
        axX = self.fig.add_axes([0.79, 0.02, 0.19, 0.06])
        self.bX = Button(axX, "Beenden", color="#8a3030", hovercolor="#a94040"); self.bX.on_clicked(self._exit)
        self.fig.canvas.mpl_connect("close_event", lambda _e: setattr(self.state, "exit", True))
        self._refresh()

    # ---------------- Hilfen ----------------
    def _auswahl(self, rect, titel, optionen, wert, setzen, farbe=None, fontsize=7.5):
        a = _Auswahl(self, rect, titel, optionen, wert, setzen, farbe=farbe, fontsize=fontsize)
        self._auswahlen.append(a)
        return a

    def _popups_schliessen(self):
        for a in self._auswahlen:
            if a._popup:
                a.schliessen()
        self._texte_zeigen(True)

    def _texte_zeigen(self, ja):
        for t in (self.status, self.status2, self.live):
            t.set_visible(ja)

    # ---------------- Objekt ----------------
    def _eig_setzen_feld(self, k, v):
        self._eig[k] = v

    def _eig_beschriften(self, k):
        """(Altname, von aussen gerufen) -- die Felder beschriften sich in _refresh selbst."""
        self._refresh()

    def _eig_anwenden(self, _e=None):
        """Das Tripel als Kommando setzen.  Meldet ZURUECK, was gefunden wurde -- auch
        Mehrdeutigkeit und Fehlschlag, statt sie zu verschlucken."""
        if self._eig_fn is None:
            return
        txt = self._eig_fn(*self._eig)
        self._eig_rueck = txt or ""
        self._refresh()

    def _set_obj(self, k):
        self.state.sel = k
        _l, _b, _m = self.state.OBJECTS[k]
        if _m == "eigenschaft":                          # die Felder zeigen dann die Adresse
            self._eig = list(self.state.EIGENSCHAFT.get(_b, (None, None, None)))
        self._eig_rueck = ""

    def zeige_eigenschaft(self, farbe=None, form=None, groesse=None, verfuegbar=None):
        """Die drei Felder auf ein von AUSSEN gesetztes Tripel stellen (Auto-Lauf)."""
        self._eig = [farbe, form, groesse]
        self._eig_da = list(verfuegbar) if verfuegbar is not None else [None, None, None]
        self._refresh()

    def add_discovered(self, idx):
        """Ein SELBST ENTDECKTES Objekt: es steht ab jetzt in der Klappliste (kein eigener Knopf)."""
        self._refresh()

    # ---------------- Ziel ----------------
    def _ziel_art_wert(self):
        if self.state.ziel_modus != "koerper":
            return "ort"
        return self.state.ziel_art or "zufall"

    def _ziel_art_setzen(self, v):
        if v == "ort":
            self.state.ziel_modus = "ort"; self.state.ziel_bezug = None
            self.state.sync_active()                     # die Scheibe taucht wieder auf (EIN_MARKER)
            self.update(self.state.sim.render(self._cam))
            return
        self.state.ziel_modus = "koerper"
        self.state.sync_active()                         # ... und verschwindet bei Koerper-Ziel
        self.update(self.state.sim.render(self._cam))
        self.state.ziel_art = None if v == "zufall" else v
        self.state.ziel_bezug = None
        if self._ziel_fn is not None and not self.state.busy:
            self._ziel_fn()                              # gleich wuerfeln: die Aufgabenzeile zeigt den Bezug

    def _tisch(self):
        try:
            if self._auf_tisch is not None:
                return list(self._auf_tisch())
        except Exception:
            pass
        return [nm for _l, nm, _m in self.state.OBJECTS]

    def _bezug_optionen(self):
        sel = self.state.selected()[1]
        return [(None, "zufällig")] + [(b, self.state.koerper_hinweis(b)) for b in self._tisch() if b != sel]

    def _bezug_setzen(self, b):
        self.state.ziel_body_fix = b
        if b is not None and self.state.ziel_modus != "koerper":
            self.state.ziel_modus = "koerper"             # ein Bezug ergibt nur mit Koerper-Ziel Sinn
            self.state.sync_active()
        self.state.ziel_bezug = None
        if self.state.ziel_modus == "koerper" and self._ziel_fn is not None and not self.state.busy:
            self._ziel_fn()

    def _kamera_klick(self, ev):
        """Links: das Objekt, das dem Klick am naechsten liegt, wird transportiert.  Rechts: Ziel --
        bei Koerper-Ziel der naechste Koerper als Bezug, sonst wandert der Marker an die Stelle.
        Die Umrechnung Pixel -> Tisch ist die Homographie der Wahrnehmung (nur Bedienung)."""
        if ev.inaxes is not self.axCam or ev.xdata is None or self._pix2welt is None:
            return
        self._popups_schliessen()
        xy = self._pix2welt((float(ev.xdata), float(ev.ydata)))
        if xy is None:
            return
        xy = np.asarray(xy, float)[:2]
        sim = self.state.sim
        if ev.button == 2 or (self._platte_klick and ev.button in (1, 3)):
            self._platte_klick = False
            self._platte("setzen", xy=xy)
            return

        def naechster(kand):
            kand = [b for b in kand if b]
            if not kand:
                return None, 1.0
            b = min(kand, key=lambda o: float(np.linalg.norm(sim.obj_pos(o)[:2] - xy)))
            return b, float(np.linalg.norm(sim.obj_pos(b)[:2] - xy))

        if ev.button == 1:
            b, d = naechster([nm for nm in self._tisch() if nm not in self.state.STUETZEN])
            if b is None or d > 0.04:
                self.live.set_text("Kein Objekt an dieser Stelle"); self.fig.canvas.draw_idle()
                return
            ks = [k for k, (_l, nm, _m) in enumerate(self.state.OBJECTS) if nm == b]
            ks = sorted(ks, key=lambda k: self.state.OBJECTS[k][2] == "eigenschaft")   # Name vor Adresse
            if not ks:
                return
            self._set_obj(ks[0])
            if self.state.ziel_body_fix == b:
                self.state.ziel_body_fix = None
            self.live.set_text(f"Objekt: {self.state.anzeige(ks[0])}")
        elif ev.button == 3:
            if self.state.ziel_modus == "koerper":
                b, d = naechster([nm for nm in self._tisch() if nm != self.state.selected()[1]])
                if b is None or d > 0.04:
                    self.live.set_text("Kein Körper an dieser Stelle"); self.fig.canvas.draw_idle()
                    return
                self._bezug_setzen(b)
                self.live.set_text(f"Bezug: {self.state.koerper_hinweis(b)}")
            else:
                from pc_cvnn.pc_act14 import REACH_XY
                from pc_cvnn.pc_act16 import BASE_CLEAR
                if not (REACH_XY[0][0] <= xy[0] <= REACH_XY[1][0] and REACH_XY[0][1] <= xy[1] <= REACH_XY[1][1]
                        and float(np.linalg.norm(xy)) >= BASE_CLEAR):
                    self.live.set_text("Stelle ausserhalb des Arbeitsbereichs"); self.fig.canvas.draw_idle()
                    return
                self.state.set_marker_xy(self.state.target_idx, xy); self.state.sync_active()
                self.update(sim.render(self._cam), f"Marker {self.state.target_idx + 1} -> "
                                                   f"[{xy[0]:+.3f}, {xy[1]:+.3f}]")
        self._refresh()

    def _set_tgt(self, i):
        self.state.target_idx = i; self.state.sync_active()
        self.update(self.state.sim.render(self._cam), f"Marker {i + 1} gewählt")

    def _ziel_neu(self, _e):
        if self.state.ziel_modus == "koerper":
            if self._ziel_fn is not None and not self.state.busy:
                self._ziel_fn()
        else:
            self.state.place_selected_random(self._rng)
            self.update(self.state.sim.render(self._cam), f"Marker {self.state.target_idx + 1} neu platziert")
        self._refresh()

    # ---------------- Platte ----------------
    def _platte_waehlen(self, v):
        if v == "klick":
            if self._platte_fn is None:
                return
            self._platte_klick = True
            self.live.set_text("Nächster Klick ins Kamerabild setzt die Platte"); self.fig.canvas.draw_idle()
            return
        self._platte(v)

    def _platte(self, aktion, **kw):
        if self._platte_fn is None:
            self.live.set_text("Keine Platte in diesem Lauf (ACT23_SOCKEL=1 fehlt)"); self.fig.canvas.draw_idle()
            return
        if self.state.busy:                                    # mid-episode -> defer (see state.busy)
            self._pending_platte.append((aktion, kw))
            self.live.set_text("Platte — nach der laufenden Episode"); self.fig.canvas.draw_idle()
            return
        txt = self._platte_fn(aktion, **kw)
        self.update(self.state.sim.render(self._cam), txt or "")
        self._refresh()

    def platte_nachholen(self):
        """Waehrend einer Episode vorgemerkte Plattenwuensche JETZT ausfuehren (zwischen Episoden)."""
        _q, self._pending_platte = self._pending_platte, []
        for aktion, kw in _q:
            self._platte(aktion, **kw)

    # ---------------- untere Leiste ----------------
    def _go(self, _e): self.state.go = True
    def _exit(self, _e): self.state.exit = True

    def _objects(self, _e):
        if self._randomize_fn is None:
            return
        if self.state.busy:                                    # mid-episode click -> defer (see state.busy)
            self._pending_randomize = True
            self.live.set_text("Objekte neu — nach der laufenden Episode"); self.fig.canvas.draw_idle()
            return
        self._randomize_fn(); self.update(self.state.sim.render(self._cam), "Objekte neu gewürfelt"); self._refresh()

    def _introduce(self, _e):
        if self._introduce_fn is None:
            return
        if self.state.busy:                                    # mid-episode click -> defer (see state.busy)
            self._pending_introduce = True
            self.live.set_text("Neues Objekt — nach der laufenden Episode"); self.fig.canvas.draw_idle()
            return
        self._introduce_fn(); self._refresh()

    def _toggle_auto(self, _e):
        self.state.auto = not self.state.auto
        self._refresh()

    # ---------------- Anzeige ----------------
    def _refresh(self):
        st = self.state
        _l, _b, _m = st.OBJECTS[st.sel]
        per_eig = _m == "eigenschaft"
        for a in self._auswahlen:
            if a in self.aEig:
                a.aktiv = True
            elif a is self.aMarker:
                a.aktiv = st.ziel_modus != "koerper"
            elif a is self.aBezug:
                a.aktiv = st.ziel_modus == "koerper"
            elif a is self.aPlatte or a is self.aPlattenFarbe:
                a.aktiv = self._platte_fn is not None
            a.refresh()
        # die Eigenschaftsfelder: bei einer NAMENS-Wahl blass, damit "Farbe: beliebig" nicht als
        # Teil des Befehls gelesen wird (Nutzerbefund 2026-09-30)
        for a in self.aEig:
            a.b.label.set_alpha(1.0 if per_eig else 0.45)
        self.bAuto.label.set_text("Auto: an" if st.auto else "Auto: aus")
        self.bAuto.color = "#2a7a4a" if st.auto else "#3a3a5a"; self.bAuto.ax.set_facecolor(self.bAuto.color)
        self.obj_info.set_text(("adressiert per EIGENSCHAFTEN" if per_eig else "adressiert per NAME")
                               + f"  -> {st.koerper_hinweis(_b)}"
                               + (f"   {self._eig_rueck}" if getattr(self, "_eig_rueck", "") else ""))
        self.ziel_info.set_text(st.ziel_hinweis())
        self.status.set_text("Aufgabe:  " + st.aufgabe())
        self.status2.set_text(st.betrieb())
        self.fig.canvas.draw_idle()

    def update(self, frame, txt=""):
        self.imCam.set_data(frame)
        if txt:
            self.live.set_text(txt)
        self.fig.canvas.draw_idle(); self.fig.canvas.flush_events()

    def wait(self):
        while not (self.state.go or self.state.exit):
            self.plt.pause(0.05)
        return "exit" if self.state.exit else "go"

    def hold(self):
        self.plt.ioff(); self.plt.show()


def run_self_learning_steering(headless=False):
    """The act23 command-steering GUI: pick an object, toggle Teacher<->Self-learned wrist, watch the arm
    grasp + deliver.  The self-learned wrist (world model) drives the LONG object; cube/L/U use the scripted
    controller exactly as pc_act21/shape_grasp_viz."""
    import pc_cvnn.pc_act16 as act16
    from pc_cvnn.arm_modules import (ArmAgent, PerceptionModule, RateWrapper, VisualCortexModule,
                                     ShapeClassifierModule)
    act16.ELONG_RATE = 0.0                                 # don't let run_combined elongate a distractor cube
    # run_combined must NEVER rebuild the scene itself: without PERSIST it calls reset_home()+scatter() at
    # EVERY episode, and scatter() set_object_size()s every body in OBJS to CUBE_HALF.  On the composite L/U
    # that clobbers the FIRST geom only (the L's 56mm arm / one U prong becomes a 24mm cube -> "a segment
    # looks rotated 90 deg" at Ausfuehren), permanently -- _set_sizes() only repairs obj_red/obj_blue.  With
    # PERSIST run_combined just does arm_home()+reposition_strays(): act23 owns ALL placement (setup_long,
    # place_all, the run_one snapshot-restore), so the scene truly persists and no geom is ever resized.
    act16.PERSIST = True
    RES = int(os.environ.get("ACT23_RES", "240"))   # 240 -> 480 am 2026-08-02 (Zweig fovea-res):
    #   zusammen mit ACT_FOVEA_F 16->20 und UNVERAENDERTEM K=4 halbiert sich der Zellabstand im
    #   Weltmass (2x Fovea-Aufloesung) bei gleichem Gesichtsfeld.  Gemessen kostet das im
    #   Fovea-Netz fast nichts (Abtastung 2.9 -> 3.2ms); teuer sind allein die 400 statt 256
    #   ZELLEN der PC-Relaxation.  Das Rendern selbst wird 4x teurer, lag aber bei ~10s je
    #   Episode.  ACHTUNG bei Aenderungen: alle PIXEL-Schwellen des Formklassifikators sind auf
    #   240px geeicht und skalieren ueber ShapeClassifierModule.px_scale mit; die gespeicherte
    #   Homographie wird ueber needs_recal() neu gefittet.
    LAM = float(os.environ.get("ACT23_LAM", "1.0"))
    NPOS = int(os.environ.get("ACT23_NPOS", "10")); NTRIAL = int(os.environ.get("ACT23_NTRIAL", "5"))
    LONG = "obj_blue"; LONG_HALF = (0.034, 0.009, 0.012)   # clearly a LONG thin bar (not a cube)
    CUBE_BODIES = ["obj_red", "obj_green"]

    print("act23 [viz] — self-learning grasper command-steering" + (" (headless self-test)" if headless else ""))
    _print_run_settings()
    sim = BracketArmSim(render_wh=(RES, RES)); sim.set_reach_site("contact")
    # ACT23_POLICY=teacher starts in teacher mode (headless isolation: execution/perception WITHOUT the
    # young world model's action lottery; the GUI toggle changes it live as before)
    shape_half0 = {nm: sim.m.geom_size[sim.m.body_geomadr[mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)]].copy()
                   for nm in ("obj_L", "obj_U", "obj_T", "obj_X")}  # pristine XML first-geom half-extents (repair below)

    # PERSISTENCE (user request): the four numpy learners -- body model, shape classifier incl. the
    # self-labelled OPEN-SET classes, world model incl. its trial buffer, runtime policy incl. its DAgger
    # aggregate -- survive across sessions, so lifelong progress (the whole point of the stage-2 DAgger
    # volume) is not lost and the ~10min startup training is skipped.  The hex perception net is NOT
    # persisted (complex PCNetwork; its warmup is ~2min and runs every session).  ACT23_FRESH=1 retrains;
    # ACT23_STATE_PATH overrides the file.  Headless self-tests stay FRESH by default (reproducible gate).
    import pickle
    STATE_PATH = os.environ.get("ACT23_STATE_PATH", os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "state", "act23_state.pkl"))
    PERSIST_STATE = (not headless) or os.environ.get("ACT23_STATE_HEADLESS", "0") == "1"
    # PERSISTENZ-SPERRE fuer Neuheits-Experimente (Nutzerwunsch 2026-08-15).  Eine einfache Form ist
    # eine EINMAL-RESSOURCE: sobald der Agent sie entdeckt und eine Klasse dafuer angelegt hat, taugt
    # sie nie wieder als Neuheitstest, und es gibt nicht mehr viele davon.  Ein Versuch darf deshalb
    # nicht versehentlich in den dauerhaften Zustand durchschlagen.
    # DEFAULT-SICHER: sobald ein ANDERER Neuheits-Koerper als der verbrauchte obj_T gewaehlt wird,
    # schaltet die Persistenz von selbst ab -- man muss sie bewusst mit ACT23_PROBE_PERSIST=1
    # wieder einschalten, nicht umgekehrt daran denken sie auszuschalten.
    # LADEN und SCHREIBEN sind ZWEI Richtungen und muessen getrennt schaltbar sein.  Der erste
    # Entwurf setzte PERSIST_STATE=False und schaltete damit auch das LADEN ab (Zeile ~788 prueft
    # dieselbe Variable) -- der Lauf startete bei null, alles war "neu", und die Aneignungsmessung
    # haette Unsinn ergeben.  Gebraucht wird: auf dem gelernten Stand AUFSETZEN, aber nichts
    # zurueckschreiben.
    # WAS EIN PROBE-LAUF IST: einer, der auf eine EIGENE Zustandsdatei zeigt (ACT23_STATE_PATH).
    # ZUVOR hing das allein an ACT23_NOVEL_BODY != obj_T -- und das war falsch, teuer und meine Schuld:
    # ich habe dem Nutzer am 2026-08-20 selbst empfohlen, fuer den GUI-Lauf ACT23_NOVEL_BODY=obj_X zu
    # setzen, um das Kreuz zu sehen.  Damit galten SEINE echten Laeufe als wegwerfbar; drei GUI-Laeufe
    # (332 Ep + zwei weitere) haben nichts zurueckgeschrieben, darunter der erste, in dem sich der
    # Agent das Kreuz selbst angeeignet und einen Knopf dafuer bekommen hat.
    # Die Hygiene bleibt erhalten: meine Messlaeufe legen IMMER eine Kopie an und setzen
    # ACT23_STATE_PATH darauf -- genau daran sind sie erkennbar, und nur sie.  Ein GUI-Lauf ohne
    # STATE_PATH schreibt wieder normal zurueck.  ACT23_NO_PERSIST=1 sperrt weiterhin von Hand.
    _probe = (bool(os.environ.get("ACT23_STATE_PATH"))
              and os.environ.get("ACT23_NOVEL_BODY", "obj_T") != "obj_T")
    WRITE_STATE = PERSIST_STATE and not (
        os.environ.get("ACT23_NO_PERSIST", "0") == "1"
        or (_probe and os.environ.get("ACT23_PROBE_PERSIST", "0") != "1"))
    if PERSIST_STATE and not WRITE_STATE:
        print("  [Versuch] Zustand wird GELADEN, aber NICHT zurueckgeschrieben -- der Lauf ist "
              "wegwerfbar (ACT23_PROBE_PERSIST=1 hebt das auf)", flush=True)
    STATE_SCHEMA = 2       # BUMP whenever a learner's STRUCTURE changes (action/feature dims, new fields)

    def _lg_pack(lg):
        """STAGE 4a persistence: after training, the latent-goal servo only ever touches its cached
        latent GRID + the learned latent-inverse D -- the PC goal-net itself is never called again.
        So persist just those arrays (no PCNetwork pickling risk) + the workspace bounds they were
        trained on (a changed REACH invalidates the world->grid map, like the shape world-check)."""
        return {"gx": lg._gx, "grid_z": lg._grid_z, "D": lg.D, "zsd": lg.zsd,
                "lo": np.asarray(GOAL_LO, float), "hi": np.asarray(GOAL_HI, float)}

    def _lg_unpack(bb):
        lg = LatentGoalServo.__new__(LatentGoalServo)
        lg.gm = None; lg.rng = np.random.default_rng(3); lg.z_g = None
        lg._gx = bb["gx"]; lg._grid_z = bb["grid_z"]; lg.D = bb["D"]
        lg.zmu = 0.0; lg.zsd = bb["zsd"]
        return lg

    def _validate_loaded(b):
        """SAFE versioning (user request): a pickle can LOAD fine and still not fit the current code
        (a class evolved since the save) -- then it would crash mid-session instead of at startup.
        Two gates: explicit schema/structure fields, then a FUNCTIONAL smoke test of every learner on
        dummy inputs.  Returns None if usable, else the human-readable reason."""
        from pc_cvnn.arm_modules.world_model import ACT_DIM as _AD
        if b.get("schema") != STATE_SCHEMA:
            return f"Schema {b.get('schema')} != Code {STATE_SCHEMA}"
        if b.get("dof") != len(ARM3):
            return f"DOF {b.get('dof')} != {len(ARM3)}"
        try:
            w, rt, sc, bmod = b["world"], b["runtime"], b["shape_clf"], b["bm"]
            bmod.body.fk(np.zeros(len(ARM3)))                  # kinematics forward
            cand = w.candidates(0)
            if cand.shape[1] != _AD:
                return f"Aktions-Dim {cand.shape[1]} != {_AD}"
            w.predict(np.zeros(w.feat_dim), cand[:2])          # world-model ensemble forward
            sc.classify(np.zeros(sc.fmu.shape[0]))             # shape head forward
            sc.resolve(np.zeros(sc.fmu.shape[0]))              # open-set gate (exemplars + thresholds)
            if rt.trained:
                # Breite AUS DEM NETZ nehmen, nicht fest verdrahten: mit dem Tastsinn (d912b74)
                # wuchs der Zustand auf 13, und die fest kodierte 11 liess den Funktionstest
                # scheitern -- woraufhin der GESAMTE Zustand (Welt-Modell, Policy, Formklassen,
                # offene Klassen) als "alte Datei" verworfen wurde.  Beim Sondierungslauf am
                # 2026-08-07 genau so passiert.
                rt.predict(np.zeros(rt.net.W1.shape[1]))       # runtime policy forward
            if b.get("colours") is not None:                   # optional stage-3 colour classes
                b["colours"].classify(np.ones(3) / 3)
            lg = b.get("latent_goal")                          # optional stage-4a goal-latent servo
            if lg is not None:                                 #   (lightweight blob, see _lg_pack)
                if not (np.allclose(lg["lo"], GOAL_LO) and np.allclose(lg["hi"], GOAL_HI)):
                    b["latent_goal"] = None                    # workspace changed -> latent grid stale,
                else:                                          #   retrain (analogue of the world check)
                    _t = _lg_unpack(lg); _t.set_goal(np.array([0.0, 0.15]))
                    _p = _t.servo(np.array([0.02, 0.14]))
                    if _p.shape != (2,) or not np.all(np.isfinite(_p)):
                        return "Ziel-Latent-Servo liefert Unsinn"
            if b.get("self_eval") is not None:                 # optional self-judge (step 1)
                _ok, _d, _f = b["self_eval"].judge([], None, colour_key="x")
                if _ok is not False or _f is not False:
                    return "Selbst-Urteil-Smoke fehlgeschlagen"
        except Exception as e:
            return f"Funktionstest: {type(e).__name__}: {e}"
        return None

    # SCHUTZ GEGEN DEN STILLEN KALTSTART (2026-08-28): wer ACT23_STATE_PATH ausdruecklich setzt,
    # MEINT eine bestimmte Zustandsdatei.  Existiert sie nicht, startete der Lauf bisher wortlos bei
    # null -- dem Nutzer ist genau das passiert: die Kopie war nicht angelegt, der GUI-Lauf trainierte
    # eine Stunde lang ein leeres Netz und fuhr erratisch, und im Banner sah alles richtig aus.
    # Der Vorgabepfad ist NICHT betroffen (ein erster Lauf ohne Datei ist dort voellig normal); es
    # greift nur, wenn die Variable GESETZT ist.  ACT23_FRESH=1 sagt "absichtlich bei null anfangen".
    # PERSIST_STATE mitpruefen: laeuft der Zustand ohnehin nicht (headless-Selbsttest), waere ein
    # Abbruch ein Fehlalarm -- dort ist "keine Datei" der Normalfall.
    # ZWEITES LOCH, 2026-08-31: `os.path.exists` ist auch fuer ein VERZEICHNIS wahr.  Ein
    # verungluecktes ACT23_STATE_PATH (Pfad ohne Dateinamen) kam durch den Riegel, das Laden warf
    # PermissionError, und der Lauf trainierte still frisch -- derselbe teure Fehlstart wie zuvor,
    # nur eine Stufe spaeter.  Jetzt wird auf DATEI geprueft, nicht auf blosse Existenz.
    if (PERSIST_STATE and os.environ.get("ACT23_STATE_PATH") and not os.path.isfile(STATE_PATH)
            and os.environ.get("ACT23_FRESH", "0") != "1"):
        raise SystemExit(f"""
  [Persistenz] ABBRUCH: ACT23_STATE_PATH zeigt auf eine Datei, die es nicht gibt:
      {STATE_PATH}
  Ein Lauf wuerde hier STILL bei null anfangen (untrainiertes Netz, erratische Bewegungen).
  Gemeint war vermutlich eine Kopie des gelernten Standes:
      Copy-Item <gelernter Stand> {STATE_PATH} -Force
  Absichtlich bei null anfangen: ACT23_FRESH=1 setzen.
""")

    _loaded = None
    if PERSIST_STATE and os.environ.get("ACT23_FRESH", "0") != "1" and os.path.exists(STATE_PATH):
        reason = None
        try:
            with open(STATE_PATH, "rb") as f:
                _b = pickle.load(f)
            reason = _validate_loaded(_b)
            if reason is None:
                _loaded = _b
        except Exception as e:
            reason = f"Laden: {type(e).__name__}: {e}"
        if reason is not None:                                 # keep the old state instead of silently
            bak = STATE_PATH + ".bak"                          #   overwriting it on the next save
            try:
                os.replace(STATE_PATH, bak)
                print(f"  [Persistenz] Zustand passt nicht zum Code ({reason}) — alte Datei -> "
                      f"{os.path.basename(bak)}, trainiere frisch", flush=True)
            except Exception:
                print(f"  [Persistenz] Zustand unbrauchbar ({reason}) — trainiere frisch", flush=True)

    if _loaded is not None:
        bm = _loaded["bm"]
    else:
        bm = BodyModelModule(rng=np.random.default_rng(5)); bm.babble(sim, 4000)
    state = CommandState23(sim)
    # EIGENSCHAFTS-KOMMANDO ohne GUI (und zugleich die Kommandozeilen-Entsprechung der spaeteren
    # Auswahlfelder): ACT23_EIG_BODY nennt den Koerper fuer die Buchfuehrung/Bewertung, die drei
    # uebrigen Variablen das Tripel.  Leer = "beliebig".  Die LOKALISIERUNG laeuft rein ueber die
    # Eigenschaften -- der Koerpername geht NICHT in die Wahrnehmung ein.
    # ACT23_AUTO_EIG=1: die Auto-Schleife wuerfelt EIGENSCHAFTS-Tripel aus sichtbaren
    # Detektionen statt Listeneintraege.  ACT23_EIG_ONLY=1 blendet zusaetzlich die alte
    # Objektzeile aus, sodass die drei Waehlfelder die einzige Bedienung sind.
    AUTO_EIG = os.environ.get("ACT23_AUTO_EIG", "0") != "0"
    _eig_body = os.environ.get("ACT23_EIG_BODY", "")
    if _eig_body:
        _k = state.add_eigenschaft(_eig_body,
                                   os.environ.get("ACT23_EIG_FARBE") or None,
                                   os.environ.get("ACT23_EIG_FORM") or None,
                                   os.environ.get("ACT23_EIG_GROESSE") or None)
        state.sel = _k
        print(f"  [Eigenschaft] '{state.OBJECTS[_k][0]}' als Kommando {_k} angelegt "
              f"(Buchfuehrung: {_eig_body})", flush=True)
    state.policy = os.environ.get("ACT23_POLICY", "self")
    state.choreo = os.environ.get("ACT23_CHOREO", "netz")   # DEFAULT netz seit 2026-08-02 (war fsm):
    #   der Nutzer schaltet beim GUI-Start ohnehin jedes Mal von Hand auf Netz um.  ACT23_CHOREO=fsm
    #   holt die gescriptete Choreographie zurueck (Rauchtests/Vergleichslaeufe nutzen sie weiter).
    panel = None
    if not headless:
        panel = CommandPanel23(state, CAM, RES, rng=np.random.default_rng(7))
        panel.update(sim.render(CAM), "Training: Farb-Wahrnehmung (Würfel + Formen als Distraktoren streuen) ...")
    os.environ["ACT18_SCATTER_EXTRA"] = "obj_L,obj_U"   # scatter the shapes too during vc warmup (consistency)
    # PERSIST the fovea net (task 3): reuse a saved, already-warmed+class-trained HexFovea -> skip the
    # ~2-3 min startup warmup + selection training.  Only meaningful with the learned gaze (FOVEA_NET).
    _pf = (_loaded.get("fovea") if (_loaded is not None and FOVEA_NET) else None)
    if _pf is not None:                                # structural check: a grid/K change since the save
        try:                                           #   makes the persisted net incompatible -> fall back
            ok = (hasattr(_pf, "net") and hasattr(_pf, "sel_head") and len(_pf.cells) == HEX_F * HEX_F
                  and int(_pf.K) == int(os.environ.get("ACT_FOVEA_K", "4")))
        except Exception:
            ok = False
        if not ok:
            print("  [Persistenz] gespeicherte Fovea passt nicht (Gitter/K geändert) -- Warmup läuft neu",
                  flush=True)
            _pf = None
    _fovea_loaded = _pf is not None
    vc, _P = VisualCortexModule.from_sim(sim, CAM, RES, headless=True, pretrained_fovea=_pf,
                                         viz=(panel.fov_viz if panel is not None else None))
    def _fresh_shape_clf():
        if panel is not None:
            panel.update(sim.render(CAM), "Form-Wahrnehmung wird trainiert ...")
        sc = ShapeClassifierModule(cam=CAM, rng=np.random.default_rng(0))
        saved = sim.d.mocap_pos.copy(); sc.calibrate(sim)

        def _shape_viz(i, steps, shp):                         # show the form-training live (one shape at a time)
            panel.update(sim.render(CAM), f"Form-Wahrnehmung: {i}/{steps}  (lernt gerade: {shp})")

        sc.train(sim, steps=int(os.environ.get("ACT23_SHAPE_STEPS", "2500")), rng=np.random.default_rng(1),
                 viz_fn=(_shape_viz if panel is not None else None),
                 viz_every=int(os.environ.get("ACT23_SHAPE_VIZ_EVERY", "40")))
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        return sc

    def _shapes_match_world(sc):
        """WORLD-CONSISTENCY post-load check (the versioning philosophy, but vs the WORLD instead of
        the schema): the loaded classifier must still FIND each trained shape in the CURRENT sim.  An
        object-geometry edit silently invalidates the trained |F| manifold -- measured with the
        widened U: the old-U classifier saw it as 27/30 NOVEL and select('U') never matched, so the
        command would run on the privileged fallback forever and the open-set would breed a phantom
        class ON the U.  Each trained shape gets 2 poses; 1 hit each is enough (the healthy
        classifier localises 0-2mm, a stale one misses ALL poses of the changed shape)."""
        keep = {o: (sim.obj_pos(o)[:2].copy(), float(sim.obj_pos(o)[2]), float(sim.obj_yaw(o)))
                for o in ALL}
        saved = sim.d.mocap_pos.copy()
        ok = True
        try:
            for body, key in (("obj_red", "cube"), ("obj_L", "L"), ("obj_U", "U")):
                hits = 0
                for xy, yaw in (((0.0, 0.15), 0.0), ((0.05, 0.18), 0.9)):
                    for o in ALL:
                        sim.set_object(o, [0.5, -0.6], z=0.012)
                    sim.set_object(body, list(xy), z=0.012, yaw=yaw)
                    mujoco.mj_forward(sim.m, sim.d)
                    det = sc.select(sim, key)
                    if det is not None and float(np.linalg.norm(np.asarray(det["pos"])
                                                                - np.asarray(xy))) < 0.03:
                        hits += 1
                if hits == 0:
                    print(f"  [Persistenz] Welt-Check: Form '{key}' wird nicht mehr erkannt", flush=True)
                    ok = False
        finally:
            for o, (xy, z, yaw) in keep.items():
                sim.set_object(o, xy.tolist(), z=z, yaw=yaw)
            sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        return ok

    if _loaded is not None:
        shape_clf = _loaded["shape_clf"]
        # HOMOGRAPHIE VOR dem Welt-Check nachfitten, wenn sich die Bildaufloesung geaendert hat.
        # Sonst laege JEDE wahrgenommene Position um den Aufloesungsfaktor daneben, _shapes_match_world
        # schluege fehl und der Klassifikator wuerde komplett neu trainiert -- wobei die SELBST
        # BENANNTEN offenen Klassen (neu-*) verloren gingen.  H ist reine Kamera-Kalibrierung, kein
        # Gelerntes: neu fitten kostet nichts und rettet die Klassen.
        if shape_clf.needs_recal(sim):
            _sv = sim.d.mocap_pos.copy()
            _n = shape_clf.calibrate(sim)
            sim.d.mocap_pos[:] = _sv; mujoco.mj_forward(sim.m, sim.d)
            print(f"  [Persistenz] Bildaufloesung geaendert -> Homographie neu gefittet ({_n} Punkte); "
                  f"gelernte Formen und offene Klassen bleiben erhalten", flush=True)
        if _shapes_match_world(shape_clf):
            if panel is not None:
                panel.update(sim.render(CAM), "Form-Wahrnehmung aus gespeichertem Zustand geladen")
        else:
            print("  [Persistenz] Form-Klassifikator passt nicht mehr zur Welt (Objekt-Geometrie "
                  "geändert?) -> NUR die Form-Wahrnehmung wird neu trainiert; Welt-Modell, Policy und "
                  "Farbklassen bleiben erhalten.  Offene Form-Klassen (neu-*) leben im alten "
                  "Deskriptor-Raum und werden verworfen -- neue Objekte werden wieder selbst entdeckt.",
                  flush=True)
            shape_clf = _fresh_shape_clf()
            _loaded["objects"] = []                            # discovered commands were keyed on the old
            _loaded["shape_key"] = {}                          #   classes -> dropped with the old manifold
    else:
        shape_clf = _fresh_shape_clf()

    # DER HOEHENSCHAETZER lebt mit den anderen Lernern im Zustand: er sammelt eine Zeile je
    # Stapel-Episode, und mit einer Zeile pro Episode dauert es sonst Hunderte Laeufe, bis er
    # etwas kann.  Ein alter Zustand ohne den Schluessel bekommt einen leeren -- additiv, deshalb
    # ohne Schema-Bump (s. _validate_loaded: der prueft die PFLICHT-Lerner).
    hoehen_schaetzer = (_loaded or {}).get("hoehe_schaetzer") or HoehenSchaetzer()
    if not isinstance(hoehen_schaetzer, HoehenSchaetzer):        # Klasse hat sich geaendert
        hoehen_schaetzer = HoehenSchaetzer()
    groessen_schaetzer = (_loaded or {}).get("groessen_schaetzer") or GroessenSchaetzer()
    if not isinstance(groessen_schaetzer, GroessenSchaetzer):
        groessen_schaetzer = GroessenSchaetzer()
    print(f"  [Groesse] Schaetzer mit {len(groessen_schaetzer.X)} Zeilen  -- "
          + ("die Policy sieht die SCHAETZUNG (ACT23_GROESSE_SEHEN=1)" if GROESSE_SEHEN
             else "lernt nur mit, die Policy sieht das Privileg"), flush=True)

    def _groesse_wahr(nm):
        """Das Etikett (Geruest): genau was run_combined bisher in den Zustand schrieb."""
        _b = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)
        _h = sim.m.geom_size[sim.m.body_geomadr[_b]]
        return float(np.min(_h[:2])), float(_h[2])

    def _groesse(cmd, xy):
        """pc_act16.GROESSE_FN: (obj_fp, obj_h) des kommandierten Objekts aus der Wahrnehmung.

        Ein Blick auf die Szene (Arm zu Hause, Marker geparkt wie bei jedem Blick).  ERST
        SCHAETZEN, DANN MERKEN: sonst stuende die eigene Zeile schon im Schaetzer.  Gemerkt werden
        ALLE stehenden Koerper der Szene (Zuordnung Detektion -> Koerper ueber die Lage, <= 20 mm:
        buchhalterisch privilegiert wie das Etikett selbst), nicht nur das kommandierte -- sonst
        sammelte er eine Zeile je Episode."""
        _sv = sim.d.mocap_pos.copy()
        try:
            dets = shape_clf.perceive_all(sim)
        finally:
            sim.d.mocap_pos[:] = _sv; mujoco.mj_forward(sim.m, sim.d)
        dets = [d for d in dets if d.get("pos") is not None]
        _schaetz = None; _grund = None
        if xy is None:
            _grund = "kein gesehener Objektort"
        elif not dets:
            _grund = "keine Detektion"
        else:
            _dc = min(dets, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"], float) - np.asarray(xy, float)[:2])))
            if float(np.linalg.norm(np.asarray(_dc["pos"], float) - np.asarray(xy, float)[:2])) > 0.03:
                _grund = "keine Detektion am gesehenen Ort"
            else:
                _schaetz = groessen_schaetzer.schaetzen(_dc)
                if _schaetz is None:
                    _grund = f"erst {len(groessen_schaetzer.X)} Zeilen (braucht {GroessenSchaetzer.MIN_ZEILEN})"
        _steht = [n for n in dict.fromkeys(n for _l, n, _m in state.OBJECTS)
                  if not _geparkt_jetzt(n)]
        _n0 = len(groessen_schaetzer.X)
        for d in dets:
            _q = np.asarray(d["pos"], float)
            _nah = [(float(np.linalg.norm(sim.obj_pos(n)[:2] - _q)), n) for n in _steht]
            if not _nah:
                continue
            _dd, _nb = min(_nah)
            if not D0_FREEZE and _dd <= 0.02 and sim.obj_pos(_nb)[2] < 0.02:      # nur Tischobjekte (kein Stapel)
                groessen_schaetzer.merken(d, *_groesse_wahr(_nb))
        if cmd is None:
            return None
        _w = _groesse_wahr(cmd)
        if _schaetz is not None:
            print(f"    [Groesse] {cmd}: gesehen fp {1000 * _schaetz[0]:.1f} h {1000 * _schaetz[1]:.1f} mm"
                  f" | wahr {1000 * _w[0]:.1f}/{1000 * _w[1]:.1f} | Fehler fp "
                  f"{1000 * abs(_schaetz[0] - _w[0]):.1f} h {1000 * abs(_schaetz[1] - _w[1]):.1f} mm"
                  f" | {'BENUTZT' if GROESSE_SEHEN else 'nur mitgelernt'} | +{len(groessen_schaetzer.X) - _n0}"
                  f" Zeilen -> {len(groessen_schaetzer.X)}", flush=True)
        else:
            print(f"    [Groesse] {cmd}: keine Schaetzung ({_grund})"
                  + (" -- RUECKFALL auf das Privileg" if GROESSE_SEHEN else "")
                  + f" | +{len(groessen_schaetzer.X) - _n0} Zeilen -> {len(groessen_schaetzer.X)}", flush=True)
        return _schaetz if GROESSE_SEHEN else None

    act16.GROESSE_FN = _groesse

    _nur_groesse = {"an": False}

    def _groesse_sammeln(n):
        """ACT23_GROESSE_SAMMELN=n: n frisch aufgebaute Szenen nur ANSCHAUEN und beschriften, ohne
        Arm -- billiger als 50 Episoden.  Je Szene ERST alle Koerper schaetzen, DANN merken: das
        ist eine Haltemessung ueber die Zeit (nie eine Zeile derselben Szene im Schaetzer).
        Fester Generator (4242) und danach zurueckgestellt: jeder Arm eines A/B bekommt denselben
        Schaetzer, und die Szenenfolge des Hauptlaufs bleibt unberuehrt."""
        _alt = crng.bit_generator.state
        crng.bit_generator.state = np.random.default_rng(4242).bit_generator.state
        _blk = []
        _nur_groesse["an"] = True                      # kein Open-Set-Blick, keine Klassengeburt
        try:
            for i in range(n):
                randomize_objects()
                _sv = sim.d.mocap_pos.copy()
                try:
                    dets = shape_clf.perceive_all(sim)
                finally:
                    sim.d.mocap_pos[:] = _sv; mujoco.mj_forward(sim.m, sim.d)
                _steht = [nm for nm in dict.fromkeys(nm for _l, nm, _m in state.OBJECTS)
                          if not _geparkt_jetzt(nm)]
                for d in dets:
                    if d.get("pos") is None:
                        continue
                    _q = np.asarray(d["pos"], float)
                    _nah = [(float(np.linalg.norm(sim.obj_pos(nm)[:2] - _q)), nm) for nm in _steht]
                    if not _nah or min(_nah)[0] > 0.02:
                        continue
                    _w = _groesse_wahr(min(_nah)[1]); _e = groessen_schaetzer.schaetzen(d)
                    if _e is not None:
                        _blk.append((abs(_e[0] - _w[0]), abs(_e[1] - _w[1]),
                                     min((0.0065, 0.009, 0.012), key=lambda c: abs(c - _e[0]))
                                     == min((0.0065, 0.009, 0.012), key=lambda c: abs(c - _w[0]))))
                for d in dets:                                     # erst jetzt merken
                    if d.get("pos") is None:
                        continue
                    _q = np.asarray(d["pos"], float)
                    _nah = [(float(np.linalg.norm(sim.obj_pos(nm)[:2] - _q)), nm) for nm in _steht]
                    if _nah and min(_nah)[0] <= 0.02:
                        groessen_schaetzer.merken(d, *_groesse_wahr(min(_nah)[1]))
                if (i + 1) % 25 == 0 and _blk:
                    _a = np.asarray(_blk, float)
                    print(f"  [Groesse] Sammeln {i + 1}/{n}: {len(groessen_schaetzer.X)} Zeilen | gehalten "
                          f"(Szenen {i - 23}-{i + 1}): fp-Fehler {1000 * _a[:, 0].mean():.2f} mm, "
                          f"h-Fehler {1000 * _a[:, 1].mean():.2f} mm, richtige Gruppe "
                          f"{100 * _a[:, 2].mean():.0f} % (n={len(_a)})", flush=True)
                    _blk = []
        finally:
            crng.bit_generator.state = _alt
            _nur_groesse["an"] = False
        randomize_objects()
    # DIE GELERNTEN WORTBEDEUTUNGEN (s. RICHTUNG_QUELLE): Wort -> Liste von Welt-Einheitsvektoren,
    # je einer pro eigener Ablage, die der Agent im Nachhinein unter diesem Wort gesehen hat.
    # Ein schlichtes dict aus Listen -- pickelbar ohne Klasse, additiv wie der Hoehenschaetzer.
    wort_bedeutung = dict((_loaded or {}).get("wort_bedeutung") or {})
    blick_daten = list((_loaded or {}).get("blick_daten") or [])   # s. BLICK_LERNEN
    for _w in RICHTUNGS_WOERTER:
        wort_bedeutung.setdefault(_w, [])

    def _wort_richtung(wort, p, laut=True):
        """Einheitsvektor in der WELT fuer ein Richtungswort am Bezugsort p, und die Quelle."""
        if RICHTUNG_QUELLE == "gelernt":
            _v = wort_bedeutung.get(wort) or []
            if len(_v) >= RICHTUNG_MIN:
                _m = np.mean(np.asarray(_v, float), axis=0)
                if float(np.linalg.norm(_m)) > 1e-6:
                    return _m / float(np.linalg.norm(_m)), f"gelernt aus {len(_v)}"
            if laut:
                print(f"    [Richtung] '{wort}': erst {len(_v)} eigene Beispiele "
                      f"(braucht {RICHTUNG_MIN}) -- RUECKFALL auf die Kamera-Achse", flush=True)
        if shape_clf.H is None:
            return None, "keine Homographie"
        _q = shape_clf._world_to_px(np.asarray(p, float))[0]
        _w1 = shape_clf._px_to_world(_q + 10.0 * np.asarray(RICHTUNGS_WOERTER[wort], float))[0]
        _d = _w1 - np.asarray(p, float)
        return _d / float(np.linalg.norm(_d)), "kamera"

    def _wort_gesehen(px_obj, px_ref):
        """Welches Wort beschreibt, wo das Objekt vom Bezug aus im BILD liegt -- die dominante Achse."""
        _d = np.asarray(px_obj, float) - np.asarray(px_ref, float)
        return max(RICHTUNGS_WOERTER, key=lambda w: float(_d @ np.asarray(RICHTUNGS_WOERTER[w])))
    # WAS DIE LETZTE EPISODE ERTASTET HAT, fuer das belegte Aussehen (s. HOEHE_BELEGT).
    # Warum ueber Episoden hinweg: am ENDE einer Episode steht der Arm ueber der Auflage und
    # verdeckt sie -- der Rauchtest fand dort nur 1 von 7 Stapeln.  Am ANFANG der naechsten ist
    # er zu Hause, und der Stapel steht noch (die Aufraeumschleife laesst ein Objekt oben liegen,
    # seit wiki/befunde/selbstrichter-stapel.md).  Das Etikett gilt unveraendert: die Oberkante
    # der Auflage aendert sich nicht dadurch, dass etwas darauf steht.
    _tast_stand = {}
    if HOEHE_SEHEN or len(hoehen_schaetzer.X):
        print(f"  [Hoehe] Schaetzer mit {len(hoehen_schaetzer.X)} Zeilen"
              + ("  -- die Oberkante kommt aus der WAHRNEHMUNG (ACT23_HOEHE_SEHEN=1)"
                 if HOEHE_SEHEN else "  -- lernt nur mit, benutzt wird das Privileg"), flush=True)

    # ACT23_UDIAG=1: U-GRASP-POINT diagnosis (mechanism-ID, no fix).  The 746-log showed U fails
    # mostly as "greift ins Leere" (47% nicht-gegriffen, |dyaw|~7).  Hypothesis (code-grounded,
    # shape_classifier:599-603): select() returns grasp_xy = MATERIAL nearest the CENTROID, and a U's
    # centroid sits in its concavity -> the grasp lands on a THIN inner rim, not the solid base.  This
    # renders the U occupancy + overlays centroid, the select() grasp point (nearest-material, what
    # runs now) and the DENSEST point (distance-transform max = base) with their material thickness,
    # so the claim is SEEN before any change.  Writes log/u_grasp_diag.png and exits.
    if os.environ.get("ACT23_UDIAG") == "1":
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as _plt
        from scipy import ndimage as _ndi
        sc = shape_clf
        saved_mp = sim.d.mocap_pos.copy()
        poses = [((0.0, 0.15), 0.0), ((0.05, 0.18), 0.9), ((-0.03, 0.13), 2.2)]
        fig, axes = _plt.subplots(1, len(poses), figsize=(4.2 * len(poses), 4.4))
        for ax, (xy, yaw) in zip(np.atleast_1d(axes), poses):
            for o in ALL:
                sim.set_object(o, [0.5, -0.6], z=0.012)
            sim.set_object("obj_U", list(xy), z=0.012, yaw=yaw)
            mujoco.mj_forward(sim.m, sim.d)
            img = sc._render_u8(sim); mask = sc._mask(img)
            labels, n = _ndi.label(mask)
            # largest component = the U
            comp = None; best_a = 0
            for lab in range(1, n + 1):
                c = (labels == lab).astype(np.float32)
                if c.sum() > best_a:
                    best_a = c.sum(); comp = c
            ys, xs = np.nonzero(comp)
            dist = _ndi.distance_transform_edt(comp)                    # material thickness (px)
            dv = dist[ys, xs]
            i_dense = int(np.argmax(dv))                                # thickest = solid base
            if sc.H is not None:
                ctr_w = sc._centroid(comp)
                W = sc._px_to_world(np.column_stack([xs, ys]))
                i_sel = int(np.argmin(np.linalg.norm(W - ctr_w, axis=1)))   # what select() uses
                move_mm = 1000.0 * float(np.linalg.norm(W[i_sel] - W[i_dense]))
                unit = "mm"
            else:                                                       # no homography -> px space
                cpx = np.array([xs.mean(), ys.mean()])
                i_sel = int(np.argmin(np.linalg.norm(np.column_stack([xs, ys]) - cpx, axis=1)))
                move_mm = float(np.hypot(xs[i_sel] - xs[i_dense], ys[i_sel] - ys[i_dense]))
                unit = "px"
            # centroid in px (mean of component)
            cx, cy = xs.mean(), ys.mean()
            thick_sel = float(dist[ys[i_sel], xs[i_sel]])
            thick_dense = float(dv[i_dense])
            ax.imshow(mask, cmap="gray", origin="upper")
            ax.plot(cx, cy, "b+", ms=14, mew=2.5, label="Schwerpunkt (Konkavität)")
            ax.plot(xs[i_sel], ys[i_sel], "rx", ms=13, mew=2.8,
                    label=f"select()-Griff  Dicke {thick_sel:.1f}px")
            ax.plot(xs[i_dense], ys[i_dense], "go", ms=11, mfc="none", mew=2.6,
                    label=f"dichtester (Basis)  Dicke {thick_dense:.1f}px")
            ax.set_title(f"U yaw {yaw:.1f} | Griff->Basis {move_mm:.0f}{unit}", fontsize=9)
            ax.legend(fontsize=7, loc="upper right")
            ax.axis("off")
            print(f"  [UDIAG] yaw {yaw:.2f}: select-Dicke {thick_sel:.1f}px  "
                  f"dichtest-Dicke {thick_dense:.1f}px  Griff->Basis {move_mm:.0f}{unit}", flush=True)
        sim.d.mocap_pos[:] = saved_mp; mujoco.mj_forward(sim.m, sim.d)
        outp = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "log", "u_grasp_diag.png")
        fig.tight_layout(); fig.savefig(outp, dpi=110)
        print(f"  [UDIAG] geschrieben -> {outp}", flush=True)
        raise SystemExit(0)

    # STAGE 4a: the place TARGET as a LATENT state (the act6 goal-as-prior, wired into the GUI).
    # The commanded goal is ENCODED once into the goal-module latent; while the object is carried,
    # the place target is DRIVEN by the latent DIFFERENCE between goal latent and the hand's latent
    # (learned latent-inverse) -- execution converges where the LATENTS MATCH, not on a decoded
    # coordinate (act-b: side-steps decode bias; RoPE latent = near-linear -> servo isolated ~0mm).
    # GUI toggle "Ziel: Latent/Koord"; env ACT23_GOAL=koord restores the coordinate place.
    _lgb = _loaded.get("latent_goal") if _loaded is not None else None
    if _lgb is not None:
        lgoal = _lg_unpack(_lgb)
        print("  [Stufe 4] Ziel-Latent-Servo aus gespeichertem Zustand geladen", flush=True)
    else:
        if panel is not None:
            panel.update(sim.render(CAM), "Stufe 4: Ziel-Latent wird trainiert (Goal-Modul + Latent-Inverse) ...")
        _gm = GoalModule2D(rng=np.random.default_rng(7))
        _gm.pretrain(int(os.environ.get("ACT23_GM_STEPS", "8000")))
        lgoal = LatentGoalServo(_gm, rng=np.random.default_rng(3))
        _rec = lgoal.train(steps=4000)
        print(f"  [Stufe 4] Ziel-Latent bereit (RoPE-Latent={_gm.rope}): "
              f"Latent-Inverse-Babble {_rec:.1f} mm", flush=True)
    lgoal_lang = LatentGoalLanguage(lgoal)
    lat_dyn = LatentDynamicsModule(latent_dim=10, action_dim=4, rng=np.random.default_rng(8))
    if _loaded is not None and "latent_dynamics" in _loaded:
        lat_dyn.unpack(_loaded["latent_dynamics"])
        print("  [Etappe 2] Latent-Dynamics Übergangsmodell aus Zustand geladen", flush=True)
    lat_attractor = LatentAttractorController(lgoal, lat_dyn, rng=np.random.default_rng(9))
    print("  [Etappe 3] Latent-Attraktor Steuerung bereit (kontinuierliches Latent-Planning)", flush=True)

    # STAGE 4b: the planner DREAMS its practice targets (act21 CuriosityPlanner.dream, wired into the
    # auto-run): candidate goals are scored by DISTANCE-NOVELTY in the GOAL-LATENT space -- the SAME
    # latent the 4a place servo executes on (lgoal.encode_world; one latent space for dreaming AND
    # acting; the dreamed latent IS the executed z_g, since post_goal_fn encodes the same position).
    # The dream memory (visited latents) PERSISTS across sessions -- the agent remembers what it has
    # already practiced.  ACT23_DREAM=0 restores the coordinate-novelty target pick.
    DREAM = os.environ.get("ACT23_DREAM", "1") == "1"
    dream_nov = DistanceNovelty()
    if _loaded is not None:
        dream_nov.seen = [np.asarray(z) for z in _loaded.get("dream_seen", [])]

    # SELF-JUDGED OUTCOME (step 1 of the self-improvement plan, user request): after every episode
    # the agent judges its own result -- commanded object found via its SELF-LABELLED classes, the
    # distance to the wish measured as GOAL-LATENT difference through the learned latent-inverse.
    # This step only INSTALLS the judge and MEASURES agreement with the privileged verdict; the
    # learners' outcome labels stay privileged until the agreement is proven (steps 2/3).
    seval = (_loaded.get("self_eval") if _loaded is not None else None) or SelfEvalModule(tol=act16.TOL)
    objmem = ObjectMemoryModule()                             # per-episode predictive belief for the gaze

    # self-supervised world model for the GRASP WRIST (collect own trials, then train).
    # OPEN-WORLD situation features -- ONE camera perception path (|F| pipeline) for EVERY object:
    #   [pos(2), cos/sin(2*yaw), cos/sin(4*yaw4), desc_embed(NH)]
    # yaw (k=2 phase, mod pi) carries an ELONGATED object's axis; yaw4 (k=4 phase, mod pi/2) carries a
    # SQUARE's orientation -- k=2 is DEGENERATE on a cube, and the fixed teacher wrist (WRIST_TGT mod
    # 90deg) is exactly what slips off DIAGONAL cubes now that the continuous scene keeps their random
    # yaw (scatter() used to re-place them axis-aligned each episode, masking the gap).  The descriptor
    # embedding (no class one-hot) lets this ONE model absorb trials from any form.  (The former
    # ObjectOrientationModule features are subsumed by the k=2 phase -- one perception path, no oo.)
    world = (_loaded["world"] if _loaded is not None else
             WorldModelModule(k=5, off_max=0.008, rng=np.random.default_rng(2),
                              feat_dim=6 + shape_clf.NH + NB_DIM + FOV_DIM + BD_DIM))
    # Schema-Erweiterungen der Reihe nach; jede ist idempotent, also greift beim Laden genau die,
    # die dem Puffer noch fehlt (14 -> 19 -> 31).
    _n_mig = world.ensure_feat_dim(6 + shape_clf.NH + NB_DIM, NB_NEUTRAL)
    if _n_mig:
        print(f"  [Schema] Nachbar-Information ergaenzt: {_n_mig} bestehende Zeilen migriert "
              f"(gueltig-Flag 0 -- sie hatten die Information nie)", flush=True)
    _n_mig = world.ensure_feat_dim(6 + shape_clf.NH + NB_DIM + FOV_DIM, FOV_NEUTRAL)
    if _n_mig:
        print(f"  [Schema] Fovea-Zustand ergaenzt: {_n_mig} bestehende Zeilen migriert "
              f"(gueltig-Flag 0)", flush=True)
    _n_mig = world.ensure_feat_dim(6 + shape_clf.NH + NB_DIM + FOV_DIM + BD_DIM, BD_NEUTRAL)
    if _n_mig:
        print(f"  [Schema] Armstellung ergaenzt: {_n_mig} bestehende Zeilen migriert "
              f"(gueltig-Flag 0)", flush=True)
    #   off_max>0 (STAGE-1 de-scripting): the grasp-point OFFSET dims are live -- the model can learn to
    #   grasp a form off its perceived grasp point; grip+gentle action dims replace the obj_U runtime rules.

    # STAGE 2 de-scripting (user request): a LEARNED runtime policy replaces the scripted choreography.
    # EVERY episode -- startup trials, manual commands, the curiosity auto-run -- is lifelong DAgger data:
    # each VISITED state is labelled by the MARKOVIAN reactive teacher (act16.reactive_subgoal; the act19
    # lesson: the stateful phase machine's labels degrade DAgger).  "Choreo: Netz" (GUI toggle /
    # ACT23_CHOREO=netz) lets the POLICY drive the sub-goals incl. the gripper; guards stay on by default
    # (train-with-guard) -- verify guard-free with ACT16_CLOSE_GUARD=0 ACT16_REFLEX=0.
    # KOERPERMODELL: Merkmalsbreite pruefen.  Seit die Zusatzgelenke (Wrist/Greifer) Eingang sind,
    # ist NF gewachsen; ein aelteres gespeichertes Modell passt nicht mehr und wird neu gebabbelt.
    # Das kostet Sekunden und verliert nichts -- die Kinematik ist die einzige rein
    # selbstueberwachte Groesse im Zustand.
    try:
        _want = ArmBodyModel3D(rng=np.random.default_rng(0)).NF
        if bm.body.NF != _want:
            print(f"  [Persistenz] Koerpermodell hat {bm.body.NF} Merkmale, erwartet {_want} "
                  f"(Wrist/Greifer neu als Eingang) -- wird neu gebabbelt ...", flush=True)
            bm.body = ArmBodyModel3D(rng=np.random.default_rng(5)); bm.babble(sim, 4000)
    except Exception as _e:
        print(f"  [Persistenz] Koerpermodell-Pruefung uebersprungen: {_e}", flush=True)
    runtime = _loaded["runtime"] if _loaded is not None else RuntimePolicyModule(rng=np.random.default_rng(4))
    # DIE AUFGESETZTE ABLAGE NEU ETIKETTIEREN (s. pc_act16.ABLAGE_FIX).  Teacher-Etiketten sind eine
    # Funktion des Zustands: wo die Korrektur das Etikett aendert, wird es ersetzt -- einmal beim
    # Laden, fuer DAgger- und Selbst-Imitationszeilen.  Danach einmal nachtrainieren.
    if not D0_FREEZE and act16.ABLAGE_FIX and len(getattr(runtime, "_X", [])):
        _n_d = _n_s = 0
        for _buf_x, _buf_y, _zaehl in ((runtime._X, runtime._Y, "d"),
                                       (getattr(runtime, "_Xi", []) or [], getattr(runtime, "_Yi", []) or [], "s")):
            for _i, _x in enumerate(_buf_x):
                act16.ABLAGE_FIX = False
                _alt = np.asarray(act16.reactive_subgoal(_x), float)
                act16.ABLAGE_FIX = True
                _neu = np.asarray(act16.reactive_subgoal(_x), float)
                if not np.allclose(_alt, _neu) and not np.allclose(np.asarray(_buf_y[_i], float), _neu):
                    #   nur noch NICHT korrigierte Zeilen -- sonst traenierte jeder GUI-Start nach
                    _buf_y[_i] = _neu
                    if _zaehl == "d":
                        _n_d += 1
                    else:
                        _n_s += 1
        print(f"  [Ablage] Teacher-Korrektur (ACT16_ABLAGE_FIX): {_n_d} DAgger- und {_n_s} "
              f"Selbst-Imitationszeilen neu etikettiert; Policy wird nachtrainiert", flush=True)
        if _n_d + _n_s:
            runtime.train(epochs=400)
    aufgeben_kopf = (_loaded or {}).get("aufgeben_kopf") or AufgebenKopf()
    if not isinstance(aufgeben_kopf, AufgebenKopf):
        aufgeben_kopf = AufgebenKopf()
    if AUFGEBEN:
        if not D0_FREEZE:
            aufgeben_kopf.lernen()
        print(f"  [Aufgeben] Kopf mit {len(aufgeben_kopf.y)} Momentaufnahmen -- "
              + ("entscheidet" if aufgeben_kopf.bereit else "sammelt noch (entscheidet noch nicht)"), flush=True)
    griff_kopf = GriffKopf()                       # Stufe 1: nur sammeln, nicht persistiert
    loslass_kopf = (_loaded or {}).get("loslass_kopf") or LoslassKopf()
    if not isinstance(loslass_kopf, LoslassKopf):
        loslass_kopf = LoslassKopf()
    if LOSLASS_KOPF and not D0_FREEZE:
        if not act16.ABLAGE_FIX:
            print("  [Loslassen] WARNUNG: ACT23_LOSLASS_KOPF ohne ACT16_ABLAGE_FIX -- die Teacher-"
                  "Etiketten am Ziel widersprechen sich, der Kopf lernt Unsinn", flush=True)
        _ok = loslass_kopf.lernen(runtime._X, runtime._Y)
        print(f"  [Loslassen] Loslass-Kopf {'gelernt' if _ok else 'NICHT gelernt (zu wenig Zeilen)'} "
              f"aus {loslass_kopf.n_fit} Halte-Zustaenden -- er entscheidet im Netzbetrieb das "
              f"Loslassen", flush=True)
    # SELBST-IMITATION BEREINIGEN (ACT23_IMIT_UMETIKETT, Vorgabe 0).  Der Puffer traegt die Wuensche
    # der Policy VOR dem Riegel (s. pc_act16.IMIT_AUSGEFUEHRT).  Einmalig beim Laden: wo der Riegel
    # gegriffen HAETTE -- Hand ueber dem ruhenden Objekt, Klaue offen, mehr als 12 mm ueber dem
    # Greifpunkt --, wird das Etikett auf "offen" gesetzt, also auf das, was ausgefuehrt wurde.
    # Danach einmal nachtrainieren.  Trainingsdaten-Geruest, keine Laufzeitregel.
    if not D0_FREEZE and os.environ.get("ACT23_IMIT_UMETIKETT", "0") == "1" and getattr(runtime, "_Xi", None):
        _n = 0
        for _x, _y in zip(runtime._Xi, runtime._Yi):
            _x = np.asarray(_x, float)
            _hg = max(0.0, float(_x[14]) - act16.GRASP_Z) if len(_x) > 14 else 0.0
            _gz = float(_x[9]) + act16.GRASP_OFFSET + _hg
            if (float(np.linalg.norm(_x[0:2] - _x[3:5])) < act16.NEAR and float(_x[5]) < 0.02
                    and float(_x[8]) > 0.45 and float(_x[2]) > _gz + 0.012 and float(_y[3]) < act16.J5_OPEN):
                _y[3] = act16.J5_OPEN; _n += 1
        print(f"  [Selbst-Imitation] {_n} von {len(runtime._Xi)} Etiketten bereinigt (vom Riegel "
              f"abgefangene Schliesswuensche -> offen); Policy wird nachtrainiert", flush=True)
        if _n:
            runtime.train(epochs=400)
    _n_rt = runtime.ensure_state_dim(13) if hasattr(runtime, "ensure_state_dim") else 0
    if _n_rt:
        # TASTSINN-Migration (11 -> 13): das Netz wird in ensure_state_dim mit NULL-Spalten
        # VERBREITERT (Ausgabe bitgleich, kein Retrain noetig); die Lifelong-Refits lernen die
        # Druckspalten allmaehlich aus den neuen Demos.
        print(f"  [Schema] Tastsinn in der Runtime-Policy ergaenzt: {_n_rt} Zeilen migriert "
              f"(gueltig-Flag 0), Netz verhaltensneutral auf 13 Eingaenge verbreitert", flush=True)
    # ABLAGEHOEHE-Migration (13 -> 14), Stufe 2 von wiki/fragen/stapeln-als-aufgabe.md.
    # DER NEUTRALWERT IST HIER KEINE NOTLUEGE.  Beim Tastsinn musste ein Gueltigkeits-Flag mit,
    # weil der Druck in den alten Episoden zwar PHYSISCH da war, aber nicht aufgezeichnet wurde --
    # "0 N" zu behaupten waere die Luege "Klaue leer" gewesen.  Die Ablagehoehe dagegen WAR in
    # jeder alten Episode GRASP_Z: die Ablagephase zielte auf genau diese Konstante.  Die alten
    # Zeilen bekommen also ihren wahren Wert, nicht einen erfundenen, und brauchen kein Flag.
    _n_tz = (runtime.ensure_state_dim(14, neutral=(act16.GRASP_Z,))
             if (act16.GOAL_Z or act16.GRIFF_Z) and hasattr(runtime, "ensure_state_dim") else 0)
    if _n_tz:
        print(f"  [Schema] Ablagehoehe in der Runtime-Policy ergaenzt: {_n_tz} Zeilen migriert "
              f"(Wert {act16.GRASP_Z}, der in ihren Episoden GALT), Netz verhaltensneutral auf "
              f"14 Eingaenge verbreitert", flush=True)
    # GREIFHOEHE-Migration (Stufe 4, ACT16_GRIFF_Z).  Dieselbe Begruendung wie bei der
    # Ablagehoehe: in JEDER alten Episode wurde auf GRASP_Z gegriffen, die alten Zeilen bekommen
    # also ihren wahren Wert und brauchen kein Gueltigkeits-Flag.
    # DIE ZIELBREITE HAENGT AN GOAL_Z: mit ihm ist die Greifhoehe die 15., ohne ihn die 14. Spalte.
    # Der Zustandsvektor wird in derselben Reihenfolge gebaut (erst tgt_z, dann griff_z), also
    # muss die Migration hier genauso rechnen -- sonst landet die Greifhoehe in der Spalte der
    # Ablagehoehe und die Policy liest eine Groesse als die andere.
    _breit = 15                    # s. den Kommentar im Zustandsvektor: GRIFF_Z zieht die
    #   Ablagespalte immer mit, damit die Anordnung eindeutig bleibt
    _n_gz = (runtime.ensure_state_dim(_breit, neutral=(act16.GRASP_Z,))
             if act16.GRIFF_Z and hasattr(runtime, "ensure_state_dim") else 0)
    if _n_gz:
        print(f"  [Schema] Greifhoehe in der Runtime-Policy ergaenzt: {_n_gz} Zeilen migriert "
              f"(Wert {act16.GRASP_Z}, der in ihren Episoden GALT), Netz verhaltensneutral auf "
              f"{_breit} Eingaenge verbreitert", flush=True)

    # STAGE 3 (user request): OPEN-SET COLOURS -- fully self-labelled, no teacher colour set anywhere.
    # Scene glances feed component CHROMATICITIES; classes are self-named ("farbe-N") and bound to the
    # body they were discovered on (plumbing aid, like the form registration).  Concrete de-crutching:
    # the LONG object is localised by its self-labelled colour class instead of privileged sim access.
    # OPTIONAL blob keys (old saves load fine without them -- no schema bump, the user's running
    # lifelong state survives).
    colours = (_loaded.get("colours") if _loaded is not None else None) or ColourOpenSetModule()
    # AUSWAHL NACH EIGENSCHAFTEN verdrahten.  Die Werte kommen aus dem, was der Agent SELBST
    # benannt hat: die Farbklassen aus dem Farb-Openset, die Formklassen aus den trainierten
    # plus den selbst gelernten, die Groessenbaender aus der Messung.  Nichts davon ist
    # vorgegeben -- es ist der Wortschatz, den er sich erworben hat.
    def _eig_werte():
        farben = sorted(getattr(colours, "classes", {}) or {})
        formen = list(getattr(shape_clf, "all_names", lambda: [])())
        return (farben, formen, [b[0] for b in GROESSEN_BAENDER])

    def _eig_setzen(farbe, form, groesse):
        """Tripel -> Kommando.  Gibt eine kurze Rueckmeldung fuer die Statuszeile zurueck."""
        pos, det, tr = finde_nach_eigenschaften(sim, shape_clf, colours, farbe, form, groesse)
        if pos is None:
            return "kein Treffer"
        # Buchfuehrung: welcher Koerper liegt dort?  NUR fuer Bewertung und Szenenverwaltung --
        # die Lokalisierung selbst hat den Namen nicht gebraucht.
        _kand = [nm for _l, nm, _m in CommandState23.OBJECTS] + list(state.SHAPE_KEY) + [NOVEL_BODY]
        _kand = [k for k in dict.fromkeys(_kand) if k]
        body = min(_kand, key=lambda o: float(np.linalg.norm(sim.obj_pos(o)[:2] - pos)))
        k = state.add_eigenschaft(body, farbe, form, groesse)
        state.sel = k
        panel._eig_werte = _eig_werte()
        mehr = f", {len(tr)} Treffer (mehrdeutig!)" if len(tr) > 1 else ""
        return f"-> {body} bei {np.round(pos, 3).tolist()}{mehr}"

    def _farb_rgb(name):
        """Der selbst gelernte Prototyp einer Farbklasse als darstellbares RGB.

        classes[name]["mu"] ist eine HELLIGKEITSNORMIERTE Chroma (die drei Anteile summieren sich
        zu ~1), also als Bildschirmfarbe zu dunkel.  Auf das Maximum normiert bleibt der Farbton
        unveraendert und wird sichtbar.  Kein Farbwert wird erfunden -- es ist der Mittelwert
        ueber alle Sichtungen, die der Agent dieser Klasse zugeordnet hat.
        """
        cl = (getattr(colours, "classes", {}) or {}).get(name)
        if cl is None:
            return None
        mu = np.clip(np.asarray(cl["mu"], float), 0.0, None)
        m = float(mu.max())
        return tuple((mu / m).tolist()) if m > 1e-6 else None

    if panel is not None:
        panel._eig_werte = _eig_werte()
        panel._eig_fn = _eig_setzen
        panel._farb_rgb = _farb_rgb
        for _k in range(3):
            panel._eig_beschriften(_k)

    def _adresse_wuerfeln(werte, mess, p, ident=None, start=None):
        """Aus (Farbe, Form, Groesse) die KUERZESTE Adresse wuerfeln, die den Koerper bei `p` trifft.

        EINE FASSUNG FUER ALLE ADRESSQUELLEN -- die Auto-Schleife (_auto_eig_umschreiben) und die
        Direkt-Adressierung (_direkt_adressieren).  Warum extra: die Auto-Schleife hat dieselbe
        Logik schon einmal in zwei Kopien getragen (kopflos und GUI), und die GUI-Kopie fehlte
        332 Episoden lang unbemerkt.  Zweimal derselbe Riss an derselben Naht war genug.

        Gibt das Tripel zurueck (None, wo eine Achse verschwiegen wird) oder None, wenn keine
        VERFOLGBARE Achse zur Verfuegung steht.  `mess` traegt die Messwerte derselben drei
        Achsen; sie werden nur bei ACT23_EIG_STETIG verglichen.

        `start` setzt die Achsen, mit denen begonnen wird, statt sie zu wuerfeln (s.
        ACT23_EIG_DIREKT_FORM); nachgelegt wird danach wie immer, bis die Adresse eindeutig ist.

        `p` ist die Lage, auf die die Adresse zeigen SOLL, und `ident` erzwingt, dass sie das auch
        tut (None = wie ACT23_EIG_IDENT).  Die Auto-Schleife uebergibt dort die wahre Koerperlage
        und laesst den Schalter entscheiden; die Direkt-Adressierung uebergibt die DETEKTION, aus
        der sie die Adresse gebildet hat, und prueft immer -- dort ist die Pruefung damit voellig
        unprivilegiert ("findet die Adresse dasselbe wieder, was ich gerade gesehen habe?") und
        sie muss sitzen, weil eine Direkt-Adresse den ganzen Lauf ueber stehen bleibt.
        """
        _verfolgbar = [i for i in (0, 1) if werte[i] is not None]
        if not _verfolgbar:
            return None
        # IMMER WUERFELN, auch wenn ein Startpunkt gesetzt ist -- und zwar GENAU dieselben Zuege.
        # WARUM (gemessen, und es haette das ganze A/B verdorben): verbraucht ein Arm drei
        # Zufallszahlen weniger als der andere, laufen beide ab diesem Moment auseinander, ohne
        # dass der Schalter eine einzige ENTSCHEIDUNG anders getroffen haette.  Im ersten Anlauf
        # divergierten die Arme ab Episode 8, obwohl die erste Adresse in beiden zeichengleich war
        # -- und obj_X wurde dann auf ZWEI VERSCHIEDENEN Detektionen adressiert (569 gegen 924 px).
        # Damit haette der Vergleich die Szene gemessen statt die Achse.
        _wurf = [bool(crng.integers(2)) for _ in range(3)]
        if not any(_wurf[i] for i in _verfolgbar):
            _wurf[_verfolgbar[int(crng.integers(len(_verfolgbar)))]] = True
        _mk = list(start) if start is not None else _wurf
        if not any(_mk[i] for i in _verfolgbar):
            return None               # Startpunkt nennt keine verfolgbare Achse -> blinde Adresse
        _sv = sim.d.mocap_pos.copy()      # die Suche PARKT die Marker (_park_markers); ohne
        for _versuch in range(4):         # Rueckgabe liefert goal_fn ein GEPARKTES Ziel
            _tri = tuple(w if m else None for w, m in zip(werte, _mk))
            _pos2, _, _tr2 = finde_nach_eigenschaften(sim, shape_clf, colours, *_tri,
                                                      mess=(mess if EIG_STETIG else None))
            # IDENTITAET, nicht nur Anzahl (s. EIG_IDENT oben): der eine Treffer muss auf dem
            # gemeinten Koerper sitzen.  Ohne das gilt eine Adresse als eindeutig, die genau ein
            # FREMDES Objekt trifft -- gemessen 316 von 318 "eindeutig" bei 8,8 % groben Fehlern.
            _trifft = True
            if (EIG_IDENT if ident is None else ident) and _pos2 is not None:
                _trifft = float(np.linalg.norm(np.asarray(_pos2, float) - p)) < 0.02
            if len(_tr2) <= 1 and _trifft:
                break
            _fehlt = [i for i in range(3) if not _mk[i] and werte[i] is not None]
            if not _fehlt:
                break                     # alle Achsen genannt und trotzdem mehrdeutig
            _mk[_fehlt[int(crng.integers(len(_fehlt)))]] = True
        sim.d.mocap_pos[:] = _sv          # gemessen: sonst 627-968 mm Endabstand
        mujoco.mj_forward(sim.m, sim.d)
        return _tri

    def _auto_eig_umschreiben():
        """Die ADRESSIERUNG des gewaehlten Koerpers in ein Eigenschafts-Tripel umschreiben.

        EINE Fassung fuer BEIDE Auto-Schleifen -- die kopflose (ACT23_AUTO_N) und die der GUI.
        DER FEHLER, DER DAZU GEFUEHRT HAT: der erste Einbau stand nur in der kopflosen Schleife,
        im GUI-Lauf war ACT23_AUTO_EIG damit WIRKUNGSLOS (vom Nutzer gemeldet 2026-09-05: "die
        Knoepfe bleiben alle auf beliebig stehen").  Meine 10-Episoden-Pruefung lief ausgerechnet
        in der kopflosen Schleife und sah deshalb sauber aus.  Die GUI-Auto-Schleife hat GENAU
        DIESEN Fehler schon einmal getragen -- NOVEL_EVERY/SCENE_EVERY waren dort 332 Episoden
        lang ohne Wirkung (s. Kommentar in der GUI-Schleife).  Zweimal derselbe Riss an derselben
        Naht: deshalb jetzt EINE Fassung statt zweier Kopien.

        NICHT die Auswahl wird angefasst, nur die Benennung: die Neugier bestimmt weiterhin,
        WELCHES Objekt geuebt wird.  Das Tripel kommt aus der Detektion, die auf dem gewaehlten
        Koerper sitzt -- es beschreibt also garantiert etwas Sichtbares.  Welche der drei Achsen
        genannt werden, wuerfelt mit (mindestens eine), damit auch UNVOLLSTAENDIGE Angaben geuebt
        werden ("das duenne Ding" statt "das duenne violette Kreuz").
        """
        if not AUTO_EIG or _uebung["body"] is not None:   # namenlose Uebung nicht umetikettieren
            return None
        _b = state.selected()[1]
        _sm = sim.d.mocap_pos.copy()
        _ds = [d for d in shape_clf.perceive_all(sim)
               if d.get("pos") is not None and float(d.get("area", 0)) >= 200.0]
        sim.d.mocap_pos[:] = _sm; mujoco.mj_forward(sim.m, sim.d)
        _p = sim.obj_pos(_b)[:2]
        _nah = min(_ds, key=lambda d: float(np.linalg.norm(
            np.asarray(d["pos"], float) - _p)), default=None)
        if _nah is None or float(np.linalg.norm(np.asarray(_nah["pos"], float) - _p)) >= 0.04:
            return None                                  # nichts Sichtbares auf dem Koerper
        _f = colours.classify(_nah["chroma"])[0] if _nah.get("chroma") is not None else None
        _fo, _g = _nah.get("shape"), groessen_band(_nah.get("dicke"), _nah.get("span"))
        # EINDEUTIGKEIT ERZWINGEN.  Gemessen: eine Angabe wie "mittel" allein passt auf DREI
        # Objekte (alle heutigen Koerper liegen in diesem Band), und der Aufloeser nimmt dann das
        # flaechengroesste -- in einer Auto-Episode das falsche, 152 mm daneben.  Ein Kommando,
        # das sein Objekt nicht identifiziert, ist keine Uebung, sondern Rauschen.  Also Achsen
        # nachlegen, bis genau EIN Treffer bleibt; unvollstaendige Angaben bleiben dort, wo sie
        # AUSREICHEN -- geuebt wird die kuerzeste Adresse, die trifft.
        # DIE GROESSE IST EIN ZUSATZ, KEINE ADRESSE.  Nutzervorgabe 2026-09-05: "Reine
        # Groessen-Adressen brauchen wir, auch nur zur Uebung, nicht.  Wenn ich etwas von aussen
        # vorgebe, wuerde ich immer sagen 'der grosse Wuerfel' oder 'der gelbe Wuerfel' oder 'der
        # Wuerfel'.  Aber nie 'das groesste Objekt'."  Also muss mindestens eine der beiden
        # VERFOLGBAREN Achsen (Farbe, Form) genannt sein -- das sind zugleich genau die, denen die
        # Fovea folgen kann (s. eig_servo).  Ist keine von beiden vorhanden, wird gar nicht
        # umgeschrieben: dann bleibt das Kommando beim Namen, statt eine blinde Adresse zu bauen.
        # DIE MESSWERTE DERSELBEN DREI ACHSEN, aus derselben Detektion -- die Adresse beschreibt
        # damit garantiert etwas Gesehenes, genau wie die Namen darueber.
        _mess = (np.asarray(_nah["chroma"], float) if _nah.get("chroma") is not None else None,
                 np.asarray(shape_clf.desc_embed(_nah["desc"]), float)
                 if _nah.get("desc") is not None else None,
                 float(_nah["span"]) if _nah.get("span") is not None else None)
        # ... UND DIE FORMACHSE OHNE KLASSE, wenn EIG_DIREKT laeuft (s. dort).  Ohne das wuerde die
        # Auto-Schleife eine Direkt-Adresse in der naechsten Episode um genau die Achse ERLEICHTERN,
        # die sie ueberhaupt erst moeglich gemacht hat: resolve() liefert fuer den klassenlosen
        # Koerper weiter None, das Tripel fiele auf Farbe und Groesse zurueck.
        if EIG_DIREKT and EIG_STETIG and _fo is None and _mess[1] is not None:
            _fo = EIG_GESEHEN
        _werte = (_f, _fo, _g)
        _tri = _adresse_wuerfeln(_werte, _mess, _p)
        if _tri is None:
            return None
        state.sel = state.add_eigenschaft(_b, *_tri)
        state.EIG_MESS[_b] = _mess          # dieselben Achsen, als Messwert (s. EIG_STETIG)
        if panel is not None:
            panel._eig_werte = _eig_werte()    # waehrend des Laufs geborene Klassen nachziehen
            panel.zeige_eigenschaft(*_tri, verfuegbar=_werte)   # genannt UND was verschwiegen wurde
        return _tri

    def _ziel_aufloesen(bez):
        """Das Ablageziel aus der WAHRNEHMUNG aufloesen (s. ZIEL_ADRESSE).

        Genau derselbe Weg wie beim Objekt: finde_nach_eigenschaften ueber die Kamera, kein
        sim.obj_pos.  Zurueck kommt eine Stelle NEBEN dem Bezugskoerper, ZIEL_ABSTAND entfernt,
        auf der ersten erreichbaren der gewuerfelten Peilungen.

        ZWEI TORE, beide schon anderswo gemessen:
          * MEHRDEUTIG IST NICHT GEFUNDEN.  Passt die Adresse auf mehrere Detektionen, wird
            NICHT die flaechengroesste genommen -- genau das hat in der Objekt-Adressierung
            152 mm danebengegriffen (s. _auto_eig_umschreiben).  Ein Ziel, das seinen Bezug
            nicht identifiziert, faellt auf den Marker zurueck.
          * DIE MARKER MUESSEN ZURUECK.  perceive_all parkt sie (_park_markers); ohne
            Wiederherstellung liefert der Rueckfall marker_xy() eine GEPARKTE Koordinate.
            Dieselbe Falle wie in _adresse_wuerfeln, deshalb dasselbe Sichern/Zuruecklegen.
        """
        from pc_cvnn.pc_act14 import REACH_XY
        from pc_cvnn.pc_act16 import BASE_CLEAR
        _sm = sim.d.mocap_pos.copy()
        try:
            _p, _det, _tr = finde_nach_eigenschaften(sim, shape_clf, colours, *bez["tripel"],
                                                     mess=(bez["mess"] if EIG_STETIG else None))
        finally:
            sim.d.mocap_pos[:] = _sm
            mujoco.mj_forward(sim.m, sim.d)
        bez["aufgeloest"] = False                        # s. Stapel-Urteil in der Ablage-Zeile
        if _p is None or len(_tr) != 1:
            print(f"    [Zieladresse] '{bez['label']}': "
                  f"{'mehrdeutig, ' + str(len(_tr)) + ' Treffer' if _tr else 'nicht gefunden'}"
                  f" -- Rückfall auf Ziel {state.target_idx + 1}", flush=True)
            return None
        if bez.get("relation") == "auf":
            # AUF: das Ziel IST die Stelle des Bezugskoerpers -- keine Peilung, kein Abstand.  Dafuer
            # kommt eine dritte Groesse dazu, die HAND-Ablagehoehe (s. ZIEL_RELATION oben):
            #     GRASP_Z + Oberkante des Bezugskoerpers
            # Die Oberkante ist das einzige Privileg auf diesem Pfad -- Teacher-Geruest, weil eine
            # Ebenen-Homographie keine Hoehe hergibt.  Sie steht NICHT im Ziel-Latent und nicht in
            # der Adresse; sie geht ueber tgt_z in die Ablagephase und (mit ACT16_GOAL_Z) in den
            # Zustandsvektor, damit die Policy sie lernen KANN.
            _bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, bez["body"])
            _wahr_oben = float(sim.obj_pos(bez["body"])[2]
                               + sim.m.geom_size[sim.m.body_geomadr[_bid]][2])
            # ERST SCHAETZEN, DANN MERKEN (s. HoehenSchaetzer).  Andersherum stuende die eben
            # gemerkte Zeile im eigenen Fit, und der berichtete Fehler waere geschoent.  Ganz
            # aussen vor ist die Stelle damit nicht -- spaetere Episoden an derselben Stelle
            # gehen ein; die stellenweise gehaltene Zahl steht in der Sonde, nicht hier.
            _geschaetzt = hoehen_schaetzer.schaetzen(_det)
            # GELERNT WIRD NUR VON EINER AUFLAGE, DIE DER AGENT SELBST FUER EIN DING HAELT.
            # Nach dem ersten gelungenen Stapel bleibt das Objekt oben liegen (die Aufraeumschleife
            # stellt nur NICHT-kommandierte Koerper zurueck), der Blob ist verschmolzen und seine
            # Flaeche waere ein FALSCHES Beispiel: groesser, aber die Auflage ist gleich hoch
            # geblieben.
            #
            # DER MASSSTAB IST DIE EINZELFLECK-SKALA, NICHT _merge_th.  Heute gemessen
            # (wiki/befunde/selbstrichter-stapel.md): `_merge_th` ist das 0,995-Quantil und sitzt
            # bei 0,339, waehrend eine Auflage MIT Wuerfel im Median nur 0,20 liest -- als Tor
            # liesse es drei von vier verschmolzenen Bloecken durch.  Richtig ist der uebliche
            # Bereich eines EINZELNEN Flecks: Median + (95er - Median) der eigenen Bezugswerte,
            # im gelernten Zustand 0,085 + 0,035 = 0,120, gegen eine leere Auflage bei 0,073-0,079.
            _cs0 = _det.get("cspread")
            _ref = getattr(shape_clf, "_cs_ref", None)
            if _cs0 is None:
                _eins = True
            elif _ref is not None and len(_ref) >= 12:
                _rr = np.asarray(_ref, float)
                _eins = float(_cs0) <= float(np.quantile(_rr, 0.5)) + float(
                    np.quantile(_rr, 0.95) - np.quantile(_rr, 0.5))
            else:
                _eins = float(_cs0) <= shape_clf._merge_th()      # kein eigener Bezug -> grob
            # DIE MERKMALE AUFHEBEN.  Beim Tasten faellt das Etikett erst am Episodenende, die
            # Detektion gibt es aber nur JETZT (danach steht das Objekt auf der Auflage und der
            # Blob ist verschmolzen).  Also hier merken, dort lernen.
            bez["_det_hoehe"] = {"area": _det.get("area"), "dicke": _det.get("dicke"),
                                 "pos": (None if _det.get("pos") is None
                                         else np.asarray(_det["pos"], float).copy())}
            bez["_eins"] = bool(_eins)
            bez["_wahr_oben"] = float(_wahr_oben)
            if (not _eins) and HOEHE_BELEGT and _tast_stand.get(bez["body"]) is not None:
                # DAS BELEGTE AUSSEHEN, mit dem Etikett der Episode, in der es ertastet wurde.
                # Genau diese Verteilung bekommt der Schaetzer beim Abstapeln vorgelegt, und nur
                # sie fehlte ihm (gemessen: auf leer gelernt -> auf belegt 34 %, also Grundrate).
                # PRUEFSTEIN: die belegte Auflage ist dieselbe Silhouette plus der Koerper, ihre
                # Flaeche darf also nicht deutlich KLEINER sein als die leere.  Sonst war der
                # Blob ein anderes Ding.
                _st = _tast_stand[bez["body"]]
                # DIE ADRESSE TRIFFT BEI BELEGTER AUFLAGE OFT DEN KLEINEN TEIL -- gemessen 239 px,
                # wo die leere Auflage 1236 hatte: `finde_nach_eigenschaften` waehlt nach dem
                # Eigenschafts-Tripel, und nach dem Schnitt passt der obere Koerper mitunter
                # besser.  Fuer den Schaetzer ist aber die AUFLAGE gemeint, also der groessere
                # Teil des Paares.  Hier steht der Arm zu Hause, das Paar ist also sichtbar.
                _dl = _det
                _pb, _ = _stapel_paar()
                if _pb is not None:
                    _dl = _pb[0]
                _af = _dl.get("area")
                if _af is not None and _st.get("area") and _af < 0.5 * float(_st["area"]):
                    print(f"    [Hoehe] belegtes Aussehen VERWORFEN: {_af:.0f}px gegen leer "
                          f"{float(_st['area']):.0f}px -- nicht dieselbe Auflage", flush=True)
                elif not D0_FREEZE and hoehen_schaetzer.merken(_dl, float(_st["oben"])):
                    print(f"    [Hoehe] belegtes Aussehen gelernt: {_af:.0f}px (leer war "
                          f"{float(_st['area']):.0f}px), Etikett {1000 * _st['oben']:.1f}mm "
                          f"aus der Tast-Episode ({len(hoehen_schaetzer.X)} Zeilen)", flush=True)
            elif not D0_FREEZE and _eins and not HOEHE_TASTEN:
                hoehen_schaetzer.merken(_det, _wahr_oben)
            elif not _eins:
                print(f"    [Hoehe] Auflage sieht belegt aus (Farbstreuung {float(_cs0):.3f}) -- "
                      f"KEIN Lernbeispiel", flush=True)
            _oben = _wahr_oben
            if HOEHE_SEHEN:
                if _geschaetzt is None:
                    print(f"    [Hoehe] noch kein Schaetzer ({len(hoehen_schaetzer.X)} von "
                          f"{HoehenSchaetzer.MIN_ZEILEN} Zeilen) -- RUECKFALL auf das Privileg",
                          flush=True)
                else:
                    _oben = float(_geschaetzt)
            if _geschaetzt is not None:
                print(f"    [Hoehe] gesehen {1000 * _geschaetzt:.1f}mm, wahr "
                      f"{1000 * _wahr_oben:.1f}mm, Fehler {1000 * (_geschaetzt - _wahr_oben):+.1f}mm"
                      f"  ({len(hoehen_schaetzer.X)} Zeilen"
                      f"{', BENUTZT' if HOEHE_SEHEN else ', nur mitgelernt'})", flush=True)
            _tz = float(act16.GRASP_Z) + _oben
            _wahr = 1000.0 * float(np.linalg.norm(_p - sim.obj_pos(bez["body"])[:2]))
            print(f"    [Zieladresse] '{bez['label']}' 1 Treffer bei "
                  f"[{_p[0]:+.3f},{_p[1]:+.3f}] (wahr {_wahr:.0f}mm) -> DARAUF ablegen, "
                  f"Oberkante {1000 * _oben:.0f}mm, Handhoehe {1000 * _tz:.0f}mm"
                  + ("" if act16.GOAL_Z else "  [ACT16_GOAL_Z=0: die Hoehe wird VERWORFEN]"),
                  flush=True)
            bez["aufgeloest"] = True
            # WIE DIE AUFLAGE LEER AUSSIEHT -- der Bezugswert fuer das Stapel-Selbsturteil.
            # Beides stammt aus DIESER Detektion, also aus der Wahrnehmung des Agenten, und wird
            # am Episodenende mit dem verglichen, was dann am Zielort steht (s. _selbst_stapel).
            bez["area0"] = float(_det.get("area")) if _det.get("area") is not None else None
            bez["cspread0"] = (float(_det["cspread"]) if _det.get("cspread") is not None else None)
            bez["ziel_xy"] = np.asarray(_p, float).copy()
            return np.array([_p[0], _p[1], _tz], float)
        if bez.get("relation") == "richtung":
            # EINE Peilung, die des Wortes -- an der WAHRGENOMMENEN Stelle des Bezugs.
            _dw, _quelle = _wort_richtung(bez["wort"], _p)
            if _dw is not None:
                _q = _p + ZIEL_ABSTAND * _dw
                if (REACH_XY[0][0] <= _q[0] <= REACH_XY[1][0] and REACH_XY[0][1] <= _q[1] <= REACH_XY[1][1]
                        and float(np.linalg.norm(_q)) >= BASE_CLEAR):
                    _wahr = 1000.0 * float(np.linalg.norm(_p - sim.obj_pos(bez["body"])[:2]))
                    print(f"    [Zieladresse] '{bez['label']}' 1 Treffer bei "
                          f"[{_p[0]:+.3f},{_p[1]:+.3f}] (wahr {_wahr:.0f}mm) -> {bez['wort']}: "
                          f"Richtung ({_dw[0]:+.2f},{_dw[1]:+.2f}) [{_quelle}], ablegen bei "
                          f"[{_q[0]:+.3f},{_q[1]:+.3f}]", flush=True)
                    bez["aufgeloest"] = True
                    bez["ziel_xy"] = np.asarray(_p, float).copy()
                    bez["ziel_rel"] = np.asarray(_q, float) - np.asarray(_p, float)   # fuer die Wahrheit
                    return _q
            print(f"    [Zieladresse] '{bez['label']}': Richtung nicht erreichbar -- "
                  f"Rückfall auf Ziel {state.target_idx + 1}", flush=True)
            return None
        for _ph in bez["peilungen"]:
            _q = _p + ZIEL_ABSTAND * np.array([np.cos(_ph), np.sin(_ph)])
            if (REACH_XY[0][0] <= _q[0] <= REACH_XY[1][0] and REACH_XY[0][1] <= _q[1] <= REACH_XY[1][1]
                    and float(np.linalg.norm(_q)) >= BASE_CLEAR):
                # "wahr" ist AUSSCHLIESSLICH Protokoll: wie weit die wahrgenommene Stelle des
                # Bezugskoerpers von seiner echten abweicht.  Der Wert geht in keine Entscheidung,
                # in kein Ziel und in keinen Lernenden -- ohne ihn waere im Log aber nicht zu
                # trennen, ob eine danebengegangene Ablage an der Adresse oder am Arm lag.
                _wahr = 1000.0 * float(np.linalg.norm(_p - sim.obj_pos(bez["body"])[:2]))
                print(f"    [Zieladresse] '{bez['label']}' 1 Treffer bei "
                      f"[{_p[0]:+.3f},{_p[1]:+.3f}] (wahr {_wahr:.0f}mm) -> ablegen daneben bei "
                      f"[{_q[0]:+.3f},{_q[1]:+.3f}]", flush=True)
                bez["aufgeloest"] = True                 # fuer das Richtungs-Etikett am Ende
                bez["ziel_xy"] = np.asarray(_p, float).copy()
                bez["ziel_rel"] = np.asarray(_q, float) - np.asarray(_p, float)   # fuer die Wahrheit
                return _q
        print(f"    [Zieladresse] '{bez['label']}' gefunden, aber keine erreichbare Ablage daneben"
              f" -- Rückfall auf Ziel {state.target_idx + 1}", flush=True)
        return None

    state.ziel_loeser = _ziel_aufloesen

    def _selbst_stapel(jdets, bez, det0):
        """DER AGENT BEURTEILT SEINEN EIGENEN STAPEL -- ohne privilegierte Hoehe.

        Das Problem, das dahintersteht: ein gestapelter Koerper ist fuer diese Kamera UNSICHTBAR.
        Er liegt vollstaendig innerhalb der Silhouette der Auflage, die Flaeche aendert sich um kein
        Pixel (gemessen 0 von 25, wiki/befunde/sockel-verschluckt-den-stapel.md).  Der gewoehnliche
        Selbstrichter sucht den Blob AM ABLAGEPUNKT und findet dort die Auflage -- er sagt deshalb
        auch bei Fehlablagen "geliefert" (6 von 9, wiki/befunde/stapeln-gemessen.md).

        WAS STATTDESSEN TRAEGT: die FARBSTREUUNG des Auflagen-Blobs.  Leer 0,069, belegt 0,149 bis
        0,397 -- ueber 150 Faelle ohne einen Ueberlapp.  Und der Massstab dafuer ist NICHT von mir
        gesetzt: `_merge_th()` ist das 0,995-Quantil der Farbstreuung, die der Agent an seinen
        EIGENEN Einzelobjekt-Sichtungen gemessen hat.  Liegt der Blob darueber, enthaelt er mehr
        als ein Ding.

        UND WIE MAN "DRAUF" VON "DANEBEN VERSCHMOLZEN" TRENNT, ebenfalls ohne erfundene Schwelle:
        zwei nebeneinander verschmolzene Koerper haben die SUMME der Flaechen, ein Stapel hat die
        der Auflage allein.  Beide Bezugswerte kennt der Agent -- die leere Auflage aus der
        Adressaufloesung (bez["area0"]), die eigene Objektflaeche aus der Startdetektion (det0).
        Verglichen wird, welcher der beiden naeher liegt.

        Gibt (drauf, grund) zurueck, oder (None, grund) wenn er sich ehrlich enthalten muss.
        """
        _mth = shape_clf._merge_th()
        if _mth is None:
            return None, "kein eigener Verschmelzungs-Massstab"
        if bez.get("area0") is None or bez.get("ziel_xy") is None:
            return None, "Auflage beim Adressieren nicht vermessen"
        _z = np.asarray(bez["ziel_xy"], float)
        _k = [d for d in jdets if d.get("pos") is not None and d.get("cspread") is not None
              and d.get("area") is not None]
        if not _k:
            return None, "nichts gesehen"
        _b = min(_k, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"], float) - _z)))
        _dz = float(np.linalg.norm(np.asarray(_b["pos"], float) - _z))
        if _dz > 0.05:
            return False, f"Auflage nicht wiedergefunden ({1000 * _dz:.0f}mm)"
        _cs, _a, _a0 = float(_b["cspread"]), float(_b["area"]), float(bez["area0"])
        # DER BEZUGSWERT IST DIE EIGENE LEERE AUFLAGE, nicht ein globaler Massstab.
        # WARUM (gemessen, wiki/befunde/selbstrichter-stapel.md): `_merge_th()` beantwortet die
        # Frage "was ueberschreitet ein EINZELNES Objekt praktisch nie" und liegt bei 0,34.  Ein
        # Sockel mit Wuerfel liest 0,20 -- er sieht aus wie ein buntes Einzelobjekt und blieb
        # darunter, in 14 von 14 Fehlanzeigen.  An DERSELBEN Auflage ist der Sprung dagegen gross:
        # leer 0,07 gegen belegt 0,20.
        # DER MASSSTAB FUER "DEUTLICH" IST EBENFALLS GEMESSEN, nicht gesetzt: wie weit die
        # Farbstreuung eines EINZELNEN Flecks ueblicherweise streut, steht in denselben
        # Bezugswerten, aus denen _merge_th sein Quantil zieht (`shape_clf._cs_ref`).  Genommen wird
        # der Abstand vom Mittelwert zum 95er-Quantil -- gestiegen um mehr als das heisst: mehr als
        # die uebliche Schwankung eines einzelnen Flecks.
        _ref = getattr(shape_clf, "_cs_ref", None)
        _spanne = None
        if _ref is not None and len(_ref) >= 12:
            _rr = np.asarray(_ref, float)
            _spanne = float(np.quantile(_rr, 0.95) - np.quantile(_rr, 0.5))
        _cs0 = bez.get("cspread0")
        if _cs0 is not None and _spanne is not None:
            _traegt = _cs > float(_cs0) + _spanne
            _wieT = (f"Farbstreuung {_cs:.3f} gegen eigene leere Auflage {float(_cs0):.3f} "
                     f"+ uebliche Schwankung {_spanne:.3f}")
        else:
            _traegt = _cs > _mth                         # Rueckfall, solange kein eigener Bezug da ist
            _wieT = f"Farbstreuung {_cs:.3f} gegen globalen Massstab {_mth:.3f} (kein eigener Bezug)"
        _ao = None if det0 is None else det0.get("area")
        if _ao:
            _drauf = abs(_a - _a0) <= abs(_a - (_a0 + float(_ao)))
            _wie = f"Flaeche {_a:.0f} gegen leer {_a0:.0f} / daneben {_a0 + float(_ao):.0f}"
        else:
            _drauf, _wie = True, f"Flaeche {_a:.0f} (eigene Flaeche unbekannt)"
        # DAS ALTE KRITERIUM WIRD MITPROTOKOLLIERT, nicht ersetzt: so vergleicht EIN Lauf beide
        # Massstaebe an denselben Episoden, statt zwei Laeufe gegeneinander stellen zu muessen.
        return (_traegt and _drauf,
                f"{_wieT} -> {'traegt etwas' if _traegt else 'leer'}; {_wie}"
                f" | global waere: {'ja' if _cs > _mth else 'nein'}")

    def _ziel_adresse_wuerfeln():
        """STUFE 1 von "Stapeln als neue Aufgabe": das Ablageziel wird eine ADRESSE.

        Gewuerfelt wird EINMAL JE EPISODE und danach benutzt; aufgeloest wird erst, wenn
        run_combined das Ziel abholt (goal_fn -> _ziel_aufloesen).  Die Trennung ist Absicht:
        der Wurf legt fest, WAS gesagt wird, die Aufloesung findet es in der Szene wieder.

        WER DER BEZUGSKOERPER IST, waehlt der Wurf aus den Koerpern, die gerade auf dem Tisch
        stehen -- das ist Aufgabenerzeugung wie die Wahl des Objekts oder die Marker-Position,
        kein Privileg im Vollzug.  Die ADRESSE selbst kommt aus der Detektion, die auf ihm sitzt,
        also aus dem, was die Kamera hergibt.

        DIE EINDEUTIGKEIT ERZWINGT _adresse_wuerfeln -- dieselbe Fassung wie fuer das Objekt,
        samt der Nutzervorgabe, dass eine reine Groessenangabe keine Adresse ist ("der blaue
        Wuerfel", nie "das groesste Objekt").  Bleibt keine eindeutige Adresse uebrig, wird gar
        keine gesetzt und der Marker bleibt das Ziel.
        """
        state.ziel_bezug = None
        if state.ziel_modus != "koerper":
            return None
        _gui = state.ziel_art                           # in der GUI fest gewaehlte Relation (None = Umgebung)
        if (_gui is None and ZIEL_MISCH is not None and ZIEL_RELATION in ("auf", "alle")
                and float(crng.random()) >= ZIEL_MISCH):
            # AUFGABENMISCHUNG (s. ZIEL_MISCH): diese Episode ist eine gewoehnliche Marker-Ablage.
            # EIGENE Zeile, nicht [Zielwurf] -- das hier ist gewollt und kein gescheiterter Wurf; die
            # Auswertung muss beides trennen koennen.
            print("    [Ziel] Marker-Episode (Aufgabenmischung)", flush=True)
            return None
        _a = state.selected()[1]
        _rel = ZIEL_RELATION
        _zwort = None
        if _gui is not None:
            _rel = _gui if _gui in ("an", "auf") else "richtung"
        elif ZIEL_ZELLEN:
            # ZELLEN (s. ZIEL_ZELLEN): erst das Wort, dann nur Bezugskoerper einer erlaubten Art.
            _ws = sorted({w for w, _k in ZIEL_ZELLEN})
            _zwort = _ws[int(crng.integers(len(_ws)))]
            _rel = "auf" if _zwort == "auf" else "richtung"
        elif _rel == "alle":
            _rel = "auf" if float(crng.random()) < 0.2 else "richtung"
        if _rel == "auf" and (AUF_ALLE or _gui == "auf"):
            # AUF JEDEN KOERPER (s. AUF_ALLE): Platten und alle Objekte der Szene.
            _kand = [nm for nm in dict.fromkeys(list(state.STUETZEN)
                                                + [nm for _l, nm, _m in state.OBJECTS])
                     if nm != _a and not _geparkt_jetzt(nm)]
        elif _rel == "auf":
            # AUF etwas gestellt wird nur, was tragen kann -- die STUETZEN.  Ein 24-mm-Wuerfel auf
            # einem 24-mm-Wuerfel verlangt unter 12 mm Versatz und ist bei gemessenen 21-25 mm
            # Ablagegenauigkeit von Anfang an unloesbar; die Auflage ist die Schwierigkeitsachse.
            _kand = [nm for nm in state.STUETZEN if nm != _a and not _geparkt_jetzt(nm)]
        else:
            _kand = [nm for nm in dict.fromkeys(nm for _l, nm, _m in state.OBJECTS)
                     if nm != _a and not _geparkt_jetzt(nm)]
        # JEDER RUECKZUG SAGT, WARUM.  Ein Wurf, der still None liefert, laesst die Episode auf
        # den Marker fallen -- und ist in der Auswertung von einer gewollten Marker-Episode nicht
        # zu unterscheiden.  Genau das hat das erste Stapel-A/B getroffen: 83 von 100 Episoden
        # ohne Adresse, und keine Zeile sagte, woran es lag (wiki/befunde/stapeln-gemessen.md).
        def _kein(grund):
            print(f"    [Zielwurf] keine Adresse: {grund}", flush=True)
            return None
        if _zwort is not None:
            _kand = [nm for nm in dict.fromkeys(list(state.STUETZEN) + [n for _l, n, _m in state.OBJECTS])
                     if nm != _a and not _geparkt_jetzt(nm) and (_zwort, zielart(nm)) in ZIEL_ZELLEN]
            if _zwort != "auf":
                # Nur Bezugskoerper, neben denen das Wort ueberhaupt erreichbar ist -- sonst verfiele
                # die Episode (der Arbeitsraum ist in y nur 140 mm breit).  Aufgabenerzeugung.
                from pc_cvnn.pc_act14 import REACH_XY
                from pc_cvnn.pc_act16 import BASE_CLEAR
                def _erreichbar(nm):
                    _pp = sim.obj_pos(nm)[:2]
                    _dw, _ = _wort_richtung(_zwort, _pp, laut=False)
                    if _dw is None:
                        return False
                    _q = _pp + ZIEL_ABSTAND * _dw
                    return bool(REACH_XY[0][0] <= _q[0] <= REACH_XY[1][0]
                                and REACH_XY[0][1] <= _q[1] <= REACH_XY[1][1]
                                and float(np.linalg.norm(_q)) >= BASE_CLEAR)
                _kand = [nm for nm in _kand if _erreichbar(nm)]
        if _gui in RICHTUNGS_WOERTER:
            # DIE GUI HAT DAS WORT FEST GEWAEHLT: nur Bezugskoerper, neben denen es erreichbar ist
            # (dieselbe Pruefung wie bei den Zellen oben).
            from pc_cvnn.pc_act14 import REACH_XY
            from pc_cvnn.pc_act16 import BASE_CLEAR
            def _erreichbar_g(nm):
                _pp = sim.obj_pos(nm)[:2]
                _dw, _ = _wort_richtung(_gui, _pp, laut=False)
                if _dw is None:
                    return False
                _q = _pp + ZIEL_ABSTAND * _dw
                return bool(REACH_XY[0][0] <= _q[0] <= REACH_XY[1][0]
                            and REACH_XY[0][1] <= _q[1] <= REACH_XY[1][1]
                            and float(np.linalg.norm(_q)) >= BASE_CLEAR)
            _kand = [nm for nm in _kand if _erreichbar_g(nm)]
        _fix_b = state.ziel_body_fix
        if _fix_b is not None:
            # IN DER GUI FEST GEWAEHLT: nur dieser Koerper, wenn er passt -- sonst sagen, warum nicht
            if _fix_b not in _kand:
                return _kein(f"gewaehlter Bezug {_fix_b} passt nicht (transportiertes Objekt, geparkt, "
                             f"oder Relation dort nicht erreichbar)")
            _kand = [_fix_b]
        if not _kand:
            return _kein("kein Bezugskoerper verfuegbar"
                         + (" (keine Stuetze in der Szene)" if _rel == "auf" else ""))
        _b = _kand[int(crng.integers(len(_kand)))]
        _sm = sim.d.mocap_pos.copy()
        _ds = [d for d in shape_clf.perceive_all(sim)
               if d.get("pos") is not None and float(d.get("area", 0)) >= 200.0]
        sim.d.mocap_pos[:] = _sm; mujoco.mj_forward(sim.m, sim.d)
        _p = sim.obj_pos(_b)[:2]
        _nah = min(_ds, key=lambda d: float(np.linalg.norm(
            np.asarray(d["pos"], float) - _p)), default=None)
        if _nah is None:
            return _kein(f"{_b}: keine Detektion im Bild")
        _dn = float(np.linalg.norm(np.asarray(_nah["pos"], float) - _p))
        if _dn >= 0.04:
            return _kein(f"{_b}: naechste Detektion {1000 * _dn:.0f} mm entfernt (Schranke 40 mm)")
        _f = colours.classify(_nah["chroma"])[0] if _nah.get("chroma") is not None else None
        _fo, _g = _nah.get("shape"), groessen_band(_nah.get("dicke"), _nah.get("span"))
        _mess = (np.asarray(_nah["chroma"], float) if _nah.get("chroma") is not None else None,
                 np.asarray(shape_clf.desc_embed(_nah["desc"]), float)
                 if _nah.get("desc") is not None else None,
                 float(_nah["span"]) if _nah.get("span") is not None else None)
        if EIG_DIREKT and EIG_STETIG and _fo is None and _mess[1] is not None:
            _fo = EIG_GESEHEN                            # Formachse ohne Klasse, s. dort
        _tri = _adresse_wuerfeln((_f, _fo, _g), _mess, _p, ident=True)
        if _tri is None:
            return _kein(f"{_b}: keine verfolgbare Achse (Farbe {_f}, Form {_fo}, Groesse {_g}) -- "
                         f"eine reine Groessenangabe ist keine Adresse")
        _ph0 = float(crng.uniform(0.0, 2.0 * np.pi))     # acht Peilungen ab einem zufaelligen
        _peil = [(_ph0 + 2.0 * np.pi * k / 8.0) for k in range(8)]   # Winkel, s. ZIEL_ADRESSE
        _wort = None
        if _rel == "richtung":
            # DAS WORT WIRD NUR UNTER DEN ERREICHBAREN GEWUERFELT -- Aufgabenerzeugung, wie die Wahl
            # des Bezugskoerpers.  Der Arbeitsraum ist in y nur 140 mm breit; "links" 50 mm neben
            # einem Koerper am linken Rand ist keine Aufgabe, sondern ein sicherer Fehlschlag.
            # Geprueft an der WAHRGENOMMENEN Stelle mit derselben Bedeutung, die spaeter aufloest.
            from pc_cvnn.pc_act14 import REACH_XY
            from pc_cvnn.pc_act16 import BASE_CLEAR
            _pn = np.asarray(_nah["pos"], float)
            _ok = []
            for _w in RICHTUNGS_WOERTER:
                _dw, _ = _wort_richtung(_w, _pn, laut=False)
                if _dw is None:
                    continue
                _q = _pn + ZIEL_ABSTAND * _dw
                if (REACH_XY[0][0] <= _q[0] <= REACH_XY[1][0] and REACH_XY[0][1] <= _q[1] <= REACH_XY[1][1]
                        and float(np.linalg.norm(_q)) >= BASE_CLEAR):
                    _ok.append(_w)
            _fix = _zwort or (_gui if _gui in RICHTUNGS_WOERTER else None)
            if _fix is not None:
                _ok = [w for w in _ok if w == _fix]
            if not _ok:
                return _kein(f"{_b}: keine Richtung erreichbar"
                             + (f" ('{_zwort}')" if _zwort else ""))
            _wort = _ok[int(crng.integers(len(_ok)))]
        _txt = " + ".join(str(t) for t in _tri if t is not None) or "beliebig"
        print(f"    [Zielzelle] {_wort or _rel}:{zielart(_b)} ({_b})", flush=True)   # Auswertung
        state.ziel_bezug = {"tripel": _tri, "mess": _mess, "peilungen": _peil, "body": _b,
                            "relation": _rel, "wort": _wort,
                            "label": ("auf " + _txt if _rel == "auf"
                                      else f"{_wort if _wort in ('vor', 'hinter') else _wort + ' von'} {_txt}"
                                      if _wort else _txt)}
        return _tri

    colour_of_body = dict(_loaded.get("colour_of_body", {})) if _loaded is not None else {}
    # SELF-HEAL pre-0a539ac collision damage in persisted states: birth names were len+1, so a
    # name could be re-issued -> DUPLICATE entries in the list / entries without a class (index/
    # remove then operate on the wrong occurrence).  Sync the list to the dict, once, at load.
    _cn = [n for n in dict.fromkeys(colours.names) if n in colours.classes]
    if _cn != colours.names:
        print(f"  [Persistenz] Farbklassen-Liste repariert ({len(colours.names)} -> {len(_cn)} "
              f"Einträge: Duplikate/Verwaiste aus der Vor-Fix-Ära entfernt)", flush=True)
        colours.names = _cn
    _stale = {b: c for b, c in colour_of_body.items() if c not in colours.classes}
    for b in _stale:                                           # a binding to a merged-away class can
        del colour_of_body[b]                                  #   never match again -> drop, re-binds
    if _stale:                                                 #   itself at the next discovery glance
        print(f"  [Persistenz] verwaiste Farb-Bindungen entfernt: {_stale}", flush=True)

    # ---------------- FARB-MISCHUNG (s. FARB_MISCHUNG oben) ------------------------------------
    _FARB_KOERPER = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U", "obj_T", "obj_X"]

    def _geoms_of(body):
        _b = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, body)
        _a0 = sim.m.body_geomadr[_b]
        return list(range(_a0, _a0 + sim.m.body_geomnum[_b]))

    _FARB_PALETTE = {b: sim.m.geom_rgba[_geoms_of(b)[0]].copy() for b in _FARB_KOERPER}

    def _faerbe_neu():
        """Die sieben vorhandenen Koerperfarben unter den Koerpern PERMUTIEREN.

        Keine neuen Farben: eine neue Farbe gebiert eine neue Farbklasse, das waere ein anderes
        Experiment.  Eine Permutation laesst die Palette genau so wahrnehmbar wie heute und
        loest allein die Zuordnung Farbe<->Form."""
        _ziel = list(_FARB_PALETTE.values())
        _perm = list(crng.permutation(len(_ziel)))
        for _b, _i in zip(_FARB_KOERPER, _perm):
            for _g in _geoms_of(_b):
                sim.m.geom_rgba[_g] = _ziel[_i]

    def _farbbindung_neu():
        """colour_of_body je Episode NEU aus der WAHRNEHMUNG setzen statt aus einer Tabelle.

        Nutzervorgabe 2026-09-10.  Mit wechselnden Farben ist "die Farbklasse dieses Koerpers"
        keine dauerhafte Groesse mehr -- die persistierte Tabelle waere ab der ersten Umfaerbung
        schlicht falsch, und daran haengen Farb-Split, Rettungspfade, ckey-Tracker, der
        Fovea-Identitaetskanal und das Selbst-Urteil.

        DERSELBE Zuordnungsschritt wie bei der Erstbindung (pc_act23.py:2826): Detektion ->
        naechster Koerper, Schranke 40 mm.  Er ist wie dort buchhalterisch privilegiert; NEU ist
        nur, dass er je Episode statt einmal laeuft.  Was der AGENT sieht, aendert sich dadurch
        nicht: die Klasse kommt aus der gerenderten Chroma, nicht aus der RGBA (die Lehre aus
        der obj_Y-Aneignung), und ein Koerper OHNE gute Zuordnung bleibt ungebunden statt geraten.
        """
        _sv = sim.d.mocap_pos.copy()
        _ds = shape_clf.perceive_all(sim)
        sim.d.mocap_pos[:] = _sv
        mujoco.mj_forward(sim.m, sim.d)
        _neu, _belegt = {}, set()
        for _d in sorted(_ds, key=lambda x: -float(x.get("area", 0))):
            if _d.get("pos") is None or _d.get("chroma") is None:
                continue
            if shape_clf.area_hi is not None and _d["area"] > shape_clf.area_hi:
                continue                                   # verschmolzener Blob -> Mischchroma, nicht binden
            _c, _cd = colours.classify(_d["chroma"])
            if _c is None or _c in _belegt:
                continue                                   # zwei Koerper duerfen nicht dieselbe Klasse teilen
            _nah = min(_FARB_KOERPER,
                       key=lambda o: float(np.linalg.norm(sim.obj_pos(o)[:2] - _d["pos"])))
            if _nah in _neu:
                continue
            if float(np.linalg.norm(sim.obj_pos(_nah)[:2] - np.asarray(_d["pos"]))) < 0.04:
                _neu[_nah] = _c
                _belegt.add(_c)
        if BINDUNG_SPLIT:
            # ZWEITER DURCHGANG fuer die Koerper, die der erste ausgelassen hat -- fast immer,
            # weil sie in einem verschmolzenen Blob steckten (s. BINDUNG_SPLIT oben).  Gleiche
            # Regeln: eine Klasse je Koerper, Schranke 40 mm, lieber ungebunden als geraten.
            _offen = [o for o in _FARB_KOERPER if o not in _neu]
            if _offen:
                _sv2 = sim.d.mocap_pos.copy()
                _teile = shape_clf.colour_parts_all(sim, colours)
                sim.d.mocap_pos[:] = _sv2
                mujoco.mj_forward(sim.m, sim.d)
                _dazu = 0
                for _t in _teile:
                    if _t["cname"] in _belegt:
                        continue
                    _nah2 = min(_offen, key=lambda o: float(
                        np.linalg.norm(sim.obj_pos(o)[:2] - _t["pos"])))
                    if _nah2 in _neu:
                        continue
                    if float(np.linalg.norm(sim.obj_pos(_nah2)[:2]
                                            - np.asarray(_t["pos"]))) < 0.04:
                        _neu[_nah2] = _t["cname"]
                        _belegt.add(_t["cname"])
                        _dazu += 1
                if _dazu and os.environ.get("ACT23_DEBUG", "0") == "1":
                    print(f"    [Bindung-Split] {_dazu} von {len(_offen)} offenen Koerpern "
                          f"pixelweise gebunden", flush=True)
        colour_of_body.clear()
        colour_of_body.update(_neu)
        return _neu

    def _farbe_wuerfeln():
        """Je Episode umfaerben und neu binden -- EINE Fassung fuer BEIDE Auto-Schleifen.

        act23 hat zwei Auto-Schleifen mit eigenem Code; ein Schalter nur in einer sieht in der
        kopflosen Kontrolle sauber aus und tut in der GUI nichts (zweimal passiert, s.
        wiki/mechanismen/invarianten.md).  Deshalb hier, und von beiden gerufen.

        REIHENFOLGE: das muss VOR curious_pick() und _auto_eig_umschreiben() laufen -- beide
        nehmen wahr, und eine nach dem Umfaerben gewuerfelte Eigenschafts-Adresse muss die NEUE
        Farbklasse tragen, sonst adressiert das Kommando eine Farbe, die es nicht mehr gibt.
        """
        if not FARB_MISCHUNG:
            return None
        _faerbe_neu()
        _b = _farbbindung_neu()
        if os.environ.get("ACT23_DEBUG", "0") == "1":
            print("    [Farbe] neu gemischt: "
                  + ", ".join(f"{k}={v}" for k, v in sorted(_b.items())), flush=True)
        return _b

    # ------------------------------------------------------------------------------------------
    # ArmAgent: der VERKEHR SOLL DURCH DIE PORTS (Nutzerplan 2026-08-23, Punkt 2)
    # ------------------------------------------------------------------------------------------
    # BEFUND, der das ausgeloest hat: die Connector-Schicht war zur Laufzeit KOMPLETT INERT.
    # act23 nannte ArmAgent 0x, .wire() 0x, agent.step() 0x; kein Modul las je den Port eines
    # anderen -- nur Selbstzugriffe; ArmModule.step() wurde von genau einer Stelle gerufen
    # (ArmAgent.step in base.py), die niemand ruft.  Zehn Module befuellten dreissig Out-Ports,
    # die nie jemand las.  Die echte Verdrahtung sind 15 Closure-Callbacks in run_combined.
    #
    # WARUM IN ETAPPEN und nicht in einem Zug: der vorhandene Portsatz beschreibt die echten
    # Schnittstellen gar nicht (fuer wrist_fn/orient_fn/carry_target_fn gab es keinen
    # Port), und run_combined wird von sieben Dateien benutzt -- ein Big-Bang waere weder
    # pruefbar noch rueckholbar.  Deshalb wandert je Etappe EINE Kante auf die Ports, mit einer
    # Gleichheitsprobe: der Lauf ist bei gegebenem Seed deterministisch, also muss das Ergebnis
    # nach dem Umbau BITGLEICH sein, sonst war die Kante nicht verhaltensneutral.
    #
    # ETAPPE 1 = ObjectMemory (s. die Aufrufstelle im Fovea-Tracker).  Bewusst diese zuerst:
    # ihre drei In-Ports entsprechen exakt der Signatur von update(), sie liegt im Bild-fuer-Bild-
    # Pfad, und genau dort setzt spaeter Punkt 4 an -- run_combined taktet die Wahrnehmung heute
    # schon mit einem hart kodierten `k % 4 == 0` (act16:403), also existiert die Multi-Raten-
    # Struktur bereits, nur unsichtbar und unveraenderlich.
    agent = ArmAgent("act23")
    # ETAPPE 4: die Bild-fuer-Bild-Wahrnehmung als eigenes Modul MIT EIGENER RATE (s. perception.py).
    # ACT23_PERCEPT_RATE=1 (Vorgabe) = jeden Takt rechnen -> verhaltensneutral, bitgleich zum
    # Callback-Pfad.  >1 laesst das Modul dazwischen den GEHALTENEN Stand liefern; das ist der
    # Knopf, an dem Punkt 4 misst.  Die Rate MULTIPLIZIERT sich mit dem `k % 4` aus act16:403.
    perception = PerceptionModule(rate=int(os.environ.get("ACT23_PERCEPT_RATE", "1")))
    # ETAPPE 5: der REGELPFAD bekommt ebenfalls eine eigene Rate.  Die Kante liegt seit Etappe 2
    # auf Ports, also ist hier nichts umzustecken -- es genuegt, die Rate zu setzen; durchgesetzt
    # wird sie im ArmAgent.  ACT23_POLICY_RATE=2 heisst: die Policy entscheidet nur jeden zweiten
    # Takt neu, dazwischen faehrt der Arm auf dem GEHALTENEN Teilziel weiter.  Zusammen mit
    # ACT23_PERCEPT_RATE ist damit beisammen, was Punkt 4 braucht: eine langsame Entscheidung
    # ueber einer schnellen Wahrnehmung -- oder umgekehrt.
    runtime.rate = int(os.environ.get("ACT23_POLICY_RATE", "1"))
    # GEGENMESSUNG zu Punkt 4: der PLANER bekommt ebenfalls eine Rate.  Gemessen wurde dort nur
    # ein langsamerer REGLER (RuntimePolicy) -- und der ist kein Planer.  Der planende Anteil, der
    # im Bild-Takt laeuft, ist der latente Ziel-Servo (place_servo_fn -> lgoal.servo, act16:506,
    # jedes Bild waehrend des Tragens).  SCHNELLER geht dort nicht: er ist bereits am Anschlag,
    # und die uebrigen Planer-Anteile (Objektwahl, Ablageziel) laufen 1x je Episode und sind
    # festgeschrieben, weil der Erfolg gegen sie gemessen wird.  Messbar ist deshalb nur der
    # Spiegel: den Planer VERLANGSAMEN und sehen, ob "langsamer schadet" spezifisch fuer den
    # Regler ist oder allgemein gilt.
    # Der Ziel-Servo hat keine Portschicht (er wird aus einem Blob per __new__ wiederhergestellt),
    # deshalb die generische Huelle statt einer Modulisierung.
    plan_takt = RateWrapper(2, 2, rate=int(os.environ.get("ACT23_PLAN_RATE", "1")), name="PlanTakt")
    lgoal._ensure_ports()          # aus dem Persistenz-Blob wiederhergestellte Servos haben keine
    #                                Portschicht (s. _lg_unpack); vor agent.add nachruesten
    for _m in (vc, shape_clf, objmem, seval, world, runtime, bm, lat_dyn, perception, plan_takt,
               lgoal):
        if _m is not None:
            agent.add(_m)
    # NOCH KEINE wire()-Kanten: eine Kante wird erst deklariert, wenn sie auch WIRKLICH ueber die
    # Ports laeuft.  Eine deklarierte, aber nicht gefahrene Verdrahtung waere genau die Attrappe,
    # die dieser Umbau beseitigen soll.

    # ACT23_REDDIAG=1: RED<->L CONFUSION diagnosis (mechanism-ID, no fix).  The user watched the red
    # cube command grasp the nearby L instead; the 24-ep GUI log shows red LOSING the fovea servo in
    # 5 of 6 episodes (the [Fovea-Servo] line only prints on >0 frames -> the colour-keyed tracker
    # found ZERO candidates all episode) and twice reporting "Blob-Verschmelzung erkannt".  The
    # persisted classes are CLEAN (farbe-1 sits 0.023 from true red), so this is NOT class drift.
    # Code-grounded hypothesis (shape_classifier:623): a component's chroma is the MEAN over all its
    # pixels -- red fused with the orange L into ONE component averages to a mixed tone matching
    # NEITHER class -> 0 candidates -> perceive() falls back to the old trained vc hex code (:1437),
    # which is documented to fire on foreign objects.  Fix candidate to validate here: split the
    # component's PIXELS by the self-learned colour classes (the same continuity idea self_eval uses
    # after release, but anchored on COLOUR so it works BEFORE the grasp, with no hand anchor).
    # Writes log/red_l_diag.png and exits.
    if os.environ.get("ACT23_REDDIAG") == "1":
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as _plt
        from scipy import ndimage as _ndi
        sc = shape_clf
        saved_mp = sim.d.mocap_pos.copy()
        ck_red, ck_L = colour_of_body.get("obj_red"), colour_of_body.get("obj_L")
        cnames = [n for n in colours.names if n in colours.classes]
        MU = np.array([colours.classes[n]["mu"] for n in cnames])   # vectorised per-pixel classify
        print(f"  [REDDIAG] Bindungen: obj_red='{ck_red}' obj_L='{ck_L}' | {len(cnames)} Farbklassen "
              f"| TH={colour_openset.TH}", flush=True)
        gaps = [0.070, 0.050, 0.038, 0.028]
        fig, axes = _plt.subplots(1, len(gaps), figsize=(4.3 * len(gaps), 4.8))
        for ax, gap in zip(np.atleast_1d(axes), gaps):
            for o in ALL:
                sim.set_object(o, [0.5, -0.6], z=0.012)
            rp = np.array([-0.015, 0.155])
            sim.set_object("obj_red", rp.tolist(), z=0.012)
            sim.set_object("obj_L", (rp + np.array([gap, 0.0])).tolist(), z=0.012, yaw=0.4)
            mujoco.mj_forward(sim.m, sim.d)
            truth = np.asarray(sim.obj_pos("obj_red")[:2], float)
            # (a) what the agent ACTUALLY sees today: whole-component chroma -> class
            dets = sc.perceive_all(sim)
            hits = [d for d in dets if colours.classify(d["chroma"])[0] == ck_red]
            # (b) the same scene at pixel level, to test the colour split
            sc._park_markers(sim)
            img = sc._render_u8(sim); mask = sc._mask(img)
            labels, n = _ndi.label(mask)
            # the component containing the true red centre
            rpx = sc._world_to_px(truth[None, :])[0] if sc.H is not None else None
            lab_red = 0
            if rpx is not None:
                yy, xx = int(round(rpx[1])), int(round(rpx[0]))
                if 0 <= yy < labels.shape[0] and 0 <= xx < labels.shape[1]:
                    lab_red = int(labels[yy, xx])
            if lab_red == 0:                                    # centre landed off-mask -> largest comp
                sizes = _ndi.sum(mask, labels, range(1, n + 1))
                lab_red = int(np.argmax(sizes)) + 1 if n else 0
            comp = (labels == lab_red)
            ys, xs = np.nonzero(comp)
            prgb = img[ys, xs].astype(float)
            psum = prgb.sum(1, keepdims=True)
            pch = np.divide(prgb, psum, out=np.zeros_like(prgb), where=psum > 1e-6)
            dmat = np.linalg.norm(pch[:, None, :] - MU[None, :, :], axis=2)   # (npx, nclass)
            nearest = dmat.argmin(1); ndist = dmat.min(1)
            assigned = np.where(ndist <= colour_openset.TH, nearest, -1)
            i_red = cnames.index(ck_red) if ck_red in cnames else -2
            sel = assigned == i_red
            # component-level truth: is this ONE blob holding BOTH objects?
            comp_ch = prgb.mean(0) / max(prgb.mean(0).sum(), 1e-6)
            comp_cls, comp_d = colours.classify(comp_ch)
            comp_ctr = sc._centroid(comp.astype(np.float32)) if sc.H is not None else None
            err_whole = (1000.0 * float(np.linalg.norm(np.asarray(comp_ctr, float) - truth))
                         if comp_ctr is not None else float("nan"))
            err_split = float("nan"); split_ctr = None
            if sel.sum() >= 8 and sc.H is not None:
                Wsel = sc._px_to_world(np.column_stack([xs[sel], ys[sel]]))
                split_ctr = Wsel.mean(0)
                err_split = 1000.0 * float(np.linalg.norm(split_ctr - truth))
            # (c) the SHIPPED method on the same scene -- validates the real code path, not this rehearsal
            real = sc.perceive_colour(sim, colours, ck_red)
            err_real, n_real = float("nan"), 0
            if real:
                rbest = min(real, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"]) - truth)))
                err_real = 1000.0 * float(np.linalg.norm(np.asarray(rbest["pos"]) - truth))
                n_real = int(rbest["area"])
            print(f"  [REDDIAG] Lücke {gap*1000:.0f}mm: {n} Komponenten, Rot-Komp {comp.sum():.0f}px "
                  f"-> Klasse '{comp_cls}' (d={comp_d:.3f}); perceive_all-Treffer auf '{ck_red}': "
                  f"{len(hits)} | Pixel-Split: {sel.sum()}/{len(xs)} px als '{ck_red}' | "
                  f"Fehler ganz {err_whole:.0f}mm vs Split {err_split:.0f}mm | "
                  f"perceive_colour(): {len(real)} Det, {n_real}px, Fehler {err_real:.0f}mm", flush=True)
            ov = np.zeros(mask.shape + (3,), float)
            ov[..., 0] = mask * 0.35
            ov[..., 1] = mask * 0.35
            ov[..., 2] = mask * 0.35
            ov[ys[sel], xs[sel]] = [1.0, 0.2, 0.2]              # pixels the split calls RED
            ax.imshow(ov, origin="upper")
            if rpx is not None:
                ax.plot(rpx[0], rpx[1], "w+", ms=15, mew=2.5, label="wahres Rot")
            ax.plot(xs.mean(), ys.mean(), "yo", ms=10, mfc="none", mew=2.4,
                    label=f"Komp-Schwerpunkt ({err_whole:.0f}mm)")
            if split_ctr is not None:
                spx = sc._world_to_px(split_ctr[None, :])[0]
                ax.plot(spx[0], spx[1], "cs", ms=10, mfc="none", mew=2.4,
                        label=f"Farb-Split ({err_split:.0f}mm)")
            ax.set_title(f"Lücke {gap*1000:.0f}mm | {n} Komp | Komp-Klasse '{comp_cls}'", fontsize=9)
            ax.legend(fontsize=7, loc="upper right"); ax.axis("off")
        sim.d.mocap_pos[:] = saved_mp; mujoco.mj_forward(sim.m, sim.d)
        outp = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "log", "red_l_diag.png")
        fig.tight_layout(); fig.savefig(outp, dpi=110)
        print(f"  [REDDIAG] geschrieben -> {outp}", flush=True)

        # BENCH: the same question END-TO-END over many random neighbour constellations, WITHOUT the
        # learning loop.  A full A/B could not answer it: both arms ran bit-identical until the split
        # first fired, then the trajectories diverged (different curiosity picks, different object
        # counts) and the delivery delta became trajectory noise -- and the red/L fusion never even
        # occurred headless.  This isolates PERCEPTION: place the L at a random offset around the red
        # cube, ask what the colour path returns with and without the split, and score against truth.
        rng = np.random.default_rng(int(os.environ.get("ACT23_SEED", "11")))
        N = int(os.environ.get("ACT23_REDBENCH_N", "120"))
        stat = {"fused": 0, "old_ok": 0, "old_err": [], "new_ok": 0, "new_err": [], "rec": 0}
        for _ in range(N):
            for o in ALL:
                sim.set_object(o, [0.5, -0.6], z=0.012)
            rp = np.array([rng.uniform(-0.08, 0.08), rng.uniform(0.11, 0.20)])
            ang = rng.uniform(0, 2 * np.pi)
            gap = rng.uniform(0.022, 0.075)                # spans fused .. clearly separate
            sim.set_object("obj_red", rp.tolist(), z=0.012)
            sim.set_object("obj_L", (rp + gap * np.array([np.cos(ang), np.sin(ang)])).tolist(),
                           z=0.012, yaw=float(rng.uniform(0, 2 * np.pi)))
            mujoco.mj_forward(sim.m, sim.d)
            truth = np.asarray(sim.obj_pos("obj_red")[:2], float)
            saved2 = sim.d.mocap_pos.copy()
            dets = sc.perceive_all(sim)
            old = [d for d in dets if d["pos"] is not None
                   and colours.classify(d["chroma"])[0] == ck_red]
            if not old:
                stat["fused"] += 1                         # today: 0 candidates -> vc fallback (grasps L)
                new = sc.perceive_colour(sim, colours, ck_red)
                if new:
                    stat["rec"] += 1
                    b = min(new, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"]) - truth)))
                    e = 1000.0 * float(np.linalg.norm(np.asarray(b["pos"]) - truth))
                    stat["new_err"].append(e); stat["new_ok"] += int(e < 15.0)
            else:
                b = min(old, key=lambda d: colours.classify(d["chroma"])[1])
                e = 1000.0 * float(np.linalg.norm(np.asarray(b["pos"]) - truth))
                stat["old_err"].append(e); stat["old_ok"] += int(e < 15.0)
            sim.d.mocap_pos[:] = saved2; mujoco.mj_forward(sim.m, sim.d)
        sim.d.mocap_pos[:] = saved_mp; mujoco.mj_forward(sim.m, sim.d)
        ne, oe = stat["new_err"], stat["old_err"]
        print(f"\n  [REDBENCH] {N} zufällige Rot+L-Konstellationen (Lücke 22-75mm, kein Lernen):", flush=True)
        print(f"    nicht verschmolzen: {N - stat['fused']}  -> alter Pfad findet Rot, "
              f"Median {np.median(oe) if oe else float('nan'):.0f}mm, <15mm: {stat['old_ok']}/{len(oe)}",
              flush=True)
        print(f"    VERSCHMOLZEN      : {stat['fused']}  -> alter Pfad findet 0 Kandidaten "
              f"(= vc-Rückfall, greift den Nachbarn)", flush=True)
        print(f"      davon vom Farb-Split gerettet: {stat['rec']}/{stat['fused']}, "
              f"Median {np.median(ne) if ne else float('nan'):.0f}mm, <15mm: {stat['new_ok']}/{len(ne)}",
              flush=True)
        raise SystemExit(0)

    # ACT23_TDIAG=1: FORM-BLINDNESS diagnosis for the open-class object (mechanism-ID, no fix).  In the
    # 120-ep GUI run "Neue Form 7" lost the fovea servo in 7 of 13 episodes (54%) vs 3 of 107 for every
    # other object (p<1e-5) -- the tracker keys on d["shape"]==key and found ZERO candidates all episode.
    # Unlike the red/L case this is the FORM path, so the colour split cannot help.  Class OVERBIRTH is
    # ruled out (0 class pairs closer than novel_th), but neu-72 sits at EXACTLY novel_th (7.72) from the
    # bound class neu-9, with neu-34/78/98/95 at 11-13.  Hypothesis: the descriptor of obj_T WANDERS with
    # pose/neighbour, so resolve() lands on a competitor or on None (novel) instead of neu-9.  This renders
    # obj_T over many poses -- alone and with a close neighbour -- and tallies what it is actually called.
    if os.environ.get("ACT23_TDIAG") == "1":
        sc = shape_clf
        _sk = dict((_loaded or {}).get("shape_key", {}))       # persisted body -> open-class binding
        NOVEL_BODY = next(iter(_sk), "obj_T")                  # (NOVEL_BODY itself is defined further down)
        key = _sk.get(NOVEL_BODY)
        print(f"  [TDIAG] {NOVEL_BODY} gebunden an Formklasse '{key}' | novel_th={sc.novel_th:.2f} "
              f"| offene Klassen {len(sc.open)}", flush=True)
        saved_mp = sim.d.mocap_pos.copy()
        rng = np.random.default_rng(int(os.environ.get("ACT23_SEED", "11")))
        N = int(os.environ.get("ACT23_TDIAG_N", "80"))
        import collections
        for scenario in ("allein", "mit Nachbarn"):
            tally = collections.Counter(); dists = {"eigen": [], "beste_fremd": []}
            tally_fix = collections.Counter()
            found = 0
            for _ in range(N):
                for o in ALL + [NOVEL_BODY]:
                    sim.set_object(o, [0.5, -0.6], z=0.012)
                tp = np.array([rng.uniform(-0.08, 0.08), rng.uniform(0.11, 0.20)])
                sim.set_object(NOVEL_BODY, tp.tolist(), z=0.012, yaw=float(rng.uniform(0, 2*np.pi)))
                if scenario != "allein":                       # a neighbour at fusion distance
                    ang = rng.uniform(0, 2*np.pi)
                    gap = rng.uniform(0.022, 0.055)
                    sim.set_object("obj_L", (tp + gap*np.array([np.cos(ang), np.sin(ang)])).tolist(),
                                   z=0.012, yaw=float(rng.uniform(0, 2*np.pi)))
                mujoco.mj_forward(sim.m, sim.d)
                dets = sc.perceive_all(sim)
                if not dets:
                    tally["KEINE Detektion"] += 1; continue
                # the detection nearest the true obj_T position is the one that matters
                d = min(dets, key=lambda q: 1e9 if q["pos"] is None
                        else float(np.linalg.norm(np.asarray(q["pos"]) - tp)))
                if d["pos"] is None or float(np.linalg.norm(np.asarray(d["pos"]) - tp)) > 0.05:
                    tally["nicht lokalisiert"] += 1; continue
                found += 1
                nm = d["shape"]
                tally[nm if nm is not None else "None (novel)"] += 1
                # how far is this descriptor from its OWN class vs the best competitor?
                de = sc.desc_embed(d["desc"]) if d.get("desc") is not None else None
                if d.get("desc") is not None:
                    best = {}
                    for cn, ex in sc.open.items():
                        A = np.asarray(ex, float)
                        best[cn] = float(np.linalg.norm(A - np.asarray(d["desc"], float), axis=1).min())
                    if key in best:
                        dists["eigen"].append(best[key])
                        others = [v for c, v in best.items() if c != key]
                        if others:
                            dists["beste_fremd"].append(min(others))
                # the SHIPPED recovery (ACT23_FORM_SPLIT) on the same scene, for the A/B in one view
                ck = colour_of_body.get(NOVEL_BODY)
                sp = sc.perceive_colour(sim, colours, ck, with_form=True) if ck else []
                if sp:
                    b = min(sp, key=lambda q: float(np.linalg.norm(np.asarray(q["pos"]) - tp)))
                    tally_fix[b["shape"] if b["shape"] is not None else "None (novel)"] += 1
                else:
                    tally_fix["kein Farb-Split"] += 1
            print(f"\n  [TDIAG] {scenario}: {N} Posen, lokalisiert {found}")
            for nm, c in tally.most_common():
                mark = "  <== KORREKT" if nm == key else ("  <== BLIND" if nm != key else "")
                print(f"      als '{nm}' erkannt: {c:3d} = {100.0*c/N:5.1f}%{mark}", flush=True)
            if dists["eigen"]:
                e = np.array(dists["eigen"]); f = np.array(dists["beste_fremd"])
                print(f"      Deskriptor-Abstand zu '{key}': median {np.median(e):.2f} "
                      f"p90 {np.percentile(e,90):.2f} | bester Fremd-Abstand median {np.median(f):.2f}"
                      f" | novel_th {sc.novel_th:.2f}")
                print(f"      Anteil mit Abstand>novel_th zur eigenen Klasse: "
                      f"{100.0*np.mean(e > sc.novel_th):.0f}%  (= wird NOVEL statt '{key}')")
                print(f"      Anteil wo ein FREMD naeher liegt: {100.0*np.mean(f < e):.0f}%")
            print(f"    -- MIT Form-Split (ACT23_FORM_SPLIT: Form auf dem farb-getrennten Teil) --")
            for nm, c in tally_fix.most_common():
                mark = "  <== KORREKT" if nm == key else ""
                print(f"      als '{nm}': {c:3d} = {100.0*c/N:5.1f}%{mark}", flush=True)
        sim.d.mocap_pos[:] = saved_mp; mujoco.mj_forward(sim.m, sim.d)
        raise SystemExit(0)

    def save_state():
        """Persist the four learners + the self-discovered command objects (every episode; cheap)."""
        if not WRITE_STATE:                             # s. die Trennung Laden/Schreiben oben
            return
        try:
            os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
            base = {nm for _l, nm, _m in CommandState23.OBJECTS}
            blob = {"schema": STATE_SCHEMA, "dof": len(ARM3),
                    "bm": bm, "shape_clf": shape_clf, "world": world, "runtime": runtime,
                    "colours": colours, "colour_of_body": dict(colour_of_body),
                    "latent_goal": _lg_pack(lgoal),
                    "latent_dynamics": lat_dyn.pack(),
                    "dream_seen": [np.asarray(z) for z in dream_nov.seen],
                    "self_eval": seval,
                    "hoehe_schaetzer": hoehen_schaetzer,
                    "groessen_schaetzer": groessen_schaetzer,
                    "loslass_kopf": loslass_kopf,
                    "aufgeben_kopf": aufgeben_kopf,
                    "wort_bedeutung": {w: [np.asarray(v, float) for v in l]
                                       for w, l in wort_bedeutung.items()},
                    "blick_daten": list(blick_daten),

                    # EIGENSCHAFTS-ADRESSEN WERDEN NICHT GESPEICHERT.  Sie sind fluechtig: der
                    # Auto-Lauf schreibt sie in JEDER Episode neu aus der aktuellen Detektion.
                    # Gespeichert blieben sie als zweiter Eintrag desselben Koerpers liegen und
                    # haben beim naechsten Start act16.OBJS verdoppelt -> Absturz in run_combined
                    # (s. randomize_objects).  Der Zustand des Nutzers trug genau das:
                    # ('Neue Form 10', 'obj_X', 'shape') UND ('farbe-6 + neu-34', 'obj_X', ...).
                    "objects": [o for o in state.OBJECTS
                                if o[1] not in base and o[2] != "eigenschaft"],
                    "shape_key": {k: v for k, v in state.SHAPE_KEY.items()
                                  if k not in CommandState23.SHAPE_KEY}}
            if FOVEA_NET:                                      # task 3: persist the warmed+class-trained
                blob["fovea"] = vc.fovea                        #   hex fovea (only when the learned gaze is
                #   used) so later sessions skip the ~2-3 min warmup + selection + class training
            with open(STATE_PATH, "wb") as f:
                pickle.dump(blob, f)
        except Exception as e:
            print(f"  [Persistenz] Speichern fehlgeschlagen: {e}", flush=True)

    def choreo_log(s, _aim, _j5):
        if not D0_FREEZE:
            runtime.observe(s, act16.reactive_subgoal(s))  # label visited states for lifelong DAgger
        #   (aim, j5): the reactive teacher is a pure function of state, the phase machine is not

    def situation_feats(cmd):
        """PERCEIVED situation of `cmd` for the world model (None if the camera can't find it).  The
        privileged position is only a MATCHING aid; the features themselves are the detection's.
        The matched detection (incl. its mask-sampled grasp_cands) is kept on
        situation_feats.last_det for the grasp-point candidate selection in run_one."""
        p_ref = sim.obj_pos(cmd)[:2]
        situation_feats.last_det = None
        saved = sim.d.mocap_pos.copy()                     # perceive_all parks the markers -> restore
        dets = shape_clf.perceive_all(sim, cands=True)
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        dets = [d for d in dets if d["pos"] is not None]
        if not dets:
            return None
        best = min(dets, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"]) - p_ref)))
        if float(np.linalg.norm(np.asarray(best["pos"]) - p_ref)) > 0.05:
            return None                                    # nearest blob is a DIFFERENT object -> no honest read
        situation_feats.last_det = best
        y2, y4 = float(best["yaw"]), float(best["yaw4"])
        # ORIENTATION THROUGH THE FOVEA (user's long-term goal, first wired lever): the k=2 RING
        # PHASE the overview path reads is NOISY (measured consistency p50: long 36deg, L 21, T 45,
        # U 26); the FOVEA-style read -- local window at the tracked object + identity chroma gate +
        # PCA long axis in world coords -- reads long 1.0deg, L 1.1, T 4.9, U 11.8.  Replace the k=2
        # slots (same dims, no schema break; the old rows' yaw was ~noise, the model had little to
        # unlearn).  Cubes keep the k=4 ring phase (PCA is degenerate for squares).
        if os.environ.get("ACT23_FOVEA_YAW", "1") == "1":
            _c = colour_of_body.get(cmd)
            _mu = (np.asarray(colours.classes[_c]["mu"], float)
                   if _c is not None and _c in colours.classes else None)
            saved = sim.d.mocap_pos.copy()                 # yaw_at parks the markers -> restore
            _r = shape_clf.yaw_at(sim, np.asarray(best["pos"], float), mu=_mu,
                                  engine=os.environ.get("ACT23_YAW_SRC", "cells"))
            sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
            if _r is not None:
                y2 = float(_r[0])
        return np.concatenate([np.asarray(best["pos"], float),
                               [np.cos(2 * y2), np.sin(2 * y2), np.cos(4 * y4), np.sin(4 * y4)],
                               shape_clf.desc_embed(best["desc"]),
                               _neighbour_feats(best, dets),
                               _fovea_feats(best),
                               _body_feats(best)])

    def _body_feats(best):
        """ARMSTELLUNG als Situations-Feature -- schliesst die letzte gestrichelte Kante
        BodyModel -> WorldModel.

        7 Dimensionen: [gueltig, FK-Surprise, cos2w0, sin2w0, d_hand, cos phi, sin phi]
          FK-Surprise  log1p des Koerpermodell-Vorhersagefehlers in MILLIMETERN.  Die Kinematik lernt
                       lebenslang weiter; ist ihr Fehler gerade gross, geht die Hand nicht dorthin,
                       wo der Griff geplant wurde.  Genau wie bei der Fovea-Surprise konnte das
                       Welt-Modell diesen Stoerterm bisher nicht von einem Aktions-Fehler trennen.
          w0           START-Orientierung der Klaue (claw_yaw = Finger-Trennachse in der Welt), als
                       PHASE ueber 2*Winkel, weil eine Klaue pi-symmetrisch ist -- dieselbe
                       Konvention wie die Wrist-AKTION.  Das ist die vom Nutzer beobachtete
                       "extreme 90-Grad-Stellung" beim Episodenstart.
          d_hand/phi   Wo der Arm HERKOMMT: Abstand und Richtung von der aktuellen Hand zum Ziel,
                       im BASIS-Rahmen (dort lebt die Kinematik).  Mit arm_reset=False ist der
                       Startpunkt jede Episode ein anderer."""
        v = np.zeros(BD_DIM)
        if not BODY_FEATS:
            return v
        try:
            w0 = float(sim.claw_yaw())
            hand = np.asarray(sim.grasp_pos(), float)[:2]
            tgt = np.asarray(best["pos"], float)
            rel = tgt - hand
            d = float(np.linalg.norm(rel))
            fk = getattr(bm.body, "last_surprise", None)
            v[0] = 1.0
            v[1] = 0.0 if fk is None else float(np.clip(np.log1p(1e3 * float(fk)), 0.0, 10.0))
            v[2], v[3] = np.cos(2 * w0), np.sin(2 * w0)
            v[4] = min(d, BD_DMAX)
            if d > 1e-6:
                ph = float(np.arctan2(rel[1], rel[0]))
                v[5], v[6] = np.cos(ph), np.sin(ph)
            else:
                v[5] = 1.0
        except Exception as _e:
            if os.environ.get("ACT23_DEBUG", "0") == "1":
                print(f"    [Koerper-Feat] uebersprungen: {_e}", flush=True)
            v[:] = 0.0
        return v

    def _fovea_feats(best):
        """ZUSTAND DES FOVEA-NETZES als Situations-Feature -- schliesst die fehlende Kante
        VisualCortex -> WorldModel (vom Nutzer in der ModulViz-Grafik entdeckt).

        12 Dimensionen: [gueltig, Surprise, |top| (10)]
          gueltig   1.0 = echt gemessen (alte Zeilen 0.0, s. ensure_feat_dim)
          Surprise  sensor_error des PC-Netzes = wie gut die Fovea erklaert, was sie sieht.  Ein
                    hoher Wert heisst, der Griff wird auf einem wackligen Perzept geplant -- genau
                    die Information, die dem Welt-Modell bisher fehlte, um schwankende
                    Servo-Qualitaet von echtem Aktions-Fehler zu unterscheiden.
          |top|     BETRAG des obersten Latents (10 komplexe Dim).  Der Betrag, nicht die Phase:
                    dieselbe Konvention wie beim Formdeskriptor (|F| ist die Bedeutung, die Phase
                    die Lage).  x10 skaliert, damit die Groessenordnung zu den uebrigen Merkmalen
                    passt (roh 0.01-0.09).

        KEINE SUCHE: perceive_all hat das Objekt schon lokalisiert, also wird die Fovea nur dorthin
        gerichtet (step_id auf best["chroma"], die eigene Chromatizitaet des Objekts) und schwingt
        FOV_SETTLE Schritte ein.  Ein volles locate() waere eine Saccaden-Suche ueber bis zu 60
        Iterationen -- unnoetig, wenn die Position bereits bekannt ist.
        learn=False, damit dieses LESEN die Fovea-Gewichte nicht veraendert."""
        v = np.zeros(FOV_DIM)
        if not FOVEA_FEATS or vc is None or getattr(vc, "fovea", None) is None:
            return v
        try:
            px = np.asarray(shape_clf._world_to_px(np.asarray(best["pos"], float))[0], float)
            # MARKER PARKEN wie bei jedem anderen Wahrnehmungs-Einstieg (shape_classifier:576/599/692).
            # BUG 2026-08-03: hier fehlte das.  situation_feats stellt die Marker unmittelbar vor
            # diesem Aufruf wieder her, die Fovea sah also die magentafarbenen Zielscheiben mit --
            # und ROT ist eine TEILMENGE von Magenta (1,0,1), der dokumentierte Fehlermodus, bei dem
            # das rote Kommando die Zielscheibe lockt.  Gemessen im 141-Ep-Lauf: der FARBPFAD
            # (Wuerfel) brach auf 10% ein, der Formpfad nur auf 27%.
            _sv = sim.d.mocap_pos.copy(); shape_clf._park_markers(sim)
            try:
                img = shape_clf._render_u8(sim)             # Arm ausgeblendet, wie beim Klassifikator
            finally:
                sim.d.mocap_pos[:] = _sv; mujoco.mj_forward(sim.m, sim.d)
            for _ in range(max(1, FOV_SETTLE)):
                vc.fovea.step_id(img, px, np.asarray(best["chroma"], float), learn=False)
            d = vc.fovea.last_diag or {}
            se = float(d.get("sensor_error", 0.0))
            top = np.abs(np.asarray(vc.fovea.net.node("top").mu))
            v[0] = 1.0
            # LOGARITHMISCH, nicht linear gedeckelt: der Wert spannt Groessenordnungen -- reife Fovea
            # ~0.26, frisch aufgewaermt >=5, im Warmup bis ~180.  Ein linearer Deckel saettigt genau
            # dort, wo die Information steckt (im Rauchtest standen beide Zeilen auf dem Deckel 5.00).
            v[1] = float(np.clip(np.log1p(max(0.0, se)), 0.0, 10.0))
            v[2:2 + len(top)] = 10.0 * top[:FOV_DIM - 2]
        except Exception as _e:
            if os.environ.get("ACT23_DEBUG", "0") == "1":
                print(f"    [Fovea-Feat] uebersprungen: {_e}", flush=True)
            v[:] = 0.0
        return v

    def _neighbour_feats(best, dets):
        """NACHBAR-INFORMATION fuers Welt-Modell (Nutzerwunsch, in ModulViz die gestrichelte Kante
        ShapeClassifier -> SelfEval).  Der User hat wiederholt beobachtet, was hier fehlt: die Klaue
        SCHIEBT beim Schliessen ein Objekt weg, sie RAMMT beim Tragen einen Nachbarn, und zwei nahe
        Objekte VERSCHMELZEN zu einem Blob (Farb-/Form-Split).  All das haengt an der Nachbarschaft,
        und das Welt-Modell sah bisher nur das Zielobjekt.

        Kostet NICHTS: perceive_all liefert ohnehin ALLE Detektionen, situation_feats warf sie bisher
        weg.  Kein zusaetzliches Rendern, keine privilegierte Information -- dieselbe eigene Kamera.
        (Nicht aus der FOVEA: die ist der Aufmerksamkeitspfad auf das EINE Zielobjekt.)

        5 Dimensionen: [gueltig, d_nah, cos phi, sin phi, n_nah]
          gueltig  1.0 = diese Zeile hat echte Nachbar-Information (alte Zeilen: 0.0, s.
                   ensure_feat_dim -- ein erfundener Sachwert waere eine Luege im Trainingssatz)
          d_nah    Abstand zum naechsten Nachbarn, auf NB_DMAX gedeckelt
          phi      RICHTUNG dorthin, im OBJEKTRAHMEN (gegen die eigene yaw-Achse gedreht) und als
                   PHASE kodiert -- dieselbe Konvention wie Wrist und Neigung.  Objekt-relativ, weil
                   "Nachbar auf der Zinkenseite" etwas anderes ist als "Nachbar hinter mir", und das
                   nur im Objektrahmen ausdrueckbar ist.
          n_nah    wieviele Nachbarn innerhalb NB_DMAX liegen (Gedraenge)"""
        v = np.array([0.0, NB_DMAX, 1.0, 0.0, 0.0])
        if not NEIGHBOURS:
            return v
        p = np.asarray(best["pos"], float)
        d = [(float(np.linalg.norm(np.asarray(o["pos"], float) - p)), o)
             for o in dets if o is not best and o.get("pos") is not None]
        v[0] = 1.0                                    # gemessen -- auch "keine Nachbarn" ist Information
        near = [x for x in d if x[0] <= NB_DMAX]
        v[4] = float(len(near))
        if d:
            dist, o = min(d, key=lambda x: x[0])
            v[1] = float(min(dist, NB_DMAX))
            rel = np.asarray(o["pos"], float) - p
            phi = float(np.arctan2(rel[1], rel[0])) - float(best.get("yaw", 0.0))   # Objektrahmen
            v[2], v[3] = np.cos(phi), np.sin(phi)
        return v

    bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, LONG)
    # ACT23_SEED (default 7 = historical behaviour): scene placement + auto target picks.  Parallel
    # label-harvest WORKERS (act23_dose_workers.py) start from the SAME state pickle with the same
    # pickled module rngs -- without distinct seeds here they would replay bit-identical episodes
    # and the parallelism would collect the same data W times (user's 8%-CPU observation).
    crng = np.random.default_rng(int(os.environ.get("ACT23_SEED", "7"))); act16.run_combined._quiet = True

    def park_all():
        sim.reset_home()
        for o in ALL:
            sim.set_object(o, [0.5, -0.6], z=0.012)
        sim.m.geom_size[sim.m.body_geomadr[mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, "obj_red")]] = np.array([0.012] * 3)
        sim.set_target_marker([0.0, -0.6], z=-0.05)

    def setup_obj(cmd, p, yaw):
        park_all()
        if cmd == LONG:
            sim.m.geom_size[sim.m.body_geomadr[bid]] = np.asarray(LONG_HALF, float)
            z = float(LONG_HALF[2])
        else:
            z = 0.012
        sim.set_object(cmd, p, z=z, yaw=yaw); mujoco.mj_forward(sim.m, sim.d); sim.step(40)
        sim.set_target_marker(TARGET, z=0.001)

    def grasp_trial(cmd, wrist, gxy, grip=None, gentle=False):
        wf = None if wrist is None else (lambda s, _w=wrist: _w)
        d, _ = act16.run_combined(sim, bm.body, None, CAM, episodes=1, cmd_fixed=cmd, force="grasp",
                                  perceive_fn=lambda c: (gxy, None, "grasp"), policy_fn=None, servo=False,
                                  goal_fn=lambda c, o: TARGET, rescatter=False, wrist_fn=wf,
                                  grip_close=grip, carry_gentle=bool(gentle),
                                  log_fn=choreo_log)         # startup trials feed the runtime policy too
        return int(d)

    def grasp_gxy(cmd):
        """The PERCEIVED grasp point for a trial: shapes via select() (a U's body centre lies in its
        concavity, on no material -- privileged centre grasps would poison the trials); else privileged."""
        key = state.SHAPE_KEY.get(cmd)
        if key is not None:
            saved = sim.d.mocap_pos.copy()                     # select() parks the markers -> restore
            det = shape_clf.select(sim, key)
            sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
            if det is not None:
                return np.asarray(det["grasp_xy"], float)
        return sim.obj_pos(cmd)[:2]

    def collect_trials(cmd, label, yaw_hi):
        """Self-supervised trials on `cmd`: random pose + yaw, RANDOM action (wrist + grasp-point offset
        + grip close-angle + gentle flag), the OWN delivered/not outcome as the only label.
        act16.OBJS=[cmd]: this object IS the scene -- park_all() parks the others OUTSIDE run_combined's
        stray bounds, and with them in OBJS reposition_strays() would drop them back onto the table as
        surprise distractors.  (Restored to all objects for the steering scene.)"""
        act16.OBJS = [cmd]
        print(f"  collecting OWN trials: {label} ({NPOS}x{NTRIAL}) ...")
        for j in range(NPOS):
            p = rand_pos(crng); yaw = crng.uniform(0, yaw_hi); setup_obj(cmd, p, yaw)
            fe = situation_feats(cmd)
            if fe is None:
                continue                                       # camera can't see it here -> no honest trial
            for t in range(NTRIAL):
                w = crng.uniform(0, np.pi); setup_obj(cmd, p, yaw)
                if t == 0:                                     # anchor trial ON the structured candidate
                    off = np.zeros(2); grip = 0.0; gentle = 0.0   # grid (offset-0, firm grip): the LCB
                    #   prefers those candidates, so the model needs EVIDENCE there -- purely random
                    #   trials left them unsampled and a young model picked edge offsets + wide grips
                    #   ("Greifer schliesst nicht weit genug", carried objects slipped mid-carry)
                else:
                    off = crng.uniform(-0.008, 0.008, 2)
                    grip = float(crng.uniform(0.0, 0.4)); gentle = float(crng.integers(2))
                ok = grasp_trial(cmd, w, grasp_gxy(cmd) + off, grip, gentle)
                world.observe(fe, action_vec(off[0], off[1], w, grip, gentle), ok)
            if panel is not None and j % 2 == 0:
                panel.update(sim.render(CAM), f"Selbst-Lernen ({label}): {(j + 1) * NTRIAL}/{NPOS * NTRIAL} Versuche")

    if _loaded is not None:
        print(f"  [Persistenz] Zustand geladen: Welt-Modell {world.n()} Versuche, Runtime-Policy "
              f"{runtime.n()} Samples, offene Klassen {shape_clf.open_names} — Startup-Training übersprungen",
              flush=True)
        if os.environ.get("ACT23_RELABEL", "0") == "1":
            # NEU ETIKETTIEREN (ACT23_RELABEL, Vorgabe 0): den DAgger-Puffer mit dem AKTUELLEN Teacher
            # neu beschriften und einmal nachtrainieren -- noetig, wenn sich der Teacher geaendert
            # hat (s. RuntimePolicyModule.relabel).  Nach den Zustands-Migrationen oben, damit
            # reactive_subgoal die vollen Zeilen sieht.
            _nr, _ch = runtime.relabel(act16.reactive_subgoal)
            runtime.train(epochs=400)
            print(f"  [Neu-Etikett] {_nr} DAgger-Zeilen mit dem aktuellen Teacher neu beschriftet, "
                  f"{_ch} davon geaendert ({100.0 * _ch / max(_nr, 1):.1f} %) -- Policy nachtrainiert "
                  f"(ACT16_NEAR_ABLAGE={act16.NEAR_ABLAGE:.3f})", flush=True)
        _bad = runtime.sanitize()                              # HEAL a DAgger buffer polluted by off-table
        if _bad:                                               # perception-glitch states (897ca5a servo bug
            runtime.train(epochs=200)                          # logged px-as-metres -> a quarter of the buffer
            save_state()                                       # went absurd + wrecked the fitted policy)
            print(f"  [Reparatur] {_bad} vergiftete Policy-Samples (off-table) entfernt + Policy neu "
                  f"trainiert ({runtime.n()} sauber) — Netz-Choreo war daneben-greifend", flush=True)
    else:
        collect_trials(LONG, "langes Objekt", np.pi)
        collect_trials("obj_red", "Würfel, auch diagonal", np.pi / 2)   # cube yaw mod pi/2 (square symmetry);
        #   the descriptor is COLOUR-agnostic, so red-cube trials transfer to the green cube too
        collect_trials("obj_L", "L-Form", 2 * np.pi)                    # stage 1: the SHAPES get own trials too
        collect_trials("obj_U", "U-Form", 2 * np.pi)                    #   (self wrist/grip/offset instead of
        #   the teacher rules; the grip+gentle dims must SEE both regimes to learn the U's contingency)
        world.train(epochs=600)
        print(f"  world model trained on {world.n()} own trials.")
        runtime.train(epochs=400)
        print(f"  runtime policy (Stufe 2) trained on {runtime.n()} teacher-labelled states "
              f"({'bereit' if runtime.trained else 'zu wenig Daten'}).")
        save_state()                                           # capture the fresh startup training

    # WELT-MODELL: die EHRLICHE Guete beim Start.  Bis 2026-08-11 gab es in der Steuerung gar keine
    # Halteteil-Bewertung -- nur im Diagnose-Pfad, und die lief ueber einen BENACHBARTEN Halteteil.
    # Der ist zu leicht: aufeinanderfolgende Zeilen stammen aus demselben Lauf, und dort bleibt die
    # SZENE STEHEN (nur das kommandierte Objekt bewegt sich), die Testzeilen haben also
    # Beinah-Duplikate im Training.  Beide Zahlen werden ausgegeben, weil die DIFFERENZ der Befund
    # ist -- gemessen 0.877 gegen 0.740, und ein frischer Lauf zeigte 0.489/0.569.
    # Wonach zu steuern ist: die Zahl MIT LUECKE.  Kostet ~25s auf einer Kopie, ACT23_WM_EVAL=0 aus.
    if os.environ.get("ACT23_WM_EVAL", "1") == "1" and world.n() >= 2400:
        try:
            _na, _lu = world.generalisation_auc()
            if np.isfinite(_lu):
                print(f"  [Welt-Guete] P(Lieferung) AUC: benachbarter Halteteil {_na:.3f} "
                      f"-- MIT LUECKE {_lu:.3f} (das ist die Verallgemeinerung; danach steuern)",
                      flush=True)
        except Exception as _e:
            print(f"  [Welt-Guete] uebersprungen: {type(_e).__name__}: {_e}", flush=True)

    scene = {}                                                 # intended (body -> (xy, z, yaw)); the scene is FIXED
    #   after placement and restored per command, so only the commanded object moves.
    # DETERMINISTIC well-spread SLOTS: the workspace (x +-0.11, y 0.07..0.21, minus the base-clear disk) is too
    # small for random rejection-sampling to reliably separate 5 biggish objects -- it fails and falls back to a
    # central clump.  Fixed slots (shuffled onto the objects + small jitter) GUARANTEE a spread, non-dense scene.
    # SPACING matters: the L spans 56mm (reach ~35mm from its centre), so two shapes pointing at each other need
    # ~70mm of centre clearance or their geoms INTERPENETRATE at placement.  mj_forward doesn't resolve contacts,
    # so an overlap is INVISIBLE in the placed render -- then the first sim.step in run_combined ejects the
    # overlapping shape ("a segment snaps/twists shortly after Ausfuehren").  SIX slots, EVERY cell inside the
    # MEASURED 4-DOF grasp envelope (probes, 3-4/4 each: centre column any y, |x|<=0.06 at the top, |x|<=0.09
    # low; the mid band |x|>~0.085 / y 0.16..0.235 FAILS 0-2/4 -- pre-existing envelope hole, see REACH note).
    # Min pair 71mm at jitter +-2mm; (0,0.115) r>BASE_CLEAR=0.11.
    # OBJEKTABSTAND IN DER SZENE.  Gemessen (331-Ep-Lauf): in 42% der Episoden verschmelzen zwei
    # Objekte im Bild zu einem Blob, und diese Episoden liefern 25% statt 38% (p=0.017) -- 13
    # Prozentpunkte, der groesste gemessene Einzeleffekt.  Die alten Slots stehen minimal 75mm
    # auseinander; das klingt nach viel, aber die Objekte sind gross (L halbe Laenge 28mm, T 21mm),
    # der RAND-Abstand ist also viel kleiner als der Mittenabstand.
    # Mehr Abstand ist bei SECHS Objekten geometrisch nicht drin: der Arbeitsbereich hat das
    # dokumentierte Huellen-Loch (|x|>0.065 bei y>0.15 ist fuer den Teacher unerreichbar, s. oben)
    # plus den Basis-Freiraum, und eine Optimierung ueber 60000 Layouts holt nur 75 -> 82mm heraus.
    # Der Sprung kommt erst mit WENIGER Objekten je Szene (Optimum unter denselben Bedingungen):
    #     6 Objekte  82mm | 5 Objekte 111mm | 4 Objekte 131mm | 3 Objekte 177mm
    # ACT23_SCENE_N waehlt, wieviele Objekte GLEICHZEITIG auf dem Tisch stehen; die uebrigen werden
    # geparkt (die Kamera sieht sie nicht, curious_pick ueberspringt sie darum von selbst).
    # ACT23_SCENE_EVERY wuerfelt die Szene alle N Episoden neu und ROTIERT dabei, welche Objekte
    # stehen -- ohne das uebte ein 4-Objekt-Lauf nur vier Formen, und die unterscheiden sich stark
    # (21-56% Lieferung), was jeden Vergleich verfaelschen wuerde.
    #
    # NACHTRAG 2026-08-14, WICHTIG: der ABSTAND ist NICHT die Ursache.  Direkt nachgemessen -- bei der
    # frischen Slot-Anordnung verschmilzt GAR NICHTS, bei keiner Objektzahl, auch nicht bei den
    # heutigen 75mm (je 6 Aufbauten mit Jitter und geparkten Markern: 6/5/4/3 Objekte -> immer genau
    # 6/5/4/3 Blobs).  Im echten Lauf beginnen die Verschmelzungen erst ab Episode 4 und steigen dann
    # auf ~40%: die Objekte WANDERN im Laufe des Laufs zusammen, weil ein geliefertes Objekt am
    # Zielmarker liegen bleibt und die Marker nah beieinander stehen.
    # Damit ist SCENE_N das falsche Mittel; der wirksame Teil dieses Umbaus ist SCENE_EVERY, das die
    # angesammelte Unordnung periodisch aufloest.
    # VORGABE = bisheriges Verhalten (6 Objekte, Szene steht den ganzen Lauf).
    SCENE_SLOTS = {
        6: [(-0.06, 0.24), (0.06, 0.24), (0.0, 0.19), (-0.09, 0.115), (0.09, 0.115), (0.0, 0.115)],
        5: [(-0.065, 0.24), (0.064, 0.24), (0.0, 0.149), (0.095, 0.091), (-0.095, 0.09)],
        4: [(0.065, 0.24), (-0.065, 0.221), (0.057, 0.107), (-0.083, 0.091)],
        3: [(0.0, 0.24), (0.095, 0.09), (-0.095, 0.09)],
    }
    SCENE_N = max(3, min(6, int(os.environ.get("ACT23_SCENE_N", "4"))))     # Vorgabe 2026-08-30
    SCENE_EVERY = int(os.environ.get("ACT23_SCENE_EVERY", "10"))   # Vorgabe 2026-08-30 (0 = nie)
    SLOTS = SCENE_SLOTS[SCENE_N]
    PARK_XY = [0.5, -0.6]                                          # ausserhalb des Kamerabildes
    scene_slots = {}                                           # body -> slot index (finds the FREE slot)
    # DER SOCKEL ALS STUETZE (s. SOCKEL oben).  Er bekommt KEINEN der SLOTS, sondern eine eigene
    # feste Stelle -- ein Slot ist fuer einen 24-mm-Koerper bemessen, die Platte ist 70 mm breit.
    # Der Abstand zu jedem Slot wird beim Start NACHGERECHNET und gemeldet.
    # DIE SCHWELLE IST GEMESSEN, NICHT GERECHNET, und das war eine Korrektur: zuerst stand hier
    # die Ueberlappungsrechnung (Sockel-Halbdiagonale 49 mm + Objekt-Halbdiagonale 17 mm = 66 mm).
    # Das ist die falsche Groesse -- Blobs VERSCHMELZEN, lange bevor sie sich beruehren.  Gemessen
    # (acht Richtungen, `perceive_all` zaehlt die Detektionen): getrennt ab **60 mm entlang der
    # Achsen und 80 mm auf den Diagonalen** -- die Ecken der quadratischen Platte reichen am
    # weitesten. Maßgeblich ist der schlechteste Fall.
    SOCKEL_FREI = 0.080
    if SOCKEL:
        # ZWEI GRUNDRISSE (ACT23_SOCKEL2=1, Vorgabe 0).  Dann steht je Szene EINE der beiden
        # Platten in der Welt und die andere geparkt -- nicht beide gleichzeitig.  Grund, und er
        # ist gemessen: die Groessenachse des Agenten saettigt bei Moebeln (GROESSEN_BAENDER endet
        # bei 6,5 px, beide Platten lesen "dick"), also koennte eine Adresse die beiden GAR NICHT
        # auseinanderhalten -- jede Episode fiele mehrdeutig auf den Marker zurueck.  Nacheinander
        # ist die Adresse eindeutig, und der Schaetzer sieht trotzdem beide Grundrisse.
        # Das Parken erledigt die Kandidatenwahl von selbst: `_ziel_adresse_wuerfeln` filtert
        # ueber `_geparkt_jetzt`.  In STUETZEN stehen BEIDE, damit auch die geparkte Platte
        # niemals als greifbares Objekt in Frage kommt.
        state.STUETZEN = list(SOCKEL_FORMEN)
        _sxy = np.asarray(SOCKEL_XY, float)
        _mind = min(float(np.linalg.norm(_sxy - np.asarray(s, float))) for s in SLOTS)
        print(f"  [Sockel] steht bei [{_sxy[0]:+.3f},{_sxy[1]:+.3f}], naechster Objekt-Slot "
              f"{1000 * _mind:.0f} mm entfernt (gemessen noetig {1000 * SOCKEL_FREI:.0f} mm)"
              + ("" if _mind >= SOCKEL_FREI else
                 "  -- ZU NAH: Objekte verschmelzen mit dem Sockel, die Zieladresse trifft dann "
                 "den gemeinsamen Blob-Schwerpunkt statt die Platte"), flush=True)
        if _mind < SOCKEL_FREI + 0.005:
            # NICHT NUR MECKERN, SONDERN DIE BESTE STELLE NENNEN.  Der Arbeitsraum ist 240 x 170 mm;
            # mit einer 70-mm-Platte und vier 24-mm-Koerpern ist er knapp, und wo genau noch Platz
            # ist, haengt an ACT23_SCENE_N (jede Slot-Zahl hat ein eigenes Muster).  Die Suche
            # laeuft ueber ein grobes Raster im Arbeitsraum und meldet das Optimum samt der
            # Slot-Zahl, mit der es reicht -- billiger als vom Nutzer geratene Koordinaten.
            from pc_cvnn.pc_act14 import REACH_XY as _RX
            _best, _bp, _bn = -1.0, None, None
            for _n, _sl in sorted(SCENE_SLOTS.items()):
                for _gx in np.linspace(_RX[0][0] + 0.04, _RX[1][0] - 0.04, 17):
                    for _gy in np.linspace(_RX[0][1] + 0.04, _RX[1][1] - 0.04, 17):
                        _q = np.array([_gx, _gy])
                        if float(np.linalg.norm(_q)) < 0.10:       # Sockelfreiheit des Arms
                            continue
                        _d = min(float(np.linalg.norm(_q - np.asarray(s, float))) for s in _sl)
                        if _d > _best:
                            _best, _bp, _bn = _d, _q, _n
            print(f"  [Sockel] bester Platz im Raster: [{_bp[0]:+.3f},{_bp[1]:+.3f}] mit "
                  f"ACT23_SCENE_N={_bn} -> {1000 * _best:.0f} mm Freiraum.  Setzen mit "
                  f"ACT23_SOCKEL_XY={_bp[0]:.3f},{_bp[1]:.3f}", flush=True)
        # UND DIE UNVERMEIDLICHE HAELFTE: ein erfolgreich abgelegtes Objekt BLEIBT auf dem Sockel
        # (die Aufraeumschleife stellt nur NICHT-kommandierte Koerper zurueck).  Danach ist der
        # Sockel-Blob per Bauart verschmolzen -- gemessen wird ein Wuerfel auf der Platte in 0 von
        # 25 Stellen eine eigene Detektion (wiki/befunde/sockel-verschluckt-den-stapel.md).  Das
        # ist kein Layoutfehler, sondern die Aufgabe: ab dem ersten Stapel adressiert "auf den
        # Sockel" einen Blob, der den Stapel enthaelt.
        print("  [Sockel] Hinweis: ein abgelegtes Objekt bleibt oben liegen; ab dann ist der "
              "Sockel-Blob verschmolzen und die Zieladresse wird mehrdeutig.", flush=True)
        scene["sockel"] = (_sxy.copy(), SOCKEL_HOEHEN[0] / 2.0, 0.0)
        if len(SOCKEL_FORMEN) > 1:
            for _s in SOCKEL_FORMEN[1:]:
                scene[_s] = (np.array(PARK_XY, float), 0.004, 0.0)
            print(f"  [Sockel] {len(SOCKEL_FORMEN)} Auflagenformen im Wechsel "
                  f"({', '.join(SOCKEL_FORMEN)}) -- je Szene steht EINE Platte, die anderen sind "
                  f"geparkt.  Die Adresse bliebe sonst mehrdeutig: alle lesen im Groessenband "
                  f"'dick'.", flush=True)
            if len(SOCKEL_FORMEN) >= 3 and HOEHE_SEHEN:
                print("  [Hoehe] Hinweis: mit drei Auflagenformen ist die SCHAETZUNG gemessen "
                      "schlechter (45-62 % richtige Stufe statt 92 %), die Stapelquote aber "
                      "nicht (85 gegen 88 %) -- die Fehlschlaege sind seitlich, nicht senkrecht. "
                      " s. wiki/befunde/drei-auflagen-im-lauf.md", flush=True)

    # DIE PLATTE VON HAND (GUI, Nutzerwunsch 2026-10-01): "aus" parkt sie wie ein nicht stehendes
    # Objekt, "xy" ist die zuletzt gewaehlte Stelle.  _sockel_setzen respektiert beides, damit
    # "Objekte neu" eine ausgeblendete oder versetzte Platte nicht zurueckholt.
    platte = {"aus": SOCKEL_AUS > 0, "aktiv": SOCKEL_FORMEN[0], "xy": np.asarray(SOCKEL_XY, float),
              "farbe": (0.05, 0.05, 1.0)}

    def _platte_stellen(steht_xy):
        """Alle Rasterstellen im Arbeitsraum mit >= SOCKEL_FREI zu jedem stehenden Objekt und
        ausserhalb der Sockelfreiheit des Arms (dasselbe Raster wie SOCKEL_WANDERT)."""
        from pc_cvnn.pc_act14 import REACH_XY as _RX
        _kand = []
        for _gx in np.linspace(_RX[0][0] + 0.035, _RX[1][0] - 0.035, 25):
            for _gy in np.linspace(_RX[0][1] + 0.035, _RX[1][1] - 0.035, 25):
                _q = np.array([_gx, _gy])
                if float(np.linalg.norm(_q)) < 0.10:
                    continue
                if all(float(np.linalg.norm(_q - np.asarray(s, float))) >= SOCKEL_FREI for s in steht_xy):
                    _kand.append(_q)
        return _kand

    def _sockel_setzen(steht_xy):
        """Den Sockel fuer eine NEUE SZENE setzen: Stelle und Hoehe (s. SOCKEL_WANDERT/_HOEHEN).

        Ohne die beiden Schalter unveraendert -- dann bleibt er, wo er steht, und behaelt die erste
        Hoehe.  Mit ihnen: Hoehe aus SOCKEL_HOEHEN gewuerfelt, Stelle aus einem Raster im Arbeitsraum
        mit >= SOCKEL_FREI zu jedem STEHENDEN Objekt (nicht zu jedem Slot -- was geparkt ist, stoert
        nicht) und ausserhalb der Sockelfreiheit des Arms.  Findet sich keine Stelle, bleibt die alte
        und es wird laut gesagt -- ein stiller Rueckfall auf den festen Ort waere genau die
        Verwechslung, die der Schalter beheben soll.
        DIE HOEHE AENDERT DIE GEOMETRIE ZUR LAUFZEIT: geom_size[2] und geom_rbound.  Das ist fuer
        EINEN Einzelkasten zulaessig (set_object_size deformiert nur zusammengesetzte Koerper, s.
        Invarianten); rbound muss mit, sonst uebersieht die Kollisionsvorpruefung die neue Kante.
        """
        if not SOCKEL:
            return
        # WELCHE PLATTE diese Szene traegt (s. SOCKEL2).  Die andere wird geparkt; damit faellt sie
        # von selbst aus der Kandidatenliste von `_ziel_adresse_wuerfeln` (die filtert ueber
        # `_geparkt_jetzt`), und die Adresse bleibt eindeutig.
        _aktiv = SOCKEL_FORMEN[int(crng.integers(len(SOCKEL_FORMEN)))]
        platte["aktiv"] = _aktiv
        for _s in SOCKEL_FORMEN:
            if _s != _aktiv or platte["aus"]:
                scene[_s] = (np.array(PARK_XY, float), 0.004, 0.0)
        if platte["aus"]:
            state.ZIEL_SPERRE = [platte["xy"].copy()] if SOCKEL_AUS == 2 else []
            print("  [Sockel] neue Szene: Platte ausgeblendet"
                  + (" (Ziele meiden ihre Stelle, ACT23_SOCKEL_AUS=2)" if SOCKEL_AUS == 2 else ""),
                  flush=True)
            return
        _bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, _aktiv)
        _g = int(sim.m.body_geomadr[_bid])
        _h = SOCKEL_HOEHEN[int(crng.integers(len(SOCKEL_HOEHEN)))] if len(SOCKEL_HOEHEN) > 1 \
            else SOCKEL_HOEHEN[0]
        sim.m.geom_size[_g][2] = _h / 2.0
        sim.m.geom_rbound[_g] = float(np.linalg.norm(sim.m.geom_size[_g]))
        _xy = np.asarray(scene.get(_aktiv, (np.asarray(SOCKEL_XY, float),))[0], float)
        if float(np.linalg.norm(_xy - np.asarray(PARK_XY, float))) < 0.05:
            _xy = platte["xy"].copy()                      # kam gerade aus dem Parkhaus: an die zuletzt
            #   gewaehlte Stelle (ohne GUI-Eingriff ist das SOCKEL_XY, wie bisher)
        if not SOCKEL_WANDERT and any(float(np.linalg.norm(_xy - np.asarray(q, float))) < SOCKEL_FREI
                                      for q in steht_xy):
            # VON HAND VERSETZT, und die neue Szene stellt ein Objekt daneben (die Slots wissen von
            # der Platte nichts).  An der festen Vorgabestelle tritt das nie ein (86 mm, s. oben).
            _kand = _platte_stellen(steht_xy)
            if _kand:
                _xy = min(_kand, key=lambda q: float(np.linalg.norm(q - _xy)))
                print(f"  [Sockel] gewaehlte Stelle kollidiert mit der neuen Szene -- naechste freie "
                      f"[{_xy[0]:+.3f},{_xy[1]:+.3f}]", flush=True)
        if SOCKEL_WANDERT:
            _kand = _platte_stellen(steht_xy)
            if _kand:
                _xy = _kand[int(crng.integers(len(_kand)))]
            else:
                print(f"  [Sockel] KEINE Stelle mit {1000 * SOCKEL_FREI:.0f} mm Freiraum -- bleibt, wo er "
                      f"war.  Mit ACT23_SCENE_N=4 ist der Arbeitsraum dafuer zu klein.", flush=True)
        scene[_aktiv] = (_xy.copy(), _h / 2.0, 0.0)
        platte["xy"] = _xy.copy()
        print(f"  [Sockel] neue Szene: {_aktiv} "
              f"({2000 * float(sim.m.geom_size[_g][0]):.0f} mm Grundriss) bei "
              f"[{_xy[0]:+.3f},{_xy[1]:+.3f}], Hoehe {1000 * _h:.0f} mm", flush=True)

    def platte_steuern(aktion, xy=None, rgb=None):
        """GUI: die Platte ein-/ausblenden, versetzen, umfaerben.  Liefert die Meldung fuer die Zeile.

        Das ist UMGEBUNGSGESTALTUNG wie "Objekte neu" oder ein versetzter Marker -- der Agent
        bekommt davon nichts gesagt, er sieht nur die veraenderte Szene.  Laeuft nur zwischen
        Episoden (die GUI merkt waehrend einer Episode vor), der Arm steht dann zu Hause.
        Ein Objekt, das AUF der Platte liegt, bleibt, wo es ist, und faellt beim Versetzen oder
        Ausblenden auf den Tisch."""
        _akt = platte["aktiv"]
        _bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, _akt)
        _hz = float(sim.m.geom_size[int(sim.m.body_geomadr[_bid])][2])
        _halb = float(sim.m.geom_size[int(sim.m.body_geomadr[_bid])][0])
        # was STEHT gerade: echte Lage, nicht `scene` (gelieferte Objekte sind gewandert); was auf
        # der Platte liegt (hoeher als ein Tischobjekt), zaehlt nicht als Hindernis
        _steht = []
        for nm in dict.fromkeys(n for _l, n, _m in state.OBJECTS):
            _p = sim.obj_pos(nm)
            if float(np.linalg.norm(_p[:2] - np.asarray(PARK_XY, float))) < 0.05:
                continue
            if float(_p[2]) > 0.016 and float(np.max(np.abs(_p[:2] - sim.obj_pos(_akt)[:2]))) < _halb:
                continue
            _steht.append(_p[:2].copy())

        def _hinstellen(q):
            sim.set_object(_akt, q, z=_hz, yaw=0.0)
            scene[_akt] = (np.asarray(q, float).copy(), _hz, 0.0)
            platte["xy"] = np.asarray(q, float).copy(); platte["aus"] = False
            state.ZIEL_SPERRE = []

        if aktion == "aus":
            if platte["aus"]:
                return "Platte ist schon ausgeblendet"
            for _s in SOCKEL_FORMEN:
                sim.set_object(_s, np.asarray(PARK_XY, float), z=0.004, yaw=0.0)
                scene[_s] = (np.array(PARK_XY, float), 0.004, 0.0)
            platte["aus"] = True
            if state.ziel_body_fix in SOCKEL_FORMEN:     # ein Bezug auf eine unsichtbare Platte
                state.ziel_body_fix = None
            if state.ziel_bezug is not None and state.ziel_bezug.get("body") in SOCKEL_FORMEN:
                state.ziel_bezug = None
            msg = "Platte ausgeblendet"
        elif aktion == "an":
            if not platte["aus"]:
                return "Platte ist schon sichtbar"
            q = platte["xy"]
            if any(float(np.linalg.norm(q - s)) < SOCKEL_FREI for s in _steht):
                _k = _platte_stellen(_steht)
                if not _k:
                    return "Kein Platz für die Platte (80 mm Abstand zu jedem Objekt nötig)"
                q = min(_k, key=lambda c: float(np.linalg.norm(c - q)))
            _hinstellen(q)
            msg = f"Platte eingeblendet bei [{q[0]:+.3f}, {q[1]:+.3f}]"
        elif aktion == "wuerfeln":
            _k = _platte_stellen(_steht)
            if not _k:
                return "Keine Stelle mit 80 mm Abstand zu allen Objekten frei"
            q = _k[int(crng.integers(len(_k)))]
            _hinstellen(q)
            msg = f"Platte -> [{q[0]:+.3f}, {q[1]:+.3f}]"
        elif aktion == "setzen":
            from pc_cvnn.pc_act14 import REACH_XY as _RX
            q = np.asarray(xy, float)[:2]
            if not (_RX[0][0] <= q[0] <= _RX[1][0] and _RX[0][1] <= q[1] <= _RX[1][1]) \
                    or float(np.linalg.norm(q)) < 0.10:
                return "Stelle ausserhalb des Arbeitsbereichs (oder zu nah am Arm)"
            _d = min((float(np.linalg.norm(q - s)) for s in _steht), default=1.0)
            if _d < _halb + 0.017:                       # Halbdiagonale Objekt: die Platte laege IM Objekt
                return f"Zu nah an einem Objekt ({1000 * _d:.0f} mm) -- die Platte würde es rammen"
            _hinstellen(q)
            msg = f"Platte -> [{q[0]:+.3f}, {q[1]:+.3f}]"
            if _d < SOCKEL_FREI:                         # erlaubt, aber laut: gemessene Schranke
                msg += f"  (nur {1000 * _d:.0f} mm zum Nachbarn: Blobs verschmelzen unter 80 mm)"
        elif aktion == "farbe":
            rgb = tuple(float(v) for v in rgb)
            for _s in SOCKEL_FORMEN:
                for _g in _geoms_of(_s):
                    sim.m.geom_rgba[_g][:3] = rgb
            platte["farbe"] = rgb
            _ch = np.asarray(rgb) / sum(rgb)
            _abst = min(float(np.linalg.norm(_ch - np.asarray(v[:3], float) / float(np.sum(v[:3]))))
                        for v in _FARB_PALETTE.values())
            msg = (f"Plattenfarbe {dict((tuple(c), n) for c, n in PLATTEN_FARBEN).get(rgb, rgb)}"
                   f" (Chroma-Abstand zur naechsten Objektfarbe {_abst:.2f}"
                   + (" -- unter 0,12: teilt eine Farbklasse!)" if _abst < 0.12 else ")"))
        else:
            return f"unbekannte Platten-Aktion {aktion}"
        mujoco.mj_forward(sim.m, sim.d)
        sim.step(30)                                     # setzen lassen (Arm steht zu Hause)
        state.sync_active()
        print(f"  [Platte] {msg}", flush=True)
        return msg

    # ERFAHRUNGS-GRUPPE fuer den Block-Bootstrap des Welt-Modells (s. world_model._bootstrap_blocks).
    # Eine Gruppe = eine STEHENDE SZENE innerhalb EINES Laufs.  Genau das ist die Einheit, ueber die
    # die Zeilen korreliert sind: die Szene wird beim Start (und auf Knopfdruck) gewuerfelt und
    # bleibt danach stehen -- run_one stellt alle NICHT kommandierten Objekte nach jeder Episode
    # wieder her, es bewegt sich also nur das kommandierte.
    # Das ist EIGENWAHRNEHMUNG, kein privilegiertes Weltwissen: der Agent weiss, wann er die Szene
    # neu aufgebaut hat, so wie ein Kind weiss, dass das eine durchgehende Sitzung war.
    exp_group = {"lauf": f"{os.getpid()}-{int(_time_mod.time())}", "szene": 0}

    def group_id():
        return f"{exp_group['lauf']}:{exp_group['szene']}"

    def _geparkt_jetzt(nm):
        """Steht `nm` gerade ABSICHTLICH ausserhalb der Szene? (s. SCENE_N)"""
        e = scene.get(nm)
        if e is None:
            return False
        return float(np.linalg.norm(np.asarray(e[0], float) - np.asarray(PARK_XY, float))) < 0.05

    def _probe_entdeckt():
        """Ist der Probe-Koerper versorgt, also nicht mehr "neu"?

        VORGABE: er traegt eine Formklasse (state.SHAPE_KEY) -- das ist der einzige Weg, auf dem er
        bisher kommandierbar werden konnte.  MIT ACT23_EIG_DIREKT gibt es einen zweiten: eine
        Eigenschafts-Adresse ohne Klasse.  Wird die hier nicht mitgezaehlt, glaubt der Erzeuger den
        Koerper weiter fuer unentdeckt und stellt ihn ZUSAETZLICH hin, obwohl randomize_objects ihm
        laengst einen regulaeren Platz gibt -- genau der Doppelplatz-Fehler, der am 2026-08-21
        45-mal aufgetreten ist.  Und die Probe-Rolle wanderte nie weiter.
        """
        return (NOVEL_BODY in state.SHAPE_KEY
                or (EIG_DIREKT and NOVEL_BODY in state.EIGENSCHAFT))

    def randomize_objects():
        exp_group["szene"] += 1                                # neue stehende Szene -> neue Gruppe
        sim.reset_home()
        # EIN EINTRAG JE KOERPER.  state.OBJECTS ist eine Liste von ADRESSEN, nicht von Koerpern:
        # seit dem Eigenschafts-Kommando kann derselbe Koerper zweimal drin stehen (einmal ueber
        # den Namen, einmal ueber Farbe/Form/Groesse).  Ungefiltert bekam er zwei Slots, und
        # act16.OBJS enthielt ihn doppelt -- dort rechnet run_combined die Ablenker-Stichprobe mit
        # len(OBJS)-1, waehrend others(cmd) BEIDE Vorkommen entfernt: ValueError "Cannot take a
        # larger sample than population" (vom Nutzer gemeldet 2026-09-05, Absturz in Episode 0).
        # VORRANG fuer den Nicht-Eigenschafts-Eintrag: nur der traegt das echte Verfahren, und
        # daran haengt die Ablagehoehe ("long" -> LONG_HALF[2] statt 0.012).
        _vorrang = {}
        for _l, nm, m in state.OBJECTS:
            if nm not in _vorrang or (_vorrang[nm] == "eigenschaft" and m != "eigenschaft"):
                _vorrang[nm] = m
        bodies = list(_vorrang.items())
        if NOVEL_BODY in scene and all(nm != NOVEL_BODY for nm, _ in bodies):
            bodies.append((NOVEL_BODY, "shape"))               # introduced but not yet discovered: keep it in play
        # WELCHE Objekte stehen: bei SCENE_N < len(bodies) rotiert das Fenster ueber die Liste, damit
        # ueber den Lauf jedes Objekt gleich oft auf dem Tisch steht (sonst uebte ein kleiner Aufbau
        # immer dieselben Formen).  Die uebrigen werden geparkt.
        # PLATZ FUER DEN PROBE-KOERPER freihalten: laeuft ein Neuheits-Versuch, stellt
        # spawn_novel_shape zusaetzlich den Probe-Koerper hin.  Belegen die regulaeren Objekte schon
        # ALLE sichtbaren Slots, landet er auf einem besetzten -- und verschmilzt sofort mit dessen
        # Nachbarn, womit die ganze Aneignungsmessung wieder an Blob-Verschmelzung scheitert (der
        # Fehlermodus aus b8d118e).  Darum steht ein regulaeres Objekt weniger.
        # ... ABER NUR, SOLANGE ER NOCH NICHT ENTDECKT IST.  Ist der Probe-Koerper laengst als Kommando
        # registriert (state.SHAPE_KEY), ist er ein GANZ NORMALES Objekt in `bodies` -- dann bekaeme er
        # einen reservierten Sonderplatz UND einen regulaeren, und es stuende ein Objekt weniger da als
        # eingestellt.  Genau das ist dem Nutzer am 2026-08-21 aufgefallen: ACT23_SCENE_N=4 gesetzt, nur
        # DREI Objekte auf dem Tisch, weil das Kreuz inzwischen "Neue Form 10" ist.
        _probe_offen = NOVEL_EVERY > 0 and not _probe_entdeckt()
        _n_steht = max(1, SCENE_N - (1 if _probe_offen else 0))
        _k = len(bodies)
        _rot = (exp_group["szene"] * _n_steht) % max(_k, 1)
        _steht = [bodies[(_rot + i) % _k] for i in range(min(_n_steht, _k))]
        _geparkt = [b for b in bodies if b not in _steht]
        order = list(range(len(SLOTS))); crng.shuffle(order)   # random object<->slot assignment (variety)
        scene_slots.clear()
        for (nm, m), si in zip(_steht, order):
            p = np.array(SLOTS[si], float) + crng.uniform(-0.002, 0.002, 2)   # small jitter
            z = float(LONG_HALF[2]) if m == "long" else 0.012
            if HOEHEN:                                         # neue Hoehe je Szene (s. HOEHEN)
                _hoehe[nm] = float(HOEHEN[int(crng.integers(len(HOEHEN)))]) / 2.0
                z = _hoehe[nm]
            yaw = crng.uniform(0, np.pi) if m == "long" else crng.uniform(0, 2 * np.pi)
            scene[nm] = (p, z, float(yaw)); scene_slots[nm] = si
        for nm, m in _geparkt:                                 # geparkt: bleibt in `scene` (nichts
            scene[nm] = (np.array(PARK_XY, float),             #   stromabwaerts bricht), steht aber
                         _hoehe.get(nm, float(LONG_HALF[2]) if m == "long" else 0.012), 0.0)   #   ausserhalb des Bildes
        if HOEHEN:
            print("    [Hoehen] " + ", ".join(f"{nm} {2000 * _hoehe[nm]:.0f}mm" for nm, _m in _steht
                                              if nm in _hoehe), flush=True)
        if _geparkt:
            print(f"    [Szene] {len(_steht)} Objekte auf dem Tisch (min. Abstand "
                  f"{1000*min(np.hypot(a[0]-b[0], a[1]-b[1]) for a, b in __import__('itertools').combinations(SLOTS, 2)):.0f}mm), "
                  f"geparkt: {', '.join(nm for nm, _ in _geparkt)}", flush=True)
        # DIE GEWUERFELTE SZENE AUCH AN act16 DURCHREICHEN.  run_combined baut zu Beginn JEDER Episode
        # seine eigene Szene auf: keep = [cmd] + Ablenker aus act16.OBJS, und weil act16.SCENE_N beim
        # Start auf len(OBJS) gesetzt wird (Absicht: "never PARKS a distractor off-table"), ist keep =
        # ALLE.  Ohne die naechsten Zeilen holt act16 die eben geparkten Objekte sofort zurueck --
        # ACT23_SCENE_N wirkte dann nur einen Wimpernschlag lang.  GEMELDET vom Nutzer 2026-08-21 mit
        # Screenshot: SCENE_N=5 gesetzt, sichtbar waren alle SIEBEN Koerper, dicht gedraengt und teils
        # ueberlappend -- genau die Nachbarschaft, aus der die Verschmelzungs-Phantome entstehen.
        # Die Kontinuitaets-Absicht bleibt gewahrt: INNERHALB eines Szenen-Fensters (ACT23_SCENE_EVERY)
        # bleibt die Menge fest, es teleportiert also nichts je Episode -- gewechselt wird nur beim
        # Wuerfeln.  Ein Kommando auf ein geparktes Objekt stellt es weiterhin hin (keep enthaelt cmd).
        act16.OBJS = list(dict.fromkeys(nm for nm, _m in _steht))   # Koerper, nicht Adressen
        act16.SCENE_N = len(act16.OBJS)
        _sockel_setzen([scene[nm][0] for nm, _m in _steht])   # Stelle + Hoehe je Szene (s. dort)
        place_all()
        open_set_glance()                                      # lifelong open-set look at the fresh scene
        if panel is not None:                                  # show the placed scene immediately (decide from it)
            panel.update(sim.render(CAM), "Szene platziert — Objekt wählen und Ausführen")
            if vc.viz is not None:                             # RE-CENTER the fovea on a fresh scene: the old
                g = np.array([RES / 2.0, RES / 2.0])           #   gaze points at where an object USED to be --
                vc._P["state"]["gaze"] = g                     #   over the new layout that looks like "the fovea
                img = sim.render(CAM)                          #   still focuses an old position" (user-observed;
                arr = vc.fovea.step(img, g, vc._P["state"]["cmd"], False)   # aiming itself always re-perceives).
                vc.viz.fovea(img, g, vc.fovea._ek(), np.clip(arr[:, :, 1:], 0, 1),
                             "Szene neu — Fovea zentriert")    # box + cells + image consistent (learn=False)

    _novel_half = {"h": None}          # aktuell erzwungene Proportion des Probe-Koerpers (s. _set_sizes)

    _hoehe = {}                       # Koerper -> halbe Hoehe (s. HOEHEN); leer = Modellhoehe

    def _hoehe_anwenden():
        """Alle Teile jedes Koerpers in _hoehe auf seine halbe Hoehe setzen (s. HOEHEN)."""
        for _nm, _h in _hoehe.items():
            for _g in _geoms_of(_nm):
                sim.m.geom_size[_g][2] = float(_h)
                sim.m.geom_rbound[_g] = float(np.linalg.norm(sim.m.geom_size[_g]))

    def _set_sizes():
        sim.m.geom_size[sim.m.body_geomadr[mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, "obj_red")]] = np.array([0.012] * 3)
        sim.m.geom_size[sim.m.body_geomadr[bid]] = np.asarray(LONG_HALF, float)   # obj_blue stays elongated
        for nm, h0 in shape_half0.items():                 # repair the L/U FIRST geom too: any set_object_size
            if nm == NOVEL_BODY and _novel_half["h"] is not None:
                # ABSICHTLICH verformter Probe-Koerper (ACT23_NOVEL_EVERY) -- NICHT zuruecksetzen.
                # GEFUNDEN 2026-08-14: _set_sizes laeuft am ENDE JEDER EPISODE, und shape_half0
                # enthaelt obj_T.  Die neue Proportion war damit eine Episode spaeter wieder weg,
                # der Agent sah die neue Form hoechstens EINMAL statt der noetigen dreimal -- das
                # ist der wahre Grund, warum in beiden A/B-Laeufen keine Klasse entstand (und
                # warum beide bitgleich waren: die Neuheit war nie lange genug da, um irgendeine
                # Schwelle zu erreichen).
                sim.m.geom_size[sim.m.body_geomadr[
                    mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)]] = np.asarray(
                        _novel_half["h"], float)
                continue
            sim.m.geom_size[sim.m.body_geomadr[mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)]] = h0
            #   on a composite body hits only its first geom and silently DEFORMS the shape ("a segment turns
            #   90 deg") -- with PERSIST above this is a no-op, but the shape must never stay deformed.
        _hoehe_anwenden()                      # NEUE HOEHEN (s. HOEHEN) zuletzt, ueber allem anderen

    def place_all():
        _set_sizes()
        for nm, (p, z, yaw) in scene.items():
            sim.set_object(nm, p, z=z, yaw=yaw)
        mujoco.mj_forward(sim.m, sim.d)
        sim.step(60)                          # SETTLE: resolve any residual contact NOW (arm at home, no reach),
        #   so the shown "Szene platziert" == the physical state run_combined starts from -- nothing can snap
        #   on the first step of Ausfuehren.  With the well-spaced slots this is a no-op (objects stay put).
        state.sync_active()

    # ------------------------------------------------------------------
    # OPEN-SET form learning: the reserve probe body obj_T was NEVER seen by any training phase (parked
    # off-table in the XML).  "Objekt hinzufügen" drops it into a free slot; the net must DISCOVER it
    # (consistent novel |F| sightings -> a self-labelled class, shape_classifier.observe_scene) and it
    # then becomes commandable through the SAME form pipeline as L/U (select/track/grasp by class name).
    # NOTE an HONEST side discovery: the LONG bar (obj_blue, resized at runtime) is ALSO form-untrained,
    # so the lifelong glances typically self-label IT first ('neu-1') -- correct open-set behaviour, its
    # sightings then claim that class instead of feeding the buffer.  It is not REGISTERED as a command
    # (it has its own button/path already); only obj_T maps to a new button, usually as 'neu-2'.
    # ------------------------------------------------------------------
    # WELCHER Koerper als Neuheit dient.  obj_T ist als Neuheit VERBRAUCHT (laengst entdeckt und als
    # "Neue Form 7" kommandierbar); obj_X (Kreuz) ist der frische Ersatz.  Einfache Formen sind knapp --
    # darum die Persistenz-Sperre gleich daneben.
    NOVEL_BODY = os.environ.get("ACT23_NOVEL_BODY", "obj_T")
    # Nachversuch der Farbbindung, s. unten.  ACT23_BIND_RETRY=0 stellt das alte Verhalten her
    # (Bindung nur im Moment der Klassengeburt).
    # VORGABE AUS (2026-08-31, nach dem ersten Test): der Nachversuch band auf EINER EINZIGEN
    # Sichtung und traf daneben -- obj_X bekam 'farbe-15' (Abstand 0,239) angeheftet.  Grund: obj_X'
    # GERENDERTE Chroma [0.414,0.456,0.130] faellt mit Abstand 0,042 in 'farbe-4', also in obj_L's
    # Klasse; die ist vergeben, der Wachhund lehnte sie richtig ab -- und der Nachversuch griff
    # daneben zur naechstbesten freien.  Eine FALSCHE Bindung ist schlimmer als gar keine, denn der
    # Form-Split sucht dann nach dem falschen Farbton.
    # BEVOR das wieder eingeschaltet wird, braucht es eine Bestaetigung ueber mehrere Blicke
    # (wie NOVEL_CONFIRM) UND eine Hoechstdistanz.  Der eigentliche Befund dahinter: obj_X und obj_L
    # sind im gerenderten Bild farblich fast gleich -- fuer obj_X gibt es ueber die FARBE keine
    # Loesung, der farbfreie Split (ACT_SHAPE_SPLIT) ist der richtige Weg.
    BIND_RETRY = os.environ.get("ACT23_BIND_RETRY", "0") != "0"
    BIND_MAX_D = float(os.environ.get("ACT23_BIND_MAX_D", "0.12"))   # = colour_openset.TH
    BIND_CONFIRM_N = int(os.environ.get("ACT23_BIND_CONFIRM", "3"))  # wie NOVEL_CONFIRM
    _bind_votes = {}

    # BINDUNG AN DEN KOMMANDO-KNOPF: nicht bei der GEBURT, sondern nach WIEDERHOLTER Uebereinstimmung.
    # WARUM (gemessen 2026-08-15, Debug-Lauf ueber 30 Episoden mit dem Kreuz obj_X): aus demselben Kreuz
    # wurden ZWEI Klassen geboren -- 'neu-285' auf einem VERSCHMOLZENEN Fleck (Kreuz + blauer Wuerfel,
    # 1019px, 23mm neben dem Kreuz) und 'neu-286' auf dem sauberen Kreuz (382px, 0mm).  Die alte Bindung
    # nahm die erste Klasse, die EINMAL innerhalb von 40mm sass -- das war das Gespenst (23mm < 40mm).
    # Folge: select('neu-285') fand nie wieder etwas, ALLE 4 Kreuz-Kommandos liefen ueber den
    # privilegierten Rueckfall, waehrend die brauchbare Klasse 'neu-286' (42-73% wiedererkannt) ohne
    # Knopf danebenlag.  Und schaerfer: gebundene Klassen sind vor dem Verhungern geschuetzt
    # (protect=SHAPE_KEY.values() im Blick), die Fehlbindung schaltete also genau die Aufraeum-Mechanik
    # ab, die das Gespenst entfernt haette.
    # WARUM WIEDERHOLUNG und nicht der Flaechenfilter: area_hi (=1411) liegt gemessen UEBER dem
    # verschmolzenen Fleck (1019) und muss es auch, denn die groesste Trainingsform L misst ~940 -- ein
    # Flaechen-Kriterium kann die beiden Faelle prinzipiell nicht trennen.  Ein einmalig verschmolzener
    # Fleck WIEDERHOLT sich dagegen nicht; das trennt ihn vom echten Objekt, ohne irgendeine Annahme
    # ueber Formen einzufuehren.
    # FREIE VERGABE (ACT23_FREIE_VERGABE, Vorgabe 0 bis gemessen).
    # DIAGNOSE (wiki/befunde/vergabe-engstelle-diagnose.md): der Knopf haengt fest an NOVEL_BODY.
    # Ist der vergeben, kehrt _register_open_class zurueck, BEVOR die Klasse Kandidatin wird -- pro
    # Zustand kann also genau EINE selbst geborene Klasse kommandierbar werden.  Gemessen an zwei
    # frischen 300-Episoden-Laeufen: 12 bzw. 4 Geburten, je genau 1 vergebener Knopf, und obj_X
    # wird kein einziges Mal adressiert.  Das Eigenschafts-Kommando umgeht das NICHT -- im
    # autonomen Lauf erweitert kein Pfad state.OBJECTS.
    #
    # DIE AENDERUNG IST KLEIN UND ABSICHTLICH KEIN NEUER MECHANISMUS: die Bestaetigungsschranke
    # (BIND_CONFIRM von BIND_WIN Blicken) bleibt genau wie sie ist.  Entfernt wird nur die
    # Festverdrahtung auf EINEN Koerper -- bestaetigt wird kuenftig gegen den Koerper, auf dem die
    # Klasse tatsaechlich sitzt.  Die Zuordnung Detektion -> naechster Koerper (40 mm) ist dieselbe
    # buchhalterische Kruecke wie in _farbbindung_neu, keine neue Privilegierung.
    FREIE_VERGABE = os.environ.get("ACT23_FREIE_VERGABE", "0") == "1"
    BIND_CONFIRM = int(os.environ.get("ACT23_BIND_CONFIRM", "3"))   # so viele Treffer ...
    BIND_WIN = int(os.environ.get("ACT23_BIND_WIN", "6"))           # ... in den letzten so vielen Blicken
    _bind_hits: dict = {}                                           # Klassenname -> je Blick 0/1
    #   (Vorgabe) bzw. der KOERPERNAME, auf dem die Klasse sass (ACT23_FREIE_VERGABE) -- s. _try_bind

    def _zaehl(hits):
        """Treffer im Fenster.  Die Eintraege sind je nach Vergabemodus 0/1 oder Koerpernamen;
        gezaehlt wird deshalb, wie oft der HAEUFIGSTE nicht-leere Eintrag vorkommt.  Bei 0/1 ist
        das identisch zu sum(hits), also gilt eine Fassung fuer beide Modi.
        DER FEHLER, DER DAZU GEFUEHRT HAT: die Mitbewerber-Zeile rechnete weiter sum(h) und ist im
        ersten Lauf mit freier Vergabe abgestuerzt (TypeError int + NoneType) -- ausgerechnet in
        dem Moment, in dem der zweite Knopf vergeben wurde."""
        from collections import Counter
        _c = Counter(x for x in hits if x)
        return _c.most_common(1)[0][1] if _c else 0


    def _register_open_class(cname):
        """Eine eben SELBST BENANNTE Klasse wird KANDIDAT fuer den Kommando-Knopf.  Gebunden wird sie erst
        von _try_bind, wenn sie wiederholt auf dem neuen Objekt sitzt (s. Block oben)."""
        # GEBURT IMMER MELDEN, auch wenn kein Knopf mehr zu vergeben ist.  Bisher stand der Ausstieg
        # VOR der Ausgabe: sobald der Probe-Koerper gebunden war, wurde jede weitere Geburt STILL
        # vollzogen.  Im Lauf vom 2026-08-21 entstanden so zwei Klassen (neu-287, neu-288) ohne eine
        # einzige Meldung -- ich habe daraus faelschlich "null Geburten" gelesen.
        if not FREIE_VERGABE and (NOVEL_BODY in state.SHAPE_KEY or NOVEL_BODY not in scene):
            print(f"  [open-set] neue Klasse '{cname}' geboren (kein Knopf zu vergeben -- "
                  f"{'der Probe-Koerper ist schon gebunden' if NOVEL_BODY in state.SHAPE_KEY else 'er steht nicht in der Szene'})",
                  flush=True)
            return
        _bind_hits.setdefault(cname, [])
        _wo = "auf dem neuen Objekt" if not FREIE_VERGABE else "auf DEMSELBEN Koerper"
        print(f"  [open-set] neue Klasse '{cname}' geboren -- Kandidat fuer einen Knopf "
              f"(braucht {BIND_CONFIRM} von {BIND_WIN} Blicken {_wo})", flush=True)

    def _try_bind(dets):
        """Je Blick: sitzt eine noch UNGEBUNDENE junge Klasse wieder auf dem neuen Objekt?  Erreicht eine
        Klasse BIND_CONFIRM Treffer im Fenster, bekommt sie den Knopf: das Objekt wandert in die GUI-Liste
        und Lokalisierung/Verfolgung laufen auf dem selbst erfundenen Klassennamen.  Der Koerper-Handle ist
        reine VERKABELUNG (welcher MuJoCo-Koerper der Knopf meint); die wahre Position dient nur dieser
        Zuordnung -- dieselbe Rolle wie in situation_feats --, select/track/Griff laufen danach rein auf
        dem Klassennamen."""
        if not _bind_hits or (not FREIE_VERGABE
                              and (NOVEL_BODY in state.SHAPE_KEY or NOVEL_BODY not in scene)):
            return
        if FREIE_VERGABE:
            # AUF WELCHEM KOERPER sitzt die Klasse?  Statt gegen den einen Probe-Koerper zu
            # pruefen, bekommt jeder Blick den Koerper zugeordnet, auf dem die Detektion liegt --
            # dieselbe 40-mm-Regel wie bisher, nur ohne Festverdrahtung.  `hits` traegt dann
            # Koerpernamen statt 0/1, und bestaetigt ist eine Klasse, wenn DERSELBE Koerper
            # BIND_CONFIRM-mal im Fenster auftaucht.  Ein Koerper, der schon eine Formklasse
            # traegt, kommt nicht in Frage -- sonst ueberschriebe die zweite Klasse die erste.
            _frei = [o for o in scene if o not in state.SHAPE_KEY
                     and o not in state.STUETZEN]      # Moebel bekommt keinen Knopf (s. STUETZEN)
            auf = {}
            for d in dets:
                if d.get("pos") is None or d.get("shape") is None or not _frei:
                    continue
                _p = np.asarray(d["pos"], float)
                _n = min(_frei, key=lambda o: float(np.linalg.norm(sim.obj_pos(o)[:2] - _p)))
                if float(np.linalg.norm(sim.obj_pos(_n)[:2] - _p)) < 0.04:
                    auf.setdefault(d["shape"], _n)
        else:
            pT = sim.obj_pos(NOVEL_BODY)[:2]
            auf = {d["shape"] for d in dets if d["pos"] is not None
                   and float(np.linalg.norm(np.asarray(d["pos"]) - pT)) < 0.04}
        for cname, hits in list(_bind_hits.items()):
            if cname not in shape_clf.open_names:              # verhungert -> Kandidat faellt weg
                del _bind_hits[cname]
                print(f"  [open-set] Kandidat '{cname}' ist verhungert -- kein Knopf", flush=True)
                continue
            hits.append(auf.get(cname) if FREIE_VERGABE else (1 if cname in auf else 0))
            del hits[:-BIND_WIN]
        if not _bind_hits:
            return
        # BESTER Kandidat, nicht der zuerst gepruefte: konkurrieren zwei Klassen um dasselbe Objekt
        # (genau der Gespenst-Fall), soll die haeufiger bestaetigte gewinnen und nicht die aeltere.
        if FREIE_VERGABE:
            # Bester Kandidat = die Klasse mit den meisten Blicken auf EINEM Koerper.
            from collections import Counter
            _best = {c: Counter(x for x in h if x).most_common(1) for c, h in _bind_hits.items()}
            _best = {c: v[0] for c, v in _best.items() if v}
            if not _best:
                return
            cname = max(_best, key=lambda c: _best[c][1])
            _ziel, _n_treffer = _best[cname]
            if _n_treffer < BIND_CONFIRM or _ziel in state.SHAPE_KEY:
                return
            hits = _bind_hits[cname]
        else:
            cname = max(_bind_hits, key=lambda c: sum(_bind_hits[c]))
            hits = _bind_hits[cname]
            _ziel = NOVEL_BODY
            if sum(hits) < BIND_CONFIRM:
                return
        # EINDEUTIGES Etikett, nicht len+1: die Klassen-Konsolidierung VERKUERZT open_names, also kann
        # len+1 auf ein LEBENDES Etikett fallen.  Genau das ist am 2026-08-16 passiert -- das Kreuz bekam
        # "Neue Form 7", das obj_T laengst traegt, und im Log liefen 18 Kommandos unter einem Namen fuer
        # zwei Koerper.  Die Klassen-NAMEN haben dieselbe Lehre laengst gezogen (s. _name_seq im
        # shape_classifier, "consolidation SHRINKS the list"); das Etikett hatte sie noch nicht.
        _vergeben = {l for l, _b, _m in state.OBJECTS}
        _n = len(shape_clf.open_names)
        while f"Neue Form {_n}" in _vergeben:
            _n += 1
        label = f"Neue Form {_n}"
        state.add_object(label, _ziel, cname)
        act16.OBJS = list(dict.fromkeys(list(act16.OBJS) + [_ziel]))        # HINZUFUEGEN, nicht alles
        act16.SCENE_N = len(act16.OBJS)                                     #   zurueckholen (s. randomize_objects)
        _bestaetigt = (sum(1 for x in hits if x == _ziel) if FREIE_VERGABE else sum(hits))
        print(f"  [open-set] NEUE FORM selbst benannt: '{cname}' -> Kommando '{label}' "
              f"auf {_ziel} (bestaetigt in {_bestaetigt} von {len(hits)} Blicken; "
              f"Mitbewerber {{{', '.join(f'{c}:{_zaehl(h)}' for c, h in _bind_hits.items() if c != cname)}}})",
              flush=True)
        if panel is not None:
            panel.add_discovered(len(state.OBJECTS) - 1)
            panel.update(sim.render(CAM),
                         f"Neue Form entdeckt und selbst benannt: '{cname}' — jetzt kommandierbar")
        if FREIE_VERGABE:
            del _bind_hits[cname]        # nur DIESE Klasse ist versorgt -- die uebrigen Kandidaten
            #   bleiben im Rennen, denn es gibt jetzt mehr als einen Knopf zu vergeben
        else:
            _bind_hits.clear()                                 # der Knopf ist vergeben

    def _direkt_adressieren(dets):
        """EINE SICHTUNG, EINE ADRESSE -- fuer einen Koerper, der KEINEN Knopf hat (EIG_DIREKT).

        Das Gegenstueck zu _try_bind, und der Unterschied ist der ganze Punkt: _try_bind braucht
        eine geborene Formklasse und BIND_CONFIRM Blicke, in denen sie sich wiederholt.  Hier
        genuegt, dass die Kamera den Koerper EINMAL sieht -- Chromatizitaet, Formeinbettung und
        Spanne liegen in jeder Detektion vor, auch in der ersten.

        WELCHE KOERPER UEBERHAUPT IN FRAGE KOMMEN: nur solche, die in der Szene stehen und noch
        keinen Eintrag in state.OBJECTS haben.  Heute ist das genau einer -- der Probe-Koerper des
        Neuheits-Erzeugers, denn die Szene wird aus state.OBJECTS plus NOVEL_BODY gebaut
        (s. randomize_objects).  Die Welt liefert also weiterhin die Geometrie; was hier wegfaellt,
        ist der WEG von der Sichtung zum Kommando.

        DER KOERPER-HANDLE IST VERKABELUNG, kein Privileg: er beantwortet nur "zu welchem Eintrag
        gehoert diese Detektion" -- fuer Buchfuehrung und Szenenverwaltung.  Die Adresse selbst
        besteht ausschliesslich aus Gemessenem, und die spaetere Lokalisierung (perceive, Zweig
        'eigenschaft') sieht den Namen nie.  Genauso arbeiten _try_bind, die Farbbindung und
        _namenlose_kandidaten seit jeher.
        """
        if not EIG_DIREKT:
            return
        _hat_adresse = {nm for _l, nm, _m in state.OBJECTS}
        # STUETZEN NICHT ALS OBJEKT ADRESSIEREN.  Der Sockel steht in `scene` (damit er platziert
        # und zurueckgestellt wird), hat aber keinen Eintrag in state.OBJECTS -- fuer diese
        # Schleife sieht er also aus wie ein unentdeckter Koerper und wuerde als KOMMANDIERBARES
        # Objekt registriert.  Dann koennte die Neugier ihn zum Greifen auswaehlen: 70 mm breit,
        # Dichte 3000.  Genau das soll state.STUETZEN verhindern (s. dort).  Seine ZIEL-Adresse
        # entsteht getrennt davon in _ziel_adresse_wuerfeln.
        _offen = [nm for nm in scene if nm not in _hat_adresse and not _geparkt_jetzt(nm)
                  and nm not in state.STUETZEN]
        if not _offen:
            return
        for d in dets:
            if d.get("pos") is None or float(d.get("area", 0.0)) < 200.0:
                continue
            # DIE VERSCHMELZUNGSSPERRE DES AGENTEN SELBST, nicht die Flaechenschranke.
            # GEMESSEN UND ZUERST FALSCH GEBAUT: ich hatte hier nur `area_hi` stehen, und der
            # erste frische Lauf hat sofort bewiesen, warum das nicht reicht -- die allererste
            # Direkt-Adresse entstand auf einem Fleck, den die Formstufe im selben Blick als
            # ('verschmolzen', [-0.082, 0.087], 603) gemeldet hatte.  603 px liegen weit unter
            # area_hi (~1411), und der Kommentar im shape_classifier sagt es seit dem 18.08.
            # ausdruecklich: "Der vorhandene Flaechen-Schutz area_hi kann das prinzipiell nicht:
            # die Verschmelzungen messen 822-1390, die groesste TRAININGSform ~940."  Die Adresse
            # beschrieb danach einen Blob aus zwei Koerpern und loeste in KEINER Episode mehr auf.
            # RICHTIG IST DIE FARBSTREUUNG (_merge_th): aus den eigenen Einzelobjekt-Flecken
            # gemessen, 0.995-Quantil, nichts eingestellt.  Sie faengt gemessen etwa zwei Drittel
            # der Phantom-Geburten und sperrt dabei keinen sauberen Einzelfleck (64 von 64 geprueft).
            # SOLANGE SIE NICHT SCHARF IST (weniger als 12 Referenzwerte), wird GAR NICHT
            # adressiert: ohne eigenen Massstab fuer "zwei Dinge in einem Fleck" ist eine Adresse,
            # die den ganzen Lauf stehen bleibt, ein unkalkulierbares Risiko.  Die Bestaetigung,
            # die hier entfaellt, war genau dieser Filter -- irgendetwas muss ihn ersetzen.
            _mth = shape_clf._merge_th()
            if _mth is None:
                return                    # der Agent hat seinen Verschmelzungs-Massstab noch nicht
            if d.get("cspread") is None or float(d["cspread"]) > _mth:
                continue
            if shape_clf.area_hi is not None and float(d["area"]) > shape_clf.area_hi:
                continue                  # die groebere Schranke bleibt als zweites Tor stehen
            # Der Kasten ist der kalibrierte Arbeitsraum -- was daneben liegt, rendert verzerrt
            # und liest sich aus einem langweiligen Grund als "neu".
            _x, _y = float(d["pos"][0]), float(d["pos"][1])
            if not (-0.115 <= _x <= 0.115 and 0.075 <= _y <= 0.235):
                continue
            _p = np.asarray(d["pos"], float)
            _nah = min(_offen, key=lambda o: float(np.linalg.norm(sim.obj_pos(o)[:2] - _p)))
            if float(np.linalg.norm(sim.obj_pos(_nah)[:2] - _p)) >= 0.04:
                continue
            _mess = (np.asarray(d["chroma"], float) if d.get("chroma") is not None else None,
                     np.asarray(shape_clf.desc_embed(d["desc"]), float)
                     if d.get("desc") is not None else None,
                     float(d["span"]) if d.get("span") is not None else None)
            _f = colours.classify(d["chroma"])[0] if d.get("chroma") is not None else None
            _fo, _g = d.get("shape"), groessen_band(d.get("dicke"), d.get("span"))
            # KEINE FARBE IN EINER DAUERHAFTEN ADRESSE, solange die Welt umfaerbt.
            # GEMESSEN, und es ist die Erklaerung fuer den bis dahin raetselhaftesten Befund:
            # obj_X trug die Adresse (farbe-1, cube, dick) und loeste in 140 Episoden KEIN
            # EINZIGES Mal brauchbar auf -- 0 von 18 ohne, 0 von 22 mit erzwungener Formachse.
            # Dabei meldete jede Aufloesung "1 Treffer", also eindeutig, und zeigte trotzdem 60-140
            # mm daneben.  Der Grund steht in _farbe_wuerfeln: ACT23_FARB_MISCHUNG (Vorgabe 1)
            # faerbt JEDE Episode neu um.  Die Adresse trifft damit nicht den Koerper, sondern
            # "was gerade farbe-1 ist" -- und das ist von Episode zu Episode ein anderer.
            # DER DOCSTRING DORT SAGT ES SEIT JEHER, nur fuer den anderen Pfad: "eine nach dem
            # Umfaerben gewuerfelte Eigenschafts-Adresse muss die NEUE Farbklasse tragen, sonst
            # adressiert das Kommando eine Farbe, die es nicht mehr gibt."  _auto_eig_umschreiben
            # wuerfelt JEDE Episode neu und ist deshalb nie betroffen; eine Direkt-Adresse steht
            # den ganzen Lauf und ist es immer.
            # DAS IST KEIN SONDERFALL, SONDERN DIE REGEL: eine dauerhafte Adresse darf nur Achsen
            # nennen, die EIGENSCHAFTEN DES KOERPERS sind.  In der gemischten Welt ist die Farbe
            # ausdruecklich keine -- sie wurde genau deshalb entkoppelt, damit der Farbpfad die
            # Identitaet nicht mehr mittraegt (s. FARB_MISCHUNG).  Mit ACT23_FARB_MISCHUNG=0 ist
            # sie wieder eine, und dann darf sie auch wieder genannt werden.
            if FARB_MISCHUNG:
                _f = None
            # DIE FORMACHSE OHNE KLASSENNAMEN.  resolve() liefert fuer eine unbekannte Form None --
            # genau deshalb ist dieser Weg diskret verschlossen.  Stetig braucht die Achse keinen
            # Namen, nur einen Messwert; der Platzhalter sagt lediglich, dass sie GENANNT ist.
            if EIG_STETIG and _fo is None and _mess[1] is not None:
                _fo = EIG_GESEHEN
            if EIG_DIREKT_FORM and _fo is None:
                continue              # ohne Formachse gibt es hier nichts zu adressieren
            # DAUERHAFT (s. EIG_DAUERHAFT, Teil 1): mit Form UND Groesse beginnen.  Die Farbe ist
            # oben schon gestrichen, wenn die Welt umfaerbt; sonst bleibt sie gewuerfelt.
            _start = ([False, True, False] if EIG_DIREKT_FORM else None)
            if EIG_DAUERHAFT:
                _start = [bool(_f is not None and not FARB_MISCHUNG), _fo is not None, _g is not None]
            _tri = _adresse_wuerfeln((_f, _fo, _g), _mess, _p, ident=True, start=_start)
            if _tri is None:
                continue                  # weder Farbe noch Form -- eine reine Groessenadresse
                #   waere blind (s. Nutzervorgabe in _auto_eig_umschreiben)
            _k = state.add_eigenschaft(_nah, *_tri)
            state.EIG_MESS[_nah] = _mess
            if EIG_GEGEN:
                # QUELLE 1: was im SELBEN Blick raeumlich getrennt daneben liegt, ist ein anderes Ding.
                _neg = []
                for _o in dets:
                    if (_o is d or _o.get("pos") is None or _o.get("desc") is None
                            or float(_o.get("area", 0.0)) < 200.0):
                        continue
                    if float(np.linalg.norm(np.asarray(_o["pos"], float) - _p)) < 0.04:
                        continue
                    if _o.get("cspread") is not None and float(_o["cspread"]) > _mth:
                        continue                  # verschmolzen: kein sauberes Gegenbeispiel
                    _neg.append((np.asarray(shape_clf.desc_embed(_o["desc"]), float),
                                 float(_o["span"]) if _o.get("span") is not None else None))
                state.EIG_NEG[_nah] = _neg[-EIG_GEGEN_MAX:]
                print(f"  [Eig-Gegen] {_nah}: {len(_neg)} Gegenbeispiele aus dem Blick der Adressierung",
                      flush=True)
            # IN DIE SZENENVERWALTUNG AUFNEHMEN, wie es _try_bind bei der Knopfvergabe tut:
            # HINZUFUEGEN, nicht alles zurueckholen (s. randomize_objects).
            act16.OBJS = list(dict.fromkeys(list(act16.OBJS) + [_nah]))
            act16.SCENE_N = len(act16.OBJS)
            print(f"  [Eig-Direkt] {_nah} aus EINER Sichtung adressiert: "
                  f"'{state.OBJECTS[_k][0]}' -- ohne Formklasse, ohne Bestaetigung, ohne Knopf "
                  f"({d.get('area', 0):.0f}px, Farbstreuung {float(d['cspread']):.3f} < {_mth:.3f}, "
                  f"Form{'klasse ' + str(_fo) if _fo != EIG_GESEHEN else 'vektor'})",
                  flush=True)
            if panel is not None:
                panel.add_discovered(_k)     # der zurueckgegebene Index, nicht len-1: add_eigenschaft
                #   UEBERSCHREIBT einen vorhandenen Eintrag desselben Koerpers, statt anzuhaengen
            _offen.remove(_nah)
            if not _offen:
                return

    # NEUGIER AUF NAMENLOSE: eine eben geborene Klasse hat DREI Belege und alle vom selben Fleck --
    # gemessen beansprucht sie ihr Objekt anderswo nur zu 47%, mit drei Sichtungen von anderswo zu 91%
    # (s. _streuung).  Die Streuung entsteht beim TRAGEN, aber der Agent fasst ein Objekt nur an, wenn es
    # ein Kommando dafuer gibt -- und den Knopf gibt es erst nach der Bestaetigung, gemessen rund zehn
    # Episoden nach der Geburt.  Bis dahin hat die Klasse aus Anspruechen laengst 10-16 Belege, und die
    # Streuung kommt zu spaet, um noch etwas zu bewegen (gemessen: wirkungslos, Commit 7f8fb28).
    # DESHALB: die Neugier darf eine noch NAMENLOSE (ungebundene) junge Klasse ueben.  Dafuer wird sie
    # VORUEBERGEHEND handhabbar gemacht und nach der Episode wieder ausgetragen -- sie bekommt also
    # KEINEN Knopf, die Bestaetigung in _try_bind entscheidet darueber weiterhin allein.  So greift das
    # Kind nach dem neuen Ding, WEIL es neu ist, und lernt es dabei von mehreren Orten kennen.
    # WIE OFT GIBT ES DIESES FENSTER UEBERHAUPT?  Gemessen ueber 8 Seeds (901-908, je 30-50 Episoden):
    #     Geburt einer Kreuz-Klasse            8 von 8 Laeufen (Episode 8-15)
    #     SOFORT gebunden (kein Fenster)       0 von 8
    #     Fenster Geburt->Bindung              im Mittel 4.8 Ep (Spanne 2-14)
    #     Neugier hat es genutzt               7 von 8 Laeufen (1-4 Uebungen)
    #     nie gebunden bis Laufende            2 von 8  (offen, s. unten)
    # Das Fenster ist also der NORMALFALL.  (Meine erste Lesart nach einem missglueckten A/B -- "Seed 908
    # bindet sofort, es gibt keine namenlose Phase" -- war falsch: dort war das Fenster 2 Episoden lang und
    # wurde nur nicht gezogen.)  OFFEN: in 2 von 8 Laeufen faellt die Bestaetigung binnen 30 Episoden NIE;
    # ob das Laufzeit ist oder ob 3-von-6 fuer manche Klassen unerreichbar bleibt, ist ungemessen.
    # REPLIKATION FEHLGESCHLAGEN (2026-08-18) -- die 33% -> 83% aus EINEM Seed-Paar (907, d483bc8)
    # halten NICHT.  Gepaarter Sweep ueber 6 frische Seeds (901-906, je 30 Ep, gleicher Seed in beiden
    # Armen; der Lauf ist bei gleichem Seed deterministisch -- zwei identische Laeufe ergaben null
    # Unterschiede, Wiederholung desselben Seeds bringt also nichts, die REPLIKATE SIND DIE SEEDS):
    #     gebunden            aus 6/6      an 6/6
    #     Wiedererkennung     aus 53.7%    an 55.5%   (besser in 4 von 6 Paaren, Vorzeichentest p=0.69)
    #     Lieferungen         2:2                     (p=1.00)
    # Das Merkmal ist damit NEUTRAL, nicht nuetzlich.  Was gemessen BLEIBT: mit der urspruenglichen
    # Kandidatenregel ("ungebunden" statt "ortsgebunden") war es SCHAEDLICH -- 2 von 8 Laeufen banden nie,
    # weil die Zuege an alte Klassen mit 50-80 Belegen gingen (s. 8604ebf).  Der Fix hat den Schaden
    # beseitigt, einen Nutzen darueber hinaus gibt es gemessen nicht.
    NAMENLOS = os.environ.get("ACT23_NAMENLOS", "1") == "1"    # 0 = alter Stand (nur Kommandierbares)
    _uebung = {"body": None}

    def _uebung_start(cname, body):
        """Die namenlose Klasse voruebergehend handhabbar machen (kein Knopf, kein Eintrag auf Dauer)."""
        _uebung["body"] = body
        state.OBJECTS = state.OBJECTS + [(f"namenlos {cname}", body, "shape")]
        state.SHAPE_KEY[body] = cname
        act16.OBJS = list(dict.fromkeys(list(act16.OBJS) + [body]))   # nur ERGAENZEN, sonst holt es die
        #   geparkten Objekte zurueck (s. randomize_objects).  SCENE_N NICHT anfassen: das ist die
        #   SZENENGROESSE (ACT23_SCENE_N), nicht die Zahl der Knoepfe -- einmal mitgesetzt, zog
        #   run_combined mehr Nachbarn als die Szene hergab und brach ab.
        state.sel = len(state.OBJECTS) - 1

    def _uebung_ende():
        """Nach der Episode wieder austragen -- der Zustand sieht danach aus wie vorher."""
        body = _uebung["body"]
        if body is None:
            return
        _uebung["body"] = None
        state.OBJECTS = [o for o in state.OBJECTS if not o[0].startswith("namenlos ")]
        state.SHAPE_KEY.pop(body, None)
        act16.OBJS = [nm for nm in act16.OBJS if nm != body or body in
                      {n for _l, n, _m in state.OBJECTS}]     # nur den Uebungs-Eintrag zuruecknehmen
        state.sel = min(state.sel, len(state.OBJECTS) - 1)

    def _namenlose_kandidaten():
        """Ungebundene junge Klassen, die JETZT sichtbar sind -> (Klassenname, Koerper-Handle).
        Die Lage kommt aus der WAHRNEHMUNG (perceive_all); der Koerper-Handle ist reine Verkabelung,
        genau wie in _try_bind und situation_feats."""
        if not NAMENLOS:
            return []
        gebunden = set(state.SHAPE_KEY.values())
        # NUR ORTSGEBUNDENE Klassen ueben.  WARUM (gemessen im 8-Seed-Sweep): in beiden Laeufen, die binnen
        # 30 Episoden NIE gebunden haben, gingen die Zuege der Neugier an ALTE namenlose Klassen -- Seed 903
        # uebte neu-13 und neu-250 (50 Belege!), Seed 904 uebte neu-250 sogar bevor die Kreuz-Klasse
        # ueberhaupt geboren war.  Die frische Klasse bekam nichts ab und blieb bei 0-17% Wiedererkennung.
        # Eine Klasse mit breiter Abdeckung gewinnt durch Tragen nichts mehr (der Zugewinn saettigt nach
        # ~3 Sichtungen von anderswo, s. _streuung), sie zieht die Aufmerksamkeit nur ab.
        # KRITERIUM ohne neuen Knopf: die SPANNWEITE der eigenen Belege gegen den selbst gemessenen Radius
        # -- liegen alle Belege enger beieinander als zwei Sichtungen desselben Objekts typischerweise
        # auseinanderliegen, ist die Klasse noch ortsgebunden und Streuung zahlt sich aus.  Am gespeicherten
        # Zustand gemessen trennt das sauber: neu-13 24.2 / neu-250 21.2 / neu-34 25.8 fallen raus,
        # neu-266 (Spannweite 0.00, alle Belege vom selben Fleck) bleibt drin.
        _r = shape_clf._birth_radius()

        def _ortsgebunden(c):
            E = np.asarray(shape_clf.open.get(c) or [])
            if len(E) < 2:
                return True
            return float(np.sqrt(((E[:, None, :] - E[None, :, :]) ** 2).sum(2)).max()) < _r

        offen = [c for c in shape_clf.open_names if c not in gebunden and _ortsgebunden(c)]
        if not offen:
            return []
        saved = sim.d.mocap_pos.copy()
        dets = shape_clf.perceive_all(sim)
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        schon = {nm for _l, nm, _m in state.OBJECTS}           # Koerper, die bereits einen Knopf haben,
        #   NICHT nochmal eintragen -- ein Doppeleintrag brachte run_combined aus dem Tritt
        # STUETZEN NICHT UEBEN.  Die Formerkennung gibt der unbekannten 70-mm-Platte eine eigene junge
        # Klasse, und ohne diese Zeile waehlte die Neugier sie als "namenlose Uebung" -- der Arm
        # versuchte, den SOCKEL zu greifen (gesehen im Rauchtest 2026-09-19: "[InKlaue] sockel").
        # Das ist der DRITTE Weg, auf dem Moebel zum Objekt werden koennte; die beiden anderen
        # (state.OBJECTS, _direkt_adressieren) waren schon dicht.
        koerper = [nm for nm in scene if nm not in schon and nm not in state.STUETZEN]
        out = []
        for d in dets:
            if d["shape"] not in offen or d["pos"] is None:
                continue
            p = np.asarray(d["pos"], float)
            nah = min(koerper, key=lambda o: float(np.linalg.norm(sim.obj_pos(o)[:2] - p)), default=None)
            if nah is not None and float(np.linalg.norm(sim.obj_pos(nah)[:2] - p)) < 0.04:
                out.append((d["shape"], nah))
        return out

    def _eig_mess_fuer(body):
        """Der Messwert einer stetigen Adresse, samt nachgefuehrter Beispiele (s. EIG_NACHFUEHREN).
        Ohne Beispiele genau der gespeicherte Wert -- dann ist alles wie vorher."""
        m = state.EIG_MESS.get(body)
        ex = state.EIG_MESS_EX.get(body) or []
        neg = (state.EIG_NEG.get(body) or []) if EIG_GEGEN else []
        if m is None or (not ex and not neg):
            return m
        if not ex:
            return (m[0], m[1], m[2], list(neg))
        emb = [np.asarray(m[1], float)] if m[1] is not None else []
        spn = [float(m[2])] if m[2] is not None else []
        emb += [np.asarray(e, float) for e, _s in ex if e is not None]
        spn += [float(s) for _e, s in ex if s is not None]
        return (m[0], np.vstack(emb) if emb else None, np.asarray(spn, float) if spn else None,
                list(neg))

    def _eig_nachfuehren(body, method, hand_xy, last):
        """Die Adresse um die Sichtung am Loslass-Punkt erweitern -- nur nach eigenem Tragen und
        eindeutiger Aufloesung (s. EIG_NACHFUEHREN).  Der Ort kommt aus der EIGENEN Hand."""
        _eindeutig = state.EIG_EINDEUTIG.pop(body, False)
        if not (EIG_NACHFUEHREN and method == "eigenschaft" and body in state.EIG_MESS):
            return
        if not _eindeutig or last <= 0.0 or hand_xy is None:
            return
        _h = np.asarray(hand_xy, float)
        if not (-0.115 <= _h[0] <= 0.115 and 0.075 <= _h[1] <= 0.235):
            return
        saved = sim.d.mocap_pos.copy()
        dets = shape_clf.perceive_all(sim)
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        nah = [d for d in dets if d.get("pos") is not None
               and float(np.linalg.norm(np.asarray(d["pos"], float) - _h)) < 0.04]
        if len(nah) != 1:
            return                                         # verschmolzen oder mehrdeutig
        d = nah[0]
        _mth = shape_clf._merge_th()
        if d.get("desc") is None or (_mth is not None and d.get("cspread") is not None
                                     and float(d["cspread"]) > _mth):
            return
        if shape_clf.area_hi is not None and float(d.get("area", 0.0)) > shape_clf.area_hi:
            return
        e = np.asarray(shape_clf.desc_embed(d["desc"]), float)
        s = float(d["span"]) if d.get("span") is not None else None
        _alt = _eig_mess_fuer(body)
        _abst = (float(np.min(np.linalg.norm(np.atleast_2d(_alt[1]) - e, axis=1)))
                 / (EIG_TOL_FORM * eig_bezug(shape_clf)) if _alt and _alt[1] is not None else float("nan"))
        ex = state.EIG_MESS_EX.setdefault(body, [])
        ex.append((e, s))
        if len(ex) > EIG_NACH_MAX:
            del ex[0]
        print(f"    [Eig-Nachfuehren] {body}: Sichtung vom Loslass-Punkt aufgenommen "
              f"(Abstand zur bisherigen Adresse {_abst:.2f} Toleranzen, {len(ex)} Beispiele)",
              flush=True)

    def _streuung(body, p0, last):
        """STREUUNG FUER EINE JUNGE KLASSE -- die Identitaet kommt aus der EIGENEN HANDLUNG.

        DAS PROBLEM (gemessen 2026-08-16, act23_split_probe): die Geburt verlangt drei Sichtungen, die
        sich EINIG sind, also drei vom selben Fleck.  Eine neugeborene Klasse ist damit ortsgebunden und
        beansprucht ihr eigenes Objekt anderswo nur zu 47%; jeder Fehlschlag gebiert die naechste
        ortsgebundene Klasse (das Kreuz erzeugte DREI).  Was fehlt, sind Belege von ANDEREN Orten:
            zusaetzliche Sichtungen von anderswo   0 -> 47.2%   1 -> 70.8%   2 -> 81.9%   3 -> 91.0%
            Fremdansprueche dabei durchgehend       0.0%
        Eine einzige Sichtung von woanders hebt die Wiedererkennung also um 24 Punkte, und anders als bei
        der zurueckgenommenen Klassen-Verschmelzung (s. shape_classifier) gibt es KEINE Kehrseite: es
        kommen echte Sichtungen desselben Objekts dazu, keine fremden.

        WOHER DIE IDENTITAET: der Agent hat das Objekt SELBST von p0 hierher getragen -- die Last auf dem
        Fingersensor (`last`, Phase heben) ist seine eigene Propriozeption, kein Etikett und keine
        Wahrheit ueber die Form.  Was er getragen hat, ist dasselbe Ding wie vorher; so lernt ein Kind
        Objektkonstanz, durch Hinbewegen und Hinsehen.  KEIN Schwellwert auf der Strecke: hat er getragen
        und sitzt am Zielort GENAU EIN sauberer Fleck, wird die Sichtung eingespeist -- lag sie nah an
        einem vorhandenen Beleg, ist sie harmlos, lag sie fern, schliesst sie genau die Luecke.  Der
        Koerper-Handle ist reine VERKABELUNG (welcher Fleck gemeint ist), dieselbe Rolle wie in
        situation_feats und _try_bind."""
        k = state.SHAPE_KEY.get(body)
        if k is None or k not in shape_clf.open or p0 is None or last <= 0.0:
            return                                             # nichts getragen -> keine Handlungs-Identitaet
        p1 = np.asarray(sim.obj_pos(body)[:2], float)
        if not (-0.115 <= p1[0] <= 0.115 and 0.075 <= p1[1] <= 0.235):
            return                                             # ausserhalb des kalibrierten Bereichs
        saved = sim.d.mocap_pos.copy()
        dets = shape_clf.perceive_all(sim)
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        nah = [d for d in dets if d["pos"] is not None
               and float(np.linalg.norm(np.asarray(d["pos"]) - p1)) < 0.04]
        if len(nah) != 1:                                      # verschmolzen/mehrdeutig -- genau so ist
            return                                             #   die Gespenst-Klasse entstanden
        d = nah[0]
        if shape_clf.area_hi is not None and d["area"] > shape_clf.area_hi:
            return
        if len(shape_clf.open[k]) >= _SC.OPEN_CAP:
            return
        z = shape_clf._z(d["desc"])
        neu = min((float(np.linalg.norm(z - q)) for q in shape_clf.open[k]), default=float("inf"))
        shape_clf.open[k].append(z)
        print(f"    [Streuung] '{k}': Sichtung vom Zielort aufgenommen, "
              f"{1000*float(np.linalg.norm(p1 - np.asarray(p0, float))):.0f}mm getragen, "
              f"Abstand zum naechsten Beleg {neu:.1f} ({len(shape_clf.open[k])} Belege)", flush=True)

    # ANEIGNUNGSKURVE (Nutzerziel 2026-08-14): nicht "wie oft liefert er", sondern "wie schnell
    # eignet er sich NEUES an".  Gemessen ab der Geburt einer selbst benannten Klasse:
    #   Alter        Episoden seit der Geburt
    #   wiedererkannt  Anteil der Blicke, in denen die Klasse GECLAIMT wurde (statt erneut "novel"
    #                zu erscheinen oder gar eine zweite Klasse zu gebaeren) -- Stufe "stabil erkannt"
    #   kommandiert  wie oft sie als Befehl gewaehlt wurde, und wie oft das geliefert hat
    # WARUM das noetig ist: in den letzten 431 Episoden gab es NULL Geburten -- die Faehigkeit, um
    # die es geht, wird im Betrieb fast nie ausgeuebt, und im Log stand bisher nur die Geburt
    # selbst, nichts danach.  Ohne diese Kurve waere jede Verbesserung daran unbelegbar.
    ACQ_WIN = int(os.environ.get("ACT23_ACQ_WIN", "12"))        # Blicke im rollenden Fenster
    acq = {}                                                   # Klassenname -> Aneignungszaehler
    acq_ep = {"n": 0}                                          # laufende Episodennummer

    def _acq_update(born, events):
        """Einen Blick verbuchen: Geburten anlegen, claims je Klasse zaehlen.

        ALLE offenen Klassen werden gefuehrt, nicht nur die in diesem Lauf geborenen.  Grund
        (2026-08-14 im ersten Messlauf beobachtet): ein verformter Probe-Koerper wurde von seiner
        ALTEN Klasse weiter geclaimt, es kam zu keiner Geburt -- und weil die Kurve nur Neugeburten
        fuehrte, war im Log NICHTS davon zu sehen.  Eine ausbleibende Geburt IST ein Ergebnis und
        muss sichtbar sein."""
        for c in born:
            acq.setdefault(c, {"born": acq_ep["n"], "claim": 0, "blick": 0, "cmd": 0, "ok": 0})
        for c in getattr(shape_clf, "open_names", []):         # auch die BESTEHENDEN Klassen
            acq.setdefault(c, {"born": None, "claim": 0, "blick": 0, "cmd": 0, "ok": 0})
        seen = {c for kind, c, *_ in events if kind == "claim"}
        for c, a in acq.items():                               # ROLLENDES FENSTER (s. acq_line)
            h = a.setdefault("hist", [])
            h.append(1 if c in seen else 0); del h[:-ACQ_WIN]
        nnov = sum(1 for kind, *_ in events if kind == "novel")
        acq_ep["novel"] = acq_ep.get("novel", 0) + nnov        # unzuordenbare Sichtungen gesamt
        for c, a in acq.items():
            a["blick"] += 1
            if c in seen:
                a["claim"] += 1

    def acq_line(maxage=60):
        """Eine Zeile je JUNGER Klasse plus eine Sammelzeile fuer die alten."""
        out, alt = [], []
        # VERHUNGERTE Klassen nicht weiter fuehren.  `acq` vergisst nie, der Klassifikator raeumt aber
        # auf (_starve_and_cap) -- eine laengst geloeschte Klasse wurde hier weiter mit "0% wiedererkannt"
        # gemeldet und sah aus wie eine tote Klasse, die niemand abraeumt.  Genau das hat der Nutzer am
        # 2026-08-22 an neu-288 bemerkt; die Klasse existierte da schon nicht mehr, die Verhungerung
        # hatte korrekt gegriffen.  Einmal als verhungert vermerken, dann nicht mehr zeigen.
        _lebt = set(getattr(shape_clf, "open_names", []) or [])
        for c, a in list(acq.items()):
            if c not in _lebt and not a.get("tot"):
                a["tot"] = True
                print(f"    [Aneignung] {c}: verhungert nach {acq_ep['n'] - (a['born'] or 0)} Ep "
                      f"(nie stabil wiedererkannt) -- wird nicht mehr gefuehrt", flush=True)
        for c, a in sorted(acq.items(), key=lambda kv: (kv[1]["born"] is not None, kv[1]["born"] or 0)):
            if a["blick"] == 0 or a.get("tot"):
                continue
            # ROLLENDE Rate statt kumulativer.  Im ersten Messlauf fiel auf, dass ein kumulativer
            # Mittelwert die Dynamik VERSTECKT: eine Klasse, die gerade angeeignet wird, klettert
            # nur zaeh, und eine, die ihr Objekt gerade VERLIERT, faellt ebenso zaeh -- man sieht
            # nicht, was JETZT passiert, sondern nur den Durchschnitt seit der Geburt.  Genau die
            # Dynamik ist aber die Aneignung.  Die kumulative Rate bleibt in Klammern daneben.
            h = a.get("hist") or []
            q = 100 * sum(h) / len(h) if h else 0.0
            qk = 100 * a["claim"] / a["blick"]
            if a["born"] is None:                              # vor diesem Lauf geboren
                # KOMMANDO-ZAHL AUCH HIER ZEIGEN.  Sie stand bisher nur in den Zeilen JUNGER
                # Klassen; fuer die bestehenden war nicht sichtbar, ob sie ueberhaupt benutzt
                # werden -- und genau daran haengt, ob "verhungert mangels Benutzung" ueberhaupt
                # eine Erklaerung sein kann.  Ohne diese Zahl ist der Fix am Zaehler (beide
                # Adressierungswege, s. run_one) nicht nachpruefbar.
                alt.append(f"{c} {q:.0f}%" + (f" ({a['cmd']}x kdo)" if a["cmd"] else ""))
                continue
            age = acq_ep["n"] - a["born"]
            if age > maxage:
                continue
            out.append(f"{c}: Alter {age} Ep, wiedererkannt {q:.0f}% (letzte {len(h)} Blicke; "
                       f"gesamt {qk:.0f}%), kommandiert {a['cmd']}x davon {a['ok']} geliefert")
        if alt:
            out.append("bestehende Klassen wiedererkannt: " + "  ".join(alt)
                       + f"  | unzuordenbare Sichtungen gesamt: {acq_ep.get('novel', 0)}")
        return out

    # NEUHEITS-ERZEUGER (ACT23_NOVEL_EVERY).  Ohne ihn gibt es nichts zu messen: in den letzten 431
    # Episoden ist NULL mal eine Klasse geboren worden, weil dieselben sechs Objekte im Umlauf sind
    # und `introduce_object` an einem GUI-Knopf haengt.
    # Erzeugt wird echte FORM-Neuheit ueber die Proportionen des Probe-Koerpers (set_object_size) --
    # der Formdeskriptor ist rotationsinvariant, aber NICHT proportionsinvariant, ein deutlich
    # anderes Seitenverhaeltnis ist fuer die Wahrnehmung also eine neue Form.  Der Koerper wird
    # dabei NICHT umbenannt und bekommt kein Label: der Agent muss ihn selbst entdecken.
    # ACHTUNG, ehrliche Grenze: das ist Neuheit in EINER Dimension (Proportion).  Ob sich daraus
    # ableiten laesst, wie schnell er eine voellig andere Form lernt, ist damit NICHT beantwortet.
    NOVEL_EVERY = int(os.environ.get("ACT23_NOVEL_EVERY", "6"))     # Vorgabe 2026-08-30 (s. unten)
    NOVEL_HOLD = os.environ.get("ACT23_NOVEL_HOLD", "0") == "1"     # EINE Form festhalten (s. unten)
    # WELCHE Proportionen wirklich neu sind -- GEMESSEN, nicht geraten (2026-08-14).  Der erste
    # Satz war unbrauchbar: der Deskriptor ist ROTATIONSINVARIANT konstruiert, also ist 10x32
    # dieselbe Form wie 32x10 und damit wie das lange Objekt (34x9).  Alle fuenf alten Werte waren
    # gedrehte BEKANNTE Formen; resolve() ordnete sie prompt einer bestehenden Klasse zu (10x32 ->
    # neu-34 in 9 von 9 Sichtungen), der Geburts-Pfad wurde nie erreicht.  Das System hatte recht,
    # der Erzeuger war falsch.
    # Massgeblich ist das SEITENVERHAELTNIS.  Bekannt: Wuerfel 1.0:1, langes Objekt 3.8:1,
    # T-Grundgeom 3.0:1.  Ueber je 8 Posen gemessen (Anteil NOVEL):
    #     12x12 (1.0:1)  2/8      10x32 (3.2:1)  1/8      18x12 (1.5:1)  2/8
    #     30x4  (7.5:1)  5/8      22x20 (1.1:1)  8/8
    # Nur die beiden letzten sind zuverlaessig neu -- ein EXTREM schlanker Stab (jenseits des
    # bekannten Bereichs) und ein fast quadratisches, aber deutlich GROESSERES Rechteck (die
    # Groesse traegt, weil die Ringradien der Harmonischen in Weltmassen liegen).
    _novel_shapes = [(0.022, 0.020, 0.012), (0.030, 0.004, 0.012),
                     (0.024, 0.022, 0.012), (0.032, 0.005, 0.012)]

    # DEN PROBE-KOERPER WEITERREICHEN (ACT23_NOVEL_WEITER, Vorgabe 0 bis gemessen).
    # DIAGNOSE (wiki/befunde/freie-vergabe-erste-tuer.md): der Erzeuger hat einen Riegel mit echtem
    # Grund -- ist der Probe-Koerper entdeckt, verwaltet ihn randomize_objects, und ein
    # zusaetzliches Hinstellen fuellte die Szene ueber SCENE_N.  Die Folge ist aber, dass es NIE
    # eine zweite neue Form gibt: nach der ersten Entdeckung kehrt spawn_novel_shape fuer immer in
    # der ersten Zeile zurueck.
    # DIE REPARATUR IST KLEIN, weil der schwierige Teil schon dasteht: die else-Verzweigung unten
    # behandelt einen Probe-Koerper, der NICHT obj_T ist, bereits richtig ("ein frischer Koerper
    # braucht die Verformung nicht: seine Neuheit ist er selbst").  Es fehlt allein, dass die Rolle
    # je weitergegeben wird.
    # UND SIE LOEST ZUGLEICH DAS DRITTE RAD: ein Koerper braucht die Szene fuer den Knopf und den
    # Knopf fuer die Szene (act16.OBJS waechst nur bei der Vergabe).  Der Erzeuger ist der einzige
    # Pfad, der einen Koerper OHNE Knopf in die Szene stellt -- also muss genau er weiterreichen.
    NOVEL_WEITER = os.environ.get("ACT23_NOVEL_WEITER", "0") == "1"

    def _probe_weiterreichen():
        """Ist der aktuelle Probe-Koerper entdeckt, die Rolle an den naechsten unentdeckten geben.

        Kandidat ist ein Koerper, der WEDER eine Formklasse traegt NOCH schon kommandierbar ist --
        sonst wuerde der Erzeuger ein Objekt als "neu" hinstellen, das der Agent laengst anspricht.
        Ist keiner mehr uebrig, bleibt es beim alten Verhalten (der Erzeuger schweigt); die Welt hat
        dann wirklich nichts Neues mehr, und das ist eine ehrliche Auskunft, keine Panne."""
        nonlocal NOVEL_BODY
        if not NOVEL_WEITER or not _probe_entdeckt():
            return
        _vergeben = set(state.SHAPE_KEY) | {nm for _l, nm, _m in state.OBJECTS}
        _naechste = [o for o in _FARB_KOERPER if o not in _vergeben]
        if not _naechste:
            return
        _alt, NOVEL_BODY = NOVEL_BODY, _naechste[0]
        print(f"    [Neuheit] Probe-Rolle weitergereicht: {_alt} ist entdeckt -> {NOVEL_BODY} "
              f"(noch offen: {', '.join(_naechste[1:]) or 'keiner'})", flush=True)

    def spawn_novel_shape():
        """Dem Probe-Koerper eine NEUE Proportion geben und ihn frei hinstellen -- ohne Label.

        NICHTS ZU TUN, wenn er laengst entdeckt und als Kommando registriert ist: dann ist er ein
        normales Objekt, das randomize_objects verwaltet, und ein zusaetzliches Hinstellen wuerde die
        Szene ueber ACT23_SCENE_N hinaus fuellen.  Im Lauf vom 2026-08-21 geschah das 45 Mal, obwohl
        das Kreuz schon "Neue Form 10" war."""
        _probe_weiterreichen()          # erst weitergeben, dann pruefen (s. oben)
        if _probe_entdeckt():
            return
        # ACT23_NOVEL_HOLD=1 haelt EINE Form ueber den ganzen Lauf fest, statt durchzuwechseln.
        # Fuer den Nachweis, DASS eine Geburt zustande kommt, ist das noetig: eine Klasse braucht
        # NOVEL_CONFIRM=3 Belege, und bei wechselnden Formen steht jede nur wenige Blicke lang da.
        # EIGENE FORM statt Verformung, wenn der Probe-Koerper eine hat.  set_object_size trifft bei
        # einem ZUSAMMENGESETZTEN Koerper nur das ERSTE Geom und verformt ihn still zu einer
        # Missgestalt -- genau davor warnt der Kommentar an _set_sizes, und obj_X (Kreuz) besteht aus
        # zwei Bars.  Ein frischer Koerper BRAUCHT die Verformung auch nicht: seine Neuheit ist er
        # selbst.  Verformt wird nur noch der verbrauchte obj_T, fuer den es keine andere Quelle gibt.
        if NOVEL_BODY == "obj_T":
            i = 0 if NOVEL_HOLD else acq_ep["n"] // max(NOVEL_EVERY, 1)
            half = _novel_shapes[i % len(_novel_shapes)]
            _novel_half["h"] = tuple(float(x) for x in half)   # gegen das Ruecksetzen in _set_sizes
            sim.set_object_size(NOVEL_BODY, np.asarray(half, float))
        else:
            half = tuple(float(x) for x in sim.m.geom_size[sim.m.body_geomadr[
                mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, NOVEL_BODY)]])
        # NUR Slots, auf die der Open-Set-Blick ueberhaupt schaut.  open_set_glance filtert mit
        # bounds=(-0.115, 0.115, 0.075, 0.235) -- die beiden oberen Slots liegen bei y=0.240 und damit
        # AUSSERHALB; eine dort hingestellte neue Form wird nie gesehen, ihre Sichtungen werden
        # verworfen (gefunden 2026-08-15, zweiter Fehler im Neuheits-Erzeuger nach dem Ruecksetzen).
        _GB = (-0.115, 0.115, 0.075, 0.235)
        _sichtbar = [i for i, (x, y) in enumerate(SLOTS)
                     if _GB[0] <= x <= _GB[1] and _GB[2] <= y <= _GB[3]]
        free = [si for si in _sichtbar if si not in scene_slots.values()]
        si = int(free[0]) if free else int(crng.choice(_sichtbar))
        p = np.array(SLOTS[si], float) + crng.uniform(-0.003, 0.003, 2)
        yaw = float(crng.uniform(0, 2 * np.pi))
        scene[NOVEL_BODY] = (p, float(half[2]), yaw); scene_slots[NOVEL_BODY] = si
        sim.set_object(NOVEL_BODY, p.tolist(), z=float(half[2]), yaw=yaw)
        mujoco.mj_forward(sim.m, sim.d)
        print(f"    [Neuheit] Probe-Koerper mit neuer Proportion {tuple(round(1000*h) for h in half)}mm "
              f"hingestellt -- ohne Label, der Agent muss ihn selbst entdecken", flush=True)

    def open_set_glance():
        """One open-set LOOK at the current scene: unknown blobs feed the novelty buffer, a young class's
        exemplar set grows over new poses (observe_scene); a class born here becomes a commandable object.
        Runs at scene EVENTS (placement, after a command), not per tracked frame."""
        if _nur_groesse["an"]:                         # Groessen-Sammeln (s. _groesse_sammeln):
            return []                                  #   dort soll NUR der Groessenschaetzer lernen
        if D0_FREEZE or shape_clf.novel_th is None:
            return []
        saved = sim.d.mocap_pos.copy()                         # observe_scene parks the markers -> restore
        _prot = set(state.SHAPE_KEY.values())                  # bound commands never starve
        if EIG_SCHUETZT:                                       # ... und was ueber EIGENSCHAFTEN
            _prot |= {t[1] for t in state.EIGENSCHAFT.values()  #     kommandierbar ist, auch nicht
                      if t[1] is not None and t[1] != EIG_GESEHEN}   # (s. EIG_SCHUETZT oben; der
            #     Platzhalter ist KEINE Klasse und hat hier nichts zu schuetzen)
        born = shape_clf.observe_scene(sim, bounds=(-0.115, 0.115, 0.075, 0.235),   # only inside the
                                       protect=_prot)
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)   # calibrated workspace (5mm inside
        #   REACH_XY; anything beyond lies where a knocked/mis-dropped object renders clipped or
        #   distorted and would read consistently-"novel" for a boring reason)
        if os.environ.get("ACT23_DEBUG", "0") == "1" and shape_clf.last_events:
            _bufn = (sum(len(g["ex"]) for g in (getattr(shape_clf, "_novel_groups", None) or []))
                     if _SC.NOVEL_CLUSTER else len(shape_clf._novel_buf))
            _grpn = len(getattr(shape_clf, "_novel_groups", None) or []) if _SC.NOVEL_CLUSTER else 0
            # buffer= zeigte bisher IMMER den FIFO -- mit aktivem Cluster-Puffer ist das der
            # eingefrorene Stand aus dem Pickle und damit irrefuehrend (im Test konstant "11",
            # waehrend die Gruppen wuchsen).  Jetzt die tatsaechlich benutzte Struktur.
            print(f"    [dbg open-set] {shape_clf.last_events}  Belege={_bufn} in {_grpn} Gruppen",
                  flush=True)
        _acq_update(born, shape_clf.last_events or [])
        for cname in born:
            _register_open_class(cname)
        # STAGE 3: OPEN-SET COLOURS from the same glance -- every in-workspace component's chromaticity
        # feeds the fully self-labelled colour classes; a newborn class is BOUND to the body it was
        # discovered on (nearest body <4cm, plumbing aid exactly like the form registration).
        saved = sim.d.mocap_pos.copy()
        dets = shape_clf.perceive_all(sim)
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        _try_bind(dets)                                        # Knopf-Bindung auf DERSELBEN Wahrnehmung
        #   wie die Farbstufe -- kein zusaetzlicher perceive_all, also kostet die Wiederholungspruefung
        #   nichts ausser dem Zaehler.
        _direkt_adressieren(dets)                              # ... und die Adresse OHNE Klasse auf
        #   derselben Wahrnehmung (s. EIG_DIREKT).  NACH _try_bind: findet die Bestaetigung in
        #   diesem Blick statt, soll der regulaere Weg den Vorrang haben -- die Direkt-Adresse
        #   ueberspringt sie nur, wenn es sonst gar keinen Weg gibt.
        bodies = list(dict.fromkeys([nm for _l, nm, _m in state.OBJECTS]
                                    + ([NOVEL_BODY] if NOVEL_BODY in scene else [])))
        for d in dets:
            if d["pos"] is None:
                continue
            if shape_clf.area_hi is not None and d["area"] > shape_clf.area_hi:
                continue                                       # merged blob = MIXED chromaticity -> would
                #   breed a phantom colour class (one appeared un-bound in the headless run)
            x, y = float(d["pos"][0]), float(d["pos"][1])
            if not (-0.115 <= x <= 0.115 and 0.075 <= y <= 0.235):
                continue                                       # same calibrated-workspace gate as the forms
            for cname in colours.observe(d["chroma"]):
                near = min(bodies, key=lambda o: float(np.linalg.norm(sim.obj_pos(o)[:2] - d["pos"])))
                if (float(np.linalg.norm(sim.obj_pos(near)[:2] - np.asarray(d["pos"]))) < 0.04
                        and near not in colour_of_body):
                    colour_of_body[near] = cname
                    print(f"  [open-set] NEUE FARBE selbst benannt: '{cname}' (auf {near})", flush=True)
                else:
                    print(f"  [open-set] NEUE FARBE selbst benannt: '{cname}'", flush=True)
            # NACHVERSUCH DER FARBBINDUNG (2026-08-31).  BEFUND, der dazu gefuehrt hat: die Schleife
            # oben laeuft ueber `colours.observe(...)`, und die gibt NUR NEU GEBORENE Namen zurueck.
            # Die Bindung wird also GENAU EINMAL versucht, im Moment der Klassengeburt.  Passt es dort
            # nicht (naechster Koerper > 40 mm entfernt oder schon vergeben), gibt es NIE einen zweiten
            # Versuch.  Genau das ist obj_X passiert: seine Farbklasse farbe-50 existiert und passt
            # (mu [0.353,0.521,0.126] gegen Chroma [0.371,0.543,0.086]), blieb aber ungebunden -- und
            # ohne Bindung laeuft der Form-Split nie, weshalb obj_X nur 80,7% statt 97-98% erkannt
            # wurde.  Ein NEUER Koerper liefe in dieselbe Falle, deshalb vor jedem Neuheits-Versuch.
            #
            # Bedingungen bewusst so streng wie bei der Erstbindung, plus eine zusaetzliche:
            #   * der Koerper ist noch ungebunden               (wie oben)
            #   * er liegt naeher als 40 mm an der Sichtung     (wie oben)
            #   * die Klasse ist noch an KEINEN anderen Koerper gebunden -- sonst teilten sich zwei
            #     Koerper eine Farbklasse, und der Form-Split holte beim einen den anderen.
            if BIND_RETRY:
                _cn, _cd = colours.classify(d["chroma"])
                # DREI WACHHUNDE, jeder aus einem beobachteten Fehlschlag:
                #  (1) die Klasse darf an KEINEN anderen Koerper gebunden sein -- sonst teilten sich
                #      zwei Koerper eine Farbe und der Form-Split holte beim einen den anderen.
                #  (2) HOECHSTDISTANZ: der erste Entwurf band obj_X an 'farbe-15' mit Abstand 0,239,
                #      weil er die beste FREIE Klasse nahm statt der PASSENDEN.  Passt keine freie
                #      Klasse gut, wird NICHT gebunden -- eine falsche Bindung ist schlimmer als keine.
                #  (3) BESTAETIGUNG ueber mehrere Blicke, wie NOVEL_CONFIRM bei den Formen.  Der erste
                #      Entwurf band auf EINER Sichtung; ein einziges schlecht belichtetes Bild reichte.
                if (_cn is not None and _cd <= BIND_MAX_D
                        and _cn not in set(colour_of_body.values())):
                    _near = min(bodies, key=lambda o: float(np.linalg.norm(sim.obj_pos(o)[:2] - d["pos"])))
                    if (float(np.linalg.norm(sim.obj_pos(_near)[:2] - np.asarray(d["pos"]))) < 0.04
                            and _near not in colour_of_body):
                        _k = (_near, _cn)
                        _bind_votes[_k] = _bind_votes.get(_k, 0) + 1
                        if _bind_votes[_k] >= BIND_CONFIRM_N:
                            colour_of_body[_near] = _cn
                            print(f"  [open-set] Farbe NACHGEBUNDEN: '{_cn}' (auf {_near}, Abstand "
                                  f"{_cd:.3f}, {_bind_votes[_k]} uebereinstimmende Blicke)", flush=True)
        return born

    def introduce_object():
        """'Objekt hinzufügen': drop the NEVER-TRAINED probe object into a free slot.  The net then has to
        DISCOVER it -- consistent open-set sightings commit a self-labelled class and the new command
        button appears.  No truth label anywhere; if the glances don't confirm, the object simply stays on
        the table and every later scene glance keeps observing it."""
        if NOVEL_BODY in scene:
            if panel is not None:
                panel.update(sim.render(CAM), "Das Objekt ist schon in der Szene")
            return
        free = [si for si in range(len(SLOTS)) if si not in scene_slots.values()]
        si = int(free[0]) if free else 0
        p = np.array(SLOTS[si], float) + crng.uniform(-0.003, 0.003, 2)
        yaw = float(crng.uniform(0, 2 * np.pi))
        _set_sizes()
        sim.set_object(NOVEL_BODY, p, z=0.012, yaw=yaw)
        mujoco.mj_forward(sim.m, sim.d); sim.step(60)
        scene[NOVEL_BODY] = (p, 0.012, yaw); scene_slots[NOVEL_BODY] = si
        if panel is not None:
            panel.update(sim.render(CAM), "Ein unbekanntes Objekt ist aufgetaucht ...")
        for g in range(4 + BIND_WIN):                          # NOVEL_CONFIRM Sichtungen + eine Reserve,
            #   PLUS das Bestaetigungsfenster: die Geburt allein vergibt den Knopf nicht mehr, die Klasse
            #   muss sich erst wiederholt auf dem Objekt zeigen (s. BIND_CONFIRM).  Bricht ab, sobald
            #   gebunden -- bei einer sauber sichtbaren Form sind das typisch 6-7 Blicke.
            open_set_glance()
            if NOVEL_BODY in state.SHAPE_KEY:
                break
            if panel is not None:
                panel.update(sim.render(CAM), f"Netz beobachtet das unbekannte Objekt ({g + 1}) ...")
            sim.step(20)
        if NOVEL_BODY not in state.SHAPE_KEY and panel is not None:
            panel.update(sim.render(CAM), "Noch keine neue Klasse — das Netz beobachtet bei jedem Befehl weiter")

    if _loaded is not None:                                    # restore SELF-DISCOVERED command objects: the
        for lbl, nm, m in _loaded.get("objects", []):          #   open-set classes live in shape_clf; the GUI
            if m == "eigenschaft":                             # SELBSTHEILUNG aelterer Zustaende: die
                continue                                       #   fluechtige Adresse wurde frueher mit-
            state.OBJECTS = state.OBJECTS + [(lbl, nm, m)]     #   plumbing (button, body<->class key) is re-
            if panel is not None:                              #   registered here so "Neue Form" survives
                panel.add_discovered(len(state.OBJECTS) - 1)   #   the restart as a commandable object
        state.SHAPE_KEY.update(_loaded.get("shape_key", {}))
        _dropped = shape_clf.enforce_cap_on_load(protect=set(state.SHAPE_KEY.values()))
        if _dropped:                                            # the cap never ran on this persisted pile
            print(f"  [Aufräumen] {len(_dropped)} verwaiste Phantom-Klassen verworfen "
                  f"-> {shape_clf.open_names}", flush=True)
    if panel is not None:
        panel._randomize_fn = randomize_objects     # wire "Objekte neu" (panel built before randomize_objects existed)
        panel._introduce_fn = introduce_object      # wire "Objekt hinzufügen" (open-set discovery)
        panel._ziel_fn = _ziel_adresse_wuerfeln     # wire "Ziel: an Körper" (s. ZIEL_ADRESSE)
        panel._pix2welt = (lambda px: shape_clf._px_to_world(np.asarray(px, float))[0]
                           if getattr(shape_clf, "Hinv", None) is not None else None)
        if SOCKEL:
            panel._platte_fn = platte_steuern
            panel._platte_zustand = lambda: platte
        panel._auf_tisch = lambda: [nm for nm in dict.fromkeys(list(state.STUETZEN)
                                                               + [n for _l, n, _m in state.OBJECTS])
                                    if not _geparkt_jetzt(nm)]
        panel._refresh()                            # Zielmodus aus der Umgebung sichtbar machen
    # CONTINUITY: make run_combined treat ALL objects as its scene -> with SCENE_N = all, keep=all so it never
    # PARKS a distractor off-table, and reposition_strays never fires (nothing is a stray) -> nothing teleports.
    # The scene just evolves: only the commanded object is grasped + delivered (and STAYS), like real life.
    # REIHENFOLGE (2026-08-21): das steht jetzt VOR randomize_objects(), nicht danach -- randomize_objects
    # engt act16.OBJS auf die STEHENDE Menge ein (s. dort), und diese Zeilen haetten das sofort wieder
    # aufgehoben.  Sie liefern hier nur noch die Vorbelegung fuer den Fall ohne Einschraenkung.
    act16.OBJS = list(dict.fromkeys(nm for _l, nm, _m in state.OBJECTS))   # s. randomize_objects:
    act16.SCENE_N = len(act16.OBJS)                                       #   Adressen != Koerper
    randomize_objects()

    def train_fovea_classes(rounds=None):
        """DETECTOR-FREE GAZE (user's goal): retrain the hex fovea net so its sel-channel dynamics
        handle EVERY self-labelled colour class, not just the 3 fixed command codes the warmup used.
        The measured limit was that step_id's injected class-colour sel is OFF-DISTRIBUTION for the
        net, so fovea_gradient's drive was too weak to carry the gaze without the detector re-anchor.
        Here the net LEARNS (net.step(learn=True)) to reconstruct the class-conditioned sel at
        centred objects (positive) + near-empty sel on background (negative), across all classes and
        random poses -- so the identity drive strengthens and the gaze can follow with a far sparser
        (ideally no) detector anchor.  Runs only when the learned gaze is active."""
        from pc_cvnn.pc_act14 import _rand_xy
        items = [(nm, np.asarray(colours.classes[c]["mu"], float))
                 for nm, c in colour_of_body.items() if c in colours.classes]
        if not items:
            return
        rounds = int(os.environ.get("ACT23_FOVEA_TRAIN_N", "80")) if rounds is None else rounds
        K = vc.fovea.K; lo, hi = HEX_F * K, RES - HEX_F * K
        snap = {nm: (sim.obj_pos(nm)[:2].copy(), float(sim.obj_pos(nm)[2]), float(sim.obj_yaw(nm)))
                for _l, nm, _m in state.OBJECTS}
        saved = sim.d.mocap_pos.copy(); shape_clf._park_markers(sim); vc.fovea.z = 1.0
        for i in range(rounds):
            for body, mu in items:
                # SCALE INVARIANCE across the zoom span (user request 0.5..2.0): the search zooms
                # OUT to re-find the class saliency and IN for detail -- sel must stay readable there.
                vc.fovea.z = (ZOOM_MIN + (ZOOM_MAX - ZOOM_MIN) * crng.random()) if FOVEA_ZOOM else 1.0
                p = _rand_xy(crng)
                sim.set_object(body, p, z=_hoehe.get(body, 0.012), yaw=float(crng.uniform(0, 2 * np.pi)))
                mujoco.mj_forward(sim.m, sim.d)
                img = sim.render(CAM)
                try:
                    px = np.asarray(shape_clf._world_to_px(np.asarray(p, float))[0], float)
                except Exception:
                    continue
                gz = np.clip(px + crng.uniform(-4, 4, 2), lo, hi)
                vc.fovea.step_id(img, gz, mu, learn=True)          # positive: class-sel blob ON the object
                bg = crng.uniform([lo, lo], [hi, hi])
                vc.fovea.step_id(img, bg, mu, learn=True)          # negative: sel ~empty off the object
            if panel is not None and i % 10 == 0:
                panel.update(sim.render(CAM), f"Blick-Netz auf Farbklassen trainieren {i}/{rounds} ...")
        for nm, (xy, z, yaw) in snap.items():
            sim.set_object(nm, xy.tolist(), z=z, yaw=yaw)
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        vc.fovea.z = 1.0
        vc.fovea._zoom_trained = _zoom_span                # persisted marker: a fovea trained on another
        #   zoom span OR another sel primitive retrains once on load (world-consistency pattern)
        print(f"  [Netz-Blick] Fovea auf {len(items)} Farbklassen umtrainiert "
              f"({rounds} Runden, Zoom {ZOOM_MIN if FOVEA_ZOOM else 1.0:.2f}-"
              f"{ZOOM_MAX if FOVEA_ZOOM else 1.0:.2f}) -- Blick-Trieb verstärkt", flush=True)

    _zoom_span = ("chroma",) + ((ZOOM_MIN, ZOOM_MAX) if FOVEA_ZOOM else (None,))
    #   "chroma" tags the sel PRIMITIVE the classes were trained with: step_id switched from the
    #   cosine match (grey table leaked through vs unsaturated class centroids) to _match_chroma,
    #   so a fovea class-trained on the old cosine-sel retrains once.
    if (FOVEA_NET and not D0_FREEZE and os.environ.get("ACT23_FOVEA_TRAIN", "1") == "1"
            and (not _fovea_loaded                 # a loaded fovea was already class-trained -> skip,
                 or getattr(vc.fovea, "_zoom_trained", "nie") != _zoom_span)):   # UNLESS zoom span or
        if _fovea_loaded:                          # sel primitive changed since it was trained
            print(f"  [Netz-Blick] geladene Fovea kennt {_zoom_span} nicht -- "
                  f"trainiere Klassen einmalig nach", flush=True)
        train_fovea_classes()

    # ACT23_MODVIZ=1: eigenes Fenster mit dem MODUL-GRAPHEN und den Zusammenspiel-Kurven
    # (src/pc_cvnn/module_viz.py).  Rein passiv -- ein Redraw je Episode, kein Eingriff in den Lauf.
    modviz = None
    if os.environ.get("ACT23_MODVIZ", "0") == "1":
        try:
            from pc_cvnn.module_viz import ModuleViz
            modviz = ModuleViz()
            print("  [ModulViz] eigenes Fenster geoeffnet (ACT23_MODVIZ=1)", flush=True)
        except Exception as _e:
            print(f"  [ModulViz] nicht verfuegbar: {_e}", flush=True)

    sel_off = {"dxy": None}                                    # the self-selected grasp-point OFFSET (dx,dy)
    #   of the CURRENT command: perceive() and the form tracker's servo obs both add it, so the executed
    #   grasp target is (perceived point + learned offset) consistently through approach corrections
    # (frueher `_sel_seed = {}` -- der Episoden-Keim liegt jetzt als Ports am PerceptionModule,
    #  s. perception.publish_seed/seed_for: Identitaet, Frische und Ruecksetzung kommen vom Port)
    #   with the SAME object the grasp targets (the tracker's own first-frame max-prob pick can differ --
    #   the user watched the U command start focused on the L before snapping over)

    def _off(xy):
        """Add the model's self-selected grasp-point offset to a perceived grasp target (stage 1)."""
        return np.asarray(xy, float) + (sel_off["dxy"] if sel_off["dxy"] is not None else 0.0)

    U_DENSEGRASP = os.environ.get("ACT23_U_DENSEGRASP", "0") == "1"   # DEFAULT AUS seit 2026-08-01 (war ON,
    #   U-only A/B 2026-07-24: +11pp, 16->25/80).  Es war eine FORM-SONDERREGEL (`if body == "obj_U"`) --
    #   genau das gezuechtete Verhalten, das der Nutzer nicht will, und es half auch nicht genug (413-Ep-Lauf:
    #   U 22% geliefert, 42% Griffverlust laut Drucksensor).  Der dichteste Punkt ist per Konstruktion
    #   KANDIDAT 0 der Maskenabtastung (shape_classifier:614, argsort(-dv)) und damit fuer JEDE Form
    #   waehlbar -- die U verliert ihn also nicht, sie muss ihn nur verdienen.  ACT23_U_DENSEGRASP=1
    #   stellt die Sonderregel wieder her (A/B).
    FORM_SPLIT = os.environ.get("ACT23_FORM_SPLIT", "1") != "0"      # the same MERGED-BLOB recovery for the
    #   FORM path (L/U/open classes): a fused component's form descriptor is destroyed, so re-read the form
    #   on the colour-separated part (perceive_colour(with_form=True)).  Measured on obj_T over 80 poses:
    #   own class 56%->95% alone, 8.8%->81% with a close neighbour, residual errors are ABSTENTIONS (never
    #   mislabels).  Also cuts how often the shape branch drops to its PRIVILEGED true-position fallback.
    #   ACT23_FORM_SPLIT=0 restores the old behaviour.
    COLOUR_SPLIT = os.environ.get("ACT23_COLOUR_SPLIT", "1") != "0"   # MERGED-BLOB recovery for the colour
    #   path (shape_classifier.perceive_colour): when a cube fuses with a neighbour and no component's mean
    #   chroma matches its class, split the occupancy per PIXEL instead of dropping to the vc hex code that
    #   grasps the neighbour.  ACT23_COLOUR_SPLIT=0 restores the old fallback.  Measured: 25mm -> 6mm.

    def _gp(det, body):
        """Greifpunkt-BEZUG einer Detektion: immer grasp_xy (Material naechst dem Schwerpunkt).

        Das ist zugleich der Bezugspunkt, auf den run_one die Kandidaten-Offsets bezieht (:2087) und
        auf den _off() sie addiert -- fruehere U-Sonderregel gab hier grasp_dense zurueck, waehrend die
        Offsets weiter gegen grasp_xy gerechnet wurden: die Verschiebung waere DOPPELT gezaehlt worden,
        sobald die Kandidaten im Netz-Modus anspringen.  Ein Bezugspunkt fuer alle Formen schliesst das
        aus.  ACT23_U_DENSEGRASP=1 holt die alte Sonderregel fuer ein A/B zurueck."""
        if U_DENSEGRASP and body == "obj_U" and det.get("grasp_dense") is not None:
            return det["grasp_dense"]
        return det["grasp_xy"]

    def _stapel_paar(dets=None):
        """Das Paar (Auflage, was darauf liegt) aus der Wahrnehmung, oder None.

        Ein gestapelter Koerper liegt nicht NEBEN der Auflage, sondern INNERHALB ihrer
        Umrisslinie -- genau deshalb verwirft ihn die raeumliche Wache des Chroma-Schnitts
        (wiki/befunde/stapel-wird-sichtbar.md).  Das Kriterium ist ihr Gegenstueck und wie sie
        massstabsrelativ: Schwerpunktabstand gemessen an der Halbspanne des groesseren Teils,
        plus ein Groessenunterschied (was getragen wird, ist kleiner als das, was traegt).
        Mehrdeutig ist nicht gefunden -- dieselbe Regel wie bei der Zieladresse.
        """
        if dets is None:
            _sm = sim.d.mocap_pos.copy()
            try:
                dets = shape_clf.perceive_all(sim)
            finally:
                sim.d.mocap_pos[:] = _sm
                mujoco.mj_forward(sim.m, sim.d)
        _ds = [d for d in dets if d.get("pos") is not None and d.get("area") is not None]
        _paare = []
        for _i in range(len(_ds)):
            for _j in range(_i + 1, len(_ds)):
                _a, _b = _ds[_i], _ds[_j]
                _gr, _kl = (_a, _b) if _a["area"] >= _b["area"] else (_b, _a)
                if _kl["area"] <= 0 or _gr["area"] / _kl["area"] < ADR_REL_KLEINER:
                    continue
                _sp = _gr.get("span")
                if _sp is None:
                    continue
                _d = float(np.linalg.norm(np.asarray(_a["pos"], float)
                                          - np.asarray(_b["pos"], float)))
                if _d < ADR_REL_ANTEIL * float(_sp):
                    _paare.append((_d, _gr, _kl))
        # DIE AUFLAGE IST MOEBEL -- also das GROESSTE Ding im Bild.  Ohne diese Schranke nimmt das
        # Kriterium zwei BRUCHSTUECKE desselben Objekts fuer einen Stapel: gemessen eine "Auflage"
        # von 263 px mit 90 px darauf, wo die 70-mm-Platte 1400 px hat.  Groessenverhaeltnis und
        # Konzentrizitaet allein erfuellt ein zerfallener Einzelkoerper genauso.  Danach griff die
        # Klaue irgendwo zu (3,32 N) und verlor sofort wieder.
        # Sie ist zugleich der Massstab, der die Mehrdeutigkeit aufloest: nicht "irgendeines von
        # zweien" (das waere der 152-mm-Fehlgriff der Objektadresse), sondern "das grosse, und nur
        # wenn es EINDEUTIG das groesste ist".
        if _ds:
            _max = max(float(d["area"]) for d in _ds)
            _paare = [q for q in _paare if float(q[1]["area"]) >= 0.9 * _max]
        if len(_paare) != 1:
            return None, ("kein Teil liegt innerhalb eines groesseren" if not _paare
                          else f"mehrdeutig: {len(_paare)} Stapel im Bild")
        return _paare[0][1:], None

    def _auf_etwas_finden():
        """"das, was auf etwas liegt" -- aus der Wahrnehmung, ohne Namen und ohne Privileg.

        Das Paar findet `_stapel_paar` (dort steht die Regel).  Hier kommt die HOEHE dazu:
        die Oberkante der Auflage, geschaetzt auf der Detektion der Auflage selbst.

        Zurueck kommt (Stelle des oberen Koerpers, Greifhoehe der Hand) oder None.
        """
        _paar, _grund = _stapel_paar()
        if _paar is None:
            print(f"    [Adresse auf] {_grund}", flush=True)
            return None
        _unten, _oben_d = _paar
        # DIE GREIFHOEHE aus derselben Quelle wie die Ablagehoehe in Stufe 2: die Oberkante der
        # AUFLAGE.  Der gegriffene Koerper steht mit seiner Unterseite darauf, seine Mitte also
        # eine Objekt-Halbhoehe darueber -- und genau das ist GRASP_Z, die Greifhoehe fuer einen
        # Koerper auf dem Tisch.  Also: Greifhoehe = GRASP_Z + Oberkante.
        _ob = hoehen_schaetzer.schaetzen(_unten)
        if _ob is None:
            print(f"    [Adresse auf] Auflage gefunden ({_unten['area']:.0f}px), aber der "
                  f"Hoehenschaetzer hat erst {len(hoehen_schaetzer.X)} Zeilen -- "
                  f"RUECKFALL auf Tischhoehe", flush=True)
            _ob = 0.0
        _gz = float(act16.GRASP_Z) + float(_ob)
        _p = np.asarray(_oben_d["pos"], float)
        print(f"    [Adresse auf] oberer Koerper bei [{_p[0]:+.3f},{_p[1]:+.3f}] "
              f"({_oben_d['area']:.0f}px auf {_unten['area']:.0f}px), Oberkante der Auflage "
              f"{1000 * _ob:.1f}mm -> Greifhoehe {1000 * _gz:.1f}mm", flush=True)
        return _oben_d, _gz

    _vorblick = {"fehlt": None, "r": None}
    _regeln_basis = (bool(act16.CLOSE_GUARD), bool(act16.REFLEX))   # wie beim Start eingestellt
    print(f"  [Regeln] Riegel/Reflex: Teacher-Betrieb {'an' if all(_regeln_basis) else _regeln_basis}, "
          f"Netzbetrieb {'an (ACT23_REGELN_NETZ=1)' if REGELN_NETZ else 'AUS -- die Policy entscheidet allein'}",
          flush=True)

    def _rueckfall(body, method, grund):
        """Jeder privilegierte Rueckfall wird gemerkt und IMMER protokolliert (s. RUECKFALL)."""
        _vorblick["fehlt"] = (body, method, grund)
        print(f"    [Rueckfall] {body} ({method}): {grund} -> "
              + ("WAHRE Lage (privilegiert)" if RUECKFALL == "privileg" else "NICHT GEFUNDEN"),
              flush=True)

    def perceive(cmd):
        _l, body, method = state.selected()
        if ADR_RELATION:
            # STUFE 4: die Adresse ist eine RELATION, kein Eigenschafts-Tripel (s. ADR_RELATION).
            # Der Koerpername wird hier nur fuer die MESSUNG benutzt, nicht fuer das Finden.
            _r = _auf_etwas_finden()
            if _r is not None:
                _det4, _gz = _r
                # DREI DINGE, DIE JEDER ANDERE ADRESSPFAD TUT und die diesem Zweig gefehlt
                # haben -- es war der GLAUBENSFEHLER aus wiki/befunde/stufe4-abstapeln-gemessen.md
                # (Glaube 28-45 mm daneben statt der sonst 5-18):
                #
                # (a) DEN KEIM VEROEFFENTLICHEN.  Ohne ihn startet der Fovea-Tracker blind auf dem
                #     wahrscheinlichsten gleichklassigen Blob -- "bei mehreren Kandidaten ein
                #     Muenzwurf", und mit dem Konzentrisch-Schnitt liegen jetzt MEHR Bloebe im
                #     Bild als vorher.  Genau die Lage, in der ein fehlender Keim teuer ist.
                # (b) DEN GREIFPUNKT nehmen, nicht den Schwerpunkt: `grasp_xy` ist das Material
                #     naechst dem Schwerpunkt, und es ist der Bezugspunkt, auf den run_one seine
                #     Kandidaten-Offsets rechnet.  Der rohe Schwerpunkt war ein zweiter Fehler.
                # (c) `_off` addieren, den selbst gewaehlten Klauenversatz -- sonst zielt der Arm
                #     systematisch neben das, was er gelernt hat.
                _grp = _gp(_det4, body)
                perception.publish_seed(f"auf:{body}", np.asarray(_det4["pos"], float),
                                       np.asarray(_det4["px"], float),
                                       np.asarray(_off(_grp), float))
                perception.seed_priv = False       # ehrlich wahrgenommen, kein Privileg
                _pz = _off(_grp)
                _wahr = float(np.linalg.norm(np.asarray(_det4["pos"], float)
                                             - sim.obj_pos(body)[:2]))
                print(f"    [Adresse auf] wahr {1000 * _wahr:.0f} mm daneben, Greifziel "
                      f"[{_pz[0]:+.3f},{_pz[1]:+.3f}]", flush=True)
                return np.array([_pz[0], _pz[1], _gz], float), None, "grasp"
            print("    [Adresse auf] nicht aufgeloest -- Rueckfall auf den gewoehnlichen Weg",
                  flush=True)
        if method == "eigenschaft":
            # LOKALISIERUNG UEBER EIGENSCHAFTEN: kein Klassenname, kein Objektname -- nur was die
            # Kamera je Detektion liefert (Farbklasse, Formklasse, Groessenband).  Damit ist ein
            # Objekt adressierbar, OHNE dass eine eigene Formklasse geboren wurde.
            _f, _fo, _g = state.EIGENSCHAFT.get(body, (None, None, None))
            # MOCAP-MARKER SICHERN UND WIEDERHERSTELLEN: perceive_all ruft _park_markers und raeumt
            # die magenta Zielscheiben aus dem Bild.  Ohne Wiederherstellung liefert goal_fn ein
            # GEPARKTES Ziel -- gemessen als Endabstand von 941-952 mm bei fehlerfreier
            # Lokalisierung (0 mm).  Der shape-Zweig macht es seit jeher genauso; ich hatte es
            # beim Bau des Eigenschafts-Zweigs uebersehen.
            _saved = sim.d.mocap_pos.copy()
            _pos, _det, _tr = finde_nach_eigenschaften(
                sim, shape_clf, colours, _f, _fo, _g,
                mess=(_eig_mess_fuer(body) if EIG_STETIG else None))
            state.EIG_EINDEUTIG[body] = bool(_pos is not None and len(_tr) == 1)
            if EIG_GEGEN and EIG_STETIG and _pos is not None and len(_tr) > 1:
                # QUELLE 2: liegt der beste Treffer KLAR vorn, sind die Mitbewerber andere Dinge.
                _mm = _eig_mess_fuer(body)
                _ab = sorted(((_eig_abstand(_o, (_f, _fo, _g), _mm[1], _mm[2], shape_clf) or 0.0), _i)
                             for _i, _o in enumerate(_tr))
                if _ab[0][0] <= EIG_GEGEN_MARGE * _ab[1][0]:
                    _ng = state.EIG_NEG.setdefault(body, [])
                    for _a, _i in _ab[1:]:
                        _o = _tr[_i]
                        if _o.get("desc") is not None:
                            _ng.append((np.asarray(shape_clf.desc_embed(_o["desc"]), float),
                                        float(_o["span"]) if _o.get("span") is not None else None))
                    del _ng[:-EIG_GEGEN_MAX]
                    print(f"    [Eig-Gegen] {body}: {len(_ab) - 1} Mitbewerber als Gegenbeispiel gemerkt "
                          f"(Abstand {_ab[0][0]:.2f} gegen {_ab[1][0]:.2f}, {len(_ng)} gesamt)", flush=True)
            sim.d.mocap_pos[:] = _saved
            mujoco.mj_forward(sim.m, sim.d)
            if _pos is not None and EIG_SPLIT:
                # VERSCHMOLZENER BLOB: die Adresse ist gelungen und trifft trotzdem den
                # Schwerpunkt ZWEIER Koerper.  Auf dem farbreinen Teil nachsehen (s. EIG_SPLIT).
                _saved = sim.d.mocap_pos.copy()
                _teil = eig_split_teil(sim, shape_clf, colours,
                                       colour_of_body.get(body), _fo, _g, _det)
                sim.d.mocap_pos[:] = _saved
                mujoco.mj_forward(sim.m, sim.d)
                if _teil is not None:
                    if os.environ.get("ACT23_DEBUG", "0") == "1":
                        print(f"    [Eig-Split] {body}: Blob verschmolzen "
                              f"(Band '{groessen_band(_det.get('dicke'), _det.get('span'))}', "
                              f"{_det.get('area', 0):.0f}px) -> farbreiner Teil "
                              f"{_teil.get('area', 0):.0f}px, "
                              f"{1000 * float(np.linalg.norm(np.asarray(_teil['pos'], float) - _pos)):.0f} mm "
                              f"verschoben", flush=True)
                    _det = _teil
                    _pos = np.asarray(_teil["pos"], float)
            if _pos is not None:
                if os.environ.get("ACT23_DEBUG", "0") == "1":
                    print(f"    [dbg] {body} via EIGENSCHAFTEN ({_f}, {_fo}, {_g}): "
                          f"{np.round(_pos, 3).tolist()} (wahr "
                          f"{np.round(sim.obj_pos(body)[:2], 3).tolist()}), "
                          f"{len(_tr)} Treffer", flush=True)
                perception.publish_seed(f"eig:{body}", np.asarray(_pos, float),
                                        np.asarray(_det["px"], float),
                                        np.asarray(_gp(_det, body), float))
                perception.seed_priv = False       # ehrlich wahrgenommen (s. AUDIT im Rueckfall)
                return _off(_gp(_det, body)), None, "grasp"
            if EIG_ABSTUFUNG and _g is not None:
                # ABSTUFUNG STATT PRIVILEG: die Groessenachse fallen lassen und erneut suchen.
                # Das bleibt eine Wahrnehmung -- die Adresse wird unschaerfer, nicht unbrauchbar.
                _saved = sim.d.mocap_pos.copy()
                _pos, _det, _tr = finde_nach_eigenschaften(sim, shape_clf, colours, _f, _fo, None)
                sim.d.mocap_pos[:] = _saved
                mujoco.mj_forward(sim.m, sim.d)
                if _pos is not None and (EIG_ABSTUFUNG == 1 or len(_tr) == 1):
                    if os.environ.get("ACT23_DEBUG", "0") == "1":
                        print(f"    [dbg] {body}: Band '{_g}' passt nicht -> ABSTUFUNG auf "
                              f"({_f}, {_fo}, beliebig): {np.round(_pos, 3).tolist()} (wahr "
                              f"{np.round(sim.obj_pos(body)[:2], 3).tolist()}), "
                              f"{len(_tr)} Treffer", flush=True)
                    perception.publish_seed(f"eig:{body}", np.asarray(_pos, float),
                                            np.asarray(_det["px"], float),
                                            np.asarray(_gp(_det, body), float))
                    perception.seed_priv = False   # ehrlich wahrgenommen, nur unschaerfer adressiert
                    return _off(_gp(_det, body)), None, "grasp"
                _pos = None                        # Abstufung hat nicht getragen -> wie bisher
            _rueckfall(body, method, f"Eigenschaften ({_f}, {_fo}, {_g}) treffen nichts")
            _pw = sim.obj_pos(body)[:2]
            if KEIM_RUECKFALL:
                # Ohne Keim startet der Tracker blind auf dem wahrscheinlichsten gleichklassigen
                # Blob -- bei mehreren Kandidaten ein Muenzwurf.  Der Keim kommt hier aus der
                # WAHREN Lage; px bleibt None, weil es dafuer keine ehrliche Bildkoordinate gibt
                # (der Anzeige-Blobfolger setzt sich seinen px-Anker selbst am ersten Treffer).
                perception.publish_seed(f"eig:{body}", np.asarray(_pw, float), None,
                                        np.asarray(_off(_pw), float))
                perception.seed_priv = True        # AUDIT: dieser Keim ist privilegiert
            return _off(_pw), None, "grasp"
        if method == "shape":                                  # L/U: FORM perception (shape classifier)
            saved = sim.d.mocap_pos.copy()                     # select() PARKS the mocap markers -> restore the
            det = shape_clf.select(sim, state.SHAPE_KEY[body])  #   target markers, else goal_fn returns a parked goal
            if det is None and FORM_SPLIT:
                # FUSED BLOB on the FORM path: a neighbour closer than ~40mm merges into one component and
                # DESTROYS the form descriptor -- measured on obj_T (ACT23_TDIAG): recognised as its own
                # class 56% alone but only 8.8% when fused, the rest read as novel or as a foreign class.
                # Recover the same way the colour path does, then classify the FORM on the separated part
                # (measured: 56->95% alone, 8.8->81% fused, and the residual errors are abstentions, never
                # mislabels).  Without this the branch below falls back to the PRIVILEGED true position.
                _ck = colour_of_body.get(body)
                _m = [d for d in shape_clf.perceive_colour(sim, colours, _ck, with_form=True)
                      if d["shape"] == state.SHAPE_KEY[body]] if _ck else []
                if _m:
                    det = max(_m, key=lambda d: float(d["prob"]))
                    print(f"    [Form-Split] {body}: Blob verschmolzen -> Form auf dem farb-getrennten "
                          f"Teil erkannt als '{det['shape']}' ({det['area']:.0f}px)", flush=True)
            sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
            if det is not None:
                perception.publish_seed(state.SHAPE_KEY[body], np.asarray(det["pos"], float),
                                        np.asarray(det["px"], float),
                                        np.asarray(_gp(det, body), float))  # raw seed grasp point: the
                #   fovea servo shifts THIS by the gaze's world motion (grasp geometry preserved)
                if os.environ.get("ACT23_DEBUG", "0") == "1":
                    print(f"    [dbg] {body} via Formklasse: Greifziel "
                          f"{np.round(_off(_gp(det, body)), 3).tolist()} "
                          f"(wahr {np.round(sim.obj_pos(body)[:2], 3).tolist()})", flush=True)
                return _off(_gp(det, body)), None, "grasp"
            _rueckfall(body, method, f"Formklasse '{state.SHAPE_KEY.get(body)}' nicht gefunden")
            return _off(sim.obj_pos(body)[:2]), None, "grasp"  # perception missed -> privileged fallback
        if method in ("long", "color"):                        # STAGE 3 de-crutching, now for the CUBES too:
            # localise by the SELF-LABELLED colour class (bound at discovery) instead of the trained vc
            # hex codes.  For the long object this replaced the last PRIVILEGED lookup; for the cubes it
            # replaces the vc colour codes AND the red-only marker parking (red aliased with the magenta
            # target disks -- perceive_all parks the markers itself, so the aliasing source is gone).
            cname = colour_of_body.get(body)
            knob = "ACT23_LONG_PRIV" if method == "long" else "ACT23_CUBE_VC"
            if cname is not None and os.environ.get(knob, "0") != "1":
                saved = sim.d.mocap_pos.copy()
                dets = shape_clf.perceive_all(sim)
                cands = [d for d in dets if d["pos"] is not None
                         and colours.classify(d["chroma"])[0] == cname]
                if not cands and COLOUR_SPLIT:
                    # MERGED BLOB: this object fused with a neighbour, so no component's MEAN chroma
                    # matches its class any more (measured: red next to the L reads as the L's class).
                    # Recover it by splitting the occupancy per PIXEL instead of dropping through to the
                    # old vc hex code, which grasps the neighbour (see perceive_colour docstring).
                    cands = shape_clf.perceive_colour(sim, colours, cname)
                    if cands:                                  # ALWAYS logged (not DEBUG-gated): this is the
                        #   only visible marker that the recovery fired, and a GUI run must stay auditable
                        print(f"    [Farb-Split] {body}: Blob verschmolzen -> Pixel-Split rettet das Ziel "
                              f"({len(cands)} Teil(e), {cands[0]['area']:.0f}px)", flush=True)
                sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
                if cands:
                    best = min(cands, key=lambda d: colours.classify(d["chroma"])[1])
                    perception.publish_seed(None, np.asarray(best["pos"], float),
                                            np.asarray(best["px"], float),
                                            np.asarray(best["grasp_xy"], float))
                    if os.environ.get("ACT23_DEBUG", "0") == "1":
                        print(f"    [dbg] {body} via Farbklasse '{cname}' lokalisiert", flush=True)
                    return _off(best["grasp_xy"]), None, "grasp"
            if method == "long":
                _rueckfall(body, method, f"Farbklasse {cname!r} " + ("ungeboren" if cname is None
                                                                     else "nicht im Bild"))
                p0 = np.asarray(sim.obj_pos(body)[:2], float)  # fallback: class unborn / not in sight
                try:
                    perception.publish_seed(None, p0,
                                            np.asarray(shape_clf._world_to_px(p0)[0], float), p0)
                except Exception:
                    pass
                return _off(p0), None, "grasp"
        if body == "obj_red":                                  # CUBE FALLBACK (class unborn / not in sight /
            saved = sim.d.mocap_pos.copy(); shape_clf._park_markers(sim)   # ACT23_CUBE_VC=1): the old trained-vc
            try:                                               #   path.  PARK the magenta markers for RED only:
                xy = vc.perceive(body)                         #   red is a SUBSET of magenta (1,0,1) and the sel
            finally:                                           #   head has no 'marker' code to out-claim it
                sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)   # contrastively -> the RED command
            return _off(xy), None, None                        #   LOCKED the target disk (user-observed).
        return _off(vc.perceive(body)), None, None             # cubes: the net localises by colour

    def plot_surprise():
        if panel is not None:
            s = vc.surprise()
            q3 = sim.arm3_angles()                             # body-model FK surprise: predicted vs real hand
            bmm = float(np.linalg.norm(bm.body.fk(q3) - sim.grasp_pos())) * 1000.0   # (was always 0: wrong attr)
            if s is not None:
                m = objmem._last                               # ObjectMemory chart curves (nan while inactive,
                panel.surp_viz.push(s["sensor"], s["state"], s["total"], s["relax"], bmm,   # i.e. FOVEA_MEM off
                                    mem_err=getattr(objmem, "err_px", None),                # or no belief yet)
                                    mem_conf=None if m is None else m["conf"])

    def track_and_plot():
        obs = vc.track()
        plot_surprise()
        return obs

    def make_shape_track(body, key=None, ckey=None, seed_key=_WIE_KEY):
        """FORM-aware live tracker (the user's fovea goal): per tracked frame, segment+classify the scene
        (perceive_all) and return the commanded SHAPE's grasp point + confidence in run_combined's
        (obs, conf) servo protocol -- approach corrections work for L/U exactly like the colour servo.
        TWO separate uses of the detections (the v1 lesson):
          * SERVO obs: commanded-CLASS match + a 5cm world jump gate.  Only valid while the object rests
            ON the table (the px->world homography is a TABLE-plane map) -- run_combined only servos in
            over/lower anyway.
          * DISPLAY follow: nearest component in IMAGE px, ANY class -- a lifted/carried shape leaves the
            table plane (world pos wrong) and often mis-classifies, but its image blob stays trackable ->
            the fovea window follows the shape through grasp AND transport, like the colour fovea does.
        SEEDING: for shapes the belief starts LAZILY from the select() detection the grasp actually
        targets (perception.seed_for; the first-frame max-prob pick can be a DIFFERENT same-class blob -- the user
        watched the U command start focused on the L).  key=None = the LONG object: no class to key on ->
        DISPLAY-ONLY blob follower seeded from the object's start position, obs stays None (the colour
        fovea drive locked the CYAN U here: the obj_blue code fires on cyan, user-observed).
        ckey = a SELF-LABELLED COLOUR class name (stage 3 cube de-crutching): servo cands are matched by
        colours.classify on the detection chromaticity instead of the shape class; conf maps the chroma
        distance into [0,1] against the class threshold (within-spread ~0.075 -> conf ~0.7).
        The hex net can't be command-keyed to a FORM, so the form tracker DRIVES the hex view itself:
        one perception step at the followed px (fovea.step: lifelong hex learning + surprise stay alive)
        and the viz drawn at the SAME gaze -- box and cells consistent, no colour-keyed follow step to
        fight the pin, no zoom-out spiral (v1 called vc.track() from the pin: the colour drive walked the
        box away from the sampled crop and zoomed out every frame -- the user's frozen/mismatched views)."""
        mem = {"xy": None, "px": None}                         # world belief (servo) + image belief (display)
        #   (the long object used to be seeded PRIVILEGED here; stage 3: perceive() now always publishes
        #   the seed for it too -- colour-class localization, or its explicit fallback -- so the lazy
        #   seed below covers key=None as well)
        objmem.reset()                                         # fresh predictive belief per episode
        vc.fovea.z = 1.0                                       # defined DETAIL zoom for the form view
        vc._fsv = {"d": [], "nf": 0, "nd": 0}                  # fovea-servo stats (per episode): frames
        #   with a net obs / a detector obs, and |net - detector| mm where both exist (shadow metric)

        def _track():
            vc._d0b_frame = None                              # trace only a frame sampled on THIS call
            _kkey = key if (seed_key is _WIE_KEY or not KEIM_FIX) else seed_key
            if mem["px"] is None and (_sd := perception.seed_for(_kkey)) is not None:
                mem["xy"], mem["px"] = _sd[0], _sd[1]                              # lazy: perceive() runs
                mem["_keim"] = True                            # nur fuer die Keim-Diagnose
                #   INSIDE run_combined, after this tracker was built -> read the seed on the first frame
                #   (key=None = the long object; its seed now comes from perceive() too, stage 3)
            saved = sim.d.mocap_pos.copy()                     # perceive_all parks the markers -> restore
            dets = shape_clf.perceive_all(sim)
            obs, conf, kont = None, 0.0, False
            if key is not None:                                # SHAPE-keyed servo cands (L/U, open classes)
                cands = [d for d in dets if d["shape"] == key and d["pos"] is not None]
                if not cands and FORM_SPLIT:                   # fused -> form descriptor destroyed; re-read
                    _ck = colour_of_body.get(body)             #   the FORM on the colour-separated part
                    if _ck:                                    #   (measured obj_T: 8.8% -> 81% when fused)
                        cands = [d for d in shape_clf.perceive_colour(sim, colours, _ck, with_form=True)
                                 if d["shape"] == key and d["pos"] is not None]
                        if cands:                              # counted SEPARATELY from the colour split so
                            vc._fsv["fsplit"] = vc._fsv.get("fsplit", 0) + 1   # a run can tell them apart
                if not cands and KONTINUITAET and mem["xy"] is not None:
                    # KONTINUITAET (s.o.): Klasse ausgefallen, Glaube steht -> dem naechsten
                    # FARB-Teil folgen statt blind zu werden.  Die Sprungschranke unten sichert.
                    _ckk = colour_of_body.get(body)
                    if _ckk:
                        cands = [d for d in shape_clf.perceive_colour(sim, colours, _ckk)
                                 if d["pos"] is not None]
                        if cands:
                            kont = True
                            vc._fsv["kont"] = vc._fsv.get("kont", 0) + 1
            elif ckey is not None:                             # COLOUR-CLASS-keyed servo cands (cubes)
                cands = [d for d in dets if d["pos"] is not None
                         and colours.classify(d["chroma"])[0] == ckey]
                if not cands and COLOUR_SPLIT:                 # fused with a neighbour -> recover by the
                    cands = shape_clf.perceive_colour(sim, colours, ckey)   # PIXEL colour split, else the
                    #   servo goes blind for the whole episode (measured: red lost the fovea in 5 of 6
                    #   GUI episodes -- the [Fovea-Servo] line was missing entirely)
                    if cands:                                  # COUNT per frame (printing every frame would
                        vc._fsv["split"] = vc._fsv.get("split", 0) + 1   # flood the log) -> reported once
                        #   in the per-episode [Fovea-Servo] line below
            else:
                cands = []                                     # long: display-only blob follower
            sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
            if cands:
                if mem["xy"] is None:                          # first sighting: most confident match
                    best = (max(cands, key=lambda d: d["prob"]) if key is not None
                            else min(cands, key=lambda d: colours.classify(d["chroma"])[1]))
                else:                                          # tracking: nearest to the belief
                    best = min(cands, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"]) - mem["xy"])))
                if mem["xy"] is None or float(np.linalg.norm(np.asarray(best["pos"]) - mem["xy"])) <= 0.05:
                    obs = _off(_gp(best, body))                # correct toward the GRASP point (+ the learned
                    conf = (float(best["prob"]) if (key is not None and not kont)  # offset, else the
                            else float(np.clip(1.0 - colours.classify(best["chroma"])[1]  # servo fights it
                                               / (2.0 * colour_openset.TH), 0.0, 1.0)))
                    mem["xy"] = np.asarray(best["pos"], float); mem["px"] = np.asarray(best["px"], float)
                    vc._fsv["nd"] += 1
                    if KEIMDIAG and not mem.get("_keim_gemeldet"):
                        mem["_keim_gemeldet"] = True
                        _bp = np.asarray(best["pos"], float)
                        _tr = [(float(np.linalg.norm(sim.obj_pos(_o)[:2] - _bp)), _o)
                               for _o in act16.OBJS]
                        _dm, _wer = min(_tr) if _tr else (float("nan"), "?")
                        _kp = mem.get('_keim') and getattr(perception, 'seed_priv', False)
                        print(f"    [Keim] {body}: Keim "
                              f"{('JA (PRIVILEGIERT)' if _kp else 'JA') if mem.get('_keim') else 'NEIN'} "
                              f"(gesucht '{_kkey}', veroeffentlicht '{getattr(perception, 'seed_key', '?')}')"
                              f" | {len(cands)} Kandidaten -> Start auf {_wer} ({1000*_dm:.0f} mm)"
                              f" | eigenes Objekt {1000*float(np.linalg.norm(sim.obj_pos(body)[:2] - _bp)):.0f} mm"
                              f" | {'RICHTIG' if _wer == body else 'FALSCH'}", flush=True)
            if obs is None and mem["px"] is not None and dets:  # class match failed (lifted/mis-class/long) ->
                near = min(dets, key=lambda d: float(np.linalg.norm(np.asarray(d["px"]) - mem["px"])))
                if float(np.linalg.norm(np.asarray(near["px"]) - mem["px"])) < 40.0:   # follow the blob in px
                    mem["px"] = np.asarray(near["px"], float)
            if mem["px"] is not None:                          # form tracker drives the hex fovea view
                lo, hi = HEX_F * vc.fovea.K, RES - HEX_F * vc.fovea.K
                _d0b_lift = D0B_LIFT_PROBE and getattr(act16.run_combined, "_d0b_phase", "") == "lift"
                # IDENTITY-CONDITIONED net gaze: point the hex fovea at the commanded object's OWN
                # self-labelled COLOUR CLASS (centroid chroma) -- fovea_gradient then drives toward THAT
                # object (no detector needed for the drive's identity, only a light occlusion re-anchor).
                id_mu = colours.classes.get(colour_of_body.get(body), {}).get("mu") if FOVEA_NET else None
                if FOVEA_NET:
                    # LEARNED FOVEA GAZE (user's goal: WHERE to look is a NET decision like the arm servos).
                    # The gaze is its own state, DRIVEN by the net's active-inference gradient on the sel
                    # channel (class-conditioned saliency, id_mu) + centring the perceived blob.  Recovery
                    # from occlusion/carry: the PREDICTIVE MEMORY (belief -> hand while carrying) if enabled,
                    # else the DETECTOR re-anchors every FOVEA_ANCHOR frames.
                    if mem.get("gaze") is None:
                        mem["gaze"] = np.asarray(mem["px"], float)   # seed from the first detection
                    mem["_fc"] = mem.get("_fc", 0) + 1
                    if not FOVEA_MEM and mem["_fc"] % FOVEA_ANCHOR == 0:
                        mem["gaze"] = 0.5 * mem["gaze"] + 0.5 * np.asarray(mem["px"], float)
                    if _d0b_lift:
                        if mem.get("_d0b_lift_gaze") is None:
                            mem["_d0b_lift_gaze"] = np.asarray(mem["gaze"], float).copy()
                        gaze = np.asarray(mem["_d0b_lift_gaze"], float)
                    else:
                        mem.pop("_d0b_lift_gaze", None)
                        gaze = np.clip(mem["gaze"], lo, hi)
                else:
                    gaze = np.clip(mem["px"], lo, hi)              # detector-set gaze (default, unchanged)
                vc._P["state"]["gaze"] = gaze
                img = sim.render(CAM)
                if id_mu is not None:                              # class-conditioned perception (sel = the
                    arr = vc.fovea.step_id(img, gaze, id_mu, not D0_FREEZE)
                else:
                    arr = vc.fovea.step(img, gaze, vc._P["state"]["cmd"], not D0_FREEZE)
                # D0b trace payload before any consumer interprets it.  `px` and `gaze` stay in
                # image coordinates: above the table, the homography is deliberately invalid.
                # The callback in run_combined adds only phase and proprioception after this real
                # camera observation.  No simulator truth enters this structure.
                _top_d0b = np.asarray(vc.fovea.net.node("top").mu)
                vc._d0b_frame = {
                    "gaze_px": [float(x) for x in np.asarray(gaze, float)],
                    "follow_px": None if mem.get("px") is None else
                                 [float(x) for x in np.asarray(mem["px"], float)],
                    "sensor_error": float((vc.fovea.last_diag or {}).get("sensor_error", 0.0)),
                    "top_re": [float(x) for x in np.real(_top_d0b)],
                    "top_im": [float(x) for x in np.imag(_top_d0b)],
                    "id_conditioned": bool(id_mu is not None),
                    "frozen": bool(D0_FREEZE),
                    "lift_probe_fixed_gaze": bool(_d0b_lift),
                }
                _d0b_sel_px = None; _d0b_sel_mass = 0.0
                if FOVEA_NET:
                    ctr = (HEX_F - 1) / 2.0
                    sel = np.real(arr[:, :, 0]) if id_mu is not None else None
                    if sel is not None and float(sel.sum()) > 0.3:  # IDENTITY drive: class-colour saliency
                        mem["_lost"] = 0                            #   present -> fovea_gradient toward it
                        com = com2d(sel)
                        _d0b_sel_mass = float(sel.sum())
                        if com is not None:
                            _d0b_sel_px = np.asarray(gaze, float) + warp_gaze_delta(com, ctr, vc.fovea._ek())
                        vc._d0b_frame.update({
                            "selection_px": None if _d0b_sel_px is None else
                                            [float(x) for x in _d0b_sel_px],
                            "selection_mass": _d0b_sel_mass,
                            "selection_cell_com": None if com is None else [float(x) for x in com],
                        })
                        drive = -fovea_gradient(vc.fovea.cells)     # net active-inference gaze drive
                        if com is not None and not _d0b_lift:
                            mem["gaze"] = np.clip(np.asarray(gaze, float)
                                                  + warp_gaze_delta(com, ctr, vc.fovea._ek())
                                                  + np.clip(drive * 6.0, -2, 2), lo, hi)
                        mass = float(np.clip(sel.max(), 0.0, 1.0))
                        # FOVEA-DRIVEN SERVO (the branch goal): while THIS identity lock holds, the
                        # net's own gaze belief -- not the detector -- supplies the approach obs: the
                        # seeded grasp point shifted by the gaze's world motion since the FIRST lock
                        # (anchor fs0, so a constant gaze<->centroid offset cancels and the grasp
                        # geometry survives -- a U's centre is a hole).  Same 5cm jump gate as the
                        # detector path; the sustained-loss branch below never reaches here, so a
                        # wrong-object fixation (user-observed) cannot steer the arm: the lock IS the
                        # gate.  "shadow" only measures |net - detector|.
                        if (FOVEA_SERVO != "0" and com is not None and shape_clf.H is not None
                                and (_sk := perception.seed_for(key)) is not None
                                and _sk[2] is not None
                                and sim.d.qpos[sim.jqadr["joint_5"]] >= act16.J5_CLOSED_TH):
                            # gripper-open gate: while CARRYING, the table-plane px->world map is wrong
                            # for the lifted object (run_combined ignores servo obs outside over/lower
                            # anyway, pc_act16 ~379 -- the gate keeps the shadow STATS honest and the
                            # anchor fs0 from being dragged by a carried object)
                            wg = shape_clf._px_to_world(np.asarray(mem["gaze"], float))[0]
                            if mem.get("fs0") is None:
                                mem["fs0"] = wg
                            dxy = wg - mem["fs0"]
                            pos_f = _sk[0] + dxy
                            if mem["xy"] is None or float(np.linalg.norm(pos_f - mem["xy"])) <= 0.05:
                                obs_f = _off(_sk[2] + dxy)
                                vc._fsv["nf"] += 1
                                if obs is not None:
                                    vc._fsv["d"].append(float(np.linalg.norm(obs_f - obs)) * 1000.0)
                                if FOVEA_SERVO == "1":
                                    # the identity LOCK is the confidence statement; map mass into
                                    # [0.5, 1] so a held lock always clears SERVO_CONF=0.5 (mass is a
                                    # saliency MAGNITUDE, not a class probability -- raw mass < 0.5
                                    # would count as "lost" and trigger detector re-acquire saccades)
                                    obs, conf = obs_f, 0.5 + 0.5 * mass
                    elif mem.get("_lost", 0) < 4:                  # BRIEF loss (occlusion flicker): keep the
                        mem["_lost"] = mem.get("_lost", 0) + 1     #   gaze on the material via raw occupancy
                        occ = np.ptp(np.real(arr[:, :, 1:]), axis=2)
                        com = com2d(occ)
                        if com is not None and float(occ.sum()) > 0.3:
                            mem["gaze"] = np.clip(np.asarray(gaze, float)
                                                  + warp_gaze_delta(com, ctr, vc.fovea._ek()), lo, hi)
                        mass = float(np.clip(occ.max(), 0.0, 1.0))
                    else:                                          # SUSTAINED identity loss = the material
                        mem["_lost"] = mem.get("_lost", 0) + 1     #   under the fovea is NOT the commanded
                        com = None; mass = 0.0                     #   object (user-observed: occupancy
                        #   centering LOCKED onto a wrong object and held itself there).  Release the
                        #   lock (no centering) and SEARCH: zoom_step(0) below widens the view toward
                        #   ZOOM_MAX until the class saliency re-enters the crop -- the identity branch
                        #   then re-acquires and the zoom narrows back in.  Active inference, no detector.
                    # NET-STEERABLE ZOOM (ACT_FOVEA_ZOOM=1; else a no-op): confident lock -> zoom IN
                    # (down to ZOOM_MIN detail), lost -> zoom OUT for the search overview.
                    centrality = float(np.exp(-np.linalg.norm(com - ctr) / 4.0)) if com is not None else 0.0
                    vc.fovea._zoom_step(mass * centrality)
                    if FOVEA_MEM:                                  # PREDICTIVE MEMORY drives recovery (no
                        visible = com is not None and mass > 0.15  #   detector): seen -> belief snaps to the
                        # NB: a PIXEL observation for the memory ONLY -- must NOT reuse `obs`, which is the
                        # world-xy grasp servo obs returned below (clobbering it fed px-as-metres to the
                        # grasp servo -> the arm flew off, never grasped: the 897ca5a "alles kaputt" bug).
                        obs_mem = mem["gaze"] if visible else None  #   net's centred estimate; hidden while
                        try:                                       #   carrying -> belief follows the hand
                            hand_px = shape_clf._world_to_px(sim.grasp_pos()[:2])[0]
                        except Exception:
                            hand_px = None
                        carrying = bool(sim.d.qpos[sim.jqadr["joint_5"]] < act16.J5_CLOSED_TH)
                        # ETAPPE 1 des Port-Umbaus: statt objmem.update(obs, hand, carrying) laeuft
                        # diese Kante jetzt UEBER DIE PORTS -- Werte in die In-Ports, Modul ueber den
                        # ArmAgent takten, Ergebnis aus dem Out-Port lesen.  Das Modul bekommt keine
                        # Argumente mehr.  Verhaltensneutral: belief_px wird in step() nur gesetzt,
                        # wenn der Glaube existiert, und update() gibt ohnehin eine Kopie zurueck --
                        # vor der ersten Sichtung liefern beide Wege None.
                        objmem.set_in("obj_px_obs", obs_mem)
                        objmem.set_in("hand_px", hand_px)
                        objmem.set_in("carrying", [1.0 if carrying else 0.0])
                        agent.step(["ObjectMemory"])
                        belief = objmem.get_out("belief_px")
                        # CONFIDENCE GATE (user-observed): after the release the belief HELD the last
                        # hand px, so the gaze parked on the ROBOT and never returned to the object.
                        # A decayed belief must release the gaze -> the occupancy/identity centering
                        # above re-acquires the object.
                        if not visible and belief is not None and objmem.conf >= 0.25:
                            mem["gaze"] = np.clip(np.asarray(belief, float), lo, hi)
                        # chart diagnostic: the memory's PREDICTION ERROR vs the detector's last fix --
                        # rises while the belief coasts through carry/occlusion, snaps down on a sighting
                        objmem.err_px = (float(np.linalg.norm(np.asarray(belief, float)
                                                              - np.asarray(mem["px"], float)))
                                         if belief is not None else float("nan"))
                    if _dbg:                                        # net-gaze tracking quality + zoom use
                        vc._fovea_drift = getattr(vc, "_fovea_drift", [])   # gaze<->detector px (small=tracks)
                        vc._fovea_drift.append(float(np.linalg.norm(
                            np.asarray(gaze, float) - np.asarray(mem["px"], float))))
                        vc._fovea_zoom = getattr(vc, "_fovea_zoom", [])
                        vc._fovea_zoom.append(float(vc.fovea.z))
                if vc.viz is not None:
                    vc.viz.fovea(img, gaze, vc.fovea._ek(), np.clip(arr[:, :, 1:], 0, 1),
                                 f"{'Netz-Servo' if FOVEA_SERVO == '1' else ('Netz-Blick' if FOVEA_NET else 'Form-Tracker')} folgt {key or body}")
                plot_surprise()
            else:
                track_and_plot()                               # nothing tracked yet -> the colour follow frame
            return obs, conf

        return _track

    HOME_Q3 = np.array([HOME[j] for j in ARM3])            # all positioning joints (3, or 4 with joint_3)

    def drive_home():
        """CONTINUOUS episode transition: after the release the arm DRIVES back to (near) its home posture
        under its normal actuators (the same reach primitive the episode uses) instead of the qpos teleport
        arm_home() does -- a physical robot can't teleport, and the user wants sim runs to stay connectable
        to the real rig.  Two legs: RAISE the claw first (a low sideways retreat could sweep the just-placed
        object), then bounded joint-space steps toward home.  NEAR home is enough (0.05 rad/joint): the next
        episode starts from a SIMILAR pose, not a bit-identical one (run_combined gets arm_reset=False).
        WRIST: set_arm3_targets CLOBBERS joint_4 to HOME on every call (the aa8446a bug class) -- without a
        per-step re-assert the wrist WHIPPED home at ground level on the first leg-1 step and flung the
        just-placed object (user-observed).  So leg 1 HOLDS the episode's wrist angle while lifting; only
        leg 2, at carry height, ramps it home at a bounded rate."""
        sim.target("joint_5", act16.J5_OPEN)
        HOME_Z_MIN = float(os.environ.get("ACT23_HOME_Z_MIN", "0"))       # Vorgabe 2026-08-30; Hoehen-Wache in Bein 2
        w = float(sim.d.qpos[sim.jqadr["joint_4"]])            # the wrist angle the episode ended with
        HOME_W = HOME["joint_4"]
        for k in range(60):                                    # leg 1: straight up, wrist HELD
            q3 = sim.arm3_angles(); h = sim.grasp_pos()
            if h[2] > act16.CARRY_Z - 0.01:
                break
            sim.set_arm3_targets(q3 + bm.body.reach_velocity(sim.arm_angles_full(), np.array([h[0], h[1], act16.CARRY_Z]),
                                                             gain=2.0, max_dq=0.026))
            sim.target("joint_4", w)                           # re-assert vs the set_arm3_targets clobber
            sim.step(2)
            if panel is not None and k % 8 == 0:
                panel.update(sim.render(CAM), "Arm hebt ab ...")
        for k in range(240):                                   # leg 2: joints home, wrist RAMPED home slowly
            q3 = sim.arm3_angles()
            if float(np.max(np.abs(q3 - HOME_Q3))) < 0.05 and abs(w - HOME_W) < 0.1:
                break
            step = np.clip(HOME_Q3 - q3, -0.03, 0.03)
            # HOEHEN-WACHE (user-beobachtet: "die Finger schleifen beim Zurueckfahren manchmal am
            # Boden, wenn der Arm beim Ablegen weit weg von der Base war").  Die Gelenkraum-
            # Interpolation ist NICHT hoehenerhaltend: gemessen in der echten Sim faellt der tiefste
            # Klauenpunkt waehrend Bein 2 von 69mm (Ablage nah) auf 23mm (Ablage bei r=0.27) -- das
            # ist die Hoehe eines 24mm-Objekts.  Das gelernte FK-Modell zeigt diesen Durchhang NICHT
            # (es sagte konstant 89mm voraus), deshalb wird hier die TATSAECHLICHE Hoehe aus der Sim
            # gelesen und reaktiv gegengesteuert, statt sich auf die Vorhersage zu verlassen.
            hz = float(sim.grasp_pos()[2])
            if hz < HOME_Z_MIN:
                h = sim.grasp_pos()
                lift = bm.body.reach_velocity(sim.arm_angles_full(), np.array([h[0], h[1], act16.CARRY_Z]),
                                              gain=2.0, max_dq=0.03)
                step = 0.5 * step + 0.5 * lift                 # heimwaerts UND wieder hoch
            sim.set_arm3_targets(q3 + step)
            w += float(np.clip(HOME_W - w, -0.02, 0.02))
            sim.target("joint_4", w)
            sim.step(2)
            if panel is not None and k % 8 == 0:
                panel.update(sim.render(CAM), "Arm fährt zur Ausgangsposition ...")

    res = {}
    def ep_end(ep, ok, err): res["ok"] = bool(ok); res["err"] = float(err)

    def _blick_merkmale(o, h, hz):
        """Merkmale des Blicks: gesehener Versatz, Handlage, Hoehe und deren Produkt (Parallaxe waechst
        mit Hoehe mal Abstand zur Kamera)."""
        return np.array([1.0, o[0], o[1], h[0], h[1], hz, h[0] * hz, h[1] * hz], float)

    def _blick_vorhersage(f):
        """Ridge-Regression auf blick_daten; None, solange zu wenig Beispiele da sind."""
        if len(blick_daten) < BLICK_MIN:
            return None
        X = np.array([np.asarray(x, float) for x, _y in blick_daten])
        Y = np.array([np.asarray(y, float) for _x, y in blick_daten])
        mu, sd = X.mean(0), X.std(0) + 1e-9
        mu[0], sd[0] = 0.0, 1.0
        Z = (X - mu) / sd
        W = np.linalg.solve(Z.T @ Z + 1.0 * np.eye(Z.shape[1]), Z.T @ Y)
        return ((np.asarray(f, float) - mu) / sd) @ W

    _blick_akt = {"v": None}
    _obj_ref = {"chroma": None}                        # s. OBJ_EIG = 2

    def _objekt_merken(hand_xy, hand_z):
        """Die Farbe des eigenen Objekts IN DER HAND merken (s. OBJ_EIG = 2): naechster Fleck an der Hand."""
        _obj_ref["chroma"] = None
        if OBJ_EIG < 2:
            return
        saved = sim.d.mocap_pos.copy()
        dets = shape_clf.perceive_all(sim)
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        _h = np.asarray(hand_xy, float)[:2]
        nah = [d for d in dets if d.get("pos") is not None and d.get("chroma") is not None
               and float(d.get("area", 0.0)) >= 100.0
               and float(np.linalg.norm(np.asarray(d["pos"], float) - _h)) < 0.04]
        if not nah:
            print("    [Objektfarbe] in der Hand nicht gesehen -- keine Referenz", flush=True)
            return
        d = min(nah, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"], float) - _h)))
        _obj_ref["chroma"] = np.asarray(d["chroma"], float).copy()
        _d0 = getattr(situation_feats, "last_det", None)
        _txt = ""
        if _d0 is not None and _d0.get("chroma") is not None:
            _txt = f", Abstand zur Tischsichtung {float(np.linalg.norm(_obj_ref['chroma'] - np.asarray(_d0['chroma'], float))):.3f}"
        print(f"    [Objektfarbe] in der Hand gemerkt{_txt}", flush=True)

    def _objekt_sehen(hand_xy, hand_z):
        """Das getragene Objekt ansehen: die Detektion naechst der Hand.  Nur Kamera + eigene Hand."""
        saved = sim.d.mocap_pos.copy()
        dets = shape_clf.perceive_all(sim)
        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
        _h = np.asarray(hand_xy, float)
        _d0 = getattr(situation_feats, "last_det", None) if OBJ_EIG == 1 else None
        _c0 = (np.asarray(_d0["chroma"], float) if (_d0 is not None and _d0.get("chroma") is not None)
               else (_obj_ref["chroma"] if OBJ_EIG >= 2 else None))
        if _c0 is not None:
            # UEBER DIE EIGENSCHAFT (s. OBJ_EIG): nur Flecken in der Farbe des eigenen Objekts
            nah = [d for d in dets if d.get("pos") is not None and float(d.get("area", 0.0)) >= 100.0
                   and d.get("chroma") is not None
                   and float(np.linalg.norm(np.asarray(d["chroma"], float) - _c0)) < OBJ_EIG_TOL
                   and float(np.linalg.norm(np.asarray(d["pos"], float) - _h)) < 0.06]
            if not nah:
                # DIAGNOSE: warum nicht gesehen?  Alle Flecken im 60-mm-Umkreis mit Abstand,
                # Farbabstand und Flaeche (auch die unter 100 px).
                _nd = sorted((float(np.linalg.norm(np.asarray(d["pos"], float) - _h)), d) for d in dets
                             if d.get("pos") is not None
                             and float(np.linalg.norm(np.asarray(d["pos"], float) - _h)) < 0.06)
                print("    [Objektblick] kein Fleck in der Farbe; nahe: " + (", ".join(
                    f"{1000.0 * r:.0f}mm Farbe "
                    + (f"{float(np.linalg.norm(np.asarray(d['chroma'], float) - _c0)):.3f}" if d.get("chroma") is not None else "-")
                    + f" Flaeche {float(d.get('area', 0.0)):.0f}" for r, d in _nd) or "keine")
                    + f" | Hand {1000.0 * float(hand_z):.0f}mm hoch", flush=True)
        else:
            nah = [d for d in dets if d.get("pos") is not None and float(d.get("area", 0.0)) >= 100.0
                   and float(np.linalg.norm(np.asarray(d["pos"], float) - _h)) < 0.04]
        if not nah:
            return None
        d = min(nah, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"], float) - _h)))
        g = np.asarray(d["pos"], float)
        if BLICK_LERNEN:                                   # s. BLICK_LERNEN
            _o = g[:2] - _h[:2]
            _f = _blick_merkmale(_o, _h[:2], float(hand_z))
            _p = _blick_vorhersage(_f)
            _blick_akt["v"] = {"f": _f, "o": _o, "p": _p}
            if BLICK_LERNEN >= 2 and _p is not None:
                return _h[:2] + np.asarray(_p, float)       # die gelernte Landestelle statt des Rohblicks
        return g

    def _ziel_nachsehen():
        """Der ZWEITE Blick auf das Ziel (s. ACT23_ZIEL_NACHSEHEN): dieselbe Aufloesung wie zu Beginn,
        jetzt aus der Naehe.  Scheitert sie (verdeckt, mehrdeutig), bleibt das erste Ziel stehen."""
        bez = state.ziel_bezug
        if bez is None or bez.get("relation") not in ("an", "richtung") or not bez.get("aufgeloest"):
            return None
        _merk = {k: bez.get(k) for k in ("aufgeloest", "ziel_xy", "ziel_rel")}
        print("    [Ziel-Nachsehen] zweiter Blick auf das Ziel", flush=True)
        q = state.ziel_loeser(bez)
        if q is None:
            bez.update(_merk)                          # erster Blick bleibt gueltig
            return None
        return q

    _dbg = os.environ.get("ACT23_DEBUG", "0") == "1"
    _dbgimg = os.environ.get("ACT23_DEBUG_IMG", "")
    def _pos():
        return {nm: np.round(sim.obj_pos(nm)[:2], 3).tolist() for _l, nm, _m in state.OBJECTS}
    def _save(tag):
        if _dbgimg:
            from PIL import Image
            Image.fromarray(sim.render(CAM)).save(os.path.join(_dbgimg, f"stage_{tag}.png"))

    # `run_combined` receives one inner episode per outer AUTO episode and restarts its own
    # counter at zero.  D0b needs the outer trajectory identity for a scene/trajectory split.
    d0b_trace_episode = [0]

    def run_one():
        import time as _time
        d0b_trace_episode[0] += 1
        _d0b_episode_id = d0b_trace_episode[0]
        # ZEITKONTO je Episode (Nutzerwunsch 2026-08-02: sehen, wann die CPU nicht mehr reicht).
        # Grob nach BLOECKEN, nicht nach Funktionen -- die Frage ist "welcher Teil wird teuer", und
        # genau auf dieser Ebene kann man handeln (Fovea-Aufloesung, Trainings-Epochen, Episodenlaenge).
        # Die Fovea zaehlt SICH SELBST (HexFovea.step), weil sie sonst in der Ausfuehrung verschwindet.
        _T = {"gesamt": _time.perf_counter()}
        _fov0 = getattr(vc.fovea, "t_step", 0.0), getattr(vc.fovea, "n_step", 0)
        _l, body, method = state.selected()
        # SNAPSHOT every object's pose before acting.  run_combined parks distractor cubes off-table and the
        # arm can knock objects -> afterwards restore all NON-commanded objects to exactly here, so the scene
        # stays put and only the commanded object moves (to the target).  No more surprise re-scatter.
        snap = {nm: (sim.obj_pos(nm)[:2].copy(), float(sim.obj_pos(nm)[2]), float(sim.obj_yaw(nm)))
                # STUETZEN MIT AUFNEHMEN (s. state.STUETZEN): der Sockel ist kein Objekt, muss aber
                # wie jedes nicht-kommandierte Ding nach der Episode zurueck an seine Stelle --
                # sonst wandert die Auflage ueber den Lauf davon, sobald der Arm sie anstreift.
                # Die Aufraeumschleife unten laeuft ueber `snap`, also genuegt dieser Zusatz.
                for nm in dict.fromkeys([n for _l2, n, _m in state.OBJECTS] + list(state.STUETZEN))}
        if _dbg: print(f"    [dbg] before  : {_pos()}", flush=True)
        _save(f"{body}_0before")
        perception.clear_seed()                                # form tracker seeds from THIS command's select()
        # STAGE 3 cube de-crutching: a cube with a bound SELF-LABELLED colour class localises + servos
        # via that class (like the long object) -- the trained vc hex codes and the red marker parking
        # remain only as FALLBACK while the class isn't born/bound yet (or ACT23_CUBE_VC=1 restores them).
        cube_ckey = (colour_of_body.get(body)
                     if method == "color" and os.environ.get("ACT23_CUBE_VC", "0") != "1" else None)
        if method == "color" and cube_ckey is None:            # FALLBACK display: drive the FOVEA to the cube
            #   via the vc colour code.  With a colour class the form tracker drives the view itself.
            #   LONG never drives by colour: its obj_blue code FIRES ON THE CYAN U (user-observed).
            try:
                if body == "obj_red":                          # red-only marker parking (see perceive())
                    saved = sim.d.mocap_pos.copy(); shape_clf._park_markers(sim)
                    try:
                        vc.perceive(body)
                    finally:
                        sim.d.mocap_pos[:] = saved; mujoco.mj_forward(sim.m, sim.d)
                else:
                    vc.perceive(body)
                if panel is not None:
                    track_and_plot(); panel.update(sim.render(CAM), f"Fovea -> {_l}")
            except Exception:
                pass
        u_cmd = (body == "obj_U"); wf = None
        fe = situation_feats(body)                               # perceived situation for the LIFELONG loop
        a_exec = None                                            # FULL action this episode runs (self mode):
        sel_off["dxy"] = None                                    #   [offset, wrist, grip, gentle]
        _mu_a = _sd_a = None                                     # Modell-Bewertung DER WAHL (s. [Welt-Vorhersage])
        # STAGE-1 de-scripting: in self mode the world model picks the WHOLE action for EVERY object --
        # wrist (the fixed teacher angle slips off diagonal cubes), grasp-point OFFSET (off_max>0),
        # and grip close-angle + gentle-carry, which used to be the hand-coded body=='obj_U' runtime
        # rules (the user's no-runtime-rules principle: the net decides, conditioned on the perceived
        # form descriptor).  L/U/T get own startup trials now; the teacher path below remains as pure
        # TRAINING scripting whose choices are logged as demonstrations.
        use_net = state.choreo in ("netz", "attractor") and runtime.trained   # decided HERE: it also gates
        #   exploration.  "attractor" is a NETZ-family mode: the runtime policy still drives the grasp;
        #   only the latent PLACE servo is replaced by the model-based attractor plan (Etappe 3, below).
        if state.policy == "self" and fe is not None:
            n_cand = 24 if (state.auto and not use_net) else 0  # EXPLORE only in the Auto self-play (random
            #   offset/grip candidates); a MANUAL command EXPLOITS the structured grid (offset-0 wrists x
            #   grip regimes) -- the user watched a young model pick edge offsets + non-closing grips.
            #   NOT on Netz episodes: the world model gets NO outcome labels there (poisoning fix), so
            #   random candidates are pure risk without learning -- exploit the model's best action.
            offs = None
            det = getattr(situation_feats, "last_det", None)
            # FALSIFIABILITY COUPLING (measured in the user's 260-ep netz run: Bilanz collapsed to
            # 3-6/30 with broad "nicht gegriffen" floods while sigma stayed inflated 0.9-2.0): with
            # the netz failure-route abstaining, a mask OFFSET that PREVENTS the lift never gets a
            # label -- the same unfalsifiability trap as the wrist, reopened through the offset door;
            # inflated sigma pushes LCB exactly into those unlabeled extrapolation offsets (model
            # exploitation, the act22 lesson).  Candidates are only OFFERED where the failure route
            # can label them: FSM episodes (or ACT23_ATTEMPT_NETZ=1).
            #
            # SEIT 2026-08-01 auch auf NETZ-Episoden -- weil der FALSIFIZIERER jetzt existiert.  Der
            # Fingerdruck-Streifen labelt genau das, was ein schlechter Greifpunkt anrichtet: kein Druck
            # beim Heben = die Klaue hat nie gehalten, kausal am GRIFF und an nichts sonst.  Gemessen im
            # 413-Ep-Netz-Lauf: feuert in 34% der Episoden, 138 von 139 Treffern waren echte
            # Nicht-Lieferungen, und die Enthaltungsquote fiel 33-43% -> 25%.  Damit ist die Begruendung
            # oben ("die netz-Fehlerroute enthaelt sich") ueberholt.  Der Puffer zeigt, was der Riegel
            # gekostet hat: die letzten ~1500 Zeilen haben Offset EXAKT 0 -- das Modell konnte nicht
            # lernen, WO es greifen soll, weil nie etwas anderes probiert wurde.
            # BLEIBT ENG: auf Netz-Episoden ist n_cand=0, es kommen also KEINE Zufalls-Offsets dazu --
            # nur die <=6 maskenabgetasteten Punkte auf echtem Material (<=50mm).  Ehrliche Grenze: ~38%
            # der Fehlschlaege fallen weiter als Enthaltung durch, die Falsifizierbarkeit ist also nicht
            # vollstaendig, nur nicht mehr null.  ACT23_GRASP_CANDS_NETZ=0 riegelt wieder ab.
            _griplabel = os.environ.get("ACT23_GRIPLABEL", "1") != "0"
            cands_ok = ((not use_net) or os.environ.get("ACT23_ATTEMPT_NETZ", "0") == "1"
                        or (_griplabel and os.environ.get("ACT23_GRASP_CANDS_NETZ", "1") != "0"))
            if (os.environ.get("ACT23_GRASP_CANDS", "1") == "1" and cands_ok
                    and det is not None and det.get("grasp_cands")):
                # GRASP-POINT DISCOVERY (user's standing goal): the candidates are REAL places on the
                # perceived material (mask-sampled), expressed as offsets from the heuristic point the
                # execution/servo uses as reference.  The world model SCORES them (LCB) against the
                # heuristic prior; credit routing (incl. the _attempted failure route) labels whatever
                # gets tried -- where to grip becomes the model's own, perception-grounded decision.
                g0 = np.asarray(det["grasp_xy"], float)
                offs = [np.asarray(p, float) - g0 for p in det["grasp_cands"]]
                # SCHRANKE 12mm (war 50mm -- zu weit gewaehlt, korrigiert nach dem 316-Ep-Lauf
                # 2026-08-01).  Gemessen, dosisabhaengig und in 5 von 6 Objekten getrennt sichtbar:
                #   Verschiebung  0-10mm -> 55% geliefert   (Heuristik-Referenz 52%)
                #                10-20mm -> 31%
                #                20-30mm -> 16%
                #                 30mm+  ->  0%  (0 von 18)
                # Griffverlust laut Drucksensor 17% (Heuristik) gegen 48% (verschoben).  Jenseits von
                # ~12mm EXTRAPOLIERT das Modell nur noch -- genau die act22-Modellausbeutung, und LCB
                # laeuft dort hinein, weil die Offset-Dimension kaum Zeilen hat.  Das ist KEINE neue
                # Regel: die Schranke gab es schon, sie stand nur an der falschen Stelle.
                # EHRLICH: auch 0-10mm zeigt keinen VORTEIL gegenueber dem heuristischen Punkt (55 vs
                # 52%) -- die Schranke rettet die Selbstkorrektur, sie belegt keinen Nutzen.
                # SCHRANKE AN DIE OBJEKTGROESSE GEKOPPELT (2026-08-07), vorher fest 12mm.
                # Gemessen an 1414 Episoden aus 20 Logs, Haltequote gegen die Verschiebung RELATIV zur
                # Material-Halbspanne des Objekts:
                #     0            62% (n=728)   <- heuristischer Punkt
                #     0.01-0.30    64% (n=276)   <- kein Schaden
                #     0.30-0.60    53% (n=234)
                #     0.60-1.00    35% (n=121)
                #     >1.00        24% (n= 55)
                # Absolut gemessen ist der Zusammenhang schwaecher (rho -0.145) als relativ (-0.161),
                # und die feste Schranke wirkt gegensaetzlich: bei den 24mm-Wuerfeln sind 6-12mm bereits
                # die halbe Objektbreite (Haltequote 28-38%), bei der 68mm langen Form dagegen harmlos
                # (65%).  Eine Zahl kann beides nicht treffen.
                # KEINE neue Regel: die Groesse kommt aus der eigenen Wahrnehmung (Material-Halbspanne
                # der Detektion), nicht aus einer Tabelle je Objekt.  ACT23_GRASP_CAND_FRAC=0 faellt auf
                # die alte feste Schranke zurueck.
                _abs = float(os.environ.get("ACT23_GRASP_CAND_CAP", "0.012"))
                _frac = float(os.environ.get("ACT23_GRASP_CAND_FRAC", "0.30"))
                _span = float(det.get("span") or 0.0)
                _cap = min(_abs, _frac * _span) if (_frac > 0 and _span > 0) else _abs
                offs = [o for o in offs if float(np.linalg.norm(o)) <= _cap]
            # ETAPPE 3 des Port-Umbaus: die AKTIONSWAHL laeuft ueber die Ports.  Erste Etappe, in
            # der ein Port ENTWORFEN werden musste -- das Welt-Modell hatte bisher nur einen
            # action-EINGANG (Aktion bewerten), aber keinen Ausgang fuer eine selbst GEWAEHLTE
            # Aktion.  chosen_action ist neu; step() unterscheidet die beiden Betriebsarten am
            # action-Port (gesetzt = bewerten, None = auswaehlen).
            # Die Auswahl-KNOEPFE bleiben bewusst ausserhalb der Ports (select_cfg): `offsets` ist
            # eine Liste variabler Laenge und `n` eine Anzahl -- ein Port ist ein Vektor fester
            # Dimension.  Datenfluss ueber Ports, Einstellungen daneben.
            world.set_in("situation", fe)
            world.set_in("action", None)
            world.select_cfg = dict(n=n_cand, lam=LAM, offsets=offs, curiosity=TILT_CURIOSITY)
            agent.step(["WorldModel"])
            a = world.get_out("chosen_action")
            _mu_a = float(np.ravel(world.get_out("p_success"))[0])
            _sd_a = float(np.ravel(world.get_out("uncertainty"))[0])
            a_exec = a; wf = (lambda s, _w=wrist_of(a): _w)
            # ANFAHR-NEIGUNG AUS DER AKTION: bisher stand dir_ref FEST auf senkrecht (0,0,-1) und die
            # Klaue kippte bei grossem Radius zwangslaeufig (gemessen: 45 Grad bei r=0.27, Korrelation
            # +1.00) -- "ein Finger von unten, einer von oben" (User).  Jetzt WAEHLT das Modell die
            # gewuenschte Neigung; sie wird in der RADIALEBENE nach aussen gekippt, weil genau dorthin
            # die Kinematik den Arm zieht.  Waehlt es die ohnehin erreichbare Neigung, entfaellt der
            # Konflikt zwischen Position und Haltung und es gibt keinen Positionsverlust.
            _tilt = wm_tilt_of(a)
            if TILT_ACTION:
                _nat = np.degrees(world.natural_tilt(world.radius_of(fe) or 0.0))
                print(f"    [Neigung] {body}: gewaehlt {np.degrees(_tilt):.0f} Grad "
                      f"(natuerlich {_nat:.0f}, r={100*(world.radius_of(fe) or 0):.0f}cm), "
                      f"sigma {_sd_a:.3f}", flush=True)
            if TILT_ACTION and _tilt > 1e-6:
                _p = np.asarray(fe[:2], float)
                _n = float(np.linalg.norm(_p))
                if _n > 1e-6:
                    _ux, _uy = _p / _n                      # Radialrichtung Basis -> Objekt
                    bm.body.dir_ref = np.array([np.sin(_tilt) * _ux, np.sin(_tilt) * _uy,
                                                -np.cos(_tilt)], float)
                    _dir_ref_set = True
            if float(np.linalg.norm(a[:2])) > 1e-9:
                sel_off["dxy"] = np.asarray(a[:2], float)
            if offs:
                # IMMER geloggt (nicht DEBUG-gated), wie [Neigung]: seit die Kandidaten auch im
                # Netz-Modus laufen, ist der Greifpunkt eine ECHTE Wahl des Modells und ein GUI-Lauf
                # muss nachvollziehbar bleiben -- "Bezug" = wieviel der gewaehlte Punkt vom
                # heuristischen abweicht, "dicht" = Abstand zum dichtesten (Kandidat 0).
                # den dichtesten Punkt EXPLIZIT aus der Detektion nehmen, nicht offs[0] annehmen: die
                # 50mm-Schranke oben kann ihn herausfiltern, dann waere offs[0] ein anderer Kandidat
                # und die Zeile loege ueber genau die Groesse, die man mitliest.
                _dn = det.get("grasp_dense")
                _d0 = None if _dn is None else np.asarray(_dn, float) - g0
                _sel = np.asarray(a[:2], float)
                _txt = "Heuristik" if float(np.linalg.norm(_sel)) <= 1e-9 else \
                       f"{1e3*_sel[0]:+.0f},{1e3*_sel[1]:+.0f}mm"
                _nd = "" if _d0 is None else f", zum dichtesten {1e3*float(np.linalg.norm(_sel-_d0)):.0f}mm"
                print(f"    [Greifpunkt] {body}: {_txt} aus {len(offs)} Masken-Kandidaten{_nd}",
                      flush=True)
            # A/B FORCE knobs (probe arms, PRIVILEGED, default off -- never a runtime rule): measure the
            # CAUSAL value of a correct wrist / a material-centred grasp point for the prong shapes
            # before anything is allowed to learn it.  ACT23_FORCE_WRIST=priv aligns the wrist to the
            # true yaw (relwrist=0 -- the direction the 40-ep YawAB probe found suggestive for L);
            # ACT23_FORCE_GRASP=prong replaces the model's grasp offset so the planned point sits ON
            # MATERIAL (L: centre of the free long-prong part, local (-7,+7)mm; U: base-bar centre
            # (0,-14)mm, the proven balanced grip) instead of the form centre (U's form centre = the
            # OPEN SLOT between the prongs, measured a coin flip).  a_exec is updated so credit labels
            # describe what actually RAN; probes run on disposable state copies only.
            _fw = os.environ.get("ACT23_FORCE_WRIST", "")
            if _fw in ("priv", "pair"):
                # "pair" = the shape-dependent pair hypothesis the two single-knob A/Bs uncovered:
                # L wants the wrist PARALLEL to the long prong (W arm 14/20 vs 9/20) while U wants it
                # QUER across the base bar (in the G arm 4 of 5 U deliveries had relwrist 61-72 deg,
                # aligned wrists at the bar failed) -- so pair adds 90 deg for obj_U, else = priv.
                wp = float(sim.obj_yaw(body))
                if _fw == "pair" and body == "obj_U":
                    wp += 0.5 * np.pi
                wp %= np.pi
                a_exec = a_exec.copy(); a_exec[2], a_exec[3] = np.cos(2 * wp), np.sin(2 * wp)
                wf = (lambda s, _w=wp: _w)
            if (os.environ.get("ACT23_FORCE_GRASP", "") == "prong" and body in ("obj_L", "obj_U")
                    and det is not None and det.get("grasp_xy") is not None):
                loc = np.array([-0.007, 0.007]) if body == "obj_L" else np.array([0.0, -0.014])
                yr = float(sim.obj_yaw(body)); cy, sy = np.cos(yr), np.sin(yr)
                tgt = sim.obj_pos(body)[:2] + np.array([cy * loc[0] - sy * loc[1],
                                                        sy * loc[0] + cy * loc[1]])
                sel_off["dxy"] = tgt - np.asarray(det["grasp_xy"], float)
                a_exec = a_exec.copy(); a_exec[0], a_exec[1] = sel_off["dxy"]
            if a_exec is not None and world.n() > 0:
                # VORHERSAGE DES WELT-MODELLS fuer die AUSGEFUEHRTE Aktion, direkt vor der Ausfuehrung.
                # WOZU: erst damit laesst sich messen, wieviel des vorhandenen Signals das Modell
                # tatsaechlich einsammelt.  Die Wiederholungsmessung (ACT23_EXV, 40 Szenen x 4) hat
                # ergeben, dass ein Vorhersager, der nur die Situation sieht, 82% erreichen KOENNTE
                # (Grundrate 54%) -- ob das Modell bei 60 oder bei 80 steht, war aus dem Log nicht
                # ablesbar, weil mu nirgends stand.
                # ABSICHTLICH die ausgefuehrte Aktion und nicht das mu aus select_action: der
                # Greifpunkt und die FORCE-Knoepfe koennen a_exec danach noch verschieben, dann
                # bewertete select_action eine Aktion, die so nie gefahren wurde.  Weicht beides ab,
                # steht die urspruengliche Zahl daneben.
                try:
                    _mx, _sx = world.predict(fe, np.asarray(a_exec, float)[None])
                    _mx, _sx = float(np.ravel(_mx)[0]), float(np.ravel(_sx)[0])
                    _dr = ("" if _mu_a is None or abs(_mx - float(_mu_a)) < 5e-3
                           else f"  (bei der Wahl {float(_mu_a):.3f}, danach verschoben)")
                    print(f"    [Welt-Vorhersage] {body}: mu {_mx:.3f}  sigma {_sx:.3f}"
                          f"  (LCB {_mx - LAM * _sx:+.3f}){_dr}", flush=True)
                except Exception as _e:
                    if os.environ.get("ACT23_DEBUG", "0") == "1":
                        print(f"    [Welt-Vorhersage] uebersprungen: {_e}", flush=True)
            if EXV_FREEZE and a_exec is not None:
                # KONTROLLE der Wiederholungsmessung: die [Kredit]-Zeile zeigt nur Wrist und Grip,
                # der Aktionsvektor enthaelt aber auch Offset und Neigung.  Zwei Wiederholungen
                # koennten in Wrist/Grip uebereinstimmen und sich trotzdem unterscheiden -- dann
                # waere nicht die Ausfuehrung isoliert.  Voller Vektor, damit das PRUEFBAR ist.
                print("    [EXV-Aktion] " + " ".join(f"{v:+.4f}" for v in np.asarray(a_exec).ravel()),
                      flush=True)
            if os.environ.get("ACT23_YAW_AB", "0") == "1":
                # A/B measurement ONLY (never fed to a learner): the PRIVILEGED true long axis next
                # to the EXECUTED wrist/offset (after any force knob), so an offline script can test
                # whether the choice is yaw-CONDITIONED (concentration of wrist-yaw).
                w_used = wrist_of(a_exec)
                off_used = sel_off["dxy"] if sel_off["dxy"] is not None else np.zeros(2)
                yaw_t = np.degrees(sim.obj_yaw(body))
                line = (f"    [YawAB] {body} wrist {np.degrees(w_used) % 180.0:.1f} "
                        f"yaw {yaw_t % 180.0:.1f}")
                if body in ("obj_L", "obj_U"):
                    # PRONG-SHAPE extension (user-observed failure: the claw approaches the L along
                    # the long prong but DIAGONAL -> the form slips and spins away): L/U are not
                    # 180-deg symmetric, so log the full 360-deg yaw, the PLANNED grasp point rotated
                    # into the OBJECT frame (which prong / where on it: L long prong = local +y at
                    # x~-7mm, foot at y=-21mm; U prongs = local +y at x=+-23mm (32mm slot since
                    # 2026-07-18, was +-19), base bar y=-14mm),
                    # and the wrist RELATIVE to the yaw -- offline pairing with GELIEFERT/dyaw tests
                    # whether alignment + grasp placement predict the slip, before anything learns.
                    line += f" yaw360 {yaw_t % 360.0:.1f}"
                    if det is not None and det.get("grasp_xy") is not None:
                        gp = np.asarray(det["grasp_xy"], float) + np.asarray(off_used, float)
                        rel = gp - sim.obj_pos(body)[:2]
                        cy, sy = np.cos(-sim.obj_yaw(body)), np.sin(-sim.obj_yaw(body))
                        lo = np.array([cy * rel[0] - sy * rel[1], sy * rel[0] + cy * rel[1]]) * 1e3
                        line += (f" grasp_obj {lo[0]:.0f},{lo[1]:.0f}"
                                 f" relwrist {(np.degrees(w_used) - yaw_t) % 180.0:.1f}")
                print(line, flush=True)
            if _dbg:
                print(f"    [dbg] Aktion (Welt-Modell): Offset {np.round(a[:2] * 1000, 1).tolist()}mm, "
                      f"Wrist {np.degrees(wrist_of(a)) % 180.0:.0f} Grad, Grip {a[4]:.2f}"
                      f"{', sanft' if a[5] > 0.5 else ''} | {0 if offs is None else len(offs)} "
                      f"Masken-Kandidaten", flush=True)
        # CLOSED-LOOP fovea: servo=True lets the live tracker CORRECT the grasp-target belief during the
        # reach (+ occlusion memory).  L/U track via the FORM-aware tracker (make_shape_track:
        # perceive_all per frame, matched by SHAPE class); CUBES with a bound colour class track via the
        # SAME tracker keyed on the class (vc.track only as fallback) -- the user's fovea goal: the fovea
        # supports approach+grasp instead of sitting on whatever colour was last commanded.  Only the
        # long object stays servo=False (no class to key on when this comment was written; kept as-is).
        # EIGENSCHAFTS-KOMMANDO: die Fovea bekommt DENSELBEN Schluessel, den das Kommando nennt.
        # REGRESSION, die das noetig gemacht hat (Nutzerbefund 2026-09-05: "Die Fovea fokussiert
        # nun irgend etwas und der Arm greift irgend etwas.  Das passt nicht mehr zusammen und war
        # vorher perfekt."):  method="eigenschaft" fiel durch ALLE Zweige hier in den else-Fall --
        # generischer Tracker, vc._fsv=None -- und zusaetzlich stand unten servo=False.  Der Arm
        # fuhr also auf die Eigenschafts-Lokalisierung (die stimmt, 0-8 mm), die Fovea folgte
        # einem davon unabhaengigen Blob: ZWEI Glauben in einer Episode.  Nennt das Tripel eine
        # Formklasse, ist das exakt der shape-Pfad; nennt es eine Farbklasse, exakt der
        # Wuerfel-Pfad.  Nichts Neues -- nur nicht mehr daran vorbei.
        eig_servo = False
        if method == "eigenschaft":
            _ef, _efo, _eg = state.EIGENSCHAFT.get(body, (None, None, None))
            _skey = f"eig:{body}"                              # so veroeffentlicht perceive() den Keim
            if _efo is not None and _efo != EIG_GESEHEN:
                track_fn = make_shape_track(body, key=_efo, seed_key=_skey)   # Formklasse -> Form-Tracker
                eig_servo = True
            elif _ef is not None:
                track_fn = make_shape_track(body, ckey=_ef, seed_key=_skey)   # Farbklasse -> Farb-Tracker
                eig_servo = True
            else:
                # DER PLATZHALTER IST KEINE KLASSE (s. EIG_GESEHEN).  Eine Formachse ohne Namen
                # traegt nur einen Messwert -- make_shape_track wuerde einer Klasse folgen, die es
                # nicht gibt.  Also faellt die Adresse hier auf den FARB-Tracker durch, und hat sie
                # auch keine Farbklasse, bleibt es ehrlich bei servo=False.  Eine Fovea, die dem
                # Einbettungsvektor selbst folgt, ist ein eigener Bau und existiert nicht.
                # NUR die Groesse genannt: es gibt keinen Schluessel, dem ein Tracker folgen kann.
                # Dann EHRLICH nur Anzeige und servo=False, statt einen Regelkreis vorzutaeuschen.
                # Die Wuerfelei erzeugt solche Adressen nicht mehr (s. _auto_eig_umschreiben:
                # Nutzervorgabe "reine Groessen-Adressen brauchen wir nicht"), von Hand sind sie
                # weiterhin moeglich.
                track_fn = make_shape_track(body)
        elif method == "shape":
            track_fn = make_shape_track(body, key=state.SHAPE_KEY[body])
        elif method == "long":
            track_fn = make_shape_track(body)                  # display-only blob follower (no class to key on)
        elif cube_ckey is not None:                            # cube with a bound colour class: colour-keyed
            track_fn = make_shape_track(body, ckey=cube_ckey)  #   servo tracker (stage 3 de-crutching)
        else:
            track_fn = track_and_plot
            vc._fsv = None                                     # no form tracker -> no fovea-servo stats
        # ETAPPE 4 des Port-Umbaus: die gewaehlte Tracker-Closure wird ins PerceptionModule
        # gehaengt, und run_combined bekommt nicht mehr sie, sondern einen Port-Leser.  Der
        # Unterschied zu einer blossen Weiterreichung: das MODUL entscheidet, ob dieser Takt
        # gerechnet oder der letzte Stand gehalten wird (ACT23_PERCEPT_RATE).  Der Aufrufer kann
        # beides nicht unterscheiden -- genau darum geht es bei Punkt 4.
        perception.bind(track_fn)                              # setzt den Takt mit zurueck
        runtime.reset_takt()                                   # Regelpfad-Takt je Episode neu

        def _wahrnehmung_ueber_ports():
            agent.step(["Perception"])
            xy, c = perception.observation()
            # PUNKT 3 an seiner ersten echten Fundstelle.  Die Servo-Korrektur des Verbrauchers
            # ist KUMULATIV (pc_act16:412):
            #     obj_belief += SERVO_K * conf * (obs - obj_belief)
            # Bei PERCEPT_RATE > 1 liefert der Port zwischen zwei gerechneten Takten denselben
            # gehaltenen Wert -- und diese Korrektur wuerde ihn ein zweites Mal anwenden und den
            # Glauben doppelt so stark zu einer veralteten Sichtung ziehen.  Eine Beobachtung
            # zaehlte dann n-fach; genau die Fehlerklasse, wegen der Punkt 3 vor Punkt 4 gehoert.
            # Das Wasserzeichen des Ports (je Verbraucher) gibt jede Nummer nur EINMAL heraus.
            # Bei rate=1 ist jeder Takt frisch -> unveraendertes Verhalten.
            if not perception.out_ports["object_xy"].frisch_fuer("servo"):
                return xy, 0.0                                 # gehalten: nicht noch einmal ziehen
            return xy, c

        def _d0b_track_log(_inner_ep, phase, tr):
            """Append an agent-visible D0b frame after a real camera track step.

            This is instrumentation only.  It neither changes the track return nor writes an
            outcome into any learner.  The later self-label is constructed offline from valid
            image-space sequences and own hand movement, not here.
            """
            if not D0B_TRACE_JSONL:
                return
            frame = getattr(vc, "_d0b_frame", None)
            if frame is None:
                return
            try:
                h = np.asarray(sim.grasp_pos(), float)
                q = np.asarray(sim.arm_angles_full(), float)
                rec = {"schema": "act23-d0b-fovea-frame-v1", "episode_id": int(_d0b_episode_id),
                       "phase": str(phase),
                       "hand_xyz": [float(x) for x in h],
                       "joint_angles": [float(x) for x in q],
                       "track_confidence": float(tr[1]) if isinstance(tr, tuple) and len(tr) > 1 else 0.0,
                       **frame}
                with open(D0B_TRACE_JSONL, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, sort_keys=True) + "\n")
                if D0B_EVAL_JSONL:
                    # Strictly external evaluation: geometric simulator truth is written only here,
                    # after the agent-visible trace.  It is never returned to the tracker or learner.
                    rest_z = float(snap[body][1])
                    obj = np.asarray(sim.obj_pos(body), float)
                    attached = bool(obj[2] > rest_z + 0.02 and np.linalg.norm(obj[:2] - h[:2]) <= 0.045)
                    ev = {"schema": "act23-d0b-eval-v1", "episode_id": int(_d0b_episode_id),
                          "phase": str(phase), "truth_lifted": bool(obj[2] > rest_z + 0.02),
                          "truth_attached": attached}
                    with open(D0B_EVAL_JSONL, "a", encoding="utf-8") as fh:
                        fh.write(json.dumps(ev, sort_keys=True) + "\n")
            except Exception as _e:
                if os.environ.get("ACT23_DEBUG", "0") == "1":
                    print(f"    [D0b-Trace] uebersprungen: {_e}", flush=True)

        track_fn = _wahrnehmung_ueber_ports
        if a_exec is not None:                                 # SELF: the model's grip + gentle dims
            grip_exec = float(np.clip(a_exec[4], 0.0, 0.45)); gentle_exec = bool(a_exec[5] > 0.5)
        else:                                                  # TEACHER: the old rules, now demonstrations
            grip_exec = 0.3 if u_cmd else None; gentle_exec = u_cmd
        # STAGE 2: "Choreo: Netz" -> the learned runtime policy drives the sub-goals; the reactive
        # teacher LABELS the visited states either way (log_fn on FSM runs = behaviour data, teacher_
        # log_fn on policy runs = true DAgger), so every episode trains the choreography lifelong.
        if state.choreo in ("netz", "attractor") and not runtime.trained:
            print("    [Stufe 2] Choreo-Netz noch nicht trainiert -- FSM fährt", flush=True)
        # STAGE 4a: "Ziel: Latent" -> the committed goal becomes a LATENT (post_goal_fn encodes it
        # once); while the object is carried, place_servo_fn drives the place target by the latent
        # difference to the hand's latent.  Works under FSM AND Netz (the policy state's target
        # follows the servo'd tgt via tgt_eff).  "Ziel: Koord" = both hooks off, classic place.
        use_latent = state.goalmode == "latent"
        pol_trace = []                                         # STEP 3: (state, action) the POLICY drives
        #   this episode -> becomes self-imitation demonstrations IF the agent self-judges a delivery
        _imit_verworfen = [0]

        def _imit_log_frisch(s, out):
            """PUNKT 3 AN DER LERNSTELLE: nur FRISCHE Entscheidungen werden Demonstration.

            run_combined ruft policy_log_fn BEDINGUNGSLOS nach jedem policy_fn (act16:555).  Bei
            ACT23_POLICY_RATE > 1 liefert der subgoal-Port zwischen zwei gerechneten Takten aber
            den GEHALTENEN Wert -- die Selbst-Imitation bekaeme dann einen FRISCHEN Zustand mit
            einer VERALTETEN Aktion gepaart.  Das ist nicht verrauscht, sondern falsch: sie lernte
            "in diesem Zustand tue das, was ich im vorigen entschieden habe".

            Das Wasserzeichen des Ports (Verbraucher "imitation") gibt jede Entscheidungs-Nummer
            genau einmal heraus.  Bei Rate 1 ist jeder Takt frisch -> unveraendertes Verhalten.

            Der REGLER bekommt den gehaltenen Wert weiterhin -- das ist die gewollte Bedeutung
            einer langsamen Entscheidung.  Nur das LERNEN daraus ist unzulaessig.
            """
            if not runtime.out_ports["subgoal"].frisch_fuer("imitation"):
                _imit_verworfen[0] += 1
                return
            pol_trace.append((s.copy(), out.copy()))
        if not D0_FREEZE:
            runtime.begin_episode()                            # pend teacher rows for lifelong DAgger
        #   this episode is NOT a self-validated success (teacher corrects failures, see end_episode)
        # dir_ref wurde ggf. oben aus der gewaehlten AKTION gekippt -- Originalwert sichern und nach
        # der Episode zuruecksetzen, damit die Neigung NUR fuer diesen Griff gilt und nicht dauerhaft
        # in Transport/Ablage und die naechste Episode durchschlaegt.
        _dir_ref_orig = None if not TILT_ACTION else np.array(bm.body.dir_ref, float).copy()
        _T["vor_ausfuehrung"] = _time.perf_counter()           # alles davor = Wahrnehmung + Aktionswahl

        def _policy_ueber_ports(s):
            """ETAPPE 2 des Port-Umbaus: der Regelpfad laeuft ueber die Ports statt ueber einen
            durchgereichten Bound Method (vorher policy_fn=runtime.predict).

            Zustand in policy_state, Modul ueber den ArmAgent takten, Teilziel aus subgoal.
            RuntimePolicyModule.step() existierte bereits fertig und wurde nie gerufen.

            STELLVERTRETEND FUER PUNKT 3: step() setzt subgoal NUR, wenn der Zustand da und die
            Policy trainiert ist -- sonst bliebe der VORIGE Wert im Port stehen und der Aufrufer
            wuerde ihn fuer frisch halten.  Hier kann das nicht eintreten (use_net verlangt
            runtime.trained, und s ist nie None), aber genau diese stille Veralterung ist der
            Grund, warum Punkt 3 Nummer und Frische in den Port legen will.
            """
            runtime.set_in("policy_state", s)
            agent.step(["RuntimePolicy"])
            return runtime.get_out("subgoal")


        # PLANER-TAKT: dieselbe Fallunterscheidung wie zuvor, nur hinter der Rate-Huelle.
        # None bleibt None -- ohne latentes Ziel gibt es keinen Ablage-Servo, und run_combined
        # darf dann auch keine Huelle bekommen, sonst haenge ich ihm ein Verhalten an, das es
        # vorher nicht gab.
        if state.choreo == "attractor":
            _plan_roh = (lambda hxy: lat_attractor.plan_step(
                lgoal.encode_world(hxy), lgoal.get_goal_vector(), hxy)[2])
        elif use_latent:
            _plan_roh = (lambda hxy: lgoal.servo(hxy, gain=0.6))
        else:
            _plan_roh = None
        if _plan_roh is None:
            _plan_ueber_ports = None
        else:
            plan_takt.bind(_plan_roh)

            def _plan_ueber_ports(hxy):
                plan_takt.set_in("arg", hxy)
                agent.step(["PlanTakt"])
                return plan_takt.get_out("ergebnis")

        def _ziel_ueber_ports(c, o, g):
            """Das FESTGELEGTE Ablageziel geht ueber den Port in den Ziel-Servo.

            Frueher rief der Ausfuehrer lgoal.set_goal()/set_goal_vector() direkt ueber eine
            Closure.  Das war die letzte echte Modul-Datenfluss-Kante in der Verdrahtung von
            run_combined -- alles uebrige ist Kommando-Schnittstelle, Konfiguration,
            Protokoll-Abgriff oder eine Projektion eines schon geporteten Werts (geprueft).

            Der Latent-Zweig bleibt AUSSERHALB des Ports: ein Ziel-LATENT hat die Dimension des
            Latentraums, ein Port eine feste.  Auf diesem Pfad ist er ohnehin tot -- state.goal_fn
            liefert marker_xy()[:2], also kommt hier immer ein 2-Vektor an.  Er steht als
            Absicherung fuer andere goal_fn.
            """
            if isinstance(g, np.ndarray) and g.ndim == 1 and len(g) > 2:
                lgoal.set_goal_vector(g)
                return
            lgoal.set_in("goal_xy", g)
            agent.step(["LatentGoal"])

        if ABSTAPELN and state.STUETZEN:
            # STUFE 4, die Aufgabe: die SZENE baut den Stapel, der BEFEHL holt ihn herunter.
            # Ohne das gaebe es nie einen gestapelten Koerper zu adressieren -- die Episode
            # erzeugt ihn sonst erst an ihrem ENDE.
            # Das ist Aufbau, kein Privileg im Steuerpfad: die Adresse muss den Koerper danach
            # selbst FINDEN (s. _auf_etwas_finden), sie bekommt nur eine Welt, in der es
            # ueberhaupt etwas zu finden gibt.
            _st = [n for n in state.STUETZEN if not _geparkt_jetzt(n)]
            if _st:
                _sn = _st[0]
                _sb = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, _sn)
                _so = float(sim.obj_pos(_sn)[2] + sim.m.geom_size[sim.m.body_geomadr[_sb]][2])
                _cb = state.selected()[1]
                _ch = float(sim.m.geom_size[sim.m.body_geomadr[
                    mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, _cb)]][2])
                _vs = np.zeros(2)
                if ABSTAPELN_VERSATZ > 0.0:
                    # AUSSERHALB DER MITTE, Richtung aus crng (s. ABSTAPELN_VERSATZ).  Der
                    # Schwerpunkt bleibt ueber der Platte, solange der Versatz unter ihrer
                    # Halbbreite liegt -- bei 70 mm also bis 35 mm.
                    _wv = float(crng.uniform(0.0, 2.0 * np.pi))
                    _vs = ABSTAPELN_VERSATZ * np.array([np.cos(_wv), np.sin(_wv)])
                sim.set_object(_cb, (sim.obj_pos(_sn)[:2] + _vs).tolist(), z=_so + _ch)
                sim.step(40)                               # setzen lassen, sonst faellt er im Bild
                print(f"  [Abstapeln] {_cb} steht auf {_sn} "
                      f"(Oberkante {1000 * _so:.0f}mm"
                      + (f", {1000 * ABSTAPELN_VERSATZ:.0f}mm neben der Mitte" if ABSTAPELN_VERSATZ > 0 else "")
                      + ") -- Aufgabe: herunterholen", flush=True)
        if SZENE_JE_EPISODE:
            # DER SZENEN-ABDRUCK -- das Messinstrument fuer die Paarung.  Genommen NACH allem, was
            # die Szene festlegt (Objektwahl, Ziel, Neubau, Farben, Abstapel-Aufbau) und VOR der
            # ersten Entscheidung.  Gerundet auf 1 mm und 0,01 rad: MuJoCo ist deterministisch,
            # aber das Setzen einer Lage laeuft durch einen Physikschritt.
            import hashlib as _hl
            _teile = [f"cmd={state.selected()[1]}", f"ziel={state.target_idx}"]
            try:
                _mx = state.marker_xy(state.target_idx)
                _teile.append(f"mk={int(round(1000*_mx[0]))},{int(round(1000*_mx[1]))}")
            except Exception:
                pass
            for _nm in sorted(set(list(scene.keys()) + list(state.STUETZEN))):
                try:
                    _q = sim.obj_pos(_nm)
                    _teile.append(f"{_nm}={int(round(1000*_q[0]))},{int(round(1000*_q[1]))},"
                                  f"{int(round(1000*_q[2]))}")
                except Exception:
                    pass
            for _st in state.STUETZEN:
                try:
                    _bs = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, _st)
                    _teile.append(f"{_st}_h={int(round(2000*sim.m.geom_size[sim.m.body_geomadr[_bs]][2]))}")
                except Exception:
                    pass
            _teile.append("farben=" + ",".join(f"{k}:{v}" for k, v in sorted(colour_of_body.items())))
            _abdruck = _hl.sha1("|".join(_teile).encode()).hexdigest()[:12]
            # AUFGABEN-ABDRUCK: dasselbe OHNE Stuetzen und ohne Farbbindungen -- die Aufgabe
            # (Objekt, Ziel, Objektlagen), wie sie zwischen einem Arm mit und einem ohne Platte
            # gleich sein muss.  Die Farbbindung ist Wahrnehmung und darf von der Platte abhaengen.
            #   GEPARKTE Koerper zaehlen nicht: sie liegen ausserhalb des Bildes auf einem Haufen,
            #   und eine dort geparkte Platte hebt sie an (z 12 -> 19 mm), ohne dass es eine
            #   Aufgabe aendert.
            _aufg = [t for t in _teile if not t.startswith(("sockel", "farben="))
                     and not (("=" in t and "," in t and t.split("=")[0] in scene)
                              and _geparkt_jetzt(t.split("=")[0]))]
            _aufg_h = _hl.sha1("|".join(_aufg).encode()).hexdigest()[:12]
            print(f"  [Szenen-Abdruck] {_abdruck}  cmd={state.selected()[1]} ziel={state.target_idx}"
                  f"  aufgabe={_aufg_h}", flush=True)
            if os.environ.get("ACT23_ABDRUCK_TEXT", "0") == "1":   # Messausgabe: was ging ein
                print("    [Abdruck-Text] " + "|".join(_aufg), flush=True)
        # DER VORBLICK (s. RUECKFALL): einmal wahrnehmen, BEVOR run_combined startet.  Das Ergebnis
        # geht unveraendert an run_combined (dessen perceive_fn liefert es beim ersten Aufruf aus
        # dem Merker).  Mit RUECKFALL=aufgeben endet die Episode hier, wenn nichts gefunden wurde.
        # REGELN NUR IM TRAINING (s. REGELN_NETZ): im Netzbetrieb aus, im Teacher-Betrieb wie
        # eingestellt (ACT16_CLOSE_GUARD / ACT16_REFLEX, Vorgabe an).
        act16.CLOSE_GUARD = _regeln_basis[0] and (REGELN_NETZ or not use_net)
        act16.REFLEX = _regeln_basis[1] and (REGELN_NETZ or not use_net)
        _vorblick["fehlt"] = None
        _vorblick["r"] = perceive(state.cmd_fn(None))
        if RUECKFALL == "aufgeben" and _vorblick["fehlt"] is not None:
            _vorblick["r"] = None
            print(f"    [Nicht gefunden] {body}: kein Versuch, die Episode zaehlt als nicht geliefert "
                  f"({_vorblick['fehlt'][2]})", flush=True)
            return False, float("nan")

        _lk = {"n": 0, "auf": 0, "ruhig": 0, "vor": None, "pose": None, "letzt": None, "quelle": None,
               "k": 0, "aufn": [], "unter": 0, "aufgegeben": None,
               "gv": None, "gv_n": 0, "gv_zu": False}

        def _policy_mit_kopf(s):
            """Netzbetrieb: die Policy entscheidet, der LOSLASS-KOPF entscheidet das Loslassen."""
            out = _policy_ueber_ports(s)
            _lk["letzt"] = np.asarray(s, float).copy()        # letzte Pose (s. LOSLASS_SELBST)
            _lk["k"] += 1
            if GRIFF_SELBST and len(s) > 14:
                # GREIFVERSUCH VERFOLGEN (s. GRIFF_SELBST): Beginn = die Klaue SCHLIESST tatsaechlich
                # (war offen > 0,45, jetzt < 0,27), die Hand steht ueber dem Objekt(glauben).  Erste
                # Fassung begann beim ersten "zu"-Befehl -- der flackert im Anflug, Momentaufnahme
                # 59 mm ueber dem Greifpunkt (Rauchtest 2026-10-06).  Die MOMENTAUFNAHME stammt aus dem
                # letzten Schritt mit noch ganz offener Klaue -- beim Unterschreiten von 0,27 hat sich
                # schon Druck aufgebaut und der Objektglaube ist auf die Hand gesprungen (seitlich
                # 0,0 mm): das waeren Folgen des Griffs, nicht Grundlage der Entscheidung.
                # Ende = getragen (gelungen) oder die Klaue geht wieder auf (misslungen).
                _q, _pr = float(s[8]), float(s[12])
                if _q > 0.45:
                    _lk["gv_zu"] = np.asarray(s, float).copy()   # letzte Pose mit offener Klaue
                if _lk["gv"] is None:
                    _o = _lk["gv_zu"]
                    if (_o is not False and _q < 0.27
                            and float(np.linalg.norm(_o[0:2] - _o[3:5])) < 0.03):
                        _lk["gv_n"] += 1
                        _lk["gv"] = GriffKopf.aspekte(_o, _lk["gv_n"]); _lk["gv_zu"] = False
                else:
                    if _pr > 0.3 and _q < 0.27 and float(s[2]) > 0.04:
                        _griff_merken(_lk, True)
                    elif _q > 0.45:
                        _griff_merken(_lk, False)
            if AUFGEBEN and _lk["k"] % AUFGEBEN_TAKT == 0 and len(s) > 13:
                _a = AufgebenKopf.aspekte(s, _lk["k"])
                _lk["aufn"].append(_a)
                if aufgeben_kopf.bereit and _lk["k"] >= AUFGEBEN_AB and _lk["aufgegeben"] is None:
                    _pa = aufgeben_kopf.p(_a)
                    _lk["unter"] = _lk["unter"] + 1 if _pa < AUFGEBEN_P else 0
                    if _lk["unter"] >= 2:
                        _lk["aufgegeben"] = (_lk["k"], _pa)
                        act16.run_combined._aufgeben = True
            if LOSLASS_KOPF and loslass_kopf.trained:
                # EINRASTEN: der Kopf urteilt nur, solange gehalten wird (Klaue < 0,27).  Ohne
                # Einrasten verstummte er, sobald die Klaue aufging, die Policy sagte wieder "zu",
                # und die Klaue pendelte um 0,27 (Rauchtest 2026-10-05).  Einmal "loslassen" heisst
                # loslassen bis zum Ende der Episode.
                # ERST RUHIG, DANN ENTSCHEIDEN (2026-10-06): im ersten Lauf oeffnete der Kopf am RAND
                # seiner Zone -- mitten im Absenken, Objekt 14-15 mm hoch, 15-43 mm seitlich -- und
                # lieferte 46/100 gegen 54/100.  Jetzt urteilt er erst, wenn die Hand LOSLASS_RUHIG
                # Schritte lang weniger als 1 mm je Schritt bewegt (Propriozeption).  Wohin die Hand
                # faehrt, entscheidet weiter die Policy; OB losgelassen wird, weiter der Kopf.
                _h = np.asarray(s[:3], float)
                _lk["ruhig"] = (_lk["ruhig"] + 1 if _lk["vor"] is not None
                                and float(np.linalg.norm(_h - _lk["vor"])) < 0.001 else 0)
                _lk["vor"] = _h
                if not _lk["auf"] and LoslassKopf.haelt(s) and _lk["ruhig"] >= LOSLASS_RUHIG:
                    # WER ENTSCHEIDET: der Teacher-Kopf SCHLAEGT VOR, wo Loslassen ueberhaupt in Frage
                    # kommt; sobald genug eigene Erfahrung da ist, hat das ERFOLGSNETZ ("klappt
                    # Loslassen hier?") ein VETO.  Erste Fassung liess das Erfolgsnetz ALLEIN
                    # entscheiden: aus 30 guten und 6 schlechten Faellen nahe am Ziel lernte es
                    # pauschal "klappt schon" und liess bei 93 und 54 mm neben dem Ziel los
                    # (Lauf 2026-10-06, 11/30 gegen 18/30) -- es weiss nicht, was es nicht weiss.
                    _eigen = LOSLASS_SELBST and loslass_kopf.erfolg_bereit
                    _ja = loslass_kopf.p(s) > 0.5 and (not _eigen or loslass_kopf.p_erfolg(s) > 0.5)
                    _lk["n"] = _lk["n"] + 1 if _ja else 0
                    if _lk["n"] >= 3:
                        _lk["auf"] = 1; _lk["pose"] = np.asarray(s, float).copy()
                        _lk["quelle"] = "Teacher-Kopf + Erfolgs-Veto" if _eigen else "Teacher-Kopf"
                if _lk["auf"]:
                    out = np.array(out, float).copy(); out[3] = act16.J5_OPEN
            return out

        def _griff_merken(_l, ok):
            _a = _l["gv"]; _l["gv"] = None
            griff_kopf.merken(_a, ok)
            print(f"    [Griff-Versuch] {_l['gv_n']}: seitlich {1000 * _a[0]:.1f} mm, ueber Greifpunkt "
                  f"{1000 * _a[1]:.1f} mm, Klaue {_a[2]:.2f}, Druck {_a[3]:.2f} N, Kurzachse "
                  f"{1000 * _a[4]:.1f} mm, Hoehe {1000 * _a[5]:.1f} mm -> {'GEHALTEN' if ok else 'nicht gehalten'}",
                  flush=True)

        def _perceive_vorblick(cmd):
            _r, _vorblick["r"] = _vorblick["r"], None
            if _r is not None:
                return _r
            # JEDER SPAETERE AUFRUF ist das Wiederfinden mitten in der Episode (run_combined,
            # "stochern", wenn der Servo das Objekt verliert).  Auch dort lieferte der Rueckfall
            # die WAHRE Lage -- ein zweiter Kanal fuer dasselbe Privileg (gemessen 2026-10-03:
            # Arm "aufgeben" bekam so trotzdem die Wahrheit).  Mit RUECKFALL=aufgeben heisst ein
            # gescheitertes Wiederfinden: nichts Neues, die Hand behaelt ihren Glauben.
            _vorblick["fehlt"] = None
            _r = perceive(cmd)
            if RUECKFALL == "aufgeben" and _vorblick["fehlt"] is not None:
                return None, None, None
            return _r
        act16.run_combined(sim, bm.body, panel, CAM, episodes=1, cmd_fixed=state.cmd_fn, force=state.force_fn,
                           goal_fn=state.goal_fn, perceive_fn=_perceive_vorblick, track_fn=track_fn,
                           policy_fn=(_policy_mit_kopf if use_net else None),
                           log_fn=(None if use_net else choreo_log),
                           teacher_log_fn=(choreo_log if use_net else None),
                           policy_log_fn=(_imit_log_frisch if use_net else None),
                           post_goal_fn=_ziel_ueber_ports,
                           #   (seval) needs the episode's goal latent even in "Ziel: Koord" mode
                           place_servo_fn=_plan_ueber_ports,
                           servo=(method in ("color", "shape") or eig_servo),
                           rescatter=False, episode_end_fn=ep_end,
                           ziel_nachsehen_fn=(_ziel_nachsehen if ZIEL_NACHSEHEN else None),
                           objekt_sehen_fn=(_objekt_sehen if OBJ_SEHEN else None),
                           objekt_merken_fn=(_objekt_merken if OBJ_EIG >= 2 else None),
                           lifelong=not D0_FREEZE, carry_gentle=gentle_exec, grip_close=grip_exec, wrist_fn=wf,
                           arm_reset=False, track_log_fn=_d0b_track_log if D0B_TRACE_JSONL else None)
        _T["nach_ausfuehrung"] = _time.perf_counter()
        if _dir_ref_orig is not None:
            bm.body.dir_ref = _dir_ref_orig                    # Neigung galt nur fuer diese Episode
        _save(f"{body}_1after_runcombined")
        if os.environ.get("ACT23_YAW_AB", "0") == "1" and body in ("obj_L", "obj_U", "obj_blue"):
            # measurement companion to [YawAB]: how much the commanded shape ROTATED over the episode
            # (privileged, wrapped to +-180).  On FAILED episodes this is the pure slip-spin signature
            # the user watches in the GUI (diagonal contact torques the L away); on deliveries it also
            # contains the carry.  The offline script pairs it with relwrist/grasp_obj + the outcome.
            dy = (np.degrees(sim.obj_yaw(body) - snap[body][2]) + 180.0) % 360.0 - 180.0
            print(f"    [YawAB-End] {body} dyaw {dy:+.1f}", flush=True)
            # PLACE diagnosis (measurement-only, 2026-07-23): the 746-ep + dose logs showed L place
            # error is GRASP-driven (central+aligned grasp -> median 19mm/70% delivered; off-centre or
            # mirrored -> ~48% gross) EXCEPT a ~5% residual that flings the object 100-285mm despite a
            # perfect grasp -- bimodal = a discrete event (release-flick / lift-whip / skitter off the
            # small table), not gradual place scatter.  Flag those: end position outside the reach area
            # = flung off, so the GUI watcher knows which episodes to inspect for the mechanism.
            _e = sim.obj_pos(body)[:2]
            _rb = [float(os.environ["ACT_REACH_X0"]), float(os.environ["ACT_REACH_X1"]),
                   float(os.environ["ACT_REACH_Y0"]), float(os.environ["ACT_REACH_Y1"])]
            _off = not (_rb[0] - 0.01 <= _e[0] <= _rb[1] + 0.01 and _rb[2] - 0.01 <= _e[1] <= _rb[3] + 0.01)
            _trav = 1000.0 * float(np.linalg.norm(_e - snap[body][0][:2]))
            print(f"    [PlaceAB] {body} Weg {_trav:.0f}mm{'  VON-FLAECHE-GEFLOGEN' if _off else ''}", flush=True)
        _ic = getattr(act16.run_combined, "_inclaw", None)
        if _ic is not None:
            # LAGE IN DER KLAUE beim Zufassen (quer zur Trennachse / tief in Richtung Backen).
            # Prueft die Vermutung aus dem 331-Ep-Lauf: ein naher Nachbar kostet 13 Prozentpunkte
            # Lieferung, OHNE dass der Griff scheitert (100% Kontakt, 100% gehalten) -- sitzt das
            # Objekt dann aussermittig, und wandert dieser Versatz bis zur Ablage durch?
            print(f"    [InKlaue] {body}: quer {_ic[0]:+.0f}mm, tief {_ic[1]:+.0f}mm "
                  f"(0,0 = mittig zwischen den Backen)", flush=True)
        _g = dict(getattr(act16.run_combined, "_grip", {}) or {})
        def _ph(*names):                                       # Mittelwert ueber die genannten Phasen
            v = [x for n in names for x in _g.get(n, [])]
            return (float(np.mean(v)), float(np.min(v))) if v else (0.0, 0.0)
        _close_m, _ = _ph("close", "lower")                    # zufassen
        _lift_m, _lift_lo = _ph("lift")                        # Last uebernehmen
        _carry_m, _carry_lo = _ph("carry")                     # halten
        _rel_m, _ = _ph("place", "release")                    # loesen
        # ABTASTZAHL JE PHASE mitloggen: "tragen 0.00" war bisher nicht von "nicht gemessen" zu
        # unterscheiden -- 87% der Episoden hatten KEINEN Trage-Messpunkt, und ich habe das einmal
        # faelschlich als Trageverlust gelesen.  Mit n je Phase ist der Unterschied im Log sichtbar.
        _cnt = "/".join(f"{n}:{len(_g.get(n, []))}" for n in ("over", "lower", "close", "lift", "carry",
                                                             "place", "release") if _g.get(n))
        print(f"    [Griffdruck] zufassen {_close_m:5.2f} | heben {_lift_m:5.2f} (min {_lift_lo:4.2f})"
              f" | tragen {_carry_m:5.2f} (min {_carry_lo:4.2f}) | loesen {_rel_m:5.2f}  [N]"
              f"  | Messpunkte {_cnt or 'KEINE'}", flush=True)
        if BLICK_LERNEN:
            # DAS ETIKETT FUER DEN BLICK (s. BLICK_LERNEN): wo liegt das Objekt jetzt, GESEHEN, relativ
            # zur Hand beim Loslassen?  Gesucht wird nahe der erwarteten Landestelle; auf etwas
            # abgelegt ("auf") wird nicht gelernt (die Detektion verschmilzt mit der Auflage).
            _bv = _blick_akt["v"]; _blick_akt["v"] = None
            _osb = getattr(act16.run_combined, "_objsicht", None)
            _lob = (_osb or {}).get("los")
            _bzb = state.ziel_bezug
            if (_bv is not None and _lob is not None
                    and not (_bzb is not None and _bzb.get("relation") == "auf")):
                _hl = np.asarray(_lob["hand"], float)[:2]
                _erw = _hl + _bv["o"]
                _sv = sim.d.mocap_pos.copy()
                _dts = shape_clf.perceive_all(sim)
                sim.d.mocap_pos[:] = _sv; mujoco.mj_forward(sim.m, sim.d)
                _kd = [np.asarray(d["pos"], float)[:2] for d in _dts
                       if d.get("pos") is not None and float(d.get("area", 0.0)) >= 100.0
                       and float(np.linalg.norm(np.asarray(d["pos"], float)[:2] - _erw)) < 0.045]
                if _kd:
                    _ps = min(_kd, key=lambda q: float(np.linalg.norm(q - _erw)))
                    _y = _ps - _hl
                    _wahr = np.asarray(sim.obj_pos(body)[:2], float) - _hl   # nur Protokoll
                    _txt = (f"Etikett {1000.0 * float(np.linalg.norm(_y)):.0f}mm (gegen Wahrheit "
                            f"{1000.0 * float(np.linalg.norm(_y - _wahr)):.0f}mm) | Rohblick daneben "
                            f"{1000.0 * float(np.linalg.norm(_bv['o'] - _y)):.0f}mm")
                    if _bv["p"] is not None:
                        _txt += (f" | gelernt daneben {1000.0 * float(np.linalg.norm(np.asarray(_bv['p']) - _y)):.0f}mm"
                                 + (" (benutzt)" if BLICK_LERNEN >= 2 else " (Schatten)"))
                    if not D0_FREEZE:
                        blick_daten.append((_bv["f"].copy(), _y.copy()))
                        del blick_daten[:-BLICK_MAX]
                    print(f"    [Blick-Lernen] {_txt} | {len(blick_daten)} Beispiele", flush=True)
                else:
                    print("    [Blick-Lernen] abgelegtes Objekt nicht gesehen -- kein Etikett", flush=True)
        _obj_ref["chroma"] = None                          # s. OBJ_EIG = 2: gilt nur fuer diese Episode
        _rel = getattr(act16.run_combined, "_release", None)
        _bzl = state.ziel_bezug
        if _bzl is not None and _bzl.get("relation") == "auf" and _bzl.get("aufgeloest"):
            # AUF ETWAS ABGELEGT? -- im LETZTEN gehaltenen Augenblick (s. AUF_LOSLASSEN).  Gemessen
            # privilegiert wie das gewoehnliche Lieferurteil auch; gezaehlt wird es nur mit Schalter,
            # protokolliert immer, damit ein Lauf ohne Schalter dieselbe Frage mitbeantwortet.
            _sbl = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, _bzl["body"])
            _obl = float(sim.obj_pos(_bzl["body"])[2] + sim.m.geom_size[sim.m.body_geomadr[_sbl]][2])
            _hb = float(sim.m.geom_size[sim.m.body_geomadr[
                mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, body)]][2])   # halbe Hoehe
            # OBEN AUF DIESEM KOERPER, nicht bloss hoch: auch seitlich innerhalb seiner groessten
            # Auflage (Platte 35 mm halb) plus Rand -- sonst zaehlte ein Koerper, der auf einem
            # NACHBARN gelandet ist.
            _eo = float(np.linalg.norm(sim.obj_pos(body)[:2] - sim.obj_pos(_bzl["body"])[:2]))
            _oben_jetzt = float(sim.obj_pos(body)[2]) - _hb > _obl - 0.004 and _eo < 0.045
            if _rel is None:
                print(f"    [Ablage auf] {_bzl['body']}: nie angehoben losgelassen -- nicht abgelegt",
                      flush=True)
            else:
                _sl = 1000.0 * float(np.linalg.norm(_rel["cxy"] - _rel["tgt"]))
                _uk = 1000.0 * (_rel["cz"] - _rel["obj_h"] - _obl)   # Unterkante minus Oberkante
                # AUF DEM ZIEL ABGELEGT: beim Loslassen innerhalb der Liefertoleranz in der richtigen
                # Hoehe -- ODER es liegt am Ende oben auf ihm.  Das Zweite gemessen noetig: auf der
                # 70-mm-Platte lagen Koerper stabil oben, die beim Loslassen 25-26 mm neben der Mitte
                # waren, und wurden als "nicht auf dem Ziel" gefuehrt.
                _drauf = (_sl < 1000.0 * act16.TOL and _uk > -4.0) or _oben_jetzt
                _txt = (f"beim Loslassen seitlich {_sl:.0f}mm, Unterkante {_uk:+.0f}mm ueber der "
                        f"Oberkante von {_bzl['body']} -> "
                        + ("AUF DEM ZIEL abgelegt" if _drauf else "nicht auf dem Ziel")
                        + (" | danach: bleibt oben" if _oben_jetzt else
                           " | danach: rutschte ab (verbesserungswuerdig)" if _drauf else ""))
                if AUF_LOSLASSEN and _drauf and not res.get("ok", False):
                    res["ok"] = True
                    _txt += "  => als GELIEFERT gewertet (ACT23_AUF_LOSLASSEN)"
                print(f"    [Ablage auf] {_txt}", flush=True)
        if _rel is not None:
            # ABLAGE-MESSUNG (nur Diagnose): trennt "zu hoch losgelassen" von "seitlich verfehlt".
            # fall  = wie hoch das OBJEKT beim Oeffnen der Klaue noch ueber seiner Ruhelage stand
            # drift = wie weit es sich danach noch bewegt hat (Fallen + Rollen)
            # ab_ziel_beim_Oeffnen = der seitliche Fehler, den die Policy schon VOR dem Loslassen hatte
            _end = np.asarray(sim.obj_pos(body)[:2], float)
            _fall = 1000.0 * max(0.0, _rel["cz"] - _rel["obj_h"])
            _drift = 1000.0 * float(np.linalg.norm(_end - _rel["cxy"]))
            _lat = 1000.0 * float(np.linalg.norm(_rel["cxy"] - _rel["tgt"]))
            _fin = 1000.0 * float(np.linalg.norm(_end - _rel["tgt"]))
            # ZERLEGUNG des seitlichen Fehlers in die KLAUENACHSE (entlang) und quer dazu.  Ein
            # systematischer Anteil ENTLANG waere dieselbe Wurzel wie der Griff-Fehler (der
            # Reichpunkt liegt nicht zwischen den Backen); ein richtungsloser Fehler waere
            # Policy-Ungenauigkeit.  Vorzeichen: + = das Objekt liegt VOR dem Ziel in Klauenrichtung.
            _dec = ""
            _f = _rel.get("fwd")
            if _f is not None and float(np.linalg.norm(_f)) > 1e-9:
                _e = np.asarray(_rel["cxy"], float) - np.asarray(_rel["tgt"], float)
                _u = np.asarray(_f, float) / float(np.linalg.norm(_f))
                _al = 1000.0 * float(_e @ _u)
                _qu = 1000.0 * float(_e @ np.array([-_u[1], _u[0]]))
                _dec = f" | entlang Klaue {_al:+.0f}mm, quer {_qu:+.0f}mm"
                if _rel.get("inclaw") is not None:
                    _dec += (f" | in der Klaue quer {_rel['inclaw'][0]:+.0f}mm, tief {_rel['inclaw'][1]:+.0f}mm"
                             f", Backenmitte {1000.0 * float(np.linalg.norm(_rel['jaw'] - np.asarray(_rel['tgt'], float))):.0f}mm vom Ziel")
                if _rel.get("reach") is not None:
                    _rv = np.asarray(_rel["reach"], float) - np.asarray(_rel["tgt"], float)
                    _ov = np.asarray(_rel["cxy"], float) - np.asarray(_rel["reach"], float)
                    _qv = np.array([-_u[1], _u[0]])
                    _dec += (f" | Reichpunkt-Ziel entlang {1000.0 * float(_rv @ _u):+.0f}mm quer {1000.0 * float(_rv @ _qv):+.0f}mm"
                             f" | Objekt-Reichpunkt entlang {1000.0 * float(_ov @ _u):+.0f}mm quer {1000.0 * float(_ov @ _qv):+.0f}mm"
                             f" | Phase {_rel.get('phase')} {_rel.get('dwell')} Schritte")
            # WARUM EINE ABLAGE DANEBENGEHT -- die zwei Faelle, die in "86 mm daneben" stecken und
            # ohne diese Zeile nicht zu trennen sind (s. wiki/befunde/ziel-als-adresse-gemessen.md):
            #   glaube   |Glaube - Wahrheit| beim Loslassen.  Gross = der Agent hat das getragene
            #            Objekt VERLOREN (Ablenker-Bindung); klein = er wusste, wo es ist.
            #   zumBezug wie weit die WAHRE Ablage vom Bezugskoerper der Zieladresse entfernt ist,
            #            und wie weit der SOLL-Abstand war.  Zieht es das Objekt zum Bezugskoerper
            #            HIN, ist der Nachbar der Magnet; streut es richtungslos, ist es die Bahn.
            _zus = ""
            _oe = getattr(act16.run_combined, "_oeffnen", None)
            if _oe is not None:
                # BEIM ECHTEN OEFFNEN (s. act16 run_combined._oeffnen): wo standen Hand und Objekt, und
                # wie weit ist das Objekt danach noch gerutscht?
                _uo = np.asarray(_oe["fwd"], float); _uo = _uo / (float(np.linalg.norm(_uo)) + 1e-12)
                _qo = np.array([-_uo[1], _uo[0]])
                _ez = np.asarray(_oe["cxy"], float) - np.asarray(_oe["tgt"], float)
                _rz = np.asarray(_oe["reach"], float) - np.asarray(_oe["tgt"], float)
                _zus += (f" | OEFFNEN: Objekt {1000.0 * float(np.linalg.norm(_ez)):.0f}mm vom Ziel "
                         f"(entlang {1000.0 * float(_ez @ _uo):+.0f}, quer {1000.0 * float(_ez @ _qo):+.0f}), "
                         f"{1000.0 * (_oe['cz'] - _oe['obj_h']):.0f}mm hoch, Reichpunkt entlang {1000.0 * float(_rz @ _uo):+.0f} "
                         f"quer {1000.0 * float(_rz @ _qo):+.0f} | danach gerutscht "
                         f"{1000.0 * float(np.linalg.norm(_end - np.asarray(_oe['cxy'], float))):.0f}mm")
            _pr = getattr(act16.run_combined, "_pruef", None)
            if _pr:
                # VOR DEM OEFFNEN HINGESCHAUT (s. act16 PRUEF_TOL): je Blick gesehen/wahr zum Ziel
                _zus += " | Hinschauen: " + "; ".join(
                    ("nicht gesehen" if e["gesehen"] is None else
                     f"gesehen {1000.0 * float(np.linalg.norm(e['gesehen'] - e['tgt'])):.0f}mm"
                     f" (wahr {1000.0 * float(np.linalg.norm(e['wahr'] - e['tgt'])):.0f}mm)")
                    + (" -> nachfuehren" if e["nach"] else " -> oeffnen") for e in _pr)
            _cb = _rel.get("cbel")
            if _cb is not None:
                _zus += f" | Glaube {1000.0 * float(np.linalg.norm(np.asarray(_cb, float) - _rel['cxy'])):.0f}mm"
            _bz = state.ziel_bezug
            if _bz is not None:
                _bp = sim.obj_pos(_bz["body"])[:2]
                if _bz.get("ziel_rel") is not None:
                    # DAS WAHRE ZIEL: wahre Lage des Bezugs plus derselbe Versatz.  Gewertet wird sonst
                    # gegen das WAHRGENOMMENE Ziel -- ein Fehler beim Sehen des Ziels waere unsichtbar.
                    _tw = _bp + np.asarray(_bz["ziel_rel"], float)
                    _zus += (f" | zum WAHREN Ziel {1000.0 * float(np.linalg.norm(_end - _tw)):.0f}mm "
                             f"(Ziel {1000.0 * float(np.linalg.norm(np.asarray(_rel['tgt'], float) - _tw)):.0f}mm "
                             f"daneben gesehen)")
                    _ns = getattr(act16.run_combined, "_nachsehen", None)
                    _os = getattr(act16.run_combined, "_objsicht", None)
                    if _os is not None:
                        _zus += (f" | Objekt in der Hand: wahr {1000.0 * float(np.linalg.norm(_os['wahr'] - _os['hand'])):.0f}mm neben der Hand"
                                 + (" (nicht gesehen)" if _os["gesehen"] is None else
                                    f", gesehen {1000.0 * float(np.linalg.norm(_os['gesehen'] - _os['wahr'])):.0f}mm daneben, "
                                    f"Versatz gesehen {1000.0 * float(np.linalg.norm(_os['gesehen'] - _os['hand'])):.0f}mm, "
                                    f"Richtungsfehler {1000.0 * float(np.linalg.norm((_os['gesehen'] - _os['hand']) - (_os['wahr'] - _os['hand']))):.0f}mm")
                                 + f", Hand {1000.0 * _os['hz']:.0f}mm hoch")
                        _lo = _os.get("los")
                        if _lo is not None:
                            # BEIM LOSLASSEN: steht die Hand auf der Sollstelle, und ist das Objekt
                            # seit dem Blick in der Klaue gewandert?
                            _zus += (f" | beim Loslassen: Hand {1000.0 * float(np.linalg.norm(_lo['hand'] - _lo['zh'])):.0f}mm von der Sollstelle, "
                                     f"Objekt seit dem Blick {1000.0 * float(np.linalg.norm((_lo['wahr'] - _lo['hand']) - (_os['wahr'] - _os['hand']))):.0f}mm in der Klaue gewandert, "
                                     f"{_lo['dwell']} Schritte"
                                     + (f", Luft {_os['luft']['dwell']} Schritte" if "luft" in _os else ""))
                    if _ns is not None:
                        _zus += (" | Nachsehen: " + ("gescheitert" if _ns["neu"] is None else
                                 f"erster Blick {1000.0 * float(np.linalg.norm(_ns['alt'] - _tw)):.0f}mm, "
                                 f"zweiter {1000.0 * float(np.linalg.norm(_ns['neu'] - _tw)):.0f}mm daneben"))
                _zus += (f" | zum Bezug {1000.0 * float(np.linalg.norm(_end - _bp)):.0f}mm"
                         f" (Soll {0.0 if _bz.get('relation') == 'auf' else 1000.0 * ZIEL_ABSTAND:.0f}mm)")
                # HAT DER ARM DEN BEZUGSKOERPER ANGERUEHRT?  Das ist der Trennungstest zwischen den
                # zwei Erklaerungen des gemessenen Mindestabstands (wiki/befunde/mindestabstand-
                # zur-ablage.md): verschiebt sich der Nachbar, ist die KLAUENMECHANIK die Ursache;
                # bleibt er stehen, waehrend der Arm vorher abbricht, ist es die
                # TRAININGSVERTEILUNG (nie ein Ziel naeher als 50 mm, s. ZIEL_SAEUBERN).
                # MUSS HIER STEHEN, nicht spaeter: die Aufraeumschleife unten setzt jeden
                # NICHT-kommandierten Koerper auf seine Pose vor der Episode zurueck -- danach
                # gemessen waere die Verschiebung per Bauart immer null.
                if _bz["body"] in snap:
                    _zus += (f" | Bezug verschoben "
                             f"{1000.0 * float(np.linalg.norm(_bp - snap[_bz['body']][0])):.0f}mm")
                if _bz.get("relation") == "auf" and not _bz.get("aufgeloest"):
                    # DER WURF GELANG, DIE AUFLOESUNG NICHT -- das Ziel war also der MARKER.
                    # Diese Ablage gegen den Sockel zu beurteilen, war der Messfehler des ersten
                    # Stapel-A/B: 6 von 12 "Stapelversuchen" hatten gar nicht auf ihn gezielt.
                    _zus += " | Stapel: NICHT BEURTEILT (Ziel fiel auf den Marker zurueck)"
                elif _bz.get("relation") == "auf":
                    # LIEGT ES DRAUF?  Zwei Groessen, und beide braucht man: die HOEHE sagt, ob es
                    # oben liegt, der seitliche VERSATZ, ob es dort auch halten kann.  Die Auflage
                    # traegt, solange der Schwerpunkt ueber ihr steht -- bei 70 mm Platte und
                    # 24 mm Wuerfel also unter 23 mm Versatz.
                    _sb = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, _bz["body"])
                    _ok_h = float(sim.obj_pos(_bz["body"])[2]
                                  + sim.m.geom_size[sim.m.body_geomadr[_sb]][2])
                    _oz = float(sim.obj_pos(body)[2])
                    _vers = 1000.0 * float(np.linalg.norm(_end - _bp))
                    # URTEIL NACH DER HOEHE, NICHT NACH DEM VERSATZ.  Die erste Fassung verlangte
                    # zusaetzlich Versatz < 23 mm ("vollstaendig auf der Platte") und verwarf damit
                    # Stapel, die bei 27 und 35 mm stabil oben lagen -- die Platte ist 35 mm
                    # halbbreit, die Physik hat laengst entschieden.  Die Schwelle liegt in der Mitte
                    # zwischen Tisch (Mitte 12 mm) und Auflage (Mitte 20 mm).  Der Versatz bleibt als
                    # Messwert stehen, er sagt, wie knapp es war.
                    # AUS DER BERUEHRUNG LERNEN (s. HOEHE_TASTEN).  Das Etikett ist die
                    # Handhoehe beim Aufsetzen minus GRASP_Z -- propriozeptiv, ohne geom_size.
                    # Es faellt hier und nicht bei der Adressierung, weil es die Episode braucht.
                    if not D0_FREEZE and HOEHE_TASTEN and _bz.get("_det_hoehe") is not None:
                        _tst = getattr(act16.run_combined, "_tast", None)
                        _hk = None if _tst is None else _tst.get("hz_kontakt")
                        if _hk is None:
                            print(f"    [Tasten] kein Aufsetzen gefuehlt -- kein Lernbeispiel"
                                  + ("" if _tst is None else
                                     f"  [Ziel {1000*_tst['tgt_z']:.1f}mm, tiefste Hand "
                                     f"{1000*_tst['hz_min']:.1f}mm, {_tst['schritte']} Schritte, "
                                     f"laengster Stillstand {_tst['still_max']}, kleinstes Sinken "
                                     f"{1000*_tst['sink_min']:.2f}mm]"), flush=True)
                        elif not _bz.get("_eins"):
                            print("    [Tasten] Auflage sah belegt aus -- kein Lernbeispiel",
                                  flush=True)
                        else:
                            _ot = float(_hk) - float(act16.GRASP_Z)
                            hoehen_schaetzer.merken(_bz["_det_hoehe"], _ot)
                            print(f"    [Tasten] aufgesetzt bei Handhoehe {1000.0 * _hk:.1f}mm "
                                  f"-> Oberkante ertastet {1000.0 * _ot:.1f}mm, wahr "
                                  f"{1000.0 * _bz['_wahr_oben']:.1f}mm, Abweichung "
                                  f"{1000.0 * (_ot - _bz['_wahr_oben']):+.1f}mm "
                                  f"({len(hoehen_schaetzer.X)} Zeilen)", flush=True)
                            if HOEHE_BELEGT:
                                # NICHT HIER LERNEN, sondern beim naechsten Adressieren: der Arm
                                # steht jetzt ueber der Auflage und verdeckt sie (Rauchtest: 1
                                # von 7 Stapeln erkannt).  Gemerkt wird nur, WAS ertastet wurde.
                                _tast_stand[_bz["body"]] = {
                                    "oben": float(_ot),
                                    "area": (_bz.get("_det_hoehe") or {}).get("area")}
                    _drauf = _oz > _ok_h + 0.008
                    _zus += (f" | Stapel: Objektmitte {1000.0 * _oz:.0f}mm (Auflage "
                             f"{1000.0 * _ok_h:.0f}mm), Versatz {_vers:.0f}mm -> "
                             f"{'LIEGT DRAUF' if _drauf else 'nicht drauf'}")
            print(f"    [Ablage] {body}: beim Oeffnen Objekt {_fall:.0f}mm ueber Ruhelage, "
                  f"seitlich {_lat:.0f}mm vom Ziel -> danach {_drift:.0f}mm gedriftet, "
                  f"final {_fin:.0f}mm{_dec}{_zus}", flush=True)
        _fsv = getattr(vc, "_fsv", None)
        if FOVEA_SERVO != "0" and _fsv and (_fsv["nf"] or _fsv["nd"]):
            # measurement line (shadow AND live): how often the net belief carried the servo vs the
            # detector, and how far apart the two were when both existed
            print(f"    [Fovea-Servo{' Schatten' if FOVEA_SERVO == 'shadow' else ''}] "
                  f"Netz-Obs {_fsv['nf']} / Detektor-Obs {_fsv['nd']} Frames"
                  + (f", |Netz-Detektor| mittel {np.mean(_fsv['d']):.1f} mm, "
                     f"max {np.max(_fsv['d']):.0f} mm" if _fsv["d"] else "")
                  + (f", Farb-Split trug {_fsv['split']} Frames" if _fsv.get("split") else "")
                  + (f", Form-Split trug {_fsv['fsplit']} Frames" if _fsv.get("fsplit") else "")
                  + (f", Kontinuitaet trug {_fsv['kont']} Frames" if _fsv.get("kont") else ""),
                  flush=True)
        if _dbg and FOVEA_NET and getattr(vc, "_fovea_drift", None):   # net-gaze tracking quality + zoom
            d = vc._fovea_drift; zz = getattr(vc, "_fovea_zoom", []) or [1.0]
            print(f"    [Netz-Blick] Drift Blick<->Objekt: mittel {np.mean(d):.1f}px, "
                  f"max {np.max(d):.0f}px | Zoom z {np.min(zz):.2f}..{np.max(zz):.2f} "
                  f"(mittel {np.mean(zz):.2f}) ({len(d)} Frames)", flush=True)
            vc._fovea_drift = []; vc._fovea_zoom = []
        hxy_end = sim.grasp_pos()[:2].copy()  # where the agent's own hand ENDED (~= release point;
        #   the soft release retreats vertically) -- the self-judge's CONTINUITY anchor, proprioceptive
        drive_home()                          # retreat FIRST: restoring an object under the still-lowered arm
        #   could re-create contact under the claw; and the next episode then starts from ~home WITHOUT a reset
        # CONTINUITY + keep the shapes UPRIGHT: leave the COMMANDED object where the action left it (delivered
        # + staying), but put every NON-commanded object back on its pre-command pose.  set_object writes a pure
        # z-rotation, so this also UN-TIPS any shape the arm nudged onto its side (the thin 24mm-tall L/U bars
        # tip easily).  No teleport (OBJS=all5 above), no full reset -- the scene just evolves as you command.
        _set_sizes()
        for nm in snap:                                        # iterate the SNAPSHOT, not state.OBJECTS: the
            #   object list can GROW mid-episode (a GUI click during the run discovers/introduces a new
            #   object -> KeyError on restore, user-hit); anything not snapped simply stays where it is
            if nm != body:
                p, z, yaw = snap[nm]; sim.set_object(nm, p, z=z, yaw=yaw)   # non-commanded: pre-command pose
            else:
                # COMMANDED object: KEEP the delivered position + heading (no position reset -- you pick it by
                # where you SEE it), but stand it UPRIGHT.  A thin, asymmetric L/U gets TORQUED by the claw during
                # the grasp and can end tilted ("a segment snaps/twists") -- set_object writes a pure z-rotation,
                # so this un-tips the delivered shape in place.  Cubes/long are already upright -> a no-op for them.
                # EINE ABLAGE AUF EINER AUFLAGE DARF NICHT "AUFGERAEUMT" WERDEN.  Die Zeile setzte
                # das kommandierte Objekt auf seine RUHEHOEHE VOM EPISODENANFANG zurueck -- gedacht
                # zum Aufstellen gekippter L/U-Formen (set_object schreibt eine reine z-Drehung).
                # Beim Stapeln baut das den Stapel ab, BEVOR der Selbstrichter die Szene sieht: er
                # bekam eine aufgeraeumte Welt vorgelegt und meldete folgerichtig "nichts drauf".
                # Liegt das Objekt HOEHER als seine eigene Ruhehoehe, steht es auf etwas -- dann
                # bleibt die Hoehe.  Ein GEKIPPTES Objekt liegt tiefer, nicht hoeher, also trifft
                # die Regel den Aufstell-Fall nicht.  Ohne Auflage in der Szene gibt es nichts, auf
                # dem ein Koerper nach dem Setzen ruhen koennte -- dort aendert die Zeile nichts.
                cp = sim.obj_pos(nm)[:2].copy()
                _zjetzt = float(sim.obj_pos(nm)[2])
                cz = _zjetzt if _zjetzt > snap[nm][1] + 0.004 else snap[nm][1]
                sim.set_object(nm, cp, z=cz, yaw=sim.obj_yaw(nm))
        mujoco.mj_forward(sim.m, sim.d); state.sync_active()
        # SELF-JUDGEMENT (before the housekeeping below MOVES a flung object -- the judge must see
        # the true outcome scene): the agent's own verdict via its self-labelled classes + the goal
        # latent; agreement with the privileged verdict is tallied per episode.
        saved_mc = sim.d.mocap_pos.copy()
        jdets = shape_clf.perceive_all(sim, wpx=True)      # material px: merged-blob recovery needs them
        sim.d.mocap_pos[:] = saved_mc; mujoco.mj_forward(sim.m, sim.d)
        det0 = getattr(situation_feats, "last_det", None)  # the object's OWN start-of-episode detection:
        s_ok, s_d, s_found = seval.judge(jdets, lgoal, colour_key=colour_of_body.get(body),   # its area is
                                         colours=colours, shape_key=state.SHAPE_KEY.get(body),  # the merge
                                         near_xy=hxy_end, key=body,                             # reference
                                         exp_area=(None if det0 is None else det0.get("area")))
        # DAS STAPEL-SELBSTURTEIL (ACT23_SELBST_STAPEL).  Es tritt NEBEN das gewoehnliche, nicht an
        # seine Stelle: "liegt A auf B" ist eine andere Frage als "ist A am Zielort", und nur die
        # erste ist beim Stapeln die richtige.  Verglichen wird hier gegen das PRIVILEGIERTE Urteil
        # (Objektmitte ueber der Auflage) -- das ist Messung, keine Entscheidungsgrundlage.
        _bz = state.ziel_bezug
        if SELBST_STAPEL and _bz is not None and _bz.get("relation") == "auf" and _bz.get("aufgeloest"):
            _sd, _grund = _selbst_stapel(jdets, _bz, det0)
            _sbid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, _bz["body"])
            _okh = float(sim.obj_pos(_bz["body"])[2] + sim.m.geom_size[sim.m.body_geomadr[_sbid]][2])
            _wahr = float(sim.obj_pos(body)[2]) > _okh + 0.008      # privilegiert, NUR zum Vergleich
            if _sd is None:
                print(f"    [Selbst-Stapel] enthalten -- {_grund}", flush=True)
            else:
                print(f"    [Selbst-Stapel] {'liegt drauf' if _sd else 'nicht drauf'}  "
                      f"{'=' if _sd == _wahr else '!='}  Welt: {'liegt drauf' if _wahr else 'nicht drauf'}"
                      f"   [{_grund}]", flush=True)
        # DAS RICHTUNGS-ETIKETT IM NACHHINEIN (s. RICHTUNG_QUELLE).  Nach jeder Ablage NEBEN einem
        # Bezug -- "an" mit Zufallspeilung ebenso wie "richtung" -- sieht der Agent, wo sein Koerper
        # vom Bezug aus im BILD liegt, und merkt sich die Weltverschiebung unter dem Wort, das er
        # sieht.  Auch eine Fehlablage ist dann ein richtiges Beispiel, nur fuer ein anderes Wort.
        # Alles aus der eigenen Wahrnehmung: Bezug = die Detektion an der aufgeloesten Stelle,
        # Objekt = die Detektion an der Hand beim Loslassen.  Die Weltlage steht nur im Protokoll.
        if _bz is not None and _bz.get("relation") in ("an", "richtung") and _bz.get("aufgeloest"):
            _zr = np.asarray(_bz["ziel_xy"], float)
            _kd = [d for d in jdets if d.get("pos") is not None and d.get("px") is not None]
            _dref = min(_kd, key=lambda d: float(np.linalg.norm(np.asarray(d["pos"], float) - _zr)),
                        default=None)
            if _dref is not None and float(np.linalg.norm(np.asarray(_dref["pos"], float) - _zr)) > 0.04:
                _dref = None
            _dobj = min((d for d in _kd if d is not _dref),
                        key=lambda d: float(np.linalg.norm(np.asarray(d["pos"], float) - hxy_end)),
                        default=None)
            if _dobj is not None and float(np.linalg.norm(np.asarray(_dobj["pos"], float) - hxy_end)) > 0.05:
                _dobj = None
            if _dref is None or _dobj is None:
                print(f"    [Richtung] enthalten -- "
                      f"{'Bezug' if _dref is None else 'eigener Koerper'} nicht gesehen", flush=True)
            else:
                _v = np.asarray(_dobj["pos"], float) - np.asarray(_dref["pos"], float)
                _dist = float(np.linalg.norm(_v))
                _ges = _wort_gesehen(_dobj["px"], _dref["px"])
                _wel = "?"                                 # PRIVILEGIERT, nur zum Vergleich
                if shape_clf.H is not None:
                    _pw = shape_clf._world_to_px(np.vstack([sim.obj_pos(body)[:2],
                                                            sim.obj_pos(_bz["body"])[:2]]))
                    _wel = _wort_gesehen(_pw[0], _pw[1])
                _soll = _bz.get("wort")
                _txt = (f"Soll {_soll}, " if _soll else "") + f"gesehen {_ges} ({1000 * _dist:.0f}mm)"
                _txt += f"  {'=' if _ges == _wel else '!='}  Welt: {_wel}"
                if _soll:
                    _txt += f"  | {'TRIFFT' if _ges == _soll else 'VERFEHLT'} das Wort"
                if not D0_FREEZE and 0.02 <= _dist <= 0.10:
                    wort_bedeutung[_ges].append(_v / _dist)
                    _txt += f"  | gemerkt unter '{_ges}' ({len(wort_bedeutung[_ges])} Beispiele)"
                else:
                    _txt += "  | nicht neben dem Bezug, kein Beispiel"
                print(f"    [Richtung] {_txt}", flush=True)
        if GRIFF_SELBST and _lk["gv"] is not None:
            _griff_merken(_lk, False)                      # Episode endete mitten im Versuch
        # AUFGEBEN AUS DEM EIGENEN ERGEBNIS (s. AUFGEBEN): alle Momentaufnahmen dieser Episode
        # bekommen das Selbst-Urteil -- ausser die Episode wurde aufgegeben (keine Selbstbestaetigung).
        if AUFGEBEN and not D0_FREEZE and s_ok is not None and _lk["aufn"]:
            if _lk["aufgegeben"] is not None:
                print(f"    [Aufgeben] nach {_lk['aufgegeben'][0]} Schritten aufgegeben (erwarteter Erfolg "
                      f"{_lk['aufgegeben'][1]:.2f}) -- Selbst-Urteil "
                      f"{'geliefert' if s_ok else 'nicht geliefert'}; lernt aus dieser Episode NICHT", flush=True)
            else:
                _vor = aufgeben_kopf.bereit
                aufgeben_kopf.merken(_lk["aufn"], bool(s_ok)); aufgeben_kopf.lernen()
                print(f"    [Aufgeben] {len(_lk['aufn'])} Momentaufnahmen -> "
                      f"{'geliefert' if s_ok else 'nicht geliefert'} | Erfahrung {len(aufgeben_kopf.y)} "
                      f"({int(sum(aufgeben_kopf.y))} gut)"
                      + (" -- KOPF ENTSCHEIDET ab jetzt" if aufgeben_kopf.bereit and not _vor else ""), flush=True)
        # LOSLASSEN AUS DEM EIGENEN ERGEBNIS (s. LOSLASS_SELBST): die Pose, in der losgelassen wurde,
        # bekommt das Selbst-Urteil als Etikett.  Nur wenn wirklich getragen wurde: vom Kopf
        # geoeffnet, oder die letzte Pose hielt noch (dann oeffnete die Aufraeumbewegung dort).
        if LOSLASS_SELBST and not D0_FREEZE and s_ok is not None:
            _pose = _lk["pose"] if _lk["pose"] is not None else (
                _lk["letzt"] if _lk["letzt"] is not None and LoslassKopf.haelt(_lk["letzt"]) else None)
            if _pose is not None:
                loslass_kopf.erfolg_merken(_pose, bool(s_ok))
                _bereit_vor = loslass_kopf.erfolg_bereit
                loslass_kopf.erfolg_lernen()
                _ye = np.asarray(loslass_kopf.ye, float)
                _a = LoslassKopf.aspekte(_pose)[0]
                print(f"    [Loslass-Erfolg] losgelassen von {_lk['quelle'] or 'Aufraeumbewegung'} bei "
                      f"{1000 * _a[0]:.0f} mm neben dem Ziel, {1000 * _a[1]:.0f} mm ueber Ablage -> "
                      f"Selbst-Urteil {'geliefert' if s_ok else 'nicht geliefert'} | Erfahrung "
                      f"{len(_ye)} ({int(_ye.sum())} gut)"
                      + (" -- ERFOLGSNETZ hat ab jetzt ein Veto" if loslass_kopf.erfolg_bereit and not _bereit_vor else ""),
                      flush=True)
        if s_ok is None:
            print(f"    [Selbst-Urteil] enthalten -- noch keine eigene Klasse für {body}", flush=True)
        else:
            tally = seval.record(s_ok, res.get("ok", False)) if not D0_FREEZE else "eingefroren"
            ref = (seval._last or {}).get("ref_mm", 0.0)   # self-calibrated perception radius applied
            refs = f", Ref-Korrektur {ref:.0f}mm" if ref >= 1.0 else ""
            if (seval._last or {}).get("merged"):
                refs += ", Blob-Verschmelzung erkannt"     # judged on MY material at the hand, not the fused centroid
            verdict = (f"geliefert ({s_d * 1000:.0f}mm vom Wunsch{refs})" if s_ok
                       else (f"nicht geliefert ({s_d * 1000:.0f}mm vom Wunsch{refs})" if s_found
                             else "nicht geliefert (Objekt nicht am Loslass-Punkt gesehen)"))
            wv = "geliefert" if res.get("ok", False) else "nicht geliefert"
            mark = "=" if bool(s_ok) == bool(res.get("ok", False)) else "!="
            print(f"    [Selbst-Urteil] {verdict}  {mark}  Welt: {wv}  (Übereinstimmung {tally})",
                  flush=True)
            if mark == "!=" and os.environ.get("ACT23_DEBUG", "0") == "1":
                le = seval._last
                print(f"      [su-dbg] hand={np.round(hxy_end,3).tolist()} obj_true="
                      f"{np.round(sim.obj_pos(body)[:2],3).tolist()} strict={le.get('n_strict')} "
                      f"cands={le.get('n_cands')} cand_pos={le.get('cand_pos')}", flush=True)
        # ETAPPE 2 (Latent Dynamics): observe THIS episode's latent transition -- the object moved from
        # its start pose to its end pose under the executed action -- and train the transition model.
        # BUGFIX 2026-07-24: the previous code used an undefined name `action` (the action is `a_exec`)
        # inside a bare `except: pass`, so it raised a NameError EVERY episode and trained NOTHING for
        # the whole 314-ep run (the [Latent-Dynamics] line never printed).  Now: real (z_start, a_exec,
        # z_end) transition, skip teacher episodes (a_exec None), and errors are LOGGED not swallowed.
        # NOTE: this is an EPISODE-LEVEL transition (one per episode), not per-step -- coarse but honest;
        # a_exec is the 6-dim world-model action (the dynamics module truncates to its action_dim).
        if a_exec is not None and not D0_FREEZE:
            try:
                _a_dyn = np.asarray(a_exec, float)
                z_start_dyn = lgoal.encode_world(snap[body][0][:2])
                z_end_dyn = lgoal.encode_world(sim.obj_pos(body)[:2])
                lat_dyn.observe(z_start_dyn, _a_dyn, z_end_dyn)
                surp = lat_dyn.predict_surprise(z_start_dyn, _a_dyn, z_end_dyn)
                loss_d = lat_dyn.train(epochs=5)
                if os.environ.get("ACT23_YAW_AB", "0") == "1":
                    print(f"    [Latent-Dynamics] Übergang beobachtet -> Surprise S={surp:.3f} | "
                          f"MSE={loss_d:.5f} | Puffer {len(lat_dyn.buffer_z)}", flush=True)
            except Exception as e:
                print(f"    [Latent-Dynamics] FEHLER: {type(e).__name__}: {e}", flush=True)
        # SCENE housekeeping (user-observed degeneration over long auto runs): an object DRAGGED outside
        # the reachable workspace by a failed grasp stays out FOREVER (the restore puts non-commanded
        # objects back on their pre-command = out pose; a commanded one keeps its end pose) -- every
        # later reach toward it is unreachable and SWEEPS through the scene ("the arm lifts some
        # unmarked object and throws it").  Return such objects to a free slot: ENVIRONMENT tidying
        # between episodes (the bounded act23 heir of act16's reposition_strays), not an agent rule.
        for _l2, nm, _m2 in state.OBJECTS:
            if _geparkt_jetzt(nm):
                continue                                       # ABSICHTLICH geparkt (ACT23_SCENE_N) --
                #   die Aufraeumroutine darf es nicht auf den Tisch zurueckholen, sonst waere die
                #   kleinere Szene nach einer Episode wieder voll (im Rauchtest genau so passiert)
            p = sim.obj_pos(nm)[:2]
            if abs(p[0]) <= 0.135 and 0.055 <= p[1] <= 0.265:
                continue                                       # inside (generous bounds: a legit delivery can
                #   rest tolerance-width past a top target -- CONTINUITY, only truly-LOST objects return)
            occ = [sim.obj_pos(o)[:2] for _l3, o, _m3 in state.OBJECTS
                   if o != nm and not _geparkt_jetzt(o)]
            free = [s for s in SLOTS
                    if all(float(np.linalg.norm(np.asarray(s) - q)) > 0.055 for q in occ)]
            if not free:
                continue
            s = max(free, key=lambda sl: min(float(np.linalg.norm(np.asarray(sl) - q)) for q in occ))
            zr = scene.get(nm, (None, _hoehe.get(nm, 0.012), 0.0))[1]
            sim.set_object(nm, np.asarray(s, float) + crng.uniform(-0.003, 0.003, 2), z=zr,
                           yaw=float(crng.uniform(0, 2 * np.pi)))
            print(f"    [Szene] {nm} lag außerhalb des Arbeitsbereichs — zurück auf einen freien Platz",
                  flush=True)
        mujoco.mj_forward(sim.m, sim.d)
        if panel is not None and vc.viz is not None:           # refresh the hex "overview Kamera (Fovea)" with
            try:                                               #   the RESTORED scene (it last rendered a pre-
                vc.viz.update(sim.render(CAM), "Szene aktualisiert")   # restore frame -> stale layout); a plain
            except Exception:                                  #   image refresh -- no colour-keyed track step
                pass                                           #   that would walk the gaze off the final view
        _streuung(body, snap.get(body, (None,))[0], _lift_m)
        _eig_nachfuehren(body, method, hxy_end, _lift_m)       # dieselbe Handlungs-Identitaet   # zuerst die selbst getragene Sichtung
        #   einspeisen, DANN der Blick -- so profitiert er schon von der breiteren Klasse
        open_set_glance()                  # lifelong OPEN-SET look at the settled scene: young self-labelled
        #   classes keep growing exemplars over the new poses; an undiscovered novel object keeps feeding
        #   the buffer (discovery can also happen HERE, not only at "Objekt hinzufügen")
        if _dbg:
            print(f"    [dbg] after ep : {_pos()}", flush=True)
            hs = {nm: np.round(sim.m.geom_size[sim.m.body_geomadr[mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)]] * 1000, 1).tolist()
                  for nm in ("obj_L", "obj_U", "obj_T")}   # the exact failure mode: a resized first geom
            print(f"    [dbg] L/U/T half : {hs}  (XML: L [7,28,12] U [7,14,12] T [21,7,12])", flush=True)
        _save(f"{body}_2after_restore")
        # LIFELONG loop (EVERY object): every command IS a trial for the world model (situation -> action
        # -> outcome).  STEP 2 (prediction-checkpoint CREDIT ROUTING, user's self-improvement plan): the
        # crude "learn only in FSM mode" gate is replaced by TWO self-measured checkpoints that decide
        # WHOSE decision failed, so the world model learns in the NORMAL (Netz) mode too -- from the
        # episodes where its OWN decision (the grasp: wrist/offset/grip/gentle) was actually put to the
        # test.  The four cases (poisoning fix, now precise):
        #   - NOT lifted            -> the grasp never happened: the POLICY/choreography missed -> ABSTAIN.
        #   - lifted + delivered    -> the grasp+carry worked -> world model +1 SUCCESS.
        #   - lifted + SLIPPED      -> the grip lost the object mid-carry -> world model +1 FAILURE.
        #   - lifted, held, off-goal-> the place AIM was wrong though the grip held -> POLICY -> ABSTAIN.
        # The outcome label is the agent's OWN verdict (step 1 SelfEval) -> fully self-supervised.
        # ACT23_WORLD_LABEL=welt forces the privileged label; ACT23_CREDIT=0 restores the FSM-only gate.
        maxcz = float(getattr(act16.run_combined, "_maxcz", 0.0))
        slipped = bool(getattr(act16.run_combined, "_slipped", False))
        rest_z = float(snap[body][1]) if body in snap else 0.012
        lifted = maxcz > rest_z + 0.02                          # object clearly left the table = grasp tested
        imit_tol = float(os.environ.get("ACT23_IMIT_TOL", "0.015"))
        # ASYMMETRIC confidence bars (user request 2026-07-18; measured on the 415-ep session log):
        # the judge's DISTANCE estimate is nearly unbiased (median |self-true| 0-3mm) but a single
        # 15mm bar discarded 48% of TRUE deliveries (77/159) -- exactly the "sieht fuer mich OK
        # abgelegt aus, Log sagt unsicher" episodes the user watched.  In the 15-25mm band the
        # judge's "geliefert" is right 85-100% per object EXCEPT the U, so:  WORLD-MODEL success
        # label accepts up to ACT23_WORLD_TOL (25mm; the ensemble tolerates the ~13% label noise,
        # and positives were the measured yield bottleneck), SELF-IMITATION keeps the strict
        # imit_tol bar (an imitated failure poisons the policy directly), and the U keeps the strict
        # bar for BOTH.  The U band was briefly un-clamped after the 32mm slot (498-ep run showed
        # 92%, 12/13) but that did NOT replicate: the 746-ep run 2026-07-21 measured 54% (7/13,
        # pooled 73%) with 6 false-positive success labels leaking in -- U's blob still merges with
        # the claw, and U's bottleneck is mechanical (5 dose runs), not the action, so extra U
        # labels have low value.  Clamp re-instated.
        world_tol = float(os.environ.get("ACT23_WORLD_TOL", "0.025"))
        if body == "obj_U":
            # U was clamped to imit_tol (15mm) after the 746-run's 6 false-positives (U blob merges with
            # the claw).  But the U-densegrasp fix (2026-07-24) delivers the U FLAT at ~18-20mm -- real wins
            # (self==Welt) that the 15mm bar discarded, starving the world model of exactly the grasps the
            # fix enabled.  User decision: loosen the WORLD-MODEL bar to 22mm to credit them (the ensemble
            # tolerates the noise); SELF-IMITATION keeps the strict 15mm imit_tol below (a borderline U grip
            # must not be imitated straight into the policy).  FP risk re-opened -> WATCH the next full run.
            world_tol = float(os.environ.get("ACT23_U_WORLD_TOL", "0.022"))
        if os.environ.get("ACT23_WORLD_LABEL", "selbst") == "welt" or s_ok is None:
            delivered = bool(res.get("ok", False)); confident = delivered; lbl_src = "Welt"
            world_conf = delivered
        else:                                                   # self-judged (step 1) -> self-supervised
            delivered = bool(s_ok)
            confident = delivered and s_d is not None and s_d < imit_tol
            world_conf = delivered and s_d is not None and s_d < world_tol
            lbl_src = "Selbst"
        attempted = bool(getattr(act16.run_combined, "_attempted", False))
        # the attempted-failure route only under the RELIABLE (FSM) choreography: there a close at
        # the object that never lifts isolates the ACTION's grasp geometry (wrist/grip).  Under the
        # LEARNED choreography the same signal is AMBIGUOUS -- the policy grazes the object and
        # closes at the wrong moment, and the wrist gets the blame.  MEASURED in the user's live
        # netz run: ~38 failure labels in 120 eps flooded the world model (798->886, mostly
        # negative), ensemble sigma inflated 0.5-0.9 -> 0.9-1.6, LCB wrist choice churned
        # (user-observed diagonal grips) and the Bilanz slid 18/30 -> 10/30 -- the fd6e526
        # poisoning symptom through a physically-gated door.  Ambiguity -> abstain (the credit
        # principle); ACT23_ATTEMPT_NETZ=1 re-enables for experiments.
        # FEHLGRIFF-LABEL UNTER NETZ, ABER GEDAEMPFT (2026-07-27).  Messung 610-Ep-Lauf: das Welt-Modell
        # sieht 36% der Episoden (220 Fehlgriffe) GAR NICHT, weil sie hier abstrahiert werden -- und lernt
        # die Ausrichtungs-Regel dadurch VERKEHRT (Puffer: schraeg Label 0.813 vs ausgerichtet 0.768,
        # waehrend die Realitaet 17% vs 35% Lieferung sagt).  Die Information sitzt NICHT in einer
        # Teilmenge: geschobene und unberuehrte Fehlgriffe sind gleich schraeg (34% vs 32%, p=1.0), aber
        # BEIDE liegen bei ~33% gegen nur 15% bei den Erfolgen -- die Fehlgriffe als GANZES tragen sie.
        # Das historische Problem beim Einschalten war nicht Falschheit, sondern FLUT: ~38 fast durchweg
        # negative Labels blaehten Sigma 0.5-0.9 -> 0.9-1.6 und liessen die LCB-Wahl flattern.  Deshalb
        # kommt das Label jetzt mit GEWICHT ACT23_FAIL_W (default 0.3) statt gar nicht: das Signal ist da,
        # die unsichere Kausalzuordnung (Anfahrt vs Griffgeometrie) steckt im Gewicht.  ACT23_FAIL_W=0
        # schaltet es faktisch ab, ACT23_ATTEMPT_NETZ=1 gibt volles Gewicht (altes Experiment).
        obs_w = 1.0                                    # fit weight of THIS episode's world-model row
        # SENSOR-BELEGTER GRIFF-FEHLSCHLAG (Fingerdruck-Streifen).  Gemessen (50 Ep): wenn der Druck
        # waehrend des HEBENS durchgehend 0 bleibt UND beim Zufassen unter 1 N lag, hat die Klaue das
        # Objekt nie gehalten -- in 92% der Faelle folgt daraus kein Erfolg.  Das ist ein KAUSAL
        # EINDEUTIGES Negativ fuer die AKTION: es haengt nur am Griff, nicht an Transport, Ablage oder
        # einem Nachbarobjekt.  Genau die Eindeutigkeit, die dem attempted-Label fehlt (dort musste die
        # unsichere Zuordnung ueber ein Gewicht von 0.3 abgefedert werden) -- hier gibt es volles
        # Gewicht.  `not delivered` als Schutz: eine Episode, die trotz Druckeinbruch liefert (kurzes
        # Nachfassen), darf kein Negativ bekommen.  ACT23_GRIPLABEL=0 schaltet es ab.
        _grip_lost = (os.environ.get("ACT23_GRIPLABEL", "1") != "0"
                      and bool(_g)                       # Sensor hat ueberhaupt gemessen
                      and _lift_m < 0.01 and _close_m < 1.0)   # oben aus run_combined._grip gelesen
        # 423-Ep-Lauf ausgewertet (2026-07-28) -- und meine erste Bewertung KORRIGIERT.
        # Ich hatte das Label fuer schaedlich erklaert (Ausrichtungs-Praeferenz -0.010 -> +0.017,
        # Sigma 0.297 -> 0.395) und dabei gegen ein BACKUP verglichen, das sich nicht nur um die 86
        # Fehlgriff-Zeilen unterscheidet, sondern um 264 neue Zeilen des Laufs -- die ~178
        # zusaetzlichen ERFOLGS-Zeilen verschoben die Praeferenz, nicht das Label.  Der saubere Test
        # (derselbe Zustand, gleicher Fit-Seed, NUR die 86 Zeilen variiert, beide frisch trainiert):
        #   ohne die Zeilen  schraeg-Praeferenz +0.060, Sigma 0.155
        #   mit  den Zeilen  schraeg-Praeferenz +0.001, Sigma 0.140
        # Das Label VERBESSERT die Ausrichtungs-Bewertung also und senkt Sigma leicht -- der User
        # hatte mit seinem Eindruck recht ("die Ausrichtung sieht nicht mehr so zufaellig aus").
        # OFFEN und NICHT dem Label zuzuordnen: die Lieferrate fiel im Lauf 47% -> 35% (nicht durch
        # die Curiosity-Zuteilung erklaert) und die L-Form von 52% auf 13% (n=15).  Ursache ungeklaert;
        # ein Kandidat ist die graduelle Imitation (23% der 12000 Demos stammen aus Ablagen, die
        # frueher verworfen worden waeren, mit 15% der Fit-Zugkraft).  LEHRE: einen Label-Effekt NUR
        # gegen denselben Datensatz messen, nie gegen einen mitgewachsenen Backup-Stand.
        fail_w = float(os.environ.get("ACT23_FAIL_W", "0.3"))
        att_full = (not use_net) or os.environ.get("ACT23_ATTEMPT_NETZ", "0") == "1"
        att_ok = att_full or fail_w > 0.0
        if os.environ.get("ACT23_CREDIT", "1") == "1":
            if _grip_lost and not delivered:
                # der Streifen BELEGT, dass die Klaue nie gehalten hat -> Aktion war schlecht
                route, outcome = "Griff hielt nicht (Drucksensor)", False
                obs_w = 1.0
            elif not lifted and attempted and not delivered and att_ok:
                # the claw CLOSED at the object and it never rose: the choreography ARRIVED, the
                # ACTION's grasp geometry (wrist/grip) failed -> the action gets a FAILURE label.
                # Without this route a grasp-PREVENTING wrist was unfalsifiable (always "nicht
                # gegriffen" -> abstain) and the world model froze on it (L-Form wrist-112 deadlock).
                # `not delivered` guard (measured): a never-lifted episode can still SHOVE the object
                # onto the goal -- that must not label the action a failure (abstain below instead).
                route, outcome = "Griff am Objekt fehlgeschlagen (Aktion)", False
                obs_w = 1.0 if att_full else fail_w     # gedaempft, solange die Zuordnung unsicher ist
            elif world_conf and os.environ.get("ACT23_CREDIT_FLAT", "1") != "0":
                # A CONFIDENT delivery (self-judge <world_tol; U=15mm) is a SUCCESS even when the object
                # never rose >20mm.  The U-densegrasp A/B (2026-07-24) exposed this: the base grip carries
                # the U FLAT to the goal (dyaw +-30-60, PlaceAB Weg ~65mm), delivering ~20mm WITHOUT tripping
                # the lift gate -> the old "elif not lifted -> abstain" discarded the win (12 of 25 on-arm
                # deliveries), starving the world model of exactly the grasps the fix enabled.  Guarded by
                # world_conf (a shove-to-goal rarely lands <15mm) + reversible (ACT23_CREDIT_FLAT=0).
                route, outcome = "sicher geliefert", True
            elif not lifted:
                route, outcome = "nicht gegriffen (Policy)", None
            elif world_conf:
                route, outcome = "sicher geliefert", True
            elif slipped:
                route, outcome = "verrutscht (Griff)", False
            elif delivered:                                     # judged delivered but NOT confident ->
                route, outcome = "unsichere Lieferung", None    #   don't credit the action either way
            else:
                route, outcome = "daneben platziert (Policy)", None
        else:                                                   # old gate: FSM only, privileged label
            outcome = bool(res.get("ok", False)) if not use_net else None
            route = "FSM" if not use_net else "Netz (aus)"
        if D0_EPISODE_JSONL and fe is not None and a_exec is not None:
            # The action trace is deliberately independent of credit eligibility.  A policy
            # abstention is no world-model training data, but it remains an executed wrist choice
            # and therefore belongs in the D0 before/after metric.
            _yaw_trace = 0.5 * np.arctan2(float(fe[3]), float(fe[2]))
            _rel_trace = abs((np.degrees(wrist_of(a_exec) - _yaw_trace) + 90.0) % 180.0 - 90.0)
            _d0_append_credit(D0_EPISODE_JSONL, {
                "schema": "act23-d0-episode-v1", "body": body, "action_source": "Selbst",
                "label_source": lbl_src, "route": route, "credit_outcome": outcome,
                "self_delivered": bool(delivered), "world_delivered": bool(res.get("ok", False)),
                "self_found": bool(s_found), "frozen": bool(EXV_FREEZE or D0_FREEZE),
                "wrist_deg": float(np.degrees(wrist_of(a_exec)) % 180.0),
                "relative_wrist_deg": float(_rel_trace), "grip": float(a_exec[4]),
                "gentle": bool(a_exec[5] > 0.5), "self_distance_m": s_d,
            })
        if fe is not None and outcome is not None:
            if a_exec is not None:
                a_obs, src = a_exec, "Selbst"
            else:
                w_obs = getattr(act16.run_combined, "_wrist_tgt", None)
                a_obs = None if w_obs is None else action_vec(
                    0.0, 0.0, float(w_obs), grip=(0.3 if u_cmd else 0.0), gentle=float(u_cmd))
                src = "Teacher"
            if a_obs is not None:
                # GRADED: pass the SELF-JUDGED distance so a success is scored by how well it landed
                # (world_model.quality) instead of a flat 1.0.  Only when the agent judged it itself --
                # under ACT23_WORLD_LABEL=welt there is no self-distance and the label stays binary.
                _qd = s_d if (lbl_src == "Selbst" and s_d is not None) else None
                _we = WORLD_EPOCHS               # bleibt so, wenn das Lernen eingefroren ist
                _naug = 0                        # auch bei eingefrorenem Lernen definiert
                if not EXV_FREEZE and not D0_FREEZE:
                    # PUNKT 3, GEPRUEFT UND NICHT NOETIG: diese Paarung ist von den logischen
                    # Raten unberuehrt.  `fe` entsteht in situation_feats VOR run_combined (also
                    # ausserhalb des Bild-Takts), `a_obs` ist die EINE Wahl dieser Episode
                    # (world.rate bleibt 1, das Modul wird genau einmal getaktet) und `outcome`
                    # das Episodenergebnis.  Kein Wert kann hier gehalten sein.  Bewusst KEINE
                    # Wache: eine Wache gegen ein Phantom taeuscht Sicherheit vor und verdeckt,
                    # wo die echte Gefahr sitzt (das war die Selbst-Imitation, s. _imit_log_frisch).
                    # WER world.rate > 1 SETZT, muss hier zuerst hinsehen.
                    world.observe(fe, a_obs, outcome, dist=_qd, weight=obs_w, group=group_id())
                    if AUGMENT:
                        # VORGESTELLTE LAGEN aus derselben Erfahrung (s. `augmentiere`).
                        # DIESELBE GRUPPE wie das Original -- das ist kein Detail: `_groups`
                        # entscheidet, welche Zeilen beim Bootstrap und beim Halteteil ZUSAMMEN
                        # bleiben.  Mit eigener Gruppe landete eine Vorstellung im Testteil, waehrend
                        # ihr Original trainiert -- die Guete waere dann Selbstbetrug (Messhygiene:
                        # "Halteteile nie zufaellig ziehen").
                        # OB EIN FEHLSCHLAG UEBERTRAGEN WERDEN DARF, entscheidet die Kredit-
                        # Zuordnung bereits: was hier ankommt, ist ursaechlich zugeordnet
                        # ("Griff hielt nicht (Drucksensor)", "verrutscht"), waehrend "daneben
                        # platziert" und "nicht gegriffen" gar nicht erst durchkommen (outcome=None).
                        # Die Forderung der Idee-Seite -- ein Negativ nur so weit uebertragen, wie
                        # seine Ursache erklaert ist -- ist damit schon erfuellt, bevor hier
                        # augmentiert wird.
                        for _fa in augmentiere(fe, shape_clf.NH, AUGMENT, crng):
                            world.observe(_fa, a_obs, outcome, dist=_qd, weight=obs_w,
                                          group=group_id())
                            _naug += 1
                    _we = welt_fit_epochen()      # Plan s.o.; Vorgabe 600 wie bisher
                    world.train(epochs=_we)
                _qs = ("" if (_qd is None or not outcome)
                       else f", Guete {wm_quality(_qd):.2f} bei {_qd*1000:.0f}mm")
                if AUGMENT and _naug:
                    _qs += f", +{_naug} vorgestellt"   # muss im Protokoll erkennbar sein, sonst
                    #   ist der Anteil vorgestellter Zeilen hinterher nicht auszaehlbar
                if _we != WORLD_EPOCHS:
                    _qs += f", Fit {_we} Epochen"   # der kurze Fit muss im Log ERKENNBAR sein,
                                                    #   sonst ist er in keiner Auswertung trennbar
                if obs_w != 1.0:
                    _qs += f", Gewicht {obs_w:.2f}"
                print(f"    [Kredit] {route} -> Welt-Modell "
                      f"{'EINGEFROREN (EXV)' if EXV_FREEZE else '+1'} ({src}, Label {lbl_src}: Wrist "
                      f"{np.degrees(wrist_of(a_obs)) % 180.0:.0f} Grad, Grip {a_obs[4]:.2f}"
                      f"{', sanft' if a_obs[5] > 0.5 else ''}, "
                      f"{'geliefert' if outcome else 'nicht geliefert'}{_qs}) -> {world.n()} Versuche",
                      flush=True)
                if D0_CREDIT_JSONL:
                    _yaw = 0.5 * np.arctan2(float(fe[3]), float(fe[2]))
                    _rel = abs((np.degrees(wrist_of(a_obs) - _yaw) + 90.0) % 180.0 - 90.0)
                    _d0_append_credit(D0_CREDIT_JSONL, {
                        "body": body, "action_source": src, "label_source": lbl_src,
                        "route": route, "outcome": bool(outcome), "weight": float(obs_w),
                        "frozen": bool(EXV_FREEZE or D0_FREEZE), "world_rows": int(world.n()),
                        "wrist_deg": float(np.degrees(wrist_of(a_obs)) % 180.0),
                        "relative_wrist_deg": float(_rel), "grip": float(a_obs[4]),
                        "gentle": bool(a_obs[5] > 0.5), "self_distance_m": _qd,
                    })
        elif fe is not None:
            print(f"    [Kredit] {route} -- Welt-Modell enthält sich (Aktion nicht schuld)", flush=True)
        # STEP 3: SELF-IMITATION GATE.  On a Netz episode the POLICY drove; if the agent self-judges a
        # CONFIDENT delivery (the STRICT imit_tol bar -- deliberately tighter than the world-model's
        # world_tol since the asymmetric split, + not-slipped) the
        # (state, action) pairs the policy actually took become its OWN demonstrations, reinforcing what
        # worked FOR IT (blended with DAgger at fit time).  A skipped real success just loses a sample;
        # an imitated failure would poison -- hence the tight bar.  ACT23_SELFIMIT=0 disables.
        # GRADED (user's idea): the flat imit_tol bar discarded 11 of 43 genuine hits (<=25mm) in the
        # 120-ep log.  Graded, a demo no longer has to be all-or-nothing -- it enters with a WEIGHT
        # (world_model.quality: 5mm ~0.96, 15mm 0.70, 24mm ~0.40), so a merely-ok placement pulls the
        # policy proportionally less instead of being thrown away.  The admission bar widens to
        # ACT23_IMIT_BAR (25mm).  ACT23_IMIT_GRADED=0 restores the flat imit_tol gate.
        _gimit = os.environ.get("ACT23_IMIT_GRADED", "1") != "0"
        imit_bar = float(os.environ.get("ACT23_IMIT_BAR", "0.025")) if _gimit else imit_tol
        # KNAPPE FEHLSCHLAEGE MIT AUFNEHMEN (2026-09-01).  BEFUND: `delivered` ist ein BINAERES Tor
        # vor einer bereits GRADUIERTEN Guete.  quality(d)=exp(-(d/0.025)^2) ist glatt --
        # 24mm -> 0,398, 26mm -> 0,339 -- aber die Behandlung war eine Klippe: 0,398 gegen NULL.
        # Die 25 mm sind die LIEFERTOLERANZ, also eine Konvention dafuer, was als geliefert ZAEHLT;
        # sie hatte keinen Grund, auch zu bestimmen, woraus GELERNT wird.  Gemessen an einem
        # 1053-Ep-Lauf: 198 Episoden ("daneben platziert") fielen so heraus, obwohl sie GETRAGEN
        # hatten -- Tragedruck 4,61 N gegen 4,86 N bei den Lieferungen, Freigabehoehe und
        # Oeffnungsabstand identisch.  Sie sind der Schwanz derselben Verteilung, kein eigener Fall.
        #
        # DREI WACHEN, damit daraus kein Freibrief wird:
        #  * nur bei GRADUIERTER Imitation (_gimit).  Ohne sie ist das Gewicht flach 1.0 -- einen
        #    Fehlschlag mit vollem Gewicht zu imitieren waere offensichtlich falsch.
        #  * eigene, weitere Schranke ACT23_IMIT_FAIL_BAR.  Ueber 45 mm aendert sie ohnehin nichts
        #    mehr (gemessen: Gewichtssumme +31,4 bei 45 mm gegen +31,8 ohne jede Schranke).
        #  * `lifted and not slipped` bleiben unveraendert stehen -- nur wirklich GETRAGENE
        #    Episoden kommen ueberhaupt in Frage.
        # ERWARTETE GROESSE, vorab: +8,5% Gewicht im Selbst-Puffer.  Die Gaussglocke daempft die
        # 198 von selbst; sie sind 19% der EPISODEN, aber nur 8,5% des GEWICHTS.  ACT23_IMIT_FAIL=0
        # stellt das alte Verhalten her.
        # VORGABE AUS (2026-09-01, nach dem A/B).  GEMESSEN, je 250 Ep, identischer Startzustand:
        # Mechanismus feuert (37x "knapp daneben" gegen 0), aber KEIN Endpunkt zeigt Nutzen --
        # Endabstand 18,0 -> 17,0 mm (p=0,57), Lieferquote 56,8 -> 54,8% (p=0,72) -- und die vorab
        # benannte REGRESSIONSWACHE ging in die falsche Richtung: Griff-Fehlschlaege 26,8 -> 30,0%
        # (p=0,49, bei dieser Stichprobe nicht aufloesbar, aber die falsche Richtung).
        # URSACHE, und sie widerlegt meine eigene Vorabschaetzung von "+8,5% Gewicht": der
        # Selbst-Puffer ist RANDVOLL (12000, jeder Schluessel bei exakt IMIT_CAP/8), und
        # `runtime_policy.imitate` verdraengt "the OLDEST sample of the FULLEST key" -- ALTERSBASIERT,
        # die Guete wird NICHT gefragt.  Es wird also nichts hinzugefuegt, sondern ERSETZT: 21% mehr
        # Eintraege (129 -> 156) heissen 21% mehr Verdraengung guter Demonstrationen durch schwaechere.
        # VORAUSSETZUNG fuer diesen Weg UND fuer die phasenweise Gutschrift: guetebewusste
        # Verdraengung.  Solange sie fehlt, ist jedes Hinzufuegen ein Nullsummenspiel.
        _ifail = _gimit and os.environ.get("ACT23_IMIT_FAIL", "0") != "0"
        if _ifail:
            imit_bar = float(os.environ.get("ACT23_IMIT_FAIL_BAR", "0.045"))
        imit_ok = (s_d is not None and s_d < imit_bar) and (delivered or _ifail)
        imitated = False
        if (use_net and pol_trace and lifted and imit_ok and not slipped
                and not EXV_FREEZE and not D0_FREEZE
                and os.environ.get("ACT23_SELFIMIT", "1") == "1"):
            _q = wm_quality(s_d) if _gimit else 1.0
            added = runtime.imitate([s for s, _a in pol_trace], [a for _s, a in pol_trace],
                                    key=body, qual=_q)
            imitated = added > 0
            mix = ", ".join(f"{k or 'alt'} {v}" for k, v in
                            sorted(runtime.imit_mix().items(), key=lambda kv: -kv[1]))
            # Die Frische-Wache meldet ihren eigenen Fang: ohne sie waeren diese Zeilen als
            # Demonstration eingegangen -- frischer Zustand, veraltete Aktion.  Bei Rate 1 ist
            # der Zaehler immer 0, die Zeile erscheint dann gar nicht.
            _vw = (f"; {_imit_verworfen[0]} gehaltene Takte NICHT gelernt (Frische-Wache)"
                   if _imit_verworfen[0] else "")
            _wort = "Lieferung" if delivered else "knapp daneben"
            print(f"    [Selbst-Imitation] {_wort} {s_d * 1000:.0f}mm (Gewicht {_q:.2f}) -> +{added} "
                  f"Demo-Schritte ({runtime.n_imit()} im Selbst-Puffer, mittlere Guete "
                  f"{runtime.imit_qual():.3f}: {mix})"
                  f"{'; Teacher-Zeilen verworfen (eigener Erfolg zählt)' if confident else ''}{_vw}",
                  flush=True)
        elif use_net and pol_trace and lifted and delivered:
            print(f"    [Selbst-Imitation] Lieferung zu unsicher ({(s_d or 0) * 1000:.0f}mm) -- "
                  f"nicht imitiert", flush=True)
        # ENTKOPPELT: the widened bar must NOT also widen which episodes DISPLACE the teacher.  Dropping
        # the teacher's correction rows stays tied to the STRICT confident bar (imit_tol) -- a merely-ok
        # episode now contributes its own demos AND keeps the teacher's correction, which is exactly the
        # regime where both signals are useful.  keep-behaviour is therefore unchanged from before.
        if not D0_FREEZE:
            runtime.end_episode(keep=not (imitated and confident) and not EXV_FREEZE)
        #   correction rows enter DAgger; a self-validated success keeps ONLY its own actions
        # STAGE 2 lifelong: refit the choreography on the aggregated teacher labels; report the SHADOW
        # divergence |policy - teacher| over this episode's VISITED states in BOTH modes -- on FSM
        # episodes it says how close the net is to the teacher, on NETZ episodes it says how far the
        # policy drifted from the teacher ALONG ITS OWN TRAJECTORY (the oscillating-Bilanz diagnostic:
        # a Bilanz trough with a Schatten spike = the lifelong refit moved the policy, not bad luck).
        div = runtime.shadow_divergence_mm()
        if modviz is not None:                                 # Zusammenspiel-Kurven (passiv)
            try:
                _fv = vc.surprise()
                # EINHEIT: body.last_surprise ist der FK-Fehler in METERN (pc_act14:307, Norm des
                # Vorhersagefehlers), die Kurve heisst "Koerper (mm)".  Ohne die Umrechnung landen
                # ~0.0008 auf einer Achse, die sich die Kurve mit dem Fovea-Fehler (~0.3-0.9) teilt
                # -> sie liegt optisch KONSTANT auf 0 (vom Nutzer beobachtet, 2026-08-02).
                _bs = getattr(bm.body, "last_surprise", None)
                modviz.push(fovea=(None if _fv is None else _fv.get("sensor")),
                            body_mm=(None if _bs is None else float(_bs) * 1000.0),
                            wm_mu=locals().get("_mu_a"), wm_sd=locals().get("_sd_a"),
                            pol_div_mm=div,
                            place_mm=(None if s_d is None else s_d * 1000.0),
                            tilt_deg=(np.degrees(locals().get("_tilt") or 0.0)
                                      if TILT_ACTION else None),
                            nat_deg=(np.degrees(world.natural_tilt(world.radius_of(fe)))
                                     if (TILT_ACTION and fe is not None) else None),
                            zoom=float(getattr(vc.fovea, "z", 1.0)),
                            servo_mm=(float(np.mean(_fs["d"]))
                                      if (_fs := getattr(vc, "_fsv", None) or {"d": []})["d"] else None))
            except Exception as _e:
                if os.environ.get("ACT23_DEBUG", "0") == "1":
                    print(f"    [ModulViz] push uebersprungen: {_e}", flush=True)
        if not EXV_FREEZE and not D0_FREEZE:
            runtime.train(epochs=200)                          # act19's DAgger refits used 300; 80 underfit
            if LOSLASS_KOPF:                                   # der Loslass-Kopf lernt mit (s. LOSLASS_KOPF)
                loslass_kopf.lernen(runtime._X, runtime._Y, epochs=60)
        #   the shifting aggregate (user watched the net under-CLOSE the gripper -- the BC smoothing
        #   artefact that stronger refits + DAgger labels at the visited close-states sharpen)
        if np.isfinite(div):
            # PHASENWEISE Aufschluesselung (2026-08-13): der Gesamtwert mittelt ueber die Episode.
            # Gemessen ist aber, dass die Policy den GREIFpunkt auf Millimeter trifft und das
            # ABLAGEziel um Zentimeter verfehlt (18mm bei Erfolg, 44mm bei Fehlschlag), waehrend ihr
            # eigener Teacher ~11mm schafft -- die Aufschluesselung zeigt, wo sie auseinanderlaeuft.
            _ph = runtime.shadow_divergence_by_phase()
            _pt = ""
            if _ph:
                _ord = [k for k in ("anfahren", "greifen", "tragen", "ablegen") if k in _ph]
                _pt = " | " + "  ".join(f"{k} {_ph[k][0]:.0f}mm({_ph[k][1]})" for k in _ord)
            print(f"    [Stufe 2] Choreo-Schatten ({'Netz' if use_net else 'FSM'}-Lauf): "
                  f"|Netz-Teacher| {div:.0f} mm ({runtime.n()} DAgger + {runtime.n_imit()} Selbst, "
                  f"nachtrainiert){_pt}", flush=True)
        # ANEIGNUNG: die Episode einer selbst benannten Klasse zuschreiben, falls sie kommandiert war.
        # BEIDE ADRESSIERUNGSWEGE ZAEHLEN (2026-09-11).  Bis hierher stand nur state.SHAPE_KEY --
        # also der KNOPF-Pfad.  Das Eigenschafts-Kommando laeuft aber ueber state.EIGENSCHAFT und
        # blieb unsichtbar: im Langlauf vom 10.09. stand 'neu-373' in ALLEN 363 Aneignungszeilen
        # mit "kommandiert 0x" und wurde im selben Protokoll fuenfmal adressiert ([Auto 409]
        # neu-373 + mittel, [Auto 511] farbe-4 + neu-373, ...).  Damit war die Aussage "keine
        # Klasse wird je kommandiert" fuer jeden Lauf mit Eigenschafts-Kommando wertlos -- und die
        # Frage "haelt Kommandieren eine Klasse am Leben" gar nicht erst stellbar.
        # Belege: wiki/befunde/langlauf-entkoppelt.md.
        acq_ep["n"] += 1
        _ck = state.SHAPE_KEY.get(body)
        if _ck is None and method == "eigenschaft":            # Formachse des Tripels (Farbe/Form/Groesse)
            _ck = state.EIGENSCHAFT.get(body, (None, None, None))[1]
        if _ck in acq:
            acq[_ck]["cmd"] += 1
            acq[_ck]["ok"] += int(bool(res.get("ok", False)))
        for _al in acq_line():
            print(f"    [Aneignung] {_al}", flush=True)
        if NOVEL_EVERY > 0 and _novel_half["h"] is not None:
            # KONTROLLE: steht der Probe-Koerper wirklich noch in der erzwungenen Proportion?
            # _set_sizes setzt die Formkoerper am Ende JEDER Episode auf die XML-Masse zurueck;
            # die Ausnahme dafuer muss nachweisbar greifen, sonst misst die ganze Kurve nichts.
            _ist = sim.m.geom_size[sim.m.body_geomadr[
                mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, NOVEL_BODY)]]
            _soll = np.asarray(_novel_half["h"], float)
            _ok = "haelt" if np.allclose(_ist[:3], _soll, atol=1e-6) else "ZURUECKGESETZT"
            print(f"    [Neuheit-Kontrolle] {NOVEL_BODY} soll {tuple(round(1000*x) for x in _soll)}mm, "
                  f"ist {tuple(round(1000*float(x)) for x in _ist[:3])}mm -> {_ok}", flush=True)
        if not EXV_FREEZE:
            save_state()                                       # lifelong progress survives a restart
        if os.environ.get("ACT23_ZEIT", "1") != "0":
            _now = _time.perf_counter()
            _ges = _now - _T["gesamt"]
            _wahr = _T.get("vor_ausfuehrung", _now) - _T["gesamt"]
            _aus = _T.get("nach_ausfuehrung", _now) - _T.get("vor_ausfuehrung", _now)
            _lern = _now - _T.get("nach_ausfuehrung", _now)    # Kredit + Welt-Fit + Selbst-Imitation
            _ft = getattr(vc.fovea, "t_step", 0.0) - _fov0[0]  #   + Runtime-Refit + Speichern
            _fn = getattr(vc.fovea, "n_step", 0) - _fov0[1]
            print(f"    [Zeit] gesamt {_ges:5.1f}s | Wahrnehmung {_wahr:4.1f} | Ausfuehrung {_aus:5.1f} "
                  f"(davon Fovea {_ft:4.1f} in {_fn} Schritten"
                  f"{f', {1e3*_ft/_fn:.0f}ms/Schritt' if _fn else ''}) | Lernen {_lern:4.1f}", flush=True)
        return res.get("ok", False), res.get("err", float("nan")) * 1000.0

    # CURIOSITY-driven auto-run (the act21 researcher pattern, user request): instead of a random pick
    # the agent practices what it KNOWS LEAST.  Object = the one whose CURRENT perceived situation has
    # the highest ensemble DISAGREEMENT sigma of the outcome model over the wrist candidates (epistemic
    # uncertainty -- exactly where one more own trial teaches the model most; a freshly discovered form
    # starts data-poor -> gets practiced automatically).  Target = DISTANCE-NOVELTY over the targets
    # already practiced (coverage, act21's dreamed goals -- no reward anywhere, both signals are the
    # agent's own: model disagreement + visit history).  ACT23_AUTO_CURIOUS=0 restores the random pick.
    AUTO_CURIOUS = os.environ.get("ACT23_AUTO_CURIOUS", "1") == "1"
    if SZENE_JE_EPISODE and AUTO_CURIOUS:
        # (3) aus dem Schalterkopf: die Neugier waehlt das Objekt nach GELERNTEN Werten, und die
        # unterscheiden sich zwischen zwei Armen.  Nicht heimlich abgeschaltet -- es ist Verhalten
        # des Agenten --, aber laut gesagt, denn die Paarung haelt dann nur bis zur ersten
        # abweichenden Wahl.
        print("  [Szene je Episode] ACT23_AUTO_CURIOUS=1 -- die Objektwahl haengt am GELERNTEN "
              "Zustand und laeuft zwischen zwei Armen auseinander.  Fuer eine gepaarte Messung "
              "ACT23_AUTO_CURIOUS=0 setzen.", flush=True)
    tgt_visited = [state.marker_xy(i) for i in range(len(state.MARKERS))]
    sig_hist = {}                                              # label -> recent sigma readings (progress signal)

    def curious_pick():
        """Pick object + target by curiosity; returns a status line, or None -> caller picks randomly.
        LEARNING PROGRESS, not raw uncertainty (the noisy-TV fix, user-observed): a stochastic outcome
        keeps the ensemble sigma HIGH forever (aleatoric noise looks like epistemic uncertainty), so
        argmax-sigma FIXATED on the freshly discovered form and practiced nothing else.  Score = the
        recent DROP of sigma (practice is paying off) + a small sigma term (young objects start
        data-poor and must be tried at all); the object is DRAWN proportional to score -- fixation
        impossible, mastered skills keep a small maintenance share."""
        from pc_cvnn.pc_act14 import _rand_xy
        from pc_cvnn.pc_act16 import BASE_CLEAR
        scores = []
        for k, (_l, nm, _m) in enumerate(state.OBJECTS):
            fe = situation_feats(nm)
            if fe is None:
                continue                                       # camera can't find it -> not a candidate
            # NEUHEIT DIREKT GEMESSEN statt aus der Ensemble-Uneinigkeit geraten.  Gemessen
            # 2026-08-11: sigma besteht zu 93% aus der INITIALISIERUNG der Mitglieder (ohne jedes
            # Resampling 0.1400 gegen 0.1502 mit), haengt entsprechend schwach an echter Neuheit
            # (+0.21) und gar nicht am Fehler (+0.030).  Es sollte zwei Jobs machen -- Risiko in
            # mu-lam*sigma und Neuheit hier -- und machte keinen.  world.novelty misst den Abstand
            # zur k-naechsten EIGENSTAENDIGEN Erfahrung; viermal dieselbe stehende Szene zaehlt
            # damit wie EINMAL (verifiziert: 12.82 -> 12.68 bei vier Wiederholungen, gegen 0.00 bei
            # vier eigenstaendigen Erfahrungen).
            # Nebenwirkung, die erwuenscht ist: das Rauschende-Fernseher-Problem entfaellt hier von
            # selbst -- ein stochastischer Ausgang haelt sigma ewig hoch, die ABDECKUNG aber nicht.
            # Die Lernfortschritts-Logik darunter bleibt, sie misst jetzt "gewinne ich hier noch
            # neues Terrain" statt "faellt meine Unsicherheit".  ACT23_NOVELTY_DIRECT=0 -> altes sigma.
            if NOVELTY_DIRECT:
                s = float(world.novelty(fe))
            else:
                _mu, sd = world.predict(fe, world.candidates(0, yaw=world.yaw_of(fe)))
                #   sigma over the action grid HERE -- same OBJECT-RELATIVE grid the choice uses
                s = float(sd.max())
            h = sig_hist.setdefault(_l, []); h.append(s); del h[:-8]
            lp = float(np.mean(h[:len(h) // 2]) - np.mean(h[len(h) // 2:])) if len(h) >= 6 else 0.0
            scores.append((max(lp, 0.0) + 0.25 * s, lp, s, k, _l))
        # NAMENLOSE mitbewerben lassen (s. _uebung oben): eine junge Klasse ohne Knopf wird nach
        # DENSELBEN Regeln bewertet wie die kommandierbaren Objekte -- kein Bonus, kein Sonderweg.  Sie
        # gewinnt von selbst oft genug, weil sie datenarm ist und das Welt-Modell dort am meisten
        # widerspricht; genau dafuer ist die Neugier da.
        for cname, nbody in _namenlose_kandidaten():
            fe = situation_feats(nbody)
            if fe is None:
                continue
            if NOVELTY_DIRECT:
                s = float(world.novelty(fe))
            else:
                _mu, sd = world.predict(fe, world.candidates(0, yaw=world.yaw_of(fe)))
                s = float(sd.max())
            h = sig_hist.setdefault(cname, []); h.append(s); del h[:-8]
            lp = float(np.mean(h[:len(h) // 2]) - np.mean(h[len(h) // 2:])) if len(h) >= 6 else 0.0
            scores.append((max(lp, 0.0) + 0.25 * s, lp, s, ("namenlos", cname, nbody),
                           f"namenlos {cname}"))
        if not scores or world.n() == 0:
            return None
        w = np.array([sc[0] for sc in scores]) + 1e-3
        _sc, lp_best, sd_best, k, lbl = scores[int(crng.choice(len(scores), p=w / w.sum()))]
        if isinstance(k, tuple):                               # namenlos gezogen -> nur fuer DIESE Episode
            _uebung_start(k[1], k[2])                          #   handhabbar, danach wieder ausgetragen
        else:
            state.sel = k
        bodies = [nm for _l2, nm, _m2 in state.OBJECTS]
        best_p, best_z, best_nov = None, None, -1.0
        for _ in range(24):                                    # target = most NOVEL reachable spot;
            p = _rand_xy(crng)                                 #   4b: novelty in the GOAL-LATENT space
            if (float(np.linalg.norm(p)) < BASE_CLEAR
                    or any(float(np.linalg.norm(p - sim.obj_pos(o)[:2])) < 0.05 for o in bodies)
                    # ... und STUETZEN mit ihrer groesseren Ausdehnung (s. place_selected_random):
                    # ein getraeumtes Ziel auf dem Sockel liesse den Arm stapeln, ohne dass es
                    # befohlen war.
                    or any(float(np.linalg.norm(p - sim.obj_pos(o)[:2])) < 0.10
                           for o in state.STUETZEN)):
                continue
            if DREAM:
                z = lgoal.encode_world(p)                      # the candidate's latent on the shared
                nov = dream_nov.score(z)                       #   dream/act manifold
            else:
                z, nov = None, min(float(np.linalg.norm(p - q)) for q in tgt_visited)
            if nov > best_nov:
                best_p, best_z, best_nov = p, z, nov
        if best_p is not None:
            state.target_idx = int(crng.integers(len(state.MARKERS)))
            state.set_marker_xy(state.target_idx, best_p); state.sync_active()
            if DREAM:
                lgoal.set_goal_vector(best_z)
                dream_nov.visit(best_z); del dream_nov.seen[:-40]   # bounded like tgt_visited: old
                #   practice fades, the workspace stays forever explorable (no novelty starvation)
            else:
                lgoal.set_goal(best_p)
                tgt_visited.append(np.asarray(best_p, float)); del tgt_visited[:-40]
        verb = "träumt Ziel" if DREAM else "neues Ziel"
        lang_info = f" | {lgoal_lang.format_latent_message(best_z, tag='z_g')}" if DREAM and best_z is not None else ""
        _sig = f"Neuheit={sd_best:.2f}" if NOVELTY_DIRECT else f"σ={sd_best:.2f}"
        try:
            lbl = state.anzeige(k)                         # farbneutral + aktuelle Farbe (s. anzeige)
        except Exception:
            pass
        return (f"[curiosity] übt '{lbl}' (Fortschritt {lp_best:+.2f}, {_sig})"
                + (f", {verb} [{best_p[0]:.2f},{best_p[1]:.2f}]"
                   + (f" (Latent-Neuheit {best_nov:.2f}){lang_info}" if DREAM else "")
                   if best_p is not None else ""))

    def bilanz_line(bilanz, obj_hist):
        """Rolling scoreboard, per MODE + per OBJECT (worst first).  MEASURED (150-ep run with the
        Schatten diagnostic): the Bilanz swings 13-43% while the policy's shadow stays flat ~10-12mm --
        the oscillation is mostly the CURIOSITY OBJECT MIX (corr Bilanz vs U+L share -0.68; a fixed-
        per-object-rate expectation reproduces it at r=+0.70), NOT learning instability.  Without the
        per-object split the scoreboard conflates task difficulty mix with skill."""
        parts = [f"{lbl} {sum(bilanz[md][-30:])}/{len(bilanz[md][-30:])}"
                 for md, lbl in (("fsm", "FSM"), ("netz", "Netz")) if bilanz[md]]
        per = {}
        for o, okv in obj_hist[-30:]:
            s, t = per.get(o, (0, 0)); per[o] = (s + okv, t + 1)
        objs = " · ".join(
            f"{o.replace(' Wuerfel', '').replace(' Objekt', '').replace('Neue Form ', 'Form-')} {s}/{t}"
            for o, (s, t) in sorted(per.items(), key=lambda kv: kv[1][0] / kv[1][1]))
        return ("    [Bilanz] letzte 30 je Modus: " + ", ".join(parts)
                + (f"  |  je Objekt: {objs}" if objs else ""))

    if not D0_FREEZE and int(os.environ.get("ACT23_GROESSE_SAMMELN", "0")) > 0:
        _groesse_sammeln(int(os.environ["ACT23_GROESSE_SAMMELN"]))
    elif not D0_FREEZE and GROESSE_SEHEN and len(groessen_schaetzer.X) < 200:
        print(f"  [Groesse] Schaetzer hat erst {len(groessen_schaetzer.X)} Zeilen -- sammle 200 Szenen "
              f"ohne Arm (einmalig, wird mit dem Zustand gespeichert)", flush=True)
        _groesse_sammeln(200)

    def _d0_components():
        """The complete in-process learner set at an AUTO-evaluation boundary.

        This is intentionally a declaration, not a freeze switch: a preflight must first expose
        every component that still learns during an evaluation before it is suppressed.
        """
        return {"bm": bm, "shape_clf": shape_clf, "world": world, "runtime": runtime,
                "colours": colours, "fovea": getattr(vc, "fovea", None), "latent_goal": lgoal,
                "latent_dynamics": lat_dyn, "dream_seen": dream_nov.seen, "self_eval": seval,
                "hoehe_schaetzer": hoehen_schaetzer, "groessen_schaetzer": groessen_schaetzer,
                "loslass_kopf": loslass_kopf, "wort_bedeutung": wort_bedeutung, "blick_daten": blick_daten}

    def _d0_boundary(name, **context):
        if not D0_MANIFEST_DIR:
            return None
        data = _d0_snapshot(_d0_components(), context={
            "boundary": name, "seed": os.environ.get("ACT23_SEED", "7"),
            "choreo": state.choreo, "auto_n": os.environ.get("ACT23_AUTO_N", "0"),
            **context,
        })
        _d0_write_manifest(os.path.join(D0_MANIFEST_DIR, f"{name}.json"), data)
        print(f"  [D0-Integritaet] {name}: Manifest geschrieben", flush=True)
        return data

    if headless and int(os.environ.get("ACT23_AUTO_N", "0")) > 0:
        # HEADLESS AUTO-RUN (for A/B measurement without the GUI): run N curiosity-picked episodes in
        # the requested choreo mode with the rolling Bilanz scoreboard -- the same loop the GUI Auto
        # button drives, minus rendering.  ACT23_CHOREO=netz + this = a long self-improvement run.
        N = int(os.environ.get("ACT23_AUTO_N"))
        state.auto = True
        print(f"  headless AUTO-Lauf: {N} Episoden, Choreo {state.choreo}, "
              f"Selbst-Imitation {'aus' if os.environ.get('ACT23_SELFIMIT','1')=='0' else 'an'}", flush=True)
        if EXV_N > 1:
            print(f"  [EXV] Ausfuehrungs-Varianz: jede der {N} Szenen {EXV_N}x wiederholt "
                  f"({N * EXV_N} Episoden), Startpose-Jitter "
                  f"{f'{EXV_JITTER:.3f} rad' if EXV_JITTER > 0 else 'aus (nur natuerliche Streuung)'}, "
                  f"Lernen {'EINGEFROREN' if EXV_FREEZE else 'AN (!)'}, "
                  f"Zustand {'unveraendert (nur einmal vor der Messung gesichert)' if EXV_FREEZE else 'WIRD FORTGESCHRIEBEN'}",
                  flush=True)
            if EXV_FREEZE:
                # EINMAL sichern, BEVOR die Messung laeuft: das Einfrieren blockiert save_state()
                # je Episode, damit die Messung den Zustand nicht veraendert.  Das Startup-Training
                # (z.B. das Nachtrainieren fehlender Fovea-Klassen, ~20 min) faellt damit aber bei
                # JEDEM Lauf der Reihe erneut an.  Hier ist noch nichts gemessen worden -- der
                # Zustand ist der geladene plus Startup -- also ist dieser eine Schreibvorgang
                # unbedenklich und spart der Dosis-Wirkungs-Reihe Stunden.
                save_state()
                print("  [EXV] Startup-Zustand einmalig gesichert (Messung selbst schreibt nicht)",
                      flush=True)
        bilanz = {"fsm": [], "netz": []}
        obj_hist = []
        _d0_before = _d0_boundary("before")
        force_list = [s.strip() for s in os.environ.get("ACT23_AUTO_OBJ", "").split(",") if s.strip()]
        #   measurement knob: pin the auto pick to one object (label substring) or CYCLE a comma list
        #   ("U-Form,Gruenes" = interleaved practice, the interference probe); curiosity mix confounds
        #   per-object trends.  ACT23_AUTO_PLACE=0 keeps the scene AS THE LAST EPISODE LEFT IT (the
        #   inheritance probe: failures shove/wedge the object and the next episode starts from that).
        for ep in range(N):
            if SZENE_JE_EPISODE:
                # (1) GENERATOR IM PLATZ zuruecksetzen -- `crng` ist in Dutzenden Closures
                # gebunden; ein neues Objekt unter demselben Namen saehen sie nicht.
                crng.bit_generator.state = np.random.default_rng(
                    [int(os.environ.get("ACT23_SEED", "7")), ep]).bit_generator.state
            if NOVEL_EVERY > 0 and ep > 0 and ep % NOVEL_EVERY == 0:
                spawn_novel_shape()                            # neue FORM einfuehren (ohne Label)
            if SZENE_JE_EPISODE or (SCENE_EVERY > 0 and ep > 0 and ep % SCENE_EVERY == 0):
                # (2) mit SZENE_JE_EPISODE JEDE Episode, auch die erste: sonst truege Episode 0
                # die Szene des Programmstarts, und die haengt am Bootstrap-Verbrauch von crng.
                randomize_objects()          # neue Szene + ROTATION, welche Objekte stehen (s. SCENE_N)
            _farbe_wuerfeln()                                  # VOR der Wahrnehmung, s. Docstring
            if force_list:
                want = force_list[ep % len(force_list)]
                # auch ueber den Koerpernamen und die alten Farbnamen ("Gruenes" = obj_green), die
                # es seit den farbneutralen Namen nicht mehr gibt
                _alt = {"rotes": "obj_red", "gruenes": "obj_green"}.get(want.lower().split()[0], "")
                ks = [k for k, (l, _n, _m) in enumerate(state.OBJECTS)
                      if want.lower() in l.lower() or want.lower() == _n.lower() or _n == _alt]
                if not ks:
                    raise SystemExit(f"ACT23_AUTO_OBJ '{want}' matcht kein Objekt")
                state.sel = ks[0]
                state.target_idx = int(crng.integers(len(state.MARKERS)))
                if os.environ.get("ACT23_AUTO_PLACE", "1") == "1":
                    state.place_selected_random(crng)          # random target MARKER position ...
                    # ... and MOVE THE OBJECT ITSELF to a random clear pose: place_selected_random
                    # only places the target, objects otherwise sit at their XML slots forever in a
                    # pinned probe (measured: the L stayed at the top-edge slot across ALL probes --
                    # a spot where even the guarded teacher cannot ARRIVE -- and every per-object
                    # probe silently measured that one unreachable pose).
                    from pc_cvnn.pc_act14 import _rand_xy
                    from pc_cvnn.pc_act16 import BASE_CLEAR
                    _pb = state.OBJECTS[state.sel][1]
                    _others = [nm for _l, nm, _m in state.OBJECTS if nm != _pb]
                    for _ in range(200):
                        _p = _rand_xy(crng)
                        if float(np.linalg.norm(_p)) >= BASE_CLEAR and all(
                                float(np.linalg.norm(_p - sim.obj_pos(o)[:2])) > 0.05 for o in _others):
                            break
                    sim.set_object(_pb, [float(_p[0]), float(_p[1])],
                                   yaw=float(crng.uniform(0.0, np.pi)))
                    mujoco.mj_forward(sim.m, sim.d)
                pick = None
            else:
                pick = curious_pick() if AUTO_CURIOUS else None
            if pick is None and not force_list:
                # nur Objekte, die auch AUF DEM TISCH stehen (ein geparktes waere unkommandierbar)
                _auf = [k for k, (_l, _n, _m) in enumerate(state.OBJECTS)
                        if float(np.linalg.norm(np.asarray(scene.get(_n, (np.zeros(2),))[0], float)
                                                - np.asarray(PARK_XY, float))) > 0.05]
                state.sel = int(crng.choice(_auf)) if _auf else int(crng.integers(len(state.OBJECTS)))
                state.target_idx = int(crng.integers(len(state.MARKERS)))
                state.place_selected_random(crng)
            elif pick is not None:
                print(f"    {pick}", flush=True)
            # AUSFUEHRUNGS-VARIANZ (ACT23_EXV=M > 1): DIESELBE Szene M-mal fahren.  Objektpose, Ziel
            # und damit die Situationsmerkmale sind bitgleich, die Aktionswahl ist deterministisch
            # (LCB; Neigungs- und Griff-Neugier stehen auf 0) -- was variiert, ist allein die
            # AUSFUEHRUNG: der Arm startet dort, wo drive_home ihn gelassen hat (arm_reset=False),
            # und die Fovea traegt ihren Zustand aus der Vorepisode mit.
            # WOZU: die Aktion erklaert gemessen nur +0.055 R^2, aber aehnliche Zeilen stimmen im
            # Ausgang zu 83-88% ueberein -- die Struktur sitzt also irgendwo.  Streuen die
            # Ergebnisse INNERHALB einer Szene, entscheidet die gefahrene Bahn und nicht die
            # getroffene Wahl; bleiben sie konstant, ist die Ausfuehrung unschuldig.
            _reps = EXV_N
            _pb = state.OBJECTS[state.sel][1]
            _pose = sim.obj_pose7(_pb)                         # VOLLE Pose, auch schraeg (s. obj_pose7)
            _scene = []
            # world.candidates() zieht n ZUFAELLIGE Aktionskandidaten aus world.rng -- ohne
            # Ruecksetzen saehe Wiederholung 2 andere Kandidaten und koennte eine andere Aktion
            # waehlen.  Dann waere nicht mehr die Ausfuehrung isoliert, sondern Wahl+Ausfuehrung
            # vermischt.  Der Bit-Generator-Zustand wird deshalb je Wiederholung zurueckgespult.
            _rng0 = world.rng.bit_generator.state if _reps > 1 else None
            _jrng = np.random.default_rng(1000 + ep)           # eigener Strom: world.rng wird zurueckgespult
            for _rep in range(_reps):
                if _rep > 0:                                   # Szene exakt wiederherstellen
                    sim.set_obj_pose7(_pb, _pose)
                    if EXV_JITTER > 0.0:                       # Startpose gezielt stoeren
                        # Gelenknamen AUS DER SIM: bei ACT14_DOF=4 hat ARM3 vier Eintraege, die
                        # Liste ist also sechs lang (joint_0..joint_5) -- eine feste Namensliste
                        # traf die falschen Gelenke.
                        _jn = list(ARM3) + ["joint_4", "joint_5"]
                        _q = sim.arm_angles_full() + _jrng.normal(0.0, EXV_JITTER, len(_jn))
                        for _j, _v in zip(_jn, _q):
                            _lo, _hi = sim.joint_range(_j)
                            _v = float(np.clip(_v, _lo, _hi))
                            sim.d.qpos[sim.jqadr[_j]] = _v
                            sim.d.ctrl[sim.act[_j]] = _v
                            # Geschwindigkeit mit auf null: sonst waere neben der gewollten
                            # Positionsstoerung noch eine ungewollte Geschwindigkeitsstoerung im
                            # Spiel und die Dosis waere nicht mehr die, die draufsteht.
                            sim.d.qvel[sim.m.jnt_dofadr[sim._jid(_j)]] = 0.0
                    mujoco.mj_forward(sim.m, sim.d); sim.step(40)
                    world.rng.bit_generator.state = _rng0
                _auto_eig_umschreiben()
                _ziel_adresse_wuerfeln()                       # ZIEL als Adresse (s. ZIEL_ADRESSE)
                print(f"  [Auto {ep}]{f' W{_rep}' if _reps > 1 else ''} {state.label()} ...", flush=True)
                try:
                    ok, err = run_one()
                finally:
                    _uebung_ende()                             # namenlose Uebung wieder austragen
                print(f"  [Auto {ep}] {'GELIEFERT' if ok else 'NICHT geliefert'}  |  Abstand {err:.0f} mm",
                      flush=True)
                _scene.append((bool(ok), float(err)))
                bilanz["netz" if state.choreo in ("netz", "attractor") else "fsm"].append(bool(ok))
                obj_hist.append((state.OBJECTS[state.sel][0], bool(ok)))
            if _reps > 1:
                _o = [x[0] for x in _scene]; _d = [x[1] for x in _scene]
                print(f"    [EXV] Szene {ep} ({state.OBJECTS[state.sel][0]}): "
                      f"{''.join('1' if x else '0' for x in _o)}  "
                      f"{sum(_o)}/{len(_o)} geliefert  Abstand {np.mean(_d):.0f}+-{np.std(_d):.0f} mm",
                      flush=True)
            if (ep + 1) % 10 == 0:
                print(bilanz_line(bilanz, obj_hist), flush=True)
        _d0_after = _d0_boundary("after")
        if _d0_before is not None:
            _d0_changed = _d0_changed_components(_d0_before, _d0_after)
            _d0_learn_changed = _d0_changed_components(_d0_before, _d0_after, learning_only=True)
            print(f"  [D0-Integritaet] Vollzustand: "
                  f"{'MUTATION: ' + ', '.join(_d0_changed) if _d0_changed else 'unveraendert'}",
                  flush=True)
            print(f"  [D0-Integritaet] Lernzustand: "
                  f"{'MUTATION: ' + ', '.join(_d0_learn_changed) if _d0_learn_changed else 'unveraendert'}",
                  flush=True)
        return

    if headless:
        def _intro_and_command():
            print("  open-set: das nie trainierte obj_T taucht auf ...")
            introduce_object()
            if NOVEL_BODY not in state.SHAPE_KEY:
                print(f"    NICHT entdeckt/registriert (Klassen: {shape_clf.open_names}, "
                      f"buffer={len(shape_clf._novel_buf)}, th={shape_clf.novel_th:.2f}) -- EXPECTED at mini "
                      f"ACT23_SHAPE_STEPS (manifold too sparse: at 250 steps known/novel OVERLAP, >=1200 "
                      f"separates; GUI default 2500 discovers).", flush=True)
                return
            print(f"    entdeckt + selbst benannt: '{state.SHAPE_KEY[NOVEL_BODY]}'  "
                  f"(Klassen: {shape_clf.open_names})", flush=True)
            state.sel = len(state.OBJECTS) - 1
            ok, err = run_one()
            print(f"    {state.OBJECTS[state.sel][0]:16s}: {'GELIEFERT' if ok else 'NICHT'}  ({err:.0f}mm)",
                  flush=True)

        intro_first = os.environ.get("ACT23_INTRO_FIRST", "0") == "1"
        if intro_first:                                        # the USER'S race: introduce while the long I
            _intro_and_command()                               # is still undiscovered -- its class is born
        print("  headless self-test: one command per object")  # FIRST from the same glances and must NOT
        for k, _o in enumerate(CommandState23.OBJECTS):        # get bound to the T's button
            state.sel = k; ok, err = run_one()
            print(f"    {state.OBJECTS[k][0]:16s}: {'GELIEFERT' if ok else 'NICHT'}  ({err:.0f}mm)", flush=True)
        if not intro_first:
            _intro_and_command()
        for _ in range(3):                                     # exercise the curiosity pick (GUI auto path)
            print(f"    curiosity: {curious_pick()}  -> sel={state.OBJECTS[state.sel][0]}", flush=True)
        state.choreo = "netz"                                  # STAGE 2: the LEARNED choreography drives
        print(f"  Stufe 2: Choreo-NETZ fährt die Kommandos ({runtime.n()} Teacher-Samples) ...")
        for k, _o in enumerate(CommandState23.OBJECTS):
            state.sel = k; ok, err = run_one()
            print(f"    {state.OBJECTS[k][0]:16s}: {'GELIEFERT' if ok else 'NICHT'}  ({err:.0f}mm)", flush=True)
        return

    act16.run_combined._quiet = True
    panel.update(sim.render(CAM), "bereit — Objekt und Ziel wählen, dann Ausführen")
    ep = 0
    bilanz = {"fsm": [], "netz": []}                           # rolling per-mode delivery record: without
    #   a scoreboard slow DAgger progress is indistinguishable from noise (user: "so la la")
    obj_hist = []                                              # (object, ok) for the per-object split
    while not state.exit:
        if not (state.go or state.auto):
            panel.plt.pause(0.05); continue
        if state.auto:                                         # AUTO-Lauf: CURIOSITY picks what to practice
            # NEUHEIT + SZENEN-WUERFELN AUCH IN DER GUI.  Beides stand bisher NUR in der kopflosen
            # Schleife, ACT23_NOVEL_EVERY und ACT23_SCENE_EVERY waren im GUI-Lauf also WIRKUNGSLOS --
            # der Nutzer startete am 2026-08-20 mit ACT23_NOVEL_BODY=obj_X und NOVEL_EVERY=6, und in
            # 332 Episoden wurde der Probe-Koerper KEIN EINZIGES MAL hingestellt (null Geburten, null
            # "[Neuheit]"-Zeilen).  Im GUI ging es bisher nur ueber den Knopf "Objekt hinzufügen".
            if NOVEL_EVERY > 0 and ep > 0 and ep % NOVEL_EVERY == 0:
                spawn_novel_shape()                            # neue FORM einfuehren (ohne Label)
            if SCENE_EVERY > 0 and ep > 0 and ep % SCENE_EVERY == 0:
                randomize_objects()                            # neue Szene + Rotation (s. SCENE_N)
            _farbe_wuerfeln()                                  # VOR der Wahrnehmung, s. Docstring
            pick = curious_pick() if AUTO_CURIOUS else None    #   (model uncertainty + goal novelty); random
            if pick is None:                                   #   fallback if perception/model isn't ready
                state.sel = int(crng.integers(len(state.OBJECTS)))
                state.target_idx = int(crng.integers(len(state.MARKERS)))
                state.place_selected_random(crng)
            else:
                print(f"    {pick}", flush=True)
            _auto_eig_umschreiben()                            # ADRESSIERUNG ueber Eigenschaften
            panel._refresh()                                   # "Auto: aus" stoppt nach der Episode
        # ZIEL als Adresse (s. ZIEL_ADRESSE) -- AUSSERHALB des Auto-Zweigs, damit der Schalter
        # auch im Hand-Befehl wirkt.  Der Wurf gilt je Episode; ohne Zielmodus "koerper" ist er
        # eine sofortige Rueckkehr und der Marker bleibt das Ziel.
        _ziel_adresse_wuerfeln()
        panel._refresh()                                       # Aufgabenzeile zeigt den gewuerfelten Bezug
        state.go = False
        tag = "Auto" if state.auto else "Befehl"
        print(f"  [{tag} {ep}] {state.label()} ...")
        state.busy = True
        try:
            ok, err = run_one()
        finally:
            state.busy = False
            _uebung_ende()                                     # namenlose Uebung wieder austragen
        line = f"[{tag} {ep}] {'GELIEFERT' if ok else 'NICHT geliefert'}  |  Abstand {err:.0f} mm"
        print("  " + line); panel.update(sim.render(CAM), line); ep += 1
        bilanz["netz" if state.choreo == "netz" else "fsm"].append(bool(ok))
        obj_hist.append((state.OBJECTS[state.sel][0], bool(ok)))
        if ep % 10 == 0:                                       # rolling last-30 scoreboard per mode+object
            print(bilanz_line(bilanz, obj_hist), flush=True)
        if panel._pending_randomize:                           # deferred mid-episode clicks run NOW,
            panel._pending_randomize = False                   #   between episodes (see state.busy)
            randomize_objects(); panel.update(sim.render(CAM), "Objekte neu gewürfelt"); panel._refresh()
        if panel._pending_introduce:
            panel._pending_introduce = False
            introduce_object(); panel._refresh()
        if panel._pending_platte:
            panel.platte_nachholen()
    print("  Steering beendet.")


#  Kernschalter, die IMMER protokolliert werden -- die Stellschrauben der laufenden Untersuchungen.
#  Alles andere erscheint nur, wenn es von der Vorgabe abweicht (s. _print_run_settings).
_CORE_KNOBS = ("ACT23_SEED", "ACT23_CHOREO", "ACT23_POLICY", "ACT23_STATE_PATH",
               "ACT23_GRASP_CANDS", "ACT23_GRASP_CANDS_NETZ", "ACT23_GRASP_CAND_CAP",
               "ACT23_GRIPLABEL", "ACT23_U_DENSEGRASP", "ACT23_CREDIT",
               "ACT23_TILT_ACTION", "ACT23_TILT_CURIOSITY", "ACT23_WRIST_REL",
               "ACT23_LAM", "ACT23_HOME_Z_MIN", "ACT14_DOF",
               "ACT23_BIND_CONFIRM", "ACT23_BIND_WIN")


def _source_defaults():
    """Vorgabewerte ALLER Schalter direkt aus dem Quelltext lesen (os.environ.get("ACT..", "..")).

    Aus dem Quelltext statt aus einer gepflegten Liste, damit die Ausgabe nicht veraltet, sobald
    ein neuer Schalter dazukommt -- in diesem Projekt passiert das staendig.  Faellt still auf
    'nur gesetzte Variablen zeigen' zurueck, wenn die Dateien nicht lesbar sind."""
    import glob
    import re as _re
    pat = _re.compile(r'os\.environ\.get\(\s*["\'](ACT\d*[A-Z0-9_]*)["\']\s*(?:,\s*["\']([^"\']*)["\'])?')
    here = os.path.dirname(os.path.abspath(__file__))
    out = {}
    try:
        files = ([os.path.join(here, n) for n in ("pc_act23.py", "pc_act18.py", "pc_act16.py",
                                                 "pc_act15.py", "pc_act14.py")]
                 + sorted(glob.glob(os.path.join(here, "arm_modules", "*.py"))))
        for f in files:
            if not os.path.exists(f):
                continue
            with open(f, encoding="utf-8", errors="replace") as fh:
                for m in pat.finditer(fh.read()):
                    out.setdefault(m.group(1), m.group(2))
    except Exception:
        pass
    return out


def _print_run_settings():
    """Die EINSTELLUNGEN des Laufs ins Log schreiben (Nutzerwunsch 2026-08-02: im Log war nicht
    nachvollziehbar, mit welchen Schaltern die GUI lief).

    Zwei Bloecke, weil ein Vollabzug aller ~138 Schalter das Log zumuellen wuerde:
      ABWEICHUNGEN  jeder Schalter, dessen Umgebungswert von der Quelltext-Vorgabe abweicht.  Das
                    ist die eigentliche Antwort auf "womit lief der Lauf" und faengt AUCH Schalter,
                    an die beim Schreiben dieser Funktion niemand gedacht hat.
      KERN          die Stellschrauben der laufenden Untersuchungen, immer sichtbar, damit man den
                    Stand auch dann sieht, wenn alles auf Vorgabe steht.
    Dazu Commit + Arbeitsbaum-Zustand, damit ein Log-Fund spaeter reproduzierbar bleibt."""
    try:
        import subprocess
        d = os.path.dirname(os.path.abspath(__file__))
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=d, capture_output=True,
                           text=True, timeout=5)
        st = subprocess.run(["git", "status", "--porcelain"], cwd=d, capture_output=True,
                            text=True, timeout=5)
        if h.returncode == 0:
            dirty = " + ungespeicherte Aenderungen" if st.stdout.strip() else ""
            print(f"  [Lauf] Commit {h.stdout.strip()}{dirty}", flush=True)
    except Exception:
        pass
    defs = _source_defaults()
    diff = []
    for k, dv in sorted(defs.items()):
        v = os.environ.get(k)
        if v is not None and v != dv:
            diff.append(f"{k}={v} (Vorgabe {dv!r})")
    for k, v in sorted(os.environ.items()):          # gesetzt, aber im Quelltext nicht gefunden
        if k.startswith("ACT") and k not in defs:
            diff.append(f"{k}={v} (keine Vorgabe im Quelltext)")
    if diff:
        print("  [Lauf] Abweichungen von der Vorgabe:", flush=True)
        for line in diff:
            print(f"           {line}", flush=True)
        _own = [d for d in diff if d.split("=")[0] not in _ENV_AT_IMPORT]
        if _own:
            print(f"           (davon von act23 selbst gesetzt, NICHT aus dem Startbefehl: "
                  f"{', '.join(sorted(d.split('=')[0] for d in _own))})", flush=True)
    else:
        print("  [Lauf] alle Schalter auf Vorgabe", flush=True)
    core = [f"{k.replace('ACT23_', '').replace('ACT14_', '')}={os.environ.get(k, defs.get(k))}"
            for k in _CORE_KNOBS if (k in os.environ or k in defs)]
    print("  [Lauf] Kern: " + "  ".join(core), flush=True)


class _Tee:
    """Mirror a console stream into a log file (user request: every session leaves a log).
    The FILE skips carriage-return progress spam (warmup/train tickers), PREFIXES every line with
    a wall-clock timestamp and writes UTF-8 regardless of the console codepage; the CONSOLE stream
    is passed through untouched (unstamped -- the timestamps are for post-hoc log analysis).

    WARUM DIE ZEITSTEMPEL (2026-08-02): der Nutzer sah die Kamera-Anzeige stehen und konnte nicht
    entscheiden, ob der Lauf haengt oder nur das Fenster nicht neu zeichnet -- und das LOG konnte
    es auch nicht, weil keine Uhrzeit drinstand.  Mit Stempel je Zeile sieht man sofort, ob die
    Episoden zum fraglichen Zeitpunkt weiterliefen (Anzeige-Problem) oder nicht (echter Haenger),
    und nebenbei, welche Phase wieviel Zeit kostet.  ACT23_LOG_TIME=0 schaltet es ab."""

    STAMP = os.environ.get("ACT23_LOG_TIME", "1") != "0"

    def __init__(self, stream, fh):
        self._s = stream
        self._f = fh
        self._bol = True                               # steht der Schreibkopf am Zeilenanfang?

    def _stamped(self, data):
        """Zeitstempel an jeden ZEILENANFANG.  write() bekommt beliebige Bruchstuecke (print gibt
        Text und '\\n' getrennt aus), darum wird der Zeilenanfang ueber Aufrufe hinweg gemerkt --
        sonst landete der Stempel mitten in der Zeile.  Leerzeilen bleiben leer."""
        if not self.STAMP:
            return data
        import time
        out = []
        for part in data.splitlines(keepends=True):
            if self._bol and part not in ("\n", "\r\n"):
                out.append(time.strftime("%H:%M:%S "))
            out.append(part)
            self._bol = part.endswith("\n")
        return "".join(out)

    def write(self, data):
        try:                                           # a dying console pipe (e.g. truncated by the
            self._s.write(data)                        # shell) must not kill the FILE log, and vice
        except Exception:                              # versa -- each side fails independently
            pass
        if "\r" not in data:
            try:
                self._f.write(self._stamped(data))
                self._f.flush()
            except Exception:
                pass

    def flush(self):
        try:
            self._s.flush()
        except Exception:
            pass
        try:
            self._f.flush()
        except Exception:
            pass

    def __getattr__(self, name):                       # encoding, isatty, buffer, ...
        return getattr(self._s, name)


def _start_session_log():
    """Tee stdout+stderr into log/pc_act23_<timestamp>_<pid>.txt at the repo root.

    ACT23_LOG=0 schaltet das Mitschreiben ab, ACT23_LOG_DIR lenkt es woanders hin -- beides fuer
    MESSLAEUFE gedacht, damit sie die run_history-Anzeige des Nutzers nicht zumuellen.

    DIE PID GEHOERT IN DEN NAMEN (2026-08-29): der Name bestand nur aus dem Zeitstempel auf die
    Sekunde genau.  Zwei parallel gestartete A/B-Arme bekamen denselben Namen und schrieben
    VERSCHRAENKT in dieselbe Datei -- zwei Laeufe in einem Log, in run_history nicht trennbar.
    """
    if os.environ.get("ACT23_LOG", "1") != "1":
        return
    import datetime
    d = os.environ.get("ACT23_LOG_DIR") or os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "log"))
    os.makedirs(d, exist_ok=True)
    path = os.path.join(
        d, f"pc_act23_{datetime.datetime.now():%Y-%m-%d_%H-%M-%S}_{os.getpid()}.txt")
    fh = open(path, "a", encoding="utf-8", errors="replace")
    sys.stdout = _Tee(sys.stdout, fh)
    sys.stderr = _Tee(sys.stderr, fh)
    print(f"  [Log] Konsole wird mitgeschrieben: {path}", flush=True)


if __name__ == "__main__":
    _start_session_log()
    if os.environ.get("ACT23_VIZ", "0") == "1":
        run_self_learning_steering(headless=(os.environ.get("ACT23_VIZ_HEADLESS", "0") == "1"))
    elif os.environ.get("ACT23_MODE", "diag").lower() == "shapes":
        main()
    else:
        main_diag()
