---
type: Befund
title: D0 Seed 29 - Seed-101-Checkpoint verfehlt beide Lernmetriken
description: Der unveränderte 120-Episoden-Vertrag liefert 92 volle Selbst-Kredite in fünf Wrist-Zellen. Gegen die valide Seed-101-Basis sinkt Lieferung von 21/40 auf 19/40, die ausgerichtete Wrist-Wahl bleibt 6/40 und das Selbsturteil sinkt; Seed 103 steht noch aus.
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
  - id: trained101-result
    resource: ../../log/d0-evaluation/seed29/trained-seed101-episodes-40ep/result.json
    title: Eingefrorener Seed-29-Checkpoint, Seed 101, Integritätsnachweis
  - id: trained101-episodes
    resource: ../../log/d0-evaluation/seed29/trained-seed101-episodes-40ep/episodes.jsonl
    title: Eingefrorenes Seed-29-Checkpoint-Episodenprotokoll, Seed 101
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

# Seed-29-Checkpoint, Familie Seed 101

Der Checkpoint wird getrennt in eine Wegwerfkopie geladen und mit demselben Freeze getestet.
Auch dieser Lauf besteht die technische Kontrolle: Rückgabecode 0, 40/40 Episodenzeilen,
leerer Lernzustands-Diff und bitgleicher Hash der Checkpointkopie vor/nach der Evaluation
(`d041348e...88e3`). Der Vergleich ist daher auswertbar.

| Metrik | Basis | Seed 29 nach Training | Differenz | Fisher, zweiseitig |
|---|---:|---:|---:|---:|
| Welt-Lieferung | 21/40 (52,5 %) | 19/40 (47,5 %) | -5 Punkte | 0,823 |
| Selbst-Lieferung (Selbsturteil) | 23/40 (57,5 %) | 20/40 (50 %) | -7,5 Punkte | 0,654 |
| Selbst gefunden | 39/40 (97,5 %) | 40/40 (100 %) | +2,5 Punkte | - |
| ausgerichtete relative Wrist <= 30° | 6/40 (15 %) | 6/40 (15 %) | 0 Punkte | 1,000 |
| Enthaltungen | 8/40 (20 %) | 10/40 (25 %) | +5 Punkte | - |

Damit verfehlt Seed 29 schon auf der ersten Testfamilie alle positiven D0-Schwellen: keine
Steigerung der Ausrichtung, Lieferung nicht um +10 Punkte und ein Rückgang des Selbsturteils.
Der Vertrag verlangt dennoch die zweite, unabhängige Familie Seed 103, bevor die Linie
geschlossen wird. Die Fisher-Werte sind wegen 40 Episoden pro Arm nur deskriptiv.

# Nächster Schritt

Die Kreditabdeckung belegt nur, dass der Seed ausreichend eigene, kausal zugeordnete Erfahrung
erhalten hat. Sie ist kein Wirkungsnachweis. Seed 101 liefert nun einen negativen Zwischenbefund.
Als Nächstes folgt die vorab fixierte Familie Seed 103, erst danach die Linienentscheidung.
