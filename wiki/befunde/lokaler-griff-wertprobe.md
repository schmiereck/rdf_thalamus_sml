---
type: Befund
title: Wertprobe lokaler Griff - Zinke quer statt Gesamtform bringt bei L, U und T nichts und kostet beim Kreuz 16 Lieferungen
description: Stufe 0 der formabhaengigen Griffwahl. Privilegierter Probe-Schalter ACT23_FORCE_GRASP=lokal_priv - Griffpunkt mittig im schmalsten lokalen Querschnitt, moeglichst nah am Schwerpunkt, Klaue quer dazu. Gepaartes act23-A/B, 100 Aufgaben nur L/U/T/X. Geliefert 49 gegen 66 (McNemar p = 0,019). L 16/14, U 13/12, T 13/17 - zusammen 42 gegen 43, also nichts. Kreuz 7 gegen 23 (16:0 Paare) - der Griff am Arm statt in der Mitte bringt die gelernte Policy zum Stillstand. Querlage in der Klaue unveraendert (6 gegen 5 mm). Das vorab festgelegte Kriterium (+10 Punkte, p < 0,05) ist verfehlt; der Faden ist geschlossen.
tags: [act23, greifen, form, wrist, greifpunkt, negativ]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-10-11T00:00:00Z }
sources:
  - id: ab
    resource: "Commit 82fc0e8, Kopie act23_state.pkl 2f70ac0d, NO_PERSIST, Seed 9301, ACT23_SZENE_JE_EPISODE=1, ACT23_AUTO_OBJ=obj_L,obj_U,obj_T,obj_X, AUTO_CURIOUS=0, Fehlgriff-Kopf + Nachsehen an, sonst GUI-Konfiguration (EIG_DIREKT/EIG_STETIG, GOAL_Z/GRIFF_Z, ABLAGE_FIX, LOSLASS_KOPF/SELBST, ENDE_HALTEN=30); je 100 Ep nacheinander, ACT23_FORCE_GRASP=lokal_priv gegen leer"
    title: A/B 2026-10-10/11
---

# Frage

Bringt ein Griff an einer einzelnen Zinke mit der Klaue quer zu ihr mehr als der heutige Griff, der
sich nach der Gesamtform richtet? Das ist Stufe 0 aus
[Formabhaengige Griffwahl](/fragen/formabhaengige-griffwahl.md), ausgeloest durch die
Nutzerbeobachtung im [GUI-Lauf 2026-10-09](/befunde/gui-lauf-2026-10-09.md).

Vorab festgelegt war: weiter nur bei mindestens +10 Punkten Lieferung auf den Zinkenformen und
McNemar p < 0,05.

# Gebaut

`lokaler_griff()` in `pc_act23.py`, Probe-Schalter `ACT23_FORCE_GRASP` (Vorgabe leer):

* Kandidaten sind Punkte der Grundflaeche mit klarer Richtung (Eigenwertverhaeltnis der Nachbarn
  im Radius 14 mm >= 2). Wuerfel und Kreuzungsmitten fallen damit heraus.
* Je Kandidat der **schmalste** zusammenhaengende Querschnitt (36 Richtungen). Seine Mitte ist der
  Griffpunkt, die Klaue schliesst entlang des Schnitts. Die Kovarianzachse kippte nahe einer
  Kreuzung um 5-16 Grad und wurde deshalb verworfen.
* Unter den Kandidaten mit 6-22 mm Breite gewinnt der, der dem Schwerpunkt am naechsten liegt.
* `lokal` liest die Kameramaske der eigenen Detektion. `lokal_priv` liest die wahre Grundflaeche
  (Geom-Boxen, 1-mm-Raster).

Gemessen wurde nur `lokal_priv`. Der Rauchtest hatte gezeigt, dass die Kameramaske den Punkt bei
U, T und X um Millimeter bis Zentimeter verschiebt. Das haette den Wert des Griffs mit dem
Wahrnehmungsfehler vermischt.

Die Probe greift dort, wo sie soll (Objektrahmen, im Lauf bestaetigt):

| Form | Griffpunkt | Klaue |
|---|---|---|
| L | (-7, -7) mm, Mitte der langen Zinke ueber dem Fuss | quer |
| U | (0, -14) mm, Mitte des Basisbalkens | quer |
| T | Stiel knapp unter dem Querbalken | quer |
| X | Arm, 11-12 mm von der Mitte | quer |

# Ergebnis

100 Aufgaben, Szenen-Abdruck in beiden Armen identisch, gepaart nach Aufgabe:

