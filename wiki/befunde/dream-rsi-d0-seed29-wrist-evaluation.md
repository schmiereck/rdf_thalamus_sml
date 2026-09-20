---
type: Befund
title: D0 Seed 29 - Trainingsabdeckung besteht, Evaluation offen
description: Der unveränderte 120-Episoden-Vertrag liefert 92 volle Selbst-Kredite in fünf Wrist-Zellen auf einer eigenen Checkpoint-Kopie. Die zwei gefrorenen Testfamilien stehen aus.
tags: [act23, dream-rsi, d0, wrist, evaluation, seed29]
status: draft
evidenz: einzelmessung
ebene: act23-ab
generated: { by: codex, at: 2026-09-20T18:00:00Z }
sources:
  - id: protocol
    resource: /messungen/dream-rsi-d0-wrist-lernaufgabe.md
    title: Fixierter D0-Pilotvertrag v1
  - id: training
    resource: ../../log/d0-training/seed29-block120/result.json
    title: Seed-29-Trainingsblock
  - id: credit
    resource: ../../log/d0-training/seed29-block120/credit.jsonl
    title: Selbst-Kreditprotokoll von Seed 29
---

# Trainingsabdeckung

Der Seed-29-Trainingsblock fährt 120 gepinnte FSM-L-Form-Episoden auf einer neuen Kopie der
D0-Basis, mit unverändertem Rezept gegenüber Seed 17. Er besteht das vorab fixierte technische
Tor:

| Metrik | Wert |
|---|---:|
| volle Selbst-Kreditzeilen | 92 |
| relative Wrist-Zellen | 5 von 8 |
| positive sichere Lieferungen | 67 |
| kausale Fehlgriffe am Objekt | 18 |
| Drucksensor-Fehlgriffe | 7 |
| Mindesttor | 40 Zeilen, 4 Zellen |

Die Basisquelle behält SHA-256 `ad9d768c...c09b9e`. Die Trainingskopie weicht danach wie
erwartet ab (`d041348e...88e3`), ohne eine Live-Datei zu berühren.

# Nächster Schritt

Die Kreditabdeckung belegt nur, dass der Seed ausreichend eigene, kausal zugeordnete Erfahrung
erhalten hat. Sie ist kein Wirkungsnachweis. Als Nächstes folgen die beiden vorab fixierten
eingefrorenen Testfamilien Seed 101 und 103 gegen deren jeweilige Basisreferenz.
