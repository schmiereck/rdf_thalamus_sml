---
type: Mechanismus
title: Die drei Splits gegen verschmolzene Flecken
description: Zwei Objekte naeher als ~40-50 mm verschmelzen zu EINER Zusammenhangskomponente. Farb-Split, Form-Split und die Verschmelzungssperre reparieren das an drei Stellen - der am besten belegte Gewinn der Wahrnehmungslinie.
tags: [act23, wahrnehmung, split]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-07T00:00:00Z }
verified: { by: human:thomas, at: 2026-08-31T00:00:00Z }
sources:
  - id: chronik
    resource: /chronik/act23.md
    title: act23-Chronik, Eintraege 2026-07-24 bis 2026-08-20
---

# Behauptung

Der haeufigste Wahrnehmungsfehler in act23 ist **Blob-Verschmelzung**: liegen zwei Koerper
naeher als etwa 40-50 mm, liefert die Segmentierung EINE Komponente. Alles, was auf der
Komponente gemittelt wird - Chroma, Formdeskriptor, Schwerpunkt -, wird dadurch falsch. Drei
Eingriffe adressieren das an drei verschiedenen Stellen.

# (1) Farb-Split - `ACT23_COLOUR_SPLIT`, Vorgabe AN

`shape_classifier:623` mittelt die Chroma ueber die ganze Komponente; der Mittelwert landet beim
Objekt mit **mehr Pixeln**. Der rote Wuerfel neben dem groesseren orangen L liest sich als
`farbe-4` (d = 0,100 < TH = 0,12), findet 0 Kandidaten, faellt auf den alten trainierten
vc-Hexcode durch - und der greift dokumentiert auf Fremdobjekte.

Gemessen ueber Luecken 70/50/38/28 mm: Komponenten 2/2/1/1, Schwerpunktfehler 0/0/25/20 mm.

`perceive_colour()` segmentiert die Occupancy auf **Pixelebene** nach den selbst gelernten
Farbklassen und relabelt zusammenhaengend. Verdrahtet als **Fallback** an beiden Pfaden, nur
wenn die normale Klasse 0 Kandidaten liefert - bei getrennten Blobs ist der
Komponenten-Mittelwert exakt (0 mm) und der Split minimal schlechter (6 mm).

    Divergenzfreier Nachweis (150 zufaellige Rot+L-Konstellationen, Luecke 22-75 mm):
      78/150 verschmolzen  -> alter Pfad 0 Kandidaten, Split rettet 78/78 = 100%, Median 6 mm
      72/150 getrennt      -> alter Pfad Median 1 mm, Split wird gar nicht gerufen

    Im GUI-Lauf (120 Ep): blinde ROT-Episoden 5/6 -> 0/20, Fisher p = 0,00009

# (2) Form-Split - `ACT23_FORM_SPLIT`, Vorgabe AN

Dieselbe Wurzel, aber der Formdeskriptor statt der Chroma. `perceive_colour(with_form=True)`
rechnet die Harmonischen auf dem **farbgetrennten** Teil.

    obj_T allein          56,2% -> 95,0% als eigene Klasse erkannt
    mit nahem Nachbarn     8,8% -> 81,2%
    Restfehler sind ausschliesslich ABSTENTIONEN, keine Fehlzuordnungen mehr

    Im GUI-Lauf (64 Ep): blinde Episoden 7/13 = 54% -> 0/12 = 0%, Fisher p = 0,0052
                         0 neue Formklassen geboren (im Lauf davor: 3)

# (3) Farbfreier Split - `ACT_SHAPE_SPLIT`, Vorgabe AN

Fuer den Fall, dass ein Koerper gar keine gebundene Farbklasse hat (obj_X). Eine Komponente, die
auf keine Klasse aufloest, wird erodiert, bis sie in mindestens 2 Kerne zerfaellt; jedes
Ursprungspixel geht an den naechsten Kern.

    Kreuz erkannt, zwei Objekte im Abstand d, je 30 Wiederholungen
      40 mm   2/30 ->  8/30      60 mm  13/30 -> 20/30
      50 mm  11/30 -> 21/30      80 mm  27/30 -> 27/30   (keine Regression)
    Verschmelzungsbereich 40-60 mm: 28,9% -> 54,4%, +25,6 Punkte, Fisher p = 0,00083

