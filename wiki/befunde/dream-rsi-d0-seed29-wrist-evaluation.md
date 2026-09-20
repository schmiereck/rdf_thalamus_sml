---
type: Befund
title: D0 Seed 29 - Trainingsabdeckung besteht, Seed-101-Basis validiert
description: Der unveränderte 120-Episoden-Vertrag liefert 92 volle Selbst-Kredite in fünf Wrist-Zellen. Die eingefrorene Seed-101-Basisfamilie besteht Integrität und reproduziert die festgelegte Referenz exakt; der trainierte Arm und Seed 103 stehen noch aus.
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
  - id: base101-result
    resource: ../../log/d0-evaluation/seed29/base-seed101-episodes-40ep/result.json
    title: Eingefrorener Seed-101-Integritätsnachweis
  - id: base101-episodes
    resource: ../../log/d0-evaluation/seed29/base-seed101-episodes-40ep/episodes.jsonl
    title: Eingefrorenes Seed-101-Episodenprotokoll
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

# Eingefrorene Basisfamilie Seed 101

Die erneute, von der Seed-29-Linie getrennte Basisfamilie umfasst vollständig 40 Episoden.
Der Runner besteht: Rückgabecode 0, 40 von 40 Episodenzeilen, keine geänderte Lernkomponente
und identischer SHA-256 der Quell- und Arbeitskopie (`ad9d768c...c09b9e`). Damit ist sie eine
gültige eingefrorene Referenz, keine unbemerkte Fortsetzung.

| Metrik | Seed-29-Basis, Seed 101 | Frühere Seed-17-Basis, Seed 101 |
|---|---:|---:|
| Welt-Lieferung | 21/40 (52,5 %) | 21/40 (52,5 %) |
| Selbst-Lieferung | 23/40 (57,5 %) | 23/40 (57,5 %) |
| Selbst gefunden | 39/40 (97,5 %) | 39/40 (97,5 %) |
| ausgerichtete relative Wrist <= 30° | 6/40 (15 %) | 6/40 (15 %) |
| Enthaltungen | 8/40 (20 %) | 8/40 (20 %) |

Alle vorab festgelegten Zähler stimmen zeilenweise mit der bereits dokumentierten Seed-17-
Basisfamilie überein. Das ist ein enger Reproduzierbarkeitsbefund für diesen eingefrorenen
Evaluator und diese konkrete Basis; es ist noch kein Lernvergleich und keine Aussage über den
Seed-29-Checkpoint.

# Nächster Schritt

Die Kreditabdeckung belegt nur, dass der Seed ausreichend eigene, kausal zugeordnete Erfahrung
erhalten hat. Sie ist kein Wirkungsnachweis. Als Nächstes folgt der Seed-29-Checkpoint gegen
diese feststehende Seed-101-Referenz, anschließend die vorab fixierte Familie Seed 103.
