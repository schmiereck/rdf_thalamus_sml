---
type: Befund
title: Der Arm stapelt genauso gut, wenn er die Hoehe der Auflage SIEHT statt sie zu wissen
description: Das letzte Privileg auf dem Stapelpfad ist gefallen. Ein A/B aus demselben warmen Zustand, Unterschied allein der Schalter ACT23_HOEHE_SEHEN - Oberkante aus sim.m.geom_size gegen Oberkante aus der eigenen Wahrnehmung. Ergebnis 17 von 20 gegen 15 von 18 Stapeln (85 gegen 83 Prozent, p = 1,00), und der Schaetzfehler im Lauf ist mit 0,7 mm kleiner als auf dem Pruefstand. In allen 31 Episoden lief die Schaetzung, kein einziger Rueckfall auf die Wahrheit. Ehrlich zur Trennschaerfe - erst ein Einbruch auf 50 Prozent waere bei dieser Fallzahl sichtbar geworden.
tags: [act23, stapeln, privileg, wahrnehmung, hoehe]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-20T00:00:00Z }
sources:
  - id: ab
    resource: "Drei kopflose Laeufe nacheinander auf Kopien von act23_state.pkl (ad9d768c), Seed 7001, Teacher fahrend: warm 60 Episoden (der Schaetzer sammelt), dann A und B je 40 Episoden aus DEMSELBEN warmen Zustand. ACT23_SOCKEL=1 ACT23_ZIEL_ADRESSE=1 ACT23_ZIEL_RELATION=auf ACT23_EIG_DIREKT=1 ACT23_EIG_STETIG=1 ACT16_GOAL_Z=1 ACT16_ZIEL_SAEUBERN=0 ACT16_ERFOLG_RUHT=1 ACT23_SOCKEL_WANDERT=1 ACT23_SOCKEL_HOEHEN=6,10,14 ACT23_SCENE_N=3 ACT23_SCENE_EVERY=2 ACT23_ZIEL_MISCH=0.8 ACT23_SELBST_STAPEL=1; Unterschied allein ACT23_HOEHE_SEHEN=0 gegen =1"
    title: Das Stufe-3-A/B
  - id: sonde
    resource: /befunde/hoehe-steckt-in-der-wahrnehmung.md
    title: Die Vorfrage, die diesen Bau erst gerechtfertigt hat
---

# Was hier gefallen ist

`_ziel_aufloesen` rechnete die Ablagehoehe als `GRASP_Z + Oberkante`, und die Oberkante kam aus
`sim.m.geom_size` - eine Designer-Zahl, die der Agent nirgends sehen kann. Sie war das **letzte
Privileg auf dem Stapelpfad**; der Code sagte das selbst.

Jetzt kommt sie aus dem `HoehenSchaetzer`: aus der scheinbaren Flaeche, der Materialdicke und dem
wahrgenommenen Ort **derselben Detektion**, die die Zieladresse ohnehin aufloest. Gelabelt wird
mit dem Privileg - das ist der erlaubte Geruest-Gebrauch nach
[Laufzeitregeln](/mechanismen/laufzeit-regeln.md). Zur Laufzeit ist es weg.

# Das A/B

Beide Arme starten aus **demselben** warmen Zustand (60 Episoden, in denen der Schaetzer seine
Zeilen gesammelt hat), mit demselben Seed. Unterschied ist ein Schalter.

    Arm                          Zieladressen   Stapel-Urteile   liegen drauf
    A  Oberkante aus geom_size        31             20          17 = 85 %
    B  Oberkante aus der Sicht        31             18          15 = 83 %

    Fisher: p = 1,00

**Kein Unterschied.** Der Versatz liegt bei 20 gegen 24 mm.

## Der Schalter hat wirklich gewirkt

Die haeufigste Art, ein solches A/B zu verlieren, ist ein Arm, der stillschweigend doch das
Privileg benutzt. Deshalb steht es in jeder Zeile:

    B:  31 Episoden "BENUTZT",  0 Rueckfaelle auf die Wahrheit
    A:   0 Episoden "BENUTZT"

Und die Klaue faehrt wirklich abgestufte Hoehen an, keine Konstante: 18, 19, 20, 21, 22, 24, 25,
27, 28, 29 mm in B.

# Der Schaetzfehler ist im Lauf KLEINER als auf dem Pruefstand

Die Zeile faellt in beiden Armen, unabhaengig vom Schalter - der Schaetzer rechnet immer mit,
benutzt wird er nur in B. Deshalb vergleichen beide Arme dieselbe Groesse:

    Arm   n    Median    |Fehler| Median    Spanne
    A     30   +0,5 mm      0,9 mm          -4,2 .. +4,6
    B     30   +0,4 mm      0,7 mm          -5,8 .. +6,0

