---
type: Befund
title: D0 Seed 17 - 120 Episoden Wrist-Training bringen auf Testfamilie 101 keinen Gewinn
description: Ueber beide Testfamilien verfehlt Seed 17 beide D0-Tore: ausgerichtete L-Wrists steigen 9/80 auf 17/80, Lieferung faellt 47/80 auf 44/80. Die Linie ist negativ geschlossen.
tags: [act23, dream-rsi, d0, wrist, evaluation, negativ]
status: stable
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
  - id: base-103
    resource: ../../log/d0-evaluation/seed17/base-seed103-episodes-40ep/result.json
    title: Gefrorene Basis, Seed 103
  - id: trained-103
    resource: ../../log/d0-evaluation/seed17/trained-seed103-episodes-40ep/result.json
    title: Gefrorener Seed-17-Checkpoint, Seed 103
  - id: base-actions-103
    resource: ../../log/d0-evaluation/seed17/base-seed103-episodes-40ep/episodes.jsonl
    title: Vollstaendige Basis-Aktionsfolge, Seed 103
  - id: trained-actions-103
    resource: ../../log/d0-evaluation/seed17/trained-seed103-episodes-40ep/episodes.jsonl
    title: Vollstaendige Checkpoint-Aktionsfolge, Seed 103
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

## Testfamilie 103

Die zweite, vorab festgelegte Familie besteht bei beiden Armen die Integritaetspruefung und hat
je 40 Episodenrecords. Der Checkpoint verschiebt die Wrist-Wahl deutlicher in Richtung
Ausrichtung, verliert aber Lieferung:

| Metrik | Basis | Seed 17 nach Training | Differenz |
|---|---:|---:|---:|
| Welt-Lieferung | 26/40 (65 %) | 23/40 (57,5 %) | -7,5 Punkte |
| positives Selbsturteil | 25/40 | 24/40 | -2,5 Punkte |
| ausgerichtete Wrist-Wahl (<=30 Grad) | 3/40 (7,5 %) | 7/40 (17,5 %) | +10 Punkte |
| mittlerer relativer Wrist | 62,4 Grad | 56,8 Grad | -5,6 Grad |
| Kredit-Enthaltungen | 9 | 8 | -1 |

Fisher zweiseitig: Lieferung `p = 0,647`, ausgerichtete Wahl `p = 0,115`.

# Bewertung

Ueber beide unabhängigen Testfamilien ergeben sich 47/80 gegen 44/80 Welt-Lieferungen und
9/80 gegen 17/80 ausgerichtete Wahl. Das sind -3,75 beziehungsweise +10 Prozentpunkte;
der gepoolte Fisher-Test bleibt fuer Lieferung `p = 0,750`, fuer Auswahl `p = 0,133`.

Seed 17 verfehlt damit das vorab fixierte Annahmetor: weder +10 Punkte Lieferung noch +20
Punkte ausgerichtete Wahl, und auf Seed 101 sank das Selbsturteil. Die Linie wird als
**negativ geschlossen**. Das widerlegt nicht Dream-RSI, denn dessen Auswahlsteuerung wurde
noch nicht gebaut; es widerlegt nur, dass dieses feste 120-Episoden-Rezept in Seed 17 den
geforderten D0-Lernnachweis liefert.

Der Vertrag verlangt einen zweiten unabhaengigen Trainingsseed auch fuer einen positiven
Schluss. Seed 29 wird deshalb mit unveraendertem Rezept und denselben beiden Testfamilien
ausgefuehrt; Ergebnisse werden nicht mit Seed 17 gepoolt, um einen Wirkungsnachweis zu
erzwingen.
