---
type: Befund
title: Fuenfter Anlauf zur Groessen-Invarianz - Ringe an der Eigenausdehnung halbieren die Kennzahl
description: Die vier bisherigen Normierungen normieren Amplituden oder skalieren Radien global und bewegen im selben Aufbau nichts (3,87 bis 4,78 gegen 4,00 Ausgangswert). Ringe, die an der Eigenausdehnung des Objekts haengen, kommen auf 1,94 bis 2,48 - eine Halbierung, ueber drei Seeds stabil. Das Ziel unter 1,0 ist damit trotzdem nicht erreicht, und der Einbau entwertet den gesamten gelernten Klassenbestand.
tags: [act23, wahrnehmung, formklassen, generalisierung]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-12T20:00:00Z }
sources:
  - id: probe
    resource: "src/pc_cvnn/act23_groessen_invarianz.py, 3 Formen x 3 Groessen x 10 Lagen, drei Seeds (5/23/41), Zustandskopie ad9d768c"
    title: Groessen-Invarianz-Pruefstand
  - id: vorher
    resource: /befunde/formfaktorisierung.md
    title: Die vier gescheiterten Anlaeufe
---

# Der Ansatz

Aus [Formfaktorisierung](/befunde/formfaktorisierung.md) stammt die Diagnose, warum die vier
bisherigen Versuche scheiterten: *"ein groesserer Arm fuellt mehr Kreisumfang JE RING, und das
ueberlebt jede Radien- oder Amplitudennormierung."*

Genau darin liegt der Hebel, den alle vier verfehlt haben. Sie normieren **Amplituden** (DC-Anteil,
Gesamtfuellung) oder skalieren die Radien **global** (an der Dicke). Die Ringe liegen aber weiter
an festen Weltradien (`RW` = 4..46 mm) - **Ring i misst bei einem doppelt so grossen Objekt eine
voellig andere Stelle der Form.**

Der fuenfte Ansatz haengt die Ringe an die **Eigenausdehnung** des Objekts: Ring i sitzt immer bei
derselben *relativen* Position (0,15 bis 1,35 der Eigenausdehnung). Dann ist "Ring 3 von 11" bei
jeder Groesse dieselbe Stelle der Form, und die Winkelfuellung dort ist eine Form- statt einer
Groessenaussage. Drei Masse fuer die Ausdehnung, weil die Wahl nicht vorab klar ist: `rms`
(Wurzel des mittleren quadratischen Abstands), `sqrtA` (Wurzel der Flaeche), `rmax`
(95. Perzentil).

# Zahlen

Kennzahl **K = groesster GROESSEN-Abstand / kleinster FORM-Abstand**; unter 1,0 waere das Ziel.
Drei Formen (Balken, Quadrat, flaches Rechteck) in je drei Groessen, 10 Lagen je Probe.

    Variante      Seed 5   Seed 23   Seed 41   Mittel
    heute           4,00      3,35      3,69     3,68     <- feste Ringe, der Ist-Zustand
    dicke           3,89      4,00      3,90     3,93     <- die vier bereits
    dc              4,09      4,78      3,87     4,25        gescheiterten
    fuellung        3,89      3,66      3,32     3,62        Fassungen
    rms             2,22      2,48      2,40     2,37     <- der fuenfte Ansatz
    sqrtA           2,78      2,64      2,24     2,55
    rmax            2,31      1,94      1,99     2,08

**Die vier alten Fassungen bewegen im selben Aufbau nichts** (3,62 bis 4,25 gegen 3,68) - ihr
Misserfolg ist damit hier repliziert. **Die relativen Ringe halbieren die Kennzahl** (2,08 bis
2,55), und zwar in allen drei Seeds.

Wichtig fuer die Richtung: die Verbesserung kommt **nicht** daher, dass alles zusammenrueckt. Der
kleinste FORM-Abstand *steigt* (4,82 -> 6,44 bei Seed 5), waehrend der groesste Groessen-Abstand
faellt (19,28 -> 14,28). Die Formen werden also **besser** getrennt und die Groessenvarianten
naeher zusammengezogen - genau das Gewuenschte.

# Bewertung

* **Deutlicher Fortschritt, Ziel nicht erreicht.** K ~2,1 heisst weiterhin: die groesste
  Groessenvariante liegt doppelt so weit von ihrer eigenen Form entfernt wie die naechste fremde
  Form. Ein Klassifikator mit fester Schwelle wuerde sie immer noch als neuartig lesen.
* **`rmax` ist am besten** (2,08), `rms` dicht dahinter (2,37). Der Unterschied liegt innerhalb
  der Seed-Streuung; eine Entscheidung zwischen beiden ist aus diesen Zahlen nicht zu treffen.
* **Der Aufbau ist haerter als der urspruengliche.** Die heutige Fassung kommt hier auf 3,68, in
  [Formfaktorisierung](/befunde/formfaktorisierung.md) auf 2,54 - andere Koerper, andere
  Groessenspanne. **Deshalb sind die vier alten Fassungen hier nachgerechnet worden**; ohne das
  waere "2,37 gegen 2,13" ein scheinbarer Rueckschritt gewesen, obwohl es ein Fortschritt ist.

# Der Preis, und er ist hoch

**Ein geaenderter Deskriptor entwertet den gesamten gelernten Klassenbestand.** Die 80 Exemplare
je offener Klasse sind mit festen Ringen berechnet; mit relativen Ringen sind sie schlicht andere
Vektoren. Die Masken, aus denen sie stammen, sind nicht gespeichert - **nachrechnen geht nicht.**

Ein Einbau bedeutet also: `novel_th` neu kalibrieren, die trainierten Formen neu anlernen, das
Open-Set von vorn aufbauen. Das ist kein Schalter, sondern ein Schnitt. Die
[Invarianten](/mechanismen/invarianten.md) verlangen dafuer ohnehin `STATE_SCHEMA` hochzuzaehlen.

# Was NICHT gezeigt ist

* **Ob act23 damit besser generalisiert.** Das hier ist `ebene: pruefstand`, und die
  [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) ist in diesem Projekt dreimal
  zugeschnappt. Die Kennzahl ist eine Eigenschaft des Deskriptors, keine des Laufs.
* **Ob K ~2,1 im Betrieb reicht.** Der [Form-Rueckhalte-Test](/befunde/form-rueckhalt.md) waere
  das direkte Mass - er braucht aber einen Klassenbestand im neuen Deskriptor, also erst den
  Schnitt oben.
* **Ob die Trennung der BEKANNTEN Formen erhalten bleibt.** Der steigende Form-Abstand deutet
  darauf hin, ist aber an drei kuenstlichen Formen gemessen, nicht an L/U/Wuerfel/Kreuz.

# Empfehlung

Nicht sofort einbauen. Die naechste billige Stufe waere, den
[Form-Rueckhalte-Test](/befunde/form-rueckhalt.md) **mit dem neuen Deskriptor auf einem
frisch angelernten Klassenbestand** zu fahren - das kostet einen Anlernlauf, aber keinen
Langlauf, und es beantwortet die Frage, die zaehlt: faellt eine uebergrosse Form dann in die
richtige Kategorie?

Erst wenn das traegt, lohnt der Schnitt am Live-Zustand.

# Verwandt

* [Formfaktorisierung](/befunde/formfaktorisierung.md) - die vier gescheiterten Anlaeufe
* [Form-Rueckhalte-Test](/befunde/form-rueckhalt.md) - das direkte Mass, das hier fehlt
* [Geburtenrate und Saettigung](/befunde/geburtenrate-und-saettigung.md) - warum das der Engpass ist
* [Die Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)
