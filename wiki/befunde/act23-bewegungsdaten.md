---
type: Befund
title: Native ACT23-Bewegungsdaten und Positionsport v2 bereit
description: 9014 geprüfte Übergänge, 362 native Kamerabildpaare und reversible Positionen aller sechs Servos im tatsächlichen Arbeitsbereich.
tags: [act23, s1, servo, latent, datensatz]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: codex, at: 2026-10-05 }
sources:
  - resource: /messungen/act23-bewegungsdaten.md
    title: Vorab festgelegter Daten- und Positionsvertrag
  - resource: ../../src/pc_cvnn/act23_transition_recorder.py
    title: Passiver Beobachter nativer Physikaufrufe und Datenprüfung
  - resource: ../../src/pc_cvnn/measured_servo.py
    title: Reversibler Positionscode v2
  - resource: ../../src/pc_cvnn/arm_modules/measured_servo.py
    title: Optionaler gemessener Sechs-Servo-Port
  - resource: ../../src/pc_cvnn/test_measured_servo.py
    title: Grenz-, Rundlauf-, Frische- und Zeitschrittprüfungen
  - resource: ../../log/act23-transitions-20261004/dataset-summary.json
    title: Zusammenfassung beider Läufe mit erneut geprüften Artefakthashes
---

# Ergebnis

Die Datengrundlage wurde auf **tatsächliche ACT23-Arbeitsbewegungen** umgestellt. Keine
unabhängig gewürfelten Gelenkendstellungen mehr. Native Objektplatzierung, FSM und overview
240×240 unverändert; Originalkamera bleibt an den vorgesehenen Hardwareaufbau gebunden.
Sechs gemessene Positionen einschließlich Greifer stehen zusätzlich als reversibler
Positions-Latent bereit. Es wurde noch kein neues Vorwärts-/Körpermodell trainiert.

| Größe | Training Seed 431 | Test Seed 443 |
|---|---:|---:|
| Ganze Episoden mit eigener Slot-Szene | 4 | 4 |
| Übergänge insgesamt | 3.035 | 5.979 |
| Davon 4 ms, native Bewegungsschritte | 2.863 | 5.807 |
| 8 ms | 160 | 160 |
| 40 ms | 4 | 4 |
| 80 ms | 8 | 8 |
| Kamerabildpaare, je 240×240 vorher/nachher | 122 | 240 |
| Ungültige Positionscodierungen | 0 | 0 |
| Zeit-/Sensoranschlussbrüche innerhalb Episoden | 0 | 0 |
| Persistenz-MSE bei 4 ms, Mittel über sechs Gelenke | 2,17205e-5 rad² | 1,75062e-5 rad² |

Gesamt: 9.014 Übergänge, davon 8.670 mit 4 ms, und 362 Bildpaare. Längere Aufrufe sind
vollständig erhalten und dürfen nicht als 4-ms-Zeilen in denselben Fit rutschen. Der alte
S1-Prädiktor wurde für 20 ms und fünf Gelenke geprüft; diese Zahlen sind kein direkter
Leistungsvergleich mit ihm. Persistenz ist lediglich eine Ausgangskontrolle, kein Lernergebnis.

# Integrität und Bedeutung

Jede Zeile enthält gemessene q/qvel, an den Simulator übergebene Servostellwerte `d.ctrl`,
gemessene q_next/qvel_next, Zeiten, Physikschrittzahl, Episode/Phase, Split und Positionscode.
Ein nativer `sim.step(n)` wird genau einmal mit unverändertem n ausgeführt. Stellwerte sind
innerhalb dieses Aufrufs konstant. Bildpaare sind über row_id und Seite 0/1 zugeordnet.
Keine künstlichen Übergänge über Episoden-/Szenenwechsel. Kameraaufnahmen stammen aus der
nativen Render-API am jeweiligen Abgriff; eine zusätzliche Kalibrierung von Renderer- oder
späterer Hardwarelatenz ist damit nicht behauptet.

