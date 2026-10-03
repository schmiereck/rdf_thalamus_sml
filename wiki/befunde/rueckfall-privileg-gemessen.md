---
type: Befund
title: Der privilegierte Wahrnehmungs-Rueckfall rettet praktisch nichts
description: Findet perceive das kommandierte Objekt nicht, nahm act23 still die wahre Lage aus MuJoCo - beim ersten Blick UND beim Wiederfinden mitten in der Episode (zweiter, bisher uebersehener Kanal). Gemessen - Namensbetrieb 1 Rueckfall in 400 Episoden (1 Lieferung gerettet), Eigenschaftsbetrieb 2 Rueckfall-Episoden in 200, beide auch mit Privileg gescheitert (111 gegen 114 von 200). Seit 2026-10-03 ist ACT23_RUECKFALL=aufgeben Vorgabe - nicht gefunden heisst kein Versuch.
tags: [act23, privileg, wahrnehmung, rueckfall, ab, laufzeit-regeln]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-10-03T00:00:00Z }
sources:
  - id: code
    resource: "fc003aa (Rueckfall sichtbar, ACT23_RUECKFALL, Vorblick), 2f2ad4d (auch das Wiederfinden), Vorgabe aufgeben danach"
    title: Umbau
  - id: lauf
    resource: "Kopflos, Kopie des Zustands 7a3f7a2d (GUI-Endstand 2026-10-02), ACT23_NO_PERSIST=1, ACT23_SZENE_JE_EPISODE=1 ACT23_AUTO_CURIOUS=0 ACT23_EIG_DIREKT=1 ACT23_EIG_STETIG=1 ACT16_GOAL_Z=1 ACT16_GRIFF_Z=1, Choreo netz, Marker-Ablage. Namensbetrieb Seeds 9971-9978 (Arm P, 9971 auch Arm A); Eigenschaftsbetrieb (ACT23_AUTO_EIG=1) Seeds 9981-9984, Arme P/A parallel"
    title: Laeufe 2026-10-03
---

# Frage

Schritt 2 aus der [Bestandsaufnahme der Laufzeitregeln](/mechanismen/laufzeit-regeln.md): wie
oft greift der privilegierte Rueckfall in `perceive`, und was bringt er?

# Was es gab

Drei Stellen in `perceive` nahmen bei Fehlschlag `sim.obj_pos(body)`:

* **Eigenschaften** (Farbe/Form/Groesse treffen nichts),
* **Formklasse** (L, U, Neue Form 7/10: Klasse nicht gefunden),
* **langes Objekt** (Farbklasse ungeboren oder nicht im Bild).

Die Wuerfel fallen auf das trainierte Farbnetz zurueck - nicht privilegiert, nicht betroffen.
Protokolliert war der Rueckfall nur unter `ACT23_DEBUG`.

**Zwei Fallen beim Ersetzen**, beide erst im Lauf gefunden:

1. `run_combined` greift selbst auf `c_true`, wenn die Wahrnehmung `None` liefert - ein blosses
   "nichts zurueckgeben" haette das Privileg nur verschoben. Deshalb ein **Vorblick** in `run_one`
   vor `run_combined`; mit `aufgeben` endet die Episode dort (kein Armweg, kein Lernen, zaehlt als
   nicht geliefert).
2. Das **Wiederfinden mitten in der Episode** (`run_combined` ruft `perceive_fn` erneut, wenn der
   Servo das Objekt verliert) lief durch denselben Rueckfall - ein zweiter Kanal. Im ersten
   Eigenschafts-Durchgang bekam der Arm "aufgeben" so trotzdem die Wahrheit (verworfen). Jetzt
   liefert ein gescheitertes Wiederfinden "nichts Neues", die Hand behaelt ihren Glauben.

# Ergebnis

**Namensbetrieb** (so laufen die GUI-Laeufe): 400 Episoden, **1 Rueckfall** (Seed 9978, Ep 22,
langes Objekt, Farbklasse in dieser Episode nicht gebunden) - mit Privileg geliefert (8 mm).
Ohne Rueckfall sind beide Arme bitgleich (Seed 9971: 27/50 und 27/50, identische Folge); der
vorab geplante 8-Seed-A/B wurde deshalb nach Seed 9971 auf eine Zaehlung mit Arm P umgestellt -
jeder weitere Seed haette nur Duplikate erzeugt.

**Eigenschaftsbetrieb** (`ACT23_AUTO_EIG=1`), 4 Seeds x 50, gepaart (200/200 gleiche Aufgaben):

| Seed | privileg | aufgeben | Rueckfall-Episoden (P) |
|---|---|---|---|
| 9981 | 28/50 | 28/50 | 1 (obj_blue, 2 Wiederfind-Versuche) - beide Arme nicht geliefert, 64 mm |
| 9982 | 26/50 | 26/50 | 0 |
| 9983 | 29/50 | 29/50 | 0 |
| 9984 | 28/50 | 31/50 | 1 (obj_L, 2 Wiederfind-Versuche) - beide Arme nicht geliefert, 42/44 mm |
| **gesamt** | **111/200** | **114/200** | 2 |

Die +3 in Seed 9984 entstehen NACH der Rueckfall-Episode durch auseinanderlaufendes Lernen, nicht
durch den Rueckfall selbst.

# Lesart

**Das Privileg rettet praktisch nichts** - eine Lieferung in 600 Episoden. Die frueheren 4-6 %
Rueckfall ([Farb-Mischung](/befunde/farb-mischung.md), 2026-09-10) gelten fuer einen aelteren
Zustand; seither ist die Wahrnehmung mehrfach verbessert worden (u. a. Chroma-Schnitt), und im
Eigenschaftsbetrieb liegt die Rate jetzt bei 1 %. Wo er heute noch greift, ist es das
Wiederfinden waehrend der Anfahrt - und dort scheitert die Episode auch mit der Wahrheit.

Seit 2026-10-03: `ACT23_RUECKFALL=aufgeben` ist Vorgabe. Jeder Rueckfall bleibt als
`[Rueckfall] ... -> NICHT GEFUNDEN` und `[Nicht gefunden] ...` im Protokoll sichtbar.
`ACT23_RUECKFALL=privileg` stellt das alte Verhalten her.

# Was offen bleibt

* Der **Keim**-Rueckfall (`ACT23_KEIM_RUECKFALL`, Vorgabe 0) ist nicht betroffen und bleibt aus.
* `run_combined` liest `c_true` weiter fuer Buchhaltung und Bewertung (Geruest) und im Tragen,
  wenn der Policy-Zustand privilegiert ist (`ACT16_OBS_STATE=0`, nicht Vorgabe).
* Ein echtes "nochmal hinschauen" (anderer Blickpunkt, Fovea-Suche) ist nicht gebaut - bei dieser
  Rate lohnt es sich nicht.

# Verwandt

* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md)
* [Groesse sehen statt wissen](/befunde/groesse-sehen-ab.md) - Schritt 1
