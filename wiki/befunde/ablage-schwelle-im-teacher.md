---
type: Befund
title: Die Ablagegenauigkeit ist eine Konstante des Teachers - er laesst los, sobald die Hand 20 mm vom Ziel entfernt tief genug ist
description: Aus der Nutzerfrage nach Aufmerksamkeit fuer Objekt und Ziel. Zerlegung von 224 Ablagen aus drei 100-Episoden-Laeufen mit unveraenderter Policy - der seitliche Abstand beim Loslassen liegt auffaellig eng bei 25-31 mm (Median 26), fast nur ENTLANG der Klauenachse (|24| gegen |9| mm quer), waehrend die Objektlage nur 12 mm falsch geglaubt wird und in der Klaue 3-5 mm versetzt sitzt. Die Ursache steht im Code - der Teacher (reactive_subgoal, ebenso die FSM) traegt, bis die HAND weniger als NEAR = 20 mm vom Ziel ist, senkt dann ab und laesst los, sobald die HOEHE erreicht ist; seitlich wird nicht weiter konvergiert. Die Policy hat genau das gelernt. Neuer Schalter ACT16_NEAR_ABLAGE (Vorgabe 20 mm, zeichengleich) trennt die Ablage vom Anfahren; das A/B steht noch aus.
tags: [act23, ablage, teacher, aufmerksamkeit, nutzeridee]
status: stable
evidenz: einzelmessung
ebene: act23-ab
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

# Das A/B (2026-09-26): der Mechanismus bestaetigt sich

Gepaart je Episode unter `ACT23_CHOREO=fsm` (der Teacher faehrt direkt), Seeds 9801/9802 je 60 Ep,
117 szenengleiche Paare, Kopien von act23_state.pkl (unveraendert):

                                         NEAR_ABLAGE 20 mm      8 mm
    seitlich beim Loslassen (Median)          22 mm            10 mm    (Q25-Q75: 9-36 gegen 5-22)
      davon entlang der Klauenachse           20 mm             6 mm
    Endlage nach dem Absetzen (Median)        19 mm            14 mm
    geliefert                                 46 / 117         54 / 117
    McNemar                                   nur 20 mm: 6 | nur 8 mm: 14   ->  p = 0,12

**Der Ablagefehler halbiert sich, und der Anteil entlang der Klaue verschwindet fast ganz** (20 -> 6
mm) - die Ursache ist damit belegt. Die Lieferquote steigt um 7 Punkte, aber nicht nachweisbar:
nach dem Loslassen driftet das Objekt noch (Endlage 14 mm), und bei 25 mm Liefertoleranz lag ein Teil
der Ablagen schon vorher innerhalb.

Unter `netz` faehrt die Policy, die noch die alte Schwelle gelernt hat; sie muesste das neue
Verhalten erst ueber die DAgger-Etiketten lernen - nicht gemessen. Die Vorgabe bleibt 20 mm, bis
ein Lauf unter `netz` zeigt, dass die Policy der neuen Schwelle folgt.

# Lernt die Policy die neue Schwelle? (2026-09-27, Netz-Betrieb)

Gepaart je Episode, Seed 9901, 150 Ep, Netz-Betrieb (die Policy faehrt), Kopien:

    Block      Schwelle 20 mm (Kontrolle)             8 mm
               gel. seitlich entlang Netz-Teacher     gel. seitlich entlang Netz-Teacher
      0- 24     13     26      24       18             13     25      23       24
     25- 49     15     25      18       18             18     17      17       25
     50- 74     18     26      25       18             15     25      20       23
     75- 99     14     27      22       19             13     21      16       21
    100-124      9     27      25       16             13     25      19       18
    125-149     12     26      24       18             14     21      14       25
    (Median je Block in mm; "Netz-Teacher" = Abweichung der Policy vom Teacher in der Ablagephase)

    geliefert Ep 0-74:   46 gegen 46   (12 | 12, p = 1,00)
    geliefert Ep 75-149: 35 gegen 40   ( 9 | 14, p = 0,41)

**Die Policy folgt nur zoegerlich.** Der Abstand beim Loslassen sinkt im 8-mm-Arm von 25 auf
um 21 mm und schwankt stark; unter FSM, wo der Teacher selbst faehrt, waren es 10 mm. Ihre
Abweichung vom Teacher in der Ablagephase ist HOEHER als in der Kontrolle (21-25 gegen 16-19 mm):
der Teacher sagt jetzt etwas anderes, die Policy hinkt hinterher.

**Warum, am Code:** im DAgger-Puffer liegen 24000 Beispiele mit den ALTEN Etiketten, davon 8000 als
geschuetzter Kern (`CORE`), der nie verdraengt wird. Neue Episoden ersetzen die uebrigen nur
langsam, und die Policy lernt eine Mischung aus alter und neuer Regel. Das passt zum
[Ruecksetz-Versuch](/befunde/ruecksetz-versuch.md): die Policy lernt langsam.

**Der naheliegende Ausweg, nicht gebaut:** `reactive_subgoal` ist eine REINE Funktion des Zustands.
Aendert sich der Teacher, lassen sich alle gespeicherten Zustaende sofort mit der neuen Regel neu
etikettieren und die Policy einmal nachtrainieren - statt 24000 Beispiele ueber Hunderte Episoden
auszuwaschen.

# Verwandt

* [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md) - die Nutzerfrage
* [Beim Ablegen zaehlt nur die seitliche Genauigkeit](/befunde/ablage-und-platzieren.md)
* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md)
