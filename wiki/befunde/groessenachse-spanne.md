---
type: Befund
title: Die Groessenachse mass die falsche Groesse - und wirkt nur zusammen mit der Identitaetspruefung
description: Die Adress-Achse "Groesse" nutzte die Materialdicke, und alle sieben Koerper liegen dort im selben Band. Auf die Ausdehnung umgestellt trennt sie alle fuenf Formen mit 2,2 bis 4,8 Streuungen. Im Lauf wirkt sie aber nur zusammen mit einer zweiten Reparatur: grobe Adressierungsfehler 10,8 auf 3,1 Prozent, wenn BEIDE an sind - jede allein bewegt nichts.
tags: [act23, kommando, wahrnehmung, generalisierung]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-14T12:00:00Z }
sources:
  - id: ab
    resource: "Faktorielles A/B: 4 kopflose Steuerungslaeufe je 150 Episoden aus derselben Kopie von act23_state.pkl (ad9d768c), ACT23_GROESSE_SPANNE x ACT23_EIG_IDENT, gleichzeitig gefahren"
    title: Siebter Anlauf, faktoriell
  - id: mess
    resource: "7 Koerper x 10 Lagen: Dicke und Spanne je Detektion"
    title: Trennkraft der beiden Achsen
---

# Der Auftrag verschob sich

Bestellt war "das Groessenband feiner". Die Messung davor zeigt, dass das nichts gebracht
haette - **die Achse ist nicht zu grob, sie ist die falsche:**

    DICKE (die bisherige Achse)
      obj_L 5,61 | obj_X 5,70 | obj_U 5,83 | obj_T 5,91 | cube 6,04
      -> alle sieben Koerper im Band "mittel" (5,2-6,5); Trennung 0,3 bis 0,7 Streuungen

    SPANNE (95.-Perzentil des Abstands vom Schwerpunkt)
      cube 20,0 | obj_X 24,4 | obj_T 28,3 | obj_L 34,5 | obj_U 37,4 mm
      -> Trennung 2,2 bis 4,8 Streuungen

Die Dicke misst die **Materialbreite**, und alle Balken sind 14 mm breit. Feinere Grenzen darauf
haetten nur die Streuung zerschnitten. Die Spanne misst die **Ausdehnung** - sie wird in
`perceive_all` laengst gerechnet (Feld `span`), war aber nie als Adressachse herausgefuehrt.

Bandraster bewusst gleichmaessig (5 mm ab 17,5), nicht auf die gemessenen Koerper gelegt:
koerpergenaue Grenzen waeren auf diese sieben ueberfittet.

# Der zweite Fund: eindeutig ist nicht richtig

Beim Lesen der Wuerfelei fiel auf, dass sie Achsen nachlegt, bis `finde_nach_eigenschaften`
**genau einen** Treffer meldet - und dabei nur die **Anzahl** prueft, nicht die **Identitaet**.
Trifft das Tripel genau eine Detektion, und ist das die falsche, gilt die Adresse als eindeutig
und ist trotzdem falsch. Das erklaert die 316 von 318 "eindeutigen" Adressen bei 8,8 % groben
Fehlern aus [dem sechsten Anlauf](/befunde/relrings-split-zielkonflikt.md).

`ACT23_EIG_IDENT=1` verlangt zusaetzlich, dass der eine Treffer auf dem gemeinten Koerper sitzt.

# Zahlen: es wirkt nur zusammen

    Arm         Ep   Quote | Adr.Median   grobe Fehler >20mm | Rueckfall | Achsen/Adresse
    g7_aus     150  58,7 % |   2,0 mm      18/167 = 10,8 %   |     7     |     1,82
    g7_span    150  55,3 % |   3,2 mm      14/159 =  8,8 %   |    21     |     1,79
    g7_ident   150  58,7 % |   2,0 mm      18/167 = 10,8 %   |     7     |     1,85
    g7_beide   150  66,0 % |   3,2 mm       5/159 =  3,1 %   |    15     |     1,79

    gegen die Vorgabe:  span   p = 0,58     ident  p = 1,00     beide  p = 0,0086

