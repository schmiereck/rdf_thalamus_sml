---
type: Befund
title: Die Direkt-Adresse verkuerzt die Aneignung eines neuen Koerpers auf 8 bis 22 Episoden - aber eine Adresse, die nur "Wuerfel" sagt, trifft den Koerper nicht
description: Nutzerauftrag - klaeren, ob die Adresse ohne Klasse (ACT23_EIG_DIREKT=1 EIG_STETIG=1) die Zeit bis zum ersten Kommando verkuerzt. Gepaart mit den vier Kettenlaeufen (Stern/V x Seed 11/23, gleicher Code, gleicher Zustand). Die Adresse entsteht in allen vier Laeufen in Episode 7, das erste Kommando folgt in Episode 8, 22, 8 und 20 - gegen nie, 43, 80 und 76 ueber Klasse und Knopf. Vier von vier Paaren in dieselbe Richtung (Vorzeichentest p = 0,125, mehr ist bei vier Paaren nicht moeglich), dazu 59 statt 16 Kommandos auf den neuen Koerper. Die Lieferquote darauf ist gleich (27 gegen 31 Prozent). Der Haken - wo die Wahrnehmung den Koerper als bekannte Klasse liest, heisst die Adresse "cube"; sie passt dann auch auf die echten Wuerfel, der Arm fasst nur in 2 von 15 Kommandos am V zu und liefert es nie.
tags: [act23, selbstlernen, kommando, lernen, nutzeridee, ab]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-09-26T00:00:00Z }
sources:
  - id: lauf
    resource: "Code 706c7f8. Kopien von act23_state.pkl (ad9d768c, danach unveraendert), ACT23_NOVEL_BODY=obj_Stern bzw. obj_V, Seeds 11 und 23, je 100 Ep; Arm Kette = Vorgaben (Laeufe vom 2026-09-25), Arm Direkt = zusaetzlich ACT23_EIG_DIREKT=1 ACT23_EIG_STETIG=1; zwei Prozesse je Block"
    title: Vier Paare Kette gegen Direkt
  - id: kette
    resource: /befunde/lerngeschwindigkeit-neuer-koerper.md
    title: Die Kettenlaeufe und der Engpass Geburt->Knopf
  - id: frueher
    resource: /befunde/adresse-ohne-klasse-gemessen.md
    title: Dieselbe Frage am 2026-09-16 im frischen Zustand (7 gegen 22 Episoden)
---

# Die Frage

Die [Kettenlaeufe](/befunde/lerngeschwindigkeit-neuer-koerper.md) zeigten: der Agent bildet die
Klasse eines neuen Koerpers frueh, kommandierbar wird er aber erst 30-56 Episoden spaeter, wenn
der Knopf vergeben ist. Die Adresse ohne Klasse (`ACT23_EIG_DIREKT`) braucht statt Geburt und
Bestaetigung nur EINE Sichtung. Am [16.09.](/befunde/adresse-ohne-klasse-gemessen.md) verkuerzte sie
das im **frischen** Zustand von 22 auf 7 Episoden. Gilt das auch im trainierten Zustand, fuer
Koerper, die die Wahrnehmung nur teilweise als neu liest?

**Vorher festgehalten** (Board): deutlich frueher; offen, ob Stern und V eine EINDEUTIGE
Formadresse bekommen.

# Ergebnis

    Koerper Seed   Kette: erstes Kommando   Direkt: Adresse   erstes Kommando   Kommandos   geliefert   Adresse
    Stern    11          nie                      Ep 7             Ep  8            17          6        '~gesehen' (Formvektor)
    Stern    23          Ep 43                    Ep 7             Ep 22            11          3        'neu-13 + dick'
    V        11          Ep 80                    Ep 7             Ep  8            15          0        'cube'
    V        23          Ep 76                    Ep 7             Ep 20            16          7        'cube + dick'

    zusammen            16 Kommandos, 5 geliefert (31 %)     59 Kommandos, 16 geliefert (27 %)
    Vorzeichentest: 4 von 4 Paaren frueher -> p = 0,125 (das Minimum bei vier Paaren)

    Lage des kommandierten Koerpers in der Klaue beim Zufassen ([InKlaue], privilegiert, nur Messung):
      Kette      in 15 von 16 Kommandos gemessen, Median 11-17 mm, nie ueber 30 mm
      Direkt     Stern 15/17, 11/11, V/23 10/16 gemessen, Median 11-17 mm
                 V/11 nur in 2 von 15 Kommandos -- der Arm fasste fast nie am V zu

