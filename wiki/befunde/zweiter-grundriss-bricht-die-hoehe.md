---
type: Befund
title: Die zweite Auflage bricht den Hoehenschaetzer - die Hoehe ist nur LESBAR, wenn der Grundriss bekannt ist
description: Die angekuendigte Bewaehrungsprobe, und sie faellt durch. Ein Schaetzer, der nur 70-mm-Platten gesehen hat, liest eine 50er um 6,0 mm zu NIEDRIG und faellt auf die Grundrate zurueck. Schlimmer - auch ein Schaetzer, der BEIDE Grundrisse gesehen hat, bleibt bei 33 Prozent, also bei der Grundrate. Der Grund ist beziffert: die scheinbare Flaeche schwankt mit dem Grundriss um das 7,5-fache dessen, was die Hoehe bewirkt (685 gegen 91). Keine der aufgezeichneten Bildgroessen trennt beides - auch das vergroesserungsfreie Formverhaeltnis nicht. Aber je Grundriss EINZELN funktioniert es unveraendert (68 und 77 Prozent), und damit ist der Ausweg benannt: die Hoehe ist keine Funktion des Bildes, sondern des Bildes GEGEBEN die Identitaet der Auflage.
tags: [act23, stapeln, wahrnehmung, hoehe, negativ, uebertragung]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-20T00:00:00Z }
sources:
  - id: sonde2
    resource: "Sonde auf einer Kopie von act23_state.pkl (ad9d768c): zwei Auflagen allein auf dem Tisch (70 x 70 und 50 x 50 mm, gleiche Farbe, gleiche Bauart), je 30 Rasterstellen x Hoehen 6/10/14 mm, je eine Detektion aus perceive_all, 180 Zeilen, keine fehlende Detektion"
    title: Die Zwei-Grundriss-Sonde
  - id: vorher
    resource: /befunde/oberkante-ohne-privileg.md
    title: Der Befund, dessen benannte Grenze hier gemessen wird
---

# Die angekuendigte Probe

[Die Oberkante ohne Privileg](/befunde/oberkante-ohne-privileg.md) endete mit einer
ausdruecklichen Grenze:

> *Alle Auflagen sind 70 x 70 mm. Die Flaeche traegt die Hoehe nur deshalb; eine kleinere Platte
> derselben Hoehe laese wie eine tiefere. Die zweite Auflage anderen Grundrisses ist die
> eigentliche Bewaehrungsprobe und ausdruecklich ungemessen.*

Jetzt ist sie gemessen. **Sie faellt durch, und haerter als vorhergesagt.**

Dazu steht eine zweite Platte in der Welt (`sockel2`, 50 x 50 mm) - **gleiche Farbe, gleiche
Bauart, einziger Unterschied der Grundriss.** Eine zweite Farbe waere ein zweiter Unterschied
gewesen und haette jede Aussage mehrdeutig gemacht.

# Was das Bild zeigt

    Grundriss   Hoehe   Flaeche   Dicke   Flaeche/Dicke^2
        50 mm    6 mm       704     9,5         8,09
        50 mm   10 mm       741    10,0         7,59
        50 mm   14 mm       778    10,0         7,91
        70 mm    6 mm      1372    13,0         8,28
        70 mm   10 mm      1425    13,5         7,91
        70 mm   14 mm      1479    13,5         7,98

Die Hoehe hebt die Flaeche um **91**, der Grundriss um **685**. Das ist der ganze Befund in zwei
Zahlen: **der Grundriss wirkt 7,5-mal so stark wie die Hoehe auf dieselbe Messgroesse.**

# (a) Uebertragung: der Schaetzer liest die kleine Platte 6 mm zu niedrig

Ein Schaetzer, der **nur** 70er Platten gesehen hat:

    angewendet auf 70 mm   Fehler Median +0,03 mm   |Fehler| 1,24 mm   richtige Stufe 81 %
    angewendet auf 50 mm   Fehler Median -6,00 mm   |Fehler| 6,00 mm   richtige Stufe 33 %  (= Grundrate)

**-6,00 mm ist kein Fehler, sondern ein Zusammenbruch.** Die Hoehen liegen zwischen 6 und 14 mm;
der Schaetzer haengt die kleine Platte unten an den Anschlag seines gesehenen Bandes. Die
Vorhersage aus der Geometrie stimmt in Richtung und Groesse.

# (b) Und BEIDE zu sehen hilft nicht

Das war die Ueberraschung. Naheliegend waere: zeig ihm beide Grundrisse, dann lernt er es.

    trainiert auf beiden, ohne zu wissen welcher   |Fehler| 3,38 mm   richtige Stufe 33 %
    Grundrate (immer die mittlere Stufe)           |Fehler| 4,00 mm   richtige Stufe 33 %

**Nichts.** Mehr Daten machen es nicht besser, sie machen es unmoeglich: in einem Topf sind
Grundriss und Hoehe in der Flaeche ununterscheidbar vermengt, und der Schaetzer lernt den
Mittelwert.

# (c) Keine Bildgroesse trennt Grundriss und Hoehe

