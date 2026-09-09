---
type: Befund
title: Kontinuitaet statt Neuklassifikation - richtig gebaut, kleines Loch
description: Der Tracker folgt bei ausgefallener Formklasse dem naechsten Farb-Teil statt blind zu werden. Er greift in 22 bis 28 Prozent der Episoden, fuellt aber nur 1,3 bis 2,2 Prozent der Anfahrschritte - und kein einziger Lauf war je ganz blind. Die Gegenprobe ist sauber (fremder Belief unveraendert, p = 1,0), die Lieferquote nicht aufgeloest.
tags: [act23, wahrnehmung, tracker, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-10T02:00:00Z }
sources:
  - id: sweep
    resource: "Gepaarter Seed-Sweep: 4 kopflose Steuerungslaeufe je 120 Episoden (Seed 7 und 23, ACT23_TRACK_KONTINUITAET 0/1), Schnappschuss 98a293f2, gleichzeitig gefahren"
    title: Kontinuitaets-A/B
  - id: diagnose
    resource: /befunde/formsplit-warum.md
    title: Die Diagnose, aus der der Weg gewaehlt wurde
---

# Was gebaut wurde

Der Form-Tracker verlangte in **jedem Bild** erneut `d["shape"] == key`. Faellt die Formklasse
bei verschmolzenem Blob aus - was sie laut [Diagnose](/befunde/formsplit-warum.md) tut, weil der
Splitteil nur 31-58 % der Pixel behaelt - fand er null Kandidaten. Jetzt folgt er stattdessen dem
naechstgelegenen **Farb**-Teil, ohne Formforderung.

Zwei Wachen, ohne die das die [Ablenker-Bindung](/befunde/ablenker-bindung-gemessen.md)
zurueckgeholt haette:

* **Nur wenn schon ein Glaube besteht** (`mem["xy"] is not None`). Beim ERSTEN Blick wird nicht
  geraten - dort entscheidet der Keim; sonst waere es genau der Muenzwurf aus
  [Der Keim erreicht den Tracker nie](/befunde/keim-erreicht-tracker-nicht.md), nur an anderer
  Stelle wieder eingebaut.
* **Die Zuversicht kommt aus der FARBE**, nicht aus einer erfundenen Klassenwahrscheinlichkeit -
  wir wissen *wo*, nicht *was*, und es wird auch nur das behauptet. Faellt sie unter
  `act16.SERVO_CONF` (0,5), ignoriert der Servo die Beobachtung von selbst. Dazu bleibt die
  5-cm-Sprungschranke.

# Zahlen

    Arm        Ep | Ep mit Kont  Kont-Frames | fremder Belief  Fehlstart | Quote
    k7_aus    120 |    0 =  0,0 %          0 |   11 =  9,2 %   2 = 1,7 % | 55,8 %
    k7_an     120 |   26 = 21,7 %        781 |   13 = 10,8 %   4 = 3,3 % | 52,5 %
    k23_aus   120 |    0 =  0,0 %          0 |   10 =  8,3 %   5 = 4,2 % | 50,0 %
    k23_an    120 |   33 = 27,5 %       1694 |    9 =  7,5 %   7 = 5,8 % | 61,7 %

    DIREKTE ZIELGROESSE (normiert, weil die Arme verschieden lange Episoden fahren)
      Detektor-Obs je Anfahrschritt, Median
        Seed  7   aus 0,312   an 0,325   (+0,013)   Kontinuitaets-Anteil 1,3 %
        Seed 23   aus 0,319   an 0,322   (+0,003)   Kontinuitaets-Anteil 2,2 %
      Episoden, in denen der Servo GANZ blind blieb:  0/120 in ALLEN VIER Armen

    GEGENPROBE fremder Belief
      Seed 7   9,2 -> 10,8 %   p = 0,83
      Seed 23  8,3 ->  7,5 %   p = 1,00
      gepoolt  8,8 ->  9,2 %   p = 1,0000

    Lieferquote (Nebengroesse)
      Seed  7  55,8 -> 52,5 %   p = 0,698
      Seed 23  50,0 -> 61,7 %   p = 0,091
      gepoolt  52,9 -> 57,1 %   p = 0,409   -- die Seeds widersprechen einander

