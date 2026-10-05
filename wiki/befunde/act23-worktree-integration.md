---
type: Befund
title: ACT23-Worktrees integriert und isoliert geprueft
description: main efb3ae2 und Codex daa44af zusammengefuehrt; Freeze um neue Lerner erweitert, FSM- und Netz-Rauchtest bestanden. Keine Aussage zur Lernleistung.
tags: [act23, integration, freeze, koordination]
status: stable
evidenz: einzelmessung
ebene: code
generated: { by: codex, at: 2026-10-05T00:00:00Z }
sources:
  - id: parents
    resource: "main efb3ae2; codex-worktree daa44af; gemeinsamer Vorfahr 15c063e"
    title: Festgehaltene Integrationsbasis
  - id: checks
    resource: "../rdf_thalamus_sml_integration/log/integration-20261005/"
    title: FSM, Netz, Positionsport und mathematische PC-Pruefungen
---

# Umfang und Konfliktaufloesung

Nutzer hat die [kontrollierte Integration](/fragen/aspekte-und-worktree-integration.md)
autorisiert. Separater Worktree `../rdf_thalamus_sml_integration`, Branch
`integration/act23-20261005`, gestartet von main `efb3ae2`; Codex `daa44af` eingemergt.
Keine direkten Aenderungen an Claudes Workspace, main, Umgebung oder Originalzustaenden.

Textkonflikte in `pc_act16.py`, `pc_act23.py` und `wiki/log.md` aufgeloest:
Wahrnehmungs-Hooks von main und Codex-Tracking-Hook gemeinsam erhalten; D0-Freeze fuer
Neuheitslernen und lifelong beibehalten; Groessensammlung und D0-Grenzmanifeste kombiniert.
Wiki-Chronik nach Datum vereinigt, identische Eintraege dedupliziert; alle verlinkten
Quellen beider Chroniken automatisch auf Erhalt geprueft. Beide Kataloge sind enthalten.

# Fachliche Integrationskorrektur

Neue main-Lerner waren im alten D0-Vertrag unbekannt. Die Komponentenliste umfasst jetzt
auch Hoehen-/Groessenschaetzer, Loslass-Kopf, Wort-Bedeutung und Blick-Daten (15 statt 10
Komponenten). Mit `ACT23_D0_FREEZE=1` werden deren Lernpuffer nicht erweitert;
automatische Groessensammlung, optionales Neuetikettieren und Loslass-Nachtraining entfallen.
Ohne D0_FREEZE bleiben diese Pfade aktiv. Keine automatische Aktivierung experimenteller
Servo- oder PC-Module im produktiven Controller.

Bei lokalen Nachbarschaftsschaetzern sind X/y der Lernzustand. Aus unveraenderten X/y
abgeleitete Normalisierungs-Caches duerfen bei Inferenz entstehen; der Vollzustandsabdruck
zeigt sie weiterhin. Regressionstests belegen sowohl diese Unterscheidung als auch die
Erkennung neuer Beispiele und veraenderter Loslass-Gewichte/Wort-/Blickspeicher.

Der Freeze-Befund gilt fuer die Manifeste **vor/nach den Episoden**. Startmigrationen und
Initialisierung sind kein Nachweis einer bitgleichen In-Memory-Darstellung der geladenen
PKL; die Dateien selbst bleiben per Hash unveraendert.

# Pruefungen

* Python-Syntax fuer `src/pc_cvnn` bestanden.
* `test_d0_integrity.py` einschliesslich neuer Lerner und Fovea-Freeze bestanden.
* `test_d0_training_runner.py`, `test_measured_servo.py` bestanden.
* `test_servo_latent.py` mit explizitem historischem Codex-Checkpoint bestanden.
* `test_energy_pc.py` bestanden: numerische Gradienten, Lebenszyklus, analytische
  Gegenkontrolle. Keine Aenderung der produktiven PC-Engine.
* Native FSM, Seed 431, eine Episode: 839 Uebergaenge, 34 Bildpaare, 60 Diagnosesichten.
  Zeit-/Sensoranschluss, sechs Positionskanaele und Bildzuordnung bestanden; keine
  Lernmutation. Quelle historische Codex-Basis `ad9d768c...`, eigene Kopie, beide unveraendert.
* Netz, Seed 431, eine Episode: 234 Tracking-Zeilen, ein Episodenprotokoll, keine Mutation
  der 15 Lernkomponenten. Eigene Kopie von Claudes `act23_state.pkl`, SHA256
  `2f70ac0d9ce2f2c525a8aa519236a6e91fbcf99ddfa536377f8ed969fd63ffa1`;
  Quelle und Kopie unveraendert. Kamera weiterhin overview 240x240.

Vorab waren rund 4 GiB physischer Speicher frei, keine Python-Prozesse sichtbar.
Simulationspruefungen nacheinander, OPENBLAS_NUM_THREADS=1 und OMP_NUM_THREADS=1.
Dies sind Integrations-Rauchtests, kein A/B-Nachweis fuer Lieferquote oder Lernleistung;
optionale Stapel-/Wort-/Blickpfade wurden nicht alle in der Simulation ausgefuehrt.

# Startvertrag und verworfene Pruefversuche

Der aktuelle Claude-Zustand hat eine Policy mit **15 Eingaengen**. Ein erster Netzstart mit
13-Kanal-Vorgabe brach bei der ersten Policy-Inferenz ab (13 gegen 15). Der erfolgreiche
Prueflauf setzt explizit `ACT16_GOAL_Z=1` und `ACT16_GRIFF_Z=1`. Keine Gewichte abgeschnitten,
keine Nullen als Ersatzhoehen erfunden, kein Nachtraining zur Anpassung. Diese Konfiguration
ist beim Wiederverwenden dieses Checkpoints Teil des Vertrags. `pc_act19.py` und
`arm_modules/runtime_policy.py` entsprechen main; der Unterschied entsteht zwischen
Checkpoint-Schema und Startkonfiguration, nicht durch eine neue Policy-Implementierung.

Der erste Aufruf des alten Servo-Port-Tests fehlte um `--output`, der zweite traf auf den im
neuen Worktree fehlenden unversionierten Modellpfad. Mit explizitem lesendem Pfad zu
`../rdf_thalamus_sml_codex/log/s1-online-readout-20261003/model.npz` besteht der Test.

# Weiterarbeit und Uebergabe

Geprueften Integrations-Commit per Fast-forward in `codex-worktree` uebernehmen. Claudes main
bleibt fuer seine laufende Arbeit unveraendert; das Board erhaelt die genaue Commit-ID und
den Hinweis zur spaeteren Uebernahme. Solange main noch efb3ae2 ist, kann Claude zwischen
Laeufen per `git merge --ff-only integration/act23-20261005` denselben Stand uebernehmen.
Falls main weitergelaufen ist, zuerst den neuen Abstand pruefen und erneut kontrolliert
integrieren. Kein Reset oder Ueberschreiben des anderen Worktrees.

Alte [native Bewegungsdaten](/befunde/act23-bewegungsdaten.md) bleiben historische Daten.
Der neue main enthaelt geaenderte Wahrnehmung/Teacher/Endebedingungen. Vor Aussagen zum
aktuellen ACT23 muss die Datengrundlage auf diesem Stand neu festgelegt bzw. erhoben werden;
keine stille Zusammenlegung verschiedener Controllerstaende. Kein neues Modelltraining
waehrend dieser Integration.
