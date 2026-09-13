---
type: Befund
title: Der Form-Split im Eigenschafts-Pfad schadet - das Verschmelzungs-Indiz waehlt bevorzugt seinen eigenen Fehlerfall
description: Beide Fassungen sind im Lauf schlechter als die Vorgabe (grobe Adressierungsfehler 3,1 auf 9,9 und 8,7 Prozent). Bei der Indiz-Fassung erzeugten ALLE FUENF Splits einen groben Fehler, und der Adressfehler ist jeweils genau so gross wie die Verschiebung des Splits - das Indiz ist ein Abstandstest, und ein falsch gewaehltes Objekt liegt weiter weg als eine Verschmelzung. Die Immer-Fassung ist harmlos, aber sie greift genau dann nicht, wenn sie gebraucht wird: die Farbbindung ueberspringt verschmolzene Blobs per Bauart.
tags: [act23, wahrnehmung, verschmelzung, kommando, negativ, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-13T00:00:00Z }
sources:
  - id: ab
    resource: "Drei kopflose Steuerungslaeufe je 150 Episoden aus derselben Kopie von act23_state.pkl (ad9d768c), ACT23_GROESSE_SPANNE=1 ACT23_EIG_IDENT=1, ACT23_EIG_SPLIT 0/1/2, gleichzeitig gefahren"
    title: Eig-Split-A/B, drei Arme
  - id: pruefstand
    resource: /befunde/eig-split-farbquelle.md
    title: Die Kalibrierung, die den Lauf nicht vorhergesagt hat
---

# Zahlen

    Arm         Ep   Quote | Adr.Median  grobe Fehler >20mm | Rueckfall | Splits
    es_aus     150  66,0 % |   3,2 mm       5/159 =  3,1 %  |    15     |    0
    es_indiz   150  57,3 % |   2,2 mm      16/162 =  9,9 %  |    11     |    5
    es_immer   150  60,0 % |   6,0 mm      14/161 =  8,7 %  |    15     |  128

    gegen die Vorgabe   grobe Fehler   indiz p = 0,022   immer p = 0,056

**Beide Fassungen sind schlechter.** `es_aus` reproduziert zum vierten Mal zifferngenau
(66,0 %, 5/159, 15 Rueckfaelle) - am Aufbau liegt es nicht.

# Das Indiz waehlt bevorzugt seinen eigenen Fehlerfall

Die Aufschluesselung ist eindeutig und braucht keine Statistik:

    es_indiz   Adressen MIT Split in derselben Episode   n=  5   grob  5 = 100,0 %  Median 56,9 mm
               Adressen OHNE Split                       n=157   grob 11 =   7,0 %  Median  1,4 mm

    Ep   8  obj_X   Adressfehler   92,9 mm   Split verschob  93 mm
    Ep  11  obj_U   Adressfehler   56,9 mm   Split verschob  54 mm
    Ep 119  obj_X   Adressfehler  215,9 mm   Split verschob 217 mm

**Der Adressfehler ist jeweils genau die Verschiebung des Splits.** Vor dem Split war die Adresse
richtig; der Split hat sie kaputtgemacht. Alle fuenf Male.

Der Grund ist strukturell und war beim Bauen nicht zu sehen. Das Indiz misst einen **Abstand**:
liegt das farbreine Material weit vom Blob-Schwerpunkt, gilt der Blob als verschmolzen. Weit weg
liegt das Material aber aus **zwei** Gruenden - Verschmelzung *oder* ein falsch gewaehltes Objekt
derselben Farbklasse. Und das falsche Objekt liegt **weiter** weg als eine Verschmelzung
(215 gegen 20-30 mm).

> **Ein Schwellwert, der auf Abstand prueft, siebt bevorzugt die groessten Abstaende heraus - und
> das sind hier nicht die Verschmelzungen, sondern die Verwechslungen.** Der Test ist nicht
> ungenau, er ist auf seinen eigenen Fehlerfall hin optimiert.

Ep 119 ist der Lehrfall: `obj_X` und `obj_L` teilen sich `farbe-4`. Genau das stand als Falle auf
der [Kalibrierseite](/befunde/eig-split-farbquelle.md) - die gestufte Filterung nach Form und
Groesse sollte es abfangen und hat es nicht, weil die Formklasse des verschmolzenen Blobs auf
**keinem** der beiden Teile passt und die Filterung dann auf "nur Farbe" zurueckfaellt.

# Die Immer-Fassung ist harmlos - und unerreichbar, wo sie gebraucht wird

    es_immer   Adressen MIT Split    n=128   grob  4 =  3,1 %   Median  5,8 mm
               Adressen OHNE Split   n= 33   grob 10 = 30,3 %   Median 13,0 mm

Die Splits selbst sind gutartig (3,1 % - wie die Vorgabe insgesamt), kosten aber **Feinheit**:
Median 5,8 statt 1,4 mm. Ueber den ganzen Arm steigt der Median von 3,2 auf 6,0 mm. Das ist der am
Pruefstand gemessene Preis des Splits auf getrennten Blobs, und er faellt im Lauf an, weil die
meisten Szenen eben NICHT verschmolzen sind.

Die schlechten Adressen sind die **ohne** Split. Und hier liegt der eigentliche Befund:

