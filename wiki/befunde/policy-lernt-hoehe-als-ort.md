---
type: Befund
title: Die Policy lernt die Ablagehoehe - aber als Ort, nicht als Hoehe, und auf Kosten der Tischablage
description: Frage 2, gemessen als kontrafaktische Probe am Netz ueber vier Zwischenstaende eines 100-Episoden-Stapellaufs. Die Policy trifft die Stapelhoehe in ihrer eigenen Verteilung auf 4,6 mm. Aber die Spalte 14 allein verschiebt ihre Zielhoehe um +25 mm statt +8 - weil der Sockel immer an derselben Stelle steht, ist die Spalte vollstaendig mit dem Zielort verwechselt. Und die Stapeldaten verdraengen die Tisch-Erfahrung aus dem Puffer bis auf den geschuetzten Kern: die normale Absenkung auf den Tisch liegt zwischenzeitlich 12-15 mm zu hoch.
tags: [act23, stapeln, policy, dagger, puffer]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-19T00:00:00Z }
sources:
  - id: lauf
    resource: "Ein kopfloser Lauf auf einer Kopie von act23_state.pkl (ad9d768c), 20 + 30 + 50 Episoden mit Seeds 4242/4243/4244, Teacher fahrend -- UNGEPRUEFT, s. Invarianten: nur mit ACT23_CHOREO=fsm zutreffend, sonst faehrt das Netz mit korrigiertem Etikett (409f7cc), ACT23_ZIEL_RELATION=auf, ACT23_EIG_DIREKT=1 ACT23_EIG_STETIG=1, Zwischenstaende ck000/020/050/100"
    title: Lernlauf Ablagehoehe
  - id: probe
    resource: "Offline am Netz: 470 echte Tisch-Absenkzustaende aus dem Originalpuffer als festes Probenset, 14. Spalte getauscht; dazu die eigenen Stapelzeilen jedes Zwischenstands"
    title: Kontrafaktische Probe
---

# Die Frage

Lernt die Policy, dass die Ablagehoehe vom Ziel abhaengt? Bisher fuhr beim Stapeln der Teacher,
und die Hoehe kommt als Teacher-Geruest aus dem Simulator. Die Vorbedingung war erst seit
[409f7cc](/befunde/teacher-widerspricht-dem-stapel.md) erfuellt - vorher war die Hoehe fuer die
Policy per Bauart unlernbar.

# Der Aufbau

Ein Lauf, 100 Episoden in drei Abschnitten (20 + 30 + 50), **der Teacher faehrt**, die Policy lernt
lifelong aus seinen Etiketten. Gemessen wird danach offline am Netz, **ohne Freeze**, weil jede
Probe ein reiner Vorwaertsdurchlauf ist:

* **kontrafaktisch:** 470 echte Absenkzustaende aus dem Originalpuffer, nur die 14. Spalte
  getauscht (Tisch gegen Sockel, +8 mm) - wie stark reagiert die Zielhoehe auf die Spalte allein?
* **in der eigenen Verteilung:** die echten Stapel-Absenkzeilen jedes Zwischenstands gegen ihr
  Etikett.
* **die alte Aufgabe:** dieselben 470 Tischzustaende mit ihrer ECHTEN Spalte gegen das
  Tisch-Etikett.

Vor Stapeldaten ist die kontrafaktische Antwort **exakt 0**, und das ist nicht Glueck, sondern
Bauart: eine im Puffer konstante Spalte hat nach der Normierung ueberall den Wert 0, ihr Gradient
ist 0, ihre Gewichte bleiben null. Deshalb braucht es keinen Kontrollarm. (Die naheliegende Sorge,
eine konstante Spalte bekomme den Normierer 1e-6 und explodiere dann bei 22 mm auf das 8000fache,
haelt aus genau diesem Grund nicht: 8000 mal ein Gewicht von exakt null ist null.)

# Zahlen

    Stand | Stapelzeilen  Absenkung | kontrafaktisch delta aim_z | eigene Stapelzeilen
          |                         |   Median   p10    p90 >4mm |  Netz  /  Etikett
    ck000 |       0          0      |   +0,0     +0,0  +0,0   0% |     -
    ck020 |    8874        717      |  +22,6     +0,9 +24,5  88% |  28 / 26 mm
    ck050 |   13731       1316      |  +25,7     +5,3 +28,0  92% |  30 / 26 mm
    ck100 |   15905        571      |  +25,7     -1,0 +29,5  87% |  28 / 26 mm

    Soll kontrafaktisch: +8 mm

**Die Policy reagiert auf die Spalte, und zwar nach 20 Episoden.** In ihrer eigenen Verteilung trifft
sie die Stapelhoehe gut: bei ck100 Etikett 25,6 mm, Netz 28,3 mm, **|Fehler| im Median 4,6 mm**.

**Aber die Spalte allein bewegt die Zielhoehe um +25 mm statt +8** - das Dreifache.

# Warum: die Spalte ist mit dem Ort verwechselt

    Zielort der Pufferzeilen bei ck100
      Stapelzeilen  n = 15905   x -19,8 +- 6,5 mm   y 151,9 +- 8,7 mm
      Tischzeilen   n =  8095   x  -5,4 +- 16,8 mm  y 109,2 +- 1,6 mm

Der Sockel steht in jeder Episode an derselben Stelle `(-18 | 149)`. Die 14. Spalte ist deshalb
**vollstaendig mit dem Zielort verwechselt** - es gibt keine einzige Zeile, in der das eine ohne das
andere vorkommt. Das Netz kann nicht wissen, ob die Hoehe von der Spalte abhaengt oder vom Ort,
und es hat etwas gelernt, das beides mischt. Die kontrafaktische Probe setzt die Spalte an Orten,
an denen nie ein Sockel stand - ausserhalb dessen, was das Netz je gesehen hat.

