---
type: Befund
title: Der Keim erreicht den Tracker beim Eigenschafts-Kommando nie
description: Der Schluessel, unter dem der Eigenschafts-Pfad die Erst-Wahrnehmung veroeffentlicht, ist ein anderer als der, unter dem der Tracker sie abfragt - in 120 von 120 Episoden. Der Tracker startet deshalb blind auf dem wahrscheinlichsten gleichklassigen Blob und trifft bei mehreren Kandidaten in 41 Prozent das falsche Objekt. Kein Start-Fehler wurde je geliefert.
tags: [act23, wahrnehmung, tracker, kommando, fehler]
status: stable
evidenz: gemessen
ebene: langlauf
generated: { by: claude/opus-5, at: 2026-09-08T23:30:00Z }
sources:
  - id: keimlauf
    resource: "Kopfloser Steuerungslauf, 120 Episoden, ACT23_KEIMDIAG=1 + ACT16_ABLENKDIAG=1 + ACT16_GLAUBDIAG=1, auf einer Kopie von act23_state.pkl (98a293f2)"
    title: Keim-Diagnoselauf
  - id: vorher
    resource: /befunde/ablenker-bindung-gemessen.md
    title: Die Messung, die diese Frage gestellt hat
---

# Behauptung

Die Ablenker-Bindung entsteht **beim Aufsetzen des Trackers**, und die Ursache ist ein
Schluesselfehler: der Eigenschafts-Pfad veroeffentlicht die Erst-Wahrnehmung unter
`eig:{body}`, der Tracker fragt sie unter der **Formklasse** ab. Die beiden treffen sich nie.

**In 120 von 120 Episoden hat der Keim nicht gegriffen.** Der Tracker faellt damit in seinen
eigenen Notzweig - den wahrscheinlichsten gleichklassigen Blob - vor dem sein Docstring
ausdruecklich warnt.

# Der Fehler am Code

    pc_act23.py:2986   perception.publish_seed(f"eig:{body}", ...)      veroeffentlicht "eig:obj_green"
    pc_act23.py:3129   ... perception.seed_for(key) ...                 fragt "cube" / "neu-34" / None
    perception.py:124  if self.seed_key != key: return None             -> immer None

Ohne Keim greift in `make_shape_track`:

    if mem["xy"] is None:            # first sighting: most confident match
        best = max(cands, key=lambda d: d["prob"])

Der Docstring daneben sagt selbst, warum das nicht genuegt: *"the first-frame max-prob pick can
be a DIFFERENT same-class blob -- the user watched the U command start focused on the L"*. Genau
dagegen war der Keim gebaut; fuer das Eigenschafts-Kommando ist er wirkungslos.

**Herkunft:** eingeschleppt mit `0d8c88f` ("Fovea an das Eigenschafts-Kommando koppeln"). Dort
wurde `method` an den vier bekannten Stellen angemeldet
([Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md)) - der Keim-Schluessel war eine
fuenfte, uebersehene.

# Zahlen

120 Episoden.[^keimlauf]

    Keim gegriffen                          0 von 120
    Schluesselpaare (gesucht -> veroeffentlicht)
      'None' -> 'eig:*' 58x | 'cube' -> 'eig:*' 13x | 'L' -> 'eig:*' 12x
      'neu-285' 9x | 'neu-9' 7x | 'U' 7x | 'neu-34' 5x | 'neu-369' 3x | 'neu-13' 3x

    Kandidaten beim Trackerstart      1: 103 | 2: 15 | 3: 2      -> mehrdeutig in 17 = 14,2 %

    Startgenauigkeit
      1 Kandidat    n = 103   Start falsch  1 =  1,0 %   geliefert 62/103 = 60,2 %
      >1 Kandidat   n =  17   Start falsch  7 = 41,2 %   geliefert  5/17  = 29,4 %

    Ausgang nach Startgenauigkeit
      Start falsch   0 von 8 geliefert
      Start richtig 67 von 112 geliefert
      Fisher exakt p = 0,0011

    die acht Fehlstarts (Endabstand)
      Ep  18 obj_blue  3 Kand. -> obj_U     ( 22 mm), eigenes  54 mm | fremd 100,0 % |  53 mm
      Ep  51 obj_U     2 Kand. -> obj_blue  (  1 mm), eigenes 143 mm | fremd  99,9 % | 243 mm
      Ep  53 obj_T     2 Kand. -> obj_blue  (  0 mm), eigenes 152 mm | fremd  99,6 % | 222 mm
      Ep  64 obj_green 1 Kand. -> obj_L     ( 11 mm), eigenes  30 mm | fremd   1,4 % | 147 mm
      Ep  65 obj_green 2 Kand. -> obj_L     ( 12 mm), eigenes  22 mm | fremd  96,3 % |  75 mm
      Ep  97 obj_red   2 Kand. -> obj_green (  1 mm), eigenes 113 mm | fremd  99,9 % | 228 mm
      Ep 117 obj_green 2 Kand. -> obj_red   (  1 mm), eigenes 154 mm | fremd  99,9 % | 111 mm
      Ep 119 obj_green 2 Kand. -> obj_red   (  1 mm), eigenes 154 mm | fremd  99,9 % |  76 mm

