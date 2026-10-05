---
type: Befund
title: Das Episodenende entscheidet der Agent selbst - und das Orakel endete zu frueh
description: Im Netzbetrieb endete eine Episode, sobald die WAHRE Objektlage im Ziel lag (Orakel aus MuJoCo). Ersetzt durch "getragen (Fingerdruck) + eigene Hand ueber dem eigenen Ziel auf Ablagehoehe, 5 Schritte ruhig". Gepaartes A/B, 8 Seeds x 50 - Orakel 53,1 %, selbst 60,7 %, Seeds 7:1 (p = 0,07), Intervall [+0,7, +14,4]. Das Orakel feuerte, waehrend die Hand noch absenkte; 60 seiner Enden landeten daneben. Unterwegs gefunden - die Policy kann nicht loslassen, weil das Orakel ihr diese Aufgabe immer abnahm.
tags: [act23, episodenende, privileg, tastsinn, laufzeit-regeln, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-10-05T00:00:00Z }
sources:
  - id: code
    resource: "0955be7 (pc_act16 ENDE_SELBST, Endgrund-Zeile [Ende]); act23 setzt ACT16_ENDE_SELBST=1 als Vorgabe"
    title: Umbau
  - id: lauf
    resource: "Kopflos, Kopie des Zustands 7a3f7a2d, ACT23_NO_PERSIST=1, Seeds 9041-9048 je 50 Ep, ACT23_SZENE_JE_EPISODE=1 ACT23_AUTO_CURIOUS=0 ACT23_EIG_DIREKT=1 ACT23_EIG_STETIG=1 ACT16_GOAL_Z=1 ACT16_GRIFF_Z=1, Choreo netz, Marker-Ablage; Arm O Orakel, Arm E ACT16_ENDE_SELBST=1; je Seed parallel. Ein erster Durchgang wurde nach ~27 Episoden wegen Speichermangels abgebrochen und verworfen"
    title: A/B-Lauf 2026-10-05
---

# Was das Ende bisher entschied

Im Netzbetrieb (`policy_fn` gesetzt) endete `run_combined` durch

1. **das Orakel**: `|wahre Objektlage - Ziel| < tol und cz < 35 mm` - ein Privileg aus MuJoCo,
2. die Zaehlung der Phasenmaschine in "release",
3. Zeitbudgets (`PHASE_STALL` 500 Schritte je Phase, `cap`).

# Was es jetzt entscheidet

`ACT16_ENDE_SELBST=1` (in act23 Vorgabe): fertig, wenn der Agent **getragen** hat (Fingerdruck
> 0,3 N bei geschlossener Klaue, Hand ueber 40 mm) und jetzt **haelt, mit der Hand ueber dem
eigenen Ziel** (`tgt`, die selbst festgelegte Ablagestelle) auf Ablagehoehe (`tgt_z + 15 mm`),
5 Schritte lang - oder die Klaue geoeffnet hat und keinen Druck mehr spuert. Keine wahre
Objektlage. Die Phasenmaschine beendet nicht mehr; die Zeitbudgets bleiben. Jede Episode
schreibt `[Ende] <Grund> nach <n> Schritten`.

# Was unterwegs auffiel: die Policy laesst nicht los

Die erste Fassung verlangte "Klaue geoeffnet". Sie feuerte nie:

* Die Policy senkt bis zur Ablagehoehe und **haelt fest** - der Druck faellt hoechstens einen
  Schritt lang ab, die Klaue oeffnet nie ueber 0,18-0,23 rad (offen ab 0,30).
* Grund: das Orakel beendete jede Episode **vor** dem Loslassen; geoeffnet hat immer die
  Aufraeumbewegung danach. Im Puffer sind Ablage-Zustaende selten (DAgger 399 von 24000, Etikett
  98 % "oeffnen", Netz oeffnet 28 %), und die Selbst-Imitation etikettiert sie zu **0 %** mit
  "oeffnen" - sie hat "am Ziel festhalten" als Erfolgsrezept gelernt.
* Offline: die Ablage-Etiketten der Selbst-Imitation auf "oeffnen" zu setzen hebt das Netz nur
  von 28 auf 26 % (Median 0,34 -> 0,43). Phasen-Gewichtung ist seit August gemessen gescheitert
  (`ACT23_PHASE_W`) und wurde nicht wiederholt.

Deshalb entscheidet der Agent jetzt das **Ende**; das **Loslassen** bleibt wie bisher die
Aufraeumbewegung. Selbst loslassen ist ein eigener offener Faden.

# Ergebnis

| Seed | Orakel | selbst |
|---|---|---|
| 9041 | 30/48 | 31/48 |
| 9042 | 28/50 | 27/50 |
| 9043 | 25/50 | 33/50 |
| 9044 | 26/50 | 28/50 |
| 9045 | 22/50 | 29/50 |
| 9046 | 28/49 | 31/49 |
| 9047 | 26/50 | 28/50 |
| 9048 | 26/50 | 34/50 |
| **gesamt** | **211/397 = 53,1 %** | **241/397 = 60,7 %** |

* Differenz +7,6 Punkte, 95 %-Intervall [+0,7, +14,4]; Seeds 7:1 (Vorzeichentest p = 0,07);
  McNemar 44:74 (p = 0,007, als Episoden-Test zu optimistisch, s. [Messvorschrift](/messungen/act23-headless-ab.md)).
* Endabstand median 23 -> 20 mm. Je 3 Episoden "nicht gefunden" (dieselben Aufgaben).
* Endgruende: Orakel 269 (davon **60 nicht geliefert**), Budget 128 (2 geliefert). Selbst: "am
  Ziel abgesetzt" 240 (38 nicht geliefert), selbst losgelassen 9, Budget 148 (**38 geliefert**).
  Schritte median 589 gegen 639.

# Lesart

**Das Privileg faellt, und es kostet nicht nur nichts - es schadete.** Das Orakel feuert im
Moment, in dem die wahre Objektlage in den 25-mm-Kreis eintritt und das Objekt unter 35 mm ist -
also oft, waehrend die Hand noch absenkt. Die Aufraeumbewegung oeffnet dann aus der Bewegung, und
60 dieser Enden landen daneben. Der Agent wartet, bis seine Hand fuenf Schritte ruhig ueber seinem
Ziel steht. Dass nach Seeds nur 7:1 bei p = 0,07 steht, haelt den Gewinn im Rahmen "sehr
wahrscheinlich", nicht "belegt"; belegt ist, dass das Abschalten nicht schadet.

# Offen

* **Selbst loslassen** - die Policy oeffnet am Ziel nicht; das Orakel hat es ihr nie abverlangt.
* 148 Budget-Enden: Episoden, die weder ankommen noch aufgeben. Ein "ich gebe auf" fehlt.

# Verwandt

* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md)
* [Riegel und Reflex entfernt](/befunde/riegel-reflex-entfernt.md) - dasselbe Muster: ein Eingriff
  von aussen verhinderte, dass das Netz einen Teil der Aufgabe lernt
