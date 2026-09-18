---
type: Befund
title: Der Sockel braucht 80 mm Freiraum - und meine Ueberlappungsrechnung verlangte 66
description: Zwei Pruefstandsmessungen zum Stapelziel. Der Sockel selbst wird auf 5,9 mm genau lokalisiert (max 8,5), systematisch 5,9 mm zur Kamera hin - die Platte ist also kein Ortsproblem. Aber ein Objekt daneben bleibt erst ab 60 mm entlang der Achsen und 80 mm auf den Diagonalen eine EIGENE Detektion; meine erste Freiraum-Schranke rechnete mit Ueberlappung und verlangte 66 mm. Mit der richtigen Schranke passt der Sockel nur bei ACT23_SCENE_N bis 4 in den Arbeitsraum.
tags: [act23, wahrnehmung, stapeln, sockel]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-18T00:00:00Z }
sources:
  - id: ort
    resource: "Offline: frischer ShapeClassifierModule, calibrate() aus 40 Punkten, Sockel allein an 15 Gitterstellen, perceive_all gegen die wahre Stelle"
    title: Lokalisierung des Sockels
  - id: verschmelz
    resource: "Offline: Sockel fest, ein Wuerfel in 8 Richtungen von 60 bis 130 mm, Zahl der Detektionen gezaehlt"
    title: Verschmelzungsabstand um den Sockel
---

# Warum das gemessen werden musste

`RELATION := auf` zielt auf den Sockel. Zwei Groessen entscheiden, ob das ueberhaupt treffen kann:
**wie genau die Platte lokalisiert wird** (ihr Ortsfehler geht voll in den Versatz des Stapels ein,
und die Auflage vertraegt nur 23 mm) und **wie viel Freiraum sie braucht**, damit sie nicht mit
einem Nachbarn zu einem Blob verschmilzt.

# Die Platte ist kein Ortsproblem

    wahre Stelle          Fehler     dx      dy
    (-0,08 | 0,100)        3,7 mm   -3,5   +1,1
    ( 0,00 | 0,100)        5,9 mm   -5,9   +1,0
    ( 0,08 | 0,100)        8,5 mm   -8,4   +1,0
    ... 15 Stellen ...
    Median 5,9 mm, max 8,5 mm        dx Median -5,9   dy Median -0,5
    ueber der Stapeltoleranz von 23 mm:  0 %

Der Fehler ist **systematisch zur Kamera hin** (sie steht bei x = -0,17) und waechst mit dem
Abstand von ihr: -3,5 mm bei x = -0,08, -8,4 mm bei x = +0,08. Das ist dieselbe Parallaxe wie bei
[einem gestapelten Koerper](/befunde/stapeln-bricht-die-tischebene.md), nur klein, weil die Platte
flach ist (Oberkante 8 mm) und ihre sichtbare Seitenflaeche den Schwerpunkt zur Kamera zieht.

Zum Vergleich: ein 24-mm-Wuerfel wird auf **0,8 mm** lokalisiert. Die Platte ist siebenmal
schlechter - und immer noch weit innerhalb dessen, was die Auflage vertraegt.

# Der Freiraum: meine Schranke war die falsche Groesse

Im Code stand zuerst eine **Ueberlappungsrechnung**: Sockel-Halbdiagonale (49 mm) plus
Objekt-Halbdiagonale (17 mm) = 66 mm. Das ist der Abstand, ab dem sich die Koerper nicht mehr
beruehren. **Blobs verschmelzen aber lange vorher.** Gemessen, acht Richtungen, `perceive_all`
zaehlt die Detektionen:

    Richtung    60   70   80   90  100  110  120  130 mm      getrennt ab
       0 Grad    2    2    2    2    2    2    2    2          60 mm
      45 Grad    1    1    2    2    2    2    2    2          80 mm
      90 Grad    2    2    2    2    2    2    2    2          60 mm
     135 Grad    1    2    2    2    2    2    2    2          70 mm
     180 Grad    2    2    2    2    2    2    2    2          60 mm
     225 Grad    1    2    2    2    2    2    2    2          70 mm
     270 Grad    2    2    2    2    2    2    2    2          60 mm
     315 Grad    1    1    2    2    2    2    2    2          80 mm

