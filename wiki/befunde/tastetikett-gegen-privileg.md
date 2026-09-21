---
type: Befund
title: Weniger Teacher kostet Genauigkeit und kostet der Aufgabe nichts - der ertastete Schaetzer stapelt wie der privilegierte
description: Das A/B zum Nutzerprinzip "weniger Teacher ist immer besser". Zwei Schaetzer, einer aus ERTASTETEN Etiketten, einer aus sim.m.geom_size, danach NUR der Schaetzer in denselben Basiszustand verpflanzt. Der ertastete ist 3,7-mal ungenauer (2,20 gegen 0,60 mm) und stapelt genauso gut - 15 von 16 gegen 17 von 19, p = 1,00. Die Fehlschlaege sind in beiden Armen seitlich (Versatz 94 und 156 mm gegen 12 und 23 mm). Enthaelt einen Scheinkontakt-Fehler, der Etiketten bis 17,9 mm verfaelschte, und die Methode, die ihn und einen verschwendeten Lauf gefunden hat - beide Artefakte VOR dem teuren A/B an einem vorhandenen Pruefsatz gegeneinanderhalten.
tags: [act23, stapeln, hoehe, privileg, tastsinn, teacher]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-21T00:00:00Z }
sources:
  - id: ab
    resource: "Vier kopflose Laeufe auf Kopien von act23_state.pkl (ad9d768c), Seed 7001, ACT23_CHOREO=fsm (Teacher fahrend), ACT23_SOCKEL_N=1: warm T 40 Ep mit ACT16_TASTEN=1 ACT23_HOEHE_TASTEN=1 (14 Tastwerte), warm P 40 Ep ohne Tasten (22 Zeilen); danach NUR der Schaetzer in denselben Basiszustand verpflanzt; dann Test T und Test P je 35 Ep mit ACT23_HOEHE_SEHEN=1 und abgeschaltetem Tasten"
    title: Das Etiketten-A/B
  - id: mech
    resource: /mechanismen/hoehe-ertasten.md
    title: Wie das Ertasten gebaut ist
  - id: wunsch
    resource: "Nutzer, 2026-09-21: 'Generell finde ich weniger teacher ist immer besser.'"
    title: Der Anlass
---

# Die Frage

[Die Auflagenhoehe ertasten](/mechanismen/hoehe-ertasten.md) hat gezeigt, dass das **Etikett**
stimmt. Offen blieb, ob ein daraus gelernter Schaetzer im Lauf **ankommt**.

# Der Aufbau, und warum er so aussieht

Die beiden Warmlaeufe unterscheiden sich nicht nur im Etikett, sondern auch im **Verhalten** - der
Tast-Arm faehrt bis zu 8 mm unter die Schaetzung. Danach unterscheiden sich Policy, Puffer und
Welt-Modell mit, und ein Testlauf maesse alles zusammen.

> Deshalb wird nach dem Warmlauf **nur der Schaetzer** in denselben Basiszustand verpflanzt. Im
> Test ist dann wirklich nur verschieden, was er gelernt hat.

Getestet wird mit **abgeschaltetem Tasten** - beide Arme fahren identisch, es entscheidet allein
die gelernte Schaetzung. Eine Auflagenform, weil der Schaetzer mit dreien ohnehin auf der
Grundrate liegt ([gemessen](/befunde/dritte-auflage-bricht-die-nachbarschaft.md)) und die
Etikettenfrage dort gar nicht sichtbar werden koennte.

# Ergebnis

                           Zeilen   Stapel            |Schaetzfehler|
    P  aus dem Privileg      22    17/19 = 89 %          0,60 mm
    T  aus der Beruehrung    14    15/16 = 94 %          2,20 mm

    Fisher: p = 1,00

**Der ertastete Schaetzer ist 3,7-mal ungenauer und stapelt genauso gut.** Das ist die Antwort auf
die Frage, und sie faellt zugunsten von "weniger Teacher" aus.

Die 94 gegen 89 % sind ausdruecklich kein Vorsprung - bei 16 und 19 Urteilen waere erst ein
Einbruch unter 9 von 16 (56 %) trennbar gewesen.

## Warum es der Aufgabe nichts ausmacht

                       |Schaetzfehler|      Versatz
    P  gelungen (16)        0,75 mm          12 mm
    P  misslungen (2)       0,55 mm          94 mm
    T  gelungen (15)        2,60 mm          23 mm
    T  misslungen (1)      10,00 mm         156 mm

Dasselbe Muster wie in [drei Auflagenformen](/befunde/drei-auflagen-im-lauf.md): **die
Fehlschlaege sind seitlich.** 94 und 156 mm Versatz sind Vorbeigriffe, keine Hoehenfehler - in P
haben die Fehlschlaege sogar den kleineren Hoehenfehler.

# Was das Etikett kostet, unabhaengig vom Lauf gemessen

