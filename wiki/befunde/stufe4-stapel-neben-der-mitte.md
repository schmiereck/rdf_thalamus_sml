---
type: Befund
title: Der Stapel neben der Mitte - der Versatz schadet dem blinden Arm nicht, die Schwerpunkt-Vermutung faellt
description: Wiederholung der drei gepaarten Arme mit dem Koerper 16 mm neben der Plattenmitte, damit der Schwerpunkt des verschmolzenen Flecks ihn nicht mehr zufaellig trifft. 88 von 90 Episoden szenengleich. Ohne Chroma-Schnitt 30 Prozent, mit Schnitt 41, mit Schnitt und relationaler Adresse 42. K0 gegen K1 p = 0,053 (16 zu 6 abweichende Paare), K1 gegen K2 p = 1,00 (11 zu 10), K0 gegen K2 p = 0,027 - nichts unter der Bonferroni-Schranke 0,0167. Zwischen den Armen waechst der Vorteil der Sichtbarkeit von 3 auf 11 Punkte - aber der DIREKTE Test, derselbe Arm zentriert gegen versetzt auf sonst gleicher Szene (90 von 90 Episoden mit gleichem Kommando und Ziel), zeigt fuer K0 nur 12 gegen 9 abweichende Episoden (p = 0,66). Der Versatz nimmt dem blinden Arm also nichts Messbares; die Vermutung, der Fleckschwerpunkt habe ihm den Stapel geschenkt, wird nicht gestuetzt, und die 11 Punkte sind dieselbe Episodenstreuung wie vorher. Die relationale Adresse fuegt der Sichtbarkeit nichts hinzu; sie loest neben der Mitte zudem seltener auf (47 statt 63 von 90 Episoden). K0 greift weiter in rund der Haelfte der Episoden zu.
tags: [act23, stapeln, sprache, gepaart, negativ, messen]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-09-24T00:00:00Z }
sources:
  - id: lauf
    resource: "Kopflose Laeufe auf Kopien von act23_state.pkl (ad9d768c, danach unveraendert): warmer Hoehenschaetzer (40 Ep, Seed 7001, 23 Tastwerte) in alle Arme verpflanzt; Seeds 9101-9103 je 30 Ep, ACT23_SZENE_JE_EPISODE=1 ACT23_AUTO_CURIOUS=0 ACT23_ABSTAPELN=1 ACT23_ABSTAPELN_VERSATZ=0.016 ACT23_CHOREO=fsm ACT23_SOCKEL_N=1; K0 ACT_SHAPE_CHROMA_SPLIT=0, K1 Schnitt+Konzentrisch, K2 Schnitt+Konzentrisch+ACT23_ADR_RELATION=1+ACT23_ADR_REL_ANTEIL=1.0; hoechstens zwei Prozesse gleichzeitig; Code 7b2405e"
    title: Die drei gepaarten Arme mit Versatz
  - id: zentriert
    resource: /befunde/stufe4-drei-arme-gepaart.md
    title: Dieselbe Reihe mit dem Koerper in der Plattenmitte
---

# Die Frage

In der [zentrierten Reihe](/befunde/stufe4-drei-arme-gepaart.md) griff auch der Arm, fuer den der
Stapel unsichtbar ist (K0, ohne Chroma-Schnitt), den gestapelten Koerper in rund der Haelfte der
Episoden. Vermutung dort: der Koerper steht genau in der Plattenmitte, der Schwerpunkt des
verschmolzenen Flecks liegt auf ihm, und der Test macht Sichtbarkeit und Relation ueberfluessig.

Hier derselbe Aufbau, nur der Koerper **16 mm neben der Mitte** in zufaelliger Richtung
(`ACT23_ABSTAPELN_VERSATZ=0.016`; die Richtung kommt aus `crng` und ist damit je Episode in allen
Armen gleich).

# Vorpruefung (Pruefstand, 12 Stellen je Versatz)

    Versatz   K0: Fleckschwerpunkt      K2: Abstand/Halbspanne     K2: kleiner Teil
              neben dem Koerper         Median (Maximum)           neben dem Koerper
     0 mm          5,7 mm                  0,37 (0,93)                  ~6 mm
     8 mm         10,4 mm
    12 mm         14,1 mm
    16 mm         18,0 mm                  ~0,74 (0,96)                 ~7 mm
    20 mm         21,8 mm                        (0,99)

Zwei Folgen fuer den Aufbau:

* 16 mm reichen, damit K0 im Mittel 18 mm neben den Koerper zielt; der Chroma-Schnitt (K1/K2)
  trifft ihn weiter auf ~7 mm.
