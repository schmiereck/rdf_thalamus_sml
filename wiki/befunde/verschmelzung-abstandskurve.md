---
type: Befund
title: Ab welchem Abstand der Split versagt - die Kurve
description: Verschmelzung reicht bis rund 75 mm Mittenabstand und beherrscht alles unter 35 mm. Der FARB-Split rettet ab 35 mm zuverlaessig (100 Prozent), bei 25 mm nur noch in 72 Prozent, bei 15 mm in 29. Die FORMKLASSE ueberlebt die Rettung viel schlechter als die Position. Ein Paar verschmilzt ueberhaupt nicht.
tags: [act23, wahrnehmung, split, verschmelzung]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-09T20:00:00Z }
sources:
  - id: probe
    resource: "src/pc_cvnn/act23_fusion_probe.py, 4 Koerperpaare x 9 Abstaende x 24 Lagen = 864 Konstellationen, Zustandskopie 98a293f2, RES=240"
    title: Verschmelzungs-Abstandsprobe
---

# Anlass

Seit August offen ([offene Faeden](/fragen/offene-faeden-act23.md)) und seither **dreimal** als
Ursache aufgetaucht: beim [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md)
("Eindeutigkeit ist nicht Richtigkeit" - zwei Koerper in ~50 mm ergaben EINE Detektion auf der
Mitte), bei der [Ablenker-Bindung](/befunde/ablenker-bindung-gemessen.md) und beim
[Rueckfall-Keim](/befunde/keim-im-rueckfall.md), wo der gewaehlte Blob bei 21 gegen 23 mm fast
genau zwischen zwei Koerpern sass.

# Behauptung

Die Grenze ist jetzt beziffert. **Verschmelzung reicht bis rund 75 mm Mittenabstand** und
beherrscht alles unter 35 mm. Der **Farb-Split rettet ab 35 mm ausnahmslos**, faellt bei 25 mm
auf 72 % und bei 15 mm auf 29 %. Die **Formklasse** ueberlebt die Rettung deutlich schlechter als
die Position.

# Zahlen

Drei verschmelzende Paare zusammengefasst (obj_red/obj_L, obj_T/obj_U, obj_L/obj_U), je 24 Lagen
und Drehungen pro Abstand:[^probe]

    d [mm]   verschmolzen        Farb-Split rettet     Formklasse erkannt
       15    59/72 = 81,9 %      17/59 =  28,8 %        8/59 = 13,6 %
       25    47/72 = 65,3 %      34/47 =  72,3 %        7/47 = 14,9 %
       35    33/72 = 45,8 %      33/33 = 100,0 %       14/33 = 42,4 %
       45    18/72 = 25,0 %      18/18 = 100,0 %       13/18 = 72,2 %
       55    13/72 = 18,1 %      13/13 = 100,0 %       10/13 = 76,9 %
       65     8/72 = 11,1 %       8/8  = 100,0 %        8/8  = 100,0 %
       75     3/72 =  4,2 %       3/3  = 100,0 %        2/3  =  66,7 %
       85     0/72 =  0,0 %        --                    --
       95     0/72 =  0,0 %        --                    --

    Lokalisierungsfehler (Median): unverschmolzen 1-6 mm, nach Farb-Split 5-12 mm

**"Verschmolzen"** heisst hier: `perceive_all` liefert **keine** Detektion, die naeher am
Zielkoerper liegt als die halbe Luecke. Das Kriterium ist absichtlich abstandsrelativ - bei 15 mm
Luecke waeren 10 mm Fehler eine Verwechslung, bei 90 mm nicht.

# Das vierte Paar verschmilzt nie

    obj_X neben obj_green    0/24 verschmolzen bei JEDEM Abstand von 15 bis 95 mm

Verschmelzung ist also **nicht** allein eine Frage des Abstands, sondern des Paares - Farbabstand
und Geometrie entscheiden mit. Wer die Kurve oben als allgemeingueltig liest, liest sie falsch.
Der Befund entwertet die Kurve nicht, er begrenzt sie: sie gilt fuer Paare, die ueberhaupt
verschmelzen koennen.

