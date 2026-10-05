---
type: Messvorschrift
title: S1 - bedingten Ausgabekopf lokal online lernen
description: Fester lokaler komplexer Delta-Update auf demselben eingefrorenen tanh-Encoder gegen Batch-Referenz.
tags: [s1, online, pc-cvnn, lernziel]
status: stable
evidenz: gemessen
ebene: pruefstand
sources:
  - resource: /befunde/s1-lernziel-audit.md
    title: Ausgangsbefund und erfolgreiche bedingte Batch-Referenz
  - resource: ../../src/pc_cvnn/act23_s1_online_readout.py
    title: Training und Kontrollen
---

# Vor dem Training festgelegt

W_x aus `log/s1-objective-20261003/tanh_prior1.npz` bleibt eingefroren. Für jede Zeile
werden dieselben Merkmale f(z(x)) mit geprüftem Gradienten <1e-5 inferiert. Kein Zielzugriff
bei dieser Inferenz. Da W_x eingefroren und Inferenz deterministisch ist, dürfen die Merkmale
einmal berechnet und für Training und Auswertung gespeichert werden.

Ein neuer W_y startet mit der historischen zufälligen S1-Initialisierung (Seed 17), nicht
mit der Batch-Lösung oder dem generativ trainierten Kopf. Gleiche 24 komplexe Eingänge und
fünf Ausgänge, kein Bias. Lokale Lernregel für `0.5 ||y-W_y.T f||²`:

`W_y += 0.004 * outer(conj(f), y-W_y.T f)`.

Zwölf Epochen in derselben zeitlichen Reihenfolge über die 2.400 Trainingszeilen aus 40
Rollouts. Genau ein Update je Zeile, kein Batch-Löser im Onlinepfad, kein Shuffle, kein
Decay/Clipping, keine Parametersuche. „Online“ bezeichnet hier die einzelne lokale
Gewichtsaktualisierung beim Offline-Replay, noch keinen lernenden Simulationslauf.

Referenzen: untrainierter Kopf, bisheriger generativer Kopf, bedingter Batch-Kopf mit
identischer Parametrisierung und Persistenz. Testauswertung erst nach feststehenden zwölf
Epochen, auf denselben bekannten zehn Diagnoserollouts. Keine unabhängige Freigabe daraus.
Tor weiterhin MSE <=0,90 der Persistenz und mindestens 4/5 Gelenke besser.

Kontrollen: numerischer Gradient der tatsächlichen Update-Regel, bekannte komplexe Abbildung,
unveränderte Parameter bei Vorhersage/Lernrate null, Trainingsnormalisierung und disjunkte
Rollouts, bitgleiche Merkmale/Vorhersagen zur Batch-Referenz, Byte-Fingerabdruck des Encoders.
Alle Epochen liefern nur Trainingsmetriken; kein Auswählen einer Epoche nach Testwerten.

Artefakte in eigenem neuem Verzeichnis, kein PKL/Simulator/Produktionspatch. Ein BLAS-Thread;
vorab 4,44 GiB RAM frei bei einem fremden aktiven Python-Lauf.

# Ausführung und Abschluss

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
& ..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_s1_online_readout.py --output-dir log\s1-online-readout-neu
```

Das Verzeichnis muss neu sein. Kontrollen laufen vor dem Training; Manifest und
Fortschrittsdatei werden geschrieben, anschließend eigenes Modell-NPZ und Ergebnis-JSON.
Der [abgeschlossene Befund](/befunde/s1-online-kopf.md) erfüllt das Diagnosetor mit
Faktor 0,0874 gegen Persistenz und 5/5 verbesserten Gelenken. Neue unabhängige Rollouts fehlen.