* **Das Stapel-Kriterium `ADR_REL_ANTEIL = 0,5` war schon fuer ZENTRIERTE Stapel grenzwertig**
  (Maximum 0,93) - strenger als sein eigener Kommentar, der "innerhalb der Umrisslinie" meint, also
  < 1,0. Fuer diese Reihe ist K2 deshalb ausdruecklich mit `ACT23_ADR_REL_ANTEIL=1.0` gelaufen. Die
  Vorgabe bleibt 0,5, damit die frueheren Messungen vergleichbar sind.

# Ergebnis

    Episoden 90, in allen drei Armen szenengleich 88 (2 ausgeschlossen)

    Arm   geliefert          zentriert (zum Vergleich)
    K0    26 von 88 = 30 %        34 %
    K1    36 von 88 = 41 %        37 %
    K2    37 von 88 = 42 %        43 %

    McNemar auf den abweichenden Paaren (Bonferroni-Schranke 0,0167):
      K0 gegen K1   nur K0  6 | nur K1 16   ->  p = 0,053
      K1 gegen K2   nur K1 10 | nur K2 11   ->  p = 1,00
      K0 gegen K2   nur K0  5 | nur K2 16   ->  p = 0,027

    je Seed:  9101  K0 13  K1 18  K2 17
              9102  K0  7  K1  9  K2 10
              9103  K0  6  K1  9  K2 10

**Kein Vergleich unterschreitet die Schranke.** Zwischen den Armen hat sich das Bild gegenueber
der zentrierten Reihe in der vorhergesagten Richtung verschoben - der direkte Test unten zeigt aber,
dass diese Verschiebung nicht vom Versatz kommt:

* **Sichtbarkeit (K0 -> K1): von 3 auf 11 Punkte**, abweichende Paare 16 zu 6 statt 11 zu 8, und
  K1 liegt in **allen drei Seeds** vor K0. Die Verschiebung teilt sich auf: K0 verliert 4 Punkte
  (34 -> 30 %), K1 gewinnt 4 (37 -> 41 %). Nur der Verlust bei K0 passt zur Vermutung - und der
  **direkte Test** (naechster Abschnitt) zeigt, dass auch er im Rauschen liegt.
* **Relation (K1 -> K2): nichts.** 11 zu 10 abweichende Paare. Was K2 vor K0 hat, ist die
  Sichtbarkeit, die es mit K1 teilt.

# Der direkte Test: derselbe Arm, zentriert gegen versetzt

Der Versatz zieht seine Richtung aus `crng`, nachdem die Szene gebaut ist. Die Szenen beider Reihen
sind deshalb bis auf die Lage des gestapelten Koerpers gleich - nachgeprueft: **in allen 90
Episoden je Arm dasselbe Kommando und dasselbe Ziel** (die Szenen-Abdruecke unterscheiden sich,
weil sie die Koerperlage enthalten). Damit ist jeder Arm mit sich selbst gepaart:

    Arm   nur zentriert geliefert | nur versetzt geliefert   McNemar
    K0              12            |          9                p = 0,66
    K1              10            |         13                p = 0,68
    K2              11            |         11                p = 1,00

**Der Versatz schadet K0 nicht messbar - netto drei Episoden von 90.** Genau das haette die
Vermutung aber verlangt: wenn der Fleckschwerpunkt dem blinden Arm den Stapel schenkt, muss ihm der
Versatz das Geschenk nehmen. Die 11 Punkte zwischen K0 und K1 in dieser Reihe entstehen aus
netto 3 Episoden Verlust bei K0 und netto 3 Gewinn bei K1 - beides im Bereich, in dem eine kleine
Aenderung den Ausgang auf identischer Szene in beide Richtungen kippt
([rund ein Fuenftel der Episoden](/befunde/stufe4-drei-arme-gepaart.md)).

# Trichter

    Arm   zugefasst >1 N   gehoben >1 N   geloest >0,1 N    (je 90 Episoden)
    K0         48               43             31
    K1         46               40             40
    K2         44               49             39

    zentriert zum Vergleich (gleiche Zaehlung):
    K0         51               44             37
    K1         51               38             35
    K2         41               51             39