# Was das heisst

1. **Die Zeit bis zum ersten Kommando schrumpft auf 8-22 Episoden**, in allen vier Paaren, im
   Mittel um mehr als 50 Episoden. Das bestaetigt die Messung vom 16.09. jetzt im trainierten
   Zustand und mit zwei weiteren Koerpern. Der neue Koerper wird dadurch auch fast viermal so oft
   kommandiert (59 gegen 16).
2. **Gekommen ist die Verkuerzung vor allem aus dem Warten.** Die Adresse steht in allen vier Laeufen
   in Episode 7 - beim ersten Blick nach dem ersten Hinstellen. Bis zum ersten Kommando vergehen
   dann 1 bis 15 Episoden, bis die Neugier den Koerper waehlt.
3. **Die Lieferquote auf dem neuen Koerper bleibt gleich** (27 gegen 31 %). Die Direkt-Adresse macht
   ihn frueher ansprechbar, nicht leichter greifbar.
4. **Eine Adresse, die nur eine BEKANNTE Klasse nennt, ist keine Adresse des neuen Koerpers.** Beim
   V liest die Wahrnehmung in vielen Lagen "Wuerfel" (s. die [Neuheits-Sonde](/befunde/lerngeschwindigkeit-neuer-koerper.md)).
   Mit Seed 11 hiess die Adresse deshalb `'cube'` - sie passt auf jeden Wuerfel der Szene. Der Arm
   fasste nur in 2 von 15 Kommandos am V zu und lieferte es nie. Mit Seed 23 hiess sie
   `'cube + dick'`; das Groessenband trennte das V von den echten Wuerfeln, und es klappte (7 von 16).
   Das ist die bekannte Grenze **"Eindeutigkeit ist nicht Richtigkeit"**: die Adresse wird beim
   Wuerfeln auf Eindeutigkeit in DIESER Szene geprueft, spaeter stehen andere Koerper da.

# Fallen

* **Vier Paare, 100 Episoden.** Die Richtung ist in allen vier gleich und gross; ein Nachweis im
  statistischen Sinn ist mit vier Paaren nicht moeglich.
* **Kette und Direkt sind nicht je Episode gepaart**, sondern je Lauf (gleicher Seed, gleicher
  Zustand); sobald ein Arm anders entscheidet, laufen die Szenen auseinander.
* **"Erstes Kommando" zaehlt das Kommando, nicht den Treffer.** Bei V/11 wurde der Koerper frueh
  kommandiert und nie getroffen - die Zahl 8 steht dort fuer eine falsche Adresse.
* **Die Hausquote sinkt im Direkt-Arm** (37-46 gegen 44-54 %), weil der schwerere neue Koerper
  oefter drankommt - kein Schaden an den alten Koerpern belegt, nicht getrennt ausgewertet.
* **Die Aufloesung selbst ist nicht protokolliert** (nur mit `ACT23_DEBUG=1`); `[InKlaue]` ist ein
  Ersatzmass.

# Was daraus folgt

Die Direkt-Adresse leistet, wofuer sie gebaut ist: sie beseitigt die Wartezeit der Vergabe. Vor
einer Vorgabe-Aenderung (heute 0) waere die Luecke aus Punkt 4 zu schliessen: eine Direkt-Adresse,
die nur eine bekannte Klasse ohne weitere Achse nennt, sollte nicht vergeben werden - oder beim
Aufloesen auf den Formvektor zurueckgreifen, der den neuen Koerper tatsaechlich beschreibt.

# Verwandt

* [Lerngeschwindigkeit mit neuem Koerper](/befunde/lerngeschwindigkeit-neuer-koerper.md) - die Kettenlaeufe
* [Aus einer Sichtung kommandierbar](/befunde/adresse-ohne-klasse-gemessen.md) - dieselbe Frage im frischen Zustand
* [Eine dauerhafte Adresse darf keine Farbe nennen](/befunde/dauer-adresse-vertraegt-keine-farbe.md)
* [Adresse ohne Klasse](/mechanismen/adresse-ohne-klasse.md) - der Mechanismus
