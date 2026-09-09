---
type: Befund
title: Warum der Split die Formklasse verliert - halbe Silhouette, knapp verfehlte Schwelle
description: Der Farb-Split behaelt nur 31 bis 58 Prozent der Pixel des Objekts. Der Deskriptor dieser halben Silhouette landet knapp jenseits von novel_th (Faktor 0,94 bis 1,55), und resolve() antwortet fast immer mit "neuartig" statt mit einer falschen Klasse. Der Ausfall ist eine Enthaltung, keine Verwechslung.
tags: [act23, wahrnehmung, split, formklassen]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-09T23:30:00Z }
sources:
  - id: probe
    resource: "src/pc_cvnn/act23_formsplit_probe.py, 3 Paare x 4 Abstaende x 24 Lagen, nur die verschmolzenen Faelle ausgewertet (87 Konstellationen), Zustandskopie 98a293f2"
    title: Form-Split-Diagnose
---

# Frage

Aus [der Abstandskurve](/befunde/verschmelzung-abstandskurve.md): der Farb-Split rettet ab 35 mm
die **Position** zu 100 %, die **Formklasse** aber nur zu 42 %. Warum?

Zwei Kandidaten mit verschiedenen Reparaturen: **A** die Silhouette wird beschnitten (dann muss
der Fussabdruck gerettet werden), **B** der Deskriptor liegt nur knapp jenseits der
Neuheitsschwelle (dann ist es eine Kalibrierfrage).

# Antwort: beide, und A verursacht B

    novel_th = 7,715

    Paar              d    n | Flaeche solo  Split  Anteil | kNN/novel_th solo  Split | richtig  novel
    obj_L neben U    25   11 |         487    152    0,31  |             0,47    1,35 |   0/11     11
                     35   14 |         517    254    0,49  |             0,45    1,21 |   1/14     13
                     45    8 |         500    266    0,53  |             0,44    1,08 |   3/8       5
                     55    4 |         541    312    0,58  |             0,44    1,01 |   2/4       2
    obj_T neben U    25   17 |         466    191    0,41  |             1,30    1,55 |   5/17     12
                     35    9 |         465    259    0,56  |             1,28    1,38 |   5/9       4
                     45   10 |         472    232    0,49  |             1,32    1,50 |   7/10      2
                     55    9 |         488    277    0,57  |             1,22    1,50 |   7/9       1
    obj_U neben L    25    3 |         804    661    0,82  |             0,50    0,94 |   1/3       1
                     35    2 |         845    552    0,65  |             0,53    1,08 |   0/2       2

* **A ist gross:** der Splitteil behaelt nur **31-58 %** der Pixel, die derselbe Koerper allein
  hat. Der Docstring von `perceive_colour` sagt es selbst - der Split *"drops shaded/edge
  pixels"*; die Messung beziffert es auf **rund die Haelfte**.
* **B folgt daraus:** der kNN-Abstand des Deskriptors springt von 0,44-0,53 (obj_L, obj_U, tief
  im Basisraum) auf **0,94-1,35**, also knapp ueber die Schwelle. Bei obj_L faellt er mit
  wachsendem Abstand monoton zurueck Richtung 1,0 - genau parallel dazu steigt die
  Wiedererkennung von 0/11 auf 2/4.
* **Der Ausfall ist eine ENTHALTUNG, keine Verwechslung.** In 55 von 58 Fehlern antwortet
  `resolve()` mit `None` ("neuartig"); nur **dreimal** kommt eine fremde Klasse heraus. Das ist
  die gutartigste Fehlerform, die es hier geben kann - und der Grund, warum eine gelockerte
  Schwelle nicht sofort Fehletiketten produzieren wuerde.

# Was das fuer eine Reparatur heisst

Drei Wege, keiner gebaut, in aufsteigender Eingriffstiefe:

1. **Kontinuitaet statt Neuklassifikation.** Der Tracker verlangt in **jedem Bild** erneut
   `d["shape"] == key` (`make_shape_track`). Die Identitaet steht aber schon fest - sie kommt aus
   der Adressierung und seit `d85250b` aus dem Keim. Gebraucht wird je Bild nur die **Position**,
   und die rettet der Split ab 35 mm vollstaendig. Faellt die Klasse aus, koennte der Tracker dem
   naechstgelegenen Splitteil innerhalb der 5-cm-Sprungschranke folgen, statt blind zu werden -
   genau das tut der farbgefuehrte Zweig bereits (`perceive_colour` ohne `with_form`).
   **Kein neuer Schwellenwert, keine Aenderung an der Wahrnehmung.** Risiko: es ist derselbe
   Mechanismus, der bei falschem Start die Ablenker-Bindung traegt - `ACT16_ABLENKDIAG` misst
   genau das mit.
2. **Kontextabhaengige Schwelle.** Die Detektion weiss bereits, dass sie aus dem Split stammt
   (`d["split"] = True`). Wer das weiss, darf nicht dieselbe Passgenauigkeit verlangen. Ein
   Faktor um 1,5 auf `novel_th` deckt fast alle gemessenen Faelle ab (0,94-1,55). Billig und
   messbar - aber es ist eine **Schwelle mehr**, und die Dicken-Wache hat gezeigt, dass Schwellen
   hier gern Kaskaden ausloesen ([Formklassen-Lebenszyklus](/mechanismen/formklassen-lebenszyklus.md)).
3. **Den Fussabdruck retten.** Naht-, Schatten- und Mischpixel morphologisch zurueckholen, damit
   die Silhouette wieder vollstaendig wird. Das ist die Ursache selbst - aber der tiefste
   Eingriff, und `perceive_all`/`perceive_colour` sind ausdrueckliches
   [Uebergangsgeruest](/ziel.md), das abgebaut und nicht ausgebaut werden soll.

**Empfehlung: Weg 1.** Er behebt die Wirkung dort, wo sie entsteht (der Servo wird blind, nicht
die Wahrnehmung falsch), braucht keinen neuen Parameter, und die Gegenprobe existiert schon.

# Fallen

* **obj_T sitzt schon solo ueber der Schwelle** (kNN/novel_th 1,22-1,32). Es ist eine selbst
  benannte offene Klasse und wird ueber die zweite Stufe von `resolve()` (relaxierter
  Anspruchsradius `OPEN_MARGIN * novel_th`) erkannt, nicht ueber die Basisklassen. Wer die
  Spalte als "obj_T wird solo nicht erkannt" liest, liest sie falsch.
* **Nur verschmolzene Faelle sind ausgewertet** (87 von 288 Konstellationen). Bei den getrennten
  stellt sich die Frage nicht.

# Verwandt

* [Verschmelzung: die Abstandskurve](/befunde/verschmelzung-abstandskurve.md) - die Frage
* [Nachbarnaehe im Lauf](/befunde/nachbarnaehe-im-lauf.md) - warum es zaehlt (13,9 Punkte)
* [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md)
