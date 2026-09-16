---
type: Befund
title: Das Wrist-Gitter kostet nichts - seine LAGE ist 2,3-mal wichtiger als seine Dichte
description: Die vierte diskretisierte Achse, offline am gelernten Weltmodell geprueft. Von 8 auf 16 Gitterpunkte zu gehen bringt exakt null; echte Gewinne beginnen erst unter 4 Grad Schrittweite und saettigen bei 0,023 Guete, wovon die Haelfte Rausch-Jagd ist. Dieselben 8 Punkte nur um eine halbe Stufe zu VERSCHIEBEN kostet dagegen 0,106 - 2,3-mal so viel, wie die feinste Verfeinerung bringt. Anders als Farbe, Form und Groesse ist der Wrist kein Diskretisierungsproblem, weil sein Gitter an der Objektachse verankert ist.
tags: [act23, weltmodell, greifen, methodik]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-16T00:00:00Z }
sources:
  - id: sonde
    resource: "Offline am Weltmodell aus act23_state.pkl (ad9d768c): 60 echte Puffersituationen, je 720 Wrist-Winkel, LCB = mu - sigma"
    title: Dosis-Wirkung des Wrist-Gitters
  - id: anlass
    resource: /mechanismen/act23-modullandschaft.md
    title: Der Wrist als vierte diskretisierte Achse
---

# Die Frage

Farbe, Form und Groesse werden diskretisiert, und diese Woche stellte sich das als gemeinsame
Ursache eines ganzen Arbeitstags heraus ([Frage](/fragen/stetige-adressierung.md)). Der Wrist ist
die **vierte** solche Achse: er wird ueber `wrist_grid=8` Punkte auf pi gewaehlt, also in
22,5-Grad-Stufen, und per Ensemble-Argmax gescort. Der Code nennt sie selbst beim Namen
(*"Die Stufung ist eine DISKRETISIERUNG wie TILT_OFFSETS und wrist_grid"*), gemessen war sie nie.

**Kostet die Stufung etwas?** Offline beantwortbar: fuer echte Situationen aus dem Puffer erst die
Wahl treffen, die der Agent trifft, dann mit festem Griff und fester Neigung den Winkel fein
durchfahren.

# Zahlen

    Gitter       Stufe  |  ROH: Gewinn gegen 8    mm  |  GEGLAETTET     mm
         8      22,50d  |              0,0000         |      0,0000
        16      11,25d  |              0,0000         |      0,0000
        48       3,75d  |              0,0134    2,9  |      0,0153    3,1
       144       1,25d  |              0,0398    5,0  |      0,0230    3,8
       720       0,25d  |              0,0462    5,4  |      0,0230    3,8
    8 verschoben 22,50d |             -0,1057

    (gepaarte Mediane ueber 60 Situationen; Gitter geschachtelt, jedes feinere ENTHAELT das 8er)

**Von 8 auf 16 Punkte zu gehen bringt exakt null.** In ueber der Haelfte der Situationen findet das
doppelt so feine Gitter denselben Optimalwert - die zusaetzlichen Punkte schlagen die vorhandenen
nicht.

Echte Gewinne beginnen erst unter **4 Grad** Schrittweite und saettigen bei +0,023 Guete, also rund
**3,8 mm** aequivalenter Ablagedistanz - bei einer Toleranz von 25 mm.

# Die Kontrolle, ohne die das ein Fehlschluss waere

**Das Maximum ueber 720 Punkte uebertrifft das ueber 8 auch dann, wenn die Kurve reines Rauschen
ist.** Das ist Maximierungs-Verzerrung, kein Befund. Zwei Gegenproben:

* **Glaettung.** Dieselbe Reihe auf der ueber eine halbe Gitterstufe gemittelten Kurve: der Gewinn
  8 -> 720 faellt von +0,0462 auf +0,0230. **Die Haelfte des Verfeinerungsgewinns ist Rausch-Jagd.**
  Dazu passt die gemessene Rauheit: 23 % der Kurvenvariation ueberleben die Glaettung (p90 32 %),
  die Kurve ist also nicht glatt.
