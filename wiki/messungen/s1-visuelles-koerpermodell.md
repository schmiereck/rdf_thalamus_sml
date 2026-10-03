---
type: Messvorschrift
title: S1-B1 - Positions-Latent als Eingang eines visuellen Körpermodells
description: Erster isolierter Verbraucher lernt die beobachtete Kameraansicht aus Gelenkphasen; keine Handpositionsetiketten.
tags: [s1, koerpermodell, latent, selbstlernen]
status: stable
evidenz: vermutung
ebene: pruefstand
generated: { by: codex, at: 2026-10-03 }
sources:
  - resource: ../../src/pc_cvnn/act23_s1_visual_body.py
    title: Erhebung und isolierter lernender Verbraucher
  - resource: ../../src/pc_cvnn/test_s1_visual_body.py
    title: Gradienten-, Konstantspalten- und Checkpointkontrollen
---

# Entscheidung und Abgrenzung

Der erste lernende Verbraucher des [Positionsports](/mechanismen/servo-latent-port.md)
sagt die **gleichzeitig beobachtete Kameraansicht** voraus. Eingang sind direkt die zehn
Re/Im-Komponenten der fünf Gelenkphasen, ohne Rückdecodierung nach q. Ziel sind 24×24×3
RGB-Werte, durch gleichmäßiges 4×4-Mittelpooling aus der festen 96×96-Übersichtskamera.
Das ist eine neue Aufgabe: propriozeptive Lage mit sichtbarem Körper verknüpfen.
Keine Handlokalisierung, kein Greifzustand und noch kein autonomer Regler.

Begründung: Der [D0b-Landmark](/befunde/d0b-hand-selbstbewegung.md) ist nicht bestanden.
Sein Schwerpunkt oder die verworfenen Fovea-Köpfe dürfen deshalb keine Handetiketten liefern.
RGB und Encoder sind auch am realen Roboter messbar. Das beweist noch keinen Hardwaretransfer.
Schatten und Hintergrund sind Teil des Bildes; ein Erfolg ist kein Nachweis semantischer
Körpersegmentierung. Auflösung 24 dient nur diesem isolierten Prüfstand, ändert keine Fovea.

# Vorabvertrag B1

* Zwei vollständig getrennte Erhebungen: Seed 401, 160 Trainingsposen; Seed 409, 64 Testposen.
  Je Pose direkte Servo-Stellwerte im bestehenden S1-Kommandobereich, 400 Physikschritte
  Einschwingen, dann Encoder und Bild ohne dazwischenliegenden Physikschritt lesen.
  Gripper joint_5 fest auf HOME, tatsächliche Stellung und Geschwindigkeit protokollieren.
  Objekte als feste Versuchsanordnung außerhalb des Blickfelds parken.
* Alle Posen behalten. Grenzverletzungen, nichtendliche Werte oder maximale Armgeschwindigkeit
  >0,05 rad/s machen die Datenerhebung ungeeignet; dann kein Training. Gripper-Spannweite
  über beide Sätze höchstens 0,01 rad. Keine still entfernten Fehlschläge.
* Synchronisationsprotokoll: Bild und Position gleicher sample_id und sim_time. Eine spätere
  Hardwarekopplung braucht echte Zeitstempel, zulässige Latenz und Enthaltung bei Veraltung.
* Verbraucher: neues isoliertes reelles MLP 10→64 tanh→1728 linear, Seed 17, Adam 400
  Vollbatch-Schritte, lr=0,003. Re/Im bedeutet keine Behauptung einer nativen PC-Engine.
  Nutzervorgabe erlaubt andere Architekturen. Eingangsnormalisierung ausschließlich Training;
  konstante Spalten erhalten Skala 1, sonst Untergrenze 1e-3. Ziel nur um Trainingsmittel
  zentrieren, keine pixelweise Verstärkung und kein Clipping bei der Auswertung.
* Kontrollen: Trainingsmittelbild und gleiches Netz mit vertauschter Zuordnung der
  Trainingsbilder (Permutation Seed 918). Identische Initialisierung und Trainingsdauer.
  Keine Testzeile in Normalisierung, Fit, Modellwahl oder Trainingsabbruch.
* Tor: Test-MSE mindestens 10 % unter Mittelbild, sowohl im ganzen Bild als auch auf
  veränderlichen Pixeln (Trainingsvarianz, über RGB gemittelt, >1e-4). Mindestens 16 solcher
  Pixel erforderlich; andernfalls unzureichende visuelle Abdeckung. Zusätzlich mindestens
  10 % unter vertauschter Kontrolle auf diesen Pixeln. Ergebnisse pro Pose veröffentlichen.
  Keine nachträgliche Schwellen-/Breiten-/Epochenwahl auf diesem Testsplit.

# Folge des Ergebnisses

Bestanden: nur Erlaubnis zu unabhängiger Replikation und danach Vorhersage der Folgeansicht
aus dem bereits geprüften Servo-Forecast. Die statische Abbildung lernt zunächst allein
`position_latent`; `transition_latent` wird nicht ungeprüft als Körperlage bezeichnet.
Verfehlt: B1 dokumentieren und Ursache untersuchen; keine automatische ACT23-Integration.
Ein späteres Körpermodell kann aktuelle und vorhergesagte Position mit demselben visuellen
Decoder verwenden. Inverse Motorik ist eine eigene Aufgabe, nicht nötig, um Position zu erhalten.

Gemeinsame PKLs, bestehendes BodyModel, produktive PC-Engine und ACT23 bleiben außerhalb dieses
Prüfstands. Artefakte liegen in einem eigenen neuen Verzeichnis; Wiederüberschreiben wird abgewiesen.

# Ausführung und Ergebnis

```powershell
$env:ACT21_HEADLESS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\test_s1_visual_body.py
..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_s1_visual_body.py collect --output log\s1-visual-body-20261003\train401 --seed 401 --count 160
..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_s1_visual_body.py collect --output log\s1-visual-body-20261003\test409 --seed 409 --count 64
..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_s1_visual_body.py train --output log\s1-visual-body-20261003\fit --train-data log\s1-visual-body-20261003\train401 --test-data log\s1-visual-body-20261003\test409
```

Bei Replikation neue Ausgabepfade verwenden. [B1-Ergebnis](/befunde/s1-visuelles-koerpermodell.md):
Erhebung und technische Kontrollen bestanden, Vorhersagetor verfehlt. Kein laufendes Training.
