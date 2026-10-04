---
type: Befund
title: ACT23-Arbeitsposen sind mit der bestehenden Roboterkamera sichtbar
description: Vier native FSM-Episoden liefern 238 Ansichten mit sichtbarer Klaue; alle liegen außerhalb der bisherigen S1-Testbox.
tags: [act23, s1, koerpermodell, kamera]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: codex, at: 2026-10-04 }
sources:
  - resource: /messungen/act23-arbeitsposen-kamera.md
    title: Vorab festgelegter Arbeitsposen-Audit
  - resource: ../../src/pc_cvnn/act23_workpose_camera_audit.py
    title: Native ACT23-Ausführung mit separatem Beobachter
  - resource: ../../log/act23-workpose-20261004-r3/result.json
    title: Vollständiger Lauf, Sichtbarkeit und Zustandskontrollen
  - resource: ../../log/act23-workpose-20261004-r3/scenes-evaluation.json
    title: Platzierte Objekte und Sichtbarkeit vor Ausführung
  - resource: ../../log/act23-workpose-20261004-r3/additional-checks.json
    title: Wiederholungsidentität, Gelenkbereiche und Portintervall
---

# Behauptung

Der Nutzerhinweis bestätigt sich in dieser Stichprobe: **Die unveränderte ACT23-Kamera
erfasst die relevanten Arbeitsposen.** Vor Ausführung sind alle 16 platzierten Objektvorkommen
(vier Szenen mit je vier Objekten) sichtbar. Mindestens eine Klaue erscheint in allen 238
abgetasteten Ansichten, beide in 207. Keine Kameraverschiebung, kein neues Sichtfeld.

Die [B1-Sichtlücke](/befunde/s1-koerpermodell-abdeckung.md) entstand bei anders gewählten
Gelenkstellungen. **Alle 238 ACT23-Arbeitsstellungen liegen außerhalb der alten S1-Box.**
Deren Vorwärtsmodell ist deshalb nicht ungeprüft auf diese Arbeitsbewegungen übertragbar.

# Aufbau und Integrität

Tatsächlicher `run_self_learning_steering(headless=True)`-Pfad des Codex-Worktrees, historische
eigene Basis `dream_rsi_d0_20260917/base.pkl` in neue lokale Arbeitskopie kopiert. Kein Lesen
des aktuell bearbeiteten PKL des anderen Agenten. Seed 421, FSM, native vier Slots mit neuer
Zuordnung je Episode. ACT23 bestimmt Objektwahl, Ziel und Bewegung; der Audit steuert nichts.
Overview 240×240, Position `[-0.17, 0.15, 0.32]`, vertikales Sichtfeld 64 Grad unverändert.

Erfasst: erster und jeder 15. Schritt jeder tatsächlich besuchten Phase, zusätzlich vor/nach
der Episode. Bilder und Encoder stammen vom gleichen Physikzeitpunkt. Geometriesegmentierung
nur als separater Evaluator; nach dessen Aufruf RGB bitgleich, qpos, Zeit und Kameraparameter
unverändert. Pixelzahlen beziehen sich auf die beiden Klauenboxen, nicht den gesamten Greifer.
Der bestehende ACT23-Ausführer enthält seine bisherigen Hilfen und Druckprotokolle; daraus
werden hier weder neue Körpermodellinputs noch Trainingsetiketten gewonnen.

Lernzustand laut D0-Vorher/Nachher-Prüfung unverändert; Vollzustand enthält erwartete Änderungen
von Arbeitszuständen/Puffern. Original und Kopie der Basis bleiben SHA256
`ad9d768c1f770c71e92954a303e1f905b3d1a96d0206ca04f6bb172e32c09b9e`.
Kein neues Modelltraining, keine Änderung am produktiven ACT23 oder an der Kamera.

# Zahlen

| Phase | Ansichten | Mindestens eine Klaue sichtbar | Beide sichtbar | Klauenpixel, Median |
|---|---:|---:|---:|---:|
| Vor Ausführung | 4 | 4 | 4 | 325 |
| Anfahrt / over | 81 | 81 | 81 | 170 |
| Absenken / lower | 12 | 12 | 12 | 79 |
| Schließen / close | 34 | 34 | 32 | 43 |
| Heben / lift | 55 | 55 | 48 | 31 |
| Tragen / carry | 22 | 22 | 9 | 7 |
| Absetzen / place | 11 | 11 | 7 | 11 |
| Öffnen / release | 15 | 15 | 10 | 22 |
| Nach Ausführung | 4 | 4 | 4 | 77 |
| Gesamt | 238 | 238 | 207 | — |

