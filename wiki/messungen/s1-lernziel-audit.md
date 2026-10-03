---
type: Messvorschrift
title: S1 - Lernziel, Nullprior und konvergiertes Training trennen
description: Drei festgelegte generative Varianten, bedingte Köpfe mit identischer Parametrisierung und direkte lineare Referenz.
tags: [s1, pc-cvnn, audit, lernziel]
status: stable
evidenz: gemessen
ebene: pruefstand
sources:
  - resource: /befunde/s1-energie-inferenz.md
    title: Ausgangsbefund und verbleibende Trainingsfrage
  - resource: ../../src/pc_cvnn/act23_s1_objective_audit.py
    title: Kontrollierter Offlinevergleich
---

# Vor dem Lauf festgelegt

Weiterhin derselbe druckfreie Datensatz, 40/10 ganze Rollouts, Seed 17, 24 komplexe latente
Dimensionen, zwölf Epochen, Lernrate 0,004, gleiche initiale W, keine Zeitkopplung und keine
Parameter-/Epochensuche. Normalisierung nur aus Training. Vorhandener Testsplit bleibt
Diagnosesplit, kein unabhängiger neuer Generalisierungsnachweis.

Energie `0.5 * lambda * ||z||² + 0.5 * ||[x,y] - W.T f(z)||²` im Training;
im Test fällt nach exakter Elimination des freien Ausgabeknotens dessen Fehlerterm weg.

| Variante | Aktivierung | lambda | Zustandslösung |
|---|---|---:|---|
| A | radiales tanh | 1 | L-BFGS-B, Gradient nach jedem Aufruf geprüft |
| B | Identität | 1 | komplexes lineares Gleichungssystem |
| C | Identität | 0 | kleinste Norm aus Least Squares, explizite Wahl bei Nicht-Eindeutigkeit |

Ein Aufruf darf erst lernen/gewertet werden, wenn der tatsächliche maximale komplexe
Gradient <1e-5 ist. A startet jeweils bei Null, maximal 2.048 Iterationen, gtol 1e-9,
ftol 1e-15. Kein Erfolgsflag ohne Gradientenprüfung. Fehlschlag bricht den Vergleich ab,
statt einen unkonvergierten Zustand still zum Training zu verwenden.

A gegen den vorigen Lauf prüft konvergiertes Training bei gleicher Energie; verschiedene
lokale Lösungen durch den anderen Solver sind bei tanh nicht ausgeschlossen. B gegen A
entfernt die Nichtlinearität. C gegen B entfernt den Prior, aber beseitigt auch Eindeutigkeit:
24 latente Dimensionen für 20 beobachtete Komponenten können bei vollem Rang alle
Trainingszeilen bereits mit zufälligen Decodern exakt rekonstruieren. Dann verschwindet
das Rekonstruktions-Lernsignal. Diese mögliche Degeneration wird explizit gemessen.

Zusätzliche vorab festgelegte Kontrollen:

* Für jede Variante W_x einfrieren. Merkmale f(z(x)) aus **nur x** inferieren, auch im Training.
  Einen neuen komplexen linearen W_y ohne Bias per Least Squares ausschließlich auf den
  Trainingsmerkmalen und y fitten (rcond=1e-10). Gleiche Kopfparametrisierung wie zuvor.
  Dies ändert Lernziel/Löser für den Kopf, nicht dessen Kapazität oder den eingefrorenen Encoder.
  Es isoliert nicht alleine Zielzugang, Onlineoptimierung und globale Least-Squares-Lösung.
* Direkte reelle lineare Regression x→y als Informations-/Lernbarkeitskontrolle, ohne Bias
  in normalisierten Koordinaten, nur Training. Keine vorgeschlagene Roboterpolicy.
* Analytische Kontrollaufgabe für lineare Inferenz; numerischer Gradiententest der
  nichtlinearen Zielfunktion. Parameterfreiheit der Evaluation und Masken/Splits prüfen.

Pro Variante werden MSE, Fehler je Gelenk und ganzem Rollout, Norm/Änderung der W,
Trainingsresiduen sowie Gradienten protokolliert. Historisches Tor weiterhin <=0,90 des
Persistenzfehlers und mindestens 4/5 Gelenke besser; hier diagnostisch, keine Integration.
Nicht beste Variante auswählen und weiter tunen. Bei Befund erst neuen Vertrag festlegen.

Eigenes Ergebnisverzeichnis und NPZ, keine PKL oder Simulation; ein BLAS-Thread.
Vor Start 4,06 GiB RAM frei bei zwei aktiven fremden Python-Läufen.

# Ausführen und Ergebnis

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
& ..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_s1_objective_audit.py --output-dir log\s1-objective-neu
& ..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\test_s1_objective_audit.py --run-dir log\s1-objective-neu --output log\s1-objective-neu\leakage-controls.json
```

Der zweite Befehl ist die nachträglich ergänzte Zielvergiftungs-/Replay-Kontrolle und eine
Negativkontrolle mit vertauschten Trainingszielen. Er verändert keine Modelle oder Quelldaten.
Neue Ergebnisverzeichnisse/-dateien erforderlich. Abbruch bei verfehltem Konvergenztor.
Abgeschlossener [Befund](/befunde/s1-lernziel-audit.md): generatives Training weiter negativ,
bedingte Köpfe erschließen das Signal; Prior entfernen allein degeneriert.