`ACT_SHAPE_SPLIT_ALWAYS` (Vorgabe AUS): "immer spalten" brachte 15 statt 14 von 36, also nur
Risiko ohne Gegenwert.

# (4) Verschmelzungssperre am Geburtspfad - `ACT_SHAPE_MERGE_GUARD`, Vorgabe AN

Verschmolzene Flecken lesen sich als bestaendige neue Form und **gebaeren Phantomklassen**. Von
26 unzuordenbaren Sichtungen sind 20 uebergross (822-1390 px gegen ~450 fuer ein sauberes
Objekt), keine liegt am neuen Koerper - meist Objekt + **Arm im Bild**.

`perceive_all` liefert je Fleck die Farbstreuung `cspread`; `observe_scene` sperrt zu stark
streuende Sichtungen vom **Geburtspfad** (Ansprueche unberuehrt).

    Phantom-Geburten 23 -> 13 (-43%) ueber 14 gepaarte Seeds
    besser 7 / schlechter 0 / gleich 7, Vorzeichentest p = 0,016
    Lieferbilanz in 13 von 14 Paaren identisch

Akkumulation ohne Sperre: 1,20 Klassen bei 30 Ep, 2,00 bei 50 (~0,04 je Episode) - auf 300
Episoden hochgerechnet ueber zehn Klassen fuer EIN Objekt.

# Fallen

* **Die Flaeche taugt prinzipiell nicht als Filter.** `area_hi = 1411`, Verschmelzungen liegen
  bei 822-1390 px, die groesste Trainingsform bei ~940. Wiederholung trennt, Flaeche nicht.
  Nicht erneut versuchen.
* **Zwei vorab gemessene Fehlwege zur Sperre:** (a) mittlerer Farbabstand zu gelernten Klassen -
  das noch farblose Kreuz liegt mit 0,074 UEBER einer echten Verschmelzung (0,028), wuerde also
  genau die neuen Objekte verwerfen; (b) Zweigipfligkeit der Farben - trennt nicht, Schattierung
  erzeugt dasselbe Signal.
* **Eine im Lauf kalibrierte Schwelle taugt nur, wenn die Referenz schneller waechst als das
  Ereignis eintritt.** Erste Fassung der Sperre nahm nur trainierte Formen als Referenz
  (~0,5 je Blick) und war erst ab Ep 23 scharf - die Phantom-Geburten fallen in Ep 10-18. Erst
  die breitere Referenz (alle Ansprueche) armiert ab Ep 5.
* **Ein A/B ueber einen LERNENDEN Lauf misst einen seltenen Wahrnehmungs-Fix nicht.** Beide Arme
  liefen bitgleich bis Ep 10; dort loeste der Split zum ersten Mal aus und verbesserte
  (16 -> 10 mm) - ab da divergieren die Trajektorien komplett und alles danach ist Rauschen. Bei
  seltenen, situativen Fixes **divergenzfrei benchmarken**.
* **Die Lieferrate ist fuer einen Wahrnehmungs-Fix die falsche Metrik.** Bei einem Fix, der
  ~18 % der Episoden beruehrt, ist ein realistischer Effekt (+5-8 Punkte) bei 120 Episoden
  unsichtbar; der 39 %-Griff-Boden dominiert. Richtige Metrik: der direkte
  Wahrnehmungszaehler (blinde Episoden).
* **Grenze der Sperre:** bei aehnlich gefaerbten Nachbarn (Cyan neben Blau) greift sie nicht.

# Offen

Der Farb-Split loest **Eindeutigkeit, nicht Richtigkeit**. Zwei Koerper in ~50 mm Abstand
verschmelzen weiterhin zu einem Blob, dessen Schwerpunkt zwischen beiden liegt - dreimal
dieselbe Detektion fuer drei verschiedene Kommandos, siehe
[Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md). Ab welchem Abstand der Split
versagt und wie oft, ist **nicht gemessen**.

# Verwandt

* [Formklassen-Lebenszyklus](/mechanismen/formklassen-lebenszyklus.md)
* [Aneignung neuer Formen](/befunde/aneignung-neuer-formen.md)
