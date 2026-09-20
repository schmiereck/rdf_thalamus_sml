---
type: Befund
title: D0 Seed 17 - 120 Episoden Wrist-Training bringen auf Testfamilie 101 keinen Gewinn
description: Gegen die gefrorene Basis bleibt Lieferung bei 21/40; ausgerichtete L-Wrists steigen nur 6/40 auf 8/40, das Selbsturteil sinkt 23 auf 21. Die zweite festgelegte Testfamilie steht noch aus.
tags: [act23, dream-rsi, d0, wrist, evaluation, negativ]
status: draft
evidenz: einzelmessung
ebene: act23-ab
generated: { by: codex, at: 2026-09-20T08:00:00Z }
sources:
  - id: protocol
    resource: /messungen/dream-rsi-d0-wrist-lernaufgabe.md
    title: Fixierter D0-Pilotvertrag v1
  - id: base
    resource: ../../log/d0-evaluation/seed17/base-seed101-episodes-40ep/result.json
    title: Gefrorene Basis, Seed 101
  - id: trained
    resource: ../../log/d0-evaluation/seed17/trained-seed101-episodes-40ep/result.json
    title: Gefrorener Seed-17-Checkpoint, Seed 101
  - id: base-actions
    resource: ../../log/d0-evaluation/seed17/base-seed101-episodes-40ep/episodes.jsonl
    title: Vollstaendige Basis-Aktionsfolge
  - id: trained-actions
    resource: ../../log/d0-evaluation/seed17/trained-seed101-episodes-40ep/episodes.jsonl
    title: Vollstaendige Checkpoint-Aktionsfolge
---

# Behauptung

Der regulaere Seed-17-Checkpoint nach 120 D0-Trainingsfolgen zeigt in der ersten vorab
festgelegten, eingefrorenen 40-Episoden-Testfamilie keinen Liefergewinn gegen die Basis. Die
Wrist-Wahl bewegt sich geringfuegig in die erwartete Richtung, erreicht aber das D0-Tor bei
weitem nicht.

# Aufbau

Beide Arme laufen kopflos mit FSM, `L-Form`, `ACT23_SEED=101` und `ACT23_D0_FREEZE=1` auf
je einer neuen Checkpoint-Kopie. Die Basis stammt aus `base.pkl`; der Trainingsarm aus
`seed17-block120/state-trained.pkl`. Beide Resultate bestehen: 40 Episodenrecords, leere
Lernzustandsdifferenz und bitgleicher Hash der jeweiligen verwendeten Kopie.

`episodes.jsonl` enthält pro ausgeführter Selbstaktion den gefalteten relativen Wrist auch bei
Kredit-Enthaltung. Ausgerichtet bedeutet für die L-Form wie im historischen Befund 0--30 Grad.
Der Fisher-Test ist nach Vertrag nur deskriptiv.

# Zahlen

| Metrik | Basis | Seed 17 nach Training | Differenz |
|---|---:|---:|---:|
| Welt-Lieferung | 21/40 (52,5 %) | 21/40 (52,5 %) | 0 Punkte |
| positives Selbsturteil | 23/40 | 21/40 | -5 Punkte |
| ausgerichtete Wrist-Wahl (<=30 Grad) | 6/40 (15 %) | 8/40 (20 %) | +5 Punkte |
| mittlerer relativer Wrist | 63,0 Grad | 59,6 Grad | -3,4 Grad |
| Kredit-Enthaltungen | 8 | 8 | 0 |

Lieferung: Fisher zweiseitig `p = 1,0`. Ausgerichtete Wahl: `p = 1,0`. Der Checkpoint hat
somit weder den geforderten Lieferzuwachs von +10 Punkten noch den Auswahlzuwachs von +20
Punkten erreicht; das Selbsturteil ging zugleich zurueck.

# Bewertung

Dies ist ein negativer Zwischenbefund für Seed 17, keine Aussage über Dream-RSI als
Trainingssteuerung. Die zweite, vorab festgelegte Testfamilie Seed 103 wird noch mit derselben
Basis und demselben Checkpoint gefahren. Erst danach wird Seed 17 als negative Linie geschlossen
oder ein technischer Widerspruch untersucht. Ein zweiter Trainingsseed darf nicht nach einem
günstigeren Ergebnis gesucht werden; der Vertrag verlangt zwei unabhängige Linien für einen
positiven Schluss.
