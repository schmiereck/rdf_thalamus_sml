---
type: Befund
title: Spanne und Identitaetspruefung im Adress-Nachspiel - derselbe Handel wie im Lauf, nur mit dem zwanzigfachen Stichprobenumfang
description: Ueber 3000 Adressen auf echten Laufszenen senken beide Schalter die groben Adressierungsfehler von 3,3 auf 1,8 Prozent (p = 0,0001) und heben den privilegierten Rueckfall von 27,1 auf 32,7 Prozent (p < 0,0001). Das ist derselbe Handel, den der siebte Anlauf an 160 Adressen fand. Und der Nachspiel zeigt, WARUM es ihn gibt: bildet und loest man die Adresse in DERSELBEN stehenden Szene, bewirken beide Schalter nichts. Sie zaehlen nur, weil die Adresse die Szene ueberlebt, in der sie geschrieben wurde.
tags: [act23, kommando, methodik, wahrnehmung]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-14T00:00:00Z }
sources:
  - id: werkzeug
    resource: src/pc_cvnn/act23_adress_wiedervorlage.py
    title: Adress-Wiedervorlage
  - id: lauf
    resource: /befunde/groessenachse-spanne.md
    title: Der siebte Anlauf, dessen Handel hier nachgerechnet wird
---

# Die Frage und das falsche Werkzeug

Nutzerfrage: *"Pruef mit der Wiedervorlage, ob ACT23_GROESSE_SPANNE und EIG_IDENT sich lohnen."*

**Die Wahrnehmungs-Wiedervorlage kann das nicht.** Sie misst verfehlte und zerteilte Koerper und
laedt dafuer `shape_classifier` neu; beide Schalter sitzen aber in `pc_act23` und beruehren
`perceive_all` gar nicht. Sie aendern, wie aus einer Detektion eine **Adresse** wird. Ein Versuch
haette fuer alle Einstellungen dieselben Zahlen geliefert - und zwar nicht, weil die Schalter
wirkungslos sind, sondern weil das Instrument blind fuer sie ist.

Gebaut wurde deshalb `act23_adress_wiedervorlage.py`: dieselbe Methode eine Ebene hoeher.

# Der Fund, der die ganze Sache erklaert

    3000 Adressen auf 200 echten Laufszenen

    VERSATZ 0 -- Adresse in DERSELBEN stehenden Szene gebildet und aufgeloest
      Vorgabe   2,3 % grob    0,0 % Rueckfall
      Spanne    2,1 %         0,0 %
      Ident     2,1 %         0,0 %
      beide     2,1 %         0,0 %      (p = 0,65 -- nichts)

    VERSATZ 1 -- auf Szene i gebildet, auf Szene i+1 aufgeloest
      Vorgabe   3,3 % grob   27,1 % Rueckfall   1,91 Achsen
      Spanne    2,0 %        32,7 %             1,91
      Ident     1,8 %        32,7 %             1,92
      beide     1,8 %        32,7 %             1,92

      grob      p = 0,0017 (Spanne) / 0,0001 (Ident, beide)
      Rueckfall p < 0,0001 durchweg

**In derselben Szene bewirken beide Schalter nichts.** Sie zaehlen erst, wenn die Adresse die
Szene ueberlebt, in der sie geschrieben wurde - und genau das tut sie im Lauf: das Tripel steht in
`state.EIGENSCHAFT`, waehrend die Szene sich unter ihm weiterbewegt.

> Das ist die Antwort auf eine Frage, die seit dem siebten Anlauf offen war: **warum** die Achsen
> ueberhaupt etwas bewirken. Nicht weil die Wahrnehmung besser wird, sondern weil eine
> spezifischere Adresse laenger gueltig bleibt.

# Der Handel, beziffert

    je 3000 Adressen, "beide" gegen Vorgabe
      grobe Fehler   100 -> 53     =  47 weniger
      Rueckfall      813 -> 982    = 169 mehr

**Pro vermiedener Fehladresse werden rund 3,6 zusaetzliche privilegierte Rueckfaelle gekauft.**
Das ist derselbe Handel, den [der siebte Anlauf](/befunde/groessenachse-spanne.md) an 160 Adressen
fand (10,8 -> 3,1 % grob bei 4,7 -> 10,0 % Rueckfall), hier an 3000 und in Minuten statt Stunden.

**Die Messung entscheidet den Handel nicht** - sie beziffert ihn. Ob 47 richtig adressierte
Objekte 169 Griffe in den Simulator wert sind, ist eine Wertung, keine Zahl. Nach
[dem Projektziel](/ziel.md) spricht einiges dagegen: Privilegien abzubauen ist ausdrueckliches
Ziel, ein falsch adressiertes Objekt dagegen ist eine ehrliche Fehlleistung des Agenten.

# Zwei Abweichungen vom Lauf, die zu nennen sind

* **Im Lauf war `EIG_IDENT` allein bitgleich zur Vorgabe** - die Pruefung griff nie, weil die
  Dicke-Achse alles ins Band "mittel" warf und nichts zum Nachlegen da war. Hier greift sie
  auch allein. Grund: `VERSATZ 1` ist **haerter** als der Lauf (Szene i+1 ist vollstaendig neu
  gestreut, waehrend sich im Lauf die Szene innerhalb der Episode nur verschiebt). Unter dieser
  Haerte gibt es genug Mehrdeutigkeit, dass die Identitaetspruefung auch ohne die Spannen-Achse
  etwas zu tun findet.
* **Die absoluten Hoehen passen nicht** (Rueckfall 27 gegen 4,7 % im Lauf), aus demselben Grund.
  Vergleichbar sind die RICHTUNGEN und das Verhaeltnis, nicht die Niveaus.

# Fallen

* **`ebene: pruefstand`, und das Werkzeug ist eine NACHBILDUNG.** Die Wuerfelei ist eine Closure in
  `run_combined` und nicht importierbar; `adresse_bilden` bildet sie Zeile fuer Zeile nach (Stand
  2026-09-14). Aendert sich der Code, aendert sich die Nachbildung nicht mit.
* **Ein Fehler, der beim Bauen auffiel und behoben ist:** in der ersten Fassung lief die
  Identitaetspruefung gegen die ZIEL-Szene - also gegen Information, die die Wuerfelei zum
  Schreibzeitpunkt nicht hat. Damit sank "grob" auf 0,1 %, ein Artefakt des Privilegs. Die Bildung
  laeuft jetzt vollstaendig auf der Quell-Szene, nur die Schlussaufloesung auf der Ziel-Szene.
* **Nicht nachgebildet**: die Neugier-Auswahl (hier werden alle Koerper adressiert) und die
  Farb-Mischung je Episode (hier gilt die Faerbung des geladenen Zustands).
* **Der Yaw** steht nicht im Protokoll und wird neu gewuerfelt.

# Folgen

`ACT23_GROESSE_SPANNE` und `ACT23_EIG_IDENT` bleiben auf `0` - die Entscheidung ist damit nicht
getroffen, aber sie ist jetzt beziffert statt geschaetzt, und sie kostet keinen Lauf mehr, wenn sie
noch einmal aufgemacht wird.

# Verwandt

* [Die Wiedervorlage](/mechanismen/wiedervorlage.md) - die Methode, hier eine Ebene hoeher
* [Die Groessenachse mass die falsche Groesse](/befunde/groessenachse-spanne.md) - der siebte Anlauf
* [Das groebere 7-mm-Raster](/befunde/spannen-raster-7mm.md)
* [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md)
