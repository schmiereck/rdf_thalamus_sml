---
type: Befund
title: Der Arm bindet an den Nachbarn, obwohl die Adressierung stimmt
description: In 6,8 % der Episoden faehrt der Arm die erste Anfahrt mehr als 80 mm neben das kommandierte Objekt - und liefert dann in 1 von 63 Faellen. Die Adressierung ist dabei nachweislich richtig (Median 2 mm, 914/920 eindeutig). Der Fehler sitzt in der Ausfuehrung, nicht in der Wahrnehmung.
tags: [act23, ausfuehrung, wahrnehmung, kommando]
status: stable
evidenz: gemessen
ebene: langlauf
generated: { by: claude/opus-5, at: 2026-09-07T16:00:00Z }
sources:
  - id: lauf932
    resource: log/pc_act23_2026-09-05_22-06-51_5152.txt
    title: GUI-Langlauf, 932 Episoden, ACT23_AUTO_EIG=1
---

# Anlass

Nutzerbeobachtung: *"In `[Auto 810] cube + dick` war der gruene Wuerfel markiert und die Fovea
hat ihn auch fokusiert, er hat aber erst den roten Wuerfel gegriffen. Danach aber, nachdem er den
roten beim Transport verloren hat, den Gruenen angefahren."* - mit der Frage, ob dahinter ein
systematischer Fehler steckt.

# Behauptung

Nein, kein Adressierungsfehler. Das
[Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) hat in genau dieser Episode
dreimal den richtigen Koerper auf 0 mm genau benannt. Der Arm ist trotzdem zum Nachbarn
gefahren. Das ist ein **eigener, haeufiger und teurer Fehlermodus**: 63 von 932 Episoden, und in
62 davon war die Episode danach verloren.

# Zahlen

Episode 810 im Volltext:

    [dbg] obj_green via EIGENSCHAFTEN (None, cube, dick): [-0.065, 0.221]
                                       (wahr [-0.065, 0.221]), 1 Treffer     <- dreimal, 0 mm
    [Glaube] Wahrnehmung 46,5 mm | Zustand 69,0 mm (max 153,0)
             | ERSTE Anfahrt 128,3 mm (386 Schritte) | daneben
    obj_green [-0.065, 0.221]   obj_red [-0.085, 0.092]   -> Abstand 130 mm
    -> NICHT geliefert, Abstand 217 mm

Die erste Anfahrt lag 128,3 mm daneben; der rote Wuerfel stand 130 mm entfernt.

Ueber den ganzen Lauf:

    Adressierung (Kommando gegen wahre Lage des gemeinten Koerpers), n = 920
      Median 2,0 mm | Maximum 32,6 mm | ueber 20 mm nur 36 Faelle
      eindeutig (genau 1 Treffer): 914/920

    Erste Anfahrt > 80 mm daneben:  63 von 932 Episoden = 6,8 %
      davon geliefert:              1 von 63

    Passt der Anfahrfehler zum Abstand eines ANDEREN Objekts (+-25 mm)?
      echt      98 %
      Kontrolle (2000 Permutationen der Fehlerwerte)  75 %  (5.-95. Perz. 68-83 %)

# Bewertung

Die Wahrnehmung ist in diesem Lauf **nicht** der Engpass - sie liefert das Ziel auf 2 mm und in
99,3 % der Faelle eindeutig. Auch die [Blobverschmelzung](/mechanismen/wahrnehmungs-splits.md),
die naheliegendste Erklaerung, scheidet fuer Episode 810 aus: die Detektion sass exakt auf dem
gruenen Wuerfel, nicht zwischen den beiden.

Der Fehler entsteht **nach** der Adressierung, in der Ausfuehrung: der Arm bindet an einen
Nachbarn und arbeitet dort weiter, obwohl das Ziel korrekt vorliegt. Das deckt sich mit dem
alten Befund zur Ablenker-Bindung aus der act21-Linie, ist aber hier zum ersten Mal in act23
quantifiziert.

**Ehrlich zur Guete des Belegs:** die Permutationskontrolle traegt nur schwach. Bei sechs
Nachbarn und +-25 mm Toleranz trifft schon ein **zufaelliger** Fehlerwert in 75 % der Faelle
irgendeinen Nachbarn. Die echten 98 % liegen zwar oberhalb des 95.-Perzentils (83 %), aber das
ist eine Richtungsangabe, kein Nachweis. Der Fehlermodus als solcher - erste Anfahrt gross
daneben, Episode danach verloren - ist dagegen hart: 63 Faelle, 1 Lieferung.

**Was das nicht heisst:** nicht jede der 63 Episoden ist eine Ablenker-Bindung. Ein grober
Anfahrfehler kann auch aus einem Regelfehler stammen. Was gemessen ist: **wenn die erste Anfahrt
mehr als 80 mm danebenliegt, ist die Episode praktisch verloren** - der Lauf holt das nicht mehr
auf, obwohl er in Episode 810 sichtbar korrigiert hat.

# Nachtrag 2026-09-08: bestaetigt und lokalisiert

Die hier noch schwache Vermutung ist direkt gemessen worden. Der Anfahr-Belief sitzt in
gescheiterten Episoden auf einem fremden Koerper (31,2 gegen 4,2 %, Fisher p = 0,0086), und zwar
auf ~4 mm genau - eine sichere Bindung ans falsche Objekt, keine Ungenauigkeit. Die
Permutationskontrolle unten wird damit gegenstandslos. Siehe
[Der Tracker rastet auf dem Nachbarn ein](/befunde/ablenker-bindung-gemessen.md).

# Wo das ansetzt

Das ist rund ein Siebtel aller Fehlschlaege, und es sitzt in einem Pfad, den keine der bisher
gemessenen Massnahmen beruehrt (Griffmechanik, Weltmodell-Merkmale, Klassenkonsolidierung).
Naechster Schritt waere zu klaeren, **welches** Signal in der Anfahrt den Nachbarn gewinnen
laesst, wenn das Ziel korrekt vorliegt - das Latent-Ziel, der Tracker oder die Choreographie.
Ungemessen.

# Verwandt

* [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) - die Adressierung, die hier
  entlastet wird
* [Fovea und Blicksteuerung](/mechanismen/fovea-und-blick.md)
* [Offene Faeden](/fragen/offene-faeden-act23.md)
