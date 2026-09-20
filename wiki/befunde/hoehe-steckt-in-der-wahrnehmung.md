---
type: Befund
title: Die Hoehe der Auflage steckt in der Wahrnehmung - 77 Prozent der Stufen aus scheinbarer Flaeche, Ort und Dicke
description: Vor dem Entfernen des letzten Privilegs auf dem Stapelpfad (die Oberkante kommt heute aus sim.m.geom_size) die Vorfrage - sieht der Agent die Hoehe ueberhaupt? Gemessen an 30 Stellen x 3 Hoehen: die scheinbare FLAECHE steigt an JEDER der 30 Stellen streng monoton mit der Hoehe, 30 von 30. Allein taugt sie nichts (der Ort streut 2,7-mal so stark wie der Hoehenhub), zusammen mit dem wahrgenommenen ORT und der Materialdicke aber sehr wohl: 1,3 mm Fehler und 77 Prozent richtige Stufe gegen 4,0 mm und 33 Prozent Grundrate, stellenweise gehalten. Alle drei Groessen sind wahrgenommen, keine privilegiert. Nebenbefund gegen meine Erwartung - der Ortsfehler sinkt mit der Hoehe, statt zu steigen.
tags: [act23, stapeln, wahrnehmung, privileg, hoehe]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-20T00:00:00Z }
sources:
  - id: sonde
    resource: "Sonde auf einer Kopie von act23_state.pkl (ad9d768c): der Sockel allein auf dem Tisch, 30 Rasterstellen im Arbeitsraum x Hoehen 6/10/14 mm, je eine Detektion aus perceive_all (240er Rendern), 90 Zeilen, keine fehlende Detektion"
    title: Die Hoehensonde
  - id: privileg
    resource: /mechanismen/relation-auf-gebaut.md
    title: Wo die Oberkante heute herkommt
---

# Die Frage

`_ziel_aufloesen` rechnet die Ablagehoehe als `GRASP_Z + Oberkante des Bezugskoerpers`, und die
Oberkante liest es aus `sim.m.geom_size`. Der Code nennt das selbst *"das einzige Privileg auf
diesem Pfad -- Teacher-Geruest, weil eine Ebenen-Homographie keine Hoehe hergibt"*.

Nach [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) muss ein Geruest zur Testzeit verschwinden.
Die Vorfrage vor dem Abbauen ist aber nicht "wie ersetze ich es", sondern:

> **Steckt die Hoehe ueberhaupt in dem, was der Agent sieht?**

Ohne diese Antwort waere jeder Umbau ein Schuss ins Dunkle.

# Aufbau

Der Sockel allein auf dem Tisch, alle Objekte geparkt, der Arm in Grundstellung - also genau die
Lage, in der auch die Zieladresse aufgeloest wird. 30 Rasterstellen im Arbeitsraum, jede in drei
Hoehen (6, 10, 14 mm). Je Stelle und Hoehe **eine Detektion aus `perceive_all`**, dieselbe, die
`finde_nach_eigenschaften` bekommt. Aufgezeichnet wird, was in der Detektion steht.

Die Zuordnung Detektion -> Sockel laeuft ueber die Wahrheit. Das ist hier zulaessig: gefragt ist,
was IN der Detektion steckt, nicht ob der Agent sie findet - Letzteres ist gemessen und funktioniert
([Das Ablageziel als Adresse](/befunde/ziel-als-adresse-gemessen.md)).

# Die scheinbare Flaeche traegt die Hoehe - vollstaendig

                 6 mm      10 mm      14 mm     gepaart 14-6 mm
    Flaeche      1372       1425       1479     +102   30/30 positiv, 30/30 streng monoton
    Dicke        13,0       13,5       13,5     +0,8   23/30 positiv,  3/30 streng monoton
    cspread     0,079      0,077      0,073    -0,005  13/30 positiv,  8/30 streng monoton

**30 von 30 Stellen streng monoton.** Es gibt keine Ausnahme und kein Rauschen - die Vergroesserung
ist reine Perspektive, und MuJoCo ist hier deterministisch. Die Information ist nicht nur vorhanden,
sie ist **exakt**.

## Und trotzdem taugt die Flaeche allein nichts

    Hoehenhub / Streuung ueber die Stellen:  0,37

Der Ort streut fast dreimal so stark wie der Hoehenhub: ein flacher Sockel nah an der Kamera liest
groesser als ein hoher weit weg. Wer nur die Flaeche misst, raet.

    Hoehe aus Flaeche                       3,47 mm   richtige Stufe 33 %   (= Grundrate)

# Zusammen mit dem wahrgenommenen ORT wird es eindeutig

Der Ort ist kein Privileg - er ist das Erste, was die Detektion liefert. Damit:

    Hoehe aus                                Fehler    richtige Stufe
      Flaeche                                3,47 mm       33 %
      Flaeche + Dicke                        3,28 mm       38 %
      Flaeche + Ort                          1,32 mm       62 %
      Flaeche + Dicke + Ort                  1,31 mm       77 %
      ------------------------------------------------------------
      Grundrate (immer die mittlere Stufe)   4,00 mm       33 %