Gesucht war eine Groesse, die den Grundriss verraet, ohne an der Hoehe zu haengen. Der beste
Kandidat war **`Flaeche / Dicke^2`**: die Flaeche waechst mit dem Quadrat der Vergroesserung, die
Dicke linear, das Verhaeltnis ist also vergroesserungsfrei - und wenn die Hoehe ueber die
sichtbare SEITENWAND wirkt (eine hohe Platte zeigt mehr Flanke), muesste sie sich dort zeigen.

                  Hub durch die Hoehe    Hub durch den Grundriss
    Flaeche            +91                    +686
    Dicke               +0,5                    +3,0
    Flaeche/Dicke^2     -0,24                   +0,26
    Farbstreuung        +0,00                   -0,00

Das Formverhaeltnis reagiert auf beides **gleich stark** - es trennt nichts, es mischt nur anders.
Die Farbstreuung sieht den Unterschied gar nicht. **Es gibt in diesen Groessen keinen Kanal fuer
den Grundriss allein.**

# Aber je Grundriss EINZELN ist alles beim Alten

    50 mm allein   |Fehler| 1,28 mm   richtige Stufe 68 %
    70 mm allein   |Fehler| 1,31 mm   richtige Stufe 77 %

**Das ist der Schluessel.** Der Befund ist nicht "die Hoehe steckt doch nicht im Bild" - sie
steckt dort, und zwar bei BEIDEN Platten gleich gut. Sie steckt nur nicht im Bild **allein**.

Und der Ausweg ist gemessen, nicht geraten:

    beide zusammen, ohne Grundriss                    33 %
    beide zusammen, Grundriss als Eingabe             49 %
    beide zusammen, Flaeche/Grundriss^2 statt Flaeche 59 %
    je Grundriss ein eigener Schaetzer             68 / 77 %

Je mehr die Rechnung von der Identitaet der Auflage weiss, desto besser wird sie - und sie wird
erst ganz gut, wenn jede Auflage ihren eigenen Schaetzer hat. Dass die Zwischenstufen nicht
heranreichen, ist erklaerbar: der Zusammenhang ist **multiplikativ** (Flaeche geht mit dem Quadrat
des Grundrisses), und ein lineares Modell in (Flaeche, Grundriss) kann das nicht darstellen.

# Der Ausweg, und warum er kein Privileg ist

> **Die Hoehe ist keine Funktion des Bildes, sondern des Bildes GEGEBEN die Identitaet der
> Auflage.**

Diese Identitaet hat der Agent bereits: er hat die Auflage in derselben Episode **adressiert**,
ueber seine eigene Wahrnehmung. Ein Schaetzer je adressierter Auflage braucht nichts Neues von
aussen.

**Und der Zirkelschluss, den man hier fuerchten muss, ist gemessen keiner.** Die Identitaet laeuft
ueber das Groessenband, das Band kommt aus der scheinbaren Flaeche - und die haengt auch an der
Hoehe. Aber genau das Zahlenverhaeltnis, das die Hoehe unlesbar macht, macht die Identitaet
sicher: **685 gegen 91.** Ein Band, das die Hoehenschwankung von 91 verschluckt und trotzdem 739
von 1425 trennt, ist bequem zu finden. Was hier schadet, hilft dort.

# Fallen

* **`ebene: pruefstand`.** Kein act23-Lauf. Die Sonde sagt, welche Information im Bild ist; sie
  sagt nicht, was ein Lauf tut ([Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)).
* **Was hier NICHT widerlegt wird:** [Die Oberkante ohne Privileg](/befunde/oberkante-ohne-privileg.md)
  bleibt gueltig - **fuer eine Welt mit einer Auflagenform.** Sie hat diese Grenze selbst benannt;
  sie ist jetzt beziffert, nicht gestuerzt.
* **Die kleine Platte ist mechanisch schwerer zu treffen.** Ihre geometrische Toleranz ist
  25 - 12 = 13 mm, die gemessene Ablagegenauigkeit liegt bei 20-25 mm. Ein Quotenvergleich
  70er gegen 50er im Lauf misst deshalb die **Mechanik**, nicht die Wahrnehmung. Ein sauberer
  act23-Vergleich muss BEIDE Arme auf DERSELBEN Platte fahren und nur das Wissen des Schaetzers
  unterscheiden.
* **Zwei Grundrisse sind zwei Punkte.** Dass ein Schaetzer je Auflage traegt, ist an zwei Platten
  gezeigt; ob er auf die dritte uebertraegt - also ob der Agent fuer jede neue Auflage von vorn
  sammeln muss - ist damit nicht beantwortet und ist die naechste Frage.
* **Die XML hat einen Koerper mehr.** Nach [Invarianten](/mechanismen/invarianten.md) veraendert
  das die Renderung. Zahlen von vor `sockel2` sind nicht zeichengenau mit spaeteren vergleichbar;
  die 70-mm-Spalten dieser Sonde reproduzieren die
  [erste Sonde](/befunde/hoehe-steckt-in-der-wahrnehmung.md) aber ziffernnah (1372/1425/1479 gegen
  1372/1425/1479), weil die zweite Platte geparkt ist.

# Verwandt

* [Die Oberkante ohne Privileg](/befunde/oberkante-ohne-privileg.md) - der Befund, dessen Grenze hier gemessen ist
* [Die Hoehe steckt in der Wahrnehmung](/befunde/hoehe-steckt-in-der-wahrnehmung.md) - die erste Sonde, eine Auflage
* [Die Adresse ohne Klasse](/mechanismen/adresse-ohne-klasse.md) - woher die Identitaet der Auflage kommt
* [Die Relation "auf" gebaut](/mechanismen/relation-auf-gebaut.md) - `state.STUETZEN`, jetzt zwei
* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - Stufe 3