* **Verschiebung.** Dieselben 8 Punkte, nur um eine halbe Stufe versetzt: **-0,1057**. Das ist
  **2,3-mal so viel, wie die feinste Verfeinerung bringt** - und zwar mit umgekehrtem Vorzeichen.

> **Die LAGE des Gitters ist 2,3-mal wichtiger als seine DICHTE.**

# Warum das so ist - und warum es schon gebaut war

Das Gitter wird um die wahrgenommene Objektachse aufgespannt (`ACT23_WRIST_REL`, Vorgabe an), nicht
um den Weltrahmen. Damit liegen zwei Gitterpunkte **exakt parallel und exakt senkrecht** zur
Objektachse - und genau dort sitzt der Wert: ausgerichtete Griffe liefern gemessen 35 % gegen 17 %
fuer diagonale (p = 0,015). Ein um 11,25 Grad verschobenes Gitter verliert beide Ausrichtungen,
und das kostet mehr, als 90 zusaetzliche Zwischenwinkel je einbringen koennten.

Diese Messung bestaetigt `WRIST_REL` damit unabhaengig und von der anderen Seite: nicht ueber die
Lieferquote, sondern ueber die Frage, was eine Verschiebung kostet.

# Antwort auf die gestellte Frage

**Der Wrist ist NICHT die vierte Problemachse.** Die Vermutung, die diese Messung ausgeloest hat,
ist damit widerlegt: anders als bei Farbe, Form und Groesse kostet die Stufung hier (fast) nichts,
weil das Gitter dort verankert ist, wo die Struktur sitzt.

**Ein feineres Gitter ist nicht zu rechtfertigen.** 8 -> 16 ist null; 8 -> 144 waere 18-mal so
viele Kandidatenbewertungen je Episode fuer 3,8 mm aequivalent, von denen die Haelfte des rohen
Effekts ohnehin Rauschen war. **Ein act23-Lauf dazu eruebrigt sich** - das ist der Zweck dieser
Offline-Pruefung: sie hat ein A/B von zwei Stunden gespart und die Antwort ist ein sauberes Nein.

# Fallen

* **`ebene: pruefstand`.** Gemessen wird die MEINUNG DES MODELLS ueber die Guete, nicht das
  Ergebnis. Das Modell kann glatt und trotzdem falsch sein. Der Schluss traegt nur in EINE
  Richtung: findet das Modell selbst zwischen den Gitterpunkten nichts, kann ein feineres Gitter
  ihm nichts zu waehlen geben - denn die Wahl trifft das Modell.
* **60 Situationen, nach Zeit mit Luecke gezogen** (jede 205. Pufferzeile), nicht zufaellig -
  benachbarte Zeilen sind Beinah-Duplikate derselben stehenden Szene.
* **Griff und Neigung bleiben fest** auf der Wahl des groben Gitters. Ob eine feinere
  Wrist-Wahl in Kombination mit einem anderen Griff mehr braechte, ist nicht gemessen.
* **Erste Fassung der Reihe war fehlerhaft** und ist hier korrigiert: 32/64/128 teilen 720 nicht
  so, dass sie die 8 Punkte enthalten - die Reihe verglich verschiedene Punktmengen statt einer
  Verfeinerung, und 32 kam unter 16 heraus. Jetzt sind die Schrittweiten 90/45/15/5/1.
* **`lam = 1,0`** wie in `select_action`; mit einem anderen Vertrauensabschlag verschiebt sich das
  Optimum, die Reihe ist nicht durchgefahren.

# Verwandt

* [Modullandschaft](/mechanismen/act23-modullandschaft.md) - wo der Wrist sitzt und was an ihm gebaut ist
* [Stetig adressieren statt Klassen vergeben](/fragen/stetige-adressierung.md) - dieselbe Frage an die drei anderen Achsen, dort mit anderem Ausgang
* [Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md) - die Ausrichtungsmessung, die die Verankerung begruendet
* [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) - warum hier kein act23-Effekt behauptet wird
