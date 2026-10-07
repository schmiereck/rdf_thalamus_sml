---
type: Befund
title: Noch an der Hand? - gelernter Vorschlag, Etikett aus der Kamera
description: Regelkonforme Fassung des Halt-Kopfs. Ein Netz sagt aus Tastsinn und Propriozeption "noch an der Hand?"; die Etiketten liefert die Kamera ueber den Selbst/Fremd-Test (zweimal hinsehen, dazwischen eine Probebewegung - wandert der eigene Farbfleck mit der Hand?). Lernlauf 100 Ep - das Kamera-Etikett stimmt in 44 von 46 Faellen mit der Messung, das Netz entscheidet ab Episode 46. Ein Verdrahtungsfehler (Eingriff wartete auf einen Blick, den es bei verdecktem Objekt nie gab) ist behoben. A/B laeuft.
tags: [act23, greifen, tragen, tastsinn, kamera, selbst-urteil, aspekte]
status: draft
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-10-07T00:00:00Z }
sources:
  - id: code
    resource: "5e29305, 9332462 (HaltSehenKopf, ACT23_HALT_SELBST=4)"
    title: Umbau
  - id: lernen
    resource: "Kopflos, c3_state -> c4_state (geschrieben), GUI-Aufbau (ACT16_ABLAGE_FIX=1 ACT23_LOSLASS_KOPF=1 ACT23_LOSLASS_SELBST=1 ACT16_ENDE_HALTEN=30), Seed 9113, 100 Ep, ACT23_HALT_SELBST=4"
    title: Lernlauf 2026-10-07
---

# Frage

[Haelt der Griff noch?](/befunde/halt-kopf.md) zeigte: Neugreifen nach gefuehltem Verlust hilft in
der Richtung - aber der Vorschlag war eine feste Schwelle auf dem Tastsinn, als Laufzeitregel
unzulaessig ([Laufzeitregeln](/mechanismen/laufzeit-regeln.md)). Kann der Agent dieselbe
Entscheidung aus eigener Erfahrung lernen, mit einem Etikett aus dem Kamerabild?

# Gebaut (`ACT23_HALT_SELBST=4`, Vorgabe 0)

* **Netz** (`HaltSehenKopf`): p(noch an der Hand | Druck, Schritte ohne Druck, hoechster Druck in
  diesem Griff, Klaue, Hand ueber Ruhe, Handgeschwindigkeit). Nur Tastsinn und Propriozeption.
* **Etikett aus der Kamera - der Selbst/Fremd-Test:** zweimal hinsehen (`perceive_all`),
  35 Schritte dazwischen. Wandert der Fleck in der Farbe des eigenen Objekts mit (> 60 % des
  Handwegs): haelt. Bleibt er liegen (< 30 %): verloren. Dazwischen oder Hand < 12 mm bewegt: kein
  Etikett. Die Farbe merkt sich der Agent selbst beim ersten Tragen (Fleck naechst der Hand).
* **Probebewegung:** waehrend des Blickpaars faehrt die Hand 40 mm Richtung Ziel, Hoehe und Klaue
  bleiben. Noetig, weil nach einem Verlust die Hand STILL steht (Rauchtest: 0-11 mm in 25 Schritten)
  - ohne Bewegung hat der Test nichts zu vergleichen. Trainingsgeruest, wie ein Kind, das die Hand
  schuettelt, um zu sehen, ob das Spielzeug mitgeht.
* **Wann geschaut wird** (Geruest): nach 10 Schritten ohne Druck, im Trageschritt 20 und dann alle
  80, und bevor das Netz eingreift - so bekommt es auch dort Etiketten, wo es "verloren" sagt.
  Hoechstens 6 Blickpaare je Episode.
* **Entscheidung:** nur das Netz, sobald es 20 Etiketten hat (je Klasse 5): sagt es dreimal in
  Folge p < 0,5, Klaue auf (bis gefuehlt offen), die Policy greift neu. Hoechstens 2 je Episode.

# Lernlauf (100 Ep, Seed 9113, von c3_state)

| Kamera-Etikett | Messung: haelt | Messung: verloren |
|---|---|---|
| HAELT | 29 | 2 |
| VERLOREN | 0 | 15 |
| unklar | 13 | 6 |

* **Das Etikett stimmt in 44 von 46 Faellen** (96 %); 19 Blickpaare ohne Etikett.
* Das Netz entscheidet ab Episode 46 (nach 46 Etiketten). An Blickpunkten danach: sagt "verloren"
  bei 7 von 12 echten Verlusten und bei 6 von 26 haltenden Griffen.
* 10 Eingriffe: 6 echte Verluste, 4 Fehlalarme; Episoden mit Eingriff geliefert 2/10. Gesamt 50/100.

**Verdrahtungsfehler gefunden und behoben (9332462):** der Eingriff wartete auf ein Blickpaar. Ist
das verlorene Objekt verdeckt (der Fleck wird nicht gefunden), versuchte der Kopf jeden Schritt neu
zu schauen und griff **nie** ein - 4 Episoden, bis zu 448 Versuche. Jetzt entscheidet das Netz auch
ohne Blick; der Blick dient nur dem Lernen. Die Lernlauf-Zahlen oben stammen aus der fehlerhaften
Fassung.

# Lesart (vorlaeufig)

Die Kamera taugt als Lehrer fuer diesen Aspekt: der Selbst/Fremd-Test ist fast fehlerfrei, wenn er
ein Etikett vergibt. Der Engpass ist das Netz: aus Tastsinn und Propriozeption allein trennt es
nur maessig (7/12 gegen 6/26) - dieselbe Lehre wie beim Klauenwinkel, der Verlust und Halt nicht
unterscheidet. Ob es trotzdem Lieferungen rettet, misst das laufende A/B (Modus 0 gegen 4, von
c4_state, Seed 9114, je 100 Ep nacheinander).

# Verwandt

* [Haelt der Griff noch?](/befunde/halt-kopf.md) - die Fassung mit fester Schwelle
* [Zufassen aus dem eigenen Ergebnis](/befunde/zufassen-selbst.md)
* [Aspekt-Rueckmeldung](/fragen/aspekt-rueckmeldung.md)
* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md)
