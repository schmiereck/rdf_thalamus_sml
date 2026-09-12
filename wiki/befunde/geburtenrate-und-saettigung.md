---
type: Befund
title: Die Geburtenrate hat zwei Ursachen - ein toter Erzeuger und eine gesaettigte Welt
description: spawn_novel_shape kehrt seit Langem in der ersten Zeile zurueck, weil sein einziger Probe-Koerper gebunden ist - der Neuheits-Erzeuger laeuft nicht. Und selbst repariert wuerde die Haelfte seiner Formen in eine bestehende Kategorie fallen. Die Formklassen SIND bereits Grobkategorien; zwei von ihnen sind naeher beieinander als die Streuung innerhalb einer einzelnen.
tags: [act23, selbstlernen, formklassen, wahrnehmung]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-12T10:00:00Z }
sources:
  - id: code
    resource: "pc_act23.py:2886 (spawn_novel_shape), :2522 (NOVEL_BODY), :2876 (_novel_shapes)"
    title: Quelltext
  - id: probe
    resource: "Zustand act23_state.pkl (ad9d768c): Exemplarstreuung im z-Raum, 7 Koerper x 10 Lagen, 4 Neuheitsformen x 8 Lagen"
    title: Kategorien-Probe
---

# Anlass

Nutzerfrage: *"Faellt Dir etwas ein, wie wir die Geburtenrate verbessern koennen?"* - und der
Gedanke dazu: *"Vielleicht sind wir am Limit. Unser Baby wuerde wahrscheinlich auch irgendwann
nur noch 'die eher roetlichen' oder 'die eher langen' oder 'die viereckigen' unterscheiden und
nicht jede Form einzeln auswendig lernen."*

Dazu die Klarstellung, die im Protokoll fehlte: **es geht um FORMklassen.** Farben haben ein
eigenes Open-Set (`colours`, Namen `farbe-*`); Formen eines im `ShapeClassifier` (`neu-*`). Im
906-Episoden-Langlauf wurden **13 Formklassen** und **3 Farbklassen** geboren. Kombinationen
haben gar kein eigenes Open-Set - sie entstehen erst im
[Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) als Tripel.

# Erste Ursache: der Erzeuger laeuft nicht

    pc_act23.py:2886   def spawn_novel_shape():
                           if NOVEL_BODY in state.SHAPE_KEY:
                               return
    pc_act23.py:2522   NOVEL_BODY = os.environ.get("ACT23_NOVEL_BODY", "obj_T")
    Zustand:           SHAPE_KEY = {'obj_T': 'neu-9', 'obj_X': 'neu-285'}

`obj_T` **ist** gebunden - die Funktion kehrt in der ersten Zeile zurueck. Gegenprobe im
906-Episoden-Langlauf: `[Neuheit-Kontrolle]` und `[Neuheit]` kommen **null Mal** vor.

Damit sind die 13 Geburten jenes Laufs **nicht** vom Neuheits-Erzeuger verursacht, sondern
spontan aus Wahrnehmungsvariation. Und es erklaert, warum `NOVEL_EVERY=3` statt 6 im
[Schutz-A/B](/befunde/eig-schuetzt-null.md) nichts an der Geburtenrate aenderte: **der Schalter
steuert eine Funktion, die sofort zurueckkehrt.**

# Zweite Ursache: die Welt ist gesaettigt - die Nutzerhypothese traegt

**Die Formklassen SIND bereits Grobkategorien.** Ueber 7 Koerper x 10 Lagen:

    obj_red, obj_green, obj_blue  ->  cube     (10/10 je Koerper)   EINE Klasse, DREI Koerper
    obj_L                         ->  L        (10/10)
    obj_U                         ->  U        (10/10)
    obj_T                         ->  neu-9    (10/10)
    obj_X                         ->  neu-285  (8/10, 2x cube)

`cube` fasst drei Koerper zusammen - genau das "die viereckigen" aus der Nutzerfrage, und es
funktioniert.

**Und zwei Klassen sind naeher beieinander als die Streuung INNERHALB einer einzigen:**

    Streuung innerhalb einer Klasse (Median / max, in Einheiten von novel_th = 7,715)
      neu-9    0,57 / 0,90        neu-13   1,14 / 2,48
      neu-34   1,07 / 2,49        neu-285  0,77 / 3,12

    Abstand zwischen den Klassenzentren
      neu-9 <-> neu-285   0,66     <- NAEHER als die Innenstreuung von neu-13 (1,14)
      neu-9 <-> neu-34    1,42          und von neu-34 (1,07)
      neu-34 <-> neu-285  1,30
      neu-9 <-> neu-13    2,40

