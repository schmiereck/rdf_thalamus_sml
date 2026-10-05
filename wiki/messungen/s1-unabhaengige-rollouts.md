---
type: Messvorschrift
title: S1 - eingefrorener unabhängiger Rollouttest und Positions-Latent-Port
description: Neue Seeds 211/307 ohne Nachtraining, gleiche Grenzen und Horizonte; Gelenkpositionen als expliziter Körpermodell-Eingang erhalten.
tags: [s1, servo, latent, koerpermodell]
status: stable
evidenz: gemessen
ebene: pruefstand
sources:
  - resource: /befunde/s1-online-kopf.md
    title: Eingefrorener Online-Kopf und vorausgehendes Diagnosetor
  - resource: ../../src/pc_cvnn/act23_s1_transition_collector.py
    title: Unveränderte Physik des Sammlers mit neuem evaluation-only-Ausgabemodus
---

# Vor Datenerhebung festgelegt

Checkpoint `log/s1-online-readout-20261003/model.npz` einschließlich Encoder, Online-Kopf
und Normalisierung einfrieren. Batch-Kopf nur Referenz. Keine neuen Fits oder Updates.
Neue Sammelseeds **211 und 307**, je **20 ganze Rollouts mit 60 Übergängen**, insgesamt
2.400 ausschließlich Testzeilen. Derselbe Simulator, gleiche inneren Stell-/äußeren
Encodergrenzen, zehn Physikschritte pro Übergang, maximal 0,025 rad Stellimpuls wie bisher.
Neue Seeds und Trajektorien sind unabhängig vom früheren Seed 101, aber kein Test eines
anderen Roboters oder einer anderen Dynamik. Alle neuen Zeilen sind mit split=test markiert.

Tor vorab: je Seed und gepoolt MSE <=0,90 von Persistenz, auf mindestens 4/5 Gelenken besser.
Keine Seed-/Epochen-/Lernratenauswahl nach Ergebnis. Bei Grenzverletzung Lauf als unvollständig
markieren, keine verwertbaren Teilzeilen herauspicken. Rohdaten nicht überschreiben.
Protokollieren: einzelne Gelenke und Rollouts, tatsächlichen Vorhersagehorizont, Normalisierung
außerhalb des Trainingsbereichs nicht anpassen, SHA vor/nachher für Modell und Arrays.

# Nutzerwunsch: Latent-Eingang für ein künftiges Körpermodell

Der 24-komplexe Latent f(z(q,qvel,ctrl_next)) ist bereits verfügbar, aber aktionsbedingt.
Er darf nicht als reiner Lagezustand ausgegeben werden. Positionsinformation wird deshalb
zusätzlich als fest benannter, direkt reversibler Positionsblock **exp(i*q)** erhalten.
Das ist Sensorcodierung, keine gelernte FK, keine analytisch erkannte Handposition und
keine Inverse-Kinematik. Im unterstützten Bereich -pi <= q < pi ist q via angle exakt
bis auf Rundung wieder verfügbar; mehrfache Umdrehungen benötigen später einen eigenen Vertrag.

Geplanter isolierter Adapter: gemessener Positionsblock, eigener Block für Geschwindigkeiten,
separater gelernter Übergangs-Latent und getrennte vorhergesagte nächste Position.
Auch der Stellbefehl ist explizit Eingabe, nicht mit Messung verwechseln. Gelenkreihenfolge,
Einheiten, Vorhersagehorizont, Code-/Encoder-Version und Eingabe-Sequenznummern festhalten.
Bestehende ArmModule-Ports casten auf float: komplexe Vektoren als abwechselnd Re/Im packen,
sonst würde der Imaginärteil verloren gehen. Kein Patch des globalen Port-Typs.

Kein zusätzlicher q-Decoder wird auf neuen Testdaten gelernt. Der Positionsblock muss
ohne Training reversibel und unabhängig vom Stellbefehl sein. Der 24er-Latent bleibt direkt
für lernende Verbraucher verfügbar. Diese stabile Schnittstelle erspart späteres inverses
Lernen allein zur Rückgewinnung der Gelenkposition; das eigentliche Körpermodell muss seine
Zusammenhänge weiterhin lernen. Noch keine Verbindung zum produktiven ACT23-Körpermodell.

# Kontrollen

Port-Roundtrip samt Imaginärteil, gleiche Messung bei anderem Befehl, unterschiedliche
Übergangs-Latents bei anderem Befehl, unveränderte Vorhersage gegenüber dem eingefrorenen
S1-Weg, Herkunft/Frische von Ports, Parameter-Freeze. Prüfport als Testverbraucher, kein
vorgeblich fertiges Körpermodell. Ein sequenzieller Prozess/ein BLAS-Thread; vorab 4,83 GiB frei.

# Ausführung und Abschluss

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:ACT21_HEADLESS='1'
& ..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_s1_transition_collector.py --output log\s1-independent-neu\seed211 --seed 211 --rollouts 20 --transitions 60 --evaluation-only
& ..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_s1_transition_collector.py --output log\s1-independent-neu\seed307 --seed 307 --rollouts 20 --transitions 60 --evaluation-only
& ..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_s1_independent_eval.py --data-root log\s1-independent-neu --output-dir log\s1-independent-eval-neu
& ..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\test_servo_latent.py --output log\s1-independent-eval-neu\port-controls.json
```

Neue Verzeichnisse erforderlich. [Abgeschlossener Befund](/befunde/s1-unabhaengige-rollouts.md):
beide Seeds und gepoolt bestanden. [Positions-/Übergangs-Port](/mechanismen/servo-latent-port.md)
gebaut und separat geprüft, Körpermodell noch nicht produktiv angeschlossen.
