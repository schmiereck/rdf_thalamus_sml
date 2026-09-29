r"""
pc_act16.py — manipulation with CLAWS: GRASP first, PUSH as fallback (user's idea).

Per the user's live observation: with the curved CLAWS the arm sometimes GRASPS the cube and
carries it well; when it misses, it should fall back to PUSHing the cube from behind with the
(slightly-closed) claws.  So this combines both and we can later see which the net learns better:
  1. GRASP:  open claws above the cube -> lower -> close -> lift.  If the cube came up -> CARRY
     it to the target and place it.
  2. PUSH (fallback, if the grasp missed): pre-closed claws approach from behind and push the
     cube to the target by genuine contact (the inward claw tips cup it).
The reach uses the LEARNED 3-D kinematics to the `contact` site (claw notch).  A visible target
marker (mocap disk) is placed on the table.  Perception is privileged sim state (camera = act15).

  ACT16_HEADLESS=1   metrics over episodes     ACT16_TARGET=obj_red|...   commanded cube
  ACT16_MODE=both|grasp|push                    (default both = grasp-then-push)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import mujoco

from pc_cvnn.pc_act14 import BracketArmSim, ArmBodyModel3D, HOME, _rand_xy, CamViz, REACH_XY

J5_OPEN = float(os.environ.get("ACT16_J5_OPEN", "0.54"))   # gripper OPEN angle (was 1.8; user first set 60% ->
J5_GRIP, J5_PUSH = 0.0, 0.55                    # 1.08, then 30% -> 0.54: the wide-open claw kept COLLIDING with
#   neighbouring objects during the approach, before it even closes).  J5_GRIP = fully-closed (grip);
#   J5_PUSH = partly-open (push).  Restore the old wide open via ACT16_J5_OPEN=1.8.
# Gripper-regime thresholds SCALE with J5_OPEN (calibrated to reproduce the old fixed values at open=1.8) -- a
# fixed 1.0/0.9/0.6 sat right at the TOP of a narrowed (1.08) range, so the "descend-while-open then close"
# choreography collapsed (the policy began closing ~30mm too HIGH; measured: gripper closed at hand_z ~60mm vs a
# 24mm object).  Scaling keeps a clean descend-while-open margin at any open width.
J5_OPEN_TH = 0.5556 * J5_OPEN                   # OPEN/approach regime boundary (= 1.0 at open 1.8)
J5_CLOSED_TH = 0.5 * J5_OPEN                    # "closed enough to count as gripping"      (= 0.9 at open 1.8)
J5_REFLEX_TH = 0.3333 * J5_OPEN                 # grasp-reflex: gripper still openish        (= 0.6 at open 1.8)
#                              (push: claws spread ~40mm to contact a wide block's face at 2 points)
OBJS = ["obj_red", "obj_green", "obj_blue"]
CUBE_HALF = np.array([0.012, 0.012, 0.012])     # graspable cube
WIDE_HALF = np.array([0.024, 0.024, 0.010])     # wide SQUARE block: too wide to grasp -> push
#                                                 (square so the push direction doesn't matter)
OVER_Z, GRASP_Z, PUSH_Z = 0.06, 0.014, 0.016
CARRY_Z = float(os.environ.get("ACT16_CARRY_Z", "0.09"))   # hand height while CARRYING a grasped object.
#   Raised 0.055 -> 0.09 so the carried object is transported clearly OVER other cubes instead of through
#   them: at 0.055 the carried cube's BOTTOM sat ~16mm up (measured), BELOW a 24mm cube's top, so the
#   transport rammed any cube on the path and knocked the object loose (deliberate cube-on-path test:
#   distractor knocked 3/6 -> 0/6 at 0.09; carried-cube bottom mean 16mm -> 50mm, clears a 24mm cube 15%
#   -> 86% of carry steps).  Still within reach; the size-adaptive carry_z floors on this.  env: ACT16_CARRY_Z.
CARRY_GAIN = float(os.environ.get("ACT16_CARRY_GAIN", "0.9"))   # GENTLE-CARRY reach (vs the normal 2.0/0.026):
CARRY_MDQ  = float(os.environ.get("ACT16_CARRY_MDQ",  "0.011")) # slower lateral transport so an off-COM grip on
#   a concave object (a perceived U) is not torn out of the claws by carry acceleration.  Opt-in (carry_gentle).
PUSH_LIFT_Z = 0.07                              # raise the claws to move behind an object (clear it)
STANDOFF, NEAR, TOL, CAP = 0.045, 0.02, 0.025, 2200
# ABLAGE-NAEHE (ACT16_NEAR_ABLAGE, Vorgabe = NEAR = 0,02 m, also zeichengleich).  Gemessen 2026-09-26
# (wiki/befunde/ablage-schwelle-im-teacher.md): der seitliche Abstand beim Loslassen liegt eng bei
# 25-31 mm (Median 26), fast nur entlang der Klauenachse, waehrend die Objektlage nur 12 mm falsch
# geglaubt wird und in der Klaue 3-5 mm versetzt sitzt.  Die Ursache ist diese Konstante: der Teacher
# traegt, bis die HAND NEAR vom Ziel ist, senkt dann ab und laesst los, sobald die HOEHE erreicht
# ist -- seitlich konvergiert wird nicht mehr.  Die Policy hat genau das gelernt.  Der Schalter
# trennt die Ablage vom Anfahren (das Greifen behaelt NEAR).
NACHSEH_R = float(os.environ.get("ACT16_NACHSEH_R", "0.04"))
OBJ_VERSATZ = os.environ.get("ACT16_OBJ_VERSATZ", "0") == "1"   # gesehenen Objektversatz ausgleichen
# ERST TIEF UNTEN HINSCHAUEN (ACT16_OBJSICHT_Z, Vorgabe 0 = sofort in NACHSEH_R).  Gemessen aus
# Traghoehe (60-93 mm): 8 von 17 verdeckt, gesehen 7-30 mm daneben -- mehr als der Versatz selbst,
# und der gesehene Versatz liegt fast immer bei 17-22 mm (Parallaxe: die Kamera bildet auf die
# Tischebene ab).  Mit dem Schalter schaut er erst, wenn die Hand unter dieser Hoehe steht.
OBJSICHT_Z = float(os.environ.get("ACT16_OBJSICHT_Z", "0"))
OBJ_WARTE = int(os.environ.get("ACT16_OBJ_WARTE", "150"))   # Schritte, die die Korrektur hoechstens dauert   # ab hier schaut er das Ziel nochmal an
NEAR_ABLAGE = float(str(os.environ.get("ACT16_NEAR_ABLAGE", "")).replace(",", ".") or NEAR)
# ABSENKEN AB (ACT16_SENK_NAH, Vorgabe = NEAR_ABLAGE, also zeichengleich).  Gemessen 2026-09-28: mit
# NEAR_ABLAGE = 8 mm erreicht das sanfte Tragen die 8 mm oft nie -- 17-29 von 60 FSM-Episoden liefen
# in die Tragezeitgrenze und oeffneten am Episodenende aus 60-90 mm Hoehe (mit 20 mm: 2).  Der Schalter
# trennt die beiden Aufgaben der einen Schwelle: ab SENK_NAH wird abgesenkt (und dabei weiter aufs
# Ziel gezielt), losgelassen wird erst unten UND naeher als NEAR_ABLAGE (FSM: hoechstens OBJ_WARTE).
SENK_NAH = float(str(os.environ.get("ACT16_SENK_NAH", "")).replace(",", ".") or NEAR_ABLAGE)
# IN DER LUFT KORRIGIEREN (ACT16_LUFT_H, Vorgabe 0 = aus, zeichengleich).  Ohne den Schalter zielt
# die Ablage waehrend des seitlichen Nachfuehrens schon auf die volle Ablagehoehe; ist die Hand noch
# nicht ueber der (um den gesehenen Objektversatz verschobenen) Stelle, steht das Objekt womoeglich
# schon auf dem Tisch und wird mitgeschleift.  Mit dem Schalter haelt die Hand LUFT_H ueber der
# Ablagehoehe, bis sie naeher als NEAR_ABLAGE an der Stelle ist (hoechstens OBJ_WARTE Schritte), und
# senkt erst dann senkrecht ab.
LUFT_H = float(str(os.environ.get("ACT16_LUFT_H", "")).replace(",", ".") or 0.0)
# VOR DEM OEFFNEN HINSCHAUEN (ACT16_PRUEF_TOL in m, Vorgabe 0 = aus, zeichengleich).  Gemessen
# 2026-09-28 (wiki/befunde/ablage-beim-oeffnen.md): Fehlablagen sind Objekte, die NACH dem Zufassen
# seitlich in der Klaue verrutscht sind (15 gegen 3 mm beim Oeffnen); die Hand steht genau.  Mit dem
# Schalter schaut die Kamera (objekt_sehen_fn) im Moment, in dem die FSM oeffnen wuerde, auf das
# Objekt: liegt es naeher als PRUEF_TOL am Ziel, wird geoeffnet; sonst wird der gesehene Versatz
# uebernommen und nachgefuehrt (mit LUFT_H > 0 wieder angehoben), hoechstens PRUEF_N-mal.
PRUEF_TOL = float(str(os.environ.get("ACT16_PRUEF_TOL", "")).replace(",", ".") or 0.0)
PRUEF_N = int(os.environ.get("ACT16_PRUEF_N", "2"))
# NACH DEM NACHFUEHREN GANZ ABSETZEN (ACT16_PRUEF_ABSETZEN, Vorgabe 0).  Gemessen 2026-09-29: nach dem
# Anheben (LUFT_H) oeffnete die FSM schon 12 mm ueber der Ablagehoehe -- das Objekt fiel aus 10-38 mm
# und rutschte weg.  Mit dem Schalter wird nach einer Nachfuehrung bis auf die Ablagehoehe abgesenkt
# (+4 mm, hoechstens OBJ_WARTE Schritte), erst dann geoeffnet.
PRUEF_ABSETZEN = os.environ.get("ACT16_PRUEF_ABSETZEN", "0") == "1"
GRASP_OFFSET = float(os.environ.get("ACT16_GRASP_OFFSET", "0.006"))   # (#2) grasp height = obj_half + this
#   (cube -> 0.018, was 0.014): the claw tips sit ~14mm below the contact site, so grasp_z=0.014 put them
#   AT the floor and any overshoot was blocked/deflected; +4mm lifts them clear while still gripping the cube
GRASP_MAX_HALF = 0.016                          # footprint half above which an object is too wide to grasp
CLAW_OFF = float(os.environ.get("ACT16_CLAW_OFF", "0.008"))
OBS_STATE = os.environ.get("ACT16_OBS_STATE", "1") == "1"   # STUFE C (Tastsinn-Vorschlag): der POLICY-
#   VORGABE AN seit 2026-08-07, nach A/B (14 Ep je Arm, gleiche Saat): privilegiert 5/14 geliefert /
#   haelt 50%, beobachtbar 4/14 / 57% -- KEIN Einbruch (Fisher p=1.0).  Die Krücke ist ersetzbar;
#   damit trainieren alle künftigen Demos auf real-tauglichen Zustaenden und der TASTSINN wird zur
#   tragenden Information.  Ehrlich: n=14 belegt Gleichheit nicht, nur die Abwesenheit eines
#   Zusammenbruchs -- der Verteilungsversatz ist konstruktiv klein (haelt: Objekt=Hand; verloren:
#   Objekt=Fallort auf Ruhehoehe), und genau der Druck entscheidet, welcher Fall gilt.
#   Zustand nutzt eine BEOBACHTBARE Objektschaetzung (Belief + Tastsinn) statt des privilegierten
#   sim.obj_pos -- s. die Konstruktion von c_obs/cz_obs in run_combined.  Nur der ZUSTAND wechselt;
#   die FSM (Teacher) behaelt ihr Privileg als Trainingssignal.  =0 (Vorgabe): altes Verhalten.   # Versatz Reichpunkt -> Backenmitte (m).
#   s. die Begruendung an der Anwendungsstelle in run_combined.  ACT16_CLAW_OFF=0 stellt das alte
#   Verhalten wieder her (fuer ein sauberes A/B).
SERVO_K, SERVO_CONF, SERVO_LOST = 0.5, 0.5, 6   # closed-loop grasp-target belief: correction gain,
#   min track-confidence to update, frames of low confidence before a saccadic re-acquire
MAX_REACQ = 2                                   # cap re-acquires per episode: a persistent track failure
#   must not loop perceive() forever (the fovea visibly re-searching every few seconds) -- then hold
PHASE_STALL = 500                               # steps in ONE phase before the episode gives up (stuck arm)
REFLEX = os.environ.get("ACT16_REFLEX", "1") == "1"      # (#4) hand-coded grasp reflex (close on a hover-stall);
#   another RUNTIME rule -- toggle off to test whether the NET closes on its own (ACT16_REFLEX=0).
HOVER_LIMIT = int(os.environ.get("ACT16_HOVER", "40"))   # (#4) steps the policy may hover OPEN+HIGH over
#   the object before the GRASP REFLEX takes over the descend+close (it stalled instead of grasping)
BASE_CLEAR = float(os.environ.get("ACT16_BASE_CLEAR", "0.11"))  # (#1) keep objects + target this far from
#   the base ORIGIN: the base plate is 0.075-half (a 15cm square at 0,0) and REACH starts at y=0.07, so
#   objects/target could spawn ON the base (unreachable / the open gripper collides with the turret)
WRIST_ALIGN = os.environ.get("ACT16_WRIST", "1") == "1"      # (B, default ON) roll joint_4 so the claw aligns to
#   the object's grip axis.  PROPRIOCEPTIVE (claw_yaw from FK, no camera), re-applied EVERY step (set_arm3_targets
#   resets joint_4 to HOME each step, AND claw_yaw is POSE-dependent, so it must keep correcting as the arm moves).
#   Orientation IS sensitive: forced-DIAGONAL cube grip slips (21/40 vs aligned 39/40), elongated LONG-axis 9/40.
#   The user KEEPS it on -- it looks clean in the viz and aligns the grasp robustly.  A few coupled-pipeline
#   grasps still regress (pc_act21 C 9/10 -> 6/10), but per the user's observation that is NOT the wrist: it is
#   the UNDERTRAINED RECOVERY states (miss -> re-grasp -> carry; the policy sometimes re-grasps then "hangs" with
#   the cube instead of carrying) -- rare in the teacher demos -> a TRAINING-coverage gap, addressed separately.
#   Cube -> fixed WRIST_TGT mod 90deg (step B, no perception); elongated -> short axis mod pi.  Disable: ACT16_WRIST=0.
WRIST_TGT = float(os.environ.get("ACT16_WRIST_TGT", "0.0"))  # world-frame grip yaw the claw aligns to (rad)
WRIST_APPROACH_R = float(os.environ.get("ACT16_WRIST_APPROACH_R", "0.07"))   # align the wrist ONLY once the hand
#   is within this horizontal radius of the object (the APPROACH) -- NOT in the initial/home pose (looks odd +
#   collides with arm/base).  Once the hand has descended to the grip (WRIST_LOCK_MARGIN) the angle is HELD
#   (re-asserted, NOT re-corrected) so the wrist does not suddenly roll and twist the object out at contact.
WRIST_LOCK_MARGIN = float(os.environ.get("ACT16_WRIST_LOCK", "0.012"))   # lock the wrist this far above grip z
# DIE REGEL GEGEN STAPEL (ACT16_ZIEL_SAEUBERN, Vorgabe 1 = wie bisher).
# run_combined schiebt ein uebergebenes Ziel in acht Durchgaengen von JEDEM Koerper um 0,05 m weg.
# Das ist eine LAUFZEITREGEL (wiki/mechanismen/laufzeit-regeln.md) und zugleich das, was ein Ziel
# AUF oder NAHE einem Koerper unmoeglich macht: jede kleinere Vorgabe wird stillschweigend auf
# 50 mm aufgeblasen.  Der Schalter laesst sie aus, ohne den Rest der Saeuberung anzutasten --
# die Sockelfreiheit (BASE_CLEAR) bleibt in jedem Fall aktiv, sonst faehrt der Arm in seinen
# eigenen Fuss.
ZIEL_SAEUBERN = os.environ.get("ACT16_ZIEL_SAEUBERN", "1") == "1"
# DIE DRITTE ZIELDIMENSION (ACT16_GOAL_Z, Vorgabe 0).  Stufe 2 von
# wiki/fragen/stapeln-als-aufgabe.md.  Eingeschaltet darf goal_fn DREI Werte liefern (der dritte
# ist die Ablagehoehe der Hand), und der Zustandsvektor der Policy bekommt sie als 14. Eingang.
# WARUM UEBERHAUPT EIN SCHALTER, obwohl der Wert ohne Stapelaufgabe konstant GRASP_Z waere:
# eine 14. Spalte ist KEINE verhaltensneutrale Ergaenzung.  Der Vorwaertsdurchlauf bleibt zwar
# bitgleich (ensure_state_dim verbreitert mit NULL-Spalten), aber ein FRISCHES Netz wird mit
# anderer Breite gezogen und jeder Refit sieht eine Spalte mehr -- ein Vorgabelauf waere danach
# nicht mehr derselbe Lauf.  Mit dem Schalter auf 0 bleibt der Zustand 13-dimensional.
# EINBAHNSTRASSE: ein Lauf MIT Schalter migriert den Puffer der Zustandsdatei dauerhaft auf 14
# Spalten.  Deshalb nur auf Kopien fahren.
GOAL_Z = os.environ.get("ACT16_GOAL_Z", "0") == "1"
# DIE GREIFHOEHE (ACT16_GRIFF_Z, Vorgabe 0) -- das Spiegelbild von GOAL_Z.
# Stufe 2 hat dem ZIEL eine dritte Dimension gegeben, damit der Arm AUF etwas ablegen kann.
# Stufe 4 braucht dasselbe fuer das OBJEKT: "nimm das, was auf Y liegt" heisst, den Griff
# TIEFER anzusetzen waere falsch -- der Koerper liegt eine Auflagenhoehe hoeher.
# Die Hoehe kommt wie beim Ziel aus perceive_fn: liefert es einen DRITTEN Wert, ist das die
# Handhoehe, bei der gegriffen wird.  Ohne Schalter oder ohne dritten Wert bleibt sie GRASP_Z
# und alle Zeilen sind Zeichen fuer Zeichen die alten.
GRIFF_Z = os.environ.get("ACT16_GRIFF_Z", "0") == "1"
# ERFOLGSBEGRIFF "RUHT" STATT "LIEGT TIEF" (ACT16_ERFOLG_RUHT, Vorgabe 0 bis gemessen).
# Stufe 2 von wiki/fragen/stapeln-als-aufgabe.md: `rested = cz < half + 0,010` heisst woertlich
# "liegt auf dem Tisch" und verbucht damit jeden GELUNGENEN Stapel als Fehlschlag.  Der Schalter
# ersetzt das durch "das Objekt bewegt sich nicht mehr und die Klaue ist offen" -- eine Definition,
# die von der Aufgabe unabhaengig ist und fuer die alte genauso gilt.
# VORGABE 0, weil er die alte Messreihe veraendern KANN (ein noch rollendes Objekt gilt jetzt als
# nicht geliefert, ein sauber gestapeltes als geliefert) und die Uebereinstimmung der beiden
# Begriffe erst gemessen werden muss.
ERFOLG_RUHT = os.environ.get("ACT16_ERFOLG_RUHT", "0") == "1"
RUHT_V = float(os.environ.get("ACT16_RUHT_V", "0.005"))   # m/s, darunter gilt ein Koerper als ruhend
# =========================================================================================
# DIE AUFLAGE ERTASTEN (ACT16_TASTEN, Vorgabe 0).  Nutzerwunsch 2026-09-21: "weniger Teacher ist
# immer besser" -- die Ablagehoehe soll aus dem AUSGANG kommen, nicht aus `sim.m.geom_size`.
#
# WAS NICHT GEHT, und das ist gemessen: der Ausgang "Stapel haelt oder nicht" traegt die Hoehe
# NICHT.  Bei gelungenen Stapeln liegt der Hoehenfehler bei 2,20 mm, bei misslungenen bei 2,30 --
# die Fehlschlaege sind seitlich (Versatz 65 gegen 15 mm), s.
# wiki/befunde/drei-auflagen-im-lauf.md.  Auf Erfolg/Misserfolg zu lernen hiesse, auf Rauschen zu
# lernen.  Das Ausgangssignal muss KOERPERLICH und ABGESTUFT sein.
#
# WAS GEHT: die Hand senkt das getragene Objekt, bis es AUFSETZT, und merkt sich, WO das war.
# `sim.grasp_pos()` ist `site_xpos`, also die tatsaechliche Handstelle aus der Vorwaertskinematik
# -- Propriozeption, die ein echter Roboter aus seinen Gelenkgebern hat, kein Simulatorwissen.
# Die Aufsetzhoehe IST die gesuchte Groesse: genau bei ihr ruht das Objekt auf der Auflage.
# Kein Objektmass noetig, keine Geometrie, kein Etikett von aussen.
#
# ZWEISEITIG WIRD DAS SIGNAL ERST DURCH DAS UEBERTASTEN.  Ohne es kaeme eine Beruehrung nur
# zustande, wenn die Schaetzung zu TIEF lag -- der Lerner bekaeme nur einseitige Beispiele und
# driftete.  Deshalb zielt die Ablagephase TAST_TIEF unter die Schaetzung und haelt an, sobald
# sie Widerstand fuehlt.  Das ist ein Reflex, kein Plan: gestoppt wird auf ein Sinnessignal hin.
# Er darf zur Testzeit abgeschaltet werden -- dann steht die gelernte Schaetzung allein.
TASTEN = os.environ.get("ACT16_TASTEN", "0") == "1"
TAST_TIEF = float(os.environ.get("ACT16_TAST_TIEF", "0.008"))   # m unter die Schaetzung hinaus
TAST_STILL = float(os.environ.get("ACT16_TAST_STILL", "0.0004"))  # m je Schritt = "sinkt nicht mehr"
TAST_N = int(os.environ.get("ACT16_TAST_N", "6"))               # so viele Schritte in Folge
# WANN GILT EIN STILLSTAND ALS WIDERSTAND UND NICHT ALS ANKUNFT?  Dicht am befohlenen Ziel wird
# der Regler von selbst langsam -- dort ist Stillstand nichtssagend.  TAST_RAND trennt beides und
# ist zugleich die Austrittsschwelle, damit kein toter Bereich dazwischen bleibt: DARUEBER zaehlt
# ein Stillstand als Beruehrung, DARUNTER gilt die Phase als durchgetastet.  Der Wert ist die
# Groessenordnung des bleibenden Regelfehlers, nicht eingestellt auf ein Ergebnis.
TAST_RAND = float(os.environ.get("ACT16_TAST_RAND", "0.002"))
SOFT_RELEASE = os.environ.get("ACT16_SOFT_RELEASE", "1") == "1"   # place: RAMP the claw open (mirror of the
#   close ramp) + retreat UP open, and never grasp-reflex onto an object already AT the goal -- the old
#   instant snap-open at grasp height FLICKED the just-placed object off the target (user-observed in the
#   act23 auto runs: "delivered, then shoved away at release/re-grasp").  ACT16_SOFT_RELEASE=0 restores.
CLOSE_GUARD = os.environ.get("ACT16_CLOSE_GUARD", "1") == "1"   # in the grasp approach, do NOT close the claw
#   while the hand is still in the AIR above the grasp height.  EDGE positions (near base/camera) descend more
#   SLOWLY, so the policy/reflex would otherwise close ~15mm too HIGH and miss -- the hand CAN reach the object,
#   it is just not DOWN yet (verified by a pure forced-open reach test).  Mirrors the teacher's own close rule
#   (hz <= grasp_z + 0.012), now ENFORCED on the learned policy too.  Disable with ACT16_CLOSE_GUARD=0.
RULEDIAG = os.environ.get("ACT16_RULEDIAG", "0") == "1"      # RIEGEL-DIAGNOSE (Vorgabe AUS): je Episode
#   zaehlen, wie oft Reflex und Schliess-Riegel die Entscheidung der Policy tatsaechlich UEBERSCHRIEBEN
#   haben -- und, davon getrennt, wie oft sie es GETAN HAETTEN.  Anlass: beide sind Laufzeitregeln
#   ausserhalb des Trainings (Nutzerprinzip: das Netz soll selbst entscheiden, wann die Klaue schliesst).
#   act21 schaltet sie zur Laufzeit ab (ACT21_RULES_TRAIN_ONLY, Vorgabe 1) und hat gemessen, dass das
#   Netz allein gleich gut liefert; act23 hat das nie nachgeholt -- dort laufen beide mit.
#   OHNE DIESE ZAEHLER WAERE DIE MESSUNG BLIND: greift eine Regel ohnehin nie, kann ihr Abschalten
#   per Konstruktion nichts aendern, und ein unauffaelliges Ergebnis haette nichts bewiesen.
ABLENKDIAG = os.environ.get("ACT16_ABLENKDIAG", "0") == "1"  # ABLENKER-DIAGNOSE (Vorgabe AUS).
#   ANLASS (2026-09-07, wiki/befunde/ablenker-anfahrt.md): in 63 von 932 Episoden liegt die ERSTE
#   Anfahrt ueber 80 mm daneben, und davon wurde 1 geliefert -- rund ein Siebtel aller Fehlschlaege.
#   Die ADRESSIERUNG ist dabei nachweislich richtig (Median 2 mm, 914/920 eindeutig); in der
#   Beispielepisode 810 stand die Detektion auf 0 mm, `[Glaube]` meldete aber Wahrnehmung 46,5 mm
#   und Zustand 69,0 mm.  Der Fehler entsteht also NACH der Adressierung, im laufenden Tracker.
#   FRAGE, DIE DIESE DIAGNOSE BEANTWORTET: sitzt der Belief `c` waehrend der Anfahrt auf einem
#   ANDEREN Koerper -- ab welchem Schritt, auf welchem, und findet er zurueck?
#   PRIVILEGIERT und AUSSCHLIESSLICH messend, wie GLAUBDIAG: die wahren Lagen gehen in keinen
#   Lernenden, in keinen Zustand und in keine Entscheidung, nur in diese Zaehler.
GLAUBDIAG = os.environ.get("ACT16_GLAUBDIAG", "0") == "1"    # GLAUBENS-DIAGNOSE (Vorgabe AUS).
#   ANLASS: die Tastsinn-Diagnose zeigte, dass in GESCHEITERTEN Episoden der Schliesswunsch in 67%
#   der Schritte ueber der Riegel-Schwelle liegt (in gelieferten: 21%), teils dauerhaft 30-60 mm zu
#   hoch -- und zwar WAEHREND das Objekt laut Wahrheit noch auf dem Tisch liegt.  Das ist kein
#   verpasster Zeitpunkt, das sieht nach einem falschen ZUSTAND aus.
#   Diese Diagnose zerlegt den Policy-Zustand an den drei Stellen, an denen er kaputtgehen kann
#   (Wahrnehmung / _cobs-Logik / Phantom-Griff) und aendert nichts.  Sie ist privilegiert und rein
#   messend: die Wahrheit geht in keinen Lernenden und in keine Entscheidung.
TASTDIAG = os.environ.get("ACT16_TASTDIAG", "0") == "1"      # TASTSINN-DIAGNOSE (Vorgabe AUS).
#   FRAGE WAR: kann ein GEFUEHLTES Signal die Hoehenschwelle des Schliess-Riegels ersetzen?  Der
#   Riegel haengt an gz = obj_h + GRASP_OFFSET, also am WISSEN ueber die Objekthoehe -- und obj_h
#   kommt aus geom_half(cmd), der ECHTEN MuJoCo-Geometrie (act16:311).  Auf dem realen Roboter
#   existiert der Wert nicht.
#
#   ANTWORT: NEIN, dreifach gemessen 2026-08-25/26.  Diese Diagnose bleibt als Messwerkzeug da;
#   der gebaute Ersatz ist wieder entfernt.  Wer es erneut versuchen will, weiss damit, was
#   bereits widerlegt ist:
#     (1) "Schliesse, wenn der Abstieg stoppt" -- der Abstieg stoppt NIE (40/40 Episoden).  Die
#         Backen fahren am Objekt VORBEI nach unten, statt darauf aufzusetzen; die Hand erreicht
#         den Greifpunkt trotzdem (tiefster Punkt Median -0.3 mm).  Es gibt keinen Aufsetzstoss.
#     (2) "Schliesse, wenn du etwas spuerst" -- die OFFENE Klaue misst in 26/40 Episoden exakt
#         0.00 N.  Der Streifen sitzt innen und meldet erst, wenn die Backen druecken; er kann
#         den Schluss also bestaetigen, nie ausloesen.
#     (3) "Merke den LEEREN Griff frueher" (Backenwinkel < 0.10 + Druck < 0.5N, im Teacher) --
#         gebaut und dort gemessen, wo die Regel FAEHRT (act19-Aufbau, policy_fn=reactive_subgoal,
#         6 Seeds x 40 Ep gepaart): 128/240 gegen 129/240, +0.4 Punkte, p=1.000, bei 431
#         Ausloesungen.  Nicht stumm, sondern wirkungslos: sie liefert dasselbe Teilziel wie die
#         vorhandene Wiederhol-Regel, nur frueher -- und zu diesem Zeitpunkt ist der Griff
#         laengst danebengegangen.  Der leere Griff ist die FOLGE, nicht die Ursache.
#   Was die Diagnose stattdessen zeigte: in GESCHEITERTEN Episoden liegt der Schliesswunsch in
#   67% der Schritte ueber der Schwelle (in gelieferten: 21%), teils dauerhaft 30-60 mm zu hoch.
#   Das sieht nach falschem Glauben ueber die eigene Lage aus, nicht nach falschem Zeitpunkt.
SIZE_ADAPT = os.environ.get("ACT_SIZE_ADAPT", "1") == "1"    # (c) derive grasp heights from object size
PERSIST = os.environ.get("ACT16_PERSIST", "0") == "1"        # keep the scene between episodes
SCENE_N = int(os.environ.get("ACT16_SCENE_N", "3"))         # objects PLACED per episode (cmd + distractors);
#   the rest of OBJS are parked off-table -- keeps the scene at ~3 like before despite 5 commandable colours
ELONG_RATE = float(os.environ.get("ACT16_ELONG", "0.25"))   # fraction of episodes with ONE elongated (2:1)
ELONG_HALF = np.array([0.024, 0.012, 0.012])                # object mixed into the data (a shape variation)
ELONG_CMD = os.environ.get("ACT16_ELONG_CMD", "0") == "1"   # the COMMANDED object is elongated (orientation-grasp
#   test, step C): the net must FIND it, PERCEIVE its long axis, and align the wrist to the SHORT axis to grip.


def _push_subgoal(hxy, hz, c, t):
    """MARKOVIAN push: get behind the object (relative to the target), lower, and follow-push it toward
    the target.  Phase inferred from geometry (no hidden state); the gripper stays spread (J5_PUSH)."""
    d = t - c; n = np.linalg.norm(d); d = d / n if n > 1e-6 else np.array([1.0, 0.0])
    behind = c - d * STANDOFF                              # contact point on the far side from the target
    proj = float(np.dot(hxy - c, d))                      # along the push dir: <0 behind, >0 past the object
    perp = float(np.linalg.norm((hxy - c) - proj * d))    # lateral offset from the push line
    low = hz < PUSH_Z + 0.012
    on_line_behind = (proj < 0.02) and (perp < NEAR)      # hand behind/at the object, on the push line
    if low and on_line_behind:                            # PUSH: follow-push the object toward the target
        return np.array([c[0] + d[0] * 0.03, c[1] + d[1] * 0.03, PUSH_Z, J5_PUSH])   # (aim just ahead of it)
    if on_line_behind and not low:                        # at the push line but raised -> LOWER
        return np.array([behind[0], behind[1], PUSH_Z, J5_PUSH])
    return np.array([behind[0], behind[1], PUSH_LIFT_Z, J5_PUSH])   # otherwise -> reposition behind, RAISED


def reactive_subgoal(state):
    """A REACTIVE (stateless) re-derivation of the grasp-and-place teacher: the sub-goal as a PURE
    function of the observed state [hand xyz, obj xy, obj z, target xy, gripper, OBJ_HEIGHT, OBJ_FOOTPRINT].
    Unlike the FSM (hidden `phase`) this is MARKOVIAN, so it is a valid DAgger expert and BC target -- the
    phase is INFERRED from geometry.  AFFORDANCE: a footprint wider than the gripper can grasp -> PUSH it;
    else GRASP.  (c) SIZE-ADAPTIVE: the grasp/place/carry heights are derived from the object's half-height
    (cube -> the old 0.014, flat/tall -> grasp at their own centre).
    Returns a flat [aim_x, aim_y, aim_z, gripper] (the same shape the policy emits)."""
    hx, hy, hz, cx, cy, cz, tx, ty, j5, obj_h, obj_fp = np.asarray(state, float)[:11]
    # state[11:13] = [druck_gueltig, fingerdruck_N] (Tastsinn, 2026-08-07).  Der TEACHER liest ihn
    # bewusst NICHT: seine Wiederhol-Logik haengt am privilegierten cz (run_combined lift-Phase) und
    # bleibt als Trainingssignal -- die POLICY bekommt den Druck als beobachtbaren Ersatz und lernt
    # per DAgger, das Teacher-Verhalten am Tastsinn statt am Privileg festzumachen.
    hxy = np.array([hx, hy]); c = np.array([cx, cy]); t = np.array([tx, ty])
    if obj_fp > GRASP_MAX_HALF:                           # AFFORDANCE: too wide to grasp -> push
        return _push_subgoal(hxy, hz, c, t)
    # GREIFHOEHE AUS DEM ZUSTAND (Spalte 15, s. ACT16_GRIFF_Z).  Ohne sie zielte der Teacher auf
    # Tischhoehe, waehrend der Koerper eine Auflage hoeher liegt -- das Etikett waere per Bauart
    # falsch, genau wie es die Ablagehoehe bis 2026-09-19 war (s. teacher-widerspricht-dem-stapel).
    h_griff = max(0.0, float(state[14]) - GRASP_Z) if len(state) >= 15 else 0.0
    if SIZE_ADAPT:
        grasp_z = obj_h + GRASP_OFFSET + h_griff          # grasp at the object's centre (cube -> 0.014)
        carry_z = max(CARRY_Z, 2.0 * obj_h + 0.02)        # lift high enough to clear a TALL object
        lift_thresh = obj_h + 0.014                       # "lifted off the table" relative to its height
    else:
        grasp_z, carry_z, lift_thresh = GRASP_Z, CARRY_Z, 0.028
    # DIE AUFLAGE AM ZIEL (Stufe 2, ACT16_GOAL_Z).  Der Zustand traegt dann als 14. Wert die
    # Ablagehoehe tgt_z = GRASP_Z + Oberkante der Auflage.  OHNE DIESE ZEILEN WIDERSPRACH DER TEACHER
    # SEINER EIGENEN AUSFUEHRUNG: die FSM legte auf der Auflage ab, choreo_log etikettiert aber JEDEN
    # besuchten Zustand mit dieser Funktion -- und die sagte "auf grasp_z absenken", also auf
    # Tischhoehe, in den Sockel hinein.  Aus jedem gelungenen Stapel haette die Policy das Gegenteil
    # gelernt (wiki/befunde/teacher-widerspricht-dem-stapel.md).
    # NUR UEBER DEM ZIEL: nur dort steht die Auflage.  Die Hoehe verschiebt dort ZWEI Groessen --
    # die Ablagehoehe, und die Hub-Schwelle: ein Objekt, das auf der Auflage aufsetzt (Mitte 20 mm),
    # laege sonst unter lift_thresh (26 mm), gaelte als "nicht mehr gehoben", und der Greifzweig
    # zielte auf grasp_z -- wieder in den Sockel.
    # VERHALTENSNEUTRAL ohne ACT16_GOAL_Z: dann hat der Zustand 13 Werte und h_auf ist 0.
    h_auf = max(0.0, float(state[13]) - GRASP_Z) if len(state) >= 14 else 0.0
    if h_auf > 0.0 and np.linalg.norm(c - t) < NEAR:
        lift_thresh = lift_thresh + h_auf
    # DIE AUFLAGE UNTER DEM OBJEKT (Stufe 4, ACT16_GRIFF_Z) verschiebt dieselbe Schwelle, nur am
    # anderen Ende: ein Koerper, der auf einer 14-mm-Platte steht, hat seine Mitte bei 26 mm und
    # laege damit SCHON UEBER lift_thresh -- der Teacher hielte ihn fuer laengst gegriffen und
    # spraenge sofort in die Ablage, ohne ihn je angefasst zu haben.  Dieselbe Klasse Fehler wie
    # oben, nur gespiegelt; die Ablageseite hat sie 2026-09-19 einen ganzen Lernlauf gekostet.
    # NUR UEBER DEM OBJEKT: nur dort steht diese Auflage.
    if h_griff > 0.0 and np.linalg.norm(hxy - c) < NEAR:
        lift_thresh = lift_thresh + h_griff
    place_z = grasp_z - h_griff + h_auf                   # abgelegt wird OHNE die Griff-Auflage
    grasped = (cz > lift_thresh) and (j5 < J5_CLOSED_TH)  # object lifted off the table AND gripper closed
    if grasped:                                           # CARRY -> place -> release
        if np.linalg.norm(hxy - t) > SENK_NAH:           # carry over the target (s. NEAR_ABLAGE, SENK_NAH)
            return np.array([tx, ty, carry_z, J5_GRIP])
        if hz > place_z + 0.012:                          # lower onto the target (or its SUPPORT)
            return np.array([tx, ty, place_z, J5_GRIP])
        if np.linalg.norm(hxy - t) > NEAR_ABLAGE:        # unten, aber noch nicht nah genug (nur SENK_NAH > NEAR_ABLAGE)
            return np.array([tx, ty, place_z, J5_GRIP])
        return np.array([tx, ty, place_z, J5_OPEN])       # release
    # (Ein gefuehlter LEERGRIFF -- Backenwinkel + Fingerdruck statt Hub-Hoehe -- stand hier und ist
    #  nach der Messung wieder entfernt: +0.4 Punkte bei p=1.000, s. die TASTDIAG-Notiz oben.)
    # RETRY a MISSED grasp instead of dragging the cube to the foot (obs 4): if the gripper is closed and
    # raised to carry height but the cube is STILL on the table, the grasp clearly missed -> re-OPEN above
    # the cube and retry the approach.  Triggers only once the empty lift is COMPLETE (a real grasp would
    # have raised the cube in lockstep, so cz>lift_thresh fires `grasped` first), so it never oscillates.
    if (j5 < 0.25) and (hz > carry_z - 0.012):
        return np.array([cx, cy, OVER_Z, J5_OPEN])        # missed -> reopen + re-approach (no push-to-foot)
    # The gripper STATE disambiguates the two regimes that look alike in (hz): descending-to-grasp
    # (gripper OPEN) vs ascending-with-cube (gripper CLOSED).  Splitting on j5 stops the open/close
    # oscillation that flung the cube (the old code re-OPENED on the lower branch while lifting).
    if j5 > J5_OPEN_TH:                                   # gripper OPEN -> APPROACH regime
        if np.linalg.norm(hxy - c) > NEAR:               # move over the cube
            return np.array([cx, cy, OVER_Z, J5_OPEN])
        if hz > grasp_z + 0.012:                          # lower onto it, still open
            return np.array([cx, cy, grasp_z, J5_OPEN])
        return np.array([cx, cy, grasp_z, max(J5_GRIP, j5 - 0.2)])    # at pose -> begin closing gently
    # gripper closing/closed (j5 <= J5_OPEN_TH): GRASP/LIFT regime -- commit, never re-open or re-approach
    if j5 > 0.25:                                         # keep closing gently, holding the grasp pose
        return np.array([cx, cy, grasp_z, max(J5_GRIP, j5 - 0.2)])    # (claws STALL ~0.18 on the cube)
    return np.array([cx, cy, carry_z, J5_GRIP])           # firm grip -> LIFT


def run_combined(sim, body, viz, CAM, episodes=12, cmd_fixed=None, force=None, perceive_fn=None,
                 mixed=False, track_fn=None, lifelong=False, log_fn=None, policy_fn=None,
                 episode_end_fn=None, cap=CAP, teacher_log_fn=None, goal_fn=None, place_servo_fn=None,
                 ood_rate=0.0, ood_rng=None, tol=None, carry_target_fn=None,
                 post_goal_fn=None, macro_log_fn=None, servo=False, rescatter=True, orient_fn=None,
                 ziel_nachsehen_fn=None, objekt_sehen_fn=None,
                 carry_gentle=False, grip_close=None, wrist_fn=None, arm_reset=True, policy_log_fn=None):
    """If perceive_fn is given it is called per episode (arm parked, scene visible) and must
    return (cube_xy, target_xy) as PERCEIVED (e.g. from the camera) — the cube position is used
    for the grasp approach, the target for the place, instead of the privileged sim values.
    Closes the perception->action loop.  (target_xy may be None to keep the given target.)"""
    rng = np.random.default_rng(int(os.environ.get("ACT16_SEED", "1")))
    gclose = J5_GRIP if grip_close is None else float(grip_close)   # the GRIP close-angle the claws hold at.
    #   J5_GRIP=0.0 = full-close: against a RIGID object the claws stall at the object's width and hold with a
    #   force proportional to how far that width is from fully-closed -> a WIDE object (perceived U gripped
    #   across its ~42mm prong span) is squeezed with large force and squirts OUT.  A wider gclose for a wide
    #   grip holds it without crushing.  Caller passes grip_close from the PERCEIVED shape.
    tol = TOL if tol is None else float(tol)             # delivery tolerance (enlargeable target)
    _tm = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, "target_marker")
    if _tm >= 0:                                          # show the disk at the scoring tolerance radius
        sim.m.geom_size[sim.m.body_geomadr[_tm]][0] = tol
    STRAY_LO, STRAY_HI = REACH_XY[0] - 0.03, REACH_XY[1] + 0.03   # valid table area (patch + margin)

    def others(nm):
        return [o for o in OBJS if o != nm]

    def clear(p, names, gap):
        return all(np.linalg.norm(p - sim.obj_pos(o)[:2]) > gap for o in names)

    def geom_half(nm):                               # the object's ACTUAL half-extents (cube/wide/OOD)
        bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)
        return sim.m.geom_size[sim.m.body_geomadr[bid]].copy()

    obj_wide = {}                                    # object affordance: wide block (push) vs cube (grasp)

    def scatter():
        pts = []
        for nm in OBJS:
            wide = mixed and (rng.random() < 0.5)            # mixed cube/wide types only when asked
            obj_wide[nm] = wide
            half = WIDE_HALF if wide else CUBE_HALF
            sim.set_object_size(nm, half)
            p = _rand_xy(rng)
            while any(np.linalg.norm(p - q) < 0.08 for q in pts) or np.linalg.norm(p) < BASE_CLEAR:
                p = _rand_xy(rng)                            # (#1) clear of other objects AND off the base
            pts.append(p); sim.set_object(nm, p, z=float(half[2]))
        mujoco.mj_forward(sim.m, sim.d); sim.step(150)

    def reposition_strays():
        """Any cube that wandered out of the valid area is dropped back inside (clear of others)."""
        moved = False
        for nm in OBJS:
            p = sim.obj_pos(nm)[:2]
            if np.any(p < STRAY_LO) or np.any(p > STRAY_HI):
                q = _rand_xy(rng)
                while not clear(q, others(nm), 0.06):
                    q = _rand_xy(rng)
                sim.set_object(nm, q); moved = True
        if moved:
            mujoco.mj_forward(sim.m, sim.d); sim.step(80)

    if PERSIST and rescatter:        # rescatter=False -> reuse the scene already on the table (e.g. the
        sim.reset_home(); scatter()  #   command interface places it ONCE at startup, keeps it across commands)
    n_grasp = n_push = deliveries = 0; perr_sum = perr_n = terr_sum = terr_n = 0.0
    dec_ok = dec_n = 0; grasp_ok = grasp_tot = push_ok = push_tot = 0
    base_ok = base_n = ood_ok = ood_n = 0                    # generalization-probe split
    narrow_ok = narrow_n = wide_ok = wide_n = 0              # affordance split: grasp narrow / push wide
    if ood_rate > 0 and ood_rng is None:
        ood_rng = np.random.default_rng(123)
    for ep in range(episodes):
        if PERSIST:
            if arm_reset:                        # arm_reset=False: the caller DRIVES the arm back to (near)
                sim.arm_home()                   #   home after each episode (act23 drive_home) -- continuous
            reposition_strays()                  #   operation, no qpos snap (a physical robot can't teleport)
        else:
            sim.reset_home(); scatter()
        sim.target("joint_3", HOME["joint_3"]); sim.target("joint_5", J5_OPEN)
        cmd = cmd_fixed(ep) if callable(cmd_fixed) else (cmd_fixed or OBJS[ep % len(OBJS)])               # cycle which cube to fetch
        # SCENE DENSITY: place SCENE_N objects (the commanded one + distractors); park the rest off-table
        keep = [cmd] + list(rng.choice(others(cmd), max(0, min(SCENE_N - 1, len(OBJS) - 1)), replace=False))
        for i, o in enumerate([o for o in OBJS if o not in keep]):
            sim.set_object(o, np.array([0.55 + 0.06 * i, 0.55]))   # parked far off-camera + out of reach
        if ELONG_CMD:                                        # COMMAND an elongated (2:1) object: orientation-grasp
            already = abs(geom_half(cmd)[0] - geom_half(cmd)[1]) > 1e-4   # test (step C) -- the net must perceive
            yaw = sim.obj_yaw(cmd) if (PERSIST and already) else float(rng.uniform(0, np.pi))   # the yaw and align
            sim.set_object_size(cmd, ELONG_HALF)             # the wrist to the SHORT axis.  Under PERSIST keep the
            sim.set_object(cmd, sim.obj_pos(cmd)[:2], z=float(ELONG_HALF[2]), yaw=yaw)   # shown yaw (what runs)
        # occasionally MIX IN an elongated (2:1) object -- a shape variation in the data (mostly cubes).
        # DISTRACTOR ONLY (never the commanded target): the cube-trained policy can't grasp an elongated
        # object across its short axis yet (the deferred orientation-grasp work) -- it would close the
        # claw early / on the wrong axis.  As a distractor it just adds shape variety for perception.
        distract = [o for o in keep if o != cmd]
        if ELONG_RATE > 0 and distract and float(rng.random()) < ELONG_RATE:
            eo = str(rng.choice(distract))
            sim.set_object_size(eo, ELONG_HALF)
            sim.set_object(eo, sim.obj_pos(eo)[:2], z=float(ELONG_HALF[2]), yaw=float(rng.uniform(0, np.pi)))
        mujoco.mj_forward(sim.m, sim.d); sim.step(40)
        c0 = sim.obj_pos(cmd)[:2]
        cmd_half = geom_half(cmd)                             # ACTUAL size (cube, or a mixed elongated block)
        ood_ep = ood_rate > 0 and float(ood_rng.random()) < ood_rate
        if ood_ep:                                            # GENERALIZATION PROBE: a NOVEL object for the
            fp = float(ood_rng.uniform(0.010, 0.015))         # VISUAL-recognition test — varied FOOTPRINT
            half = np.array([fp, fp, float(ood_rng.uniform(0.011, 0.013))])   # but ~CONSTANT height (≈cube)
            sim.set_object_size(cmd, half); sim.set_object(cmd, c0, z=float(half[2]))   # so the grasp height
            mujoco.mj_forward(sim.m, sim.d); sim.step(60); cmd_half = half             # stays as learned
            c0 = sim.obj_pos(cmd)[:2]
        obj_h = float(cmd_half[2])                            # object size for the SIZE-ADAPTIVE grasp
        obj_fp = float(np.min(cmd_half[:2]))                  # SHORT-axis half: graspable across the NARROWEST
        #   dimension (cube: =mean; elongated: the 12mm short axis -> graspable when the claw aligns to it)
        # (B) WRIST target: align the claw to the object's grip axis.  Elongated -> the SHORT axis (mod pi: a
        # rectangle has 180deg symmetry, the long axis is the WRONG grip, the finite-ish pads can't span 48mm);
        # cube -> ACT16_WRIST_TGT mod 90deg.  Uses privileged obj_yaw for now (perception = step C).
        elong = abs(cmd_half[0] - cmd_half[1]) > 1e-4
        if elong:
            if orient_fn is not None:                         # (C) PERCEIVED long axis -> grip the SHORT axis
                long_axis = orient_fn(cmd)                    # world-frame long-axis yaw (mod pi), or None
                if long_axis is not None:
                    wrist_tgt = float(long_axis) + np.pi / 2
                else:                                         # perception failed -> fall back to privileged
                    wrist_tgt = sim.obj_yaw(cmd) + (np.pi / 2 if cmd_half[0] > cmd_half[1] else 0.0)
            else:                                             # privileged orientation (no perception)
                wrist_tgt = sim.obj_yaw(cmd) + (np.pi / 2 if cmd_half[0] > cmd_half[1] else 0.0)
            wrist_mod = np.pi
        else:
            wrist_tgt, wrist_mod = WRIST_TGT, np.pi / 2
        run_combined._wrist_tgt = float(wrist_tgt)            # expose the teacher's wrist target so a BC
        #   collector (act23) can log it as the 5th action dim (learn the wrist from the teacher).
        tgt_z = GRASP_Z                                      # ABLAGEHOEHE der Hand; s. goal_fn unten
        tgt = _rand_xy(rng)                                  # target: away from the cube, off any cube, off base
        while np.linalg.norm(tgt - c0) < 0.06 or not clear(tgt, OBJS, 0.05) or np.linalg.norm(tgt) < BASE_CLEAR:
            tgt = _rand_xy(rng)
        sim.set_target_marker(tgt); sim.step(40)
        tgt_true = tgt.copy(); cube_plan = None; mode_perc = None  # perceive cube + target + mode
        griff_z = GRASP_Z                                     # GREIFHOEHE der Hand; s. GRIFF_Z oben
        if perceive_fn:
            cube_plan, tgt_perc, mode_perc = perceive_fn(cmd)
            if cube_plan is not None and GRIFF_Z and len(np.asarray(cube_plan, float)) == 3:
                # DRITTER WERT = GREIFHOEHE.  Verhaltensneutral ohne Schalter (dann wird ein
                # dritter Wert gar nicht erst gelesen) und ohne dritten Wert.
                griff_z, cube_plan = float(np.asarray(cube_plan, float)[2]), np.asarray(cube_plan, float)[:2]
            if cube_plan is not None:
                cube_plan = np.asarray(cube_plan, float)[:2]
                perr_sum += float(np.linalg.norm(cube_plan - sim.obj_pos(cmd)[:2])); perr_n += 1
            if tgt_perc is not None:
                terr_sum += float(np.linalg.norm(tgt_perc - tgt_true)); terr_n += 1; tgt = tgt_perc
            if mode_perc is not None:                             # affordance decision correctness
                ideal = "push" if obj_wide.get(cmd, False) else "grasp"
                dec_ok += int(mode_perc == ideal); dec_n += 1
        if goal_fn is not None:                               # PLANNER dreams the place target from the
            obj_xy = cube_plan if cube_plan is not None else sim.obj_pos(cmd)[:2]   # perceived object
            tgt = np.asarray(goal_fn(cmd, obj_xy), float)     # -> commit to it (and SCORE against it)
            # DIE DRITTE ZIELDIMENSION (Stufe 2 von wiki/fragen/stapeln-als-aufgabe.md).
            # goal_fn darf DREI Werte liefern: dann ist der dritte die ABLAGEHOEHE der Hand.
            # Bisher war sie die Konstante GRASP_Z -- die Policy konnte "lass hoeher los" gar nicht
            # ausdruecken, und damit war Stapeln nicht nur ungelernt, sondern unsagbar.
            # VERHALTENSNEUTRAL: ohne Schalter oder ohne dritten Wert bleibt tgt_z = GRASP_Z.
            if GOAL_Z and len(tgt) >= 3:
                tgt_z, tgt = float(tgt[2]), tgt[:2]
            elif len(tgt) >= 3:
                tgt = tgt[:2]
            for _ in range(8):                                # SANITIZE the dreamed goal: off objects + base
                moved = False
                for o in (OBJS if ZIEL_SAEUBERN else ()):     # (#3) push it OFF any object it landed on
                    dv = tgt - sim.obj_pos(o)[:2]; dn = float(np.linalg.norm(dv))
                    if dn < 0.05:
                        tgt = sim.obj_pos(o)[:2] + (dv / dn if dn > 1e-6 else np.array([1.0, 0.0])) * 0.05
                        moved = True
                d = float(np.linalg.norm(tgt))                # (#1) keep it off the base
                if d < BASE_CLEAR:
                    tgt = tgt * (BASE_CLEAR / d) if d > 1e-6 else np.array([0.0, BASE_CLEAR]); moved = True
                if not moved:
                    break
            tgt_true = tgt.copy(); sim.set_target_marker(tgt); sim.step(20)   # also moves the visible marker
        if post_goal_fn is not None:                          # now the COMMITTED goal is known: e.g. drop an
            obj_now = cube_plan if cube_plan is not None else sim.obj_pos(cmd)[:2]   # obstacle on the carry path
            post_goal_fn(cmd, obj_now, tgt_true)              # (placed AFTER the goal so it can clear both ends)
        mode = (force(cmd) if callable(force) else force) or mode_perc or "grasp"
        phase = "over" if mode == "grasp" else "approach"
        dwell = 0; via = "grasp"; done = False; grasp_retry = 0
        run_combined._nachsehen = None                        # s. ZIEL NOCHMAL ANSCHAUEN
        run_combined._objsicht = None                         # s. DAS OBJEKT IN DER HAND ANSCHAUEN
        _hand_versatz = np.zeros(2)                           # Objekt minus Hand, gesehen (Vorgabe: 0)
        _luft_fertig = False                                  # s. LUFT_H
        _pruef_n = 0                                          # s. PRUEF_TOL
        _absetzen = False                                     # s. PRUEF_ABSETZEN
        run_combined._pruef = []
        # closed-loop grasp-target BELIEF: starts at the up-front perception, then the live fovea
        # CORRECTS it each frame (precision-weighted, occlusion-gated) instead of freezing the snapshot
        obj_belief = (cube_plan.copy() if cube_plan is not None else None) if servo else None
        servo_lost = 0; reacquires = 0; hover = 0            # (#4) grasp-reflex hover counter
        wrist_hold = None                                    # last aligned joint_4 (held through the grip)
        guard_minz = 1.0; guard_stall = 0                    # close-guard: deepest descent + stall counter
        run_combined._rule = {"schritte": 0, "reflex": 0, "reflex_wuerde": 0,
                              "riegel": 0, "riegel_wuerde": 0}   # RIEGEL-DIAGNOSE (s. RULEDIAG)
        run_combined._glaub = {"n": 0, "wahrn": 0.0, "orts": 0.0, "orts_max": 0.0,   # GLAUBENS-DIAGNOSE
                               "hoehe": 0.0, "phantom": 0, "phantom_ab": None,
                               "anfahrt": 0, "anfahrt_orts": 0.0,
                               "a1": 0, "a1_orts": 0.0, "a1_offen": True}
        run_combined._ablenk = {"n": 0, "fremd": 0, "ab": None, "wer": {},   # ABLENKER-DIAGNOSE
                                "d_eigen": 0.0, "d_fremd": 0.0, "zuletzt_fremd": False}
        run_combined._tast = {"n": 0, "stall_h": None, "stall_p": None,   # TASTSINN-DIAGNOSE
                              "close_h": None, "close_p": None, "p_max_offen": 0.0,
                              "min_h": None, "wunsch": [], "gesenkt": 0}
        last_phase = phase; phase_age = 0                    # STALL-ESCAPE: don't hang in one phase forever
        run_combined._cobs = None; run_combined._held_prev = False   # beobachtbare Objektschaetzung (Stufe C)
        run_combined._lift_xy = None                         # Handposition beim ABHEBEN (Trage-Etikett)
        run_combined._maxcz = float(obj_h)                   # CHECKPOINTS (act23 credit routing): three
        run_combined._slipped = False                        #   self-measurable predictions per episode.
        run_combined._attempted = False
        run_combined._inclaw = None                          # (quer, tief) mm des Objekts relativ zur
        #   Backenmitte beim Zufassen; None = die Klaue hat nie tief am Objekt geschlossen
        run_combined._release = None       # release snapshot (see the step loop)
        run_combined._oeffnen = None       # Schnappschuss im ECHTEN Moment des Oeffnens (FSM), s. unten
        run_combined._tast = None          # Tast-Ergebnis der Ablage (s. TASTEN)
        run_combined._grip = {}            # Fingerdruck-Streifen: Messreihe JE PHASE (N).
        #   Ein realer Streifen liefert durchgehend -- also wird er auch durchgehend aufgezeichnet und
        #   nach Phase getrennt ausgewertet.  Der reine Spitzenwert ueber die Episode trennte Erfolg
        #   von Misserfolg NICHT (gemessen 45 Ep: 6.7 vs 8.1 N, p=0.43), weil er nur sagt DASS die
        #   Klaue gedrueckt hat, nicht ob sie GEHALTEN hat -- gescheiterte Griffe drueckten sogar am
        #   festesten (11.0 N: schief eingeklemmt und weggeschoben).  Die Frage "haelt der Griff" ist
        #   eine Frage ueber ZEIT, also braucht es den Verlauf: fest zufassen (close), Last uebernehmen
        #   (lift), sie halten (carry), sauber loesen (release).
        #   _maxcz = highest the object rose (GRASP checkpoint: did the grasp actually happen?).
        #   _slipped = while carried, did the object SEPARATE from the hand (CARRY checkpoint: did the
        #   grip hold?).  _attempted = the claw CLOSED low AT the believed object while it still sat on
        #   the table -- the choreography ARRIVED and gripped; if the object then never lifts, the
        #   ACTION (wrist/grip geometry) failed, not the aim.  Without this the not-lifted route always
        #   abstained and a grasp-preventing wrist could NEVER be disconfirmed (measured: the world
        #   model froze on wrist 112deg for the L, 0/29 across probes, LCB never updated).  Together
        #   they route the outcome to the learner whose prediction broke: never arrived -> choreography
        #   (policy); closed at the object + no lift OR slip -> the world-model action; held but
        #   off-goal -> the place aim (policy).
        for k in range(cap):
            phase_age = phase_age + 1 if phase == last_phase else 0
            last_phase = phase
            if phase_age > PHASE_STALL:                       # stuck (e.g. can't reach the believed object)
                break                                         # -> give up this episode instead of looping
            c_true = sim.obj_pos(cmd)[:2]; cz = sim.obj_pos(cmd)[2]; h = sim.grasp_pos(); hxy = h[:2]; hz = h[2]
            if cz > run_combined._maxcz:
                run_combined._maxcz = float(cz)
            if cz > obj_h + 0.02 and float(np.linalg.norm(c_true - hxy)) > 0.045:
                run_combined._slipped = True                 # lifted but the object is far from the claw
            # ZIEL NOCHMAL ANSCHAUEN (ziel_nachsehen_fn, s. ACT23_ZIEL_NACHSEHEN).  Das Ziel wird zu
            # Beginn EINMAL gesehen und dann festgehalten (wiki/fragen/aufmerksamkeit-objekt-ziel.md).
            # Hier schaut der Agent ein zweites Mal hin: EINMAL, sobald er das Objekt traegt und die
            # Hand in NACHSEH_R um das Ziel steht -- also aus der Naehe, kurz vor dem Ablegen.
            # Liefert der Blick ein Ziel, wird es das neue Ziel der Episode: Steuerung, Ziel-Latent
            # (post_goal_fn) und Wertung, genau wie beim ersten Blick.
            if (ziel_nachsehen_fn is not None and run_combined._nachsehen is None
                    and cz > obj_h + 0.014 and sim.d.qpos[sim.jqadr["joint_5"]] < J5_CLOSED_TH
                    and float(np.linalg.norm(hxy - tgt_true)) < NACHSEH_R):
                _g2 = ziel_nachsehen_fn()
                run_combined._nachsehen = {"alt": tgt_true.copy(), "neu": None}
                if _g2 is not None:
                    _g2 = np.asarray(_g2, float)[:2]
                    run_combined._nachsehen["neu"] = _g2.copy()
                    tgt = _g2.copy(); tgt_true = _g2.copy()
                    if post_goal_fn is not None:
                        post_goal_fn(cmd, c_true, tgt_true)
            # DAS OBJEKT IN DER HAND ANSCHAUEN (objekt_sehen_fn, s. ACT23_OBJ_SEHEN).  Beim Tragen gilt
            # die Objektlage als GLEICH der Hand (s. _cobs unten) -- gemessen liegt es beim Loslassen
            # aber 12-16 mm daneben, und genau das landet in der Ablage, weil der Teacher die HAND zum
            # Ziel bringt (wiki/fragen/aufmerksamkeit-objekt-ziel.md).  EINMAL, zur selben Zeit wie der
            # zweite Blick aufs Ziel: der Versatz Objekt-minus-Hand wird gesehen und protokolliert;
            # nur mit ACT16_OBJ_VERSATZ=1 fuehrt er die Hand so, dass das OBJEKT aufs Ziel kommt.
            if (objekt_sehen_fn is not None and run_combined._objsicht is None
                    and cz > obj_h + 0.004 and sim.d.qpos[sim.jqadr["joint_5"]] < J5_CLOSED_TH
                    and float(np.linalg.norm(hxy - tgt_true)) < NACHSEH_R
                    and (OBJSICHT_Z <= 0.0 or hz < OBJSICHT_Z)):
                _gs = objekt_sehen_fn(hxy, float(hz))
                run_combined._objsicht = {"hand": hxy.copy(), "hz": float(hz), "wahr": c_true.copy(),
                                          "gesehen": None if _gs is None else np.asarray(_gs, float)[:2].copy()}
                if _gs is not None and OBJ_VERSATZ:
                    _hand_versatz = np.asarray(_gs, float)[:2] - hxy
            tgt_eff = tgt                                     # routed carry target (obstacle): once the
            if carry_target_fn is not None and cz > 0.03:     # object is lifted, follow the planned route
                _wp = carry_target_fn(hxy, tgt_true)          # AROUND the perceived board instead of going
                if _wp is not None:                           # straight to the goal (goal still used for done)
                    tgt_eff = np.array([_wp[0], _wp[1]], float)
            # FOLLOW the object live while approaching it; when it is occluded (gripper over it)
            # the tracker returns None and we keep the last estimate (memory) — the act11 pattern.
            if track_fn is not None and k % 4 == 0:           # follow live: drives the gaze + viz +
                tr = track_fn()                              # lifelong net learning, and SHOWS the
                #   real-view occlusion.  WITHOUT servo it does NOT overwrite the grasp estimate (the
                #   agent acts on the clean up-front perception as MEMORY, the act11 pattern).  WITH
                #   servo the SAME observation CLOSES THE LOOP: it corrects the grasp-target belief.
                if servo and obj_belief is not None and isinstance(tr, tuple) \
                        and phase in ("over", "lower"):
                    obs, conf = tr
                    if obs is not None and conf >= SERVO_CONF:          # confident view -> correct
                        obj_belief = obj_belief + SERVO_K * conf * (np.asarray(obs, float) - obj_belief)
                        servo_lost = 0
                    else:                                              # lost it (occluded/weak)
                        servo_lost += 1
                        if servo_lost >= SERVO_LOST and perceive_fn is not None and reacquires < MAX_REACQ:
                            fresh, _, _ = perceive_fn(cmd)             # saccadic RE-ACQUIRE ("stochern")
                            # DERSELBE DRITTE WERT WIE OBEN.  perceive_fn darf mit ACT16_GRIFF_Z
                            # eine Greifhoehe mitliefern; dieser Pfad hat sie nicht abgeschnitten
                            # und der Vergleich mit einer 2er-Lage brach die Episode ab.  Die
                            # Hoehe wird hier NICHT neu gesetzt: sie gilt fuer die Episode, und
                            # ein Wiederfinden mitten im Griff soll sie nicht verschieben.
                            if fresh is not None:
                                fresh = np.asarray(fresh, float)[:2]
                            if fresh is not None:
                                obj_belief = np.asarray(fresh, float)
                            servo_lost = 0; reacquires += 1           # bounded: then hold the belief
            # grasp approach aims at the BELIEF (servo: live-corrected) or the frozen perception;
            # the true position is used once the cube is grabbed / for the fallback and the measure.
            grasp_src = obj_belief if (servo and obj_belief is not None) else cube_plan
            c = grasp_src if (grasp_src is not None and phase in ("over", "lower", "close")) else c_true
            if (not run_combined._attempted and cz < obj_h + 0.02
                    and float(np.linalg.norm(hxy - c_true)) < 0.03
                    and hz < obj_h + GRASP_OFFSET + 0.02
                    and sim.d.qpos[sim.jqadr["joint_5"]] < J5_CLOSED_TH):
                run_combined._attempted = True                # claw closed low AT the object, object still
                if run_combined._inclaw is None:              # LAGE IN DER KLAUE im Moment des
                    try:                                      #   Zufassens (nur beim ERSTEN Mal, s.
                        run_combined._inclaw = sim.in_claw(c_true)   # pc_act14.in_claw)
                    except Exception:
                        run_combined._inclaw = None
                #                                               down -> the grasp was TESTED (see header)
            if via == "push" and np.linalg.norm(c - tgt) < tol:  # pushed home -> done
                break
            if policy_fn is not None and np.linalg.norm(c_true - tgt_true) < tol and cz < 0.035:
                break                                            # learned policy: object placed -> done
            d = tgt - c; n = np.linalg.norm(d); d = d / n if n > 1e-6 else np.array([1.0, 0.0])

            if mode == "grasp":
                via = "grasp"
                if phase == "over":
                    j5, aim = J5_OPEN, np.array([c[0], c[1], OVER_Z])
                    if np.linalg.norm(hxy - c) < NEAR:
                        phase = "lower"
                elif phase == "lower":
                    j5, aim = J5_OPEN, np.array([c[0], c[1], griff_z])
                    if hz < griff_z + 0.010:
                        phase, dwell = "close", 0
                elif phase == "close":
                    dwell += 1                                    # close SLOWLY (ramp) so the
                    frac = min(1.0, dwell / 60.0)                 # claws don't shove the cube
                    j5 = J5_OPEN + (gclose - J5_OPEN) * frac
                    aim = np.array([c[0], c[1], griff_z])
                    if dwell > 90:
                        phase = "lift"
                elif phase == "lift":
                    j5, aim = gclose, np.array([hxy[0], hxy[1], CARRY_Z])
                    if hz > CARRY_Z - 0.015:
                        if cz > 0.030:                            # cube clearly lifted off the table
                            phase = "carry"                      # grasped!
                        elif obj_fp <= GRASP_MAX_HALF and grasp_retry < 2:
                            grasp_retry += 1; phase = "over"      # narrow: RETRY the grasp (no push-to-foot)
                        else:
                            mode, phase = "push", "approach"      # wide / retries spent -> push fallback
                elif phase == "carry":
                    j5, aim = gclose, np.array([tgt_eff[0], tgt_eff[1], CARRY_Z])   # via the routed waypoint
                    if np.linalg.norm(hxy - tgt_true) < SENK_NAH:   # s. NEAR_ABLAGE, SENK_NAH
                        phase, dwell = "place", 0
                elif phase == "place":
                    # ABLAGEHOEHE: tgt_z statt der Konstanten GRASP_Z.  Ohne dritten Wert aus
                    # goal_fn ist tgt_z == GRASP_Z, und diese Zeilen sind Zeichen fuer Zeichen die alten.
                    if not TASTEN:
                        # OBJEKT AUFS ZIEL, NICHT DIE HAND (ACT16_OBJ_VERSATZ): ist der Versatz
                        # Objekt-minus-Hand gesehen, wird die Hand um ihn verschoben, und losgelassen
                        # wird erst, wenn die verschobene Stelle erreicht ist (hoechstens OBJ_WARTE
                        # Schritte, dann wie bisher).  Ohne gesehenen Versatz ist _hand_versatz = 0 und
                        # die Zeilen sind die alten.
                        _zh = np.asarray(tgt, float) - _hand_versatz
                        j5, aim = gclose, np.array([_zh[0], _zh[1], tgt_z])
                        dwell += 1
                        if LUFT_H > 0.0 and not _luft_fertig:     # s. LUFT_H: erst oben ankommen
                            aim = np.array([_zh[0], _zh[1], tgt_z + LUFT_H])
                            if ((objekt_sehen_fn is None or run_combined._objsicht is not None)
                                    and float(np.linalg.norm(hxy - _zh)) < NEAR_ABLAGE
                                    or dwell > OBJ_WARTE):
                                _luft_fertig = True
                                if run_combined._objsicht is not None:
                                    run_combined._objsicht["luft"] = {"dwell": dwell, "hz": float(hz)}
                        _da = ((not np.any(_hand_versatz) and SENK_NAH <= NEAR_ABLAGE)
                               or dwell > OBJ_WARTE
                               or float(np.linalg.norm(hxy - _zh)) < NEAR_ABLAGE)
                        if _absetzen and (LUFT_H <= 0.0 or _luft_fertig):   # s. PRUEF_ABSETZEN
                            aim = np.array([aim[0], aim[1], tgt_z - 0.003])
                        _frei = (hz < (tgt_z + 0.004 if _absetzen and dwell <= OBJ_WARTE else tgt_z + 0.012)
                                 and _da and (LUFT_H <= 0.0 or _luft_fertig))
                        if (_frei and PRUEF_TOL > 0.0 and objekt_sehen_fn is not None
                                and _pruef_n < PRUEF_N):
                            # VOR DEM OEFFNEN HINSCHAUEN (s. PRUEF_TOL)
                            _gp = objekt_sehen_fn(hxy, float(hz))
                            _pruef_n += 1
                            _eintrag = {"gesehen": None if _gp is None else np.asarray(_gp, float)[:2].copy(),
                                        "wahr": c_true.copy(), "tgt": np.asarray(tgt, float).copy(),
                                        "nach": False}
                            if _gp is not None and float(np.linalg.norm(np.asarray(_gp, float)[:2] - tgt)) > PRUEF_TOL:
                                _hand_versatz = np.asarray(_gp, float)[:2] - hxy
                                dwell = 0; _frei = False; _eintrag["nach"] = True
                                _absetzen = PRUEF_ABSETZEN
                                if LUFT_H > 0.0:
                                    _luft_fertig = False
                            run_combined._pruef.append(_eintrag)
                        if _frei:
                            if run_combined._objsicht is not None:   # Diagnose, s. ACT23_OBJ_SEHEN
                                run_combined._objsicht["los"] = {"hand": hxy.copy(), "wahr": c_true.copy(),
                                                                 "zh": _zh.copy(), "dwell": dwell}
                            phase, dwell = "release", 0
                    else:
                        # ERTASTEN (s. TASTEN oben): TAST_TIEF unter die Schaetzung zielen und
                        # anhalten, sobald die Hand nicht mehr sinkt, obwohl sie es soll.  Die
                        # Hoehe, bei der sie stehen bleibt, ist die Aufsetzhoehe -- das Etikett.
                        _zt = tgt_z - TAST_TIEF
                        j5, aim = gclose, np.array([tgt[0], tgt[1], _zt])
                        _st = run_combined._tast
                        if _st is None:
                            _st = run_combined._tast = {"hz_vor": float(hz), "still": 0,
                                                        "hz_kontakt": None, "tgt_z": float(tgt_z),
                                                        "hz_min": float(hz), "still_max": 0,
                                                        "sink_min": 9.9, "schritte": 0}
                        _st["schritte"] += 1
                        _st["hz_min"] = min(_st["hz_min"], float(hz))
                        # SINKT SIE NOCH?  Verglichen wird die GEFUEHLTE Handhoehe mit sich selbst,
                        # nicht mit dem Befehl -- ein Stillstand bei noch tieferem Ziel heisst
                        # Widerstand.  Erst ueber TAST_N Schritte, damit ein einzelner ruhiger
                        # Regelschritt nicht als Beruehrung durchgeht.
                        _sink = _st["hz_vor"] - hz
                        # NUR IM TASTFENSTER HORCHEN.  Die Ablagephase beginnt, sobald die Hand
                        # seitlich am Ziel ist -- sie kann dann noch zentimeterweit darueber
                        # stehen, und JEDER Stillstand auf dem Weg nach unten galt als Beruehrung.
                        # GEMESSEN (20 Tastwerte): dadurch lagen einzelne Etiketten bis +17,9 mm
                        # daneben, die Streuung war 5,79 mm bei einem Median von +0,40 -- und
                        # dieses Rauschen halbierte die Genauigkeit des Lerners (87 -> 53 %
                        # richtige Stufe auf denselben Sondenzeilen).  Das Fenster ist symmetrisch
                        # um die Schaetzung: so weit, wie sie selbst danebenliegen kann.
                        _im_fenster = hz < _st["tgt_z"] + TAST_TIEF
                        if not _im_fenster:
                            _st["still"] = 0
                        if _im_fenster and hz > _zt + TAST_RAND:
                            _st["sink_min"] = min(_st["sink_min"], float(_sink))
                        if _im_fenster and hz > _zt + TAST_RAND and _sink < TAST_STILL:
                            if _st["still"] == 0:
                                # DIE HOEHE BEIM BEGINN DES STILLSTANDS ist die Aufsetzhoehe --
                                # nicht die am Ende des Fensters.  Gemessen: waehrend der TAST_N
                                # Bestaetigungsschritte kriecht die Hand noch bis zu TAST_N *
                                # TAST_STILL weiter (je Schritt unter der Schwelle, in Summe
                                # nicht), und das las die Oberkante systematisch 0 bis 4 mm ZU
                                # TIEF.  Der Beginn ist der Augenblick der Beruehrung, das Ende
                                # nur der Augenblick, in dem ich ihr glaube.
                                _st["hz_still0"] = float(hz + _sink)
                            _st["still"] += 1
                        else:
                            _st["still"] = 0
                        _st["still_max"] = max(_st["still_max"], _st["still"])
                        _st["hz_vor"] = float(hz)
                        if _st["still"] >= TAST_N:
                            _st["hz_kontakt"] = float(_st["hz_still0"])   # AUFGESETZT -- die Messung
                            _st["z_rel"] = float(hz)                      # losgelassen wird HIER
                            phase, dwell = "release", 0
                        elif hz < _zt + TAST_RAND:
                            _st["z_rel"] = float(hz)           # durchgetastet ohne Widerstand
                            phase, dwell = "release", 0
                        # `tgt_z` wird NICHT angefasst.  Es ist das ZIEL, steht (mit ACT16_GOAL_Z)
                        # im Zustandsvektor der Policy und labelt ueber reactive_subgoal die
                        # DAgger-Zeilen.  Es mitten in der Episode zu verschieben hiesse, den
                        # Lernstoff mit dem Tastergebnis zu vermischen -- die Ablagehoehe stuende
                        # dann in den Etiketten schon, bevor der Schaetzer sie gelernt hat.
                else:  # release
                    if SOFT_RELEASE:
                        dwell += 1
                        frac = min(1.0, dwell / 40.0)         # open SLOWLY (the mirror of the close ramp:
                        j5 = gclose + (J5_OPEN - gclose) * frac   # an instant snap-open FLICKS the placed
                        _zr0 = tgt_z
                        if TASTEN and run_combined._tast is not None:
                            _zr0 = float(run_combined._tast.get("z_rel", tgt_z))
                        zr = _zr0 if dwell <= 40 else OVER_Z   # object); then retreat UP already open
                        aim = np.array([tgt[0], tgt[1], zr])
                        if dwell > 65:
                            break
                    else:
                        _zr0 = tgt_z
                        if TASTEN and run_combined._tast is not None:
                            _zr0 = float(run_combined._tast.get("z_rel", tgt_z))
                        j5, aim, dwell = J5_OPEN, np.array([tgt[0], tgt[1], _zr0]), dwell + 1
                        if dwell > 50:
                            break
            else:  # PUSH: get behind the object (OVER it, since the arm can't go through), push
                via = "push"
                behind = c - d * STANDOFF
                if phase == "approach":                          # move behind the object, raised
                    j5, aim = J5_PUSH, np.array([behind[0], behind[1], PUSH_LIFT_Z])
                    if np.linalg.norm(hxy - behind) < NEAR:
                        phase = "pdown"
                elif phase == "pdown":                           # lower the claws behind it
                    j5, aim = J5_PUSH, np.array([behind[0], behind[1], PUSH_Z])
                    if hz < PUSH_Z + 0.012:
                        phase = "push"
                else:                                            # push the object toward the target
                    ahead = c + d * 0.02
                    j5, aim = J5_PUSH, np.array([ahead[0], ahead[1], PUSH_Z])
                    if np.dot(hxy - c, d) > 0.025 or np.linalg.norm(hxy - c) > 0.08:
                        phase = "approach"

            if place_servo_fn is not None:                    # (b) LATENT-DIFFERENCE place: while the
                if cz > 0.028 and sim.d.qpos[sim.jqadr["joint_5"]] < J5_CLOSED_TH:   # object carried, drive
                    tgt = np.asarray(place_servo_fn(hxy), float)  # the place target by the latent servo
            # state for a LEARNED action policy: hand, object, object-z, target, gripper, OBJ SIZE (c)
            # + TASTSINN [gueltig, druck_N] (2026-08-07): der Fingerdruck-Streifen als LAUFZEIT-Eingang.
            # Gemessen: Druck beim Zufassen sagt das Halten fast deterministisch vorher (<0.5N -> 4%,
            # >2N -> 86%), und die Verluste passieren beim Heben/Tragen -- wo die Kamera das Objekt
            # unter dem Greifer verliert und bisher nur das PRIVILEGIERTE cz den Verlust verriet.
            # Auf dem realen Roboter existiert cz nicht; der Streifen ist die geplante Hardware.
            try:
                press = float(sim.grip_pressure("left"))
            except Exception:
                press = -1.0                                   # Sensor nicht lesbar -> gueltig=0
            _j5q = float(sim.d.qpos[sim.jqadr["joint_5"]])
            # STUFE C (ACT16_OBS_STATE=1): BEOBACHTBARE Objektschaetzung fuer den Policy-Zustand.
            # Das privilegierte c_true/cz stand bisher auch WAEHREND DES TRAGENS im Zustand -- auf dem
            # realen Roboter existiert es nicht, und die Kamera sieht das Objekt unter dem Greifer
            # nicht.  Beobachtbarer Ersatz, rein aus Belief + TASTSINN:
            #   haelt (Druck>0.3N, Klaue zu)  -> Objekt IST an der Hand: c_obs=hand_xy, cz_obs=hand_z
            #   Anfahrphasen                  -> c ist dort ohnehin der Fovea-Belief (beobachtbar)
            #   Verlust (haelt -> haelt nicht)-> Objekt fiel WO DIE HAND WAR: c_obs friert dort ein,
            #                                    cz_obs = Ruhehoehe obj_h (es liegt wieder auf dem Tisch)
            # Die FSM selbst faehrt weiter mit dem Privileg (Teacher = Trainingssignal); nur was die
            # POLICY sieht -- und was als Demo-Zustand GELOGGT wird -- wechselt auf beobachtbar.
            _holding = press > 0.3 and _j5q < J5_CLOSED_TH
            if run_combined._cobs is None or phase in ("over", "lower", "close"):
                run_combined._cobs = (np.asarray(c, float).copy(), float(obj_h))
            if _holding:
                run_combined._cobs = (np.asarray(hxy, float).copy(), float(hz))
            elif run_combined._held_prev:                       # eben verloren -> am Fallort einfrieren
                run_combined._cobs = (np.asarray(hxy, float).copy(), float(obj_h))
            run_combined._held_prev = _holding
            if OBS_STATE:
                c_st, cz_st = run_combined._cobs
            else:
                c_st, cz_st = c, cz                            # altes Verhalten (privilegiert im Carry)
            # DIE ABLAGEHOEHE als 14. Eingang (ACT16_GOAL_Z, s. oben).  Bisher stand hier NICHTS --
            # das Ziel war zweidimensional, und die Policy konnte "lass hoeher los" nicht einmal
            # ausdruecken.
            # KEIN GUELTIGKEITS-FLAG noetig, anders als beim Tastsinn: alte Zeilen bekommen bei der
            # Migration GRASP_Z, und das ist keine Erfindung, sondern was in ihren Episoden
            # tatsaechlich galt (die Ablagehoehe war bis hierhin diese Konstante).  Der Neutralwert
            # ist hier die Wahrheit, nicht eine Notluege.
            state = np.array([h[0], h[1], h[2], c_st[0], c_st[1], cz_st, tgt_eff[0], tgt_eff[1],
                              _j5q, obj_h, obj_fp,
                              1.0 if press >= 0 else 0.0, max(press, 0.0)]
                             # DIE ANORDNUNG MUSS EINDEUTIG SEIN.  Mit GRIFF_Z ohne GOAL_Z
                             # laege die GREIFhoehe auf Platz 14 -- genau dort, wo
                             # reactive_subgoal die ABLAGEhoehe liest.  Die Policy bekaeme die
                             # eine Groesse als die andere.  Deshalb zieht GRIFF_Z die
                             # Ablagespalte immer mit; ohne ACT16_GOAL_Z bleibt sie auf GRASP_Z
                             # stehen und ist damit verhaltensneutral.
                             + ([tgt_z] if (GOAL_Z or GRIFF_Z) else [])
                             + ([griff_z] if GRIFF_Z else []), float)
            if GLAUBDIAG:
                # GLAUBENS-DIAGNOSE: wo genau geht der Zustand kaputt, den die Policy sieht?
                # ZERLEGT in die drei Stellen, an denen er entstehen kann -- eine Gesamtabweichung
                # allein saehe bei allen dreien gleich aus:
                #   wahrn   |c - c_true|      die FOVEA-Schaetzung selbst (Wahrnehmung)
                #   orts    |c_st - c_true|   was am Ende IM ZUSTAND steht (nach der _cobs-Logik)
                #   phantom _holding, WAEHREND das Objekt laut Wahrheit noch auf dem Tisch liegt
                #           -> der Agent glaubt zu tragen und faehrt Ablage statt Griff.  Das ist die
                #           Kandidatenerklaerung fuer die dauerhaft 30-60 mm zu hohen Schliesswuensche.
                # PRIVILEGIERT und AUSSCHLIESSLICH Messung: c_true/cz gehen nirgends in einen
                # Lernenden, in keinen Zustand und in keine Entscheidung -- nur in diese Zaehler.
                _g = run_combined._glaub
                _g["n"] += 1
                _g["wahrn"] += float(np.linalg.norm(np.asarray(c, float) - c_true))
                _do = float(np.linalg.norm(np.asarray(c_st, float) - c_true))
                _g["orts"] += _do
                _g["orts_max"] = max(_g["orts_max"], _do)
                _g["hoehe"] += abs(float(cz_st) - float(cz))
                if _holding and cz < obj_h + 0.014:            # zu tragen geglaubt, liegt aber noch
                    _g["phantom"] += 1
                    if _g["phantom_ab"] is None:
                        _g["phantom_ab"] = _g["n"]
                if phase in ("over", "lower", "close"):
                    _g["anfahrt"] += 1
                    _g["anfahrt_orts"] += _do
                    # NUR DIE ERSTE ANFAHRT, bis zum ersten Schliesswunsch.  Danach ist der Wert
                    # WERTLOS als Ursache: eine gescheiterte Episode faehrt mehrfach an, und die
                    # spaeteren Anfahrten sehen ein Objekt, das der erste Fehlgriff schon
                    # angestossen hat -- der Ortsfehler waere dann FOLGE des Fehlschlags und nicht
                    # seine Ursache.  Ohne diese Trennung misst man die Richtung falsch herum.
                    if _g["a1_offen"]:
                        _g["a1"] += 1
                        _g["a1_orts"] += _do
                if _j5q < J5_OPEN_TH:
                    _g["a1_offen"] = False                     # ab hier: Klaue geschlossen gewesen
            if ABLENKDIAG and phase in ("over", "lower", "close"):
                # Auf WELCHEN Koerper zeigt der Belief `c`?  Nur waehrend der Anfahrt -- danach
                # traegt die Hand das Objekt und `c` folgt absichtlich der Hand (s. _cobs).
                _cb = np.asarray(c, float)
                _kand = [(float(np.linalg.norm(sim.obj_pos(_o)[:2] - _cb)), _o) for _o in OBJS]
                if _kand:
                    _dmin, _wer = min(_kand)
                    _de = float(np.linalg.norm(np.asarray(c_true, float) - _cb))
                    _ab = run_combined._ablenk
                    _ab["n"] += 1
                    _ab["d_eigen"] += _de
                    _ab["d_fremd"] += _dmin
                    _fremd = (_wer != cmd)
                    _ab["zuletzt_fremd"] = _fremd
                    if _fremd:
                        _ab["fremd"] += 1
                        _ab["wer"][_wer] = _ab["wer"].get(_wer, 0) + 1
                        if _ab["ab"] is None:
                            _ab["ab"] = _ab["n"]
            if teacher_log_fn is not None:                    # DAgger: the FSM's sub-goal at the
                teacher_log_fn(state, np.asarray(aim, float).copy(), float(j5))   # (policy-)VISITED state
            route_carry = carry_target_fn is not None and phase == "carry"   # the routed carry follows the
            # (act23) LEARNED wrist as a SEPARATE, overridable action: wrist_fn(state) -> desired world claw_yaw,
            # kept OUT of the aim policy (sharing one MLP made the wrist compete for capacity and degraded the
            # aim).  Decoupled, the wrist is independently learnable/planner-optimisable (stage 3).  Default None
            # -> the teacher's heuristic WRIST_ALIGN, exactly as before.
            policy_wrist = float(wrist_fn(state)) if wrist_fn is not None else None
            if policy_fn is not None and not route_carry:     # planned waypoints (FSM servo); the LEARNED
                out = policy_fn(state); aim = np.asarray(out[:3], float); j5 = float(out[3]); via = "policy"
                if policy_log_fn is not None:                  # SELF-IMITATION (act23 step 3): log the state
                    policy_log_fn(state, np.asarray(out, float))   # + the action the POLICY ITSELF drove
            elif route_carry:                                 # policy carries to a STATIC goal only, so it
                via = "route"                                 # cannot follow side-waypoints -> servo the route
            # (#4) GRASP REFLEX -- active-inference framing: once the hand is positioned OVER the object the
            # agent EXPECTS to be grasping; hovering OPEN + HIGH instead is a sustained prediction error that
            # drives a descend+close.  Fires ONLY on a stall (HOVER_LIMIT), so the learned policy still drives
            # normally -- this just guarantees the grasp EXECUTES instead of the policy hovering forever (#4).
            gz = obj_h + GRASP_OFFSET
            at_goal = np.linalg.norm(c - tgt) < tol and cz < 0.035   # object already RESTS at the goal --
            #   re-grasping it is a misfire in ANY flow (the "nachfassen" that shoved a delivered object)
            if (np.linalg.norm(hxy - c) < 0.03 and cz < 0.035 and j5 > J5_REFLEX_TH and hz > gz + 0.012
                    and not (SOFT_RELEASE and (at_goal or phase == "release"))):
                hover += 1
            else:
                hover = 0
            # RIEGEL-DIAGNOSE: die BEDINGUNG wird getrennt vom SCHALTER ausgewertet, damit der Zaehler
            # auch im Arm OHNE Regel sagt, wie oft sie gegriffen HAETTE.  Verhaltensneutral: bei
            # REFLEX/CLOSE_GUARD=1 ist der Ablauf Zeile fuer Zeile derselbe; bei =0 werden nur Zaehler
            # gefuehrt (guard_minz/guard_stall wirken ausschliesslich innerhalb dieses Blocks).
            run_combined._rule["schritte"] += 1
            if hover > HOVER_LIMIT:
                run_combined._rule["reflex_wuerde"] += 1
                if REFLEX:
                    run_combined._rule["reflex"] += 1
                    aim = np.array([c[0], c[1], gz]); j5 = max(J5_GRIP, j5 - 0.2); via = "reflex"
            if mode == "grasp" and cz < obj_h + 0.014:        # PROGRESS-aware close guard: keep the
                if hz < guard_minz - 0.0008:                  # claw OPEN while the hand is still DESCENDING toward
                    guard_minz = hz; guard_stall = 0          # the object (slow at the edges), so it does not close
                else:                                         # in the air -- BUT release once the descent STALLS
                    guard_stall += 1                          # (no downward progress) so a genuine stall still
                if TASTDIAG:
                    # HIER, VOR dem Riegel: j5 ist noch das, was Policy/Reflex WOLLEN.  Nach dem
                    # Riegel waere es sein Ergebnis, und die Frage "wann wollte sie schliessen"
                    # waere nicht mehr beantwortbar.
                    _t = run_combined._tast
                    _t["n"] += 1
                    _sinkt = hz < guard_minz - 0.0008          # eigener Abstieg -- propriozeptiv
                    # NUR IM ECHTEN ABSTIEG messen.  Die erste Fassung zaehlte jeden nicht-sinkenden
                    # Schritt als "Stillstand" -- auch den allerersten, als die Hand noch in Ruhelage
                    # stand.  Ergebnis waren 148 mm ueber dem Greifpunkt, also die Starthoehe des Arms,
                    # und nicht der gesuchte Aufsetzpunkt.  Ein Stillstand zaehlt erst, wenn die Hand
                    # (a) ueber dem Objekt steht und (b) vorher wirklich abgestiegen ist.
                    _t["gesenkt"] += 1 if _sinkt else 0
                    _ueber = float(np.linalg.norm(hxy - c)) < NEAR
                    if _ueber and (_t["min_h"] is None or hz - gz < _t["min_h"]):
                        _t["min_h"] = float(hz - gz)           # tiefster Punkt ueber dem Greifpunkt
                    if (_t["stall_h"] is None and _ueber and _t["gesenkt"] >= 20
                            and guard_stall >= 5):             # 5 Schritte ohne Fortschritt = aufgesetzt
                        _t["stall_h"] = float(hz - gz)
                        _t["stall_p"] = float(max(press, 0.0))
                    if j5 < J5_OPEN_TH:                        # JEDER Schliesswunsch, nicht nur der erste:
                        _t["wunsch"].append(float(hz - gz))    #   der Riegel faengt die Ausreisser, also
                        if _t["close_h"] is None:              #   sagt erst die Verteilung, was er leistet
                            _t["close_h"] = float(hz - gz)
                            _t["close_p"] = float(max(press, 0.0))
                    else:                                      # Druck, den der OFFENE Greifer schon spuert
                        _t["p_max_offen"] = max(_t["p_max_offen"], float(max(press, 0.0)))
                if hz > gz + 0.012 and guard_stall < HOVER_LIMIT:   # closes (the reflex) and never DEADLOCKS open
                    if j5 < J5_OPEN:                          # nur zaehlen, wenn die Klaue WIRKLICH
                        run_combined._rule["riegel_wuerde"] += 1   # aufgerissen wuerde -- sonst zaehlte
                        if CLOSE_GUARD:                       # man Schritte mit ohnehin offener Klaue mit
                            run_combined._rule["riegel"] += 1
                    if CLOSE_GUARD:
                        j5 = max(j5, J5_OPEN)
            else:
                guard_minz = 1.0; guard_stall = 0             # not in the grasp approach -> reset the tracker
            if log_fn is not None:                            # log the EXECUTED (state -> subgoal)
                log_fn(state, np.asarray(aim, float), float(j5))
            if macro_log_fn is not None:                      # EXECUTED step + the FSM phase (for macro
                macro_log_fn(state, np.asarray(aim, float), float(j5), phase)   # sub-goal segmentation)
            # RELEASE SNAPSHOT (measurement only, no behaviour): the FIRST step at which the claw re-opens
            # while the object is still LIFTED tells us how the placement actually ends -- released high
            # (object then FALLS and rolls) vs set down and let go.  The 120-ep run showed 27.5% "daneben
            # platziert" at a median of 34mm after a real 126mm carry, and the policy buffer says the place
            # branch aims 16mm too high; this separates "dropped from height" from "missed laterally".
            # Take the LAST step at which the claw still HELD the lifted object -- overwritten every such
            # step, so what survives is the instant before the release.  (A first-open trigger is wrong:
            # the claw sits above J5_CLOSED_TH for much of the carry anyway, so it fired at lift-off and
            # reported a constant 14mm "fall" = the lift threshold itself.)
            # DER ECHTE MOMENT DES OEFFNENS (Messung, 2026-09-28).  Der Schnappschuss darunter friert ein,
            # sobald das Objekt unter 14 mm ueber Ruhelage sinkt -- fuehrt die Hand unten noch nach
            # (SENK_NAH, OBJ_VERSATZ, LUFT_H), ist das NICHT das Oeffnen.  Hier: der erste Schritt der
            # FSM-Phase "release".
            if phase == "release" and run_combined._oeffnen is None:
                run_combined._oeffnen = {"cxy": np.asarray(c_true, float).copy(), "cz": float(cz),
                                         "obj_h": float(obj_h), "reach": np.asarray(hxy, float)[:2].copy(),
                                         "tgt": np.asarray(tgt_true, float).copy(),
                                         "fwd": np.asarray(sim.claw_fwd(), float)[:2].copy()}
            if j5 < J5_CLOSED_TH and cz > obj_h + 0.014:
                run_combined._release = {"hz": float(hz), "cz": float(cz),
                                         "obj_h": float(obj_h),
                                         "cxy": np.asarray(c_true, float).copy(),
                                         # WAS DER AGENT GLAUBTE, wo das Objekt ist, im selben
                                         # Augenblick (Messung, geht in keine Entscheidung).  Ohne
                                         # das ist "86 mm daneben abgelegt" nicht aufzuloesen:
                                         # falsch HINGETRAGEN (Glaube stimmt, Bahn nicht) sieht
                                         # genauso aus wie VERLOREN (Glaube sitzt woanders).
                                         "cbel": np.asarray(c_st, float).copy(),
                                         "tgt": np.asarray(tgt_true, float).copy(),
                                         # KLAUENRICHTUNG beim Loslassen, fuer die Zerlegung des
                                         # Ablage-Fehlers (2026-08-13): der Klauenversatz CLAW_OFF
                                         # korrigiert den GRIFF; ob er beim ABLEGEN richtig herum
                                         # wirkt, hat nie jemand geprueft.  Ohne die Richtung sagt
                                         # der Log nur den Betrag ("seitlich 44mm").
                                         "fwd": np.asarray(sim.claw_fwd(), float)[:2].copy(),
                                         # LAGE IN DER KLAUE BEIM LOSLASSEN und wo die BACKENMITTE
                                         # steht (Messung, 2026-09-28): trennt "das Objekt sitzt
                                         # aussermittig" von "die Klaue steht daneben".
                                         "inclaw": sim.in_claw(c_true),
                                         "jaw": np.asarray(sim.jaw_mid(), float)[:2].copy(),
                                         "reach": np.asarray(hxy, float)[:2].copy(),
                                         "phase": phase, "dwell": int(dwell)}
            sim.target("joint_5", j5)
            if press >= 0:                                    # DRUCKMESSSTREIFEN (ein Finger, innen);
                # PHASE FUER DIE MESSUNG aus der BEOBACHTBAREN Lage ableiten, nicht aus dem
                # FSM-Zustand.  GRUND (gemessen 2026-08-07): die FSM schaltet erst auf "carry", wenn
                # die HAND ihre eigene Hubvorgabe erreicht (hz > CARRY_Z-0.015).  Im NETZ-Modus
                # ueberschreibt die Policy den Zielpunkt, der Arm folgt ihr, die Bedingung tritt nie
                # ein -- die Phase bleibt bei "lift" haengen.  Folge: "carry" erscheint in 45% der
                # FSM-Episoden, aber nur in 12% der Netz-Episoden, und der TRANSPORT wurde unter
                # "lift" verbucht.  "tragen 0.00" hiess also nicht "verloren" und nicht "nicht
                # gemessen", sondern "falsch einsortiert".
                # Beobachtbar: gehoben + Klaue zu + die Hand hat sich seit dem Abheben seitlich
                # bewegt -> das ist Transport, unabhaengig davon, wer den Arm fuehrt.
                _lifted = cz > obj_h + 0.02 and j5 < J5_CLOSED_TH
                if _lifted and run_combined._lift_xy is None:
                    run_combined._lift_xy = np.asarray(hxy, float).copy()
                _phl = phase
                if _lifted and run_combined._lift_xy is not None                         and float(np.linalg.norm(hxy - run_combined._lift_xy)) > 0.03:
                    _phl = "carry"
                elif _lifted and phase in ("lift", "over", "lower", "close"):
                    _phl = "lift"
                run_combined._grip.setdefault(_phl, []).append(press)   # im Zustand bereits gelesen
            gentle = abs(j5 - J5_PUSH) < 0.2 and aim[2] < PUSH_Z + 0.02   # spread gripper + low = a PUSH
            # GENTLE CARRY: a concave object (e.g. a perceived U) is gripped OFF its centre-of-mass (its COM
            # sits in the concavity, on no material), so the lateral acceleration of a normal-speed carry tears
            # it out of the claws.  When the caller flags carry_gentle (driven by the PERCEIVED shape), the
            # transport of a lifted, gripped object runs slow -> the off-COM grip survives the carry.
            carrying = carry_gentle and cz > 0.03 and j5 < 0.5 * (J5_OPEN + J5_GRIP) and aim[2] > PUSH_Z
            if gentle:    g, mdq = 1.3, 0.016
            elif carrying: g, mdq = CARRY_GAIN, CARRY_MDQ
            else:         g, mdq = 2.0, 0.026                            # (derived from the sub-goal, so it
            # BACKENMITTE STATT REICHPUNKT (2026-08-07).  Der Reichpunkt (site "contact") liegt NICHT
            # zwischen den Backen: die Backenmitte sitzt 4.1mm davor bei offener und 8.6mm bei
            # geschlossener Klaue (gemessen, ueber alle Wrist-Winkel konstant).  Bei +-6mm Backentiefe
            # schliessen die Backen damit VOR dem Objekt.  Das Ziel wird deshalb um CLAW_OFF ENTGEGEN
            # der Klauenachse verschoben, sodass die BACKEN dort landen, wo bisher der Reichpunkt kam.
            # Verschoben wird das REICHZIEL, nicht die Vorgaben: alle Koordinaten (Teacher, Policy,
            # 24000 DAgger-Beispiele) bleiben damit gueltig.
            # Kausal gemessen (16 Posen, anfahren-schliessen-heben): Versatz 0 -> 0% gehoben bei 4.5N
            # Zufassdruck und 0.0N beim Heben; +4mm -> 56%, +6mm -> 62%, +8mm -> 69%, +10mm -> 44%.
            # Das Optimum +8mm trifft den geometrischen Wert 8.6mm von der anderen Seite.
            _aim = np.asarray(aim, float)
            if CLAW_OFF > 0.0:
                _aim = _aim - CLAW_OFF * sim.claw_fwd()
            # VOLLE Winkel ins Koerpermodell (ARM3 + Wrist + Greifer): der Wrist verschiebt den
            # Reichpunkt um bis zu 21mm und war fuer die gelernte Kinematik bisher unsichtbar
            # (Vorhersagefehler 7.1 -> 5.3mm, seit er mitgelernt wird).  set_arm3_targets bekommt
            # weiterhin nur die STELLGELENKE.
            q3 = sim.arm3_angles(); qf = sim.arm_angles_full()
            sim.set_arm3_targets(q3 + body.reach_velocity(qf, _aim, gain=g, max_dq=mdq))
            if WRIST_ALIGN or policy_wrist is not None:        # (B) align the claw to the object's grip axis --
                # a 5-dim policy (act23) supplies its OWN desired claw_yaw (LEARNED wrist); else the teacher's
                # heuristic wrist_tgt.  The parallel claw is symmetric mod pi, so the learned wrist aligns mod pi.
                w_tgt = wrist_tgt if policy_wrist is None else policy_wrist
                w_mod = wrist_mod if policy_wrist is None else np.pi
                near = np.linalg.norm(hxy - c) < WRIST_APPROACH_R      # ONLY during the APPROACH (near the
                gripping = j5 < J5_GRIP + 0.4                  #   object), and only while still open + above the
                descended = hz <= gz + WRIST_LOCK_MARGIN       #   grip.  set_arm3_targets resets joint_4 to HOME
                if near and not gripping and not descended:    #   each step + claw_yaw is POSE-dependent, so it
                    cy = sim.claw_yaw()                        #   keeps CORRECTING here (slope ~ -1) as the arm moves
                    err = (cy - w_tgt + w_mod / 2) % w_mod - w_mod / 2
                    wrist_hold = float(np.clip(sim.d.qpos[sim.jqadr["joint_4"]] + 0.6 * err, 0.0, np.pi))
                    sim.target("joint_4", wrist_hold)
                elif wrist_hold is not None:                   # descended/gripping -> HOLD the aligned angle (no
                    sim.target("joint_4", wrist_hold)          #   sudden roll at contact; re-assert vs the home reset)
            sim.step(2)
            if lifelong and k % 3 == 0:                       # LIFELONG: refine the learned kinematics
                body.observe(sim.arm_angles_full(), sim.grasp_pos(), lr=0.02)   # from the real (joints,hand)
            if viz is not None and k % 5 == 0:
                viz.update(sim.render(CAM), f"ep {ep} {via} {cmd} [{phase}]"
                                            f"  obj->tgt {np.linalg.norm(c-tgt)*1000:.0f}mm")
        sim.target("joint_5", J5_OPEN)                      # complete any placement: RELEASE, then let
        for s in range(40):                                 # the scene SETTLE before scoring (the cube
            sim.step(4)                                     # may still be falling / just-released when
            if track_fn is not None and s % 2 == 0:         # "placed" was declared).  KEEP the live
                track_fn()                                  # fovea window updating through the settle
            if viz is not None and policy_fn is not None:   # so the RELEASE + drop is actually SHOWN
                viz.update(sim.render(CAM), f"ep {ep} {via} {cmd} [settling]")   # (else it freezes mid-air)
        cpos = sim.obj_pos(cmd)
        err = np.linalg.norm(cpos[:2] - tgt_true)           # measure against the TRUE target
        rested = cpos[2] < cmd_half[2] + 0.010              # rests on the table (uses the OBJECT's height)
        if ERFOLG_RUHT:
            # ERFOLGSBEGRIFF FUER STUFE 2 (wiki/fragen/stapeln-als-aufgabe.md).
            # "rested" heisst woertlich LIEGT AUF DEM TISCH -- ein gelungener Stapel faellt
            # deshalb durch, obwohl er die Aufgabe erfuellt.  Der aufgabenunabhaengige Begriff ist
            # RUHT: das Objekt bewegt sich nicht mehr.  Er gilt fuer die alte Aufgabe genauso
            # (etwas, das auf dem Tisch liegt, ruht) und ist damit der ehrlichere von beiden --
            # er verlangt nur, dass die Sendung ANGEKOMMEN ist, nicht, wie hoch sie liegt.
            # ER IST NICHT GRATIS, und darum steht er auf einem Schalter: ein Objekt, das der Arm
            # noch haelt, ruht in der Klaue ebenfalls.  Deshalb die zweite Bedingung -- die Klaue
            # ist offen (nach dem Settle steht sie auf J5_OPEN, s. oben).
            _bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, cmd)
            _da = int(sim.m.jnt_dofadr[int(sim.m.body_jntadr[_bid])])   # Freejoint: 3 Linear-DOF zuerst
            _v = float(np.linalg.norm(sim.d.qvel[_da:_da + 3]))
            rested = (_v < RUHT_V) and sim.d.qpos[sim.jqadr["joint_5"]] > J5_CLOSED_TH
        ok = err < tol and rested
        deliveries += ok; n_grasp += (via == "grasp" and ok); n_push += (via == "push" and ok)
        if via == "grasp":
            grasp_tot += 1; grasp_ok += ok
        else:
            push_tot += 1; push_ok += ok
        if ood_ep:
            ood_n += 1; ood_ok += ok
        else:
            base_n += 1; base_ok += ok
        if obj_fp > GRASP_MAX_HALF:                           # affordance: this object should be PUSHED
            wide_n += 1; wide_ok += ok
        else:
            narrow_n += 1; narrow_ok += ok
        if episode_end_fn is not None:                       # self-improvement: reward = f(ok, err)
            episode_end_fn(ep, bool(ok), float(err))
        if RULEDIAG:                                          # bewusst NICHT an _quiet gehaengt: act23
            _r = run_combined._rule                            # fuehrt run_combined stumm, und genau dort
            print(f"    [Riegel] Schritte {_r['schritte']:4d} | Reflex {_r['reflex']:3d}"   # soll gezaehlt
                  f" (haette {_r['reflex_wuerde']:3d}) | Riegel {_r['riegel']:3d}"          # werden
                  f" (haette {_r['riegel_wuerde']:3d})", flush=True)
        if GLAUBDIAG:
            _g = run_combined._glaub
            _m = max(1, _g["n"]); _a = max(1, _g["anfahrt"])
            print(f"    [Glaube] Schritte {_g['n']:4d} | Wahrnehmung {1000*_g['wahrn']/_m:5.1f} mm"
                  f" | Zustand {1000*_g['orts']/_m:5.1f} mm (max {1000*_g['orts_max']:5.1f})"
                  f" | Anfahrt {1000*_g['anfahrt_orts']/_a:5.1f} mm"
                  f" | ERSTE Anfahrt {1000*_g['a1_orts']/max(1, _g['a1']):5.1f} mm ({_g['a1']:3d} Schritte)"
                  f" | Hoehe {1000*_g['hoehe']/_m:5.1f} mm"
                  f" | Phantom-Griff {_g['phantom']:4d}"
                  f" (ab {'--' if _g['phantom_ab'] is None else _g['phantom_ab']})"
                  f" | {'OK' if ok else 'daneben'}", flush=True)
        if ABLENKDIAG:
            _b = run_combined._ablenk
            _bn = max(1, _b["n"])
            _top = sorted(_b["wer"].items(), key=lambda kv: -kv[1])[:2]
            print(f"    [Ablenker] Anfahrt {_b['n']:4d} Schritte | Belief auf FREMDEM Koerper"
                  f" {_b['fremd']:4d} = {100.0 * _b['fremd'] / _bn:5.1f} %"
                  f" (ab Schritt {'--' if _b['ab'] is None else _b['ab']},"
                  f" am Ende {'FREMD' if _b['zuletzt_fremd'] else 'eigen'})"
                  f" | wer: {', '.join(f'{k} {v}' for k, v in _top) if _top else '--'}"
                  f" | Abstand Belief->eigen {1000 * _b['d_eigen'] / _bn:5.1f} mm,"
                  f" ->naechster {1000 * _b['d_fremd'] / _bn:5.1f} mm"
                  f" | {'OK' if ok else 'daneben'}", flush=True)
        if TASTDIAG:
            _t = run_combined._tast
            def _mm(v):
                return "  --  " if v is None else f"{1000.0 * v:+6.1f}"
            def _n(v):
                return " -- " if v is None else f"{v:4.2f}"
            _w = sorted(_t["wunsch"])
            _wmed = _mm(_w[len(_w) // 2]) if _w else "  --  "
            _whi = _mm(_w[-1]) if _w else "  --  "
            _wueber = sum(1 for v in _w if v > 0.012)          # oberhalb der Riegel-Schwelle
            print(f"    [Tastsinn] Aufsetzen {_mm(_t['stall_h'])} mm (Druck {_n(_t['stall_p'])} N)"
                  f" | tiefster Punkt {_mm(_t['min_h'])} mm"
                  f" | Schliesswunsch: erst {_mm(_t['close_h'])} Median {_wmed} hoechst {_whi} mm,"
                  f" {_wueber}/{len(_w)} ueber der Schwelle"
                  f" | Druck offen max {_t['p_max_offen']:4.2f} N | {'OK' if ok else 'daneben'}",
                  flush=True)
        typ = "OOD " if ood_ep else (("wide" if obj_wide.get(cmd, False) else "cube") if perceive_fn else "")
        if not getattr(run_combined, "_quiet", False):
            print(f"  ep {ep:2d}: {'OK ' if ok else 'no '} {typ:4s} via {via:5s}  obj->tgt {err*1000:.0f} mm")
    if not getattr(run_combined, "_quiet", False):
        print(f"  == combined grasp-then-push: DELIVERED {deliveries}/{episodes}  "
              f"(by grasp {n_grasp}, by push {n_push}) ==")
        if ood_n:                                            # generalization probe: keep base vs OOD apart
            print(f"  GENERALIZATION: base small-cube {base_ok}/{base_n}  |  OOD novel size/shape {ood_ok}/{ood_n}")
        if wide_n:                                            # affordance: grasp-narrow vs push-wide split
            print(f"  AFFORDANCE: narrow->grasp {narrow_ok}/{narrow_n}  |  wide->push {wide_ok}/{wide_n}")
        if dec_n:
            print(f"  AFFORDANCE decision (grasp cube / push wide) correct: {dec_ok}/{int(dec_n)}")
            print(f"  per mode: grasp {grasp_ok}/{grasp_tot}, push {push_ok}/{push_tot}")
        if perr_n:
            print(f"  camera-perceived CUBE vs true: {perr_sum/perr_n*1000:.1f} mm  (over {int(perr_n)} eps)")
        if terr_n:
            print(f"  camera-perceived TARGET vs true: {terr_sum/terr_n*1000:.1f} mm  (over {int(terr_n)} eps)")
    if viz is not None and not getattr(run_combined, "_quiet", False):   # _quiet -> caller owns the viz
        print("  [viz] close the window to exit."); viz.hold()           #   lifecycle (e.g. interactive
    return deliveries, episodes                                          #   command steering keeps it open)


def main():
    HEADLESS = os.environ.get("ACT16_HEADLESS", "0") == "1"
    CAM = os.environ.get("ACT16_CAM", "overview").lower()
    TARGET = os.environ.get("ACT16_TARGET", "") or None       # fix one cube, or None = cycle all
    EPISODES = int(os.environ.get("ACT16_EPISODES", "12"))
    MODE = os.environ.get("ACT16_MODE", "both").lower()
    force = None if MODE == "both" else MODE                  # grasp | push to force one branch

    print(f"act16 — manipulation with CLAWS: grasp-then-push  (mode={MODE})")
    sim = BracketArmSim()
    sim.set_reach_site("contact")
    body = ArmBodyModel3D(rng=np.random.default_rng(5))
    print("  babbling the arm to learn its 3-D kinematics (to the contact point) ...")
    body.babble(sim, 4000)
    viz = None
    if not HEADLESS:
        try:
            import matplotlib  # noqa
            viz = CamViz(CAM)
        except Exception as e:
            print(f"  [viz] matplotlib unavailable ({e}); running headless")
    run_combined(sim, body, viz, CAM, episodes=EPISODES, cmd_fixed=TARGET, force=force)


if __name__ == "__main__":
    main()
