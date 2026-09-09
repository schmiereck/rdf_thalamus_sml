---
type: Befund
title: Die Formerkennung kuerzt NICHT ueber die Farbe ab - aber die offenen Klassen wackeln
description: Umgefaerbt in die Farbe jedes anderen Koerpers bleibt die Formklasse bei den trainierten Formen zu 100 Prozent erhalten. Der Deskriptor ist farbblind, wie konstruiert. Der Test legt dafuer etwas anderes frei: obj_X wird schon in seiner EIGENEN Farbe nur in 4 von 8 Lagen richtig genannt - meist als "cube".
tags: [act23, wahrnehmung, formklassen, farbe]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-10T12:00:00Z }
sources:
  - id: probe
    resource: "src/pc_cvnn/act23_farbe_form_probe.py, 7 Koerper x 6 Fremdfarben x 8 Lagen = 336 Umfaerbungen, Zustandskopie 98a293f2"
    title: Farb-Rueckhalte-Test
---

# Anlass

Nutzerbeobachtung: *"Wir sollten mal die Farben von der Form entkoppeln. Wenn ich mich nicht
taeusche haben die Objekte immer die gleiche Farbe."* Nachgezaehlt stimmt das und ist enger als
vermutet - der Wuerfel gibt es in **drei** Farben, alle anderen Formen in genau einer, und in
**5 von 6** Farbklassen bestimmt die Farbe die Form eindeutig:

    farbe-1 -> cube | farbe-2 -> cube | farbe-5 -> cube | farbe-3 -> U | farbe-14 -> neu-9
    farbe-4 -> L UND neu-285      <- die einzige Ausnahme, und die ist eine Kollision des
                                     Chroma-Klassifikators (obj_L orange, obj_X gelbgruen),
                                     kein Design

Die Sorge dahinter: ein Netz, das "orange -> L" lernt, liegt in dieser Welt zu 100 % richtig, und
keine Messung im heutigen Aufbau koennte diese Abkuerzung von echter Formerkennung unterscheiden.
Das trifft [das Projektziel](/ziel.md) direkt.

# Antwort: die Wahrnehmung kuerzt nicht ab

Jeder Koerper wurde nacheinander in die Farbe **jedes anderen** umgefaerbt, ueber 8 Lagen und
Drehungen, alles einzeln auf dem Tisch.[^probe]

    Koerper     Formklasse gehalten   Farbklasse gewechselt (Kontrolle)
    obj_red        48/48 = 100 %          48/48 = 100 %
    obj_green      48/48 = 100 %          48/48 = 100 %
    obj_blue       48/48 = 100 %          48/48 = 100 %
    obj_L          48/48 = 100 %          40/48 =  83 %
    obj_U          48/48 = 100 %          48/48 = 100 %
    obj_T          38/48 =  79 %          48/48 = 100 %
    obj_X          22/48 =  46 %          40/48 =  83 %
    GESAMT        300/336 = 89 %         320/336 = 95 %

**Bei allen trainierten Formen (cube, L, U) haelt die Klasse zu 100 %.** Das ist die Erwartung -
der Deskriptor rechnet auf der Belegungsmaske, nicht auf der Farbe - aber sie war einen Test wert,
denn haette sie nicht gehalten, waere jede Entkopplung sinnlos gewesen, bevor der Deskriptor
repariert ist.

Die Kontrollgroesse zeigt, dass der Test wirklich faerbt (95 %). Die 83 % bei obj_L und obj_X
sind kein Fehler, sondern dieselbe Kollision wie oben: faerbt man den einen in die Farbe des
anderen, bleibt die Klasse `farbe-4` - zu Recht.

# Was der Test stattdessen freilegt

**Die selbst geborenen Klassen sind fuer sich instabil, unabhaengig von der Farbe:**

    In der EIGENEN Farbe, ueber 8 Lagen:
      obj_T   Form 'neu-9' in 6/8 Lagen
      obj_X   Form 'cube'  in 4/8 Lagen   <- haeufigste Nennung, NICHT neu-285

obj_X wird in seiner eigenen Farbe in der Haelfte der Lagen als **Wuerfel** gelesen. Das ist kein
Farbproblem und keine Verschmelzung - der Koerper steht allein auf dem Tisch. Es ist genau die
"wandernde Deskriptor"-Hypothese, die der `ACT23_TDIAG`-Kommentar seit August formuliert, hier
zum ersten Mal ausserhalb einer Verschmelzungsszene belegt.

Damit relativiert sich auch die Zahl 46 % bei umgefaerbtem obj_X: gegen einen Bezugswert von 4/8
gemessen ist sie kaum schlechter als der Ausgangszustand. **Die Farbe ist nicht das Problem, die
Klasse ist es.**

# Bewertung fuer die Entkopplung

* **Eine Entkopplung wuerde die Formerkennung NICHT brechen** - das ist die eigentliche Auskunft.
  Das Risiko liegt nicht im Klassifikator, sondern in der farbgebundenen Verrohrung:
  `colour_of_body` steuert den Farb-Split, die Rettungspfade und den ckey-Tracker. Wechselt ein
  Koerper die Farbe zwischen Episoden, ist "die Farbklasse dieses Koerpers" keine feste Groesse
  mehr. Das ist ein Umbau, kein Schalter.
* **Sie waere sogar aufdeckend.** Heute maskiert die perfekte Farb-Form-Kopplung, dass obj_X seine
  Formklasse nur in der Haelfte der Lagen haelt - der Farbpfad faengt es auf. Entkoppelt man,
  wird diese Schwaeche sichtbar statt getragen.
* **Innerhalb einer Episode darf die Farbe fest bleiben** (Nutzervorgabe) - das genuegt, damit
  Keim, Tracker und Split innerhalb der Episode weiter funktionieren. Neu zu klaeren ist nur, was
  `colour_of_body` **zwischen** den Episoden bedeutet.

# Fallen

* **Der Bezugswert muss mitgemessen werden.** Ohne die Spalte "in der eigenen Farbe" haette obj_X
  mit 46 % wie ein dramatischer Farbeffekt ausgesehen; gegen 4/8 gehalten ist es fast nichts.
* **Alles einzeln auf dem Tisch.** Verschmelzung ist hier ausgeschlossen; die Instabilitaet ist
  reine Eigenstreuung ueber Lagen.

# Verwandt

* [Projektziel](/ziel.md) - warum die Kopplung ueberhaupt ein Problem ist
* [Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md) - die instabilen offenen Klassen
* [Formklassen-Lebenszyklus](/mechanismen/formklassen-lebenszyklus.md)
