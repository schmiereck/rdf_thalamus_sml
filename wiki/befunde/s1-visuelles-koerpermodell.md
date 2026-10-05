---
type: Befund
title: S1-B1 - Visueller Körperdecoder lernt Trainingsposen, verfehlt neue Posen
description: Der erste Verbraucher der Gelenkphasen bleibt auf 64 neuen Posen 28 Prozent schlechter als das Mittelbild.
tags: [s1, koerpermodell, latent, selbstlernen]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: codex, at: 2026-10-03 }
sources:
  - resource: /messungen/s1-visuelles-koerpermodell.md
    title: Vorabvertrag und reproduzierbare Befehle
  - resource: ../../src/pc_cvnn/act23_s1_visual_body.py
    title: Datenerhebung, VisualBody und Kontrollen
  - resource: ../../src/pc_cvnn/test_s1_visual_body.py
    title: Mathematische und Lebenszykluskontrollen
  - resource: ../../log/s1-visual-body-20261003/fit/result.json
    title: Gesamtergebnis einschließlich MSE je Testpose und Trainingsverlauf
  - resource: ../../log/s1-visual-body-20261003/fit/diagnostics.json
    title: Nachgelagerte beschreibende Kontrolle ohne Nachtraining
---

# Behauptung

Ein isolierter lernender Verbraucher des Positions-Latents ist gebaut und auf selbst
erhobenen Encoder-/Kamerapaaren trainiert. Sein erstes Tor ist **verfehlt**: Unbekannte
Posen werden schlechter vorhergesagt als durch das konstante Trainingsmittelbild.
Das ist kein Gegenbeleg zur Brauchbarkeit des Positions-Latents an sich und widerlegt
nicht die bestandene propriozeptive S1-Vorhersage.

# Aufbau

160 Trainingsposen Seed 401, 64 vollständig getrennte Testposen Seed 409. Fünf direkte
Servo-Stellwerte, keine IK, kein Teacher, keine Druckdaten, keine geometrischen Handetiketten.
Je Pose nach 400 Schritten Einschwingen Bild und Encoder zum gleichen Simulationszeitpunkt.
MLP 10→64→1728 sieht direkt `[cos q0, sin q0, ...]`; kein inverses Netz rekonstruiert q.
Beobachtetes RGB ist das selbst erzeugte Ziel. Aktionsbedingter S1-Latent und Servo-Forecast
werden in B1 noch nicht benötigt. Vorab festgelegte 400 Adam-Schritte, kein Test-Tuning.

Dies ist eine Python-API (`VisualBody.predict(position_latent_batch)`), noch kein produktiv
verdrahtetes ArmModule. Ein Portwert kann direkt als Zeile dieser Matrix eingehen. Gespeicherte
Modelle lassen sich mit `VisualBody.load()` wieder laden. Bestehendes BodyModel bleibt erhalten.

# Zahlen

| Messgröße | Ergebnis |
|---|---:|
| Nach dem Einschwingen außerhalb der S1-Grenzen | 0 / 224 |
| Maximale Armgeschwindigkeit Training / Test | 9,10e-5 / 8,76e-5 rad/s |
| Spannweite fest gehaltener Greifer | 0,001241 rad |
| Veränderliche Pixel gemäß Trainingsvarianz | 178 / 576 |
| Trainings-MSE Mittelbild | 0,00172092 |
| Trainings-MSE nach letztem Update | 0,000223146 |
| Test-MSE Mittelbild | 0,00120399 |
| Test-MSE Körperdecoder | 0,00154129 |
| Test-MSE mit vertauschten Trainingsbildern | 0,00409216 |
| Testverhältnis Decoder / Mittelbild, gesamtes Bild | 1,28015 |
| Testverhältnis Decoder / Mittelbild, variable Pixel | 1,28056 |
| Testverhältnis Decoder / vertauschte Kontrolle, variable Pixel | 0,37562 |
| Testposen mit kleinerem Fehler als Mittelbild | 17 / 64 |

