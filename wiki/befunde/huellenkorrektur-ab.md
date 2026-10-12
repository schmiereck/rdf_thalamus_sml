---
type: Befund
title: Kollisionshuelle nachfuehren - act23-A/B neutral
description: Gepaartes act23-A/B (8 Seeds x 25 Episoden je Arm) der Huellenkorrektur e4eb65e gegen die alte Huelle (ACT14_HUELLE_ALT=1). Kein Unterschied - 118/200 gegen 120/200, Vorzeichen ueber Seeds 4:4, McNemar p = 0,33, Balken 22/25 gegen 21/25. Die Korrektur bleibt als richtige Physik an; sie kostet nichts und bringt messbar nichts. NACHTRAG 2026-10-12: Pruefung aller umbemessenen Koerper - bei MEHRTEILIGEN Koerpern muss auch der Huellbaum (bvh_aabb) mit, sonst bleiben verpasste Kontakte (verformtes obj_T 32 von 320); jetzt behoben, gegen neu kompiliertes Modell 0 verpasst. Das A/B oben pruefte die Teilkorrektur.
tags: [act23, physik, kollision, ab, balken]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-10-12T03:00:00Z }
sources:
  - id: sweep
    resource: "Kopflose GUI-Steuerung, Seeds 9701-9708, ACT23_AUTO_N=25, SZENE_JE_EPISODE=1, AUTO_CURIOUS=0, EIG_DIREKT/EIG_STETIG=1, GOAL_Z/GRIFF_Z=1, Kopie des Hauptzustands df320cd0, NO_PERSIST; Arm A ACT14_HUELLE_ALT=1, Arm B 0; Commit 674f878"
    title: A/B Huellenkorrektur
  - id: fehler
    resource: /befunde/balken-welt-schraeg.md
    title: Balken-Welt (Fund des Huellenfehlers)
---

# Frage

Der Huellenfehler ([Balken-Welt](/befunde/balken-welt-schraeg.md)): zur Laufzeit umbemessene Koerper
behielten `geom_rbound`/`geom_aabb` aus dem Kompilieren; die Enden des 68-mm-Balkens waren fuer die
Klauennaegel unsichtbar. Seit e4eb65e fuehrt `BracketArmSim.huelle_nachfuehren` beides nach, auch in der
Vorgabewelt. Nutzerauftrag 2026-10-11: *"Starte den A/B-Lauf fuer die Huellenkorrektur."*

# Aufbau

Ein Schalter als einzige Abweichung: `ACT14_HUELLE_ALT=1` stellt das alte Verhalten her (Arm A), Vorgabe ist
die Korrektur (Arm B). **Geprueft vor dem Lauf:** Arm A ist mit dem Commit vor der Korrektur (16ea5d8)
zeichengleich - 3 Episoden, 310 Logzeilen identisch bis auf Zeitangaben. Aufbau sonst nach
[Kopfloses A/B](/messungen/act23-headless-ab.md), gepaart je Episode, je zwei Prozesse.

# Zahlen

    Seed     9701  9702  9703  9704  9705  9706  9707  9708   gesamt
    A alt     14    15    13    16    15    15    15    15    118/200 (59 %)
    B neu     16    17    12    17    12    14    14    18    120/200 (60 %)
    B - A     +2    +2    -1    +1    -3    -1    -1    +3

* **Vorzeichen ueber Seeds 4:4**, Wilcoxon p = 0,67 (massgeblich, s. Messvorschrift).
* Episoden mit gleichem Szenen-Abdruck 131: nur A geliefert 10, nur B 16, McNemar p = 0,33 (Beiwerk;
  ueberschaetzt, weil die Arme weiterlernen). 69 Episoden mit verschiedenem Abdruck fallen heraus.
* Die Arme trennen sich frueh: erste verschieden ausgehende Episode je Seed 1-9 (ein Seed nie).
* Objektmischung in beiden Armen identisch. Je Objekt nichts auch nur in der Naehe (Bonferroni 7 Objekte:
  0,0071): Balken 22/25 gegen 21/25, Wuerfel A 22/30 gegen 22/30, Wuerfel B 11/37 gegen 14/37, L 11/21
  gegen 13/21, U 9/24 gegen 13/24, Neue Form 7 21/35 gegen 19/35, Neue Form 10 22/28 gegen 18/28.
* Gegenprobe Zaehlung: `[Auto N] GELIEFERT` und `[Selbst-Urteil] ... Welt:` stimmen in allen 400
  Episoden ueberein.

# Bewertung

**Neutral.** Die Korrektur aendert die Physik messbar (Probe: 0 -> 4 Kontakte am Balkenende) und die
Laufbahnen der Arme (sie trennen sich nach wenigen Episoden), aber nicht die Lieferquote - auch nicht am
Balken, wo sie ansetzt. Plausibel, weil der Arm den Balken nahe der Mitte greift und die unsichtbaren
aeusseren ~4 mm dabei kaum beruehrt werden (nicht gemessen).