Kleinste sichtbare Klauenfläche: 2 Pixel. Sichtbarkeit allein belegt somit noch keine präzise
visuelle Handreferenz, besonders beim Tragen. Gründe für das zeitweise Fehlen einer zweiten
Klaue sind hier nicht separat auf Verdeckung, Projektion und Rasterauflösung zerlegt.
Diese Messpunkte sind zeitlich korreliert und nicht 238 unabhängige Experimente.

Ausgeführte Objekte: Kreuz (`obj_X`), langes Objekt, grüner Würfel, L. Drei Lieferungen,
L nicht geliefert. Die Fehlerepisode ist eingeschlossen; Lieferquote ist kein Erfolgstor
dieses Kameraaudits. Alle vier kommandierten Objekte waren vor Ausführung sichtbar,
mit 369/437/290/597 Pixeln. Auch sämtliche zwölf anderen platzierten Objektvorkommen waren sichtbar.

# Konsequenz für Servo- und Körpermodell

Die gemessenen Gelenkbereiche unterscheiden sich stark von S1:

| Gelenk | Minimum / Maximum in dieser Stichprobe (rad) | Außerhalb S1-Intervall |
|---|---|---:|
| joint_0 | 0,61586 / 2,08221 | 13 / 238 |
| joint_1 | −0,00027 / 2,51061 | 214 / 238 |
| joint_2 | −0,00239 / 0,43221 | 106 / 238 |
| joint_3 | 1,79729 / 3,14179 | 192 / 238 |
| joint_4 | 0,89922 / 1,93281 | 0 / 238 |

Jede Zeile verletzt mindestens eine alte S1-Achsgrenze. Der eingefrorene S1-Prädiktor wurde
hier nicht eingesetzt oder neu bewertet: Aus Extrapolation wird kein negatives Modellurteil.
Der [Positionsport v1](/mechanismen/servo-latent-port.md) begrenzt q auf `[−pi,pi)`; 24
abgetastete Stellungen überschreiten diesen Bereich geringfügig an joint_3. Vor einer
ACT23-Verdrahtung ist deshalb ein explizit erweiterter, weiterhin reversibler Positionsvertrag
nötig. Nicht still modulo abschneiden oder Sensormessung verwerfen. Dafür ist kein inverses
Netztraining zur Rückgewinnung der Winkel erforderlich.

Der Greifer bewegt sich zwischen 0,07703 und 0,56601 rad. B1 hielt ihn fest; ein künftiger
visueller Körperdecoder muss diesen Sensor berücksichtigen. Außerdem verändert ACT23 die
Objektszene unabhängig von q: das vollständige RGB-Bild lässt sich dann nicht allein aus fünf
Armwinkeln deterministisch vorhersagen. Zielrepräsentation beziehungsweise Szenenkontext
müssen in einem neuen Vertrag ausdrücklich behandelt werden.

# Entscheidung

**Bestehende physikalische Roboterkamera beibehalten.** Nächste Datengrundlage aus tatsächlichen
ACT23-Arbeitsbewegungen aufbauen, einschließlich Geschwindigkeiten, direkter Stellbefehle und
zeitlich zugeordneter Folgezustände; vor neuem Training ein eigener Vertrag und nach ganzen
Szenen/Episoden getrennte neue Halteteile. Keine Rückkehr zu beliebigen unabhängigen
Gelenkendstellungen und keine ungeprüfte Wiederverwendung des S1-Checkpoints außerhalb seiner
Messdomäne. Positionsinformation erhalten, Portbereich und Greiferkanal explizit erweitern.

Dieser Audit ist keine allgemeine Kamera-Abdeckungsgarantie: vier Episoden eines historischen
Zustands, FSM, kein A/B und kein Hardwarelauf. Er reicht jedoch aus, um die vorgeschlagene
Kameraverschiebung als nächsten Schritt zurückzunehmen und den Messaufbau an ACT23 auszurichten.

# Artefakte und technische Wiederholungen

Vollständig: `log/act23-workpose-20261004-r3/`: `act23.log`, `result.json`, `observations.json`,
`scenes-evaluation.json`, `camera-observations.npz`, `claw-evaluation.npz`, `episodes.jsonl`,
D0-Manifeste, `additional-checks.json`, `native-camera-phases.png`.
Die Bildtafel zeigt jeweils den ersten Messpunkt sechs benannter Phasen, ohne Bildveränderung.

Zwei vorherige Ausführungen scheiterten beim Export des neuen Beobachters: zuerst ein
Kommando-Callback statt Objektname, danach ein NumPy-Integer in der Rückgabestatistik.
Skript korrigiert; alte Logs erhalten. R2 enthält bereits alle 238 Zahlenbeobachtungen;
diese sind in R3 exakt gleich. Die Wiederholungen sind **keine weiteren unabhängigen Seeds**.
Keine ursprüngliche Messzeile zum Verbessern des Befunds entfernt. Kein Lauf mehr aktiv.
