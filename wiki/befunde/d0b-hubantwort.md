---
type: Befund
title: D0b-Hubantwort - feste Fovea-Rohantwort verfehlt den Replikationsvertrag
description: Der erste Richtungsbefund hält als feste, enthaltende Zellantwort auf Seed 103 nicht: drei Fehlgriffe werden als getragen markiert, Precision 0,786 statt 0,80.
tags: [act23, dream-rsi, d0b, fovea, hub, greifen, selbstbewegung]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: codex, at: 2026-09-25T16:00:00Z }
sources:
  - id: contract
    resource: /messungen/d0b-hubantwort.md
    title: Vorab festgelegter Prüfvertrag und vollständige Zahlen
  - id: frames
    resource: ../../log/d0b-lift-response/seed101-12ep/fovea_frames.jsonl
    title: Agentenzugängliche Fovea- und Handtraces
  - id: truth
    resource: ../../log/d0b-lift-response/seed101-12ep/eval_truth.jsonl
    title: Getrennte Simulator-Evaluation des Tragens
  - id: receipt
    resource: ../../log/d0b-lift-response/seed101-12ep/result.json
    title: Eingefrorene Laufquittung und Komponentenhashes
  - id: replication-frames
    resource: ../../log/d0b-lift-response/seed103-20ep/fovea_frames.jsonl
    title: Neue, agentenzugängliche Seed-103-Foveatraces
  - id: replication-truth
    resource: ../../log/d0b-lift-response/seed103-20ep/eval_truth.jsonl
    title: Getrennte Seed-103-Trageevaluation
  - id: replication-audit
    resource: ../../log/d0b-lift-response/seed103-20ep/audit.json
    title: Festgeschriebene Rohantwort-Auswertung
---

# Behauptung

Eine eigene Hubbewegung erzeugt bei festem Fovea-Blick eine messbare Bildantwort. Die einfache,
aus dem ersten Audit festgeschriebene Zellantwort trennt Tragen und Fehlgriff jedoch nicht
präzise genug und ist als Greifzustandsprädiktor verworfen.

# Aufbau

Der Schalter `ACT23_D0B_LIFT_PROBE=1` friert den aktuellen Fovea-Blick ausschließlich während
der FSM-Phase `lift` ein. Er verändert weder Teacher, Ziel, Greifer, Servorückgabe noch
Lerngewichte. Der agentenzugängliche Trace enthält Auswahl-Schwerpunkt und -masse im
Fovea-Zellraster, Fovea-Topzustand, Blick und Handpose. Kontakt und Objektpose werden erst in
der getrennten Evaluationsdatei nachgeschlagen.

Der eingefrorene Lauf verwendete Seed 101, zwölf Episoden und die unveränderte Basis
`base.pkl`. Der Runner bestätigt Rückgabecode 0, 0 veränderte Lernkomponenten und identische
Basis-SHA vor/nach dem Lauf.[^receipt]

# Zahlen

| Größe | getragen (n=6) | nicht getragen (n=4) |
|---|---:|---:|
| Änderung Auswahl-Schwerpunkt, Median | 3,89 Zellen | 0,60 Zellen |
| Bereich Auswahl-Schwerpunkt | 0,55–4,56 | 0,40–1,10 |
| Änderung Auswahlmasse, Median | 20,09 | 63,04 |
| Änderung Topzustand, Median | 0,27 | 0,23 |

Alle 389 Liftframes hatten fixierten Blick und vollständigen Auswahl-Schwerpunkt; zehn
Episoden enthalten einen Lift und damit 379 benachbarte Bildpaare. Die Gruppen werden ausschließlich
über die letzte getrennte Tragewahrheit der jeweiligen Trajektorie gebildet.[^frames][^truth]

Der exakte Permutationstest für größere Schwerpunktänderung in der getragenen Gruppe ergibt
einseitig `p=0,057`, zweiseitig `p=0,114` (U=20, n=6 gegen n=4). Das ist bei einer
Einzelmessung ein Richtungsbefund, kein Signifikanz- oder Leistungsnachweis.

# Bewertung

Die vorherige Blockade war die fehlende Bildraumreferenz der Hand. Der feste Blick beseitigt
dieses Problem für die Hubphase: die Änderung ist bereits in Zellkoordinaten relativ zu
derselben Kameraansicht messbar. Anders als beim Handlandmark wird keine Klaue lokalisiert.

Ein Klassifikator oder eine Laufzeitregel folgt daraus noch nicht. Die vier von sechs sichtbaren
positiven Trajektorien oberhalb 1,5 Zellen sind kein zulässiges Ergebnis, weil diese Schwelle
aus genau denselben zehn Trajektorien abgelesen wurde. Auswahlmasse und Topzustand sind hier
keine überzeugenden Alternativen.

# Replikation

Die vorab festgelegte Replikationsfamilie Seed 103 enthält 17 gültige Trajektorien. Sie erfüllt
die Abdeckung (mindestens 12), Recall (11/13 = 0,846) und Enthaltung (2/17 = 0,118), doch drei
Fehlgriffe werden als `getragen` markiert. Damit liegt die Precision bei 11/14 = 0,786 und unter
dem vorher festgelegten Tor 0,80.[^replication-audit]

Das ist kein Rundungsgrund für eine Schwellenänderung: Die Schwellen 1,50/0,75 und alle Tore
standen bereits im Vertrag. Nach dessen expliziter Abbruchregel wird Seed 107 nicht gefahren;
eine zweite Familie könnte den verworfenen Prädiktor nicht wieder zulassen.

# Folgen

Die feste Schwerpunktantwort wird weder nachoptimiert noch als Lernkopf oder Laufzeitregel
verdrahtet. D0b/F0 ist mit den bisher geprüften Handlandmarks, Crop-Köpfen und dieser Rohantwort
zurückgestellt. Ein späterer Neustart braucht eine eigenständige Repräsentations- oder
Aufgabenhypothese samt neuem Vertrag; höhere Fovea-Auflösung oder ein Motorpfad sind dadurch
nicht belegt.
