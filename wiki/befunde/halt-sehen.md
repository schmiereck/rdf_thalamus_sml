---
type: Befund
title: Noch an der Hand? - gelernter Vorschlag, Etikett aus der Kamera
description: Regelkonforme Fassung des Halt-Kopfs. Ein Netz sagt aus Tastsinn und Propriozeption "noch an der Hand?"; die Etiketten liefert die Kamera ueber den Selbst/Fremd-Test (zweimal hinsehen, dazwischen eine Probebewegung - wandert der eigene Farbfleck mit der Hand?). Lernlauf 100 Ep - das Kamera-Etikett stimmt in 44 von 46 Faellen mit der Messung, das Netz entscheidet ab Episode 46. Ein Verdrahtungsfehler (Eingriff wartete auf einen Blick, den es bei verdecktem Objekt nie gab) ist behoben. A/B je 100 Ep - 49 gegen 50 % geliefert (p = 1,00); leeres Herumstehen nach Verlust 14 -> 6 Episoden, aber die neu gegriffenen Objekte scheitern an der Ablage. Vorgabe aus.
tags: [act23, greifen, tragen, tastsinn, kamera, selbst-urteil, aspekte]
status: stable
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
  - id: ab
    resource: "c4_state, NO_PERSIST, GUI-Aufbau wie oben, Seed 9114, je 100 Ep nacheinander, ACT23_HALT_SELBST=0 gegen 4"
    title: A/B 2026-10-07
  - id: ablage
    resource: "cb7bff8 (Nachgreifen-Ende), 6102c2a (Nachsehen); je 100 Ep Seed 9114 von c4_state, Modus 4, Kontrollarm aus dem A/B"
    title: Ablage nach dem Neugreifen 2026-10-08
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

# A/B (Seed 9114, je 100 Ep nacheinander, beide von c4_state)

Modus 0 (aus) gegen Modus 4 (das gelernte Netz entscheidet von Anfang an, schaut und lernt weiter).
Aufgabenfolge in allen 100 Episoden gleich (Abdruck).

| | aus | gelernter Vorschlag |
|---|---|---|
| geliefert | 49/100 | **50/100** |
| "getragen, dann lange leer oben" (> 200 Schritte ohne Druck, Hand > 30 mm) | 14 | **6** |
| Episoden mit Eingriff | - | 24 (25 Eingriffe: 16 echte Verluste, 9 Fehlalarme) |
| dieselben 24 Aufgaben geliefert | 11/24 | 10/24 |

* McNemar 16 gegen 17 diskordante Paare, p = 1,00.
* Kamera-Etikett gegen Messung: 35 von 38 Etiketten richtig (27 haelt, 8 verloren; 3 "haelt",
  obwohl verloren); 21 Blickpaare ohne Etikett.
* Netz an Blickpunkten: sagt "verloren" bei 10 von 14 echten Verlusten, bei 5 von 45 haltenden
  Griffen - besser als im Lernlauf (mehr Etiketten).
* Nach einem Eingriff enden 14 Episoden mit "losgelassen"/"abgesetzt", nur 6 mit Stillstand; 10
  davon geliefert. Der Agent greift also wirklich neu und traegt wieder - der zweite Anlauf
  scheitert aber genauso oft an der Ablage wie der erste.

# Lesart

**Ehrliches Negativ fuer die Lieferquote, positiv fuer den Mechanismus.** Was gelernt werden
sollte, ist gelernt: der Agent merkt selbst, dass er nichts mehr haelt (Kamera als Lehrer, 92-96 %
richtige Etiketten; das Netz erkennt 10 von 14 Verlusten), und das leere Herumstehen mit
geschlossener Klaue faellt von 14 auf 6 Episoden. Geliefert wird dadurch nicht mehr (49 gegen 50) -
die geretteten Objekte gehen beim zweiten Ablegen verloren.

Damit ist auch das positive Vorzeichen aus [Haelt der Griff noch?](/befunde/halt-kopf.md)
(Rettung 4/6 gegen 2/8, ein Seed) **nicht bestaetigt**.

Im Sinne von [wiki/ziel.md](/ziel.md) zaehlt die Aneignung: der Agent hat einen Aspekt seiner
eigenen Lage ("ich halte nichts mehr") aus eigener Erfahrung zu erkennen gelernt, ohne Teacher und
ohne feste Schwelle. Fuer die Lieferquote ist dieser Faden erschoepft; der Engpass liegt in der
Ablage nach dem Neugreifen.

