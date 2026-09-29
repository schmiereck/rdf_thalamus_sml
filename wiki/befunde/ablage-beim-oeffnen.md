---
type: Befund
title: Beim echten Oeffnen - Fehlablagen sind seitlich in der Klaue verrutschte Objekte, nicht schlecht gewaehlte Griffe
description: Diagnose 2026-09-28 mit einem Schnappschuss im ECHTEN Moment des Oeffnens (FSM-Phase release). Die Hand steht praezise (Reichpunkt quer 0, entlang konstant -16 mm = Klauenversatz); das Objekt liegt beim Oeffnen schon auf dem Tisch, im Median 14 mm vom Ziel, und rutscht danach noch 6 mm. Gelieferte und nicht gelieferte Ablagen unterscheiden sich an EINER Stelle - dem seitlichen Versatz Objekt gegen Hand beim Oeffnen (Median 3 gegen 15 mm). Beim Zufassen sassen beide Gruppen gleich mittig (3 mm); der Versatz entsteht danach, beim Heben, Tragen und Absetzen. Mittiger greifen hilft also nicht, der Griff verrutscht.
tags: [act23, ablage, greifen, klaue, diagnose, nutzeridee]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-09-28T00:00:00Z }
sources:
  - id: logs
    resource: "FSM, ACT16_NEAR_ABLAGE=0.008, ACT16_SENK_NAH=0.020, ZIEL_ADRESSE, Seeds 9811/9812 je 60 Ep (reproduzieren die fruehere Reihe zeichengleich); Zeilen [InKlaue] und [Ablage] ... OEFFNEN"
    title: 70 Ablagen
  - id: code
    resource: "src/pc_cvnn/pc_act16.py run_combined._oeffnen (erster Schritt der Phase release); pc_act23.py Ablage-Zeile 'OEFFNEN:'"
    title: Schnappschuss beim Oeffnen
---

# Die Frage

Nutzerauftrag: das Objekt mittig greifen, damit der Versatz in der Hand nicht entsteht. Hinweis des
Nutzers: mittig ist nicht immer ideal - das L wird am langen Zinken gegriffen, und das hat funktioniert.

# Vorab: der alte Schnappschuss lag im falschen Moment

Die Ablage-Zeile misst "beim Loslassen" im letzten Schritt, in dem das Objekt noch > 14 mm ueber
seiner Ruhelage haengt. Fuehrt die Hand unten nach (SENK_NAH), ist das der Anfang des Nachfuehrens,
nicht das Oeffnen (Berichtigung auf [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md)).
Neu: `run_combined._oeffnen`, der erste Schritt der FSM-Phase release (nur Protokoll).

# Messung (70 Ablagen aus der Tiefe, Quartile)

                                   alle           geliefert (51)    nicht geliefert (19)
    Objekt - Ziel beim Oeffnen     7 / 14 / 23    6 / 11 / 18       23 / 30 / 42 mm
    Objekthoehe beim Oeffnen       -1 / 0 / 3     (liegt schon auf dem Tisch; U: 5-15 mm)
    Reichpunkt - Ziel entlang      -20 / -16 / -10 (konstant: der Klauenversatz)
    Reichpunkt - Ziel quer         -2 / 0 / 2     (die Hand steht seitlich genau)
    danach gerutscht               4 / 6 / 11     4 / 6 / 9         0 / 5 / 18
    Endlage                        8 / 16 / 25    6 / 12 / 18       30 / 33 / 47

    seitlicher Versatz Objekt gegen Hand (Betrag, Median):
                                   geliefert      nicht geliefert
    beim Zufassen ([InKlaue])        3 mm           3 mm
    bei 14 mm Hoehe (Absenken)       2 mm           8 mm
    beim Oeffnen                     3 mm          15 mm

Von 17 Endlagen ueber 25 mm lagen 11 schon beim Oeffnen daneben, 6 kamen erst durch Rutschen dazu.

# Was das heisst

**Die Hand ist praezise, und gegriffen wird mittig - bei Erfolg wie Misserfolg (3 mm).** Die
Fehlablagen entstehen, weil das Objekt NACH dem Zufassen seitlich in der Klaue verrutscht: schon
beim Absenken 8 mm, beim Oeffnen 15 mm. Mittiger greifen hilft deshalb nicht; der Griff haelt die
Lage nicht. Das deckt den Hinweis des Nutzers: der Griffpunkt selbst ist nicht das Problem.

