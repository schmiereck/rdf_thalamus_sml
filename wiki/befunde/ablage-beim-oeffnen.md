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

# Verwandt

* [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md)
* [Ablage-Schwelle im Teacher](/befunde/ablage-schwelle-im-teacher.md) (widerlegt)
