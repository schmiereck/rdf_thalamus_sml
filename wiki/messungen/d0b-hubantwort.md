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

# Replikationsvertrag v1

Die explorative Seed-101-Auswertung ist abgeschlossen und wird nicht mehr für Wahl oder Tuning
benutzt. Für zwei neue, vollständig eingefrorene Familien mit Seeds 103 und 107 gilt unverändert:

* Eine Trajektorie ist nur bei mindestens zwei `lift`-Frames mit festem Blick und vollständigem
  `selection_cell_com` gültig.
* Der einzige Prädiktor ist die euklidische Distanz zwischen erstem und letztem Zell-Schwerpunkt.
  Er lautet `getragen` ab 1,50 Zellen, `nicht getragen` bis 0,75 Zellen und sonst `Enthaltung`.
* Der Auswerter liest die Wahrheit erst nach Erzeugung dieser drei Labels. Er prüft außerdem die
  Zeilen- und ID-Gleichheit beider Dateien und bricht bei einem Liftframe ohne festen Blick ab.
* Jede Familie umfasst 20 Episoden und braucht mindestens 12 gültige Trajektorien. Fehlt diese
  Abdeckung, ist sie technisch unentschieden und wird nicht durch Nachziehen der Episodenzahl
  ersetzt.
* Der Wahrnehmungskandidat besteht nur, wenn beide Familien mindestens 0,80 Precision für
  `getragen`, mindestens 0,50 Recall über alle tatsächlich getragenen gültigen Trajektorien und
  höchstens 0,50 Enthaltungen erreichen. Ein einziger Verstoß verwirft diese feste Rohantwort;
  kein Schwellen- oder Merkmals-Tuning folgt.

Ausführbarer Auswerter:

```powershell
..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_d0b_lift_response_audit.py `
  log\d0b-lift-response\seed103-20ep --output log\d0b-lift-response\seed103-20ep\audit.json
```

# Replikation Seed 103: verworfen

Seed 103 liefert 20 vollständige Episoden, 17 gültige Lifttrajektorien und unveränderte
Basis-SHA `ad9d768c...c09b9e`; der Lauf hat keine Lernkomponenten geändert. Der festgelegte
Auswerter erzeugt 14-mal `getragen`, einmal `nicht getragen` und zweimal Enthaltung. Gegen die
erst nach der Labelbildung gelesene Wahrheit sind dies TP=11, FP=3, FN=1, TN=0: Precision
0,786, Recall 0,846 und Enthaltung 0,118.

Die Abdeckung, Recall- und Enthaltungs-Tore bestehen, die Precision verfehlt mit 0,786 jedoch
das vorab festgelegte 0,80-Tor. Nach dem Vertrag verwirft bereits dieser Verstoß die feste
Rohantwort; Seed 107 wird deshalb nicht als Rettungs-, Schwellen- oder Merkmals-Tuning
ausgeführt. Der negative Befund steht in [D0b-Hubantwort](/befunde/d0b-hubantwort.md).
