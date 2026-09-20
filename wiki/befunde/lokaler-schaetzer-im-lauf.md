---
type: Befund
title: Der lokale Hoehenschaetzer haelt im Lauf - auf beiden Grundrissen, aber die Quote bleibt unentschieden
description: Die act23-Bestaetigung zum lokalen Schaetzer, in einer Welt mit zwei Auflagenformen (70 und 50 mm im Wechsel). Die Schaetzung selbst traegt - 0,60 mm auf der kleinen und 1,10 mm auf der grossen Platte, wo der alte globale Schaetzer auf der Grundrate gelegen haette. Die Stapelquote ist 16 von 17 mit dem Privileg gegen 14 von 18 mit der Schaetzung (94 gegen 78 Prozent, p = 0,338) - nominell schlechter, aber diese Messung koennte erst einen Einbruch auf 61 Prozent von "kein Unterschied" trennen. Der Satz, der traegt, betrifft die Schaetzung, nicht die Quote.
tags: [act23, stapeln, hoehe, privileg, wahrnehmung]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-20T00:00:00Z }
sources:
  - id: ab
    resource: "Drei kopflose Laeufe nacheinander auf Kopien von act23_state.pkl (ad9d768c), Seed 7001, Teacher fahrend: warm 60 Episoden (51 Zieladressen, 9 Lernbeispiele verworfen -> 42 Zeilen), dann A und B je 40 aus DEMSELBEN warmen Zustand. Wie das erste Stufe-3-A/B, zusaetzlich ACT23_SOCKEL2=1; Unterschied allein ACT23_HOEHE_SEHEN=0 gegen =1"
    title: Das Zwei-Grundriss-A/B
  - id: bruch
    resource: /befunde/zweiter-grundriss-bricht-die-hoehe.md
    title: Warum der Schaetzer umgebaut werden musste
---

# Was geprueft wird

Der globale lineare Schaetzer faellt in einer Welt mit zwei Auflagenformen auf die Grundrate
([gemessen](/befunde/zweiter-grundriss-bricht-die-hoehe.md)). Der Umbau auf ein **lokales** Modell
heilt das auf dem Pruefstand (0,73 mm / 92 %). Nach
[Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) sagt das ueber act23 nichts - also dieser Lauf.

Die Welt hat jetzt beide Platten (`ACT23_SOCKEL2=1`), je Szene eine im Wechsel.

# Die Schaetzung traegt, und das ist der Befund

                          Stapel        |Schaetzfehler|
    A Privileg  50 mm    7/7  = 100 %      0,60 mm
    A Privileg  70 mm    9/10 =  90 %      0,70 mm
    A Privileg  gesamt  16/17 =  94 %      0,60 mm

    B gesehen   50 mm    6/9  =  67 %      0,60 mm
    B gesehen   70 mm    8/9  =  89 %      1,10 mm
    B gesehen   gesamt  14/18 =  78 %      0,80 mm

**0,60 und 1,10 mm auf den beiden Grundrissen** - dort, wo der alte globale Schaetzer bei der
Grundrate gelegen haette (auf dem Pruefstand 3,38 mm, also praktisch geraten). Die Zeile faellt in
beiden Armen, der Schaetzer rechnet also auch in A mit; beide Arme messen dieselbe Groesse und
kommen auf dieselbe Groessenordnung.

**Das war die Frage dieses Laufs, und sie ist mit Ja beantwortet.**

## Er ist im Lauf besser, als die Pruefstands-Duennbesetzung erwarten liess

Der Schaetzer hatte nach dem warmen Lauf 42 Zeilen. Die Sparsamkeitsleiter der Sonde sagt fuer
diese Menge rund 50-60 % richtige Stufe voraus; gemessen sind 0,8 mm Fehler, also deutlich besser.

