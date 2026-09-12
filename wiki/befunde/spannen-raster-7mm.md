---
type: Befund
title: Das groebere 7-mm-Raster senkt den Rueckfall nicht - es verdreifacht ihn, und zwar wegen des OBERSTEN Bandes
description: Geprueft, ob ein 7-mm-Raster den Preis der Groessenachse senkt. Die Adressierung bleibt gut (2,6 gegen 3,1 Prozent grobe Fehler, beide weit unter den 10,8 der Vorgabe), aber der privilegierte Rueckfall steigt von 7 auf 20 Episoden (p = 0,014). Ursache ist nicht die Rasterweite, sondern ein zusaetzliches oberstes Band "gewaltig", das nur bei Blob-Verschmelzung entsteht und im naechsten Bild nie wieder passt. Nebenbefund: der Wiederholungsarm reproduziert den siebten Anlauf zifferngenau.
tags: [act23, kommando, wahrnehmung, negativ, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-13T00:00:00Z }
sources:
  - id: ab
    resource: "Drei kopflose Steuerungslaeufe je 150 Episoden aus derselben Kopie von act23_state.pkl (ad9d768c), gleichzeitig gefahren: Vorgabe / gemessene Liste / 7-mm-Raster"
    title: Rastervergleich, drei Arme
  - id: vorher
    resource: /befunde/groessenachse-spanne.md
    title: Der siebte Anlauf, dessen offene Frage hier beantwortet wird
---

# Die Frage

[Der siebte Anlauf](/befunde/groessenachse-spanne.md) liess eine Frage offen: die Groessenachse
"Spanne" senkt die groben Adressierungsfehler von 10,8 auf 3,1 %, **verdoppelt aber den
privilegierten Rueckfall** (7 -> 15 von 150 Episoden). Die Vermutung dort: feinere Baender heissen
haeufiger "keine Adresse passt". Ein groeberes Raster muesste den Preis also senken.

**Vorab gerechnet, um keinen Lauf zu verschwenden:** entscheidend ist nicht, ob ALLE Koerper
getrennt werden - baugleiche Wuerfel SOLLEN ein Band teilen -, sondern ob die getrennt werden, die
sich eine **Formklasse** teilen. Das war gemessen `neu-3 <- obj_T, obj_U, obj_blue`, und die liegen
bei 5 wie bei 7 mm in drei verschiedenen Baendern. 7 mm verliert nur `obj_T`/`obj_X`, und die
tragen verschiedene Formklassen.

    gemessene Liste  cube klein | obj_X mittelklein | obj_T mittel | obj_L gross | obj_U riesig
    7-mm-Raster      cube klein | obj_X klein       | obj_T mittelklein | obj_L mittel | obj_U mittel

# Zahlen

    Arm        Ep   Quote | Adr.Median   grobe Fehler >20mm | Rueckfall | Achsen/Adresse
    r7_aus    150  58,7 % |   2,0 mm      18/167 = 10,8 %   |     7     |     1,81
    r7_fein   150  66,0 % |   3,2 mm       5/159 =  3,1 %   |    15     |     1,79
    r7_grob   150  60,0 % |   3,6 mm       4/153 =  2,6 %   |    20     |     1,79

    gegen die Vorgabe   grobe Fehler   fein p = 0,0086   grob p = 0,0038
                        Rueckfall      fein p = 0,12     grob p = 0,0142
                        Quote          fein p = 0,23     grob p = 0,91

**Die Antwort ist nein.** Der Adressierungsgewinn bleibt (2,6 % ist so gut wie 3,1 %), der
Rueckfall wird nicht besser, sondern **schlechter**: 20 statt 15, gegen 7 in der Vorgabe. Das ist
der einzige Wert, der sich gegen die Vorgabe aufloest.

# Der Nebenbefund, der den Aufbau traegt

`r7_aus` und `r7_fein` sind **Wiederholungen** von `g7_aus` und `g7_beide` aus dem siebten Anlauf.
Sie reproduzieren zifferngenau - 58,7 / 66,0 % Quote, 18/167 und 5/159 grobe Fehler, 7 und 15
Rueckfaelle. Nach [Laeufe sind reproduzierbar](/befunde/laeufe-sind-reproduzierbar.md) ist das
erwartbar und trotzdem wert, einmal nachgesehen zu haben: **der siebte Anlauf war kein Ausreisser,
und die Auswertung ist stabil.**

