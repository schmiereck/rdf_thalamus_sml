---
type: Befund
title: Zwischen Zufassen und Anheben - der Griff rutscht, weil der Objektglaube daneben liegt, und danach versucht der Arm es nie wieder
description: Mess-Spur (ACT23_GREIF_SPUR) ueber 98 Episoden im GUI-Aufbau. 30 Episoden bringen das Objekt nicht hoch; das groesste Fehlerbild (14) - gut zugefasst (4,6 N), die Hand hebt 54 mm, das Objekt bleibt liegen. Die Hand steht dabei genau auf dem Objektglauben, aber der Glaube liegt 15 mm neben der wahren Lage (gelungene Griffe 9 mm, p = 0,014). Danach schliesst die Klaue in 11 von 14 Faellen nie wieder auf - die Hand schwebt mit leerer, geschlossener Klaue an einer Teacher-Schwelle. Die Schwelle vorzuziehen (ACT16_NACHGRIFF_FIX) verschiebt nur den Haengepunkt - 60 gegen 68 gehoben, 49 gegen 52 geliefert. Lehre: die MSE-Policy bleibt an den Grenzen eines unstetigen Teachers haengen.
tags: [act23, greifen, anheben, objektglaube, diagnose, teacher]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-10-08T00:00:00Z }
sources:
  - id: code
    resource: "da25c68 (ACT23_GREIF_SPUR, nur Messung)"
    title: Greif-Spur
  - id: lauf
    resource: "c4_state, NO_PERSIST, GUI-Aufbau (ACT16_ABLAGE_FIX=1 ACT23_LOSLASS_KOPF=1 ACT23_LOSLASS_SELBST=1 ACT16_ENDE_HALTEN=30), Seed 9115, 100 Ep (98 mit Spur-Zeile), ohne Halt-Kopf"
    title: Diagnoselauf 2026-10-08
  - id: fix
    resource: "90edcd8 (ACT16_NACHGRIFF_FIX), sonst wie der Diagnoselauf, Seed 9115, 100 Ep"
    title: Nachgriff-Fix 2026-10-08
---

# Frage

[Ablage im Netzbetrieb](/befunde/ablage-im-netzbetrieb.md) fand den groessten Verlust vor dem
Tragen: "gegriffen, aber nicht hochgebracht" (13 % aller Episoden). Die Einteilung dort war grob.
Was passiert zwischen Anflug und Anheben?

# Messung

`ACT23_GREIF_SPUR=1` (nur Messung) verfolgt jede Episode vom Anflug bis zum gelungenen Anheben
(Druck und Objekt > 15 mm ueber Ruhelage) oder zum Ende: jedes Schliessen der Klaue mit Hoehe ueber
dem Greifpunkt, Hand gegen Objektglauben, Hand und Glauben gegen die wahre Lage, Druck und Hub in
den 80 Schritten danach.

98 Episoden, 68 gehoben (52 geliefert). Die 30 nicht gehobenen:

| Fehlerbild | Episoden |
|---|---|
| **Druck aufgebaut, Hand hob, Objekt blieb liegen** | **14** |
| nie geschlossen, Hand kam nicht herunter (tiefste 17 mm ueber Greifpunkt) | 5 |
| unten geschlossen, kein Druck (daneben, Hand 11 mm vom Objekt) | 4 |
| Druck, Hand hob kaum | 3 |
| nur in der Luft geschlossen (136 mm hoch, im Anflug) | 2 |
| unten, Policy wollte zu, Klaue blieb offen | 2 |

# Das Herausrutschen (14 gegen 68 gehobene)

Werte beim Schliessen (Quartile):

    Hand ueber Greifpunkt     rutschte 2 / 6 / 12 mm      gehoben 0 / 2 / 4     p = 0,038
    Hand - wahres Objekt      rutschte 12 / 15 / 21       gehoben 7 / 9 / 14    p = 0,003
    Glaube - wahres Objekt    rutschte 11 / 15 / 21       gehoben 5 / 9 / 14    p = 0,014
    Hand - Glaube             0 / 0 / 5                   0 / 0 / 1             p = 0,98
    Druck                     2,6 / 4,6 / 8,2 N           4,9 / 6,2 / 8,6 N     p = 0,16

