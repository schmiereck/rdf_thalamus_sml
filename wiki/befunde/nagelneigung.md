---
type: Befund
title: Der Nagel traegt 95% der Griffkraft - und bewirkt auf act23-Ebene nichts
description: Auf dem isolierten Pruefstand hebt ein flacherer Nagel die Wuerfelquote um 12,5 Punkte. Im sauberen act23-A/B: -2,0 Punkte, p = 0,76. Der Musterfall der Pruefstandsfalle, samt uebersehenem Konfounder.
tags: [act23, greifer, geometrie, negativ]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-08-29T00:00:00Z }
verified: { by: human:thomas, at: 2026-08-29T18:33:00Z }
sources:
  - id: ab
    resource: /raw/index.md
    title: act23-A/B 2026-08-29, byteweise identischer Startzustand sha256 afc739f7, Seed 11, je 200 Ep
---

# Behauptung

**Auf act23-Ebene bewirkt die Nagelgeometrie nichts.** Die Mechanismus-Kette darunter ist
trotzdem gemessen richtig und wertvoll - sie beschreibt, was der Pruefstand tut, nicht, was der
Agent daraus macht.

# Die Ist-Geometrie, die vorher niemand kannte

`assets/bracket_arm.xml` hat `compiler angle="radian"` - `euler="0 1.0 0"` sind **57,3 Grad**,
nicht 1 Grad. Scharnier am Fingerfuss plus gerader Schaft: die Klaue ist ein nach unten offenes
**V**, dessen Halboeffnung exakt dem Gelenkwinkel `j5` entspricht.

    Kraftsumme  Nagel (claw_*) 675 + 673   |   Schaft (finger_*) 36 + 36
    erste Beruehrung: claw_left bei j5 = 0,296

**95 % der Griffkraft laufen ueber die beiden Naegel.** Der Griff wird von den Naegeln gemacht,
nicht von den Backenflaechen.

# Pruefstand: ein klares Plateau

`knick_probe.py`, act19-Aufbau mit fahrendem Teacher, 6 Seeds x 40 Ep je Arm, gepaart:

    Arm    Nagel     Lieferungen      Endabstand    gegen K0
    A      57,3   128/240 = 53,3%      39,1 mm      (Original)
    K0     57,3   123/240 = 51,2%      37,4 mm      Kontrolle
    N40    40,0   133/240 = 55,4%      34,0 mm       +4,2  p = 0,410
    N30    30,0   150/240 = 62,5%      30,4 mm      +11,3  p = 0,0165
    N20    20,0   153/240 = 63,8%      29,4 mm      +12,5  p = 0,0073  **
    N10    10,0   151/240 = 62,9%      30,3 mm      +11,7  p = 0,0127
    N00     0,0   141/240 = 58,8%      31,0 mm       +7,5  p = 0,119

Monoton in **beiden** Endpunkten ueber vier unabhaengige Arme, Vorzeichentest 6/6 Seeds. Das
Optimum ist ein **Plateau von 30 bis 10 Grad**, feiner ist nicht gedeckt.

**Mechanismus-Befund, der die Nutzerbeobachtung bestaetigt** ("Objekte werden beim Schliessen
nach vorne gedrueckt"): bei 14-mm-Objekten mit +/-6 mm Versatz schiebt der Greifer das Objekt im
Median **+18,4 mm** nach vorn aus der Klaue. Mit Nagel 20 Grad: **+0,4 mm**.

# act23: nichts

    ALT (Nagel 57,3)  102/200 = 51,0%   Median-Abstand 24 mm
    NEU (Nagel 20)     98/200 = 49,0%   Median-Abstand 25 mm
    -2,0 Punkte  [-11,7; +7,7]  Fisher p = 0,76   kein Trend ueber die 50er-Bloecke

    Mechanismus (VORAB benannt): tragen Median 1,75 -> 0,00 N, Klaue leer 48,0 -> 51,5%
    -> zeigt in die GEGENRICHTUNG

Auf den **echten Formen** (L/U/T) hatte der Pruefstand das schon vorweggenommen: gegen den
heutigen Greifer -0,4 / -4,2 / -1,7 Punkte, also nichts. Der +12,5-Punkte-Gewinn gilt
**ausschliesslich fuer Wuerfel** - und damit fuer die Objekte, die ohnehin die leichten waren.

# Fallen

* **Mein Zwischenbericht war falsch.** Aus einem GUI-Lauf hatte ich +10,3 Punkte als
  Greifer-Gewinn gemeldet, mit Griffdruck 0,00 -> 2,42 N als "unabhaengiger Bestaetigung". Der
  ALT-Arm zeigt: der **alte** Greifer erreicht auf demselben Zustand 51,0 % gegen 44,7 % im alten
  GUI-Lauf. Der Unterschied sass im Zustand bzw. Prozesskontext.
  > **Ein gespeicherter Zustand in einem frischen Prozess verhaelt sich anders als derselbe
  > Zustand mitten in einem laufenden Lauf.** Das ist der uebersehene Konfounder, und er ist fuer
  > jeden kuenftigen Vergleich dieser Art relevant.
* **Ein Test, der nicht fehlschlagen kann, ist kein Test.** Die erste
  Deckungsgleichheits-Pruefung tastete die falsche Achse ab (y statt z) und meldete 0,000000 mm,
  ohne je etwas verglichen zu haben. Immer eine Gegenprobe fahren, die anschlagen **muss**.
* **Die groesste Einschraenkung, spaet bemerkt:** `pc_act16.py:42` sagt
  `OBJS = ["obj_red","obj_green","obj_blue"]` - die gesamte Nagel- und Knick-Reihe lief
  ausschliesslich auf **24-mm-Wuerfeln**. Die L/U/T-Formen sind 14 mm breit und kamen nie vor.
* **Dasselbe Beweismass muss in beide Richtungen gelten.** Der "Trend ueber vier Arme", mit dem
  ich den Nagelbefund gestuetzt habe, zeigt beim laengeren Vorderglied monoton **gegen** die
  Idee (0/15/20/25 mm -> 63,8/61,7/60,0/57,1 %).

# Folgen

`ACT14_FINGER_KNICK`/`_NAGEL` bleiben als Werkzeug (alle Vorgabe AUS im Code;
`ACT14_FINGER_KNICK="0"` ist seit dem 30.08. gesetzt, allein zur Uebereinstimmung mit dem
gelernten Zustand - siehe [Vorgaben 2026-08-30](/entscheidungen/defaults-2026-08-30.md)).

> **Der isolierte Greif-Pruefstand sagt act23-Ergebnisse in KEINER Richtung vorher.** Er meldete
> +12,5 Punkte auf Wuerfeln - auf act23-Ebene null. Er meldete null auf den Formen - das war
> zufaellig richtig.

Ein Geometriewechsel **entwertet** ausserdem Teile des gelernten Zustands (Griffpunkt-Heuristik
und Weltmodell-Statistik wurden am 57,3-Grad-Nagel gelernt). Erst auf eigener Zustandsdatei
fahren.

# Verwandt

* [Die Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)
* [Greif-Lerndeckel](/befunde/greif-lerndeckel.md)
