---
type: Messvorschrift
title: D0b-Hubantwort - fester Fovea-Blick während eigener Hubbewegung
description: Eingefrorener Prüfstand: Der Fovea-Blick bleibt während der Lift-FSM fixiert; relative Auswahlposition, Masse und Topzustand werden nur gegen getrennte Tragewahrheit ausgewertet.
tags: [act23, dream-rsi, d0b, fovea, hub, selbstbewegung]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: codex, at: 2026-09-25T15:00:00Z }
---

# Vertrag

`ACT23_D0B_LIFT_PROBE=1` friert ausschließlich im FSM-Abschnitt `lift` den aktuellen Fovea-Blick
fest. Er ändert weder Ziel, Greifer, Teacher, Servo-Rückgabe noch Lerngewichte. Der Trace enthält
nur den relativen Auswahl-Schwerpunkt im Fovea-Zellraster, Auswahlmasse, Topzustand, Blick und
eigene Handpose. Objektpose und Tragen stehen ausschließlich in der getrennten Evaluationsdatei.

Ein erster eingefrorener 12-Episoden-Lauf prüft nur Beobachtbarkeit: vollständige IDs, mindestens
30 gültige Liftpaare mit festem Blick und getrennte Auswertung der Bildänderung gegen Tragen.
Keine Klassifikation und kein Kopf vor diesem Audit.

# Ergebnis Seed 101

Der Lauf ist vollständig: `result.json` meldet 12 Episoden, Rückgabecode 0, unveränderte
Basis-SHA-256 `ad9d768c...c09b9e` und keine geänderten Lernkomponenten. Die 3.359 Fovea-Frames
haben je eine getrennte Evaluationszeile mit gleicher äußerer Episoden-ID und FSM-Phase.

| Größe | Wert |
|---|---:|
| Lift-Frames / Blick tatsächlich fixiert | 389 / 389 |
| Episoden mit beobachtetem Lift | 10 / 12 |
| gültige benachbarte Liftpaare | 379 |
| vollständiger relativer Auswahlschwerpunkt | 389 / 389 |
| am Liftende tatsächlich getragen | 6 / 10 |

Für jede der zehn Trajektorien wird nur die Differenz zwischen erstem und letztem
Festblick-Liftframe betrachtet. Der Betrag der Änderung des Auswahl-Schwerpunkts im
16×16-Fovea-Zellraster liegt bei den sechs am Ende getragenen Objekten bei Median 3,89 Zellen,
bei den vier nicht getragenen bei 0,60 Zellen. Der explorative exakte Permutationstest ergibt
einseitig `p = 0,057` (zweiseitig `p = 0,114`, n=6 gegen n=4). Auswahlmasse und Topzustand
trennen die beiden Gruppen in dieser kleinen Stichprobe nicht klar.

Damit ist der Beobachtbarkeitsvertrag erfüllt, aber kein Greifzustandsklassifikator belegt:
die Schwelle, die in diesen Daten vier von sechs getragenen Fällen und keinen der vier
Fehlgriffe auswählt, wäre nachträglich gewählt. Der nächste zulässige Schritt ist eine
unabhängige, vorab mit diesem Merkmalsvektor und Enthaltungskriterium festgelegte
Replikationsfamilie; erst dort darf eine Klassifikationsgüte gegen die getrennte Wahrheit
bewertet werden. Der Befund steht in [D0b-Hubantwort](/befunde/d0b-hubantwort.md).
