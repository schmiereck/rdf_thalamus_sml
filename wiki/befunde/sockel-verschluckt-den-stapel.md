---
type: Befund
title: Der Sockel verschluckt den Stapel - aber die Farbstreuung verraet ihn
description: Ein Wuerfel auf der breiten Sockelplatte wird in 0 von 25 Stellen eine eigene Detektion. Nicht verschmolzen mit Versatz, sondern vollstaendig verschluckt - die Flaeche aendert sich um kein einziges Pixel, weil die Silhouette des Wuerfels ganz innerhalb der Platte liegt. Der Chroma-Schnitt hilft nicht, er ist auf "Deskriptor trifft keine Klasse" verriegelt. Was den Stapel doch verraet, ist cspread: 0,069 leer gegen 0,149 bis 0,397 belegt, ueber 100 Positiv- und 50 Negativfaelle ohne einen einzigen Ueberlapp.
tags: [act23, wahrnehmung, stapeln, sockel]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-17T00:00:00Z }
sources:
  - id: sonde
    resource: "Offline: frischer ShapeClassifierModule, calibrate() aus 40 Punkten, perceive_all an 25 Gitterstellen des Arbeitsraums; Sockel allein / Wuerfel drauf (4 Farben) / Wuerfel daneben"
    title: Wahrnehmung des Sockels
  - id: entwurf
    resource: /fragen/stapeln-als-aufgabe.md
    title: Stapeln als neue Aufgabe
---

# Warum es den Sockel gibt

Stufe 2 braucht ein Stapelziel, dessen geometrische Toleranz zur vorhandenen Ablagegenauigkeit
passt. Ein 24-mm-Wuerfel auf einem 24-mm-Wuerfel verlangt unter 12 mm Versatz, gemessen sind
21-25 mm ([Ablage und Platzieren](/befunde/ablage-und-platzieren.md)) - die Aufgabe waere von
Anfang an unloesbar und das Lernsignal null. Eine **70 x 70 x 8 mm** Platte gibt 35 - 12 = **23 mm**
Toleranz, und weil sie flach ist, sollte sie zugleich den Parallaxenfehler klein halten
([16 mm auf einem zweiten Wuerfel](/befunde/stapeln-bricht-die-tischebene.md)).

Die zweite Erwartung hat sich erledigt, bevor sie geprueft werden konnte.

# Der gestapelte Koerper ist nicht ungenau - er ist weg

    nur Sockel:              1 Detektion   area 1396   pos [-0,006, +0,150]   cspread 0,072
    Sockel + Wuerfel DRAUF:  1 Detektion   area 1396   pos [-0,006, +0,150]   cspread 0,342
    Sockel + Wuerfel DANEBEN: 2 Detektionen

    eigene Detektion fuer den gestapelten Wuerfel:  0 von 25 Stellen

**Die Flaeche aendert sich um kein einziges Pixel.** Die Silhouette des Wuerfels liegt vollstaendig
innerhalb der der Platte; aus Sicht der Kamera ist da nichts Neues. Die Frage nach dem
Lokalisierungsfehler stellt sich damit gar nicht - es gibt nichts zu lokalisieren.

**Der Chroma-Schnitt rettet es nicht** (`ACT_SHAPE_CHROMA_SPLIT=1`: ebenfalls 0 von 25). Das
Werkzeug waere das richtige, sein Tor ist das falsche.

> **BERICHTIGT 2026-09-21: es ist ein ANDERES Tor als hier stand.** Die Begruendung lautete, der
> Chroma-Schnitt sei auf *"Deskriptor trifft KEINE Klasse"* verriegelt. Diese Sperre sitzt am
> **Erosions**-Split, nicht am Chroma-Schnitt. Einzeln nachgerechnet faellt in Wahrheit jedes Tor
> bis auf die **raeumliche Wache**: Chroma-Abstand 0,805 gegen eine Schwelle von 0,12, Deckung
> 1,00 - und dann Trennung 0,29 gegen geforderte 1,0. Die Wache verwirft Teile mit
> zusammenfallenden Schwerpunkten, weil das Schattierungsschichten EINES Koerpers sind; ein
> gestapelter Koerper sitzt konzentrisch und sieht fuer sie genauso aus.
> Setzt man sie aus, sobald die Farbstreuung sagt, dass mehr als ein Ding im Fleck ist, trifft die
> Detektion den Wuerfel in **24 von 25** Stellen, ohne dass die leere Platte zerfaellt.
> Gemessen in [Der Stapel wird sichtbar](/befunde/stapel-wird-sichtbar.md).