| | Kontrolle | lokal_priv | nur lokal / nur Kontrolle | McNemar p |
|---|---|---|---|---|
| **geliefert** | **66** | **49** | 15 / 32 | **0,019** |
| getragen | 75 | 71 | 9 / 13 | 0,52 |
| L (25) | 14 | 16 | 6 / 4 | 0,75 |
| U (25) | 12 | 13 | 6 / 5 | 1,00 |
| T (25) | 17 | 13 | 3 / 7 | 0,34 |
| **X (25)** | **23** | **7** | 0 / 16 | 0,00003 |

Das Kreuz uebersteht auch Bonferroni fuer vier Formen. L, U und T zusammen: 43 gegen 42.

| Mechanismus (alle 100) | Kontrolle | lokal_priv |
|---|---|---|
| Druck beim Anheben, Median | 2,03 N | 1,52 N |
| Druck beim Anheben > 0,3 N | 78/93 | 66/93 |
| Querlage in der Klaue, Median | 5 mm | 6 mm (p = 0,25) |
| eigene Ablagen getroffen | 48/55 | 36/45 |
| Episoden mit Fehlgriff-Eingriff | 21 | 31 |

**Beim Kreuz** endeten 12 von 18 Fehlschlaegen im **Stillstand**, 8 davon ohne je zu tragen. Das
Ende "Stillstand" kommt auch bei gelieferten Episoden vor (Kontrolle X: 10 von 25 bei 23
Lieferungen), entscheidend ist hier die Kombination mit "nicht getragen". Die
Kontrolle greift das Kreuz in der Mitte (Heuristik-Punkt) und liefert 23 von 25. Der Armgriff
liegt 11-12 mm daneben, also ausserhalb dessen, was die Netz-Choreographie je gesehen hat.

# Lesart

* **Die Nutzerbeobachtung ist richtig, aber nicht die Ursache der Verluste.** Die Klaue richtet
  sich tatsaechlich nach der Gesamtform; das ist am Code belegt
  ([Konzept](/fragen/formabhaengige-griffwahl.md)). Wird stattdessen gezielt eine Zinke quer
  gegriffen, aendert sich bei L, U und T nichts - nicht die Lieferung und nicht einmal die
  Querlage in der Klaue, also der Mechanismus, ueber den der Gewinn haette laufen sollen.
* **Das bestaetigt aeltere Befunde unabhaengig:** U quer am Basisbalken war schon 2026-07 ohne
  Gewinn ([U-Form-Engpass](/befunde/u-form-engpass.md)). Die Probe hier ist sauberer, weil Punkt
  und Klaue zusammenpassen, und kommt zum selben Ergebnis.
* **Das Kreuz zeigt die Kosten eines aufgezwungenen Griffs:** Ein Griff, den die Policy nie
  gelernt hat, legt sie lahm. Der Schaden sagt also mehr ueber die Policy als ueber den Griff -
  er laesst sich aber auch nicht wegrechnen, weil er bei L, U und T keinen Gewinn verdeckt.

**Grenze:** Gemessen ist der Griff unter der heutigen, auf den Gesamtform-Griff trainierten
Policy. Ob ein Teacher, der von Anfang an lokal greift, eine Policy hervorbraechte, die davon
profitiert, ist nicht gemessen. Bei L, U und T gibt es dafuer allerdings wenig Anhalt: Episoden
mit Ende "Stillstand" (gelieferte eingeschlossen) sind dort kaum haeufiger als in der Kontrolle
(L 10/10, U 13/11, T 12/7), anders als beim Kreuz. Der Griff wird also ausgefuehrt und bringt
trotzdem nichts.

# Folgen

* Nach dem vorab festgelegten Kriterium endet die formabhaengige Griffwahl hier. Stufe 1 und 2
  werden nicht gebaut. Der Faden steht unter "Ausdruecklich geschlossen" in
  [Offene Faeden](/fragen/offene-faeden-act23.md).
* `ACT23_FORCE_GRASP=lokal|lokal_priv` bleibt als Probe-Werkzeug im Code (Vorgabe leer, wie
  `prong`).
* Wo die Verluste der Zinkenformen tatsaechlich sitzen: zerlegt in
  [Verluste nach dem Anheben](/befunde/verluste-nach-dem-anheben.md) - L und U setzen knapp daneben
  ab, weil die Hand den seitlichen Sitz des Objekts nicht ausgleicht.

# Verwandt

* [Formabhaengige Griffwahl](/fragen/formabhaengige-griffwahl.md) - das Konzept
* [U-Form-Engpass](/befunde/u-form-engpass.md), [Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md),
  [Greif-Lerndeckel](/befunde/greif-lerndeckel.md)
