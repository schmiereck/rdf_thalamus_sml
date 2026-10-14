---
type: Befund
title: Wie genau sind die Tisch-Homographien?
description: Beide Homographien (shape_clf.H aus dem Zustand, Fovea-H) sind auf dem Tisch sehr genau - perceive_all trifft den wahren Grundriss-Schwerpunkt im Median auf 0,8 mm (max 3,3 mm), Mitte und Rand gleich. Ihr einziger grosser Fehler ist die Hoehe - die Kalibrierung legt eine Ebene durch die Mitte des 24-mm-Wuerfels, und je Millimeter Abweichung davon kommen rund 0,6 mm Ortsfehler dazu (30 mm angehoben 18 mm, 60 mm angehoben 40 mm). Die Fovea-H ist gleich gut, am Rand etwas schlechter; die beiden H weichen im Median 1,4 mm voneinander ab.
tags: [act23, wahrnehmung, homographie, perceive_all, fovea]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-10-14T00:00:00Z }
sources:
  - id: sonde
    resource: "Sonde im Scratchpad (nicht committet), Stand 9396979, Kopie des Hauptzustands df320cd0; Kamera 240 px, Balken auf LONG_HALF umbemessen"
    title: Homographie-Sonde
  - id: plan
    resource: /fragen/perceive-all-abloesen.md
    title: perceive_all abloesen
---

# Frage

Wie genau ist die heutige Umrechnung vom Bild auf den Tisch, getrennt nach Tischmitte, Rand und
gehobenen Koerpern? Das ist die Messlatte fuer Schritt 1 in
[perceive_all abloesen](/fragen/perceive-all-abloesen.md). Nutzerauftrag 2026-10-14, mit der
Zusatzfrage, ob sich auch die Fovea-Homographie messen laesst.

**Ja, sie laesst sich messen:** `setup_following_fovea` gibt `px_to_world` nach aussen, mit dem
gespeicherten Fovea-Netz ohne Training (Aufbau in 0 s).

# Aufbau

* **A, rein geometrisch:** ein wahrer 3D-Punkt wird mit dem Kameramodell ins Bild projiziert und
  ueber H zurueck auf den Tisch gerechnet. 11 x 11 Punkte ueber den Arbeitsraum, sieben Hoehen.
  Das Kameramodell ist geprueft: die projizierte Wuerfelmitte trifft den Farbschwerpunkt im
  gerenderten Bild auf 0,66 px (max 1,1 px).
* **B, perceive_all Ende zu Ende:** acht Koerper (Wuerfel rot und gruen, Balken, L, U, T, X, Y)
  einzeln auf dem Tisch, je 40 Orte mit zufaelliger Drehung, jeweils auf dem Tisch, 30 mm und
  60 mm angehoben (nur gerendert, nicht simuliert). Wahrheit ist der Schwerpunkt des Grundrisses aus
  den Quadern des Koerpers.
* **C, Fovea Ende zu Ende:** ihr Kalibrierdetektor (`detect_px`, Farbschwerpunkt) und die Fovea-H,
  fuer die drei Farbkoerper, gleiche Hoehen.
* "Mitte" ist die innere Haelfte des Arbeitsraums (x -110 bis 110 mm, y 70 bis 210 mm), "Rand"
  der Rest.

# Zahlen

**A - Fehler der Umrechnung allein, Median (p90) in mm:**

    Hoehe des Punktes     0     8    12    24    36    50    80 mm
    shape_clf.H  Mitte   7,3   3,3   1,4   6,1  13,5  23,0  47,2
                 Rand    7,8   3,5   1,4   6,4  14,0  24,0  49,4   (Rand p90 bei 12 mm: 2,0)
    Fovea-H      Mitte   6,1   2,1   1,2   7,3  14,8  24,3  48,5
                 Rand    6,4   2,5   2,0   7,2  15,1  25,7  51,6   (Rand p90 bei 12 mm: 3,4, max 5,5)

    shape_clf.H gegen Fovea-H bei 12 mm: Median 1,4, p90 2,7, max 4,3 mm