**Entscheidung:** die Korrektur bleibt Vorgabe - sie ist die richtige Physik und kostet nichts.
`ACT14_HUELLE_ALT=1` bleibt als Rueckschalter fuer Vergleiche mit aelteren Laeufen.

# Nachtrag 2026-10-12: alle umbemessenen Koerper geprueft

Nutzerauftrag: *"Pruefe auch die anderen umbemessenen Koerper auf den Huellenfehler."*

**Bestandsaufnahme** (jede Laufzeit-Schreibung auf `geom_size` im act23-Pfad):

    Stelle                                        was                                  vorher             jetzt
    pc_act14 set_object_size (act16-Streuung,     beliebige Quader, u. a. Neuheit obj_T Teil ok (e4eb65e)  + Huellbaum
      Neuheits-Verformung obj_T)
    act23 Balken (setup_obj, _set_sizes)          68 x 18 mm auf 24-mm-Wuerfel          Teil ok            unveraendert (1 Teil)
    act23 main_diag obj_red (ACT23_MODE=diag)     56 x 20 mm auf 24-mm-Wuerfel          NICHTS             nachgefuehrt
    act23 _set_sizes Neuheit obj_T (direkt)       erstes Teil verformt                  NICHTS             nachgefuehrt
    act23 Rueckstellen obj_red / L-U-Teile (h0)   zurueck aufs Kompilat                 NICHTS (Huelle     nachgefuehrt
                                                                                         blieb zu gross)
    act23 Sockel- und Formhoehen                  z-Halbachse                           nur rbound         + aabb + Huellbaum
    ObjectOrientationModule.train,                Trainingsbilder, Koerper umbemessen   NICHTS             nachgefuehrt
      ShapeClassifierModule.train
    pc_act16 Zielscheibe                          Radius                                -                  contype 0, beruehrt nichts

Nicht angefasst (ausserhalb des act23-Pfads, eigene Werkzeuge): `act23_relrings_ab.py`,
`chain_obstacle_data.py` (verformt ein HINDERNIS - dort koennte der Fehler wirken), `shape_grasp_viz.py`.

**Neuer Befund - der Huellbaum mehrteiliger Koerper:** MuJoCo fuehrt fuer Koerper mit mehreren Teilen
(L, U, T, X, Y, die Finger) einen Huellbaum `bvh_aabb` im TRAEGHEITSrahmen des Koerpers, ebenfalls aus dem
Kompilieren. Probe gegen ein mit der verformten Groesse NEU KOMPILIERTES Modell als Wahrheit, je 600 zufaellige
Lagen von L/U/X/Wuerfel am verformten obj_T:

    obj_T erstes Teil   Kontakt im Neukompilat   alt verpasst   nur Teilhuelle verpasst   + Huellbaum verpasst
    60 x 8 mm              320                      40              32                         0
    44 x 40 mm             384                      85              -                          0

Kein zusaetzlicher (falscher) Kontakt in irgendeiner Fassung. `BracketArmSim._koerper_bvh` rechnet den Baum
von den Blaettern her neu; auf allen unveraenderten mehrteiligen Koerpern trifft es das Kompilat auf
0,0000 mm. Fallen beim Bau: Kindverweise zaehlen relativ zu `body_bvhadr`, Teilnummern absolut; der Rahmen
ist `body_ipos`/`body_iquat`, nicht der Koerperrahmen (zwei Fehlversuche, beide am Kompilat erkannt).

**Berichtigung zum Balken:** unsichtbar war nicht nur ein aeusseres ~4-mm-Stueck. Nagelgrosser Wuerfel 2 mm in
der Seite des 68-mm-Balkens: Kontakt bis 24 mm von der Mitte, **ab 28 mm keiner** - die aeusseren rund
8 mm je Ende fehlten. Bei main_diag (`obj_red` auf 56 mm) fehlte das Ende ebenso.

**Pruefung:** `ACT14_HUELLE_ALT=1` stellt das alte Verhalten weiter zeichengleich her (4 Episoden, 335
Logzeilen identisch mit 16ea5d8). Rauchtest der neuen Fassung 4 Episoden ohne Fehler.

**Nicht gemessen:** die Wirkung der Erweiterung (Huellbaum, Neuheits-obj_T, Rueckstellungen) auf act23 -
das A/B oben pruefte nur die Teilkorrektur. Masse und Traegheit umbemessener Koerper bleiben die des
Kompilats (kein Huellenfehler, aber derselbe Typ von Altlast; nicht angefasst).

# Verwandt

* [Balken-Welt: schraeg schadet nicht](/befunde/balken-welt-schraeg.md) - Fund des Fehlers
* [Kopfloses A/B](/messungen/act23-headless-ab.md)