**Die Hand faehrt genau dorthin, wo der Agent das Objekt glaubt - der Glaube liegt daneben.** Der
Griff baut trotzdem Druck auf (das Objekt wird am Rand gefasst) und rutscht beim Anheben heraus.
Ursache ist die Verortung, nicht die Klauensteuerung. Betroffen sind ueberwiegend Wuerfel (gruen,
blau, rot je 3), nicht die Formen.

# Und danach: kein zweiter Versuch

11 der 14 Episoden schliessen nur EINMAL. Die Hand steigt mit geschlossener Klaue auf 56-63 mm ueber
dem Greifpunkt und schwebt dort hunderte Schritte, bis die Episode steht. Dasselbe Schweben zeigen
die beiden "in der Luft geschlossen"-Episoden.

Bestaetigt (Spur mit Teacher-Etikett, 30 Episoden): eine Totzone im Teacher. `reactive_subgoal` laesst nur neu greifen, wenn
die Hand mit leerer Klaue die volle Traghoehe erreicht hat (`hz > carry_z - 12 mm` = 78 mm); 56-63 mm
ueber einem Greifpunkt von 18 mm sind 74-81 mm - genau um diese Schwelle. Darunter etikettiert der
Teacher "geschlossen weiter anheben", und die Policy hat das Schweben gelernt.
Gemessen schwebt die Hand bei 73-81 mm, und das Teacher-Etikett springt dort zwischen "auf 90 mm
anheben" und "aufmachen". In zwei Faellen folgt die Policy dem Teacher auch dort nicht, wo er
eindeutig ist (93 mm "auf", 67 mm "auf 90 anheben") - die Lage ist selten.

# Gemessen: die Schwelle vorziehen (`ACT16_NACHGRIFF_FIX`) - die Totzone wandert mit

Teacher-Korrektur: ein Fehlgriff gilt schon ab 25 mm ueber dem Greifpunkt (statt ab Traghoehe),
beim Laden werden die Zeilen in der Zone neu etikettiert (2657 DAgger, 65 eigene) und die Policy
nachtrainiert. Echte Griffe sind nicht betroffen (sie gelten ab 14 mm Hub als gegriffen). Gleicher
Seed (9115), gleicher Zustand, je 100 Episoden, alle Aufgaben gleich:

| | Kontrolle | Nachgriff-Fix |
|---|---|---|
| gehoben | 68 | 60 (14 gegen 6 Paare, p = 0,12) |
| geliefert | 52 | 49 (16 gegen 13, p = 0,71) |
| herausgerutscht | 14 | 21 |
| unten, Klaue bleibt offen | 2 | 5 |
| Episoden mit zweitem Schliessen | 3 | 6 |

**Ehrliches Negativ.** Die Policy schwebt jetzt bei 40-55 mm - um die NEUE Schwelle (18 + 25 mm) -,
mit der Klaue bei 0,25, genau auf der Klauenschwelle des Teachers (`j5 < 0,25`). Das Teacher-Etikett
springt dort zwischen "auf", "vorsichtig weiter schliessen" und "anheben".

**Lehre (Mechanismus):** eine Policy, die mit mittlerem quadratischem Fehler einen UNSTETIGEN
Teacher nachahmt, mittelt an dessen Entscheidungsgrenzen und bleibt genau dort haengen. Eine
Schwelle zu verschieben, verschiebt nur den Haengepunkt. Dasselbe Muster zeigte die Klaue beim
Loslassen (Pendeln um 0,27, s. [Loslassen](/befunde/loslassen.md)); geloest wurde es dort durch
einen EIGENEN Kopf fuer die eine Entscheidung, der aus Einzelaspekten 99 % statt 35 % traf.

Naheliegender naechster Schritt: ein eigener Kopf "Fehlgriff - aufmachen?" nach dem
Muster des Loslass-Kopfs - gebaut und gemessen in [Fehlgriff-Kopf](/befunde/fehlgriff-kopf.md): das Schweben ist weg, die Quote nicht besser.
`ACT16_NACHGRIFF_FIX` bleibt Vorgabe 0.

# Verwandt

* [Ablage im Netzbetrieb](/befunde/ablage-im-netzbetrieb.md)
* [Noch an der Hand?](/befunde/halt-sehen.md) - Verlieren beim Tragen
* [Zufassen aus dem eigenen Ergebnis](/befunde/zufassen-selbst.md)
* [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md) - Objektglaube 12-16 mm
