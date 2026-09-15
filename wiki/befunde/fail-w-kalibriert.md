---
type: Befund
title: fail_w ist zu hoch fuer die Vorhersage und trotzdem richtig - die 946 gedaempften Zeilen sind ALLE Fehlschlaege, und die Route existiert gegen eine Blockade, nicht fuer die AUC
description: Die Kalibrierung ist bei Luecke 1500 monoton fallend - je kleiner fail_w, desto besser, mit 0,0 als Optimum (+0,0079 gegen die heutigen 0,3, bei 5 von 5 Seeds). Bei Luecke 4000 ist alles flach (Spanne 0,0016, Vorzeichen zufaellig). Und der beste Wert darf nicht eingestellt werden: fail_w=0 schaltet die Kredit-Route ganz ab, und die wurde gegen eine gemessene Weltmodell-Blockade eingebaut. Empfehlung ist deshalb 0,1, nicht 0,0.
tags: [act23, weltmodell, puffer, kredit]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-15T00:00:00Z }
sources:
  - id: kal
    resource: "Offline auf einer Kopie von act23_state.pkl: 6 Werte x 2 Luecken (1500/4000) x 5 Seeds, gepaart gegen fail_w=0,3 desselben Seeds, reiner Halteteil aus 500 echten Zeilen"
    title: fail_w-Kalibrierung
  - id: anlass
    resource: /befunde/sanfter-abfall.md
    title: Die Nullkontrolle, die die Daempfung erstmals bezifferte
---

# Was fail_w ist

`ACT23_FAIL_W` (Vorgabe 0,3) daempft die Kredit-Route *"Griff am Objekt fehlgeschlagen (Aktion)"*,
solange die Zuordnung nicht sicher ist (`obs_w = 1.0 if att_full else fail_w`). Betroffen sind
**946 von 10322 Trainingszeilen = 9,2 %** - und die Zaehlung zeigt etwas, das ich nicht erwartet
hatte:

    davon positiv: 0

**Alle gedaempften Zeilen sind Fehlschlaege.** Das ist bauartbedingt (die Route vergibt nur
`outcome=False`), stand aber nirgends, und es aendert die Lesart jedes Ergebnisses unten: fail_w
zu senken heisst, unsichere NEGATIVE leiser zu stellen.

# Zahlen

     fail_w |         Luecke 1500          |         Luecke 4000
            | Median   gegen 0,3   besser  | Median   gegen 0,3   besser
        0,0 | 0,7382    +0,0079    5/5     | 0,7091    +0,0007    3/5
        0,1 | 0,7339    +0,0031    5/5     | 0,7076    +0,0000    2/5
        0,3 | 0,7303    +0,0000    0/5     | 0,7065    +0,0000    0/5
        0,5 | 0,7272    -0,0031    0/5     | 0,7059    +0,0001    3/5
        0,7 | 0,7250    -0,0062    0/5     | 0,7059    +0,0001    3/5
        1,0 | 0,7219    -0,0092    0/5     | 0,7043    -0,0009    2/5

**Bei Luecke 1500 monoton fallend**, ohne Optimum in der Mitte: je kleiner, desto besser.
**Bei Luecke 4000 flach** - die ganze Spanne betraegt 0,0016, und die Vorzeichen sind Muenzwuerfe
(3/5, 2/5, 3/5, 3/5, 2/5).

Die Deutung liegt nahe und passt zum Zweck der Daempfung: die unsicher zugeordneten Fehlschlaege
sind **verrauschte Etiketten**. Sie leiser zu stellen entfernt Rauschen, und deshalb hilft weniger
immer mehr. Dass es nur nah hilft, reiht sich in alles andere dieser Serie ein.

# Der beste Wert darf nicht eingestellt werden

`fail_w = 0` ist offline das Optimum - und zur Laufzeit etwas anderes als "Gewicht null":

    att_ok = att_full or fail_w > 0.0

Mit 0 wird die **Route ganz abgeschaltet**; die Episode wird zur Enthaltung und erzeugt gar keine
Zeile. Fuer den Puffer ist das fast dasselbe, fuer das VERHALTEN nicht. Der Kommentar an der
Route sagt, wogegen sie gebaut wurde:

> *"Without this route a grasp-PREVENTING wrist was unfalsifiable (always 'nicht gegriffen' ->
> abstain) and the world model froze on it (L-Form wrist-112 deadlock)."*

**Die Route existiert nicht fuer die AUC, sondern gegen eine gemessene Blockade.** Sie
abzuschalten koennte die Blockade zurueckbringen, und das wuerde diese Messung nicht sehen - sie
rechnet auf einem stehenden Puffer, in dem die Blockade schon vorbei ist.

> Ein Optimum am Rand ist hier also kein Einstellwert, sondern eine Warnung: die Kennzahl misst
> nicht, wofuer die Sache gebaut wurde.

# Empfehlung

**0,1 statt 0,3**, falls ueberhaupt geaendert wird. Es behaelt die Route (`att_ok` bleibt wahr,
Zeilen entstehen weiter, die Falsifizierbarkeit bleibt), reduziert das Etikettenrauschen und ist
bei Luecke 1500 mit +0,0031 in 5 von 5 Seeds besser. Bei Luecke 4000 ist es wie alles andere
wirkungslos - der Gewinn ist ausdruecklich Nahfeld.

**Nicht geaendert** ohne einen Lauf, der auf die Blockade schaut: die Groesse, die hier zaehlt,
ist nicht die AUC, sondern ob das Weltmodell auf einer Greifgeometrie haengen bleibt.

# Was diese Serie insgesamt sagt

Vier Gewichtungsfragen hintereinander, und jede endet gleich: **jeder Gewinn ist Nahfeld.**

    Positionsgewichtung (Stufe)          nah +0,0156   fern -0,0070
    Positionsgewichtung (Verlauf)        nah +0,0089   fern -0,0049
    gespeicherte Daempfung gegen gleich  nah +0,0108   fern +0,0013
    fail_w 0,3 -> 0,0                    nah +0,0079   fern +0,0007

Keine Gewichtung verbessert die Verallgemeinerung. Die beiden inhaltlichen (Daempfung, fail_w)
schaden fern wenigstens nicht, die beiden positionsbasierten schon.

# Fallen

* **`ebene: pruefstand`**, stehender Puffer, ein Halteteil je Luecke, 5 Seeds.
* **Der Punkt 0,0 ist offline nicht das Laufzeitverhalten** (s. oben) - er misst "Zeile vorhanden,
  ignoriert", nicht "Route aus".
* **Die gedaempften Zeilen werden am Gewichtswert 0,3 erkannt.** Sollte eine andere Quelle
  denselben Wert vergeben, waere sie mitgezaehlt; im Puffer gibt es nur die Werte 0,3 und 1,0.
* **Keine Aussage ueber die Blockade.** Die Kennzahl kann sie nicht sehen.

# Verwandt

* [Kein Gewichtungsverlauf hilft bei beiden Luecken](/befunde/sanfter-abfall.md) - wo der Faden herkam
* [Alte Pufferzeilen abwerten](/befunde/alte-zeilen-abwerten.md) - dieselbe Nahfeld-Falle
* [Keine Hoehergewichtung bringt etwas](/befunde/gewichtung-bringt-nichts.md)
