---
type: Befund
title: 1109 Episoden ohne Lernfortschritt
description: Ehrliches Negativ mit der groessten Stichprobe bisher - 43 Stunden GUI-Lauf heben weder Lieferquote noch Riegelanteil noch Teacher-Abstand noch Formaneignung. Laenger laufen lassen bringt nichts.
tags: [act23, langlauf, negativ]
status: stable
evidenz: gemessen
ebene: langlauf
generated: { by: claude/opus-5, at: 2026-08-28T00:00:00Z }
verified: { by: human:thomas, at: 2026-08-28T09:57:00Z }
sources:
  - id: langlauf
    resource: /raw/index.md
    title: log/pc_act23_2026-08-26_13-44-26.txt - 1109 Episoden, 43 h, Commit 7ca0657
---

# Behauptung

Die Online-Lernschleife bringt in tausend Episoden **keinen** Fortschritt. Wer die Quote oder
die Verallgemeinerung heben will, darf nicht auf "laenger laufen lassen" setzen.

# Zahlen

496/1109 = **44,7 %**, Median-Endabstand 27 mm.[^langlauf] Riegel und Reflex waren an (Vorgabe),
dazu `SCENE_N=4`, `NOVEL_EVERY=6`, `HOME_Z_MIN=0`, `YAW_AB=1`, `FOVEA_ZOOM=1`.

    1. Haelfte  242/554 = 43,7 %
    2. Haelfte  254/555 = 45,8 %     +2,1 Punkte, Fisher p = 0,51
    (Objektmischung beider Haelften vergleichbar - erklaert es nicht)

**Drei unabhaengige innere Messgroessen sind ebenso flach:**

    Block         Riegel/Schritt   ERSTE Anfahrt   |Netz-Teacher|
       0- 199         35,0 %          5,9 mm          8,9 mm
     400- 599         38,0 %          6,2 mm          8,9 mm
     800- 999         37,4 %          6,1 mm          9,3 mm
    1000-1108         36,0 %          7,0 mm          8,8 mm

**Wo die Griff-Fehlschlaege sitzen - einheitlich ueber alle Objekte:**

    Objekt            Fehlschlaege   'tragen' = 0 N   nie gegriffen (>80 mm)
    Rotes Wuerfel        n= 83           87 %              58 %
    U-Form               n=117           77 %              50 %
    Gruenes Wuerfel      n= 73           74 %              55 %
    L-Form               n= 81           72 %              43 %
    Neue Form 10         n= 96           60 %              27 %

**Formen** (Bonferroni-Schranke 0,0071 bei 7 Objekten):

    Langes Objekt    91/163 = 55,8 %   Rest 42,8 %   p = 0,0021  ** ueberlebt
    Neue Form 10    102/198 = 51,5 %                 p = 0,0402
    L-Form           69/150 = 46,0 %
    Gruenes Wuerfel  54/127 = 42,5 %
    Neue Form 7      63/154 = 40,9 %
    U-Form           75/192 = 39,1 %   Rest 45,9 %   p = 0,0936    NICHT belegt
    Rotes Wuerfel    42/125 = 33,6 %   Rest 46,1 %   p = 0,0097  * knapp verfehlt

# Bewertung

Das ueberzeugt gerade **nicht** deshalb, weil ein Effekt im Rauschen untergeht, sondern weil
vier voneinander unabhaengige Groessen gleichzeitig flach sind. Der Riegel greift am Ende so oft
ein wie am Anfang: die Policy hat die Schliess-Entscheidung auch nach 1109 Episoden nicht
gelernt - unabhaengige Bestaetigung bei neunfacher Episodenzahl, siehe
[Laufzeitregeln](/mechanismen/laufzeit-regeln.md). Der Teacher-Abstand bleibt bei 9 mm; die
Policy naehert sich weder an noch entfernt sie sich.

Die zwei belegten Engpaesse sind (1) die **Klassenkonsolidierung**, siehe
[Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md), und (2) die **Griffmechanik** -
in 60-87 % aller Fehlschlaege hat die Klaue nie etwas getragen. Der Fehler sitzt im **Griff**,
nicht in der Ablage.

# Offen

**Der rote Wuerfel ist das schlechteste Objekt** - ausgerechnet die einfachste Form, und in der
eingefrorenen 80-Episoden-Messung lag er noch bei 57 %. Unerklaert.

# Verwandt

* [Vorgaben 2026-08-30](/entscheidungen/defaults-2026-08-30.md) - der Nachfolgelauf mit 56,4 %
* [Exekutionsvarianz](/befunde/exekutionsvarianz.md)
