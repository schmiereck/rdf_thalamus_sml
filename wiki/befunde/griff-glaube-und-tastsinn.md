---
type: Befund
title: Kein Glaubensfehler, und der Tastsinn traegt die Schliess-Entscheidung nicht
description: Zwei ehrliche Negative aus derselben Diagnosereihe. Der Zustand vor dem ERSTEN Griffversuch ist in Erfolg und Misserfolg identisch (12,8 gegen 13,0 mm); der Fingerdruck kann die Hoehenschwelle dreifach gemessen nicht ersetzen.
tags: [act23, greifen, tastsinn, negativ]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-08-28T09:57:00Z }
verified: { by: human:thomas, at: 2026-08-28T09:57:00Z }
sources:
  - id: glaub
    resource: /raw/index.md
    title: ACT16_GLAUBDIAG, 80 Episoden, 8 Seeds
  - id: tast
    resource: /raw/index.md
    title: ACT16_TASTDIAG / ACT16_TASTGRIFF, 40 bzw. 6x40 Episoden
---

# Behauptung 1: Es gibt keinen Glaubensfehler

Der Zustand vor dem **ersten** Griffversuch - dem unverfaelschten - ist in beiden Gruppen
gleich. Alles Trennende entsteht **danach**.

    Schliesszeitpunkt (erster Versuch)   12,8 mm (geliefert) gegen 13,0 mm (daneben) -- gleich
    Hoehenglaube |cz_st - wahr|           2,3 gegen 1,5 mm -- in Misserfolgen BESSER
    Seitliche Lokalisierung, NUR erste Anfahrt   3,9 gegen 6,1 mm, p = 0,249 -- nicht belegt
    Phantom-Griff (_holding waehrend das Objekt liegt)  31 gegen 38 Schritte -- ZAEHLARTEFAKT
      der Ablagephase (ab Schritt ~380 in BEIDEN Gruppen)

Die urspruengliche Lesart war: in gescheiterten Episoden liege der Schliesswunsch in 67 % der
Schritte zu hoch - "eine Policy, die die ganze Episode ueber woanders zu sein glaubt". **Die
Lesart war falsch.** Der erste Griff geht daneben, die Episode schleift in Wiederholungen
(Median 506 -> 956 Schritte), und jeder Zyklus verbringt viele Schritte hoch mit geschlossener
Klaue. Die 67 % waren ein **Symptom** des Schleifens und damit zirkulaer zum Misserfolg.

# Die Falle, die fast getaeuscht haette

Ueber **alle** Anfahrten gemittelt sah der Ortsfehler nach einem Befund aus (4,3 gegen 7,6 mm,
p = 0,018). Das war ein **Richtungsfehler**: gescheiterte Episoden fahren mehrfach an, und die
spaeteren Anfahrten sehen ein Objekt, das der erste Fehlgriff schon angestossen hat - der
Ortsfehler ist dort **Folge**, nicht Ursache. Auf die erste Anfahrt begrenzt faellt der
Unterschied auf +2,2 mm und p = 0,249. Kontrolle mitgefahren: die erste Anfahrt ist in beiden
Gruppen gleich lang (362 gegen 372 Schritte).

# Behauptung 2: Der Fingerdruck kann die Hoehenschwelle nicht ersetzen

Der Fingerdruck liegt als `state[11:13]` im Policy-Zustand. Die Policy lernt ihn trotzdem nicht
fuer den Schliesszeitpunkt, weil der **Teacher ihn bewusst nicht liest** und rein nach Hoehe
entscheidet (`act16:186`, `if hz > grasp_z + 0.012`). Ein Netz kann nicht lernen, was im Etikett
nicht vorkommt.

    1. Abstiegs-Stillstand als Ersatz (40 Ep): der Abstieg kommt 40/40 NIE zum Stillstand.
       Die Backen fahren am Objekt VORBEI nach unten statt darauf aufzusetzen
       (tiefster Punkt Median -0,3 mm, Spanne -5,5..+15,0).
       "Schliesse, wenn du stehen bleibst" existiert in dieser Geometrie nicht.
    2. Druck als Ausloeser: die OFFENE Klaue misst in 26/40 Episoden exakt 0,00 N.
       Der Streifen sitzt innen und meldet erst, wenn die Backen druecken.
    3. Gefuehlter Leergriff (gebaut, dort gemessen wo die Regel FAEHRT, 6 Seeds x 40 Ep gepaart):
       128/240 gegen 129/240, +0,4 Punkte, p = 1,000; Endabstand 39,1 -> 39,9 mm.
       Die Regel feuerte 431x - sie ist nicht stumm, sie ist wirkungslos.

Warum: die Regel liefert dasselbe Teilziel wie die vorhandene Wiederhol-Regel, nur frueher.
**Frueher zu merken, dass die Klaue leer ist, hilft nicht - der Fehler ist zu diesem Zeitpunkt
schon passiert.** Der leere Griff ist die Folge, nicht die Ursache.

# Zwei eigene Aufbaufehler

* **`reactive_subgoal` FAEHRT in act23 nirgends.** Es wird an genau einer Stelle gerufen
  (`pc_act23.py:1440`) und dort als DAgger-**Etikett**. Weder "Choreo: Netz" noch "fsm" testen
  eine Aenderung darin als Verhalten; der fsm-Arm kam folgerichtig exakt 57/120 gegen 57/120
  heraus. **Wer eine Teacher-Regel als VERHALTEN messen will, muss sie als `policy_fn`
  uebergeben.**
* **Einen Untergruppen-Befund aus 14 Episoden nicht als Befund fuehren.** Der U-Form-Verdacht
  (4/14 = 29 % gegen 39/66 = 59 %, p = 0,0444) **repliziert nicht**: im Langlauf mit n = 192
  sind es 39,1 % gegen 45,9 %, p = 0,0936. Ein klassischer Kleinstichprobeneffekt.

# Folgen

Die Suche nach einem Wahrnehmungs- oder Zustandsfehler als Ursache der Greif-Fehlschlaege ist
**erledigt** - es gibt keinen. Wer die Quote heben will, muss an der Greifgeometrie ansetzen,
nicht an Fovea oder Objektglauben.

Der verbleibende offene Hebel aus derselben Diagnose ist **kein Quotenthema, sondern eines der
Echtheit**: `obj_h` stammt aus `geom_half(cmd)`, also aus der echten MuJoCo-Geometrie -
`grasp_z` ist damit **privilegiert**, im Teacher, im Riegel und als Policy-Eingang (Dim 9). Auf
echter Hardware existiert der Wert nicht. Groesserer Hebel als der Riegel.

Werkzeuge: `ACT16_RULEDIAG`, `ACT16_GLAUBDIAG`, `ACT16_TASTDIAG` bleiben (alle Vorgabe AUS,
verhaltensneutral, bitgleich geprueft) - sie haben in einer Sitzung dreimal einen Fehlschluss
verhindert. `ACT16_TASTGRIFF` ist wieder entfernt; die Begruendung steht als Notiz an der
Konstante.

# Verwandt

* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) - die Riegel-Messung, die das ausgeloest hat
* [1109 Episoden ohne Lernfortschritt](/befunde/langlauf-ohne-fortschritt.md)