> **Verallgemeinert:** fuer diese Kamera ist ein Koerper, der auf einem GROESSEREN Koerper liegt,
> in der SILHOUETTE unsichtbar. Das gilt nicht nur fuer den Sockel; es ist die Eigenschaft einer
> Ein-Ansichten-Silhouette. Eine Auflage, die KLEINER ist als das getragene Objekt, kehrt das um -
> kauft aber die Toleranz zurueck, um die es beim Sockel ging.
>
> **EINGESCHRAENKT 2026-09-21.** Hier stand "unsichtbar" ohne den Zusatz "in der Silhouette", und
> das war zu weit. Die Flaechenmessung oben steht; die FARBE traegt aber, was die Umrisslinie
> nicht hergibt - und dieselbe Seite misst das weiter unten selbst (0,069 leer gegen 0,149-0,397
> belegt, ohne Ueberlapp). Ich hatte es als ANZEIGE gelesen und nicht als LOKALISIERUNG. Mit dem
> Chroma-Schnitt und ausgesetzter raeumlicher Wache wird der Koerper in **24 von 25** Stellen
> gefunden: [Der Stapel wird sichtbar](/befunde/stapel-wird-sichtbar.md).

# Was ihn doch verraet

    Farbstreuung (cspread) der Sockel-Detektion, 25 Stellen im Arbeitsraum

      Sockel allein                n= 25   Median 0,069   min 0,052   max 0,118
      Sockel, Wuerfel DANEBEN      n= 25   Median 0,069   min 0,052   max 0,118
      Sockel, rot DRAUF            n= 25   Median 0,346   min 0,287
      Sockel, gruen DRAUF          n= 25   Median 0,345   min 0,286
      Sockel, orange DRAUF         n= 25   Median 0,330   min 0,281
      Sockel, violett DRAUF        n= 25   Median 0,161   min 0,149

      hoechster LEER-Wert 0,118  gegen  niedrigster DRAUF-Wert 0,149   ->  Abstand +0,030
      100 Positiv- gegen 50 Negativfaelle, KEIN Ueberlapp

`cspread` ist keine neue Groesse: sie steht seit jeher auf jeder Detektion, und `_merge_th()` lernt
ihre Schwelle bereits aus den EIGENEN Einzelobjekt-Werten des Agenten (0,995-Quantil). Zusammen mit
der unveraenderten Flaeche ergibt das eine Signatur aus ausschliesslich schon berechneten Groessen:

> **Flaeche unveraendert + Farbstreuung hoch = da liegt etwas drauf.**
> Das trennt einen STAPEL auch von zwei nebeneinander verschmolzenen Koerpern, deren Flaeche sich
> ADDIERT - und genau diese Verwechslung ist der Grund, warum `area_hi` als Verschmelzungswache
> versagt hat ([dort dokumentiert](/mechanismen/adresse-ohne-klasse.md)).

**"A liegt auf B" waere damit als RELATION lesbar, nicht als zweite Position.** Das ist nicht der
Notbehelf, als der es zuerst aussieht: es ist, was die Relation bedeutet. Eine Position von A
braucht niemand, um zu wissen, dass A auf B liegt.

# Grenzen dieses Wegs

* **Violett ist der Engpass** (0,161 gegen die Leer-Obergrenze 0,118) - es ist die dem Sockelblau
  naechste Farbe. Ein Koerper in der Farbe DES SOCKELS wuerde nicht trennen. Der Sockel steht
  deshalb nicht in `_FARB_KOERPER`: die Episoden-Permutation kann ihm keine der sieben
  Objektfarben geben.
* **Die Flaechenhaelfte der Signatur gilt fuer DEN SOCKEL**, weil er quadratisch und symmetrisch
  ist und seine Flaeche an allen 25 Stellen exakt 1396 misst. Bei einem beliebigen Bezugskoerper
  schwankt sie mit der Lage; die Signatur muesste dann relativ zu seiner eigenen Flaechenstatistik
  gelesen werden.
* **Der Sockel sieht selbst wie eine Verschmelzung aus:** Flaeche 1396, und die gemessene
  Verschmelzungsspanne ist 822-1390 bei einer groessten TRAININGSform von ~940. Er wird als Form
  `U` und Band `dick` gelesen. Fuer die Adressierung ist das unkritisch (eine 70-mm-Platte ist von
  allem anderen weit weg), fuer jede Wache, die ueber die Flaeche geht, ist es eine Falle.
* **`ebene: pruefstand`.** Gestellte Szenen, kein Lauf.

# Verwandt

* [Stufe 2 vorbereitet](/mechanismen/stufe2-vorbereitet.md) - was daraufhin gebaut wurde
* [Stapeln als neue Aufgabe](/fragen/stapeln-als-aufgabe.md) - der Entwurf
* [Ein gestapelter Koerper liest 16 mm daneben](/befunde/stapeln-bricht-die-tischebene.md) - die Messung, die der Sockel entkraeftet: bei breiter Auflage gibt es gar keinen Lesefehler, weil es keine Lesung gibt
* [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md) - warum Blobs verschmelzen und was dagegen gebaut ist
