---
type: Befund
title: Die Ablagegenauigkeit ist eine Konstante des Teachers - er laesst los, sobald die Hand 20 mm vom Ziel entfernt tief genug ist
description: Aus der Nutzerfrage nach Aufmerksamkeit fuer Objekt und Ziel. Zerlegung von 224 Ablagen aus drei 100-Episoden-Laeufen mit unveraenderter Policy - der seitliche Abstand beim Loslassen liegt auffaellig eng bei 25-31 mm (Median 26), fast nur ENTLANG der Klauenachse (|24| gegen |9| mm quer), waehrend die Objektlage nur 12 mm falsch geglaubt wird und in der Klaue 3-5 mm versetzt sitzt. Die Ursache steht im Code - der Teacher (reactive_subgoal, ebenso die FSM) traegt, bis die HAND weniger als NEAR = 20 mm vom Ziel ist, senkt dann ab und laesst los, sobald die HOEHE erreicht ist; seitlich wird nicht weiter konvergiert. Die Policy hat genau das gelernt. Neuer Schalter ACT16_NEAR_ABLAGE (Vorgabe 20 mm, zeichengleich) trennt die Ablage vom Anfahren; das A/B steht noch aus.
tags: [act23, ablage, teacher, aufmerksamkeit, nutzeridee]
status: draft
evidenz: einzelmessung
ebene: code
generated: { by: claude/opus-5.5, at: 2026-09-26T00:00:00Z }
sources:
  - id: logs
    resource: "Ruecksetz-Versuch 2026-09-25, Arme Kontrolle / Weltmodell frisch / Fovea frisch (Policy unveraendert), Seed 9701, je 100 Ep; Zeilen [Ablage], [InKlaue], [Stufe 2] je Phase"
    title: 224 Ablagen
  - id: code
    resource: "src/pc_cvnn/pc_act16.py: reactive_subgoal (carry solange |Hand-Ziel| > NEAR, dann absenken, loslassen bei hz <= place_z + 12 mm) und FSM-Phase carry -> place -> release; NEAR = 0,02"
    title: Die Ablage-Regel
---

# Die Frage

Nutzerfrage 2026-09-26: *"ob wir die Aufmerksamkeiten richtig steuern - eine Aufmerksamkeit fuer das
zu transportierende Objekt und seine Position und eine fuer den Zielpunkt/das Zielobjekt."* Die
Architektur dazu steht auf [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md).
Diese Seite beantwortet die Vorfrage: **woher kommt der bekannte Ablagefehler** (Median 19-25 mm,
[dort](/befunde/ablage-und-platzieren.md))? Liegt er an fehlender Aufmerksamkeit auf dem Ziel?

# Zerlegung (224 Ablagen, Policy unveraendert)

    seitlicher Abstand zum Ziel beim Loslassen   Median 26 mm   (Q25 25, Q75 31)
      davon entlang der Klauenachse              |24| mm
      quer dazu                                  | 9| mm
    Objektlage: Annahme gegen Wahrheit ("Glaube")  Median 12 mm
    Objekt in der Klaue beim Zufassen            tief |5| mm, quer |3| mm
      Rangkorrelation mit dem Ablageversatz      +0,22 (entlang), +0,25 (quer)
    Endabstand nach dem Loslassen                Median 20 mm

Drei Beobachtungen passen nicht zu Rauschen oder Wahrnehmung:

1. **Die Verteilung ist eng.** Die Haelfte aller Ablagen liegt zwischen 25 und 31 mm - das ist eine
   Schwelle, keine Streuung.
2. **Der Versatz liegt entlang der Klauenachse**, nicht quer dazu.
3. **Die Wahrnehmung ist genauer als die Ablage** (12 gegen 26 mm), und der Versatz in der Klaue
   ist zu klein, um die Ablage zu erklaeren.

# Die Ursache steht im Teacher

`reactive_subgoal` (das Etikett, aus dem die Policy lernt) und die FSM machen dasselbe:

    getragen:  |Hand - Ziel| > NEAR        -> weiter zum Ziel tragen
               sonst, Hand hoeher als Ablagehoehe + 12 mm -> absenken (Richtung Ziel)
               sonst                        -> LOSLASSEN

`NEAR` ist 20 mm. Die Hand kommt aus der Ferne, ueberschreitet die 20-mm-Grenze und wird sofort
abgesenkt; losgelassen wird, sobald die HOEHE erreicht ist - ob die Hand seitlich angekommen ist,
fragt die Regel nicht. 20 mm Hand plus einige Millimeter Versatz in der Klaue ergeben die
gemessenen 25-31 mm, und der Versatz zeigt in Bewegungsrichtung. **Die Policy hat diese Regel
nachgeahmt** (Abweichung zum Teacher in der Ablagephase Median 18 mm) - sie ist so genau wie ihr
Lehrer, und der Lehrer ist hier grob.

Das ist KEIN "ueber den Teacher hinaus lernen" ([geschlossen](/befunde/greif-lerndeckel.md)),
sondern eine Ungenauigkeit IM Teacher, und ein Teacher darf nach
[Laufzeitregeln](/mechanismen/laufzeit-regeln.md) als Trainingsgeruest geaendert werden.

# Der Schalter

`ACT16_NEAR_ABLAGE` (Vorgabe = NEAR = 0,02 m, zeichengleich) trennt die Ablage-Naehe von der
Anfahr-Naehe beim Greifen; er gilt im Teacher und in der FSM. Die Hand erreicht nachweislich etwa
6 mm (erste Anfahrt im [Langlauf](/befunde/langlauf-ohne-fortschritt.md): 5,9 mm).

**Offen, als naechstes zu messen:** ein gepaartes A/B unter `ACT23_CHOREO=fsm` (dort faehrt der
Teacher direkt, die Wirkung ist ohne Umlernen sichtbar) mit 8 gegen 20 mm. Erwartung: der Abstand
beim Loslassen faellt deutlich, die Lieferquote steigt. Fuer die Policy (`netz`) muesste sie das neue
Verhalten erst ueber DAgger lernen.

# Verwandt

* [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md) - die Nutzerfrage
* [Beim Ablegen zaehlt nur die seitliche Genauigkeit](/befunde/ablage-und-platzieren.md)
* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md)
