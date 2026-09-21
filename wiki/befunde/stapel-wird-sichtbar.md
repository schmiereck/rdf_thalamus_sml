---
type: Befund
title: Der gestapelte Koerper wird sichtbar - die raeumliche Wache war der Riegel, nicht die Silhouette
description: Ein Wuerfel auf der Sockelplatte bekam in 0 von 25 Stellen eine eigene Detektion. Die Ursache ist jetzt genau lokalisiert und es ist eine andere als bisher notiert - nicht das Klassentor des Chroma-Schnitts, sondern seine RAEUMLICHE WACHE. Sie verwirft Teile mit zusammenfallenden Schwerpunkten, weil das Schattierungsschichten EINES Koerpers sind; ein gestapelter Koerper sitzt aber konzentrisch auf seiner Auflage und faellt in dieselbe Falle (Trennung 0,29 gegen geforderte 1,0, bei einem Chroma-Abstand von 0,805 gegen eine Schwelle von 0,12). Wird die Wache ausgesetzt, sobald die Farbstreuung sagt, dass mehr als ein Ding im Fleck ist, trifft die Detektion den Wuerfel in 24 von 25 Stellen - und die leere Platte zerfaellt in 0 von 25. Damit ist die Voraussetzung fuer Stufe 4 da.
tags: [act23, stapeln, wahrnehmung, chroma-split, sprache]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-21T00:00:00Z }
sources:
  - id: riegel
    resource: "Sonde auf einer Kopie von act23_state.pkl (ad9d768c): Sockel allein und Sockel mit Wuerfel, die Ausstiege von _chroma_teile einzeln nachgerechnet"
    title: Welcher Riegel es wirklich ist
  - id: sicht
    resource: "Sonde, 25 Rasterstellen x (leer / Wuerfel drauf) x drei Einstellungen (ohne Chroma-Schnitt, mit, mit + Ausnahme)"
    title: Die Sichtbarkeitsmessung
  - id: alt
    resource: /befunde/sockel-verschluckt-den-stapel.md
    title: Der Befund, dessen Ursache hier berichtigt wird
---

# Warum das ueberhaupt gebraucht wird

Die Sprache kann bisher nur *"lege X auf Y"*. Der naechste Schritt ist dieselbe Relation im
**Subjekt**: *"nimm das, was auf Y liegt"* - die Voraussetzung fuers Umstapeln und der eigentliche
Beleg, dass es eine Sprache ist und kein Sonderfall.

Dafuer muss der Agent den gestapelten Koerper **finden**. Bisher konnte er das nicht
([0 von 25](/befunde/sockel-verschluckt-den-stapel.md)).

# Die Ursache war eine andere als notiert

Auf der alten Seite steht, der Chroma-Schnitt sei *"auf den Verdachtsfall Deskriptor trifft KEINE
Klasse verriegelt"*. **Das stimmt nicht** - diese Sperre sitzt am Erosions-Split, nicht am
Chroma-Schnitt. Die Ausstiege einzeln nachgerechnet:

    Sockel LEER            Chroma-Abstand 0,247 > TH 0,12  -> weiter
                           zwei tragende Teile?   NEIN     -> Ausstieg (richtig so)

    Sockel + Wuerfel       Chroma-Abstand 0,805 > TH 0,12  -> weiter
                           zwei tragende Teile?   ja, Deckung 1,00  -> weiter
                           raeumliche Wache  0,29 gegen 1,0         -> AUSSTIEG

**Alle Tore fallen bis auf die raeumliche Wache.** Sie verlangt, dass die Schwerpunkte der beiden
Teile weit auseinanderliegen - und ist genau dafuer gebaut: ein schattierter Einzelkoerper zerfaellt
chromatisch in Deck- und Seitenflaechen, deren Schwerpunkte fast zusammenfallen.

> **Ein gestapelter Koerper sieht fuer diese Wache aus wie eine Schattierungsschicht**, weil er
> konzentrisch auf seiner Auflage sitzt. Die Wache ist nicht falsch, sie ist fuer diesen Fall blind.

(Nebenbei: `ACT_SHAPE_CHROMA_SPLIT` steht per Vorgabe auf **0**. Auch eingeschaltet aendert es
nichts - gemessen ebenfalls 0 von 25.)