`ACT23_HALT_SELBST` bleibt Vorgabe 0.

# Ablage nach dem Neugreifen (2026-10-08)

Nutzerauftrag nach dem A/B: "Kuemmere dich um die Ablage nach dem Neugreifen." Die Diagnose fand
zwei Fehler VOR der Ablage - die neu gegriffenen Objekte kamen meist gar nicht bis dorthin.

1. **Nachgreifen galt als Loslassen.** Das Selbst-Ende (`pc_act16`, ENDE_SELBST) wertet "Klaue
   offen, kein Druck, Hand ueber dem eigenen Ziel" als "losgelassen"; "trug" bleibt die ganze
   Episode gesetzt. Oeffnete der Kopf zum Neugreifen in Zielnaehe, endete die Episode sofort
   (13 der 24 Eingriffs-Episoden endeten so). Abhilfe: eine **Efferenzkopie**
   `run_combined._nachgreifen`, gesetzt vom Kopf beim Eingriff, geloescht beim naechsten Griff;
   solange sie steht, ist Oeffnen kein Ende. Ohne Eingriff verhaltensneutral. Eine Abhilfe ueber
   "Druck vor dem Oeffnen" waere falsch gewesen - manche Objekte werden mit 0 N getragen (Nagel).
2. **Der Objektglaube blieb am Verlustort stehen.** Er friert dort ein, wo der Druck verloren ging;
   das Objekt lag 15-20 mm daneben, die Policy griff 400 Schritte lang daneben (Diagnose
   `ACT23_HALT_DIAG`, nur Messung). Abhilfe: **Nachsehen** (`ACT23_HALT_NACHSEHEN`, Vorgabe 1,
   wirkt nur mit HALT_SELBST=4 und nur nach einem Eingriff) - alle 20 Schritte sucht die Kamera den
   eigenen Farbfleck, der Glaube springt dorthin. Blickfehler zur wahren Lage im Median 4 mm.

Gleicher Seed (9114) und Zustand (c4_state), je 100 Episoden, Kontrollarm 49/100:

| Fassung | geliefert | Eingriffs-Episoden geliefert (dieselben Aufgaben ohne Kopf) | Enden nach Eingriff |
|---|---|---|---|
| Kopf | 50 | 10/24 (11) | losgelassen 13, Stillstand 9, abgesetzt 2 |
| + Nachgreifen-Ende | 52 | 10/23 (10) | losgelassen 4, Stillstand 14, abgesetzt 5 |
| + Nachsehen | 51 | 12/22 (12) | losgelassen 9, abgesetzt 7, Stillstand 6 |

* Keine Fassung unterscheidet sich vom Kontrollarm (p = 1,00 / 0,75 / 0,88).
* **Die Ablage nach dem Neugreifen ist jetzt so gut wie die erste:** Endabstand im Median 19 mm
  (16 Ablagen nach Eingriff) gegen 17 mm (43 ohne); ueber 25 mm 4/16 gegen 8/43. Die verbleibenden
  Fehlschlaege sind gewoehnliche Ablagefehler (27-39 mm) und vier Stillstaende (einer: Objekt
  verdeckt unter der tief stehenden Hand, die Kamera findet es nie).

**Lesart:** Der besondere Mangel "nach dem Neugreifen" ist behoben - zwei echte Fehler im
Zusammenspiel, beide sauber geloest und ohne Wirkung auf Episoden ohne Eingriff. Die Lieferquote
hebt das nicht messbar: ein Teil der Eingriffs-Aufgaben liefert auch ohne Kopf (12/22), und was
uebrig bleibt, ist die allgemeine Ablagegenauigkeit (Toleranz 25 mm, Median 17-19 mm) - ein
anderer, aelterer Faden. `ACT23_HALT_SELBST` bleibt Vorgabe 0.

# Verwandt

* [Haelt der Griff noch?](/befunde/halt-kopf.md) - die Fassung mit fester Schwelle
* [Zufassen aus dem eigenen Ergebnis](/befunde/zufassen-selbst.md)
* [Aspekt-Rueckmeldung](/fragen/aspekt-rueckmeldung.md)
* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md)
