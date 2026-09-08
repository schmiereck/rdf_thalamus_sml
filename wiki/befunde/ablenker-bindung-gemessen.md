---
type: Befund
title: Der Tracker rastet auf dem Nachbarn ein - direkt gemessen
description: Die Ablenker-Bindung ist bestaetigt und lokalisiert. Der Belief, dem die Policy folgt, sitzt in gescheiterten Episoden dreimal so oft auf einem FREMDEN Koerper wie in gelieferten (31,2 gegen 4,2 Prozent, Fisher p = 0,0086) - und zwar auf 4 mm genau, also als sichere Bindung, nicht als Drift. Der Fehler sitzt im laufenden Tracker, nicht in der Adressierung.
tags: [act23, wahrnehmung, tracker, ausfuehrung]
status: stable
evidenz: gemessen
ebene: langlauf
generated: { by: claude/opus-5, at: 2026-09-08T21:00:00Z }
sources:
  - id: diag
    resource: "Kopfloser Steuerungslauf mit ACT16_ABLENKDIAG=1 und ACT16_GLAUBDIAG=1, 64 auswertbare Episoden, auf einer Kopie von act23_state.pkl (f9976054)"
    title: Ablenker-Diagnoselauf
  - id: vorlaeufer
    resource: /befunde/ablenker-anfahrt.md
    title: Der Befund, der diese Messung ausgeloest hat
---

# Behauptung

Die in [Ablenker-Bindung in der Anfahrt](/befunde/ablenker-anfahrt.md) vermutete Ursache ist
bestaetigt und praezise lokalisiert: **der Objekt-Belief `c`, dem die Policy waehrend der Anfahrt
folgt, rastet auf einem Nachbarkoerper ein.** Nicht als allmaehliche Drift - der Belief steht dann
rund 4 mm neben dem **falschen** Koerper und ueber 50 mm neben dem richtigen. Es ist eine sichere
Bindung an das falsche Objekt.

Die Adressierung ist daran unschuldig; sie liefert das richtige Ziel (Median 2 mm). Der Fehler
entsteht danach, im laufenden Tracker.

# Aufbau

Neue Diagnose `ACT16_ABLENKDIAG=1` (Vorgabe aus), gebaut nach dem Vorbild von `GLAUBDIAG`:
**privilegiert und ausschliesslich messend** - die wahren Koerperlagen gehen in keinen Lerner, in
keinen Zustand und in keine Entscheidung, nur in Zaehler. Gezaehlt wird ausschliesslich waehrend
der Anfahrt (`over`/`lower`/`close`); danach traegt die Hand das Objekt und `c` folgt
absichtlich der Hand (`_cobs`).

Je Episode: auf welchen der Koerper zeigt `c`, ab welchem Schritt weicht das vom kommandierten
ab, welcher gewinnt, und wie weit steht `c` von beiden.

# Zahlen

64 auswertbare Episoden.[^diag]

    Belief lag zeitweise auf einem FREMDEN Koerper
      GELIEFERT           2 von 48 =  4,2 %
      NICHT geliefert     5 von 16 = 31,2 %
      Fisher exakt p = 0,0086

    nach der ERSTEN Anfahrt (das Kriterium aus dem Vorlaeuferbefund)
      erste Anfahrt >  80 mm   n =  2   Fremd-Anteil Median 71,6 %   2 von 2 betroffen, 0 geliefert
      erste Anfahrt <= 80 mm   n = 62   Fremd-Anteil Median  0,0 %   5 von 62 betroffen

    die beiden schweren Faelle im Einzelnen
      Ep 48  erste Anfahrt 136,1 mm | fremd 99,9 % AB SCHRITT 1 | wer: obj_green 897, obj_X 4
             Belief -> eigenes Objekt 124,4 mm, -> naechster Koerper 4,2 mm | daneben
      Ep 20  erste Anfahrt 129,7 mm | fremd 43,2 % ab Schritt 5  | wer: obj_X 432
             Belief -> eigenes Objekt  56,7 mm, -> naechster Koerper 4,1 mm | daneben