Der Grund ist der Zuschnitt, nicht das Glueck: die Sonde hat ein **gleichmaessiges Raster**
ausgeduennt, ein Lauf besucht dagegen wenige Stellen **mehrfach** (die Szene wechselt nur alle zwei
Episoden). Die Nachbarschaft ist dort, wo gefragt wird, dichter besetzt als bei einer
gleichverteilten Stichprobe derselben Groesse. **Fuer einen lokalen Schaetzer ist ein Lauf die
guenstigere Welt** - was fuer den globalen keinen Unterschied gemacht haette.

# Die Quote bleibt unentschieden

    A 16/17 = 94 %   gegen   B 14/18 = 78 %      p = 0,338
    signifikant erst ab B <= 11/18 = 61 %

**16 Punkte nominell schlechter, und die Messung kann das nicht von null unterscheiden.** Das ist
ehrlich gesagt der unbefriedigende Teil: anders als beim
[ersten Stufe-3-A/B](/befunde/oberkante-ohne-privileg.md) (85 gegen 83 %) liegt hier eine Luecke,
die gross genug waere, um zu stoeren, und zu klein, um sie zu zeigen.

Was sich dazu sagen laesst, ohne zu ueberziehen:

* Die Luecke sitzt auf der **kleinen** Platte (7/7 gegen 6/9), und **dort ist die Schaetzung
  gleich gut wie im Privileg-Arm** (0,60 gegen 0,60 mm). Die drei Fehlschlaege haben also keinen
  sichtbaren Hoehenfehler hinter sich.
* Die kleine Platte ist mechanisch die schwerere: geometrische Toleranz 13 mm gegen 23 mm, bei
  einer gemessenen Ablagegenauigkeit von 20-25 mm. Dass sie mehr Fehlschlaege traegt, ist zu
  erwarten - in A ist sie mit 7/7 nur nicht dazu gekommen, es zu zeigen.
* Beides bleibt eine Erklaerung, keine Messung. **n = 7 und n = 9 tragen sie nicht.**

# Fallen

* **`p = 0,338` heisst nicht "gleich", und diesmal ist das mehr als eine Formalie.** Alles zwischen
  61 und 94 % ist mit dieser Fallzahl nicht von "kein Unterschied" zu trennen. Wer wissen will, ob
  die 16 Punkte echt sind, braucht einen Lauf mit der drei- bis vierfachen Zahl an Stapel-Urteilen.
* **Nur 17 bzw. 18 Urteile aus 33 Zieladressen.** Der Rest erreicht das Loslassen nicht; die
  Auszaehlung haengt damit an einem Zwischenschritt, den dieser Befund nicht kontrolliert.
* **Die XML hat einen Koerper mehr als beim ersten Stufe-3-A/B.** Nach
  [Invarianten](/mechanismen/invarianten.md) ist die Renderung dadurch nicht mehr zeichengenau
  dieselbe; die 94 % hier und die 85 % dort sind **nicht** direkt vergleichbar. Innerhalb dieses
  Laufs ist der Vergleich sauber, beide Arme teilen die XML.
* **Zwei Grundrisse, nicht drei.** Ob der lokale Schaetzer eine DRITTE Auflagenform aufnimmt, ohne
  fuer sie von vorn sammeln zu muessen, ist die naechste Frage und ungemessen.
* **Das Geruest steht weiter.** Gelabelt wird mit dem Privileg; nur zur Laufzeit ist es aus dem
  Pfad. Unveraendert gegenueber dem [ersten A/B](/befunde/oberkante-ohne-privileg.md).

# Verwandt

* [Die zweite Auflage bricht den Hoehenschaetzer](/befunde/zweiter-grundriss-bricht-die-hoehe.md) - der Bruch und der Umbau
* [Die Oberkante ohne Privileg](/befunde/oberkante-ohne-privileg.md) - das erste Stufe-3-A/B, eine Auflagenform
* [Die Hoehe steckt in der Wahrnehmung](/befunde/hoehe-steckt-in-der-wahrnehmung.md) - die Vorfrage
* [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) - warum dieser Lauf noetig war
* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - Stufe 3