> Der Split braucht `colour_of_body`. Und `_farbbindung_neu` **ueberspringt verschmolzene Blobs**
> bei der Bindung (`area > area_hi` -> "Mischchroma, nicht binden"). **Die Rettung ist per Bauart
> genau in den Episoden nicht verfuegbar, fuer die sie gebaut wurde.**

Dass es episodenweise und nicht koerperweise ist, zeigt die Aufteilung: **jeder** Koerper bekommt
mal einen Split und mal keinen (obj_X 28 mit / 1 ohne bis obj_red 11 / 8). Kein Koerper ist
dauerhaft ungebunden. Die groben Fehler ohne Split sitzen auf obj_blue, obj_U und obj_red - den
Koerpern, die am haeufigsten verschmelzen.

Die Zuordnung "ohne Split = ungebunden" ist **naheliegend, aber nicht einzeln belegt**:
`colour_of_body` wird nicht protokolliert. Die zweite moegliche Ursache waere, dass
`perceive_colour` zu wenige Pixel findet.

# Die fuenfte Pruefstandsfalle, mit Vorwarnung

    Pruefstand (480 Lagen)   heutiger Pfad  8,5 mm Median, 11,9 % ueber 20 mm
                             immer trennen  5,8 mm Median,  1,5 % ueber 20 mm

    Lauf (150 Episoden)      Vorgabe        3,2 mm Median,  3,1 % grob
                             immer trennen  6,0 mm Median,  8,7 % grob

**Vollstaendige Umkehr in beiden Kennzahlen.** Der Grund stand vorher auf der Kalibrierseite:
*"Die Lagenverteilung ist nicht die des Laufs. Die Sonde stellt gezielt nahe Nachbarn (20-50 mm)
und uebergewichtet damit Verschmelzungen stark."*

> Das ist der erste Fall, in dem die Falle **vorher benannt** war und trotzdem zugeschnappt hat.
> Eine benannte Einschraenkung ersetzt keine Messung - sie sagt nur, wo man nachsehen muss.

# Bewertung

* **Der Auftrag ist erfuellt und die Antwort ist nein.** Der Form-Split laesst sich in den
  Eigenschafts-Pfad einbauen, aber er traegt dort nicht.
* **Der Unterschied zum Form-Pfad ist jetzt benannt:** dort springt der Split bei einem echten
  Misserfolg ein (`select()` liefert None) und braucht keinen Schwellwert. Hier gibt es keinen
  Misserfolg, und jeder Ersatz-Ausloeser, der auf Abstand prueft, siebt die Verwechslungen heraus
  statt der Verschmelzungen. **Das ist kein Kalibrierproblem, sondern ein Konstruktionsproblem.**
* **Die Catch-22 ist der wertvollste Teil.** Sie gilt fuer JEDEN Rettungsweg, der ueber die
  gebundene Farbklasse geht - auch fuer den Form-Pfad, dort nur bisher unbemerkt.

# Was ein naechster Anlauf brauchte

Kein Abstands-Schwellwert, sondern ein Ausloeser, der Verschmelzung von Verwechslung **trennt**.
Ungebaut, ungemessen, in der Reihenfolge ihrer Billigkeit:

1. **Die Flaeche statt des Abstands.** Ein verschmolzener Blob ist deutlich groesser als das, was
   eine Farbklasse darin ausmacht - bei einer Verwechslung ist er es nicht.
2. **Die Bindung nachholen**, statt verschmolzene Blobs zu ueberspringen: wer in einer Episode
   verschmolzen war, bleibt an die Klasse gebunden, die er in der letzten sauberen Episode trug.
   Das loest die Catch-22 direkt.
3. **Mehrere Teile auswerten statt `max(area)`** - bei zwei Kandidaten derselben Farbe ist die
   Wahl zwischen ihnen das eigentliche Problem, und die Flaeche ist dafuer das falsche Mass.

# Fallen

* **Ein Seed je Arm**, und die Arme sind nach dem ersten Eingriff verschiedene Laeufe. Die
  Gesamtzahlen tragen deshalb nur begrenzt - der Befund zum Indiz traegt trotzdem, weil er
  **innerhalb** der Episoden misst (Adressfehler = Split-Verschiebung, fuenf von fuenf).
* **Die Quote sagt hier nichts** (66,0 / 57,3 / 60,0 %, alle innerhalb der
  [Nachweisgrenze](/befunde/rechnerlast.md)).
* **`perceive_colour` gibt den Teilen jetzt `span` und `dicke`** - das bleibt im Code, weil es
  unabhaengig vom Schalter richtig ist: ohne sie traegt eine Split-Detektion keine Groesse.

# Folgen

`ACT23_EIG_SPLIT` bleibt auf `0`. Beide Fassungen bleiben im Code samt Begruendung.

# Verwandt

* [Beim Trennen entscheidet die Farbquelle](/befunde/eig-split-farbquelle.md) - die Kalibrierung, deren Nebenbefund hier entkraeftet wird
* [Jeder grobe Adressfehler sitzt im obersten Band](/befunde/adressfehler-sind-verschmelzung.md) - der Anlass
* [Die Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) - der fuenfte Fall, erstmals mit Vorwarnung
* [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md) - der Mechanismus auf dem Form-Pfad
