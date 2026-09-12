---
type: Befund
title: Relative Ringe bestehen den Form-Rueckhalte-Test - uebergrosse Formen 18 statt 68 Prozent verloren
description: Mit Ringen an der Eigenausdehnung erkennt der frisch angelernte Klassifikator uebergrosse Formen (1,4x bis 2,0x) in 69 Prozent der Faelle richtig statt in 18. Die Trainingsgenauigkeit bleibt bei 1,000, die Verwechslungen bei unter 1,3 Prozent. Ueber zwei Seeds stabil. Was fehlt: eine Messung im Lauf.
tags: [act23, wahrnehmung, formklassen, generalisierung]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-13T00:00:00Z }
sources:
  - id: ab
    resource: "src/pc_cvnn/act23_relrings_ab.py, zwei frisch angelernte Klassifikatoren je Seed (2500 Trainingsschritte), 3 Formen x 7 Groessen x 8 Lagen = 168 Sichtungen je Arm, Seeds 5 und 23"
    title: Relrings-A/B mit frischem Anlernen
---

> **ENTKRAEFTET IM LAUF (2026-09-13).** Zwei frische Laeufe zu je 300 Episoden zeigen: die
> Geburtenrate bleibt identisch (5 zu 5), das Ueberleben wird nicht besser, und die
> **Adressierung leidet messbar** (grobe Fehler 2,1 -> 9,8 %, p = 0,0001). Der Gewinn unten ist
> echt, betrifft aber nur die KLASSIFIKATION - am selben Deskriptor haengt die Lokalisierung, und
> die verliert mehr. Siehe [Relative Ringe im Lauf](/befunde/relrings-im-lauf.md).

# Die Frage

Aus [Groessen-Invarianz, fuenfter Anlauf](/befunde/groessen-invarianz-fuenfter-anlauf.md): die
Kennzahl faellt von 3,68 auf 2,08, aber das ist eine Eigenschaft des **Deskriptors**. Die Frage,
die zaehlt, steht in [Form-Rueckhalte-Test](/befunde/form-rueckhalt.md): **wird eine uebergrosse
Form noch als ihre Form erkannt?**

Weil ein geaenderter Deskriptor mit gespeicherten Exemplaren nicht vergleichbar ist, werden **beide
Arme frisch angelernt** - gleicher Seed, gleiche Trainingsschritte, einziger Unterschied
`ACT_SHAPE_RELRINGS`. Getestet werden die drei **trainierten** Formen (cube, L, U) in Groessen von
0,7x bis 2,0x; die Sollkategorie ist damit unstrittig - ein doppelt so grosser Wuerfel IST ein
Wuerfel. Keine offenen Klassen, keine Sollvorgabe von Hand.

# Zahlen

    Trainingsgenauigkeit   fest 1,000 / relativ 1,000   (beide Seeds)
    novel_th               fest 7,76 / 7,90   relativ 7,78 / 7,43

    ALLE Groessen (168 Sichtungen je Arm)
                 richtig        neu (uebersegmentiert)   falsch
      Seed  5    fest    61,9 %   38,1 %                  0,0 %
                 relativ 86,9 %   11,9 %                  1,2 %
      Seed 23    fest    65,5 %   34,5 %                  0,0 %
                 relativ 84,5 %   14,9 %                  0,6 %

    NUR die uebergrossen Faelle (>= 1,4x), 72 Sichtungen je Arm
      Seed  5    fest    15,3 %  (11/72)     relativ 72,2 %  (52/72)
      Seed 23    fest    20,8 %  (15/72)     relativ 65,3 %  (47/72)

    zusammengefasst uebergross:  fest 18,1 %  ->  relativ 68,8 %

Der Verlauf je Form zeigt, wo es kippt (Seed 5, Auszug):

    L  1,20x   fest 8/8 richtig   relativ 8/8
    L  1,40x   fest 0/8           relativ 8/8
    L  1,70x   fest 0/8           relativ 5/8
    U  1,70x   fest 2/8           relativ 8/8
    U  2,00x   fest 0/8           relativ 8/8

# Bewertung

* **Die Pruefstandszahl hat diesmal getragen.** Die Kennzahl sagte "halbiert", der direkte Test
  sagt "18 % -> 69 % bei den uebergrossen Faellen". Das ist in diesem Projekt nicht
  selbstverstaendlich ([Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)) - hier stimmt die
  Richtung, und die Groessenordnung ist sogar deutlicher als die Kennzahl vermuten liess.
* **Kein Preis bei den bekannten Formen.** Trainingsgenauigkeit bleibt 1,000, `novel_th`
  kalibriert sich auf denselben Bereich, und bei 1,0x ist beides gleich gut. Die Verbesserung
  kostet also nicht die Trennschaerfe, die heute funktioniert.
* **Verwechslungen bleiben selten**, steigen aber von exakt 0 auf 0,6-1,2 %. Der feste Deskriptor
  irrt sich nie, er **enthaelt sich** - der relative trifft fast immer und irrt sich gelegentlich.
  Fuer die Aneignung ist das der bessere Handel (eine Enthaltung gebiert eine Phantomklasse), aber
  es ist ein Handel und keine reine Verbesserung.
* **Der Rest ist echt.** Auch relativ bleiben 31 % der uebergrossen Faelle unerkannt, vor allem
  bei 2,0x. Groessen-Invarianz ist verbessert, nicht hergestellt.

# Was NICHT gezeigt ist

* **Keine Messung im Lauf.** `ebene: pruefstand`. Ob act23 damit mehr Klassen konsolidiert, ob
  die Lieferquote sich bewegt, ob die Geburtenrate sinkt (was sie *sollte*) - alles ungemessen.
* **Nur trainierte Formen.** Die offenen Klassen (`neu-*`) sind hier gar nicht im Spiel; sie
  entstehen erst im Betrieb. Ob relative Ringe auch dort die Kategorien besser zusammenhalten,
  folgt daraus nicht.
* **Nur in der Ebene skaliert.** Die Hoehe bleibt konstant; eine gleichmaessig skalierte Form ist
  nicht geprueft.

# Der Preis eines Einbaus bleibt

Unveraendert gegenueber [dem fuenften Anlauf](/befunde/groessen-invarianz-fuenfter-anlauf.md):
der gelernte Klassenbestand ist mit festen Ringen gerechnet und laesst sich nicht nachrechnen
(die Masken sind nicht gespeichert). Ein Umschalten am Live-Zustand heisst `train()` neu,
`novel_th` neu, Open-Set von vorn - und nach den [Invarianten](/mechanismen/invarianten.md)
`STATE_SCHEMA` hochzaehlen.

**Die Entscheidung ist damit nicht mehr "ob es hilft", sondern "ob der Schnitt jetzt lohnt".**
Ein Weg dazwischen: den Schalter auf einer **Kopie** des Zustands mit frischem Anlernen ueber
einige hundert Episoden fahren und die Aneignung gegen den heutigen Lauf halten. Das ist die
erste Messung, die `ebene: act23-ab` erreichen wuerde.

# Verwandt

* [Groessen-Invarianz, fuenfter Anlauf](/befunde/groessen-invarianz-fuenfter-anlauf.md) - die Kennzahl
* [Form-Rueckhalte-Test](/befunde/form-rueckhalt.md) - die Metrik, hier angewandt
* [Formfaktorisierung](/befunde/formfaktorisierung.md) - die vier gescheiterten Anlaeufe
* [Geburtenrate und Saettigung](/befunde/geburtenrate-und-saettigung.md)