Wo es verrutscht, ist nur grob eingegrenzt: ein Teil beim Heben/Tragen (bis 14 mm Hoehe), ein Teil
beim Absetzen und Nachfuehren unten, wenn das Objekt schon den Tisch beruehrt. Nicht gemessen.

Moegliche Hebel (keiner gemessen): der Blick aufs Objekt kurz vor dem Oeffnen (die Kamera sieht es
unten auf ~5 mm, s. [Aufmerksamkeit](/fragen/aufmerksamkeit-objekt-ziel.md)) und bei grossem Versatz
nicht loslassen, sondern nachgreifen; oder die seitliche Nachfuehrung abschliessen, BEVOR das Objekt
den Tisch beruehrt.

# Gemessen 2026-09-29: vor dem Oeffnen hinschauen (`ACT16_PRUEF_TOL`)

Nutzerauftrag, Hebel 1. Im Moment, in dem die FSM oeffnen wuerde, sieht die Kamera das Objekt an
(objekt_sehen_fn: Detektion naechst der Hand). Liegt es mehr als 12 mm vom Ziel, wird der gesehene
Versatz uebernommen und mit angehobenem Objekt (`ACT16_LUFT_H` = 15 mm) nachgefuehrt, hoechstens
zweimal. Vorgabe 0, zeichengleich. Gleiche Szenen wie die Diagnose oben (Kontrolle), 120 Paare:

                                        Kontrolle        hinschauen
    geliefert                           56 / 120         57 / 120   (15 | 16, p = 1,00)
    Endlage zum WAHREN Ziel (Median)    22 mm            17 mm
    Objekt-Ziel beim Oeffnen (Q)        7 / 14 / 23      5 / 11 / 22
    Endlage (Q)                         8 / 16 / 25      6 / 12 / 26
    Blicke                              -                92, davon 31 Ablagen nachgefuehrt, 14 nicht gesehen
    gesehen gegen wahr                  -                Median 1 mm, Q75 5 mm

**Die Ablage wird genauer (Median 22 -> 17 mm zum wahren Ziel), die Lieferungen nicht.** Die
Kamera sieht das Objekt unten fast immer richtig und die Nachfuehrung bringt es meist nah heran -
die Fehlablagen sitzen aber in drei Schwaenzen, die das Hinschauen nicht erreicht:

1. **Nicht gesehen** (14 Blicke; auffaellig oft `obj_red`, 33-59 mm daneben) - verdeckt unter der Klaue.
2. **Falsches Objekt gesehen** - "gesehen 34 mm (wahr 9)", "gesehen 77 (wahr 31)": die naechste
   Detektion im 40-mm-Umkreis der Hand ist dann offenbar der Bezugskoerper neben dem Ziel; die
   Nachfuehrung schiebt das Objekt WEG.
3. **Aus der Luft gefallen** - nach dem Anheben wird bei 10-38 mm Objekthoehe geoeffnet (vor allem U),
   das Objekt faellt und rutscht (bis 26 mm) - richtig ausgerichtet, dann verloren.

Naechste Stellschrauben, nicht gemessen: nach dem Nachfuehren ganz absetzen, bevor geoeffnet wird;
das getragene Objekt ueber seine Eigenschaften (Farbe/Form) statt als naechsten Fleck suchen.

# Gemessen 2026-09-29: absetzen + ueber die Farbe suchen - schlechter, der Farbfilter macht blind

