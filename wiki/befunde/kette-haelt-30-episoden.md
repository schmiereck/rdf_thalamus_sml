---
type: Befund
title: Die Aneignungskette traegt 29 Episoden lang - danach ist die Welt leer, und 371 Episoden lang passiert nichts mehr
description: 400 frische Episoden mit Erzeuger und freier Vergabe. Alle drei Knoepfe fallen bis Episode 29, dann meldet der Erzeuger "noch offen: keiner" und es kommt keiner mehr dazu. Fuenf spaeter geborene Klassen verhungern samt und sonders nach rund 25 Episoden. Eine der drei gebundenen Klassen stirbt nach 145 Episoden - der Koerper bleibt adressierbar, der selbst gegebene Name ist weg. Der Engpass ist damit nicht mehr die Maschinerie, sondern die Welt: sieben Koerper, in 29 Episoden vergeben.
tags: [act23, selbstlernen, formklassen, langlauf]
status: stable
evidenz: gemessen
ebene: langlauf
generated: { by: claude/opus-5, at: 2026-09-16T00:00:00Z }
sources:
  - id: lauf
    resource: "Ein frischer Lauf (ACT23_FRESH=1) ueber 400 Episoden mit ACT23_FREIE_VERGABE=1 ACT23_NOVEL_WEITER=1, auf einer Scratch-Datei"
    title: Langlauf der Aneignungskette
  - id: vorher
    resource: /befunde/erzeuger-repariert.md
    title: Der Kurzlauf, dessen Haltbarkeit hier geprueft wird
---

# Die Frage

[Der Kurzlauf](/befunde/erzeuger-repariert.md) zeigte 3 Knoepfe statt 1 und `obj_X` erstmals selbst
angeeignet - in 140 Episoden. Offen blieb: **halten die Knoepfe, und ueberleben die Klassen?**

# Alles Wesentliche passiert bis Episode 29

    Ep  21   'neu-1' -> 'Neue Form 2' auf obj_T
    Ep  23   Probe-Rolle weitergereicht: obj_T ist entdeckt -> obj_X (noch offen: keiner)
    Ep  26   'neu-3' -> 'Neue Form 4' auf obj_blue
    Ep  29   'neu-4' -> 'Neue Form 5' auf obj_X
    ------------------------------------------------ danach 371 Episoden ohne einen weiteren Knopf

Die Meldung bei Ep 23 sagt es selbst: **nach obj_X ist der Vorrat leer.** Die Welt hat sieben
Koerper, und sie sind nach 29 Episoden vergeben.

Was danach kommt, ist Leerlauf mit Bewegung:

    Ep 239  neu-5 geboren   ->  Ep 262  verhungert nach 24 Ep
    Ep 264  neu-6 geboren   ->  Ep 290  verhungert nach 27 Ep
    Ep 336  neu-7 geboren   ->  Ep 360  verhungert nach 25 Ep
    Ep 353  neu-8 geboren   ->  (Laufende bei Ep 400)

Fuenf Geburten nach der Saettigung, **alle mit derselben Begruendung** - *"nie stabil
wiedererkannt"*, nach 24 bis 27 Episoden. Das ist kein Vergabeproblem mehr: freie Koerper gibt es
(obj_red, obj_green, obj_L, obj_U tragen keine Formklasse), aber keine der neuen Klassen bestaetigt
sich dreimal auf demselben.

# Eine der drei gebundenen Klassen stirbt

    Ep 170  neu-4: verhungert nach 145 Ep (nie stabil wiedererkannt)

`neu-4` war die Klasse von `obj_X` - also genau die, wegen der die Kette gebaut wurde. Sie haelt
145 Episoden und stirbt dann.

**Der Koerper bleibt trotzdem adressierbar:**

    Adressierungen je Block (100 Ep)       Bl1  Bl2  Bl3  Bl4
      obj_X                                 11   19   10   18

Bloecke 3 und 4 liegen nach dem Tod der Klasse, und `obj_X` wird dort weiter angesprochen - ueber
Farbe und Groesse, denn der Eintrag in `state.OBJECTS` ueberlebt das Sterben der Klasse. **Verloren
ist der selbst gegebene Name, nicht der Zugriff.**

Ob das ein Muster ist (die zuletzt gebundene Klasse stirbt zuerst) oder ein Einzelfall, sagt ein
Lauf nicht. `obj_X` ist der schwierigste Koerper - er teilt sich die Farbklasse mit `obj_L` und ist
gerendert fast gleich.

# Die Quote bestaetigt das bekannte Bild

    je 100 Episoden:   3 %  |  17 %  |  16 %  |  16 %

Hochlauf im ersten Block, dann flach. Dasselbe Muster wie
[1109 Episoden ohne Fortschritt](/befunde/langlauf-ohne-fortschritt.md), nur mit drei Aneignungen
am Anfang statt einer.

# Was das heisst

* **Die Kette funktioniert und ist nicht der Engpass mehr.** Sie tut in 29 Episoden alles, was sie
  tun kann. Die drei Knoepfe fallen zuverlaessig, zwei der drei Klassen leben nach 400 Episoden
  noch.
* **Der Engpass ist jetzt die WELT.** Sieben Koerper sind die Obergrenze der Aneignung, und sie ist
  in 29 Episoden erreicht. Alles danach ist Churn: Klassen entstehen, finden keinen Halt,
  verschwinden.
* **Ein Langlauf lohnt in dieser Welt nicht mehr.** Was er messen koennte, ist nach 30 Episoden
  entschieden. Das ist die schaerfste Fassung dessen, was *"laenger laufen lassen bringt nichts"*
  schon sagte - jetzt mit einem Grund statt nur einer Beobachtung.

# Was daraus folgt

Der naechste Schritt ist kein Schalter mehr, sondern eine **Quelle neuer Geometrie**. Der heutige
Erzeuger verteilt Rollen unter sieben vorhandenen Koerpern; er erfindet keine Objekte. Die
vorhandene Verformung (`_novel_shapes`, vier gemessene Proportionen) trifft ausserdem nur das
**erste Geom** - nur die drei Wuerfel sind einzeln-geometrisch.

Solange die Welt nicht mehr hergibt, ist jede weitere Arbeit an der Vergabe-Maschinerie Arbeit an
einem geloesten Problem.

# Fallen

* **Ein Seed, ein Lauf.** Die strukturellen Aussagen (Saettigung bei Ep 29, 3 Knoepfe, Tod von
  neu-4) sind Beobachtungen dieses Laufs; die Verhungerungszeiten (24-27 Ep) wiederholen sich
  auffaellig, sind aber vier Faelle.
* **`neu-8` lebte bei Ep 400 noch** - ihr Schicksal ist offen.
* **Der Lauf ist frisch.** Auf dem gespeicherten Zustand waere er gar nicht moeglich: dort sind
  alle sieben Koerper vergeben, beide Schalter also wirkungslos.
* **Vorgabe bleibt 0** fuer beide Schalter. Sie sind richtig, aber sie bewegen in der heutigen
  Welt nach 29 Episoden nichts mehr.

# Verwandt

* [Der Erzeuger reicht die Probe-Rolle weiter](/befunde/erzeuger-repariert.md) - der Kurzlauf
* [Die freie Vergabe oeffnet die erste Tuer](/befunde/freie-vergabe-erste-tuer.md)
* [Die Geburtenrate hat zwei Ursachen](/befunde/geburtenrate-und-saettigung.md) - "eine gesaettigte Welt", hier beziffert
* [Ziel](/ziel.md)
