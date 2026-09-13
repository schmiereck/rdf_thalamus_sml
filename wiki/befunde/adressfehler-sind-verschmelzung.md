---
type: Befund
title: JEDER grobe Adressierungsfehler sitzt im obersten Groessenband - die Adressierung hat kein Groessenproblem, sondern ein Verschmelzungsproblem
description: In zwei Armen zu je 150 Episoden liegen 26 von 26 groben Adressierungsfehlern im Band "riesig" (Spanne ab 36 mm). In den uebrigen 266 Adressen ueber alle anderen Baender: null. Kein einzelner Koerper wird so gross ausser obj_U - "riesig" ist faktisch das Band der verschmolzenen Blobs. Damit ist der Restfehler des siebten Anlaufs lokalisiert, und er ist keine Frage der Achse.
tags: [act23, kommando, wahrnehmung, verschmelzung]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-13T00:00:00Z }
sources:
  - id: ab
    resource: "Zwei kopflose Steuerungslaeufe je 150 Episoden aus derselben Kopie von act23_state.pkl (ad9d768c), ACT23_GROESSE_SPANNE=1 ACT23_EIG_IDENT=1, ACT23_EIG_ABSTUFUNG 0 gegen 1"
    title: Nebenauswertung des Abstufungs-A/B
---

# Der Befund

Aufgefallen beim Auswerten des [Abstufungs-Laufs](/befunde/abstufung-statt-privileg.md), nicht
gesucht. Grobe Adressierungsfehler (>20 mm), aufgeschluesselt nach dem Groessenband der Adresse:

    Arm        winzig  klein  mittelklein  mittel  gross  riesig  (ohne Band)
    ab_aus      0/2    0/10      0/9       0/20   0/14    5/21      0/83
    ab_best     0/5    0/15      0/7       0/20   0/10   21/44      0/71

    zusammen   26 von 26 groben Fehlern im Band "riesig"
               0 von 266 Adressen in allen anderen Baendern zusammen
               Fisher p = 3,4e-21

Das ist keine Tendenz, das ist eine Trennlinie. **Ausserhalb von `riesig` ist die Adressierung
fehlerfrei** - ueber alle Farben, alle Formklassen, beide Arme.

# Warum das nichts mit Groesse zu tun hat

`riesig` faengt alles ab 36,0 mm Spanne. Gemessen misst der groesste einzelne Koerper, obj_U,
**37,4 mm** ([Groessenachse](/befunde/groessenachse-spanne.md)) - er ist der einzige, der legitim
dort landet. Alles andere in `riesig` ist ein **verschmolzener Blob** aus zwei Koerpern, die naeher
als ~40 mm beieinander lagen ([Verschmelzungs-Abstandskurve](/befunde/verschmelzung-abstandskurve.md)).

Die Formklassen bestaetigen es: der Fehler haengt an einer einzigen Klasse.

    je Formklasse der Adresse (grobe Fehler / Adressen)
      ab_aus    neu-13  3/9    | alle uebrigen zusammen  2/150
      ab_best   neu-13 17/23   | alle uebrigen zusammen  4/152

`neu-13` ist auf einem verschmolzenen Blob geboren worden. Wer sie adressiert, adressiert den
Schwerpunkt **zweier** Koerper - und liegt damit genau die 20 bis 30 mm daneben, die als "grober
Fehler" gezaehlt werden.

# Was das an der bisherigen Lesart aendert

Der [siebte Anlauf](/befunde/groessenachse-spanne.md) senkte die groben Fehler von 10,8 auf 3,1 %
und liess offen, woher der Rest kommt. Die naheliegende Annahme war "noch zu grobe Baender" - sie
war der Anlass fuer das [7-mm-Raster](/befunde/spannen-raster-7mm.md), das nichts brachte.

**Der Rest ist kein Rest der Achse.** Er ist die Verschmelzung, die durch die Achse nur sichtbarer
wurde, weil sie sich im obersten Band sammelt.

> Rueckblickend erklaert das auch, warum der Identitaetscheck erst ZUSAMMEN mit der Spannen-Achse
> wirkte: die Dicke-Achse warf alles ins Band "mittel" und vermischte verschmolzene mit einzelnen
> Koerpern. Die Spanne sortiert die Verschmelzungen nach oben aus - **sie hat den Fehler nicht
> behoben, sondern ihn an einen Ort gelegt, an dem man ihn sehen kann.**

# Der naheliegende Eingriff, und warum er schon existiert

Fuer genau diesen Fall gibt es im Code bereits eine Rettung - aber nur auf dem FORM-Pfad
(`ACT23_FORM_SPLIT`, `perceive`, Zweig `shape`): ist der Blob verschmolzen, wird die Form auf dem
**farb-getrennten** Teil noch einmal erkannt. Gemessen hob das obj_T von 8,8 auf 81 % im
verschmolzenen Fall.

**Der Eigenschafts-Pfad hat diese Rettung nie bekommen.** Er ist juenger als der Form-Pfad, und der
Split wurde damals nur dort eingebaut, wo das Problem auffiel. Das waere kein neuer Mechanismus und
keine neue Laufzeitregel, sondern ein vorhandener Mechanismus an einer zweiten Stelle.

Ungemessen. Es ist der naechste naheliegende Schritt, und er ist billiger als jede weitere Arbeit
an der Groessenachse.

# Fallen

* **Zwei Arme, ein Seed je Arm.** Der Befund traegt trotzdem, weil er INNERHALB der Laeufe ueber
  331 Adressen misst und in beiden Armen dieselbe Trennlinie zeigt (p = 2,6e-05 bzw. 4,2e-15
  jeweils fuer sich allein).
* **`riesig` ist nicht gleich verschmolzen.** obj_U gehoert legitim dorthin; von den 65
  `riesig`-Adressen sind 39 richtig. Das Band ist ein Verdachtsmoment, kein Nachweis - eine
  Gegenmassnahme darf es nicht einfach verwerfen.
* **Die Zaehlung enthaelt Wiederholungen.** Dieselbe `[dbg]`-Zeile erscheint mehrfach je Episode;
  so wurde auch im siebten Anlauf gezaehlt, damit die Zahlen vergleichbar bleiben
  ([Rasterbefund](/befunde/spannen-raster-7mm.md), Abschnitt zur Auswerter-Falle).

# Verwandt

* [Abstufung statt Privileg](/befunde/abstufung-statt-privileg.md) - der Lauf, aus dem das hier abfiel
* [Die Groessenachse mass die falsche Groesse](/befunde/groessenachse-spanne.md) - der Restfehler, hier lokalisiert
* [Verschmelzungs-Abstandskurve](/befunde/verschmelzung-abstandskurve.md) - ab wann Blobs verschmelzen
* [Das groebere 7-mm-Raster](/befunde/spannen-raster-7mm.md) - das Band "gewaltig", dieselbe Ursache
