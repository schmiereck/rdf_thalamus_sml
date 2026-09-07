---
type: Befund
title: Greif-Lerndeckel - der Teacher ist die praktische Decke
description: Ehrliches Negativ: Greifen ueber den geskripteten Teacher hinaus zu LERNEN zahlt sich in diesem Sim nicht aus. Die echten Griffgewinne kamen aus Mechanismus-Korrekturen. Enthaelt die Gegenprobe, in der Selbstlernen sehr wohl gelang.
tags: [act23, greifen, selbstlernen, negativ]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-06-30T00:00:00Z }
verified: { by: human:thomas, at: 2026-06-30T17:08:00Z }
sources:
  - id: diag
    resource: "pc_act23.py ACT23_MODE=diag, Commit e15b2bd"
    title: Gegenprobe im signalreichen Regime
---

# Behauptung

In diesem Sim ist der **Teacher die praktische Decke**: der wahrgenommene Greifpunkt plus das
propriozeptive `WRIST_ALIGN` plus gezielte Mechanik-Korrekturen. Der Rest an Spielraum ist zu
klein und zu verrauscht, um ihn zu lernen, und ein aggressives Modell-Argmax **schadet**.

# Zahlen

Jede Messung kopflos auf der Uebersichtskamera:

* **Entschaerfung der Praemisse:** das ferne U ist kein sauberes Wrist-Problem. Die Hand
  erreicht das ferne Objekt (0-4 mm) und hebt an den meisten fernen Stellen voll (62-66 mm),
  liefert aber nicht - der dominante Fehler ist **Trage-Rutschen** (das konkave U liegt neben
  dem Schwerpunkt) plus der lange Tragweg. Der Wrist zaehlt nur in einem schmalen Positionsband.
* **Dichter Kredit im Online-RL** (die Kernhypothese des Planers): Potentialformung pro Schritt
  gegen Episoden-AWR, gleicher BC-Start, 15 Iterationen -> **beide verschlechtern sich**
  (Episode 0,17 -> 0,09; dicht 0,21 -> 0,07).
* **Wrist-Such-Orakel** (bestes aus 8 Wrists je Situation gegen `WRIST_ALIGN`) zeigt Spielraum
  (Wuerfel +1, L +2, U +3), aber klein, rauschdominiert und stichprobenabhaengig (Teacher-U
  schwankt 4/10 <-> 8/16). Greifpunkt-Orakel noch kleiner (+1/+1/+2).
* **Den Spielraum einzusammeln scheitert auf jedem Weg:** (a) Suche + Destillation des besten
  Wrists: gemischt (L +2, U -2). (b) Ergebnismodell-Imagination + Argmax: gleichauf mit dem
  Teacher (Wuerfel 15=15, L 9=9, U 8 gegen 7). (c) am staerksten - **gemeinsames** Argmax ueber
  Greifpunkt und Wrist: durchweg schlechter (Wuerfel 15->10, L 9->6, U 8->6) durch
  **Modellausbeutung** (Fluch des Optimierers).
* **Der gebaute Selbstlern-Greifer** (Commit `207d212`): Modell-AUC nur **0,57**, LCB-Sicherheit
  scheitert (8/12 gegen 10/12 auf L), und die U-Lernkurve **faellt** mit mehr eigener Erfahrung
  9 -> 8 -> 7 -> 5.

# Bewertung

Die Ursache ist **Signal, nicht Architektur**: der Griff-Ausgang ist aus (Merkmale, Aktion)
nahezu unvorhersagbar, weil der Spielraum ueber dem Teacher winzig und rauschdominiert ist. LCB
schuetzt nur, solange sigma hoch ist; schrumpft sigma, uebernimmt das schwache mu - "selbstsicher
falsch", und die Kurve faellt.

**Eine Aufgabe nahe der Decke hat zu wenig lernbares Signal, um Selbstverbesserung ueberhaupt zu
zeigen.** Das ist kein Urteil ueber die Architektur.

# Die Gegenprobe - im signalreichen Regime funktioniert es

`ACT23_MODE=diag` (Vorgabe, Commit `e15b2bd`): ein diagonal ausgerichtetes, laengliches
`obj_red`, dessen Lieferung am Wrist haengt, privilegierter Yaw des Teachers abgeschaltet.[^diag]

    Modell-AUC 0,86   (gegen 0,57 nahe der Decke)
    fester Wrist 13/16 | privilegierter Yaw 13/16 | SELBST GELERNT 15/16

Der selbstueberwachte Agent erreicht bzw. schlaegt den privilegierten Teacher **ohne Privileg**,
aus eigener Erfahrung.

**Ehrliche Einschraenkung:** der Wrist-Spielraum ist klein (der Sim richtet sich selbst aus,
fester Wrist liegt schon bei 13/16), 15 gegen 13 liegt im Rauschen von 16 Stichproben, und die
Lernkurve ist **flach** (15 -> 13 -> 13), nicht steigend. Die belastbare Aussage ist
**AUC 0,86 plus Gleichstand mit dem privilegierten Teacher ohne Privileg**.

# Folgen

Vor weiterer "ueber den Teacher hinaus lernen"-Arbeit am Griff: es hat sich nicht ausgezahlt.
Die echten Griffgewinne kamen aus gezielten **Mechanismus-Korrekturen** (`grip_close` fuer das
U, kontrastive Wahrnehmung), nicht aus RL, Suche oder Imagination.

Die Lehre fuer kuenftige Selbstlern-Arbeit: die Architektur (selbstueberwachtes Ensemble-
Weltmodell + LCB-Handeln) **wirkt, wo echter Spielraum ist**. Also signalreiche oder
teacherlose Aufgaben waehlen, keine nahe der Decke.

Ein sauberes Beispiel dafuer, dass Uebertragung ueber Bauteile hinweg traegt: die
Greif-Uebertragung liefert bei 14 mm Armbreite +16,1 und bei 20 mm +24,4 Punkte ueber dem Haus;
10 mm scheitert an der **Wahrnehmung**, nicht am Greifen.

# Verwandt

* [Projektziel](/ziel.md) - schlechter als der Teacher ist ausdruecklich in Ordnung
* [Exekutionsvarianz](/befunde/exekutionsvarianz.md)