**Jede Aenderung allein bewegt nichts. Zusammen fallen die groben Fehler von 10,8 auf 3,1 %.**

`g7_ident` ist **bitgleich** zu `g7_aus` - der Identitaetscheck hat kein einziges Mal gegriffen.
Der Grund steht in der Bandverteilung:

    g7_aus     dick 12 | duenn 2 | mittel 75
    g7_beide   winzig 2 | klein 10 | mittelklein 9 | mittel 20 | gross 14 | riesig 21

Mit der Dicke-Achse landen fast alle Adressen im Band "mittel". Wenn die Pruefung bemerkt, dass
die Adresse den falschen Koerper trifft, **hat sie nichts zum Nachlegen** - die Groesse trennt ja
nicht. Erst die Spanne gibt ihr eine Achse, die tatsaechlich unterscheidet.

Umgekehrt nutzt die Spanne allein wenig: die Wuerfelei legt sie nur nach, wenn *mehrere* Treffer
auftreten - und bei einem einzigen falschen Treffer tut sie es eben nicht.

> **Die beiden Aenderungen sind kein Paket, sondern Schloss und Schluessel.** Wer sie einzeln
> misst, misst zweimal null. Genau dafuer war das A/B faktoriell angelegt.

# Bewertung

* **Die Zielgroesse faellt um zwei Drittel** (10,8 -> 3,1 %, p = 0,0086) und liegt damit unter dem
  Niveau, das der feste Deskriptor ohne Groessen-Invarianz erreichte (2,1 % im sechsten Anlauf,
  allerdings anderer Aufbau).
* **Die Lieferquote geht in die richtige Richtung**, ist aber nicht aufgeloest: 58,7 -> 66,0 %,
  p = 0,23 bei n = 150. Das ist die uebliche Nachweisgrenze
  ([Rechnerlast](/befunde/rechnerlast.md)).
* **Der Median-Adressfehler STEIGT** (2,0 -> 3,2 mm), waehrend die groben Fehler fallen. Kein
  Widerspruch: die Spanne kostet etwas Feinheit und gewinnt die Faelle, in denen frueher der
  falsche Koerper adressiert wurde.

# Der Preis, und er ist real

**Der privilegierte Rueckfall verdoppelt sich** (7 -> 15, mit Spanne allein sogar 21). Feinere
Baender heissen: haeufiger passt gar keine Adresse, und dann greift der privilegierte Pfad. Das
sind ~5 % der Episoden gegen ~5 % vorher... genauer: 15 von 150 gegen 7 von 150, also 10,0 % gegen
4,7 %. Fuer ein Projekt, das [Privilegien abbauen](/ziel.md) will, ist das ein echter Nachteil und
kein Rundungsfehler.

Ob er sich mit einem groeberen Raster (etwa 7 mm statt 5) vermeiden laesst, ohne die Trennkraft zu
verlieren, ist **ungemessen**.

# Fallen

* **Ein Seed je Arm**, 150 Episoden. Der Adressierungsbefund traegt, weil er innerhalb der Laeufe
  ueber ~160 Sichtungen misst; die Quote traegt nicht.
* **Die Bandnamen sind neu** (winzig/klein/mittelklein/mittel/gross/riesig statt
  duenn/mittel/dick). Ein gespeicherter Zustand mit alten Tripeln in `state.EIGENSCHAFT` wuerde
  sie nicht mehr finden - das ist folgenlos, weil `EIGENSCHAFT` nicht persistiert wird, aber es
  ist eine Stolperstelle fuer kuenftige Auswertungen alter Protokolle.
* **Beides bleibt auf Vorgabe 0.** Zwei gekoppelte Schalter einzuschalten ist eine groessere
  Entscheidung als einer, und der Rueckfall-Preis gehoert vorher benannt.

# Verwandt

* [Sechster Anlauf: der Zielkonflikt](/befunde/relrings-split-zielkonflikt.md) - der Anlass
* [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) - "Eindeutigkeit ist nicht Richtigkeit"
* [Formfaktorisierung](/befunde/formfaktorisierung.md) - "die Faktorisierung gehoert NEBEN den Deskriptor"
