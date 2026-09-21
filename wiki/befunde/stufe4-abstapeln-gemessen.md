---
type: Befund
title: Stufe 4 gemessen - die Sprache traegt, das Abstapeln nicht. Und der Hoehenschaetzer scheitert an einer Verteilungsverschiebung
description: Das A/B zur Relation in der Adresse. Die Sprache funktioniert - "nimm das, was auf Y liegt" wird in 27 von 38 Versuchen aufgeloest, mit 6 mm Median-Fehler, und der Arm hebt den gestapelten Koerper in 23 von 23 Ablagen wirklich herunter. Geliefert wird trotzdem NICHTS, in beiden Armen 0 von 30 und 0 von 24. Zwei Ursachen sind beziffert: der Arm verliert den getragenen Koerper aus dem Glauben (28 bis 45 mm statt der sonst 5 bis 18) und legt 29 mm neben dem Ziel ab, und der Hoehenschaetzer liest die Auflage voellig falsch - wahr 6/10/14 mm, geschaetzt 11,1/6,0/9,2, die Reihenfolge ist zerstoert. Die Ursache dafuer ist eine Verteilungsverschiebung, die ich selbst erzeugt habe.
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

    A  gewoehnliche Adresse    0 von 30 geliefert    Endabstand Median 148 mm
    B  relationale Adresse     0 von 24 geliefert    Endabstand Median 118 mm

**Null.** Die Sprache traegt, die Aufgabe nicht.

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
* **Zwei Programmierfehler haben diesen Lauf zweimal gekostet**, beide im Messaufbau und nicht im
  Gegenstand: eine Hilfsfunktion, die ihre Schalter setzte statt sie auszugeben (alle Laeufe
  fuhren mit Vorgaben, erkannt nur an "0 Tastwerte"), und ein zweiter `perceive_fn`-Aufruf im
  Wiederfind-Pfad, dem die dritte Rueckgabe die Episode brach. Beide sind behoben.

# Verwandt

* [Der Stapel wird sichtbar](/befunde/stapel-wird-sichtbar.md) - die Voraussetzung, die vorher geloest wurde
* [Weniger Teacher](/befunde/tastetikett-gegen-privileg.md) - wo der Hoehenschaetzer 0,6 bis 2,2 mm erreicht
* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - Stufe 4
* [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) - der Sichtbarkeits-Pruefstand sagte 24 von 25, der Lauf sagt 0 geliefert