`obj_T` (21x7 mm) und `obj_X` (21x6 mm) sind geometrisch fast dasselbe - zwei lange duenne
Balken. Der Deskriptor sieht sie entsprechend: `neu-9` und `neu-285` sind **keine zwei
Kategorien**, sondern eine, die zufaellig zweimal geboren wurde. Dass `obj_X` in 2 von 10 Lagen
als `cube` gelesen wird, passt ins Bild.

# Die entscheidende Probe: waeren die Neuheitsformen ueberhaupt neu?

Die vier Proportionen, die `spawn_novel_shape` auf `obj_T` setzen wuerde:

    Halbmasse [mm]   Verhaeltnis   genannt ueber 8 Lagen
    22 x 20             1,1:1       None 8/8          <- neuartig
    30 x  4             7,5:1       neu-9 7, None 1   <- faellt in die BESTEHENDE Klasse
    24 x 22             1,1:1       None 8/8          <- neuartig
    32 x  5             6,4:1       neu-9 6, None 2   <- faellt in die BESTEHENDE Klasse

**Die Haelfte des Neuheitsvorrats ist gar nicht neu.** Die beiden langen duennen Varianten sind
fuer die Wahrnehmung dasselbe wie `obj_T` - und das ist **kein Fehler, sondern korrekte
Verallgemeinerung**: ein 30x4-Balken *ist* dieselbe Kategorie wie ein 21x7-Balken.

Die beiden fast-quadratischen (1,1:1) waeren dagegen echt neu - interessanterweise auch nicht als
`cube` erkannt, obwohl der Wuerfel 1:1 ist. Der Unterschied liegt in der absoluten Groesse
(22 mm gegen 12 mm Halbmass).

# Bewertung

**Die Nutzerhypothese ist bestaetigt, und zwar schaerfer als formuliert.** Es ist nicht nur so,
dass der Agent *irgendwann* grob sortieren wuerde - er tut es **bereits**: drei Wuerfel in einer
Klasse, und zwei nominell verschiedene Klassen, die dieselbe Kategorie meinen.

Daraus folgt etwas Unbequemes fuer die bisherige Messweise: **"mehr Geburten" ist kein gutes Ziel.**
Eine Geburt bedeutet "das kenne ich nicht" - in einer Welt mit vier unterscheidbaren Grobformen
ist eine hohe Geburtenrate ein Zeichen von schlechter Verallgemeinerung, nicht von guter
Aneignung. Die 13 Geburten des Langlaufs, die alle verhungerten, koennten genau das sein:
**Uebersegmentierung, die sich von selbst korrigiert.**

Die richtige Frage waere dann nicht "warum gebiert er so wenig", sondern: **"faellt ein neues
Objekt in die richtige Grobkategorie?"** Das ist Verallgemeinerung und trifft
[das Projektziel](/ziel.md) direkter als jede Geburtenzahl.

# Was daraus folgt - drei Wege, keiner gebaut

1. **Den Erzeuger reparieren** (klein): `NOVEL_BODY` auf einen ungebundenen Koerper legen, oder
   die Sperre loesen. Bringt aber nach obigem nur die Haelfte der Formen als echte Neuheit - und
   mehr Geburten sind, siehe oben, nicht zwingend das Ziel.
2. **Echte Formtopologie statt Proportionen** (mittel): ein Ring, ein Dreieck, ein Stern, ein
   Balken mit drei Zinken. Proportionsvarianten desselben Balkens sind fuer einen
   rotationsinvarianten Deskriptor eben *derselbe Balken*. Das ist eine Szenen-Erweiterung.
3. **Die Metrik wechseln** (am wichtigsten): statt Geburten zu zaehlen, einen **Rueckhalte-Test
   fuer Formen** bauen - ein Koerper, den der Agent nie gesehen hat, wird hingestellt, und
   gemessen wird, ob er in die passende bestehende Kategorie faellt statt eine neue zu gebaeren.
   Das ist dieselbe Bauart wie der
   [Farb-Rueckhalte-Test](/befunde/farbe-form-rueckhalt.md) und kostet keinen Lauf.

# Fallen

* **Zwei Klassen, eine Kategorie ist kein Beweis fuer Saettigung im Allgemeinen** - es ist ein
  Beleg fuer diese sieben Koerper. Eine Welt mit topologisch verschiedenen Formen koennte anders
  aussehen; das ist ungemessen.
* **Die Innenstreuung ist teils groesser als der Abstand zwischen Klassen** (neu-13 innen 1,14
  gegen neu-9/neu-285 0,66). Die Klassen ueberlappen also; "saubere Kategorien" waere zu viel
  gesagt.

# Verwandt

* [Farb-Rueckhalte-Test](/befunde/farbe-form-rueckhalt.md) - dieselbe Bauart fuer die Farbachse
* [Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md) - die Geburtenzahlen, hier neu gedeutet
* [Der Eigenschafts-Schutz wirkt nicht](/befunde/eig-schuetzt-null.md) - warum NOVEL_EVERY dort nichts tat
* [Projektziel](/ziel.md)
