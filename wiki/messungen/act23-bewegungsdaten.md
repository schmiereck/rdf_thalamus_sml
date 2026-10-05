---
type: Messvorschrift
title: Native ACT23-Bewegungsdaten und gemessener Positionsport v2
description: Sechs Servo-Messkanäle, unveränderte ACT23-Bewegung und Kamera, getrennte Läufe vor neuem Modelltraining.
tags: [act23, s1, servo, latent, datensatz]
status: stable
evidenz: vermutung
ebene: pruefstand
generated: { by: codex, at: 2026-10-04 }
---

# Entscheidung

Nutzerauftrag: tatsächlichen ACT23-Arbeitsbereich verwenden. Keine neu erfundene Gelenkbox;
Bewegungen kommen aus nativen ACT23-FSM-Episoden mit dessen Objektplatzierung. Roboterkamera
`overview` bleibt bei unverändertem Blick und 240×240. [Arbeitsposen-Audit](/befunde/act23-arbeitsposen-kamera.md)
ist die Grundlage. Dieses Paket bereitet Daten und Schnittstellen vor, trainiert keinen Forecast.

# Datenvertrag vor Erhebung

* Eigene eingefrorene Kopien der historischen Basis. Seed 431: vier Trainings-Episoden;
  Seed 443: vier Test-Episoden. Je Episode neue native Slot-Szene. Keine zufällige Zeilentrennung.
  Alle Phasen einschließlich Aufbau/Nachlauf und Fehlversuche speichern; kein Erfolgssampling.
* Beobachter liest direkt vor und nach jedem **unveränderten** `sim.step(n)` innerhalb der
  Ausführung sechs gemessene q, qvel und die wirklich angelegten sechs Stellwerte. Genau ein
  Aufruf mit dem ursprünglichen n. Keine zusätzliche Physik und keine umgestellten Aktuatoren.
* Stellwerte müssen während dieses Aufrufs konstant bleiben. Zeitdifferenz muss n×Physikdt
  entsprechen. ACT23 ruft im Bewegungszyklus `step(2)` bei dt=0,002 s: primär **4 ms**, nicht
  der alte 20-ms-S1-Horizont. Andere Aufruflängen behalten und getrennt bilanzieren, nicht
  als gleich lange Schritte ausgeben. Keine Übergänge über Episoden-/Zustandsresets erfinden.
* Jede 25. aufgezeichnete Transition erhält vor/nachher je ein natives RGB-Bild mit row_id
  und Seite 0/1. Alle Zwischenübergänge behalten. Keine Segmentierungs-/Handpositionslabels
  im Übergangsdatensatz, keine Druck- oder Kontaktsensoreingaben. Der native Ausführer selbst
  behält seine vorhandenen Hilfen; dies ist noch keine autonome neu gelernte Servopolicy.
* Prüfung: endliche Daten, zeitliche und sensorische Anschlussgleichheit innerhalb Episoden,
  korrekte Bildpaarzuordnung, Positions-Rundlauf <1e-12 rad, identische Zustandsdateihashes
  und unveränderte Lernkomponenten. Alle ungültigen Positionen bleiben im Protokoll; ein
  verletztes Tor sperrt den Datensatz für den nächsten Fit. Persistenz-MSE je Horizont/Gelenk
  nur als Ausgangskontrolle, kein Vergleich verschiedener Horizonte als Lerngewinn.

# Positionsvertrag v2

Separater gemessener Port für `joint_0..joint_5`, einschließlich Greifer. Zwölf Re/Im-Werte
`[cos q0,sin q0,...,cos q5,sin q5]`; Geschwindigkeit separat als sechs Werte. Kein Befehl
und kein gelernter Forecast nötig, um Position bereitzustellen. Kein inverses Netztraining.

Explizite Darstellungsdomäne `[-0,1; pi+0,1]` rad für jeden Encoder umfasst nominale Gelenkwege
und kleine dynamische Überschreitungen. **Keine neuen Aktuator-/Sicherheitsgrenzen.** Bei
Verletzung abweisen statt abschneiden. Rücklesen mit einem um pi/2 zentrierten Phasenzweig;
die Domäne ist kürzer als 2pi und reversibel. Neue Schema-ID:
`joint-phase-v2/6/ReIm-interleaved/rad/[-0.1,pi+0.1]`.

`MeasuredServoModule` liefert nur gemessene Position/Geschwindigkeit, keine ungeprüfte
S1-Prognose. Alte v1-Ports und Checkpoints bleiben unverändert. Frische/Invalidierung wie
bei v1: gleiche gehaltene Messung nicht neu melden, neue Messgeneration schon; fehlende
Messung als fehlend ausgeben. Noch nicht produktiv in ACT23 verdrahtet.

# Ausführung

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\test_measured_servo.py
..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_workpose_camera_audit.py --state src\pc_cvnn\state\dream_rsi_d0_20260917\base.pkl --output log\act23-transitions-20261004\train431 --seed 431 --episodes 4 --split train
..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_workpose_camera_audit.py --state src\pc_cvnn\state\dream_rsi_d0_20260917\base.pkl --output log\act23-transitions-20261004\test443 --seed 443 --episodes 4 --split test
```

Rohübergänge: `transitions.jsonl`, Bildpaare: `transition-camera.npz`. Native Sichtbarkeits-
Diagnose weiterhin getrennt. Für Wiederholung neue Ordner. Vier Episoden je Split sind eine
erste Datengrundlage, keine allgemeine Sim-to-Real-Validierung. Erst danach eigener Fit-Vertrag.

**Abgeschlossen:** [Befund](/befunde/act23-bewegungsdaten.md), 9.014 gültige Übergänge und
362 Kamerabildpaare. Beide Läufe und sämtliche Integritätsprüfungen abgeschlossen; kein Fit.
