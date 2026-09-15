---
type: Befund
title: Die freie Vergabe oeffnet die erste Tuer - zwei Knoepfe statt einem, und dahinter stehen zwei weitere
description: Der Riegel ist auf: 2 vergebene Knoepfe gegen 1, und eine Klasse bindet erstmals an den Koerper, auf dem sie sitzt, statt an den reservierten Probe-Koerper. Das Repertoire wird trotzdem nicht breiter, denn der zweite Knopf ging an einen Koerper, der ohnehin kommandierbar war. Dahinter werden zwei weitere Tueren sichtbar: drei Kandidaten verhungern vor der Bestaetigung, und ein Koerper kann nur Knopf bekommen, wenn er in der Szene steht - eingefuehrt wird aber nur der eine Probe-Koerper.
tags: [act23, selbstlernen, formklassen, kommando, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-15T00:00:00Z }
sources:
  - id: ab
    resource: "Zwei frische Laeufe (ACT23_FRESH=1) je 120 Episoden, ACT23_FREIE_VERGABE 0 gegen 1"
    title: Freie Vergabe, erster Lauf
  - id: diag
    resource: /befunde/vergabe-engstelle-diagnose.md
    title: Die Diagnose, die hier teils bestaetigt und teils korrigiert wird
---

# Der Einbau

Aus [der Diagnose](/befunde/vergabe-engstelle-diagnose.md): der Knopf haengt fest an `NOVEL_BODY`.
`ACT23_FREIE_VERGABE=1` entfernt **nur diese Festverdrahtung** - die Bestaetigungsschranke
(`BIND_CONFIRM` von `BIND_WIN` Blicken) bleibt unveraendert, und bestaetigt wird gegen den Koerper,
auf dem die Klasse tatsaechlich sitzt. Ein Koerper, der schon eine Formklasse traegt, kommt nicht
in Frage.

# Zahlen

    Arm       Ep   Quote   Geburten   Knoepfe   Kandidaten verhungert
    fv_aus   120   3,3 %       4         1               0
    fv_an    120   6,7 %       5         2               3

    fv_an:  'neu-1' -> 'Neue Form 2' auf obj_T      (3 von 6 Blicken)
            'neu-3' -> 'Neue Form 3' auf obj_blue   (3 von 3 Blicken)

**Der Riegel ist auf.** Zum ersten Mal bekommt eine selbst geborene Klasse einen Knopf auf einem
anderen Koerper als dem reservierten Probe-Koerper. Im Vorgabearm ist nach dem ersten Knopf
strukturell Schluss, egal wie viele Klassen noch geboren werden.

Die Quote (3,3 gegen 6,7 %) sind 4 gegen 8 Lieferungen in 120 frischen Episoden und sagen nichts.

# Und das Repertoire wird trotzdem nicht breiter

Der zweite Knopf ging an **obj_blue** - einen Koerper, der von Anfang an in `state.OBJECTS` steht.
Die Liste der adressierten Koerper ist in beiden Armen identisch:

    obj_L  obj_T  obj_U  obj_blue  obj_green  obj_red

Gewonnen ist also: obj_blue hat jetzt zusaetzlich eine selbst benannte Formklasse. Nicht gewonnen
ist: ein Objekt, das der Agent vorher nicht ansprechen konnte.

# Die zweite Tuer, erstmals sichtbar

    Kandidaten verhungert:   fv_aus 0      fv_an 3

Die Null im Vorgabearm ist kein gutes Zeichen, sondern die Engstelle selbst: dort wird nach dem
ersten Knopf **niemand mehr Kandidat**, also kann auch niemand als Kandidat verhungern. Im freien
Arm registrieren sich alle - und `neu-2`, `neu-4`, `neu-5` sterben, bevor sie dreimal auf demselben
Koerper bestaetigt sind.

> **Die Engstelle hat mehr als eine Tuer, wie befuerchtet.** Die erste ist auf; dahinter steht der
> Verhungerungsschutz, der eine junge Klasse nach ~25 Blicken loescht
> ([Der blinde Fleck der Aneignung](/befunde/aneignung-blinder-fleck.md)).

# Die dritte Tuer - und eine Korrektur an meiner Diagnose

[Die Diagnose](/befunde/vergabe-engstelle-diagnose.md) schrieb, `obj_X` werde nie adressiert,
*"obwohl er die ganze Zeit sichtbar auf dem Tisch liegt"*. **Das ist falsch.** Nachgezaehlt:

    frischer Lauf, Koerper in 'after ep':  obj_red obj_green obj_L obj_U obj_blue
    obj_X im gesamten Protokoll erwaehnt:  0 mal

**Im frischen Lauf steht obj_X gar nicht in der Szene.** Er taucht nur in Laeufen aus dem
gespeicherten Zustand auf, weil er dort historisch einmal einen Knopf bekam - und `_try_bind`
traegt den Koerper bei der Vergabe in `act16.OBJS` ein.

Damit schliesst sich ein drittes Rad:

    ein Koerper kann nur Knopf bekommen, wenn er in der SZENE steht
      (`_frei = [o for o in scene if o not in state.SHAPE_KEY]`)
    in die Szene kommt er durch die Vergabe  (`act16.OBJS + [_ziel]`)
    als NEUES Objekt eingefuehrt wird aber nur der eine Probe-Koerper (NOVEL_EVERY)

**Die freie Vergabe kann nur verteilen, was schon da ist.** Sie macht aus einem Knopf mehrere,
aber sie bringt kein neues Objekt in die Welt. Dafuer waere `spawn_novel_shape` zustaendig - und
das kehrt seit Langem in der ersten Zeile zurueck
([Geburtenrate und Saettigung](/befunde/geburtenrate-und-saettigung.md)).

# Bewertung

* **Der Einbau tut, was er soll**, und ist mechanisch belegt (2 Knoepfe, zweiter auf einem anderen
  Koerper, Bestaetigung 3 von 3).
* **Er reicht allein nicht.** Ohne einen Erzeuger neuer Objekte und ohne Schutz junger Klassen
  verteilt er Knoepfe an Koerper, die ohnehin kommandierbar waren.
* **Die Reihenfolge ist damit klar geworden:** erst muss die Welt etwas Neues anbieten
  (`spawn_novel_shape`), dann muss eine junge Klasse lange genug leben (Verhungerungsschutz), und
  erst dann traegt die freie Vergabe. Ich habe die drei fuer EIN Problem gehalten.

# Fallen

* **Je ein Seed, 120 frische Episoden.** Fuer die strukturelle Aussage (2 gegen 1 Knopf) reicht
  das, fuer Geburtenzahlen und Quote nicht.
* **Ein Absturz im ersten Anlauf**, von mir verursacht: die Mitbewerber-Zeile rechnete `sum(h)`
  weiter, waehrend `hits` jetzt Koerpernamen traegt. Behoben durch eine gemeinsame Zaehlhilfe
  `_zaehl`, die fuer beide Modi gilt. Der Absturz kam ausgerechnet im Moment der zweiten Vergabe -
  der Mechanismus hatte da schon funktioniert.
* **Vorgabe bleibt 0.** Der Schalter allein bewegt das Ziel nicht.

# Verwandt

* [Die Vergabe-Engstelle, diagnostiziert](/befunde/vergabe-engstelle-diagnose.md) - hier teils korrigiert
* [Die Geburtenrate hat zwei Ursachen](/befunde/geburtenrate-und-saettigung.md) - der tote Erzeuger
* [Der blinde Fleck der Aneignung](/befunde/aneignung-blinder-fleck.md) - die zweite Tuer
* [Ziel](/ziel.md)
