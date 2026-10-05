---
type: Befund
title: D0 Seed 29 - 120 Episoden verfehlen den Wrist-Lernvertrag
description: Der unveränderte 120-Episoden-Vertrag liefert 92 volle Selbst-Kredite in fünf Wrist-Zellen. Seed 101 verliert Lieferung und Selbsturteil, Seed 103 gewinnt Lieferung, aber nur +7,5 statt +20 Punkte Ausrichtung. Gepoolt steigen Lieferung und Ausrichtung jeweils nur +3,75 Punkte; die Linie ist negativ geschlossen.
tags: [act23, dream-rsi, d0, wrist, evaluation, seed29]
status: stable
evidenz: gemessen
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
  - id: base103-result
    resource: ../../log/d0-evaluation/seed29/base-seed103-episodes-40ep/result.json
    title: Eingefrorener Seed-103-Integritätsnachweis
  - id: base103-episodes
    resource: ../../log/d0-evaluation/seed29/base-seed103-episodes-40ep/episodes.jsonl
    title: Eingefrorenes Seed-103-Episodenprotokoll
  - id: trained103-result
    resource: ../../log/d0-evaluation/seed29/trained-seed103-episodes-40ep/result.json
    title: Eingefrorener Seed-29-Checkpoint, Seed 103, Integritätsnachweis
  - id: trained103-episodes
    resource: ../../log/d0-evaluation/seed29/trained-seed103-episodes-40ep/episodes.jsonl
    title: Eingefrorenes Seed-29-Checkpoint-Episodenprotokoll, Seed 103
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

# Eingefrorene Basisfamilie Seed 103

Die zweite Basisfamilie ist ebenfalls vollständig und integer: Rückgabecode 0, 40/40
Episodenzeilen, keine geänderte Lernkomponente sowie bitgleicher Quell- und Arbeitskopiehash
(`ad9d768c...c09b9e`). Ihre Kennzahlen reproduzieren die frühere Seed-17-Basisfamilie mit Seed
103 exakt.

| Metrik | Seed-29-Basis, Seed 103 |
|---|---:|
| Welt-Lieferung | 26/40 (65 %) |
| Selbst-Lieferung (Selbsturteil) | 25/40 (62,5 %) |
| Selbst gefunden | 40/40 (100 %) |
| ausgerichtete relative Wrist <= 30° | 3/40 (7,5 %) |
| Enthaltungen | 9/40 (22,5 %) |

# Seed-29-Checkpoint, Familie Seed 103

Der letzte Vergleichslauf ist ebenfalls technisch gültig: Rückgabecode 0, 40/40 Episodenzeilen,
leerer Lernzustands-Diff und bitgleicher Checkpointhash vor/nach der Evaluation
(`d041348e...88e3`).

| Metrik | Basis | Seed 29 nach Training | Differenz | Fisher, zweiseitig |
|---|---:|---:|---:|---:|
| Welt-Lieferung | 26/40 (65 %) | 31/40 (77,5 %) | +12,5 Punkte | 0,323 |
| Selbst-Lieferung (Selbsturteil) | 25/40 (62,5 %) | 31/40 (77,5 %) | +15 Punkte | 0,222 |
| Selbst gefunden | 40/40 (100 %) | 39/40 (97,5 %) | -2,5 Punkte | - |
| ausgerichtete relative Wrist <= 30° | 3/40 (7,5 %) | 6/40 (15 %) | +7,5 Punkte | 0,481 |
| Enthaltungen | 9/40 (22,5 %) | 3/40 (7,5 %) | -15 Punkte | - |

Seed 103 erfüllt die Lieferschwelle und verschlechtert sein Selbsturteil nicht, erreicht aber
nicht die notwendige Ausrichtungssteigerung von mindestens +20 Punkten. Die Fisher-Werte sind
bei 40 Episoden pro Arm rein deskriptiv.

# Abschluss Seed 29 und D0

| Metrik | Basis, beide Familien | Seed 29 nach Training | Differenz | Fisher, zweiseitig |
|---|---:|---:|---:|---:|
| Welt-Lieferung | 47/80 (58,75 %) | 50/80 (62,5 %) | +3,75 Punkte | 0,746 |
| Selbst-Lieferung (Selbsturteil) | 48/80 (60 %) | 51/80 (63,75 %) | +3,75 Punkte | 0,745 |
| ausgerichtete relative Wrist <= 30° | 9/80 (11,25 %) | 12/80 (15 %) | +3,75 Punkte | 0,640 |

Der gepoolte Vergleich ist nur beschreibend; der Vertrag fordert den Effekt ohnehin in **beiden**
unabhängigen Trainingslinien. Seed 17 war bereits negativ geschlossen (Ausrichtung +10 statt
+20 Punkte, Lieferung -3,75 Punkte). Seed 29 verfehlt Seed 101 bei Lieferung, Selbsturteil und
Ausrichtung; auf Seed 103 bleibt die Ausrichtung unter der Schwelle. Damit besteht keine der
beiden Linien den D0-Pilotvertrag.

D0 ist als negativer Pilot geschlossen. Das widerlegt weder die Dream-RSI-Idee noch spätere
Trainingssteuerung, aber es widerlegt für diese Basis und dieses unveränderte 120-Episoden-Rezept
einen belastbaren Nachweis, dass Selbst-Kredit die objektrelative Wrist-Auswahl verbessert.
Es folgt kein Nachtraining, Pooling als positiver Ersatzschluss oder Parametertuning. Eine
Wiederaufnahme benötigt einen neuen D0-Kandidaten samt vor dem Lauf festgelegtem Vertrag.

Die Kreditabdeckung belegt nur, dass der Seed ausreichend eigene, kausal zugeordnete Erfahrung
erhalten hat. Sie ist kein Wirkungsnachweis. Seed 101 liefert einen negativen Zwischenbefund;
die Seed-103-Basis liegt nun integer vor. Als Nächstes folgt der Seed-29-Checkpoint auf dieser
vorab fixierten Familie, erst danach die Linienentscheidung.
