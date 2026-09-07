---
type: Mechanismus
title: Lebenszyklus einer selbst geborenen Formklasse
description: Geburt aus drei einigen Sichtungen, namenloses Fenster, Bindung an einen Koerper, Anspruchsradius, Verhungern, Einfrieren bei 80 Exemplaren. Wo der Weg von der Sichtung zum Kommando abreisst.
tags: [act23, formklassen, aneignung]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-07T00:00:00Z }
verified: { by: human:thomas, at: 2026-09-02T17:37:00Z }
sources:
  - id: chronik
    resource: /chronik/act23.md
    title: act23-Chronik, Eintraege 2026-08-15 bis 2026-09-04
---

# Die Kette

    Sichtung -> NEUARTIG (kNN-Abstand > novel_th = 7,72)
             -> GEBURT   (NOVEL_CONFIRM = 3 raeumlich konsistente Sichtungen)
             -> KANDIDAT (namenloses Fenster)
             -> BINDUNG  (3 von 6 Blicken wieder auf demselben Koerper)
             -> KNOPF / kommandierbar
    parallel: ANSPRUCH je Blick (relaxierter Radius OPEN_MARGIN = 1,6 x novel_th = 12,34)
              VERHUNGERN (STARVE_N = 25 Blicke ohne Treffer, sofern <= 6 Exemplare)
              KAPPUNG bei OPEN_CAP = 80 Exemplaren

# Geburt und Bindung

**Die Geburt verlangt drei Sichtungen, die sich einig sind - also alle vom selben Fleck.** Die
junge Klasse ist damit **ortsgebunden** und beansprucht ihr Objekt anderswo nur zu 47 % (mit
drei Sichtungen von verschiedenen Orten: 91 %, Fremdansprueche durchgehend 0 %). Das ist die
Wurzel des Konsolidierungsproblems.

**Die Bindung war frueher der Engpass, nicht die Aneignung.** Aus demselben Kreuz wurden ZWEI
Klassen geboren - eine auf einem verschmolzenen Fleck (23 mm neben dem Objekt), eine auf dem
sauberen Kreuz. Die alte Bindung nahm die erste Klasse, die einmal innerhalb von 40 mm sass -
das **Gespenst**. Folge: alle Kreuz-Kommandos liefen ueber den privilegierten Rueckfall
(0/12 Formklassen-Treffer), waehrend die brauchbare Klasse ohne Knopf danebenlag. Gebundene
Klassen sind zudem vor dem Verhungern geschuetzt - die Fehlbindung schaltete genau die
Aufraeummechanik ab, die das Gespenst entfernt haette.

Fix (`ACT23_BIND_CONFIRM` / `_WIN`, `_try_bind`): die Geburt macht nur noch **Kandidat**; den
Knopf bekommt, wer in 3 von 6 Blicken wieder auf dem Objekt sitzt.

    Formklassen-Treffer bei obj_X   0/12 -> 8/16, p = 0,008
    Kosten: die Bindung faellt ~10 Episoden spaeter

# Das namenlose Fenster

Sweep ueber 8 Seeds: Geburt einer Kreuz-Klasse in **8 von 8** Laeufen (Ep 8-15), **sofort
gebunden in 0 von 8**. Das namenlose Fenster ist der Normalfall, im Mittel 4,8 Episoden
(Spanne 2-14).

Die Neugier darf eine noch namenlose Klasse ueben (`ACT23_NAMENLOS`) - voruebergehend
handhabbar, danach ausgetragen, kein Knopf. **Wiedererkennung 33 % -> 83 %** (p = 0,036,
gepaart, ein Seed-Paar).

Ein Entwurfsfehler dabei: "namenlos" hiess zuerst schlicht **ungebunden** - das trifft auch
uralte Klassen mit 50-80 Belegen. Die Neugier verschwendete ihre knappen Zuege daran.
Korrigiertes Kriterium: **noch ortsgebunden** (Spannweite der eigenen Belege < selbst gemessener
Radius 11,46). Gebunden 4/6 -> 6/6 ueber sechs Seeds; aber Seed 905 faellt 100 % -> 50 %, und
die Fenster werden **laenger** (3,2 -> 7,3 Ep) statt kuerzer. Ungemessen warum.

# Anspruch, Verhungern, Einfrieren

**Der grosszuegige Anspruchsradius ist gemessen noetig** - obj_T braucht den Rabatt selbst in
47,5 % seiner Sichtungen. Zudrehen halbiert die Erkennung des T. Der Quelltext nennt den Grund:
"young exemplar sets are sparse over poses".

