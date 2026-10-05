---
type: Messvorschrift
title: ACT23-Arbeitsposen mit unveränderter Roboterkamera
description: Vier native eingefrorene ACT23-FSM-Episoden, phasenweiser Kamera-/Encoderabgriff und getrennte Sichtbarkeitsevaluation.
tags: [act23, s1, koerpermodell, kamera]
status: stable
evidenz: vermutung
ebene: pruefstand
generated: { by: codex, at: 2026-10-04 }
---

# Verbindliche Vorgabe

Der Nutzer bestätigt: `overview` entspricht der Kamera am physikalischen Arm. Kameraposition,
Blickrichtung und Sichtfeld bleiben unverändert. Es wird das native ACT23-Bild mit 240×240
Pixeln erfasst, kein 24×24-B1-Zielbild und keine zusätzliche Kamera.

# Aufbau

`act23_workpose_camera_audit.py` startet den tatsächlichen `run_self_learning_steering`-Pfad
des Codex-Worktrees kopflos. Eigene Kopie von `dream_rsi_d0_20260917/base.pkl`, D0_FREEZE und
NO_PERSIST; vier FSM-Episoden, Seed 421, vier Objekte pro Szene, neue native Slot-Anordnung
je Episode. Keine erzwungene Objektliste: ACT23 wählt aus den tatsächlich platzierten Objekten.
Alle Bewegungen und Platzierungen erfolgen im bestehenden ACT23-Pfad. Der Zustand ist der
historische Forschungsstand, nicht der aktuelle gelernte Zustand des parallelen Agenten.

Der Beobachter umschließt ausschließlich im Auditprozess `run_combined`, erhält vorhandene
Hooks und liest vor/nach jeder Episode sowie beim ersten und jedem 15. Schritt jeder Phase
RGB, gemessene Gelenklage und Greiferwinkel. Kein neuer Controller. Native Lernkomponenten
werden vor/nach den Episoden über die vorhandenen D0-Manifeste verglichen; Original und Kopie
des Zustands bleiben hashgleich. Weltmodell-Startbewertung aus, kein neues Körpermodelltraining.

Separater Evaluator zählt sichtbare Klauenpixel pro Phase sowie Objektpixel vor Ausführung.
Segmentierung bleibt in separater NPZ-Datei und liefert keine Trainingsetiketten. Nach jedem
Evaluatorbild muss ein neues RGB-Bild bitgleich zum unmittelbar vorherigen sein; Physikzeit,
Gelenkzustand und Kameraparameter dürfen sich dabei nicht ändern.

Zusätzlich Anteil der Arbeitsposen außerhalb der bisherigen S1-Gelenkbox protokollieren:
ein bestandener Forecast in dieser Box rechtfertigt keine ungeprüfte Extrapolation nach ACT23.
Keine Auswahl erfolgreicher Episoden. Vier Episoden sind eine diagnostische Stichprobe,
kein allgemeiner Sichtbarkeitsnachweis und kein Wirksamkeits-A/B. Home/Anfahrt von Greif- und
Tragephasen unterscheiden. Fehlende Phasen als fehlend belassen.

# Ausführung

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_workpose_camera_audit.py --state src\pc_cvnn\state\dream_rsi_d0_20260917\base.pkl --output log\act23-workpose-20261004
```

Neuer Ausgabeordner erforderlich. `act23.log` enthält Fortschritt; Rohbeobachtungen und
privilegierte Evaluation sind getrennt. Nach Ergebnis Wiki und Forschungsplan fortschreiben.

**Abgeschlossen:** [Befund](/befunde/act23-arbeitsposen-kamera.md). Vollständiger Export unter
`log/act23-workpose-20261004-r3` nach zwei dokumentierten Exportkorrekturen. Kamera bestätigt
für diese Stichprobe; 238/238 Ansichten mit Klaue, alle Stellungen außerhalb der alten S1-Box.
