---
type: Befund
title: Der Erzeuger reicht die Probe-Rolle weiter - und der Agent eignet sich zum ersten Mal einen Koerper an, den er strukturell nie erreichen konnte
description: Mit ACT23_NOVEL_WEITER gibt der Neuheits-Erzeuger die Probe-Rolle an den naechsten unentdeckten Koerper, statt nach der ersten Entdeckung fuer immer zu schweigen. Zusammen mit der freien Vergabe: 3 vergebene Knoepfe gegen 1, obj_X wird zum ersten Mal in die Szene gestellt, selbst benannt, kommandierbar und 17-mal adressiert. Und die eine verhungerte Klasse stirbt erstmals aus dem richtigen Grund - nie stabil wiedererkannt, statt kein Knopf zu haben.
tags: [act23, selbstlernen, formklassen, kommando, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-15T00:00:00Z }
sources:
  - id: ab
    resource: "Zwei frische Laeufe (ACT23_FRESH=1) je 140 Episoden, Vorgabe gegen ACT23_FREIE_VERGABE=1 ACT23_NOVEL_WEITER=1"
    title: Erzeuger und freie Vergabe zusammen
  - id: vorher
    resource: /befunde/freie-vergabe-erste-tuer.md
    title: Der Lauf davor, der die Reihenfolge klaerte
---

# Der Riegel und sein Grund

`spawn_novel_shape` kehrt zurueck, sobald der Probe-Koerper entdeckt ist - **mit echtem Grund**:
danach verwaltet ihn `randomize_objects`, und ein zusaetzliches Hinstellen fuellte die Szene ueber
`SCENE_N` (im Lauf vom 2026-08-21 45-mal geschehen). Die Folge ist trotzdem, dass es **nie eine
zweite neue Form gibt**.

