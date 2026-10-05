---
type: Messvorschrift
title: S1-PC-Vorwärtsmodell - direkte Stellwerte sagen Encoderfolge voraus
description: Isolierter komplexwertiger PC-Experte sagt q_next aus q, qvel und direktem ctrl_next voraus; Bewertung nur auf ganzen zurückgehaltenen Servo-Rollouts.
tags: [act23, dream-rsi, s1, servo, propriozeption, pc-cvnn]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: codex, at: 2026-09-27T08:00:00Z }
---

# Vertrag

Der Experte erhält ausschließlich den normalisierten Kontext `(q, qvel, ctrl_next)` mit 15
Werten und sagt die fünf Werte `q_next` vorher. Ein komplexwertiger PC-Graph enthält einen
24-dimensionalen latenten Knoten, der beide Sensoren generativ dekodiert. Trainiert wird in
zeitlicher Reihenfolge innerhalb jedes der 40 Trainingsrollouts, zwölf Epochen; zwischen
Rollouts wird nur der flüchtige Netzzustand zurückgesetzt. Testrollouts ändern keine Gewichte.

Referenzen sind die starke Persistenzvorhersage `q_next=q` und die konstante Trainingsmitte.
Primäres Maß ist MSE in rad² auf zehn ganzen Testrollouts. Der Kandidat besteht nur bei höchstens
0,90 des Persistenz-MSE **und** geringerem Fehler auf mindestens vier der fünf Gelenke. Bei
Verfehlen folgt kein Parameter-Tuning und keine Motorpolicy.

```powershell
..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_s1_pc_forward_audit.py `
  log\s1-proprio\seed101-50x60-safe --output log\s1-pc-forward\seed17.json
```

Der Audit liest den Quellmanifest und bricht ab, falls Druck, Kontakt/Objekt oder Teacher/IK
entgegen dem S1-Vertrag markiert sind. Er schreibt keinen Aktuator und keine ACT23-Datei.

# Ergebnis Seed 17: verworfen

Der Audit verarbeitet 2.400 Trainings- und 600 ganze Testzeilen ohne Split-Leck. Der PC-Experte
erreicht auf den Testrollouts MSE `0,021131` rad², die konstante Referenz `0,065823` rad² und
die Persistenz `q_next=q` jedoch nur `0,000138` rad². Damit beträgt der PC-/Persistenzquotient
153,59 statt höchstens 0,90; auf keinem der fünf Gelenke ist der PC-Fehler kleiner als
Persistenz.

Der Kandidat verfehlt beide vorab gesetzten Tore. Es folgen weder mehr Epochen, andere
Latentgröße noch eine Motorpolicy. Der Befund steht in
[S1-PC-Vorwärtsmodell](/befunde/s1-pc-vorwaertsmodell.md).