Originalbasis und beide Arbeitskopien bleiben hashgleich, Lernkomponenten laut D0-Manifeste
unverändert. SHA256 der JSONL- und Kameraartefakte beim Abschluss erneut geprüft. Alle
Fehlversuche bleiben erhalten. Druck, Kontakte und geometrische Handpositionen sind keine
Eingabespalten dieses Übergangsdatensatzes. Der vorhandene ACT23-Ausführer behält seine
bisherigen Hilfen: die Erhebung ist keine neu gelernte autonome Servosteuerung.

Der separate Sichtbarkeitsaudit findet eine Klaue in 203/212 Trainingsansichten und 411/411
Testansichten. Die neun fehlenden Ansichten liegen beim Heben/Tragen. Das präzisiert die
vorherigen 238/238 einer anderen Stichprobe, widerspricht aber nicht deren Messung. Keine
Sichtbarkeitsgarantie, kein Entfernen unsichtbarer Abschnitte; keine Kameraänderung.

# Positionsinformation für das Körpermodell

`MeasuredServoModule`: Eingang q6 und optional qvel6; Ausgang zwölf interleaved Re/Im-Werte
für `exp(i*q)` und separat sechs Geschwindigkeiten. Kein Befehl nötig, kein Forecast und
keine Verbindung zum ungeprüft extrapolierten alten S1-Checkpoint. Noch nicht produktiv
in ACT23 verdrahtet. Alte Schnittstellen und Checkpoints bleiben unverändert.

Schema `joint-phase-v2/6/ReIm-interleaved/rad/[-0.1,pi+0.1]`. Rücklesen auf einem um pi/2
zentrierten Phasenzweig ist im deklarierten Intervall eindeutig. Die Grenzen sind eine
Darstellungsdomäne, keine neuen Motorgrenzen. Tests: 1.001 Rand-/Zufallsfälle maximal
4,45e-16 rad Rundlauffehler; 238 alte ACT23-Arbeitsposen maximal 2,23e-16 rad. Alle 9.014
neuen Anfangs-/Folgepaare bestehen <1e-12 rad. Ungültige oder mehrdeutige Eingaben werden
abgewiesen, nicht abgeschnitten. Fehlende/gleiche/neue Messgenerationen korrekt behandelt.

Der neue Bereich wird tatsächlich gebraucht: Im Test erreicht joint_4 −0,06627 bis
3,21850 rad, joint_3 bis 3,14180 rad. Kleine dynamische Überschreitungen gehen nicht verloren.
Der gemessene Greifer ist jetzt von Beginn an ein eigener Kanal. Ein Körpermodell muss
diese Positionen nicht später durch inverses Netztraining rekonstruieren.

# Nächster Modellvergleich

1. Vor dem Fit einen eigenen festen Vertrag für sechs Kanäle und 4-ms-Folgepositionen
   formulieren. Lernziel aus tatsächlichen Folgemessungen, kein analytischer FK-Teacher.
2. Nur Trainingslauf für Normalisierung/Fit verwenden; Testlauf 443 bleibt vollständig
   außerhalb. Gesamtergebnis, jedes Gelenk **und jede Episode** gegen Persistenz bewerten.
   Training hat 795/639/632/797 Bewegungsschritte je Episode, Test 1522/1009/1076/2200.
   Zeilenquoten allein würden lange Fehlversuche übergewichten. Vier Episoden je Split sind
   weiterhin wenig unabhängige Evidenz; bei Erfolg frischer Lauf erforderlich.
3. Positionsport v2 als gemessene Information erhalten. Der spätere visuelle Körperlerner
   braucht angesichts wechselnder Objektszenen ein geeignetes Ziel oder Szenenkontext;
   das ganze RGB-Bild ist nicht allein durch q bestimmt. Kein Nachoptimieren von B1 auf
   altem Testseed 409 und keine neue Kamera.

# Artefakte

`log/act23-transitions-20261004/train431/` und `test443/`: `transitions.jsonl`,
`transition-camera.npz`, `result.json`, native Beobachtungen, getrennte Klauenevaluation,
Episodenprotokolle, Integritätsmanifeste und eigene `state-input.pkl`. Zusammenfassung:
`dataset-summary.json`. Keine aktiven Läufe mehr. Die Phasen-/Geometrieprotokolle dienen
der Diagnose, nicht als zusätzliche Lernfeatures.