Gegen **1,31 mm** auf dem Pruefstand
([Sonde](/befunde/hoehe-steckt-in-der-wahrnehmung.md)). Das ist kein Widerspruch, sondern ein
anderer Zuschnitt: die Sonde hielt jede Stelle heraus, hier sind fruehere Episoden an derselben
Stelle im Fit. **Die 0,7 mm sind also die guenstigere Zahl** - die uebertragbare steht in der Sonde.

Nach Auflagenhoehe in B, und der alte blinde Fleck ist keiner:

    6 mm:  5 von 7 Stapel,  |Fehler| 0,7 mm
    10 mm: 5 von 6 Stapel,  |Fehler| 0,8 mm
    14 mm: 4 von 4 Stapel,  |Fehler| 1,2 mm

# Was das wert ist - und was nicht

Nach [Projektziel](/ziel.md) zaehlt nicht die Quote, sondern was der Agent selbst kann. Gemessen
ist: **eine Groesse, die er bisher gesagt bekam, holt er sich jetzt aus seinem eigenen Bild, und
die Aufgabe leidet nicht darunter.** Das ist der Ertrag, nicht die 83 %.

Es ist ausdruecklich **kein** Fortschritt in der Leistung, und es war keiner zu erwarten: die
geschaetzte Hoehe kann bestenfalls so gut sein wie die wahre.

# Fallen

* **`p = 1,00` heisst nicht "gleich".** Bei 20 gegen 18 Urteilen waere erst ein **Einbruch auf
  9 von 18 (50 %)** signifikant geworden (p = 0,035). Alles zwischen 50 und 85 % haette diese
  Messung nicht von "kein Unterschied" unterscheiden koennen. Der Satz, der hier traegt, ist:
  *kein Verlust, der bei dieser Fallzahl sichtbar waere.*
* **Das Geruest hat ihn trainiert.** Der Schaetzer lernt aus dem Privileg. Zur Testzeit ist es
  aus dem Pfad, im Training nicht - und ein Agent, der nie einen privilegierten Lauf gesehen
  haette, haette diesen Schaetzer nicht. Die Hoehe aus dem **Ausgang** zu lernen (ein Stapel haelt
  oder nicht) ist die naechste, haertere Stufe und ist nicht gemessen.
* **Der Grundriss ist fest - und das ist die harte Grenze dieses Befundes.** Alle Auflagen sind
  70 x 70 mm. **GEMESSEN am selben Tag: die Bewaehrungsprobe faellt durch**
  ([Die zweite Auflage bricht den Hoehenschaetzer](/befunde/zweiter-grundriss-bricht-die-hoehe.md)).
  Dieser Schaetzer liest eine 50-mm-Platte um 6,0 mm zu niedrig, und auch einer, der beide
  Grundrisse gesehen hat, faellt auf die Grundrate. **Alles auf dieser Seite gilt damit fuer eine
  Welt mit EINER Auflagenform.** Der Ausweg steht dort: ein Schaetzer je adressierter Auflage.
* **Das Lerntor ist entschieden, nicht gemessen.** Von 46 Gelegenheiten im warmen Lauf sind 14
  verworfen worden, weil die Auflage belegt aussah (Farbstreuung ueber der Einzelfleck-Skala).
  Streng gegen lax ist ein eigenes A/B, das nicht gelaufen ist; die Begruendung fuer streng ist,
  dass ein verschmolzener Blob genau das Merkmal angreift, das die Hoehe traegt.
* **32 Zeilen, nicht 90.** Der Schaetzer im Lauf ist duenner besetzt als der der Sonde. Dass er
  trotzdem auf 0,7 mm kommt, spricht fuer die Staerke des Signals, nicht fuer die Datenmenge.

# Verwandt

* [Die Hoehe steckt in der Wahrnehmung](/befunde/hoehe-steckt-in-der-wahrnehmung.md) - die Vorfrage, auf dem Pruefstand
* [Die Relation "auf" gebaut](/mechanismen/relation-auf-gebaut.md) - wo die Oberkante herkam, und der fuenfte Pflichtschalter
* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) - warum ein Geruest fallen muss
* [Die Policy lernt die Hoehe als Ort](/befunde/policy-lernt-hoehe-als-ort.md) - was die Policy mit der Hoehe tut
* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - Stufe 3
* [Der Stapel-Selbstrichter](/befunde/selbstrichter-stapel.md) - woher die Einzelfleck-Skala des Lerntors kommt