**K0 fasst auch neben der Mitte in 48 von 90 Episoden zu** - der Versatz aendert an seinem
Trichter wenig (51 -> 48 zugefasst, 37 -> 31 geloest), passend zum direkten Test. Ob diese Griffe den gestapelten
Koerper, die Platte oder einen Nachbarn treffen, ist aus dem Protokoll nicht zu lesen - nicht
untersucht. Die Zaehlung "geloest" ist hier neu definiert (Loesedruck > 0,1 N) und deshalb nicht
mit der Spalte "losgelassen" der zentrierten Seite vergleichbar; die Vergleichszeile oben ist
mit derselben Zaehlung neu ausgezaehlt.

## Die relationale Adresse loest neben der Mitte seltener auf

    Reihe       Episoden mit aufgeloester Relation   wahr daneben (Median)   < 15 mm
    zentriert             63 von 90                         6 mm              68 / 69
    Versatz               47 von 90                         7 mm              52 / 53

Wenn sie aufloest, trifft sie so genau wie vorher. **Sie loest aber in 16 Episoden weniger auf** -
obwohl das Abstandskriterium auf 1,0 gelockert ist. Welche der anderen Bedingungen von
`_stapel_paar()` (Flaechenverhaeltnis >= 1,5, Moebel-Schranke 0,9 x groesster Fleck) neben der
Mitte greift, ist nicht untersucht. Im Rueckfall adressiert K2 gewoehnlich, also wie K1 - das
erklaert, warum K2 nicht schlechter ist als K1, und haelt den Vergleich K1/K2 zugleich unscharf.

# Einordnung

Die Vermutung der zentrierten Seite - "der Koerper in der Plattenmitte schenkt dem blinden Arm den
Stapel" - **wird nicht gestuetzt**: 16 mm Versatz, auf dem Pruefstand 18 mm Zielfehler fuer K0,
kosten K0 im Lauf nichts Messbares. Warum der blinde Arm trotzdem in der Haelfte der Episoden
zufasst, bleibt offen - der Fovea-Servo und die Kandidaten-Offsets beim Greifen korrigieren
womoeglich Zielfehler dieser Groesse; nicht untersucht. Die relationale Adresse leistet
gegenueber der gewoehnlichen Eigenschafts-Adresse auf einem sichtbar gemachten Stapel nichts
Messbares - weder zentriert noch daneben.

Nach [Projektziel](/ziel.md) aendert das am Ertrag von Stufe 4 nichts: der Mechanismus
`ADRESSE := RELATION ADRESSE` ist gebaut und loest auf. Gemessen ist, dass die Aufgabe
"herunterholen" ihn nicht braucht, weil der obere Koerper auch ueber seine Eigenschaften eindeutig
ist. Eine Aufgabe, die ihn braucht, muesste zwei GLEICHE Koerper enthalten, von denen nur einer
auf etwas liegt.

# Fallen

* **p = 0,053 ist kein Befund - und hier sogar eine Falle.** Die 16 zu 6 zwischen K0 und K1 sahen
  wie die Bestaetigung der Vermutung aus; erst der Selbstvergleich jedes Arms zeigte, dass sie es
  nicht ist. Ohne ihn stuende hier "halb bestaetigt" (so stand es im ersten Entwurf dieser Seite).
* **Zwei Aenderungen in K2**: Versatz UND gelockertes Kriterium. Der Vergleich zentriert/Versatz
  ist fuer K2 also nicht rein. Fuer K0 und K1 ist er es.
* **Drei Seeds, 30 Episoden, ein gemeinsamer Hoehenschaetzer** - wie in der zentrierten Reihe.
* **Der Vergleich zentriert/Versatz ist gepaart, aber nicht bitgleich im Uebrigen**: die eine
  zusaetzliche Zufallszahl verschiebt alle spaeteren Ziehungen aus `crng` innerhalb der Episode
  (Entscheidungen, Rauschen). Das ist dieselbe Art Unterschied wie zwischen zwei Armen - und
  bestaetigt, dass auf identischer Szene eine kleine Aenderung den Ausgang in rund einem Viertel
  der Episoden kippt (21 bis 23 von 90), in beide Richtungen gleich oft.

# Verwandt

* [Drei Arme je Episode gepaart](/befunde/stufe4-drei-arme-gepaart.md) - die zentrierte Reihe und ihre Vermutung
* [Der gepaarte Sweep](/befunde/stufe4-sweep-widerlegt.md) - die Adresse allein, ueber acht Seeds
* [Der Stapel wird sichtbar](/befunde/stapel-wird-sichtbar.md) - der Chroma-Schnitt, dessen Wirkung sich hier in der Richtung zeigt
* [Gepaart je Episode](/messungen/act23-headless-ab.md) - das Werkzeug
* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - Stufe 4
