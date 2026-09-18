---
type: Messvorschrift
title: D0 - Trennbarkeit der Y- und T-Formrepräsentation
description: Vorab festgelegte Diagnose, ob der bestehende Formdeskriptor Y und T in frischen, getrennten Ansichten unterscheidet und ob drei Y-Stützansichten T fälschlich beanspruchen.
tags: [act23, dream-rsi, d0, wahrnehmung, formklasse]
status: draft
evidenz: vermutung
ebene: pruefstand
generated: { by: codex, at: 2026-09-18T00:55:00Z }
sources:
  - id: d0
    resource: /befunde/dream-rsi-d0-lernaufgabe.md
    title: D0-Gegenprobe mit T-Fehlanspruechen
  - id: mechanism
    resource: ../src/pc_cvnn/arm_modules/shape_classifier.py
    title: descriptor, resolve und Open-Set-Anspruch
---

# Frage

Die frische D0-Gegenprobe erkennt alle gehaltenen Y-Sichten, beansprucht aber in beiden Seeds
alle vier T-Kontrollen als Y. Diese Sonde trennt zwei Fragen: (a) enthalten die vorhandenen
Deskriptoren unter kontrollierten Blicken ueberhaupt ein Y/T-Signal; (b) reicht dieses Signal
fuer den tatsaechlichen, aus drei Sichten aufgebauten Open-Set-Anspruch aus? Sie misst weder
Armlernen noch eine neue Architektur.

# Vorab festgelegter Aufbau

Zwei neue Seeds 1703 und 1704 erzeugen jeweils einen frischen `ShapeClassifierModule`. Er wird
mit 2500 gerenderten, **ueberwacht** gelabelten cube/L/U-Ansichten trainiert, wie die v2-D0-
Gegenprobe. Y und T bleiben dabei geparkt. Danach werden pro Seed 3 Y-Stuetzansichten und je
32 unabhaengige, zurueckgehaltene Y- und T-Szenen gerendert: andere RNG-Stroeme, zufaellige
Tischpositionen, Yaw und drei Farben. Nur ein Koerper ist sichtbar. Der Auswerter darf die
Koerper-ID erst nach dem Rendern als externe Sollklasse benutzen; der Klassifikator erhaelt
keine T- oder Y-Etiketten.

Die drei Y-Deskriptoren werden als eine hypothetische junge Open-Set-Klasse eingesetzt.
`resolve` bleibt unveraendert und verwendet seine vorhandenen Schwellen. So ist der
Fehlanspruch direkt mit D0 vergleichbar, ohne eine Klassengeburt oder Exemplare zu schreiben.
Als getrennte, explorative Geometrie-Diagnose wird 1-NN mit Leave-one-out auf allen 64
gelabelten Auswertedeskriptoren berechnet. Diese zweite Zahl ist kein erreichbarer
Selbstlern-Algorithmus, sondern die Obergrenze eines lokalen Nachbarn auf genau dieser Menge.

# Primaere Messgroessen und Entscheidung

Primaer je Seed: Anteil der 32 T-Szenen, die die Y-Stuetzklasse beansprucht, sowie Anteil der
32 Y-Szenen, die sie beansprucht. Die Operationalisierung ist fuer diese Aufgabe nur dann
ausreichend getrennt, wenn beide Seeds mindestens 75 % Y-Anspruch und hoechstens 1/32
T-Fehlanspruch zeigen. Sekundaer: Median und 10./90.-Perzentil der minimalen Abstaende von
Y-Stuetzen zu Y bzw. T, relativ zur `OPEN_MARGIN * novel_th`; LOO-1-NN-Trefferquote.

Alle Szenen, Rohdeskriptoren, Schwellen, Quell- und Zustands-Hashes und ein archivierter Runner
werden in einem neuen Ergebnisordner gespeichert. Das Eingabe-Pickle wird nur gelesen. Ein
Absturz, fehlender Detektor oder veraenderter Eingabehash ist ein technischer Fehler, nicht
eine ausgelassene Szene. Ein einzelner Prozess mit einem BLAS-Thread; keine Nachwahl von Seeds
oder Parametern nach Einsicht.

# Aufruf

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
& '../rdf_thalamus_sml/.venv/Scripts/python.exe' src/pc_cvnn/act23_dream_rsi_yt_separation.py `
  --state src/pc_cvnn/state/dream_rsi_d0_20260917/base.pkl `
  --out log/dream_rsi_d0_20260918/yt_separation_01
```
