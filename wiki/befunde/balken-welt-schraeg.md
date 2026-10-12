---
type: Befund
title: Eine Welt, in der schraeges Greifen am Balken schadet - nicht gefunden, die Klaue richtet den Balken selbst aus
description: Pruefstand mit erzwungener Klauenlage (quer 90 gegen schraeg 45 Grad) in acht Balken-Welten. Breiter (21/23 mm), schwerer oder glatter Balken - schraeg liefert so gut wie quer, weil die schliessende Klaue den Balken eindreht. Schwer UND griffig verhindert das Eindrehen (0 Grad), laesst dann aber auch quer kaum noch heben (48 g 3/12 gegen 3/12, 97 g und 194 g 0). Eine Welt mit Gefaelle zwischen quer und schraeg gibt es mit Balkeneigenschaften allein nicht. NACHTRAG: auch eine schmaler oeffnende Klaue (44/37/34 statt 56 mm) und feiner gestufte Reibung/Masse erzeugen keins (gepoolt Klaue 17/36 gegen 13/36, p = 0,47) - und schraeg haelt dort OHNE Eindrehen (Median 1 Grad). NACHTRAG 2: auch ein langer schmaler Balken (100/130 mm lang, 12/18 mm breit, auch mit Klaue bis 37 mm) gibt keins (quer 21/48 gegen schraeg 22/48).
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
dreht die schliessende Klaue ihn Richtung quer - auch 23 mm breit (~~die Backen oeffnen innen rund
24 mm~~ **BERICHTIGT 2026-10-11:** die Naegel stehen offen 56 mm auseinander, 26 mm erst an der
Schliessschwelle 0,27 - es war reichlich Platz) und auch 5-fach schwer. Ein glatter Balken dreht sich sogar leichter ein. Damit liefert
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

# Nachtrag 2026-10-11: Klaue schmaler, Reibung und Masse feiner

Nutzerauftrag: *"Mache Klaue etwas schmaler oeffnen und Reibung und Gewicht feiner abstufen."*

**Gebaut:** `ACT23_KLAUE_OFFEN_MAX=<joint_5>` - ein Anschlag am Greifermotor (`actuator_ctrlrange`
von m5). Das Netz befiehlt weiter, was es will; die Klaue kommt nur nicht weiter auf. Weltschalter,
keine Regel. Nicht unter 0,31 setzen: das Loslassen zaehlt erst ab `J5_OPEN_TH` = 0,30 als offen.
Nebenwirkung nur im Log: die `[Schub]`-Marke "schliesst" (j5 < 0,8 x 0,54) liegt dann schon im Anflug.

**Lichte Weite der Klaue** (gemessen mit `mj_geomDistance`, Ruhelage nach 1500 Schritten):

    joint_5          0,54   0,50   0,46   0,42   0,38   0,34   0,30   0,27
    Naegel  (mm)       56     52     48     44     39     35     30     26
    Endstuecke (mm)    53     49     46     42     39     35     31     29

Grob ueberschlagen braucht ein 18-mm-Balken unter 45 Grad mit ~12 mm breiten Backen rund
18/sin45 + 12/tan45 = 37 mm, quer nur 18 mm.

**Zahlen** (gleicher Aufbau wie oben: Seed 9511, je 12 Episoden, Balken immer auf dem Tisch, Kopie
des Hauptzustands, NO_PERSIST; je Paar zwei Prozesse gleichzeitig):

    Welt                                   quer 90   schraeg 45   |Drehung beim Schliessen| 45er Arm   Lage beim Zufassen (45er)
    Klaue bis 0,42 (44 mm)                  7          5           Median 2, max 18                  45-62
    Klaue bis 0,36 (37 mm)                  5          4           Median 1, max 10                  44-54
    Klaue bis 0,33 (34 mm)                  5          4           Median 1, max 5                   44-50
    10 g, Reibung 1,7                       7          6           Median 1, max 12                  45-57
    10 g, Reibung 2,0                       4          6           Median 0, max 7                   45-52
    19 g, Reibung 1,7                       5          6           Median 1, max 9                   44-54
    19 g, Reibung 2,0                       4          5           Median 1, max 3                   45-48
    29 g, Reibung 2,0                       4          4           Median 1, max 3                   45-47

Klaue gepoolt quer 17/36 gegen schraeg 13/36, Fisher p = 0,47. Kein einzelner Vergleich auch nur
in der Naehe (Bonferroni ueber 8 Welten: Schranke 0,006). Die Fehlerarten (Griff am Objekt
fehlgeschlagen / hielt nicht / daneben platziert) sind in beiden Armen gleich verteilt.

**Bewertung:**

* **Kein Gefaelle, auch nicht mit schmaler Klaue.** Bei 34 mm Oeffnung - unter der Ueberschlags-
  grenze von 37 mm fuer 45 Grad - greift die Klaue schraeg so gut wie quer.
* **Die obige Erklaerung "die Klaue dreht den Balken ein" ist unvollstaendig.** Mit schmaler Klaue
  und mit griffigem Balken dreht er sich beim Schliessen kaum noch (Median 0-1 Grad, Lage beim
  Zufassen 44-50), und schraeg liefert trotzdem 4-6 von 12. **Ein 45-Grad-Griff haelt an diesem
  Balken von sich aus.** Das Eindrehen ist ein Begleiteffekt, nicht der Grund, warum schraeg nichts
  kostet. Der Ueberschlag mit 37 mm unterschaetzt offenbar, wie weit die Naegel (Neigung, sie
  greifen unterhalb der Oberkante) einen schraegen Balken umfassen.