**Stellenweise gehalten**, nie zufaellig geteilt: die vorhergesagte Stelle kommt in keiner
Trainingszeile vor. Der Zusammenhang ist also nicht an die Stellen angepasst, sondern uebertraegt
sich auf eine ungesehene.

Ein lineares Modell reicht. Das ist der Punkt: was ein Kleinste-Quadrate-Fit aus vier
wahrgenommenen Zahlen holt, kann ein lernendes Netz auch.

# Der Nebenbefund, der meiner Erwartung widerspricht

    Ortsfehler    6 mm: 0,006    10 mm: 0,005    14 mm: 0,004
    gepaart 14-6 mm: -0,002 -- 0 von 30 positiv

Ich hatte das Gegenteil erwartet. Nach
[Ein gestapelter Koerper liest 16 mm daneben](/befunde/stapeln-bricht-die-tischebene.md) verschiebt
eine angehobene Flaeche ihren Schwerpunkt radial von der Kamera weg, mit `r = +1,00` zum
Kameraabstand - hoeher haette also **weiter daneben** heissen muessen.

Die Aufloesung ist einfach und bestaetigt dieselbe Physik: **die Homographie ist nicht auf die
Tischplatte geeicht, sondern auf die Hoehe der Kalibrierkoerper** (~12 mm). Ein 14-mm-Sockel liegt
dieser Ebene naeher als ein 6-mm-Sockel, also liest er genauer. Der Fehler ist monoton in der
Hoehe - nur mit dem Nullpunkt bei ~12 mm statt bei 0.

> **Nicht verwertbar, und zwar grundsaetzlich.** Den Ortsfehler zu messen setzt voraus, den wahren
> Ort zu kennen. Er ist eine Aussage ueber die Kamera, kein Kanal fuer den Agenten. Die Flaeche ist
> es.

# Was das fuer das Privileg heisst

Die Oberkante kann aus der Wahrnehmung kommen. Was jetzt zu bauen ist:

1. Aus der Detektion, die die Zieladresse ohnehin aufloest, ein **gelerntes** Hoehenmass statt
   `geom_size` - Flaeche, Ort und Dicke stehen in derselben Detektion, `area0` wird bereits
   mitgeschrieben.
2. `tgt_z` im Zustandsvektor aus dieser Schaetzung speisen statt aus der Wahrheit.
3. **act23-A/B**, denn erst das belegt eine Wirkung.

# Fallen

* **`ebene: pruefstand`.** Nach [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) sagt das ueber
  einen act23-Lauf **nichts** vorher. Die Sonde lokalisiert die Information, mehr nicht - dreimal
  ist hier schon ein sauberes Pruefstandsergebnis auf act23-Ebene verpufft.
* **Die Welt der Sonde ist aufgeraeumt.** Der Sockel steht allein. Im Lauf stehen Nachbarn daneben,
  und ab dem ersten Stapel ist der Blob ohnehin verschmolzen
  ([0 von 25](/befunde/sockel-verschluckt-den-stapel.md)). Eine verschmolzene Flaeche ist groesser
  und wuerde als "hoeher" gelesen. Genau das ist die naechste Messung, nicht diese.
* **Der Grundriss ist fest, und das ist inzwischen gemessen.** Die Flaeche traegt die Hoehe nur,
  weil ALLE Sockel 70 x 70 mm haben. **Die Bewaehrungsprobe ist gelaufen und faellt durch**
  ([Die zweite Auflage bricht den Hoehenschaetzer](/befunde/zweiter-grundriss-bricht-die-hoehe.md)):
  eine 50-mm-Platte wird 6,0 mm zu niedrig gelesen, und beide Grundrisse zu zeigen hilft NICHT -
  der Grundriss hebt die Flaeche um 685, die Hoehe nur um 91. Je Grundriss einzeln bleibt es bei
  68-77 %. **Alle Zahlen dieser Seite gelten fuer EINE Auflagenform.**
* **Drei Stufen, 4 mm auseinander.** 77 % richtige Stufe heisst nicht 77 % in einer Welt mit
  feineren oder weiteren Hoehen.
* **Die Dicke bringt nur mit dem Ort etwas** (38 % allein, aber 62 -> 77 % als Zugabe). Sie ist
  gequantelt (Pixel) und fuer sich zu grob.

# Verwandt

* [Die Relation "auf" gebaut](/mechanismen/relation-auf-gebaut.md) - wo die Oberkante heute herkommt
* [Ein gestapelter Koerper liest 16 mm daneben](/befunde/stapeln-bricht-die-tischebene.md) - dieselbe Physik, anderer Nullpunkt
* [Der Sockel verschluckt den Stapel](/befunde/sockel-verschluckt-den-stapel.md) - warum die belegte Auflage eine andere Messung braucht
* [Die Policy lernt die Hoehe als Ort](/befunde/policy-lernt-hoehe-als-ort.md) - was die Policy mit der privilegierten Hoehe heute tut
* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) - warum das Geruest fallen muss
* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - Stufe 3