**B - perceive_all gegen wahren Grundriss-Schwerpunkt (alle acht Koerper, n = 320 je Hoehe):**

    Hub      Mitte Median / p90 / max     Rand Median / p90 / max
    0 mm     0,8 / 1,6 / 3,3              0,8 / 1,7 / 2,9
    30 mm   18,1 / 23,8 / 26,9           18,1 / 28,9 / 32,1
    60 mm   40,7 / 53,7 / 58,2           40,2 / 63,2 / 70,7

Auf dem Tisch je Koerper: X 0,4 mm, Y 0,6-0,7, Wuerfel und Balken 0,7-0,8, L/U/T 1,0-1,8 mm
(Median). Keine Szene ohne Detektion.

**C - Fovea-Weg (Farbschwerpunkt + Fovea-H), Median in mm:** auf dem Tisch 1,1-1,8 (max 4,2);
30 mm angehoben 16-25; 60 mm angehoben 39-54.

# Bewertung

* **Auf dem Tisch ist die Homographie kein Problem.** 0,8 mm Median ist weit unter allem, was
  die Klaue aufloest. Mitte und Rand unterscheiden sich nicht nennenswert. Die Ortsfehler beim
  Greifen kommen nicht von hier (vgl. [Klauenlage und Griffversatz](/befunde/klauenlage-und-griffversatz.md):
  der Versatz entsteht beim Schieben und Reichen).
* **Die Homographie ist eine Ebene in 12 mm Hoehe, nicht der Tisch.** Kalibriert wird mit dem
  Schwerpunkt des 24-mm-Wuerfels, also seiner Mitte. Alle heutigen Koerper sind 24 mm hoch, deshalb
  passt das. Je Millimeter Abweichung kommen rund 0,6 mm Ortsfehler dazu (Kamera schraeg bei
  x -170, y 150 mm, 320 mm hoch; die Richtung des Fehlers ist nicht ausgewertet). Ein 16-mm-Koerper laege damit rund 2-3 mm
  daneben, ein 48-mm-Koerper rund 7 mm. Das erklaert die
  [16 mm am Stapel](/befunde/stapeln-bricht-die-tischebene.md) der Groessenordnung nach.
* **Mit besserer Kalibrierung ist das nicht zu beheben.** Aus einem einzigen Bildpunkt folgt der
  Ort erst, wenn die Hoehe bekannt ist. Jede Umrechnung, auch eine gelernte, braucht deshalb die
  Hoehe als Eingang - oder einen zweiten Blick.
* **Die Fovea-H ist gleich gut, am Rand etwas schlechter** (p90 3,4 gegen 2,0 mm). Sie wird mit
  dem Wuerfel bei z = 8 mm statt 12 mm kalibriert (`set_object`-Vorgabe), er steckt dabei 4 mm im
  Tisch. Ob das den Unterschied erklaert, ist nicht geprueft. Die beiden H weichen im
  Median 1,4 mm voneinander ab.

# Folgen fuer die Abloesung

Die Messlatte fuer einen gelernten Ort ist **rund 1 mm auf dem Tisch** - die heutige Homographie
ist dort kaum zu schlagen. Ein Gewinn ist nur bei der **Hoehe** moeglich. Die eigene Hand liefert
genau solche Etiketten: Bildort und Ort mit Hoehe aus dem Koerpermodell. Eine gelernte Umrechnung
koennte also (Bildpunkt, Hoehe) -> Ort lernen, die Hoehe kaeme fuer Objekte aus dem
[Hoehenschaetzer](/mechanismen/hoehe-ertasten.md). Ob die Hand dafuer oft genug sichtbar ist, ist
noch nicht gemessen.

# Nebenbefund, nicht verfolgt

In 61 von 960 Szenen mit einem einzigen Koerper lieferte perceive_all mehr als eine Detektion. Das
passt zum Erosions-Split, der den Elternfleck neben den Teilen stehen laesst, wenn die Form nicht
aufloest - angehobene Koerper sehen anders aus. Nicht naeher aufgeschluesselt.

# Verwandt

* [perceive_all abloesen](/fragen/perceive-all-abloesen.md)
* [Fovea und Blick](/mechanismen/fovea-und-blick.md)
* [Stapeln bricht die Tischebene](/befunde/stapeln-bricht-die-tischebene.md)