**60 mm entlang der Achsen, 80 mm auf den Diagonalen** - die Ecken der quadratischen Platte reichen
am weitesten. Maßgeblich ist der schlechteste Fall: **80 mm**, also 14 mm mehr, als meine
Rechnung verlangte.

# Folge: der Arbeitsraum setzt die Szenengroesse

Der Startcheck sucht jetzt die beste Sockelstelle im Raster und meldet sie:

    ACT23_SCENE_N=3   bester Freiraum 105 mm   bei ( 0,000 | 0,134)   reicht
    ACT23_SCENE_N=4   bester Freiraum  86 mm   bei (-0,018 | 0,149)   reicht
    ACT23_SCENE_N=5   bester Freiraum  72 mm                          ZU WENIG
    ACT23_SCENE_N=6   bester Freiraum  62 mm                          ZU WENIG

> **Mit einem Sockel sind hoechstens vier Objekte moeglich.** Der Arbeitsraum ist 240 x 170 mm; eine
> 70-mm-Platte und fuenf 24-mm-Koerper passen nicht mehr so hinein, dass die Wahrnehmung sie
> auseinanderhaelt.

Die Vorgabestelle ist deshalb gesucht, nicht geraten: `(-0,018 | 0,149)`, 86 mm Freiraum bei der
Vorgabe-Szenengroesse 4. Mit der vorherigen geratenen Stelle `(0 | 0,165)` waren es 81 mm - knapp
ueber der Schranke, und im Lauf las der Agent die Platte **14 bis 18 mm** daneben, weil sie
gelegentlich doch verschmolz. Mit der gesuchten Stelle sind es **1 bis 8 mm**.

# Die Haelfte, die sich nicht wegplanen laesst

Ein erfolgreich abgelegtes Objekt **bleibt oben liegen** - die Aufraeumschleife stellt nur
NICHT-kommandierte Koerper zurueck. Ab dem ersten Stapel ist der Sockel-Blob also per Bauart
verschmolzen, und zwar vollstaendig: ein Wuerfel auf der Platte ist in
[0 von 25 Stellen](/befunde/sockel-verschluckt-den-stapel.md) eine eigene Detektion.

**Das ist kein Layoutfehler, sondern die Aufgabe.** Ab dann adressiert "auf den Sockel" einen Blob,
der den Stapel enthaelt - und genau dafuer ist die Farbstreuung da, die "da liegt etwas drauf"
ohne Ueberlapp trennt (0,069 leer gegen 0,149-0,397 belegt). Der Startcheck sagt es beim Start
laut, damit niemand die spaeteren Mehrdeutigkeiten fuer einen Fehler haelt.

# Fallen

* **`ebene: pruefstand`.** Gestellte Szenen, keine Laufaussage.
* **Eine Objektgroesse.** Gemessen mit einem 24-mm-Wuerfel als Nachbarn; ein langes Objekt
  (obj_blue) reicht weiter und braucht mehr.
* **Die Richtungsabhaengigkeit ist eine Eigenschaft der QUADRATISCHEN Platte.** Eine runde Auflage
  haette einen richtungsunabhaengigen Freiraum - und geringeren.
* **Die Slots tragen +-2 mm Jitter.** Die 86 mm sind der Nennwert, nicht die Untergrenze.

# Verwandt

* [Die Relation "auf", gebaut](/mechanismen/relation-auf-gebaut.md) - was diese Zahlen konfigurieren
* [Der Sockel verschluckt den Stapel](/befunde/sockel-verschluckt-den-stapel.md) - warum ein Stapel nur ueber die Farbstreuung sichtbar ist
* [Ein gestapelter Koerper liest 16 mm daneben](/befunde/stapeln-bricht-die-tischebene.md) - dieselbe Parallaxe, groesser
* [Nachbarnaehe im Lauf](/befunde/nachbarnaehe-im-lauf.md) - warum Verschmelzungsabstaende hier ueberhaupt zaehlen