# Der wunde Punkt: die Formklasse

Der Farb-Split rettet ab 35 mm die **Position** zu 100 %, die **Formklasse** aber nur zu 42 %,
und erst ab 65 mm zuverlaessig. Das trifft das
[Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) an seiner Formachse und den
`shape`-Pfad direkt: wer ueber die Form adressiert, verliert sein Ziel in einem Bereich, in dem
der Farbpfad laengst wieder traegt. Es deckt sich mit der aelteren Einzelmessung an obj_T
(8,8 % erkannt bei Verschmelzung, 81 % nach dem Form-Split) und erklaert, warum die
Form-Rettung dort noetig war.

# Was die kleinen Abstaende NICHT hergeben

`mj_forward` loest keine Durchdringung auf - der eingestellte Abstand ist exakt der realisierte
(geprueft: 15 -> 15,0 mm). Bei kleinen d **durchdringen** sich die Koerper deshalb, und solche
Szenen kann ein echter Lauf nicht erzeugen. Der kleinste beruehrende Mittenabstand haengt von der
Drehung ab:

    obj_red + obj_L     19..40 mm        obj_T + obj_U      13..35 mm
    obj_L  + obj_U      14..42 mm        obj_X + obj_green  18..33 mm

**Die 15-mm-Zeile ist damit ueberwiegend unphysikalisch** und sagt etwas ueber die Segmentierung,
nichts ueber erreichbare Szenen. Der physikalisch belastbare Bereich beginnt bei ~25 mm - und
genau dort steht der Split bei 72 %, nicht bei 100 %.

# Bewertung

* **Die praktische Grenze liegt bei 25-35 mm.** Darueber traegt der Farb-Split die Position
  vollstaendig, darunter wird er unzuverlaessig - und darunter faengt der physikalisch moegliche
  Bereich gerade erst an.
* **Verschmelzung ist haeufiger als erwartet.** Noch bei 55 mm verschmelzen 18 % der
  Konstellationen, bei 65 mm 11 %. Die frueher genannte Hausnummer "~40-50 mm" war zu optimistisch.
* **Position und Identitaet sind zwei verschiedene Rettungen.** Die Position kommt ab 35 mm
  sicher zurueck, die Klasse nicht. Fuer eine Adressierung ueber die Form ist die Grenze also
  deutlich weiter draussen als fuer eine ueber die Farbe.

**Was das ausdruecklich NICHT ist:** eine Aussage darueber, wie oft das im Lauf passiert oder was
es dort kostet. Das ist eine isolierte Wahrnehmungsprobe
([Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)); die Haeufigkeit im Lauf haengt daran, wie
`randomize_objects` die Koerper verteilt, und ist hier **nicht** gemessen.

# Aufbau

`src/pc_cvnn/act23_fusion_probe.py` - zwei Koerper in kontrolliertem Mittenabstand, alles andere
geparkt, kein Lauf und kein Lernen. Farb- und Formklasse werden **empirisch** bestimmt (Koerper
allein hinstellen und die Wahrnehmung fragen), nicht aus `shape_key` gelesen - dort stehen nur die
selbst geborenen Klassen, die trainierten Formen L und U fehlen.

    FUS_STATE=<Kopie> FUS_N=24 FUS_DMIN=15 FUS_DMAX=95 FUS_DSTEP=10 \
    FUS_PAARE="obj_red:obj_L,obj_T:obj_U,obj_X:obj_green,obj_L:obj_U" \
    ACT14_DOF=4 .venv/Scripts/python.exe src/pc_cvnn/act23_fusion_probe.py

RES bleibt 240 - die Homographie haengt daran.

# Verwandt

* [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md) - der Mechanismus, hier vermessen
* [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) - "Eindeutigkeit ist nicht Richtigkeit"
* [Keim im Rueckfall](/befunde/keim-im-rueckfall.md) - der dritte Fall, der hierher fuehrte
* [Die Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)
