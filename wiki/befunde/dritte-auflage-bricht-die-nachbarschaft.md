---
type: Befund
title: Die dritte Auflage bricht die Nachbarschaft - der lokale Schaetzer skaliert nicht, und eigene Zeilen helfen nicht
description: Eine dritte Auflagenform (60 mm, genau zwischen den bekannten 50 und 70) laesst den lokalen Hoehenschaetzer von 92 auf 62 Prozent fallen, auf der neuen Platte auf 48. Das Verblueffende - ihr EIGENE Zeilen zu geben hilft nicht (0 bis 45 Zeilen: 33 bis 42 Prozent), obwohl ihr Signal allein trainiert perfekt ist (100 Prozent, 0,41 mm). Die Ursache ist beziffert und liegt nicht bei den Daten, sondern bei der Auswahl: rund 12 Prozent fremde Nachbarn, die 5- bis 8-mal weiter weg liegen als der naechste eigene und deshalb eine Zehn-Punkt-Ausgleichsrechnung per Hebelwirkung beherrschen. Mit grundrissreinen Nachbarn waeren es 86/98/98 Prozent. Vier Abhilfen gemessen, keine uebernommen. Korrigiert meine eigene Verallgemeinerung vom Vortag.
tags: [act23, stapeln, hoehe, wahrnehmung, negativ, uebertragung]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-21T00:00:00Z }
sources:
  - id: sonde3
    resource: "Sonde auf einer Kopie von act23_state.pkl (ad9d768c): drei Auflagen einzeln auf dem Tisch (70, 60, 50 mm, gleiche Farbe und Bauart), je 30 Rasterstellen x Hoehen 6/10/14 mm, 270 Zeilen, keine fehlende Detektion. Alle Auswertungen stellenweise gehalten."
    title: Die Drei-Grundriss-Sonde
  - id: vorher
    resource: /befunde/lokaler-schaetzer-im-lauf.md
    title: Der Befund, dessen offene Frage hier beantwortet wird
---

# Die offene Frage

[Der lokale Hoehenschaetzer haelt im Lauf](/befunde/lokaler-schaetzer-im-lauf.md) schloss mit:

> *Ob der lokale Schaetzer eine DRITTE Auflagenform aufnimmt, ohne fuer sie von vorn sammeln zu
> muessen, ist die naechste Frage und ungemessen.*

Die dritte Platte ist **60 x 60 mm - genau zwischen den bekannten 50 und 70**, und das mit Absicht.
Ein lokales Modell holt seine Ebene aus den naechsten Nachbarn; bei 60 mm sind das Zeilen **beider**
bekannter Platten, also genau die Mischung, an der der globale Schaetzer zerbrochen ist. Eine 90er
oder 35er haette nur eine Nachbarschaft und waere die bequeme Frage gewesen.

**Vorhergesagt war: die Uebertragung ohne eigene Zeilen scheitert.** Sie scheitert. Aber der Rest
kam anders.

# Das Signal der neuen Platte ist perfekt

Bevor irgendetwas ueber Uebertragung gesagt wird: die 60er Platte ist fuer sich **leichter** zu
lesen als die beiden anderen.

    je Grundriss ALLEIN trainiert      |Fehler|    richtige Stufe
        50 mm                          0,74 mm        83 %
        60 mm                          0,41 mm       100 %
        70 mm                          0,45 mm       100 %

Was folgt, ist also kein Problem der neuen Platte.

# Und trotzdem: im Topf faellt alles

    im Topf mit allen dreien           |Fehler|    richtige Stufe
        50 mm                          1,26 mm        66 %
        60 mm                          2,16 mm        48 %
        70 mm                          1,04 mm        72 %
        gesamt                         1,33 mm        62 %

Zum Vergleich: mit **zwei** Platten waren es 92 % (0,73 mm). Die dritte Form kostet 30 Punkte, und
sie kostet sie **auch den beiden alten**.

## Eigene Zeilen helfen nicht - und das ist der eigentliche Befund