# Die Ausnahme braucht keine neue Zahl

Die Wache unterscheidet "nebeneinander" von "uebereinander geschichtet" **raeumlich**. Was sie
nicht kann, kann die **Farbstreuung**: sie misst, wie weit die Pixel-Chromatizitaet im Fleck
streut, und ein Fleck mit zwei Farbpopulationen ueberschreitet den Massstab eines Einzelobjekts.

    leere Platte          Farbstreuung 0,068
    Platte mit Wuerfel    Farbstreuung 0,329
    Massstab              0,120   (Median + uebliche Schwankung der eigenen Sichtungen)

Der Massstab ist derselbe wie beim [Stapel-Selbsturteil](/befunde/selbstrichter-stapel.md) und beim
Lerntor des Hoehenschaetzers - **dritte Verwendung derselben gemessenen Groesse**, keine neue
Schwelle. Liegt der Fleck darueber, wird die raeumliche Wache ausgesetzt.

# Ergebnis

                                          Wuerfel getroffen   leere Platte zerfaellt
    ohne Chroma-Schnitt (Vorgabe)             0 von 25              0 von 25
    Chroma-Schnitt an, Wache unveraendert     0 von 25              0 von 25
    Chroma-Schnitt + Ausnahme                24 von 25              0 von 25

**24 von 25**, und die Gegenprobe kostet nichts: die leere Platte zerfaellt in keinem einzigen Fall.
Getroffen heisst hier, dass der kleinere der beiden Teile naeher als 15 mm an der wahren Wuerfelmitte
liegt - eine Adresse, die auf den Koerper zeigt, nicht nur eine zweite Detektion.

# Was damit widerlegt ist

Die alte Seite verallgemeinert:

> *fuer diese Kamera ist ein Koerper, der auf einem GROESSEREN Koerper liegt, unsichtbar. Das gilt
> nicht nur fuer den Sockel; es ist die Eigenschaft einer Ein-Ansichten-Silhouette.*

**Das gilt nur fuer die Silhouette, nicht fuer die Wahrnehmung.** Die Flaeche aendert sich
weiterhin um kein Pixel - diese Messung steht. Aber die Farbe traegt, was die Umrisslinie nicht
hergibt, und die alte Seite hatte das selbst gemessen (0,069 leer gegen 0,149-0,397 belegt, ohne
Ueberlapp); sie hat es nur als *Anzeige* gelesen und nicht als *Lokalisierung*. Der Abschnitt ist
dort entsprechend berichtigt.

# Fallen

* **`ebene: pruefstand`.** Eine aufgeraeumte Welt, ein Koerper auf einer Platte. Ob es im Lauf
  traegt - mit Nachbarn, Arm und wechselnden Objektfarben - ist **nicht gemessen**, und nach
  [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) sagt das nichts vorher.
* **Die Farbe des oberen Koerpers entscheidet.** Die alte Seite misst 0,161 fuer violett gegen
  0,330-0,346 fuer rot/gruen/orange. Ein Koerper, dessen Chroma der Platte nahe kommt, bleibt
  unsichtbar - der Massstab liegt bei 0,120, violett kaeme also noch durch, aber die Spanne ist
  eng. **Eine blaue Kiste auf der blauen Platte bleibt unsichtbar.**
* **Es ist die leichte Richtung.** Der Wuerfel ist KLEINER als die Platte und sitzt mittig. Zwei
  gleich grosse Koerper uebereinander, oder ein Koerper, der ueber den Rand haengt, sind nicht
  gemessen.
* **Vorgabe bleibt 0** fuer beide Schalter. Der Chroma-Schnitt veraendert die Wahrnehmung in jeder
  Episode, und seine Wirkung auf die Lieferquote ist
  [ausdruecklich geschlossen als nicht nachweisbar](/fragen/offene-faeden-act23.md) - er darf
  deshalb nicht nebenbei mitlaufen.

# Verwandt

* [Der Sockel verschluckt den Stapel](/befunde/sockel-verschluckt-den-stapel.md) - die Ursprungsmessung, hier in der Ursache berichtigt
* [Der Stapel-Selbstrichter](/befunde/selbstrichter-stapel.md) - woher der Massstab kommt
* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - Stufe 4
