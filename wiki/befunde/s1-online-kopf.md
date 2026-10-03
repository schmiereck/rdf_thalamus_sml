---
type: Befund
title: S1 - lokaler bedingter Online-Kopf besteht das Diagnosetor
description: Zwölf Epochen lokaler komplexer Updates schlagen Persistenz auf 5/5 Gelenken; Batch-Referenz bleibt genauer, unabhängige Rollouts fehlen noch.
tags: [s1, online, pc-cvnn, lernziel]
status: stable
evidenz: einzelmessung
ebene: pruefstand
sources:
  - resource: /messungen/s1-online-kopf.md
    title: Vorab festgelegter Trainingsvertrag
  - resource: ../../src/pc_cvnn/act23_s1_online_readout.py
    title: Lokale Lernregel, Kontrollen und Auswertung
  - resource: ../../log/s1-online-readout-20261003/result.json
    title: Lernkurve und Testmetriken
  - resource: ../../log/s1-online-readout-20261003/manifest.json
    title: Initialisierung, Encoder-/Daten-SHA und Rezept
  - resource: ../../log/s1-online-readout-20261003/controls.json
    title: Numerischer Gradient und bekannte komplexe Abbildung
---

# Ergebnis

Der bedingte Ausgabekopf lernt auch mit einer lokalen komplexen Delta-Regel aus zufälligen
Startgewichten. Ein Batch-Löser ist für den Gewinn gegenüber Persistenz hier nicht notwendig.
Das vorher festgelegte Diagnosetor (höchstens 0,90 des Persistenzfehlers und mindestens 4/5
Gelenke besser) wird erfüllt. **Noch kein unabhängiger Generalisierungsnachweis und keine
autonome Motorpolicy:** Derselbe bekannte Diagnosesplit wird verwendet.

„Online“ bedeutet in diesem Versuch einen lokalen Parameterupdate nach jeder Zeile beim
Offline-Replay selbst gesammelter Übergänge. Es gab keinen gleichzeitig lernenden Roboterlauf.
Der Encoder bleibt aus dem vorherigen Lernziel-Audit übernommen und eingefroren; nur der
bedingte Kopf lernt neu. Die Merkmale werden ausschließlich aus x inferiert, nie aus Testzielen.

# Messwerte

40/10 ganze Trainings-/Testrollouts, 2.400/600 Zeilen; Seed 17, zwölf Epochen, eta 0,004.
Kein Bias, Decay, Clipping, Shuffle, Batch-Warmstart oder Parameter-Tuning.

| Kopf/Referenz | Test-MSE rad² | Faktor gegenüber Persistenz | Bessere Gelenke |
|---|---:|---:|---:|
| Zufälliger untrainierter Kopf | 4,49740e-2 | 326,891 | 0/5 |
| Generativer Kopf aus vorherigem Audit | 5,99232e-4 | 4,35548 | 2/5 |
| **Bedingter lokaler Online-Kopf** | **1,20244e-5** | **0,087399** | **5/5** |
| Bedingte Batch-Referenz | 9,49378e-8 | 0,00069005 | 5/5 |
| Persistenz q_next=q | 1,37581e-4 | 1 | — |

Der Online-Kopf senkt das Test-MSE gegenüber Persistenz um rund 91,26 Prozent. Er ist auch
auf jedem der zehn ganzen Testrollouts besser; MSE je Rollout zwischen 9,83e-6 und 1,35e-5.
Die Batch-Referenz hat noch einen rund 126,66-mal kleineren MSE als der Online-Kopf.
Das ist ein Optimierungsabstand nach dem festen Budget, keine Aufforderung, den bekannten
Testsatz durch nachträgliche Epochen-/Lernratensuche auszunutzen.

Train-MSE fällt von 0,049257 vor Training über 0,012011 nach Epoche eins und 7,66509e-5
nach Epoche fünf auf 1,17195e-5 nach Epoche zwölf. Alle zwölf Trainingsmetriken fallen;
Test-MSE wurde erst nach dem vollständigen festgelegten Training ausgewertet.

# Technische Kontrollen

Die tatsächliche Update-Regel `W += eta * outer(conj(f), y-W.T f)` trifft den numerischen
negativen Gradienten mit relativem Fehler 1,02e-10. Eine bekannte komplexe lineare Abbildung
wird mit Gewichts-MSE 1,22e-33 gelernt. Vorhersage und Lernrate null verändern keine Gewichte;
der Aufrufer behält seine ursprüngliche Initialisierung unverändert.

Die Normalisierung stimmt exakt mit den ausschließlich aus Training berechneten Werten
überein. Ganze Rollouts sind disjunkt. Die kontextbasierte Inferenz unterschreitet überall
die Toleranz 1e-5. Der neu berechnete Batch-Kopf und seine Testvorhersagen stimmen bitgleich
mit dem vorherigen Audit überein: Es sind tatsächlich dieselben Merkmale und Referenzen.
Encoderdatei und Encodergewichte bleiben unverändert, Testauswertung verändert den Online-Kopf
nicht. Die Zielvergiftungs-/Replay-Kontrollen des [Lernziel-Audits](/befunde/s1-lernziel-audit.md)
gelten für den hier wiederverwendeten Merkmalsweg; dessen Daten oder Normalisierung wurden
nicht geändert.

Eigener Checkpoint: `log/s1-online-readout-20261003/model.npz` mit eingefrorenem Encoder,
trainiertem Kopf, Initialisierung, Batch-Referenz und Normalisierung. Rohquelle und
Encoder-Checkpoint nur gelesen. Keine PKL, Produktionsengine oder Simulation geändert.
Laufdauer rund 11,9 Sekunden einschließlich Merkmalsinferenz; ein BLAS-Thread, vorab
4,44 GiB freier RAM. Alle eigenen Prozesse beendet.

# Entscheidung

Der bedingte lokale Lernweg ist für diesen Prüfstand tragfähig und benötigt keinen
Batch-Warmstart. Die vorherige Frage „ist der Erfolg allein dem Batch-Löser zuzuschreiben?“
ist damit für das Persistenztor verneint, nicht für das Erreichen der Batch-Genauigkeit.

Als Nächstes den jetzt festgelegten Encoder/Kopf samt Normalisierung einfrieren und auf
**neuen ganzen Servo-Rollouts mit vorher unbenutztem Sammelseed** prüfen: zuerst ohne
Nachtraining, weiterhin ohne Druck-/Kontakt-/Teacher-/IK-Eingaben, mit unverändertem Tor.
Das trennt Bestätigung von weiterem Lernen. Erst danach einen eigenen Online-Anpassungstest
oder geschlossenen Regelkreis planen. Dieser neue Datensatz ist noch nicht gesammelt.