Die naheliegende Erwartung: die neue Platte braucht eben ein paar eigene Beispiele.

    eigene Zeilen der 60er     0      3      6     12     24     45
    richtige Stufe 60 mm      33 %   38 %   42 %   38 %   42 %   33 %
    richtige Stufe 50/70      90 %   88 %   88 %   88 %   79 %   77 %

**Nichts.** 45 eigene Zeilen aendern nichts an der neuen Platte und **verschlechtern die alten**.
Das Problem sind nicht die Daten.

# Die Ursache, beziffert

Der naechste Nachbar gleichen Grundrisses liegt bei 0,11-0,16 (standardisiert), der naechste
fremde bei 0,80-0,92 - **fuenf- bis achtmal weiter**. Trotzdem sind unter den 10 Nachbarn im
Schnitt 12 % fremde (60 mm: 88 % rein, 70 mm: 91 %, 50 mm: 96 %); mit nur zwei Platten waren es
**100 % rein**. Am Rand des Arbeitsraums sind eigene Nachbarn duenn gesaet, und dann ruecken fremde
nach.

> **Ein einziger fremder Punkt unter zehn genuegt.** Er liegt in der beherrschenden Richtung
> (Flaeche) rund eine ganze Streuung entfernt, und eine Ausgleichsrechnung ueber zehn Punkte mit
> fuenf Parametern hat gegen solche **Hebelwirkung** keinen Schutz.

Der Gegenbeweis mit einem Orakel - Nachbarn kuenstlich auf denselben Grundriss beschraenkt, was
der Agent nicht kann:

    Nachbarn                  50 mm    60 mm    70 mm
    gemischt (wie heute)       66 %     48 %     72 %
    grundrissrein (Orakel)     86 %     98 %     98 %

**Die Information ist vollstaendig da. Was fehlt, ist die Auswahl.**

# Vier Abhilfen gemessen, keine uebernommen

    Verfahren                       50 mm   60 mm   70 mm   gesamt
    heutige Fassung (hart, k=10)     66 %    48 %    72 %    62 %
    Aussehen zuerst, dann Ort        66 %    44 %    56 %    55 %
    robust: Abweichler wegwerfen     58 %    44 %    66 %    56 %
    kleinere Nachbarschaft (k=6)     64 %    70 %    76 %      -
    lokal GEWICHTET (tricube, k=10)  66 %    61 %    79 %    69 %

Die ersten beiden waren meine Hypothesen, und **beide sind schlechter als das, was schon da war**.
"Aussehen zuerst" waehlt zwar grundrissrein, presst die Nachbarschaft dann aber so eng im Ort
zusammen, dass der Daempfer den Fit auf den Mittelwert zieht.

Die Gewichtung (der Lehrbuchgriff gegen Hebelwirkung) hilft am meisten - **und wird trotzdem nicht
uebernommen**:

    an denselben Sonden        hart            gewichtet
    eine Auflage              100 % / 0,45 mm   98 % / 0,34 mm
    zwei Auflagen              92 % / 0,73 mm   89 % / 0,72 mm
    drei Auflagen              62 % / 1,33 mm   69 % / 1,12 mm

Sie verbessert nur den schwersten Fall und verschlechtert die beiden einfacheren - und 69 % sind
weit von den 94 % des Orakels entfernt. Das zu uebernehmen hiesse, an 270 Sondenzeilen anzupassen
und nebenbei die
[act23-Messung vom Vortag](/befunde/lokaler-schaetzer-im-lauf.md) zu entwerten, die mit der harten
Fassung gelaufen ist. **Der Code bleibt, wie er ist.**

# Was ich am Vortag zu weit gesagt habe

Auf [Die zweite Auflage bricht den Hoehenschaetzer](/befunde/zweiter-grundriss-bricht-die-hoehe.md)
steht:

> *Ein Modell, das seine Ebene nur aus der NACHBARSCHAFT legt, wird dadurch von selbst zu einem
> Modell je Grundriss, ohne dass ihm jemand sagt, dass es zwei gibt.*

