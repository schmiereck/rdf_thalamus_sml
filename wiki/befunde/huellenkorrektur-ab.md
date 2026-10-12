---
type: Befund
title: Kollisionshuelle nachfuehren - act23-A/B neutral
description: Gepaartes act23-A/B (8 Seeds x 25 Episoden je Arm) der Huellenkorrektur e4eb65e gegen die alte Huelle (ACT14_HUELLE_ALT=1). Kein Unterschied - 118/200 gegen 120/200, Vorzeichen ueber Seeds 4:4, McNemar p = 0,33, Balken 22/25 gegen 21/25. Die Korrektur bleibt als richtige Physik an; sie kostet nichts und bringt messbar nichts.
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

# Verwandt

* [Balken-Welt: schraeg schadet nicht](/befunde/balken-welt-schraeg.md) - Fund des Fehlers
* [Kopfloses A/B](/messungen/act23-headless-ab.md)
