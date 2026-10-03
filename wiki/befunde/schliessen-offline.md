---
type: Befund
title: Die Schliess-Entscheidung offline - die Policy kann sie, bis auf ein 4-mm-Band und den Stillstand
description: Am Puffer und Netz des gelernten Zustands gemessen - ueber 16 mm ueber dem Greifpunkt will die Policy praktisch nie schliessen (0-3 %), darunter folgt sie dem Teacher. Die alte Zahl "schliesst in 30 % der Schritte zu hoch" war ein Zaehlartefakt (der Riegel wertet j5 = 0,53 statt 0,54 als Schliesswunsch). Echt bleiben ein unscharfes Band 12-16 mm (24 %) und ein Stillstand, den der Policy-Zustand nicht sehen kann. Die Selbst-Imitation speichert die Wuensche VOR dem Riegel; sie zu bereinigen bewegt das Band nur 24 -> 19 %.
tags: [act23, schliessen, riegel, reflex, policy, laufzeit-regeln]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5.5, at: 2026-10-03T00:00:00Z }
sources:
  - id: zustand
    resource: "act23_state.pkl 7a3f7a2d (Kopie), runtime._X/_Y (24000 DAgger), runtime._Xi/_Yi (12000 Selbst-Imitation), runtime.net"
    title: Puffer und Netz
---

# Frage

Schritt 3 der [Laufzeitregeln](/mechanismen/laufzeit-regeln.md): Riegel (`CLOSE_GUARD`) und Reflex
(`REFLEX`) laufen in act23 zur Laufzeit. Die Riegel-Messung vom 25.08. schloss: "die Policy
kommandiert das Schliessen zu hoch, in 29 % der Schritte - sie hat das Verhalten nie gelernt".
**Warum** sie das tun sollte, obwohl der Teacher eine klare Hoehenschwelle vorgibt, war nie
untersucht.

# Messung (offline, kein Lauf)

Zustaende der Anfahrt: Hand innerhalb 3 cm ueber dem Objekt, Objekt ruht (cz < 20 mm), Klaue offen
(j5 > 0,45). Hoehe = Hand ueber dem Greifpunkt `obj_h + GRASP_OFFSET (+ Auflage)`. "Schliessen
beginnen" = j5 < 0,50 (der Teacher schliesst sanft: `j5 - 0,2`, also 0,34 aus offen).

| Hoehe | Teacher-Etikett | Netz | Selbst-Imitation-Etikett |
|---|---|---|---|
| 6-12 mm | 65 % | 77 % | 100 % |
| **12-16 mm** | **0 %** | **24 %** | **48 %** |
| 16-20 mm | 0 % | 0 % | 2 % |
| ueber 20 mm | 0 % | 1-3 % | 6-11 % |

Und das Absenken (Zielhoehe minus Hand, ueber 12 mm): Netz median -31 mm, Teacher -36 mm; "senkt
nicht" 9 % bei 12-20 mm, 0-1 % darueber.

# Lesart

1. **Die Policy hat den Schliesszeitpunkt im Wesentlichen gelernt.** Die 29-30 % "zu hoch" der
   Riegel-Messung zaehlten jedes `j5 < J5_OPEN` (0,54); das Netz gibt oben im Median 0,52-0,53
   aus - Regressionswackeln, kein Schliesswunsch. Der Zaehler `riegel_wuerde` misst also fast nur
   Rauschen. Neu: `frueh zu` in der Riegel-Zeile zaehlt `j5 < 0,45` ueber 12 mm.
2. **Echt ist ein Band von 0-4 mm zu frueh** (12-16 mm: 24 %). Ursache ist ueberwiegend die
   Regression einer harten Stufe mit einem glatten Netz: die Selbst-Imitation zu bereinigen (885
   von 12000 Etiketten auf "offen", `ACT23_IMIT_UMETIKETT`) senkt das Band nur 24 -> 19 %.
3. **Die Selbst-Imitation speicherte Wuensche statt Ausgefuehrtes** - Wuensche, die der Riegel
   abfing, wurden zum Vorbild. Behebbar mit `ACT16_IMIT_AUSGEFUEHRT` (Vorgabe 0, noch nicht
   gemessen).
4. **Der Reflex rettet keinen Absenk-Unwillen**, sondern einen physischen Stillstand ueber
   12 mm: dort schliesst der Teacher nie, und der Policy-Zustand hat **keine Bewegungsgeschichte**,
   an der ein Stillstand erkennbar waere. Eine Policy kann diese Entscheidung so nicht lernen -
   das ist eine Luecke im Zustand, kein Lernversagen.

`ebene: pruefstand` - sagt nichts darueber, was ein Abschalten auf act23-Ebene kostet. Das misst
das A/B, das daran anschliesst.

# Verwandt

* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md)
* [Griffglaube und Tastsinn](/befunde/griff-glaube-und-tastsinn.md) - "der Abstieg kommt nie zum
  Stillstand" (40/40) - gemessen am Fingerdruck-Ersatz, ein anderes Kriterium als `guard_stall`