# Bewertung

* **Der Fehler ist total, die Gelegenheit selten.** Der Keim greift nie - aber in 103 von 120
  Episoden steht nur **ein** Blob der gesuchten Klasse im Bild, und dann trifft auch ein blinder
  Griff. Schaden entsteht nur in den 14,2 % mehrdeutigen Szenen.
* **Dort ist es ein Muenzwurf.** 41,2 % Fehlstart bei meist zwei Kandidaten ist genau das, was
  eine Wahl ohne Ortsanker vorhersagt.
* **Ein Fehlstart ist ein Totalverlust.** 0 von 8 geliefert, Endabstaende 53 bis 243 mm, und der
  Belief bleibt zu 96-100 % der Anfahrt auf dem falschen Koerper. Er korrigiert sich nicht.
* **Die Haeufigkeit deckt sich unabhaengig.** 8 von 120 = 6,7 % verlorene Episoden gegenueber
  6,8 % Episoden mit erster Anfahrt > 80 mm im 932-Episoden-Lauf
  ([Ablenker-Bindung](/befunde/ablenker-anfahrt.md)) - zwei getrennte Messungen, dieselbe
  Groessenordnung.
* **Ep 64 gehoert nicht dazu.** Dort stand nur ein Kandidat, und der war selbst eine
  Fehldetektion (11 mm neben obj_L). Ein Keim haette das nicht verhindert - andere Ursache,
  nicht mitzaehlen.

# Was eine Reparatur brächte - geschaetzt, nicht gemessen

Sieben der acht Fehlstarts sind mehrdeutige Faelle und waeren mit Keim vermeidbar. Bei der
Grundquote der sauberen Starts (59,8 %) waeren das rund **4 zusaetzliche Lieferungen auf 120
Episoden, also etwa 3,5 Punkte**. Das ist eine **Hochrechnung aus dieser Messung**, kein
Ergebnis: ob die geretteten Episoden tatsaechlich wie die uebrigen liefern, ist unbekannt.

# Nachtrag 2026-09-09: gebaut und gemessen

Die Reparatur steht hinter `ACT23_KEIM_FIX` (Vorgabe 0) und wirkt: Fehlstarts unter mehrdeutigen
Szenen 51,5 -> 6,7 % (p = 0,0001, gepaart ueber zwei Seeds). Die unten geschaetzten ~3,5 Punkte
Lieferquote haben sich **nicht** bestaetigt (gepoolt +2,5 Punkte, p = 0,65). Siehe
[Keim-Fix, A/B](/befunde/keim-fix-ab.md).

# Die Reparatur, die ich vorschlagen wuerde

`make_shape_track` einen eigenen `seed_key`-Parameter geben, Vorgabe `seed_key=key` - damit
bleibt jeder bestehende Pfad unveraendert - und im Eigenschafts-Zweig `seed_key=f"eig:{body}"`
uebergeben.

Warum nicht einfach unter der Formklasse veroeffentlichen: der Schluessel `"cube"` waere
mehrdeutig, sobald zwei Koerper dieselbe Formklasse tragen - und genau das ist der Fall, der hier
schiefgeht. Die Identitaet `eig:{body}` ist die einzige, die den gemeinten Koerper wirklich
benennt.

**Das ist ein Eingriff in den Wahrnehmungspfad und gehoert danach durch ein
[kopfloses A/B](/messungen/act23-headless-ab.md)** - mit der Einschraenkung, dass nur ~14 % der
Episoden ueberhaupt betroffen sind, der Effekt also klein gegen die Nachweisgrenze von 26 Punkten
je 50er-Fenster ist ([Rechnerlast](/befunde/rechnerlast.md)). Belastbarer als die Quote waere
hier die **direkte** Zielgroesse: der Anteil falscher Trackerstarts unter den mehrdeutigen
Szenen, den `ACT23_KEIMDIAG` misst.

# Verwandt

* [Der Tracker rastet auf dem Nachbarn ein](/befunde/ablenker-bindung-gemessen.md) - die Messung davor
* [Ablenker-Bindung in der Anfahrt](/befunde/ablenker-anfahrt.md) - der Ausgangsbefund
* [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) - die "vier Stellen", jetzt fuenf