* **Die feinen Stufen fuellen die Luecke nicht.** Zwischen "dreht ein, liefert" und "schwer und
  griffig, liefert gar nicht" (frueher 48 g) gibt es bei 10-29 g und Reibung 1,7-2,0 keine Zone,
  in der nur schraeg scheitert. Quer liegt hier bei 4-7 von 12 - unter den frueheren 8 der
  Standardwelt, einzeln nicht signifikant (z. B. 4/12 gegen 8/12, p = 0,22; andere Laeufe,
  anderer Commit).

**Ehrliches Negativ, jetzt ueber Balken UND Klaue:** in dieser Physik kostet ein 45-Grad-Griff am
Balken nichts. Damit gibt es fuer das Weltmodell keine Gegenbeispiele, aus denen es "quer" lernen
koennte - und es gibt auch keinen Grund, warum es das sollte. Ein weiterer Kandidat waere ein
deutlich LAENGERER oder schmalerer Balken (bei 45 Grad greift die Klaue dann eher eine Kante);
nicht gemessen.

# Nachtrag 2 (2026-10-11): langer schmaler Balken

Nutzerauftrag: *"Teste den langen schmalen Balken."*

**Gebaut:** `ACT23_BALKEN_LAENGE=<mm>` (Vorgabe 68). Masse und Traegheit bleiben die des 9,7-g-Wuerfels,
wie schon bei der Breite.

**Nebenbefund, Welt-Fehler:** obj_blue ist im Modell ein 24-mm-Wuerfel und wird erst zur Laufzeit auf
Balkenmass gestreckt (`geom_size`); `geom_rbound` (21 mm) und `geom_aabb` bleiben dabei auf dem Wuerfel.
Probe: Wuerfel 6 mm ueberlappend am Ende eines 120-mm-Balkens -> **0 Kontakte** (mit nachgefuehrter Huelle
4, der Wuerfel wird weggedrueckt). Mit `ACT23_BALKEN_LAENGE` wird die Huelle nachgefuehrt. **Die Vorgabewelt
ist unveraendert**: nach Rechnung (Huellradien 21 + ~9 mm) sind die aeusseren ~4 mm des 68-mm-Balkens fuer
die Klauennaegel unsichtbar (**BERICHTIGT 2026-10-12: gemessen rund 8 mm je Ende**, s. [Huellenkorrektur](/befunde/huellenkorrektur-ab.md)) - fuer Griffe nahe der Mitte belanglos, nicht am Arm gemessen. Beheben waere
eine Aenderung der Vorgabephysik (Nutzerentscheid).

**BEHOBEN 2026-10-11 (Nutzerauftrag "Behebe den Huellenfehler auch in der Standardwelt"):**
`BracketArmSim.huelle_nachfuehren(g)` (pc_act14) setzt `geom_rbound` und `geom_aabb` eines Quaders aus
seinem `geom_size`; `set_object_size` ruft es immer, act23 ruft es fuer den Balken und an den beiden
Hoehen-Stellen (Sockel, Formhoehen), die bisher nur `geom_rbound` nachfuehrten. Gemessen: **beide Felder
sind noetig** - nur rbound oder nur aabb nachgefuehrt gibt weiter 0 Kontakte. In der Vorgabewelt bekommt
ein nagelgrosser Wuerfel, der 2 mm in das Ende des 68-mm-Balkens ragt, jetzt 4 statt 0 Kontakte. Rauchtest
act23 (3 Ep, Wuerfel/Balken/L) laeuft und liefert. **Alle Balken-Zahlen oben stammen noch aus der Welt mit
alter Huelle** (Ausnahme: die LAENGE-Zeilen). Eine Wirkung auf act23 ist nicht gemessen (kein A/B). NACHTRAG 2026-10-12: gemessen, neutral - [Huellenkorrektur: act23-A/B](/befunde/huellenkorrektur-ab.md).

**Zahlen** (gleicher Aufbau, je 12 Episoden):

    Welt                                   quer 90   schraeg 45   |Drehung beim Schliessen| 45er   Lage beim Zufassen (45er)
    100 x 12 mm                             6          6           Median 1, max 5                44-49
    130 x 12 mm                             4          6           Median 0, max 4                44-49
    130 x 18 mm                             7          7           Median 0, max 16               44-60
    130 x 12 mm, Klaue bis 0,36 (37 mm)     4          3           Median 0, max 1                44-46

Gepoolt quer 21/48 gegen schraeg 22/48. Kein Vergleich auch nur in der Naehe einer Signifikanz.
Fehlerarten in beiden Armen gemischt (nicht gegriffen / Griff am Objekt fehlgeschlagen / hielt nicht /
daneben platziert), keine Art haeuft sich im 45er Arm.

**Bewertung:** Auch Laenge und Schmalheit erzeugen kein Gefaelle. Der Balken dreht sich beim Schliessen
nicht (Median 0 Grad), der 45-Grad-Griff haelt ihn trotzdem so gut wie der quere. Damit ist die
Balken-Welt ueber Breite, Laenge, Masse, Reibung und Klauenoeffnung abgesucht: **in dieser Physik kostet
ein schraeger Griff am Balken nichts.** Meine Vermutung, ein langer schmaler Balken lasse die Klaue bei
45 Grad nur eine Kante fassen, ist widerlegt.

# Verwandt

* [Klauenlage und Griffversatz](/befunde/klauenlage-und-griffversatz.md) - der Anlass
* [Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md) - Ausrichtung als lernbare Policy, wo sie wirkt
* [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)
