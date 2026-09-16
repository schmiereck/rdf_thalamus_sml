---
type: Befund
title: Die stetige Formachse ist genauso trennscharf wie die Klasse - sie ist nicht besser, sondern ein anderer Punkt auf derselben Tauschkurve
description: Auf denselben echten Laufszenen, mit identischer Wuerfelei und Aufloesung, nur die Matching-Regel getauscht: Klassenname gegen Abstand im Einbettungsraum. Ueber fuenf Toleranzen bleiben die groben Adressierungsfehler flach bei 4,9 bis 6,7 Prozent, keine davon vom diskreten Bezug zu unterscheiden. Was sich aendert, ist allein der privilegierte Rueckfall - streng 60 Prozent, locker 16 gegen 27 beim Bezug. Damit ist der Weg frei, aber der Gewinn nicht belegt: er muesste aus dem Wegfall des Klassen-Lebenszyklus kommen, und den misst diese Sonde nicht.
tags: [act23, kommando, latent, methodik]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-16T00:00:00Z }
sources:
  - id: sonde
    resource: "src/pc_cvnn/act23_adress_wiedervorlage.py mit AW_VERSATZ=1: 60 echte Laufszenen, 4 Achsen-Wuerfe je Koerper, 568 Adressen je Variante, Zustand ad9d768c"
    title: Diskret gegen stetig auf denselben Szenen
  - id: frage
    resource: /fragen/stetige-adressierung.md
    title: Die Frage, deren erster Schritt das ist
---

# Der Aufbau

[Die Frage](/fragen/stetige-adressierung.md) nannte als billigsten ersten Schritt: beide
Adressierungen auf denselben echten Laufszenen gegeneinanderstellen. Getauscht wird **nur die
Matching-Regel**:

    diskret   Gleichheit der Namen          (Farbklasse, Formklasse, Groessenband)
    stetig    Abstand unter Toleranz        (Chromatizitaet, desc_embed, Spanne in mm)

Alles andere bleibt Zeile fuer Zeile gleich - die Achsen-Wuerfelei, das Nachlegen bis eindeutig,
die Identitaetspruefung, die Aufloesung auf der VERSCHOBENEN Szene. Damit misst der Vergleich die
Regel und nicht die Strategie.

**Zwei der drei Toleranzen sind nicht geraten.** Die Farbschwelle ist `colour_openset.TH` - dieselbe
Zahl, die entscheidet, ob zwei Chromatizitaeten dieselbe Klasse waeren. Die Formtoleranz ist
**relativ** zum je Lauf gemessenen Median-Abstand zweier verschiedener Koerper im Einbettungsraum
(hier 1,858), damit keine nackte Zahl festgeschrieben wird. Nur die Groessentoleranz (+/-5 mm) ist
gesetzt.

# Zahlen

    Variante   Adressen   grobe Fehler >20mm   Rueckfall        Achsen   eindeutig
    diskret       568       28 =  4,9 %        155 = 27,3 %      1,89      67,6 %
    t0.20         568       30 =  5,3 %        342 = 60,2 %      1,81      38,0 %
    t0.35         568       32 =  5,6 %        249 = 43,8 %      1,88      51,6 %
    t0.50         568       28 =  4,9 %        171 = 30,1 %      1,91      66,4 %
    t0.75         568       31 =  5,5 %        117 = 20,6 %      2,00      73,4 %
    t1.00         568       38 =  6,7 %         92 = 16,2 %      2,06      76,9 %

    gegen diskret (Fisher, grobe Fehler):  p = 0,89 | 0,69 | 1,00 | 0,79 | 0,25

# Die Antwort auf die gestellte Frage

**Die stetige Formachse ist trennscharf genug.** Ueber den ganzen Toleranzbereich liegen die groben
Adressierungsfehler zwischen 4,9 und 6,7 % und sind in keinem Fall vom diskreten Bezug zu
unterscheiden. Bei `t0.50` sind sie sogar identisch (28 von 568 in beiden).

**Der Weg ist damit frei - und das ist alles, was gezeigt ist.**

# Sie ist nicht besser, sie ist woanders auf derselben Kurve

Was sich mit der Toleranz aendert, ist nicht die Genauigkeit, sondern der **Rueckfall**: streng
60,2 %, locker 16,2 %, diskret 27,3 %. Und die Spalte daneben erklaert, warum:

    Achsen je Adresse   1,81 (streng)  ->  1,89 (diskret)  ->  2,06 (locker)

Eine lockere Formachse trennt weniger, also legt die Wuerfelei mehr Achsen nach, und dann passt
haeufiger etwas. **`t1.00` ist nicht "bessere Formerkennung", sondern fast "Form egal", kompensiert
durch Farbe und Groesse.**

Wer den Rueckfall senken will, kann das also haben - fuer etwa denselben Wechselkurs wie beim
[siebten Anlauf](/befunde/groessenachse-spanne.md), nur in die andere Richtung: `t0.75` kauft
6,7 Punkte weniger Rueckfall mit 0,6 Punkten mehr groben Fehlern (nicht aufgeloest).

# Was das fuer die Frage bedeutet

Die [Frage](/fragen/stetige-adressierung.md) behauptet, die Aneignungsprobleme seien Artefakte der
Diskretisierung. **Diese Messung stuetzt das nicht und widerlegt es auch nicht** - sie misst die
ADRESSIERUNG, und dort ist die Diskretisierung offenbar unschaedlich.

Der behauptete Gewinn muesste woanders herkommen: aus dem Wegfall von Geburt, Bestaetigung,
Knopfvergabe, Verhungerungsschutz und Saettigung. **Das misst diese Sonde per Konstruktion nicht.**
Sie raeumt nur den Einwand aus, der den Weg sonst gleich versperrt haette - *"vielleicht ist ein
Vektor gar nicht trennscharf genug"*.

# Fallen

* **`ebene: pruefstand`.** Nachbildung der Wuerfelei, nachgestellte Szenen, geladener Zustand.
* **`AW_VERSATZ=1`** (Adresse auf Szene i gebildet, auf i+1 aufgeloest) ist haerter als der Lauf;
  die absoluten Hoehen sind nicht die des Laufs, nur die Richtungen vergleichbar.
* **Die Groessentoleranz (+/-5 mm) ist gesetzt, nicht gemessen.** Sie wurde nicht mitgefahren;
  ob ein anderer Wert die Kurve verschiebt, ist offen.
* **Der Chroma-Abstand benutzt `TH`** - damit ist die Farbachse faktisch weiter "dieselbe Klasse",
  nur ohne den Namen. Der eigentliche Unterschied steckt in der Formachse.
* **Ein Zustand, ein Szenensatz.** Der Median-Abstand im Einbettungsraum (1,858) ist die Bezugs-
  groesse fuer alle Formtoleranzen und wurde einmal gemessen.

# Verwandt

* [Stetig adressieren statt Klassen vergeben](/fragen/stetige-adressierung.md) - die Frage
* [Spanne und Identitaetspruefung im Adress-Nachspiel](/befunde/spanne-ident-wiedervorlage.md) - dasselbe Werkzeug, andere Achse
* [Die Daempfungsfunktion](/befunde/daempfungsfunktion.md) - der Rauschboden des Deskriptors
* [Die Groessenachse mass die falsche Groesse](/befunde/groessenachse-spanne.md) - derselbe Wechselkurs, andere Richtung