**Die Verhungerungs-Arithmetik erzwingt das Ergebnis:**

    Ueberleben verlangt > 6 Exemplare in 25 Blicken. Exemplare kommen NUR aus Treffern.
      bei  4% Trefferrate -> 1,0 erwartete Treffer -> VERHUNGERT
      bei 10%             -> 2,5                   -> VERHUNGERT
      bei 28%             -> 7,0                   -> ueberlebt gerade
    Junge Klassen liegen bei 1-4% kumulativ. Etablierte: neu-9 33% | neu-285 33% | neu-34 25%

Henne und Ei: eine Klasse braucht Treffer, um Exemplare zu sammeln, und Exemplare, um Treffer zu
erzielen. Die Schwelle liegt fast genau dort, wo die ausgereiften Klassen liegen.

**Bei 80 Exemplaren friert eine Klasse ein** (`shape_classifier.py:642`, `OPEN_CAP`) - sie nimmt
nie wieder eines auf. Alle vier Klassen im Nutzerzustand stehen bei exakt 80; von 80 Eintraegen
sind nur 18-36 verschieden, und **85 % der verschiedenen Exemplare von neu-9 liegen weiter als
`novel_th` von JEDER frischen Sichtung**. Die Klassen sind breite veraltete Wolken - und eine
breite Wolke beansprucht alles in ihrer Naehe.

Auffrischung (`ACT_SHAPE_EX_REFRESH`, Vorgabe **AUS**) ersetzt bei Kapazitaet ein Duplikat.
Fassung 1 machte es **schlimmer** (gemessene Kaskade, siehe Fallen); Fassung 2 frischt nur bei
einem SICHEREN Anspruch auf und ist damit sicher, aber ohne Nutzennachweis - und sie war
zwischenzeitlich ein **Geburtenunterdruecker**.

# Fallen

* **Man kann eine falsch beanspruchende Klasse nicht dadurch reparieren, dass man sie mehr
  lernen laesst - sie lernt aus ihrem eigenen Irrtum.** Gemessen, 15 aufeinanderfolgende
  10-mm-Y-Sichtungen, Abstand zu neu-9:

        ohne Auffrischung   13,4 10,6 13,4 9,2 ... 9,5 10,9   -> 11,2 auf 10,3   STABIL
        MIT Fassung 1       13,4  7,5  3,0 4,4 ... 4,4  5,1   ->  7,0 auf  4,2   KOLLABIERT

* **Bei jeder Aneignungsmessung zuerst pruefen, OB die gemessene Klasse die ist, die auf dem
  Objekt sitzt.** Eine Aneignungskurve verfolgte das Gespenst und beschrieb einen Fleck, den es
  einmal gab - nicht das Lernverhalten.
* **Paarabstaende modellieren eine Klasse mit EINEM Beleg.** Mit 3 Belegen ist der min-Abstand
  viel kleiner (6,5 statt 9,0). Der kNN-Abstand haengt massiv an der Belegzahl: n=3 -> 15,0,
  n=20 -> 9,6, n=2500 -> 3,3.
* **Erfolg und Misserfolg haben unterschiedliche Logformate** - "obj_X via Formklasse:" gegen
  "obj_X: Formklasse NICHT gefunden". Ein Muster mit "obj_X:" zaehlt nur die Misserfolge.
* **Zwei Aenderungen an derselben Maschinerie zwischen zwei Messungen, und die zweite Messung
  ist nicht mehr an die erste anschliessbar.** Wer eine Kette von A/Bs faehrt, darf die Vorgaben
  zwischendrin nicht verschieben - auch nicht "sichere" Verbesserungen ohne Nutzennachweis.

# Wo der naechste Versuch ansetzen muesste

**An der Geburt, nicht am Anspruch.** Eine Klasse aus 3 Sichtungen EINER Lage ist von vornherein
zu eng; zwei Fassungen einer Wache am Anspruchstor sind gemessen gescheitert. Denkbar: Geburt
erst nach Sichtungen aus mehreren Lagen, oder die Geburtsbelege ueber die bekannte Ausrichtung
(`_yaw_from(F)`) auf verschiedene Lagen verteilen. Ungeprueft. Siehe auch
[latente Augmentierung](/fragen/latente-augmentierung.md).

# Verwandt

* [Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md)
* [Aneignung neuer Formen](/befunde/aneignung-neuer-formen.md)
* [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md)
* [Formfaktorisierung](/befunde/formfaktorisierung.md)
