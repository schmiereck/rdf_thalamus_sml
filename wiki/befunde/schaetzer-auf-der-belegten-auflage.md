---
type: Befund
title: Der Hoehenschaetzer auf der belegten Auflage - die Verteilungsverschiebung ist beziffert und behoben, die Ausbeute ist duenn
description: Stufe 4 ist daran gescheitert, dass der Hoehenschaetzer auf der LEEREN Auflage gelernt hat und nach der BELEGTEN gefragt wurde, die durch den Konzentrisch-Schnitt zerfaellt. Offline reproduziert - auf leer gelernt und auf belegt geprueft ergibt 34 Prozent, also Grundrate, waehrend auf beidem gelernt 97 und 78 Prozent ergibt und auf der leeren Auflage nichts kostet. Der Versatz ist 264 Pixel bei einem Hoehenhub von 127 bis 145. Gebaut: dieselbe Episode liefert zwei Aussehen mit einem Etikett, denn die Oberkante aendert sich nicht dadurch, dass etwas darauf steht. Drei Dinge hat erst der Rauchtest erzwungen, und die Ausbeute bleibt mit einem belegten Beispiel auf sechs Tastwerte duenn.
tags: [act23, stapeln, hoehe, wahrnehmung, verteilungsverschiebung]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-21T00:00:00Z }
sources:
  - id: sonde
    resource: "Sonde auf einer Kopie von act23_state.pkl (ad9d768c) mit Chroma-Schnitt und Konzentrisch-Ausnahme: 30 Rasterstellen x Hoehen 6/10/14 mm x (leere Auflage | Wuerfel darauf), 180 Zeilen; aufgezeichnet wird der GROESSERE Teil des Paares -- genau die Detektion, die _auf_etwas_finden dem Schaetzer vorlegt"
    title: Die Leer-gegen-Belegt-Sonde
  - id: anlass
    resource: /befunde/stufe4-abstapeln-gemessen.md
    title: Der Lauf, an dem es aufgefallen ist
---

# Der Anlass

[Stufe 4](/befunde/stufe4-abstapeln-gemessen.md) hat 0 von 24 geliefert, und eine der beiden
bezifferten Ursachen war der Hoehenschaetzer: wahr 6/10/14 mm, geschaetzt 11,1/6,0/9,2 - die
Reihenfolge zerstoert, also schlechter als raten.

Die Vermutung dort lautete: er hat auf der **leeren** Auflage gelernt und wird nach der
**belegten** gefragt, die durch den Konzentrisch-Schnitt zerfaellt. Das ist jetzt gemessen.

# Die Verschiebung, beziffert

    Median der Auflagen-Flaeche       6 mm     10 mm    14 mm     Hub durch die Hoehe
    leer                              1354     1427     1500           +145
    belegt (groesserer Teil)          1102     1160     1230           +127

    Versatz leer -> belegt:  264 px

**Der Versatz ist rund doppelt so gross wie das Signal.** Die Flaeche ist die staerkste Achse des
Schaetzers; eine Eingabe, die 264 px daneben liegt, ist fuer ihn eine andere Welt.

# Und was das kostet

    trainiert auf     geprueft auf    |Fehler|   richtige Stufe
    NUR leer          leer             0,57 mm      96 %
    NUR leer          belegt           6,00 mm      34 %     <- der Fall aus dem Lauf
    NUR belegt        leer             6,00 mm      33 %
    NUR belegt        belegt           0,95 mm      74 %
    beiden            leer             0,60 mm      97 %
    beiden            belegt           0,91 mm      78 %

Stellenweise gehalten, Grundrate 33 %.

**Der Lauf-Fehlschlag ist damit offline reproduziert** (34 %, Grundrate), und die Abhilfe steht
daneben: **auf beidem zu lernen kostet auf der leeren Auflage nichts** (96 -> 97 %) und rettet die
belegte (34 -> 78 %).