> **Die Policy hat die Stapelhoehe gelernt, aber nicht als Funktion der Auflagenhoehe, sondern als
> Eigenschaft einer Situation: "dort, in dieser Art Episode, hoeher ablegen".** Mit einem festen
> Sockel laesst sich das eine vom anderen gar nicht trennen.

# Und es kostet die alte Aufgabe

    Stand | Tischzeilen im Puffer | Tisch-Absenkung: Netz  |Fehler| Med | alle Phasen |Fehler| Med
    ck000 |        24000          |       22,7 mm           4,7 mm    |          2,8 mm
    ck020 |        15126          |       34,8 mm          16,8 mm    |          3,9 mm
    ck050 |        10269          |       37,7 mm          19,7 mm    |          6,7 mm
    ck100 |         8095          |       25,9 mm           7,9 mm    |          5,4 mm

    Tisch-Etikett der Absenkung: 18 mm

**Bei der gewoehnlichen Ablage auf den Tisch senkt die Policy nach 20-50 Stapel-Episoden 12-15 mm
zu hoch ab.** Sie hat "weniger tief absenken" aus den Stapeldaten auf die alte Aufgabe uebertragen.

Die Ursache steht in der ersten Spalte: **100 Stapel-Episoden haben die gesamte uebrige
Tisch-Erfahrung aus dem Puffer verdraengt.** Der Puffer fasst 24000 Zeilen, davon sind die ersten
8000 geschuetzt (`CORE`). Die uebrigen 16000 werden der Reihe nach ueberschrieben - nach 100
Episoden ausschliesslich mit Stapeldaten. Was an Tisch-Erfahrung bleibt, ist der Kern, und der
stammt aus einer fruehen Phase mit fast festem Zielort (y 109 +- 1,6 mm).

Bei ck100 erholt sich der Tischfehler teilweise (7,9 mm). Ob das eine Stabilisierung ist oder
Zufall eines Zwischenstands, sagt eine Messung mit vier Punkten nicht.

> **NACHTRAG 2026-09-19:** die Folge fuer die Tischablage ist NICHT sicher belegt. Im gemischten
> Lauf schwankt derselbe Fehler auf den aktuellen Tischzeilen zwischen 3,0 und 14,6 mm, ohne
> stetigen Trend ([Gemischt lernen](/befunde/gemischt-lernen-erster-lauf.md)). Die 12-15 mm oben
> sind auf ALTEN Zustaenden gemessen und koennen ebenso Refit-Unruhe sein. Belegt bleibt die
> Verdraengung selbst (24000 -> 8095 Tischzeilen).

# Was daraus folgt

Zwei Konstruktionsfehler des Lernlaufs, beide mit klarer Abhilfe:

1. **Der Sockel muss wandern.** Solange er fest steht, ist Hoehe gleich Ort. Mit wechselnder
   Sockelstelle je Szene ist die 14. Spalte der einzige verlaessliche Hinweis auf die Hoehe - erst
   dann kann die kontrafaktische Probe +8 mm zeigen, wenn es gelernt ist. Besser noch: Sockel
   verschiedener Hoehe, damit die Spalte mehr als zwei Werte annimmt.
2. **Aufgaben mischen statt ersetzen.** Ein Lauf aus 100 % Stapel-Episoden verdraengt die alte
   Aufgabe aus dem Puffer; ein Kind, das stapeln lernt, hoert auch nicht auf, Dinge auf den Tisch zu
   legen. Etwa die Haelfte der Episoden mit Marker-Ziel wuerde beide Verteilungen im Puffer halten.

**Was hier NICHT gemessen ist:** das Verhalten. Die Probe sagt, was die Policy ausgeben WUERDE; ob
sie, selbst fahrend, stapelt, ist ein `ACT23_CHOREO=netz`-Lauf und steht aus.

# Fallen

* **`ebene: pruefstand`.** Gemessen ist das Netz, nicht der Arm.
* **Ein Lauf, ein Seed je Abschnitt.** Die Groessenordnungen (0 gegen +25 mm, 4,7 gegen 16-20 mm)
  tragen, die Zwischenstaende einzeln nicht.
* **Die "Stapelzeilen" umfassen die GANZE Episode**, nicht nur die Absenkung: die 14. Spalte steht
  eine Episode lang auf dem Sockelwert. Von 15905 Stapelzeilen gehoeren nur 571 zur Absenkung.
* **Die Absenkzeilen schwanken zwischen den Staenden** (717 / 1316 / 571), weil der FIFO-Puffer
  sie laufend ersetzt - die Probe misst jeweils die, die gerade drinstehen.
* **Das feste Probenset stammt aus dem Originalpuffer.** Es misst die alte Aufgabe so, wie sie vor
  dem Lauf aussah; nach ck050 steht keine einzige dieser Zeilen mehr im Puffer.

# Verwandt

* [Der Teacher widersprach dem Stapel](/befunde/teacher-widerspricht-dem-stapel.md) - die Vorbedingung, und der Messplan
* [Der Arm stapelt](/befunde/stapeln-gemessen.md) - Frage 2 stammt von dort
* [Imitationspuffer](/befunde/imitationspuffer.md) - die Nullsummen-Diagnose: jeder neue Eintrag verdraengt einen alten
* [Merkmale kommen zu spaet](/befunde/merkmale-kommen-zu-spaet.md) - dasselbe Pufferproblem von der anderen Seite
* [Die Relation "auf", gebaut](/mechanismen/relation-auf-gebaut.md) - `ACT23_SOCKEL_XY`, der bisher feste Ort
