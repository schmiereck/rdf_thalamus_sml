---
type: Messvorschrift
title: S1 mit isolierter Energie-Inferenz
description: Mathematisch geprüfte Inferenz und explizit zeitloser Lebenszyklus vor erneuter Offlinebewertung auf dem vorhandenen S1-Split.
tags: [s1, engine, audit, pc-cvnn]
status: stable
evidenz: gemessen
ebene: pruefstand
sources:
  - resource: ../../src/pc_cvnn/energy_pc.py
    title: Isolierte Referenzengine
  - resource: ../../src/pc_cvnn/test_energy_pc.py
    title: Unabhängige Ableitungs- und Lebenszyklustests
  - resource: ../../src/pc_cvnn/act23_s1_energy_forward.py
    title: Festgelegter S1-Vergleich
---

# Vor dem S1-Lauf festgelegt (2026-10-03)

Energie und Ableitungen entsprechen dem [Auditvertrag](/befunde/pc-engine-mathematik-audit.md).
energy_pc.py ist ein separates Referenzmodell, kein Patch oder alternativer Standard für ACT23.
Es besitzt W, Zustände und explizite Clamp-Masken, aber kein V. Zeitmodus ist ausschließlich
`off`; `frozen`/`learn` werden zurückgewiesen. commit_step ist explizit wirkungslos.
Reset löscht Zustände und Clamps, hält W unverändert. Jede Probe setzt ihre Clamps neu.
Nichtendliche Werte werden als Fehler gemeldet. Keine Zufallsinitialisierung im Sensorzustand.

Alle Faktoren eins, top-Knoten haben einen quadratischen Nullprior. Simultane Zustandsableitung
mit komplexer Konjugation, vollständigem radialem tanh-Jacobian und 1/Eingangsanzahl.
Armijo-Rückwärtssuche sichert den Energieabstieg bei festen W; keine Behauptung globaler
Konvergenz bei nichtlinearen Netzen. Ein lokaler W-Gradientenschritt folgt nach der Inferenz.
Kein Decay/Clipping und keine heuristischen Rückgabefaktoren in diesem Referenzvertrag.

Die Validierung besteht vor S1: 18 Graphfälle (drei Seeds, sechs Kombinationen von Aktivierung,
Komplexität und Eingangsanzahl), zentrale unabhängige Differenzen aller Zustände und W.
Maximaler relativer Fehler 1,26e-9. Exakter Gegenfall fällt 0,50 → 0,41.
Analytische lineare Inferenz weicht maximal 1,46e-9 ab; bekanntes nichtlineares Decodieren
lernt W auf MSE 1,50e-31. Nichtlineare freie Inferenz erreicht Gradient <1e-9.
Rohbeleg: `log/energy-pc-20261003/validation.json`.

Ergänzende Randfallkontrollen während des S1-Laufs bestehen ebenfalls:
tanh-Jacobian bei Null, nahe Null und Sättigung (maximal 5,56e-11), zyklischer Graph mit
Selbstverbindung (5,53e-10), unabhängige Vorhersage nach fremden vorigen Clamps und sichere
Rückwärtssuche bei übergroßer Startschrittweite (56 Verkleinerungen).
Beleg: `validation-extended.json` im selben Verzeichnis. Dabei wurde nur das Testskript
erweitert; die laufende Inferenzimplementierung und das S1-Rezept blieben unverändert.

# Festes S1-Rezept

Bestehende 3.000 druckfreie Übergänge, 40/10 ganze Rollouts, Seed 17, 24 latente Dimensionen,
zwölf Epochen, Lernrate 0,004. W-Initialisierung entspricht dem historischen S1-Netz.
Jede Zeile startet bei Null; keine zeitliche Zustandsübernahme und kein Testziel in der Inferenz.
Training und Test verwenden bis zu 128 Schritte, Startschrittweite 0,08, Gradiententoleranz 1e-5.
Jede Probe meldet Restgradient und Konvergenz. Falls sie die Schrittgrenze erreicht, ist sie
nicht automatisch konvergiert. Nach jeder Epoche wird Fortschritt geschrieben.

Nach abgeschlossenem Training wird auf demselben eingefrorenen Checkpoint zusätzlich jede
Testinferenz um höchstens 2.048 Schritte bei Toleranz 1e-7 fortgesetzt. Diese vorher festgelegte
Diagnose misst den Effekt endlicher Relaxation, sie wählt keine neuen Trainingsparameter.
Primäres Tor bleibt 128-Schritt-MSE <=0,90 der Persistenz und Verbesserung auf mindestens 4/5 Gelenken.

Normalisierung ausschließlich aus Training; Spalten mit std <1e-6 werden in Training und
Test stumm. Alle Streuungen und Masken werden protokolliert. Der Hinweis stammt aus Claudes
Policy-Fix 59c85c4: beinahe konstante Eingaben dürfen nicht unbemerkt riesig verstärkt werden.
Die dortige physikalische Schwelle 0,5 mm ist nicht auf gemischte Winkel/Geschwindigkeiten
übertragbar. Diese S1-Regel ist nur ein Schutz gegen numerisch konstante Spalten, keine
allgemeine Lösung für späteres Nachtraining mit veränderten Eingangssignalen.

Vergleich mit alten Zahlen ist deskriptiv: Neben Ableitungen ändern sich Zeitbehandlung,
Reset pro Probe, Schrittbudget und Regularisierung. Keine isolierte Effektzuweisung an
eine einzelne Korrektur. Der bereits verwendete Testsplit liefert eine technische Gegenprüfung,
keine neue unabhängige Generalisierungsbestätigung. Kein Tuning bei Verfehlen des Tors.

# Ausführen und Ressourcen

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
& ..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\test_energy_pc.py --output log\energy-pc-neu\validation.json
& ..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_s1_energy_forward.py --output-dir log\s1-energy-neu
```

Neue Ergebnisverzeichnisse erforderlich. Manifest mit Daten-/Code-SHA und Rezept, Fortschritt,
W-Checkpoint als eigenes NPZ, Vorhersagen und Ergebnis-JSON. Kein Simulator, keine PKL.
Vor Start 4,18 GiB physischer RAM frei; zwei fremde Python-Läufe je etwa 0,56 GiB.
Nur ein zusätzlicher Prozess mit einem BLAS-Thread vorgesehen.

# Ergebnis und zusätzliche Solver-Gegenprüfung

Der [Befund](/befunde/s1-energie-inferenz.md) enthält die abgeschlossenen Zahlen und Grenzen.
Wegen unvollständiger Konvergenz der Testinferenz wurde nach dem festgelegten Lauf derselbe
Checkpoint ohne Nachtraining zusätzlich mit exakt eliminiertem freiem Ausgabeknoten geprüft:

```powershell
& ..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_s1_energy_checkpoint.py --checkpoint-dir log\s1-energy-20261003 --output-dir log\s1-energy-checkpoint-neu
```

Dies ist eine nachträgliche technische Solver-Diagnose, kein Teil des vorab fixierten primären
Leistungstors und keine Auswahl eines anderen Modells. Der Audit bricht ab, wenn eine Probe
die ursprüngliche Gradiententoleranz 1e-5 verfehlt oder sich der Checkpoint verändert.