Nutzerauftrag, beide Stellschrauben zusammen: `ACT16_PRUEF_ABSETZEN` (nach einer Nachfuehrung bis
auf Ablagehoehe +4 mm absenken, erst dann oeffnen) und `ACT23_OBJ_EIG` (im 60-mm-Umkreis nur Flecken,
deren Chromatizitaet naeher als 0,05 an der eigenen Sichtung des Objekts zu Beginn der Episode liegt).
Beide Vorgabe 0. Sonst wie oben (hinschauen, LUFT_H), dieselben 120 Szenen:

                                   Kontrolle   hinschauen   + absetzen + Farbe
    geliefert                      56          57           45    (gegen Kontrolle 19 | 8, p = 0,05;
                                                                    gegen hinschauen 20 | 8, p = 0,04)
    zum WAHREN Ziel (Median)       22 mm       17 mm        25 mm
    Objekt beim Tragen gesehen     55          51           18
    "nicht gesehen" (alle Blicke)  -           40           98
    Blick > 8 mm falsch            -           14 von 92    2 von 45
    nachgefuehrt                   -           31           14

**Der Farbfilter trifft, wenn er etwas findet (2 statt 14 falsche Objekte), aber er findet das
gehaltene Objekt meist nicht mehr** (beim Tragen 18 statt 51-55 Sichtungen): die Farbe des Flecks an
der Klaue weicht offenbar von der Farbe derselben Sichtung auf dem freien Tisch ab (Klaue im Bild,
Schatten, verschmolzener Fleck - nicht gemessen). Damit faellt das Nachfuehren weitgehend aus.
Warum die Lieferungen UNTER die Kontrolle fallen, ist nicht getrennt: die Absetz-Regel greift nur
in 14 Ablagen, und die Laeufe lernen online, sodass sich die Paare ab der ersten Abweichung
auseinanderentwickeln (in allen drei Armen streuen 15-20 Paare je Richtung). Mit Bonferroni fuer
zwei Vergleiche (Schranke 0,025) ist keiner der beiden p-Werte signifikant - belegt ist nur: die
Kombination hilft nicht. Schalter bleiben aus.

Offene Wege, nicht gemessen: Toleranz der Farbe lockern oder zusaetzlich Form/Groesse nutzen;
die Farbe der Referenz aus einer Sichtung IN der Hand nehmen statt vom freien Tisch; ABSETZEN
einzeln messen.

# Gemessen 2026-09-29: Referenzfarbe aus der Hand (`ACT23_OBJ_EIG=2`)

**ENDGUELTIG (alle 120 Paare):**

                                   gegen Kontrolle   gegen hinschauen   gegen Tisch-Farbe
    geliefert                      56 -> 59          57 -> 59           45 -> 59
    McNemar                        13 | 16, p = 0,71  12 | 14, p = 0,85  8 | 22, p = 0,016
    zum WAHREN Ziel (Median)       22 -> 19 mm       17 -> 19 mm        25 -> 19 mm
    Referenz gemerkt 185-mal (3 nicht gesehen, 8 ueber der Toleranz); Blicke beim Ablegen 49
    gesehen, 0 falsches Objekt, 103-mal "nicht gesehen"; 18 von 72 Ablagen nachgefuehrt.

Bonferroni (drei Vergleiche, Schranke 0,017): der Unterschied zur Tisch-Farben-Reihe liegt knapp
darunter - die Referenz aus der Hand ist besser als die vom Tisch, aber nicht besser als bloss
hinschauen oder die Kontrolle. Die folgende Tabelle ist der vorlaeufige Stand bei ~100 Paaren.


Nutzerauftrag. Die Farbe wird gemerkt, sobald die Klaue zu ist und das Objekt noch steht
(`objekt_merken_fn`, Uebergang close -> lift), sonst wie die Reihe davor (hinschauen, absetzen,
LUFT_H). Stand bei 49/51 von 60 Episoden je Seed (der Warte-Befehl wurde vom System wegen
Speicherknappheit beendet, die Laeufe liefen weiter):

                                   gegen Kontrolle   gegen hinschauen   gegen Tisch-Farbe
    geliefert                      47 -> 51          49 -> 52           40 -> 52
    McNemar                        10 | 14, p = 0,54  9 | 12, p = 0,66   8 | 20, p = 0,036
    zum WAHREN Ziel (Median)       24 -> 16 mm       16 -> 16 mm        24 -> 16 mm

    Referenz in der Hand gemerkt   160-mal, 1-mal nicht gesehen
    Farbabstand Hand gegen Tisch   meist 0,00-0,06; nur 7 von 160 ueber der Toleranz 0,05
    Blicke beim Ablegen            43 gesehen, 0 falsches Objekt; 84-mal "nicht gesehen"

