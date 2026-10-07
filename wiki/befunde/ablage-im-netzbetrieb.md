---
type: Befund
title: Ablage im Netzbetrieb - 86 % der eigenen Ablagen treffen, die Ablage ist nur der drittgroesste Verlust
description: Zerlegung von 380 Episoden im heutigen GUI-Aufbau (Netzbetrieb, Loslass-Kopf mit Erfolgs-Veto, Selbst-Ende). Wenn der Agent selbst ablegt, liefert er 173 von 201 Mal. Von allen Episoden scheitern 9,2 % an einer Fehlablage, aber 20 % schon vor dem Tragen (13,4 % gegriffen und nicht hochgebracht, 6,8 % gar nicht gegriffen) und 11,3 % durch Verlieren unterwegs. Anders als im FSM-Befund sitzt das Objekt bei Fehlablagen schon beim Zufassen seitlich versetzt (9 gegen 2 mm); 23 von 28 Fehlablagen sind T, U, L. Die U-Form liefert 30 %, X 76 %.
tags: [act23, ablage, diagnose, greifen, formen]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-10-08T00:00:00Z }
sources:
  - id: laeufe
    resource: "Kopflose Laeufe im GUI-Aufbau (ACT16_ABLAGE_FIX=1 ACT23_LOSLASS_KOPF=1 ACT23_LOSLASS_SELBST=1 ACT16_ENDE_HALTEN=30), ohne eingreifenden Halt-Kopf: griff_sammeln (Seed 9101, 80 Ep), halt_sammeln (9111, 100), halt_ab_m2 (9112, 100), halt4_ab_m0 (9114, 100)"
    title: 380 Episoden 2026-10-06 bis -08
---

# Frage

Nutzerauftrag 2026-10-08: "Kuemmere dich um die allgemeine Ablagegenauigkeit." Die bisherige
Ablage-Linie ([Ablage beim Oeffnen](/befunde/ablage-beim-oeffnen.md),
[Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md)) ist im **FSM-Betrieb**
gemessen und dort als ausgeschoepft vermerkt. Heute legt im Netzbetrieb die Policy ab, und der
[Loslass-Kopf](/befunde/loslassen.md) entscheidet das Oeffnen. Gilt die alte Zerlegung noch?

# Wohin die Episoden gehen (380 Episoden, 56 % geliefert)

| Ausgang | Episoden | Anteil |
|---|---|---|
| geliefert | 213 | 56,1 % |
| gegriffen, aber nicht hochgebracht | 51 | 13,4 % |
| getragen, unterwegs verloren | 43 | 11,3 % |
| **eigene Ablage daneben** | **35** | **9,2 %** |
| gar nicht gegriffen | 26 | 6,8 % |
| getragen, dann Stillstand | 8 | 2,1 % |
| Objekt nicht gefunden | 4 | 1,1 % |

**Wo der Agent selbst ablegt (Ende "losgelassen"/"am Ziel abgesetzt", mit Ablage-Zeile), liefert er
173 von 201 Mal (86 %).**

# Die Fehlablagen (28 mit vollstaendiger Ablage-Zeile)

Quartile, geliefert gegen nicht geliefert:

    seitlich beim Oeffnen          16/21/26      27/32/36 mm
    Endlage                         9/14/19      26/30/34
    Drift danach                    8/14/19       8/11/20   (gleich)
    Objekt gegen Hand quer          Median 1     Median 14 mm
    Hand gegen Ziel                 Median 21    Median 24  (fast gleich)
    beim ZUFASSEN quer ([InKlaue])  Median 2     Median 9

* **Die Hand steht fast gleich gut; das Objekt sitzt quer in der Klaue daneben.** Das deckt die alte
  Lesart - mit einem Unterschied: im Netzbetrieb ist der Versatz schon **beim Zufassen** da (9 gegen
  2 mm), im FSM-Befund entstand er erst danach (3 gegen 3 mm beim Zufassen).
* 23 der 28 Fehlablagen sind T, U oder L.

# Je Objekt

| Objekt | n | geliefert | nie getragen | unterwegs verloren | Ablage daneben |
|---|---|---|---|---|---|
| U | 46 | **30 %** | 17 | 5 | 8 |
| T | 63 | 48 % | 13 | 8 | 10 |
| L | 54 | 50 % | 10 | 11 | 6 |
| gruen | 60 | 52 % | 16 | 7 | 5 |
| blau | 62 | 66 % | 11 | 3 | 1 |
| rot | 44 | 70 % | 3 | 5 | 4 |
| X | 51 | 76 % | 7 | 4 | 1 |