# Bewertung

* **Die Sicherheitsfrage ist sauber beantwortet.** Der fremde Belief bewegt sich nicht
  (p = 1,0000), in beiden Seeds. Das benannte Risiko - die Ablenker-Bindung ueber einen
  klassenfreien Pfad zurueckzuholen - ist gemessen nicht eingetreten. Die beiden Wachen tragen.
* **Das Loch ist kleiner als die Begruendung nahelegte.** Ich hatte vom "blinden Servo"
  gesprochen; tatsaechlich lief **kein einziger** Lauf je ganz blind, und der Servo hatte auch
  ohne die Aenderung in 31-32 % der Anfahrschritte eine Beobachtung. Die Kontinuitaet fuellt
  1,3-2,2 % der Schritte. Das ist ein realer, aber kleiner Gewinn.
* **Die Lieferquote ist nicht aufgeloest** und die Seeds zeigen in **verschiedene** Richtungen
  (-3,3 und +11,7 Punkte). Wer daraus einen Gewinn liest, liest Rauschen. Bei 1-2 % betroffener
  Schritte war das die Erwartung.
* **Die Fehlstart-Spalte gehoert nicht hierher.** Sie steigt (1,7 -> 3,3 % und 4,2 -> 5,8 %),
  aber die Kontinuitaet kann den ERSTEN Trackerstart per Konstruktion nicht beeinflussen - sie
  verlangt einen bestehenden Glauben. Das ist Trajektorien-Divergenz: die Arme sehen ab dem
  ersten Eingriff andere Szenen ([Zwei Laeufe sind dieselbe
  Rechnung](/befunde/laeufe-sind-reproduzierbar.md)).

# Die Vorhersage, die vorab stand

*"Die Kontinuitaet wird selten greifen... Wenn am Ende die Frames im einstelligen Prozentbereich
liegen und die Ablenker-Zahlen unveraendert sind, ist das ein sauberer, aber kleiner Gewinn - und
ich werde ihn dann auch so nennen."* Beides ist eingetreten: 1,3-2,2 % der Schritte, Ablenker
unveraendert. Der Befund wird entsprechend als **klein** gefuehrt, nicht als Erfolg.

Eine Haelfte der Vorhersage war trotzdem falsch: sie greift in **22-28 % der EPISODEN**, nicht
selten. Viele Episoden haben also einzelne Bilder ohne Formtreffer - nur eben wenige je Episode.

# Folgen

**Der Nutzer hat die Vorgabe am 2026-09-10 auf `1` gestellt.** Anders als beim
[Rueckfall-Keim](/befunde/keim-im-rueckfall.md), der ebenfalls klein war, gibt es hier **keinen
grundsaetzlichen Preis**: der Pfad ist rein wahrnehmungsbasiert (Farb-Split, Sprungschranke,
farbbasierte Zuversicht), er fuegt kein Privileg hinzu und widerspricht dem
[Projektziel](/ziel.md) nicht - er verlagert Identitaet von "jedes Bild neu erkennen" auf "einmal
feststellen und dann verfolgen", was architektonisch die sauberere Antwort ist.

**Dafuer:** mehr Information fuer den Servo, kein gemessener Schaden, prinzipientreu.
**Dagegen:** ein Codepfad mehr fuer 1-2 % der Schritte, ohne belegten Ertrag.

Das war eine Abwaegung, keine Rechnung - der Nutzer hat sie zugunsten der Umstellung
entschieden. **Ausdruecklich nicht mitgekauft:** ein Quotengewinn (gepoolt 52,9 -> 57,1 %,
p = 0,41, Seeds gegenlaeufig). Rueckfall in einer Zeile: `ACT23_TRACK_KONTINUITAET=0`.

# Verwandt

* [Warum der Split die Formklasse verliert](/befunde/formsplit-warum.md) - die Diagnose davor
* [Nachbarnaehe im Lauf](/befunde/nachbarnaehe-im-lauf.md) - warum die Linie ueberhaupt verfolgt wurde
* [Der Keim erreicht den Tracker nie](/befunde/keim-erreicht-tracker-nicht.md) - die erste Wache stammt daher