**Die Vermutung von oben ist damit widerlegt:** die Farbe in der Hand ist fast dieselbe wie auf dem
Tisch, und mit der Hand-Referenz bleibt der Blick ebenso oft "blind" (84 gegen 98). Der Farbfilter
lehnt also etwas ANDERES ab - was, zeigt eine Diagnose, die erst in neuen Laeufen greift (Zeile
`[Objektblick] kein Fleck in der Farbe; nahe: ...` mit Abstand, Farbabstand und Flaeche jedes
nahen Flecks). Die Lieferzahlen liegen alle im Rauschen der online lernenden Paare; der Einbruch
der Tisch-Farben-Reihe (45) wiederholt sich hier nicht und war vermutlich Streuung. Ergebnis:
genauer als die Kontrolle (16 gegen 24 mm), nicht mehr Lieferungen, nicht besser als bloss
hinschauen.

# Gemessen 2026-09-29: warum der Blick "nicht gesehen" meldet (Diagnose)

`ACT23_OBJ_EIG=2`, Diagnosezeile `[Objektblick]` (61b1a33), FSM, Seeds 9811/9812 je 30 Ep:
35 abgelehnte Blicke, eingeteilt nach dem naechsten Fleck im 60-mm-Umkreis der Hand:

    16  nichts in der Naehe - nur Flecken in 29-56 mm Abstand mit ganz anderer Farbe (0,14-0,62):
        das eigene Objekt ist VERDECKT (Klaue/Arm).  Die fernen Flecken sind Nachbarn - genau die,
        die der ungefilterte Blick (40 mm) frueher als "das Objekt" nahm (die 14 Fehlgriffe).
    10  naher Fleck (3-27 mm) knapp ueber der Farbtoleranz (0,055-0,075 bei Toleranz 0,05):
        das eigene Objekt, zu streng abgelehnt.
     9  naher Fleck (7-23 mm) mit deutlich anderer Farbe (0,11-0,26): vermutlich das Objekt mit
        der Klaue zu einem Fleck verschmolzen (Mischfarbe) - nicht geprueft.

Die Blindheit hat also zwei Haelften: eine ehrliche (Verdeckung, knapp die Haelfte) und eine
selbstgemachte (zu enge Toleranz, ein Drittel; dazu die Mischflecken). Naheliegend: Toleranz auf
~0,08 (holt die 10 zurueck, die Nachbarn liegen bei >= 0,14). Gegen die Verdeckung hilft nur ein
anderer Blickwinkel oder die Hand kurz wegnehmen - nicht gebaut.

# Gemessen 2026-09-30: Farbtoleranz 0,08 - sieht mehr, liefert nicht mehr

`ACT23_OBJ_EIG=2`, `ACT23_OBJ_EIG_TOL=0.08` (statt 0,05), sonst wie die Hand-Referenz-Reihe,
dieselben 120 Szenen:

                                   Toleranz 0,05    Toleranz 0,08
    Blicke gesehen / nicht gesehen 49 / 103         70 / 77
    falsches Objekt (> 8 mm)       0                4
    nachgefuehrt                   18 von 72        25 von 73
    geliefert                      59               59     (9 | 9, p = 1,00)
    gegen Kontrolle (56)                            8 | 11, p = 0,65
    zum WAHREN Ziel (Median)       19 mm            19 mm

**Die gelockerte Toleranz holt die knapp abgelehnten Blicke zurueck (+21 gesehen, 4 falsche) und
fuehrt oefter nach - an Lieferungen und Endlage aendert das nichts.** Die 19 Fehlablagen liegen beim
Oeffnen im Median 40 mm daneben und werden meist gar nicht gesehen (verdeckt). Damit ist die
Hinschau-Linie ausgeschoepft: sie macht die mittleren Ablagen genauer (22 -> 17-19 mm), die
Fehlablagen sind ueberwiegend verdeckte Objekte, die die Kamera aus dieser Lage nicht sehen kann.
Alle Schalter bleiben aus.

# Verwandt

* [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md)
* [Ablage-Schwelle im Teacher](/befunde/ablage-schwelle-im-teacher.md) (widerlegt)