# Bewertung

* **Es ist eine Bindung, keine Ungenauigkeit.** 4,2 bzw. 4,1 mm zum falschen Koerper ist die
  normale Lokalisierungsguete - der Tracker arbeitet praezise, nur am falschen Objekt. Damit
  scheidet "die Wahrnehmung ist zu ungenau" als Erklaerung aus.
* **Sie beginnt frueh.** In Episode 48 ab dem **ersten** Anfahrschritt. Die Bindung entsteht also
  beim Aufsetzen des Trackers, nicht durch Verwechslung im Verlauf.
* **Sie loest sich nicht von selbst.** 99,9 % bzw. 43,2 % der Anfahrschritte bleiben fremd.
* **Der Zusammenhang mit dem Ausgang ist signifikant** (p = 0,0086) und ueberlebt die kleine
  Stichprobe. Er ersetzt die schwache Permutationskontrolle des
  [Vorlaeuferbefunds](/befunde/ablenker-anfahrt.md), die bei sechs Nachbarn und +-25 mm
  Toleranz eine Zufallstrefferquote von 75 % hatte und deshalb nur Richtung angeben konnte.

# Fallen und Vorbehalte

* **Der Lauf wurde bei 64 statt 150 Episoden abgebrochen**, weil der Arbeitsspeicher knapp wurde
  (0,7 GB frei) und der parallele GUI-Lauf des Nutzers Vorrang hatte. Der Haupttest ist trotzdem
  signifikant; die Untergruppe "erste Anfahrt > 80 mm" umfasst aber nur **zwei** Episoden und
  traegt fuer sich allein nichts.
* **Die Lieferquote lag in diesem Lauf bei 75 %** (48/64) statt der ueblichen ~52 %, und der
  Anteil schwerer Anfahrfehler entsprechend bei 3 % statt 6,8 %. Ursache ungeklaert - der
  Zustand ist neuer als der des Vorlaeuferbefunds. **Fuer den hier gemessenen Zusammenhang ist
  das unerheblich** (er vergleicht innerhalb desselben Laufs), fuer die Haeufigkeitsangabe nicht.
* **Was NICHT gemessen ist: warum** der Tracker einrastet. Zwei Kandidaten liegen nahe und sind
  unterscheidbar - die Blobverschmelzung zweier naher Koerper
  ([Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md)) und eine Fehlzuordnung der
  Form-/Farbklasse beim Aufsetzen des Trackers. Episode 48 spricht fuer das Zweite: die Bindung
  steht ab Schritt 1 fest, und `obj_green` gewinnt 897 von 901 Schritten.

# Naechster Schritt

Die Frage ist jetzt eng genug fuer eine gezielte Messung: **entsteht die Bindung beim Aufsetzen
des Trackers?** Dafuer genuegt, beim ersten Anfahrschritt Detektion und gewaehlten Schluessel
mitzuschreiben und gegen die Adressierung derselben Episode zu halten - die steht ohnehin schon
im Protokoll (`[dbg] ... via EIGENSCHAFTEN ... n Treffer`). Wenn Adressierung und Tracker-Start
auseinanderfallen, ist der Ort gefunden.

Erst danach lohnt eine Aenderung. Eine naheliegende waere, den Tracker an die **adressierte
Detektion** zu binden statt ihn frei aufsetzen zu lassen - das ist aber ein Eingriff in den
Wahrnehmungspfad und braucht die Ursache zuerst.

# Verwandt

* [Ablenker-Bindung in der Anfahrt](/befunde/ablenker-anfahrt.md) - der Vorlaeufer, hier bestaetigt
* [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) - die Adressierung, erneut entlastet
* [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md) - der eine der beiden Ursachenkandidaten
* [Fovea und Blicksteuerung](/mechanismen/fovea-und-blick.md)
