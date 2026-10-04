---
type: Befund
title: Flache Objekte tiefer greifen - bringt nichts, die Vermutung war Rauschen
description: Vermutet war, dass der Teacher 16-mm-Objekte an der Kante greift (Hand 14 mm, Oberkante 16 mm) und die Policy sie deshalb nicht lernt. ACT16_GREIF_FLACH greift hoechstens 6 mm unter die Oberkante (16 mm -> 10 mm). Pruefstand, Teacher auf lauter 16-mm-Objekten, 30 Episoden gepaart - alt 13/30, tiefer 11/30 (p = 0,79). Der Teacher greift 16 mm so gut wie 24 mm (43 %); die "3 von 9" der Vorprobe waren Rauschen.
tags: [act23, hoehe, greifen, teacher, negativ]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: claude/opus-5.5, at: 2026-10-04T00:00:00Z }
sources:
  - id: code
    resource: "pc_act16.py GREIF_FLACH / greif_abzug (Etikett, Phasenmaschine, Reflex, Ablagehoehe), Vorgabe 0"
    title: Schalter
  - id: lauf
    resource: "Kopflos, Kopie des Zustands 7a3f7a2d, ACT23_HOEHEN=16 (alle Objekte 16 mm), ACT23_CHOREO=fsm, Seed 9021, je 30 Ep, ACT16_GREIF_FLACH 0/1 parallel"
    title: Pruefstand 2026-10-04
---

# Vermutung

Aus [Neue Objekthoehen](/befunde/neue-hoehen-gelernt.md): die Policy lernte 16-mm-Objekte kaum,
und der Teacher hatte in einer Vorprobe nur 3 von 9 geschafft. Am Code: beide Greifpfade landen
bei 16 mm auf 14 mm Handhoehe (Etikett `obj_h + GRASP_OFFSET`, Phasenmaschine `GRASP_Z`), also
2 mm unter der Oberkante; die Backen reichen etwa +-5-6 mm um den Bezugspunkt der Hand.

# Gebaut

`ACT16_GREIF_FLACH` (Vorgabe 0): die Hand steht hoechstens `ACT16_GREIF_TIEFE` (6 mm) unter der
Oberkante - in Etikett, Phasenmaschine, Reflex-Zielhoehe und Ablagehoehe gleich. Fuer 24 und
32 mm aendert sich nichts, 16 mm wird auf 10 mm gegriffen.

# Messung

| Teacher (FSM), alle Objekte 16 mm, 30 Episoden | geliefert |
|---|---|
| alt (14 mm) | 13/30 = 43 % |
| tiefer (10 mm) | 11/30 = 37 % |

Gepaart 6:4, Fisher p = 0,79. Fehlerarten gleich verteilt.

# Lesart

**Ehrliches Negativ.** Tiefer greifen hilft nicht, und es war nicht noetig: der Teacher greift
16 mm so gut wie 24 mm. Die Vermutung stand auf 9 Episoden - genau die Kleinstichprobenfalle, vor
der [Griffglaube und Tastsinn](/befunde/griff-glaube-und-tastsinn.md) schon einmal gewarnt hat.
Die Policy endet bei 16 mm auf Teacher-Niveau; die flache Lernkurve dort heisst "schon nahe am
Deckel", nicht "lernt nicht". Kein act23-A/B gefahren - am Pruefstand ist schon der Mechanismus
wirkungslos.

# Verwandt

* [Neue Objekthoehen](/befunde/neue-hoehen-gelernt.md) - dort korrigiert
* [Greif-Lerndeckel](/befunde/greif-lerndeckel.md)