Die Reparatur ist klein, weil der schwierige Teil schon dastand: die `else`-Verzweigung behandelt
einen Probe-Koerper, der nicht `obj_T` ist, bereits richtig (*"ein frischer Koerper braucht die
Verformung nicht: seine Neuheit ist er selbst"*). Es fehlte allein, dass die Rolle je
weitergegeben wird.

**Und genau der Erzeuger musste es sein.** Aus dem [vorigen Lauf](/befunde/freie-vergabe-erste-tuer.md):
ein Koerper braucht die Szene fuer den Knopf und den Knopf fuer die Szene (`act16.OBJS` waechst nur
bei der Vergabe). Der Erzeuger ist der **einzige** Pfad, der einen Koerper OHNE Knopf in die Szene
stellt.

# Zahlen

    Arm        Ep   Quote   Geburten   Knoepfe   verhungert   adressierte Koerper
    nw_aus    140   7,1 %       4         1          0                6
    nw_beide  140   5,7 %       4         3          1                7

    nw_beide:
      [Neuheit] Probe-Rolle weitergereicht: obj_T ist entdeckt -> obj_X (noch offen: keiner)
      'neu-1' -> 'Neue Form 2' auf obj_T
      'neu-3' -> 'Neue Form 4' auf obj_blue
      'neu-4' -> 'Neue Form 5' auf obj_X        <- der Koerper, den es vorher nicht gab

    Adressierungen je Koerper (nw_beide)
      obj_blue 40 | obj_L 20 | obj_red 19 | obj_X 17 | obj_T 16 | obj_green 13 | obj_U 11

**`obj_X` wird zum ersten Mal in die Szene gestellt, selbst benannt, kommandierbar - und
17-mal adressiert.** Kein einmaliger Treffer, sondern ein regulaerer Teilnehmer.

Im Vorgabearm bleibt es bei sechs Koerpern und einem Knopf, bei gleich vielen Geburten (4 zu 4).
**Der Gewinn sind nicht mehr Geburten, sondern dass eine Geburt den Knopf erreicht.**

# Die verhungerte Klasse stirbt erstmals aus dem richtigen Grund

    nw_aus     0 Kandidaten verhungert   (es wird nach dem ersten Knopf keiner mehr Kandidat)
    nw_beide   1 Kandidat verhungert:
               "neu-2: verhungert nach 27 Ep (nie stabil wiedererkannt)"

Die Null im Vorgabearm ist kein gutes Zeichen. Dort kann niemand als Kandidat sterben, weil
niemand mehr Kandidat wird - die 13-von-13-Meldung aus dem Langlauf war Buchhaltung, keine
Auslese.

Hier stirbt `neu-2`, **weil die Wahrnehmung sie nicht stabil wiedererkennt**. Das ist die Auslese,
die der Verhungerungsschutz leisten soll: eine Phantomklasse verschwindet, eine tragfaehige bleibt.
Zum ersten Mal ist der Mechanismus an der Sache gemessen worden statt an einer Engstelle davor.

# Die ehrliche Grenze steht in der Meldung selbst

    "-> obj_X (noch offen: keiner)"

Nach `obj_X` ist der Vorrat leer. Die Welt hat **sieben** Koerper, und mehr kann dieser Erzeuger
nicht anbieten - er verteilt Rollen, er erfindet keine Objekte. Danach schweigt er wieder, und das
ist eine ehrliche Auskunft, keine Panne.

Wer echte Formvielfalt will, braucht eine Quelle neuer Geometrie. Die vorhandene Verformung
(`_novel_shapes`, vier gemessene Proportionen) trifft ausserdem nur das **erste Geom** eines
Koerpers - `obj_T` hat deren zwei, `obj_U` drei. Nur die drei Wuerfel sind einzeln-geometrisch und
damit sauber verformbar; das steht so noch nirgends und relativiert den Kommentar am Erzeuger, der
nur `obj_X` als zusammengesetzt nennt.

# Bewertung

* **Zum ersten Mal in dieser Linie ein Ergebnis auf der Zielgroesse.** Der Agent erschliesst sich
  selbst einen Koerper, der ihm strukturell verschlossen war - ohne Etikett, ohne GUI-Klick, ohne
  privilegierte Einfuehrung.
* **Die Quote sagt nichts** (7,1 gegen 5,7 % sind 10 gegen 8 Lieferungen in 140 frischen Episoden).
  Sie war auch nie das Kriterium.
* **Drei Schalter, eine Kette.** Erzeuger (`NOVEL_WEITER`) bringt den Koerper in die Szene, freie
  Vergabe (`FREIE_VERGABE`) gibt ihm den Knopf, der Verhungerungsschutz entscheidet, ob die Klasse
  lebt. Einzeln bewegt keiner davon etwas - das war der Befund des vorigen Laufs und ist hier
  bestaetigt.

# Fallen

* **Je ein Seed, 140 frische Episoden.** Die strukturellen Aussagen (Weitergabe, 3 Knoepfe, obj_X
  adressiert) sind mechanisch belegt; Geburtenzahlen und Quote sind es nicht.
* **Nur bis obj_X.** Die Kette endet, wenn alle sieben Koerper vergeben sind. Ein Langlauf wuerde
  danach wieder stehen.
* **Nicht geprueft**, ob die drei Knoepfe auch ueber Hunderte Episoden halten oder ob die jungen
  Klassen spaeter doch noch sterben.
* **Vorgabe bleibt 0** fuer beide Schalter.

# Verwandt

* [Die freie Vergabe oeffnet die erste Tuer](/befunde/freie-vergabe-erste-tuer.md) - der Lauf davor
* [Die Vergabe-Engstelle, diagnostiziert](/befunde/vergabe-engstelle-diagnose.md) - die Diagnose
* [Die Geburtenrate hat zwei Ursachen](/befunde/geburtenrate-und-saettigung.md) - der tote Erzeuger, hier repariert
* [Ziel](/ziel.md) - der Massstab
