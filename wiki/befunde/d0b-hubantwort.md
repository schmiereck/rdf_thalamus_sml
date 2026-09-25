---
type: Befund
title: D0b-Hubantwort - feste Fovea zeigt einen Kandidaten für den visuellen Greifzustand
description: Bei festem Blick verschiebt sich der Fovea-Auswahlschwerpunkt in sechs getragenen Lifttrajektorien stärker als in vier Fehlgriffen; die Einzelmessung ist noch kein Klassifikator.
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
---

# Behauptung

Eine eigene Hubbewegung erzeugt bei festem Fovea-Blick einen sichtbaren Kandidaten für
„Objekt wird mit der Hand bewegt“. Der rohe, relativ zum Blick gemessene Auswahl-Schwerpunkt
verändert sich in dieser kleinen Probe bei getragenen Objekten stärker als bei Fehlgriffen.

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

# Folgen

D0b bleibt auf Prüfstandsebene offen. Als nächstes wird ein separater Vertrag für eine
Replikationsfamilie festgelegt: die hier festgelegte Rohantwort wird ohne Nachanpassung gegen
eine einfache, enthaltende Klassifikation geprüft, nach ganzen Trajektorien und mit weiterhin
getrennter Tragewahrheit. Erst ein bestandener, reproduzierter Wahrnehmungsbefund erlaubt einen
lernenden Verbraucher im ACT23-Pfad.
