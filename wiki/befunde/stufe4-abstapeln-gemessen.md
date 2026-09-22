---
type: Befund
title: Stufe 4 gemessen - die relationale Adresse verdoppelt das Abstapeln (BERICHTIGT: die erste Fassung stand auf einem Zaehlfehler)
description: Das A/B zur Relation in der Adresse. BERICHTIGT 2026-09-22 - die erste Fassung meldete 0 von 30 gegen 0 von 24 und schloss daraus, die Aufgabe sei nicht geloest. Das war ein Zaehlfehler von mir: die Erfolgszeile heisst GELIEFERT in Grossbuchstaben, mein fallunterscheidendes grep traf nur das kleingeschriebene 'NICHT geliefert' und zaehlte damit JEDEN Erfolg als Misserfolg. Richtig gezaehlt: 5 von 35 ohne die Relation gegen 11 von 34 mit ihr, also 14 gegen 32 Prozent bei p = 0,093. Die relationale Adresse verdoppelt das Abstapeln. Die Sprachzahlen und die Hoehenschaetzer-Diagnose der ersten Fassung bleiben gueltig; die Schlussfolgerung war falsch.
tags: [act23, stapeln, sprache, negativ, hoehe, wahrnehmung]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-21T00:00:00Z }
sources:
  - id: ab
    resource: "Drei kopflose Laeufe auf Kopien von act23_state.pkl (ad9d768c), Seed 7001, ACT23_CHOREO=fsm, ACT23_SOCKEL_N=1, Chroma-Schnitt und Konzentrisch-Ausnahme in BEIDEN Armen: warm 40 Ep gewoehnliche Stapelaufgabe mit Tasten (20 Tastwerte), dann nur der Schaetzer verpflanzt, dann A und B je 35 Ep Abstapeln; Unterschied allein ACT23_ADR_RELATION=0 gegen =1"
    title: Das Stufe-4-A/B
  - id: sicht
    resource: /befunde/stapel-wird-sichtbar.md
    title: Die Voraussetzung, die vorher geloest wurde
---

# BERICHTIGUNG 2026-09-22: diese Seite stand auf einem Zaehlfehler

Die erste Fassung meldete **0 von 30 gegen 0 von 24 geliefert** und schloss daraus: *"die Sprache
traegt, die Aufgabe nicht"*. **Beides war falsch gezaehlt.**

Die Erfolgszeile des Laufs heisst `[Auto 7] GELIEFERT` - in **Grossbuchstaben**. Mein
fallunterscheidendes `grep` suchte nach `geliefert` und traf damit ausschliesslich die
kleingeschriebene Variante in `NICHT geliefert`. **Jeder Erfolg wurde als Misserfolg gezaehlt**,
und weil das jeden Arm gleich traf, sah es wie ein durchgaengiges Null aus statt wie ein Fehler.

Richtig gezaehlt, und zwar ueber beide unabhaengigen Zeilen, die im Protokoll stehen
(`[Auto N] GELIEFERT` und `Welt: geliefert` - sie stimmen Episode fuer Episode ueberein):

    A  gewoehnliche Adresse     5 von 35 = 14 %
    B  relationale Adresse     11 von 34 = 32 %      Fisher p = 0,093

**Die relationale Adresse verdoppelt das Abstapeln.** Zur Einordnung die gewoehnliche
Transportaufgabe auf demselben Zustand, am selben Tag gemessen: 40 bis 66 % je nach
Choreographie - das Abstapeln ist also die deutlich schwerere Aufgabe, und 32 % sind dafuer kein
schlechter Wert.

`p = 0,093` ist nicht signifikant. Die Richtung ist stark, die Fallzahl klein; es ist ein Hinweis,
kein Beleg.

## Was von der ersten Fassung bleibt

* **Alle Sprachzahlen** - Adresse aufgeloest 27 von 38 mit 6 mm Median, getragen 23 von 23. Die
  wurden aus anderen Zeilen gezaehlt und sind vom Fehler nicht beruehrt.
* **Die Hoehenschaetzer-Diagnose** (wahr 6/10/14 mm, geschaetzt 11,1/6,0/9,2) und ihre Ursache,
  die Verteilungsverschiebung - eigenstaendig gemessen und inzwischen
  [beziffert und behoben](/befunde/schaetzer-auf-der-belegten-auflage.md).
* **Der Glaubensfehler** (28-45 mm statt 5-18) als MESSWERT.

## Was faellt

* Die Schlussfolgerung *"die Aufgabe ist nicht geloest"*.
* Die Zuschreibung, der Glaubensfehler und der Schaetzer seien die **Ursache** eines
  Totalausfalls - es gab keinen Totalausfall. Beide bleiben Maengel, aber sie erklaeren jetzt den
  Abstand zwischen 32 und 100 %, nicht den zwischen 0 und irgendetwas.
* Der Satz, keine der Ursachen liege in der Sprache, war richtig - nur nicht aus dem genannten
  Grund.

# Was funktioniert

**Die Sprache.** `ADRESSE := ... | RELATION ADRESSE` loest auf:

    Adresse aufgeloest        27 von 38 Versuchen
      Fehler                  Median 6 mm, 90 %-Wert 12 mm
    kein Stapel gefunden       5
    mehrdeutig                 6

**Der Griff.** In **23 von 23** Ablagen hing der Koerper wirklich an der Klaue (15 mm ueber seiner
Ruhelage beim Oeffnen). Der Arm holt den gestapelten Koerper also herunter - genau das, was vor
Stufe 4 unmoeglich war.

Im Vergleichsarm ohne die Relation: 17 Ablagen und 6-mal "nie getragen".