# Lesart

Die Ablage ist im Netzbetrieb **nicht der Engpass**: selbst eine perfekte Ablage hoebe die Quote um
hoechstens 9 Punkte, und die Hebel dafuer (Objekt in der Hand ansehen, Hand um den Versatz
verschieben, vor dem Oeffnen hinschauen) sind im FSM-Betrieb mehrfach ohne Lieferwirkung gemessen.
Die groesseren Posten liegen davor - **das Hochbringen** (20 % nie getragen) und **das Halten**
(11 % unterwegs verloren). Alle drei Posten haengen am selben Ding: wie das Objekt in der Klaue
sitzt. Bei Fehlablagen sitzt es schon beim Zufassen schief, und die Formen mit Ecken und Zinken
(U, T, L) fuehren in jeder Spalte.

# Sitz in der Klaue - Voraussetzung vor dem Bauen geprueft (2026-10-08)

Nutzerentscheidung: an der gemeinsamen Wurzel ansetzen - lernen, wo das Objekt in der Klaue sitzt,
und schief sitzende Griffe vor dem Anheben neu ansetzen. Vorher geprueft, ob der Sitz beim Zufassen
(`[InKlaue]`, privilegiert, nur Messung) den Ausgang ueberhaupt vorhersagt. 331 Episoden mit Zeile.

Ueber alle Objekte zusammen ein steiler Gradient:

    |quer| beim Zufassen   0-3 mm   3-6    6-10   10-15   > 15
    geliefert              79 %     65 %   51 %   45 %    30 %     (n 148 / 69 / 47 / 44 / 23)

**Das ist ueberwiegend die Form, nicht der Sitz.** `[InKlaue]` misst gegen die Objektmitte; L, T, U
werden absichtlich an einem Zinken gegriffen (Median |quer| 7-12 mm, Wuerfel 1 mm). Innerhalb jeder
Form, geteilt am Median des eigenen |quer|:

| Objekt | n | Median |quer| | geliefert darunter / darueber | |quer| geliefert gegen nicht |
|---|---|---|---|---|
| L | 51 | 10 mm | 54 / 52 % | 8 gegen 10 mm (p = 0,63) |
| T | 55 | 7 mm | 55 / 54 % | 6 gegen 7 mm (p = 0,31) |
| U | 37 | 12 mm | 50 / 24 % | 11 gegen 15 mm (p = 0,053) |
| X | 49 | 3 mm | 85 / 73 % | 3 gegen 4 mm (p = 0,10) |
| blau | 53 | 1 mm | 85 / 69 % | 1 gegen 2 mm (p = 0,057) |
| gruen | 48 | 1 mm | 72 / 53 % | 1 gegen 2 mm (p = 0,079) |
| rot | 38 | 1 mm | 92 / 62 % | 1 gegen 2 mm (p = 0,059) |

* **L und T: kein Zusammenhang.**
* **Wuerfel und X:** eine Richtung, aber bei 1 gegen 2 mm - weit unter dem, was die Kamera in der
  Tiefe aufloest (Median ~5 mm, [Aufmerksamkeit](/fragen/aufmerksamkeit-objekt-ziel.md)). Ein Kopf,
  der aus dem Kamerabild "sitzt schief" lernt, haette dort nichts zu sehen.
* **U:** die einzige Form mit sichtbarem Unterschied (11 gegen 15 mm), knapp nicht signifikant bei
  37 Episoden - und der [U-Form-Engpass](/befunde/u-form-engpass.md) ist ein geschlossener Faden
  (fuenf Anlaeufe am Griff ohne Wirkung).

**Ehrliches Negativ vor dem Bau:** der Sitz in der Klaue, so wie die Kamera ihn sehen koennte, ist
kein tragender Hebel. Nicht gebaut. Das passt zu [Zufassen aus dem eigenen Ergebnis](/befunde/zufassen-selbst.md):
auch dort trennten die Aspekte vor dem Schliessen nicht.

# Verwandt

* [Ablage beim echten Oeffnen](/befunde/ablage-beim-oeffnen.md) - die FSM-Zerlegung
* [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md) - Objekt-Versatz-Korrektur (FSM)
* [Noch an der Hand?](/befunde/halt-sehen.md) - das Verlieren unterwegs
* [Zufassen aus dem eigenen Ergebnis](/befunde/zufassen-selbst.md)
* [U-Form-Engpass](/befunde/u-form-engpass.md)
