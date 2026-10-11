---
type: Befund
title: Eine Welt, in der schraeges Greifen am Balken schadet - nicht gefunden, die Klaue richtet den Balken selbst aus
description: Pruefstand mit erzwungener Klauenlage (quer 90 gegen schraeg 45 Grad) in acht Balken-Welten. Breiter (21/23 mm), schwerer oder glatter Balken - schraeg liefert so gut wie quer, weil die schliessende Klaue den Balken eindreht. Schwer UND griffig verhindert das Eindrehen (0 Grad), laesst dann aber auch quer kaum noch heben (48 g 3/12 gegen 3/12, 97 g und 194 g 0). Eine Welt mit Gefaelle zwischen quer und schraeg gibt es mit Balkeneigenschaften allein nicht; der naechste Hebel waere die Klaue selbst.
tags: [act23, wrist, welt, balken, pruefstand, selbstlernen]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-10-11T23:00:00Z }
sources:
  - id: sweep
    resource: "Kopflose GUI-Steuerung, Seed 9511, je 12 Episoden, ACT23_AUTO_OBJ=obj_blue ACT23_SZENE_MIT=obj_blue ACT23_FORCE_WRIST=rel:90|rel:45, Kopie des Hauptzustands, NO_PERSIST; Schalter ACT23_BALKEN_BREITE/MASSE/REIBUNG"
    title: Pruefstand Balken-Welt
  - id: anlass
    resource: /befunde/klauenlage-und-griffversatz.md
    title: Klauenlage am Balken (Anlass)
---

# Anlass

Nutzerauftrag 2026-10-11: *"Baue eine Welt, in der schraeges Greifen am Balken schadet."* Folge aus
[Klauenlage und Griffversatz](/befunde/klauenlage-und-griffversatz.md): der Agent greift den Balken
im Median 65 statt 90 Grad, weil schraeg in der Standardwelt nichts kostet - also lernt das
Weltmodell keine Querlage. Erst eine Welt, in der schraeg scheitert, gaebe ihm Gegenbeispiele.

Vor dem Lernlauf die Vorfrage am Pruefstand: **gibt es eine Welt, in der erzwungen quer gut und
erzwungen schraeg schlecht liefert?** (Pruefstand reicht hier: gefragt ist eine Eigenschaft der
Welt, nicht eine Wirkung auf act23.)

# Gebaut (alle Vorgabe aus, zeichengleich)

* `ACT23_BALKEN_BREITE` (mm, Vorgabe 18), `ACT23_BALKEN_MASSE` (Faktor), `ACT23_BALKEN_REIBUNG`
  (setzt zusaetzlich `geom_priority`, sonst nimmt MuJoCo das Maximum mit Klaue und Tisch, je 1,0, und
  ein kleinerer Wert waere wirkungslos). Weltschalter, keine Laufzeitregel.
* `ACT23_SZENE_MIT=<koerper>`: der Koerper steht immer auf dem Tisch - behebt die Messfalle aus dem
  Balkenlauf (Rotation parkte den kommandierten Balken, 26 von 60 "nicht gefunden").
* `ACT23_FORCE_WRIST=rel:<Grad>`: Finger-Trennachse in diesem Winkel zur wahren Laengsachse
  (privilegierter Messknopf, nur Zustandskopien).

# Zahlen (je Arm 12 Episoden, Balken immer auf dem Tisch)

    Welt                          quer 90         schraeg 45      Winkel beim Zufassen (45er Arm)   Drehung beim Schliessen
                                  geliefert       geliefert
    Standard 18 mm, 10 g            8               8             45-59
    breit 21 mm                     6               5             45-81
    sehr breit 23 mm                7               7             46-62
    5x schwer, glatt (0,4)          9               8             53-76  (dreht sich LEICHTER ein)
    5x schwer, griffig (2,0)        3               3             44-46                              ~0 Grad
    10x schwer, griffig             0 / 10          0 / 10        43-46   (Lauf bei 10 Ep abgebrochen)  ~0 Grad
    20x schwer, griffig 18 mm       0               0             44-46                              0 Grad
    20x schwer, griffig 21 mm       0               0             44-46                              0 Grad

(Die 10x-Arme wurden vom System wegen Speichermangel nach 10 Episoden beendet; nicht neu gestartet.)

# Bewertung

**Die Klaue richtet den Balken selbst aus.** Solange der Balken sich auf dem Tisch drehen kann,
dreht die schliessende Klaue ihn Richtung quer - auch 23 mm breit (die Backen oeffnen innen rund
24 mm) und auch 5-fach schwer. Ein glatter Balken dreht sich sogar leichter ein. Damit liefert
schraeg so gut wie quer.

**Wird das Eindrehen verhindert, scheitert alles.** Schwer und griffig haelt den Balken fest
(Drehung 0 Grad), aber dann liefert auch quer nicht mehr (3/12, 0/10, 0/12) - Quer und schraeg
fallen gemeinsam. Warum der griffige 48-g-Balken auch quer kaum gehoben wird (glatt bei gleicher
Masse 9/12), ist nicht untersucht.

**Ehrliches Negativ:** Ueber Breite, Masse und Reibung des Balkens entsteht kein Gefaelle zwischen
quer und schraeg. Das bestaetigt die alte Lesart "der Wrist ist in dieser selbstausrichtenden
Simulation nicht der Lieferhebel" und erklaert, warum das Weltmodell am Balken keine Querlage lernt:
es gibt in dieser Physik keine Gegenbeispiele.

**Offen:** ein Eingriff an der KLAUE (schmalere Oeffnung, kuerzere Backen) statt am Balken. Das ist
eine Aenderung am Greifer und betrifft alle Objekte; nicht ohne Nutzerentscheid. Zwischenwerte der
Reibung (z. B. 1,6-1,8 bei 10-20 g) sind nicht gemessen.

# Verwandt

* [Klauenlage und Griffversatz](/befunde/klauenlage-und-griffversatz.md) - der Anlass
* [Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md) - Ausrichtung als lernbare Policy, wo sie wirkt
* [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)