Bemerkenswert ist die Symmetrie: auch andersherum bricht es zusammen (nur belegt gelernt, leer
geprueft: 33 %). Es ist keine Frage von "schwerer" oder "leichter", sondern von **derselben
Verteilung**.

# Gebaut: zwei Aussehen, ein Etikett

Die Episode liefert beides ohne eine zweite Messung. Der Koerper wird ohnehin auf die Auflage
gelegt; **ihre Oberkante aendert sich nicht dadurch, dass etwas darauf steht** - es ist dieselbe
Zahl, nur ein zweites Aussehen dazu. `ACT23_HOEHE_BELEGT`, Vorgabe 0.

## Drei Dinge hat erst der Rauchtest erzwungen

1. **Aufgenommen wird beim NAECHSTEN Adressieren, nicht am Episodenende.** Dort steht der Arm
   ueber der Auflage und verdeckt sie - gemessen 1 von 7 Stapeln erkannt. Am Anfang der naechsten
   Episode ist er zu Hause, und der Stapel steht noch (die Aufraeumschleife laesst ein Objekt oben
   liegen, seit [Selbstrichter](/befunde/selbstrichter-stapel.md)).
2. **Die Adresse trifft bei belegter Auflage oft den KLEINEN Teil** - gemessen 239 px, wo die
   leere Auflage 1236 hatte. `finde_nach_eigenschaften` waehlt nach dem Eigenschafts-Tripel, und
   nach dem Schnitt passt der obere Koerper mitunter besser. Gemeint ist die Auflage, also der
   groessere Teil des Paares.
3. **Ein Pruefstein aus derselben Episode.** Die belegte Auflage ist dieselbe Silhouette plus der
   Koerper - ihre Flaeche darf also nicht deutlich KLEINER sein als die leere, die dieselbe
   Episode beim Adressieren gemessen hat. Das ist Physik, keine gesetzte Zahl, und es hat prompt
   ein Beispiel mit 227 px gegen 990 px verworfen. Eine solche Zeile zoege den Schaetzer auf
   seiner staerksten Achse in die Irre.

# Fallen

* **Die Ausbeute ist duenn: 1 belegtes Beispiel auf 6 Tastwerte.** Ein belegtes Aussehen setzt
  voraus, dass der Stapel gelingt, in die naechste Episode ueberlebt, dieselbe Auflage dort wieder
  adressiert wird und das Paar erkennbar ist. Vier Bedingungen hintereinander. Ob das fuer einen
  brauchbaren Schaetzer reicht, ist **nicht gemessen**.
* **`ebene: pruefstand`.** Die Zahlen oben stammen aus einer aufgeraeumten Sonde. Der Stufe-4-Lauf
  mit dem reparierten Schaetzer steht aus, und nach
  [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) sagt die Sonde ihn nicht vorher - beim
  letzten Mal sagte sie 24 von 25 und der Lauf sagte 0 geliefert.
* **Die zweite Ursache des Stufe-4-Fehlschlags ist damit NICHT behoben:** der Arm verliert den
  getragenen Koerper aus dem Glauben (28-45 mm statt 5-18). Selbst ein perfekter Schaetzer aendert
  daran nichts.
* **Eine Auflagenform, ein Objekt, eine Farbe.** Die Sonde legt immer denselben roten Wuerfel auf
  dieselbe 70-mm-Platte.

# Verwandt

* [Stufe 4 gemessen](/befunde/stufe4-abstapeln-gemessen.md) - der Lauf, an dem es aufgefallen ist
* [Der Stapel wird sichtbar](/befunde/stapel-wird-sichtbar.md) - der Schnitt, der die Verschiebung erzeugt
* [Die Auflagenhoehe ertasten](/mechanismen/hoehe-ertasten.md) - woher das Etikett kommt
* [Die zweite Auflage bricht den Hoehenschaetzer](/befunde/zweiter-grundriss-bricht-die-hoehe.md) - dieselbe Krankheit, anderer Ausloeser