**Das gilt nicht als Prinzip, sondern nur solange die Formen weit auseinanderliegen.** Bei zwei
Platten war die Nachbarschaft zu 100 % rein, bei dreien nur noch zu 88 %, und diese 12 % genuegen.
Der Satz ist auf der dortigen Seite entsprechend eingeschraenkt.

Die Messungen dort bleiben gueltig; die **Verallgemeinerung** war meine, nicht die der Daten.

# Was das fuer die Welt heisst

`ACT23_SOCKEL_N=3` stellt alle drei Platten im Wechsel auf (Vorgabe 1; `ACT23_SOCKEL2=1` bleibt
gleichbedeutend mit 2). Der Rauchtest zeigt sauberen Wechsel und Adressen, die auf 4-6 mm treffen -
die **Adressierung** der dritten Platte ist kein Problem, nur ihre Hoehe.

`ACT23_HOEHE_SEHEN` mit drei Formen: **diese Warnung habe ich zurueckgenommen.** Sie stand hier
zuerst als "sollte nicht benutzt werden", gestuetzt allein auf die 48 % dieser Sonde. Der
[act23-Lauf](/befunde/drei-auflagen-im-lauf.md) zeigt, dass die Aufgabe das nicht merkt (85 gegen
88 % gestapelt, die neue Platte 7/7). Der Start meldet jetzt die Verschlechterung der SCHAETZUNG,
ohne vom Schalter abzuraten. Die Vorgabe bleibt 0.

# Fallen

* **`ebene: pruefstand` - und die act23-Gegenprobe ist inzwischen gefahren, auf Wunsch des
  Nutzers.** Meine Begruendung, sie lohne nicht, war zu pauschal: sie galt fuer die Stapelquote,
  nicht fuer den Schaetzfehler. **Das Ergebnis:
  [die Vorhersage trifft zifferngenau ein und ist folgenlos](/befunde/drei-auflagen-im-lauf.md)** -
  45 % richtige Stufe gegen die hier vorhergesagten 48 %, und die Stapelquote bleibt bei 85 gegen
  88 %. Die Fehlschlaege sind seitlich (Versatz 65 gegen 15 mm), der Hoehenfehler ist bei
  gelungenen und misslungenen Stapeln gleich gross. **Die Messgroesse dieser Seite loest feiner
  auf als die Aufgabe.**
* **60 mm ist der schwerste Fall, nicht der typische.** Eine Form weit ausserhalb der bekannten
  haette nur eine Nachbarschaft. Wie stark der Bruch von der LAGE der neuen Form abhaengt, ist
  nicht gemessen.
* **Das Orakel ist kein Weg.** "Nachbarn gleichen Grundrisses" setzt voraus, den Grundriss zu
  kennen - genau das, was der Agent nicht kann (die Groessenachse saettigt bei Moebeln, s. die
  [zweite Auflage](/befunde/zweiter-grundriss-bricht-die-hoehe.md)). Es beziffert die Obergrenze,
  mehr nicht.
* **Drei Punkte sind drei Punkte.** Ob der Bruch bei vier Formen weitergeht oder sich bei dichter
  Belegung wieder schliesst (dann waeren die Nachbarn wieder ueberwiegend eigene), ist offen.

# Verwandt

* [Der lokale Hoehenschaetzer haelt im Lauf](/befunde/lokaler-schaetzer-im-lauf.md) - die offene Frage, die hier beantwortet wird
* [Die zweite Auflage bricht den Hoehenschaetzer](/befunde/zweiter-grundriss-bricht-die-hoehe.md) - dort steht die Verallgemeinerung, die hier eingeschraenkt wird
* [Die Hoehe steckt in der Wahrnehmung](/befunde/hoehe-steckt-in-der-wahrnehmung.md) - die erste Sonde
* [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) - warum hier keine Wirkungsaussage steht
* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - Stufe 3
