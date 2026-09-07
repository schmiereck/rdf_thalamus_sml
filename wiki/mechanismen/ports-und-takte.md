---
type: Mechanismus
title: Ports, Takte und die Bitgleichheits-Pruefung
description: Der PCModule-Port-Umbau und die logischen Raten. Enthaelt die schaerfste Pruefmethode des Projekts - Laeufe sind deterministisch, also muss jede Etappe BITGLEICH sein.
tags: [act23, architektur, ports, methodik]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-08-25T00:00:00Z }
verified: { by: human:thomas, at: 2026-08-25T09:07:00Z }
sources:
  - id: plan
    resource: "Nutzerplan 2026-08-23, Punkte 1-5"
    title: aus der Frage nach Thread-Parallelisierung entstanden
---

# Stand des Umbaus

    1. Erst messen, wohin die Zeit geht     ERLEDIGT - meine MuJoCo-Vermutung WIDERLEGT
                                            (Physik + Rendern 2,9 %; EIN Netz 73,4 %)
    2. Verkehr durch die Ports (ArmAgent)   4 Kanten; 7 Datenfluss-Callbacks offen
    3. Nummer und Frische im Port           GEBAUT; Paarung an den Lernstellen offen
    4. Logische Raten messen                GEMESSEN, s. unten
    5. Threads                              von Punkt 1 erledigt: nicht gerechtfertigt

**Punkt 1 fuehrte zu etwas anderem als geplant:** statt Threads wurde die PC-Engine
**vektorisiert** (`relax_vec.py`) - Netzschritt 291,6 -> 25,7 ms (11,3x), Episode 60,8 -> 21,0 s
(2,9x). Danach ist `Policy.fit` (`runtime.train(epochs=200)` je Episode auf 24000 Zeilen) mit
~47 % der groesste Posten - und das ist **echte Rechenarbeit**, kein Overhead (groessere Batches
machen es schlechter).

**Ausgangsbefund zu Punkt 2:** die Connector-Schicht war zur Laufzeit **komplett inert** -
`ArmAgent` 0x in act23, kein Modul las je den Port eines anderen, `ArmModule.step()` hatte genau
einen Aufrufer, den niemand rief. Zehn Module befuellten dreissig Out-Ports, die nie jemand las.

Der Umbau laeuft in Etappen, weil (a) der vorhandene Portsatz die echten Schnittstellen nicht
beschreibt (fuer `size_fn`/`wrist_fn`/`orient_fn`/`carry_target_fn` gibt es keinen Port) und
(b) `run_combined` von **sieben** Dateien benutzt wird.

# Die Pruefmethode, die alles traegt

> Laeufe sind bei gegebenem Seed **deterministisch**. Jede Etappe wird gegen einen gespeicherten
> Lauf verglichen und muss **BITGLEICH** sein (Seed 101, 6 Episoden, geladener Zustand
> schreibgeschuetzt, gleiche Threadzahl; Zeitstempel, `[Zeit]` und Commit-Zeile ausgenommen).

Das ist ungleich schaerfer als ein statistischer A/B-Vergleich. Zwei Fallen, beide real
eingetreten:

* **Gepickelte Module haben spaeter deklarierte Ports nicht** (`__init__` laeuft beim Laden
  nicht) -> `_ensure_ports()` / `Port.__setstate__`. Sonst `KeyError` auf dem Live-Zustand.
* **Der Portpfad fuehrt stille Veralterung ein**, wo ein Argument per Konstruktion frisch ist.
  Deshalb muss Punkt 3 vor Punkt 4 kommen - live gefunden an der kumulativen Servo-Korrektur
  (`pc_act16:412`), die eine gehaltene Sichtung doppelt zog.

Nicht jede Kante ist umsteckbar: `track_fn` war act23-Code, der mehrere Module orchestriert -
dort musste erst ein `PerceptionModule` entstehen. `goal_fn` ist gar kein Modul-Datenfluss,
sondern die Kommando-Schnittstelle.

# Logische Raten - Traegheit nur im Planer

Punkt 4 des Nutzerplans: "messen, ob ein langsamer Planer ueber einer schnellen Wahrnehmung dem
Agenten gut tut". 12 Seeds x 10 Episoden = 120 je Arm, gepaart:

    A   alles Rate 1        62/120 = 51,7%                                        25 mm
    B1  REGLER Rate 2       49/120 = 40,8%   -10,8 [-22,9; +1,8]  p=0,120   39 mm  (Abstand p=0,039)
    B2  PLANER Rate 2       63/120 = 52,5%   + 0,8 [-11,6; +13,3] p=1,000   26 mm  (Abstand p=0,549)
    B3  WAHRNEHMUNG Rate 2  49/120 = 40,8%   -10,8 [-22,9; +1,8]  p=0,120   43 mm  (Abstand p=0,039)

> **Traegheit ist nur im PLANER erlaubt.** Wahrnehmung und Regelung muessen beide schnell laufen.

Kein Test reisst die vorangemeldete Schranke, aber drei Blickwinkel zeigen dasselbe Muster, und
die Planer-Aussage ist die belastbarere: ihr Intervall liegt **eng um null**, ein Schaden ueber
~12 Punkte ist ausgeschlossen.

**Warum das im Nachhinein erwartbar ist:** die Runtime-Policy ist **kein Planer**, sondern ein
reaktiver Regler, der bild-fuer-bild das Teilziel nachfuehrt. Der echte Planer in act23
(`curious_pick` + Latent-Goal-Servo) laeuft ohnehin nur einmal je Episode, also ~150x langsamer
als die Wahrnehmung: die vom Nutzer gemeinte Konfiguration **existiert im System bereits**.

Knoepfe: `ACT23_PERCEPT_RATE`, `ACT23_POLICY_RATE`, `ACT23_PLAN_RATE` (alle Vorgabe 1;
Rate 1 ist bitgleich zum Zustand vor dem Umbau).

# Fallen

* **Eine Messung wiederholen, wenn sich die Voraussetzung geaendert hat.** B1 lief zuerst ohne
  die Frische-Wache und liess je Episode ~220 falsch gepaarte Zeilen (frischer Zustand,
  veraltete Aktion) ins Lernen. Der Verdacht, der -10,8-Nachteil sei dieses Artefakt, war
  falsch - die Quote ist identisch, nur der Median-Abstand ging 31 -> 39 mm.
* B1*, B1 und B3 haben zufaellig **alle** 49/120, aber 0 von 12 Seeds sind identisch. Gleiche
  Summen heissen nicht gleiche Laeufe.

# Verwandt

* [Modullandschaft](/mechanismen/act23-modullandschaft.md)
* [Kopfloses A/B](/messungen/act23-headless-ab.md)