> Eine Falle dabei war meine eigene: mein erster Auswerter entdoppelte aufeinanderfolgende
> gleiche `[dbg]`-Zeilen und kam auf 8/148 statt 18/167. Die Zahlen sahen plausibel aus und waren
> mit der gemessenen Seite **nicht** vergleichbar. Zwei Auswerter auf denselben Daten sind zwei
> verschiedene Messungen.

# Die Ursache: nicht die Weite, sondern das oberste Band

Die Aufschluesselung der Rueckfaelle zeigt, dass es nicht an der Rasterweite liegt:

    r7_grob, 20 Rueckfaelle -- davon mit Band "gewaltig"
      obj_U  (farbe-6, neu-13, gewaltig)   3x
      obj_L  (farbe-6,  None,  gewaltig)   2x
      obj_blue (farbe-4, None, gewaltig)   1x
                                          ---
                                           6   -> ohne sie 14, also wie r7_fein

`gewaltig` ist das siebte Band des gleichmaessigen Rasters und faengt alles ueber 52,5 mm. **Kein
einzelner Koerper wird so gross** - der groesste, obj_U, misst 37,4 mm. Wer in `gewaltig` landet,
ist ein **verschmolzener Blob** aus zwei Koerpern
([Verschmelzungs-Abstandskurve](/befunde/verschmelzung-abstandskurve.md)).

Damit ist der Mechanismus klar: die Wuerfelei schreibt ein Tripel aus der Wahrnehmung EINER Szene.
Verschmelzen dort zwei Koerper, wird `gewaltig` ins Tripel geschrieben - und im naechsten Bild, wo
sie getrennt liegen, **passt es nie wieder**. Das Band ist eine Falle, aus der es keinen Rueckweg
gibt.

Die gemessene Liste hat dieses Problem nicht, weil ihr oberstes Band **offen** ist (`riesig`
ab 36 mm, ohne Obergrenze). Verschmolzene Blobs landen dort zusammen mit obj_U - unsauber, aber
wiederfindbar.

> **Ein offenes oberstes Band ist keine Nachlaessigkeit, sondern haelt den Ausreisser im
> adressierbaren Bereich.** Das gleichmaessige Raster hat es beim Aufraeumen entfernt.

# Was das NICHT zeigt

* **Nicht, dass 7 mm als Weite schlecht ist.** Ohne die sechs `gewaltig`-Faelle waere `r7_grob`
  bei 14 Rueckfaellen - nicht von `r7_fein` (15) zu unterscheiden. Geprueft ist die Kombination
  aus Weite und Bandzahl, nicht die Weite allein.
* **Nicht, dass ein offenes Top-Band den Preis loest.** Auch `r7_fein` zahlt 15 gegen 7. Der
  Rueckfall-Preis der Spannen-Achse bleibt ungeloest; dieser Lauf hat nur eine falsche Erklaerung
  dafuer ausgeraeumt.
* **Ein Seed je Arm**, 150 Episoden. Der Adressierungsbefund traegt (~160 Sichtungen je Arm), die
  Quote nicht - 58,7 / 66,0 / 60,0 % liegen alle innerhalb der
  [Nachweisgrenze](/befunde/rechnerlast.md).

# Folgen

`ACT23_SPANNE_RASTER` bleibt auf `0` - die gemessene Liste ist die bessere der drei geprueften
Varianten. Der Schalter bleibt samt dieser Begruendung im Code.

Die Entscheidung ueber `ACT23_GROESSE_SPANNE` + `ACT23_EIG_IDENT` (beide noch auf `0`) ist damit
**nicht** leichter geworden: der Handel lautet unveraendert *grobe Adressierungsfehler 10,8 -> 3,1 %
gegen privilegierten Rueckfall 4,7 -> 10,0 % der Episoden*. Ein billigerer Weg waere, den Rueckfall
gar nicht erst zu brauchen: bei "kein Treffer" die **Groessenachse fallen lassen** statt zu
privilegieren. Das ist ungebaut und ungemessen.

# Verwandt

* [Die Groessenachse mass die falsche Groesse](/befunde/groessenachse-spanne.md) - der siebte Anlauf, dessen offene Frage hier beantwortet ist
* [Verschmelzungs-Abstandskurve](/befunde/verschmelzung-abstandskurve.md) - woher `gewaltig` kommt
* [Laeufe sind reproduzierbar](/befunde/laeufe-sind-reproduzierbar.md) - warum die Wiederholung zifferngenau ist
* [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md)