Das Tast-Etikett gegen die Wahrheit, die nirgends eingeht (n = 13, nach dem Fehler unten):

    Median -0,60 mm    |Median| 1,10 mm    Streuung 2,60 mm

Und was dieses Rauschen einen Lerner kostet - 90 Sondenzeilen, stellenweise gehalten, das
Etikettenrauschen aus der **gemessenen** Verteilung gezogen:

    exakt (Privileg), 20 Zeilen      0,81 mm   86 % richtige Stufe
    ertastet,         20 Zeilen      1,66 mm   69 %

**Rund 20 Punkte.** Das ist der Preis, und er ist damit beziffert - unabhaengig davon, dass die
Aufgabe ihn nicht spuert.

# Der Fehler, der fast durchgegangen waere: Scheinkontakte

Die Ablagephase beginnt, sobald die Hand **seitlich** am Ziel ist - sie kann dann noch
zentimeterweit darueber stehen. In der ersten Fassung galt **jeder** Stillstand auf dem Weg nach
unten als Beruehrung.

    Tastetiketten VOR dem Fenster    n=20   Median +0,40   Streuung 5,79   Spanne -2,30..+17,90
    Tastetiketten NACH dem Fenster   n=13   Median -0,60   Streuung 2,60   Spanne -4,10.. +5,80

    was der Lerner daraus macht:     vorher 3,35 mm / 52 %     nachher 1,66 mm / 69 %

Ein einzelnes Etikett lag **17,9 mm** daneben, und das halbierte die Genauigkeit des Lerners. Die
Abhilfe ist ein Fenster um die Schaetzung, so weit, wie sie selbst danebenliegen kann.

# Die Methode, die das gefunden hat

Die erste Fassung dieses A/B lief mit drei Auflagenformen und war schon bis zu den Warmlaeufen
durch. **Vor** den Testarmen habe ich die verpflanzten Schaetzer gegen 270 vorhandene
Sondenzeilen gehalten - und alle lagen auf der Grundrate. Die 105 Minuten Testlauf haetten drei
gleich unbrauchbare Schaetzer verglichen.

> **Vor jedem teuren A/B die beiden Artefakte an einem vorhandenen Pruefsatz gegeneinanderhalten.
> Sind sie dort ununterscheidbar, kann es der Lauf auch nicht.**

Fuer die zweite Fassung war der Vorab-Check positiv (T 42 %, P 60 % gegen eine Grundrate von
33 %), und erst danach sind die Arme gelaufen.

# Fallen

* **Der Vorab-Check sagt den Lauf NICHT vorher, auch nicht der Groesse nach.** Auf dem Pruefsatz
  lag T bei 4,26 mm, im Lauf bei 2,20; P bei 1,78 gegen 0,60. **Der Lauf ist die guenstigere
  Welt** - er besucht wenige Stellen mehrfach, die Nachbarschaft ist dort dichter als im
  gleichmaessigen Raster. Der Check taugt zum **Aussortieren**, nicht zum Vorhersagen.
* **Ein Bias, der sich nicht bestaetigt hat.** Auf dem Pruefsatz las T systematisch 4,05 mm zu
  tief; im Lauf sind es 0,40 mm. Bei 14 Zeilen war das Stichprobenzufall. Ich hatte ihn vorher als
  Beobachtung notiert - richtig war, ihn nicht zu erklaeren.
* **n = 16 und 19 Urteile.** `p = 1,00` heisst nur "kein Unterschied, den dieser Lauf zeigen
  koennte". Die tragende Aussage ist nicht die Quote, sondern der Vergleich Hoehenfehler-gelungen
  gegen -misslungen und der Versatz.
* **Eine Auflagenform.** Mit dreien liegt jeder Schaetzer auf der Grundrate, egal woher sein
  Etikett kam - dieser Befund sagt nichts ueber jene Welt.
* **Das Tasten braucht die FSM-Choreographie** und ist eine Verhaltensaenderung (bis 8 mm unter
  die Schaetzung). Beide Schalter stehen auf Vorgabe 0.
* **Die Ausbeute bleibt der Preis:** 14 gegen 22 Zeilen aus je 40 Episoden. Weniger Teacher kostet
  hier Datenmenge, und bei einer Aufgabe mit engerer Hoehentoleranz koennte das allein schon
  entscheiden.

# Verwandt

* [Die Auflagenhoehe ertasten](/mechanismen/hoehe-ertasten.md) - wie das Etikett entsteht
* [Die Oberkante ohne Privileg](/befunde/oberkante-ohne-privileg.md) - der Schaetzer selbst
* [Drei Auflagenformen im Lauf](/befunde/drei-auflagen-im-lauf.md) - woher die Toleranz der Aufgabe bekannt ist
* [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) - der Vorab-Check ist ihr Gegenstueck, nicht ihre Widerlegung
* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - Stufe 3