Erforderlich waren jeweils Verhältnisse ≤0,90. Die echte Paarung schlägt die vertauschte
Kontrolle deutlich, verfehlt aber beide Mittelbildvergleiche. Die gesamte Erhebung wurde
behalten; keine Testpose entfernt. Einzelne Posen sind keine unabhängigen Roboterläufe;
eine Initialisierung und eine feste Kamera begrenzen die Aussage.

Finite-Differenzen-Kontrolle der vier Parameterblöcke: maximal 1,23e-10 Fehler. Konstante
Eingangsspalten werden ignoriert und nicht millionenfach verstärkt. Ungültige Phasen werden
abgewiesen. Speichern/Laden erhält Vorhersagen exakt; reine Inferenz verändert keine Gewichte.
Die Prüfung lief zunächst in eine Sandbox-Sperre für temporäre Dateien; der Kontrolltest nutzt
deshalb einen NPZ-Speicherpuffer. Der echte Trainingscheckpoint auf Platte wurde zusätzlich
geladen und auf bitgleiche Vorhersagen geprüft.

# Bewertung und nächste Entscheidung

Trainingsfehler sinkt, Testfehler bleibt deutlich höher: **fehlende Generalisierung** dieses
ersten Decoders. Daraus lässt sich noch nicht unterscheiden, ob Abdeckung, Bildauflösung,
Netzstruktur oder Regularisierung den Engpass bilden. Kein pauschales Urteil gegen PC-CVNN:
dieser Decoder ist ein isoliertes reelles MLP, keine Änderung der produktiven PC-Engine.

Die vier fest ausgewählten Ansichten (Testpose 0,16,32,48; `fit/views.png`) zeigen viel
unveränderten Hintergrund und Armteile am rechten Bildrand. Diese Sichtkontrolle ist keine
quantifizierte Handabdeckung. Auch ein bestandenes Bild-MSE-Tor hätte noch keine genaue
Handreferenz geliefert. Schatten können das Ziel ebenso mitbestimmen wie der sichtbare Arm.

**Nächster sinnvoller Schritt:** Kamera-/Posenabdeckung und Generalisierung getrennt auditieren,
bevor ein weiterer Trainingskandidat festgelegt wird. Klären, ob der relevante bewegte Körper
im gewählten Kameraraum ausreichend sichtbar und aufgelöst ist; vorhandene Paare dafür nutzen.
Eventuelle Simulatorgeometrie nur in getrenntem Evaluator, niemals als Trainingsetikett.
Danach neuer vorab festgelegter Trainings-/Testvertrag mit frischen Testdaten, falls ein
begründeter neuer Kandidat entsteht. Kein Nachoptimieren auf Seed 409 und keine Integration.

Der Nutzerwunsch bleibt erfüllt: gemessene Position steht unverändert und reversibel als
eigener Latentblock bereit. Die Verknüpfung mit visuellen Folgen ist jetzt konkret lernbar
und prüfbar gemacht, aber in dieser ersten Ausführung noch nicht bestanden.

# Artefakte

**Nachfolgender Audit:** [Kamera- und Gelenkraumabdeckung](/befunde/s1-koerpermodell-abdeckung.md)
ist geprüft. Beide Klauen liegen in 145/224 Posen außerhalb des Bildes. Der RGB-Fehler bleibt
auch innerhalb der Trainingshülle über dem Mittelbild; Sichtbarkeit erklärt ihn nicht allein.
Nächster Schritt ist ein geeigneter Körperblick vor einem neuen Trainingsvertrag.

`log/s1-visual-body-20261003/`: Rohbilder, gleichzeitig gemessene q/qvel, Gelenkphasen,
Zeitstempel und Zielbilder in `train401/samples.npz` und `test409/samples.npz`; zugehörige
Manifeste enthalten SHA256. `fit/model.npz`, `shuffled-model.npz`, `predictions.npz`,
`result.json`, `diagnostics.json`, `views.png` lokal erhalten. Die Bildtafel beschneidet nur
die Anzeige auf [0,1]; die MSE verwendet unbeschnittene Vorhersagen.

Checkpoint-SHA256: `04aa5fbe344963dff321e395f3bee57369cb4046ebe8edd12961b22123386e66`.
Keine gemeinsame PKL gelesen oder geschrieben; kein Lauf mehr aktiv.