# Was nicht funktioniert

    FALSCH GEZAEHLT (erste Fassung):
    A  gewoehnliche Adresse    0 von 30 geliefert
    B  relationale Adresse     0 von 24 geliefert

    RICHTIG (s. Berichtigung oben):
    A  gewoehnliche Adresse    5 von 35 = 14 %
    B  relationale Adresse    11 von 34 = 32 %      p = 0,093

Der Endabstand-Median (148 und 118 mm) ist ebenfalls irrefuehrend: er mittelt ueber gelungene und
misslungene Episoden, und die misslungenen dominieren.

## Ursache 1: der Arm verliert den Koerper aus dem Glauben

    beim Oeffnen   seitlich vom Ziel   Median 29 mm
    Glaube (wo der Agent das Objekt vermutet)   28 bis 45 mm daneben

Zum Vergleich: in den gewoehnlichen Stapellaeufen liegt der Glaube bei 5 bis 18 mm. Der Arm
greift richtig, traegt richtig - und legt dann 29 mm neben dem Ziel ab, weil er waehrend des
Tragens nicht mehr weiss, was er traegt. Bei einer Liefertoleranz in dieser Groessenordnung
faellt damit jede Episode durch.

## Ursache 2: der Hoehenschaetzer liest die Auflage falsch, und ich habe es verursacht

    wahre Oberkante    6 mm  ->  geschaetzt  11,1 mm   (n=8)
                      10 mm  ->  geschaetzt   6,0 mm   (n=4)
                      14 mm  ->  geschaetzt   9,2 mm   (n=13)

**Die Reihenfolge ist zerstoert** - das ist schlechter als raten. Der Schaetzer lag in seinen
eigenen Messungen bei 0,6 bis 2,2 mm
([dort](/befunde/tastetikett-gegen-privileg.md)); hier liegt er 4 bis 5 mm daneben und monoton
falsch herum.

> **Die Ursache ist eine Verteilungsverschiebung, die dieser Aufbau selbst erzeugt.** Gelernt hat
> er auf Detektionen der **leeren** Auflage - ein Blob von rund 1400 px. Gefragt wird er beim
> Abstapeln nach der **belegten** Auflage, und die zerfaellt durch den Konzentrisch-Schnitt in
> zwei Teile: die Auflage ist dann nur noch der groessere Rest (gemessen 738 bis 1543 px), der
> Wuerfel ist abgezogen. Er bekommt also ein Merkmal, das er so nie gesehen hat - und seine
> staerkste Achse ist ausgerechnet die Flaeche.

Das ist bitter und lehrreich zugleich: **der Schnitt, der Stufe 4 erst moeglich macht, zerstoert
die Eingabe des Hoehenschaetzers.** Zwei Bausteine, jeder fuer sich gemessen gut, die sich
gegenseitig untergraben.

# Was daraus folgt

* **Die Sprachaussage steht.** Die Relation in der Adresse loest auf und fuehrt zu einem
  gegriffenen, getragenen Koerper. Das ist der Teil, der Stufe 4 ausmacht, und er ist belegt.
* **Die Aufgabe ist nicht geloest.** Abstapeln liefert nicht, und keine der beiden Ursachen liegt
  in der Sprache.
* **Der Schaetzer muss auf dem sehen, was er im Einsatz bekommt.** Entweder lernt er auf der
  belegten Auflage (das Tasten liefert das Etikett ohnehin genau dann), oder er bekommt ein
  Merkmal, das der Schnitt nicht veraendert. Das ist die naechste Messung, nicht diese.

# Fallen

* **Der Vergleich A gegen B ist als QUOTE wertlos** - beide sind 0. Was ihn traegt, sind die
  Zwischenschritte: Adresse aufgeloest (27 gegen 0) und getragen (23 von 23 gegen 17 mit 6-mal
  "nie getragen").
* **Nicht alle 35 Episoden zaehlen mit.** A hat 30 Auto-Zeilen, B 24 - der Rest bricht vorher ab.
  Warum, ist nicht untersucht.
* **Der Glaubensfehler ist nicht zerlegt.** 28 bis 45 mm koennten vom Chroma-Schnitt kommen (der
  Tracker sieht jetzt mehr Bloebe), von der falschen Greifhoehe, oder vom Tragen eines Koerpers,
  der zu Beginn hoch stand. Drei Kandidaten, keine Messung.
* **Eine Auflagenform, ein Seed, ein Lauf je Arm.**
* **DREI Fehler im Messaufbau, keiner im Gegenstand.** Der schwerste ist der Zaehlfehler oben --
  er hat aus einem positiven Ergebnis ein negatives gemacht und mich danach einen halben Tag
  Ursachensuche fuer einen Ausfall gekostet, den es nicht gab. Die anderen zwei: eine Hilfsfunktion, die ihre Schalter setzte statt sie auszugeben (alle Laeufe
  fuhren mit Vorgaben, erkannt nur an "0 Tastwerte"), und ein zweiter `perceive_fn`-Aufruf im
  Wiederfind-Pfad, dem die dritte Rueckgabe die Episode brach. Beide sind behoben.

# Verwandt

* [Der Stapel wird sichtbar](/befunde/stapel-wird-sichtbar.md) - die Voraussetzung, die vorher geloest wurde
* [Weniger Teacher](/befunde/tastetikett-gegen-privileg.md) - wo der Hoehenschaetzer 0,6 bis 2,2 mm erreicht
* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - Stufe 4
* [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) - der Sichtbarkeits-Pruefstand sagte 24 von 25, der Lauf sagt 0 geliefert
