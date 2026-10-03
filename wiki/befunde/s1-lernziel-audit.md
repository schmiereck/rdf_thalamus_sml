---
type: Befund
title: S1 - bedingter Ausgabekopf erschließt vorhandenes Vorhersagesignal
description: Konvergiertes generatives Training bleibt bei 4,36-fachem Persistenzfehler; ein auf kontextinferierten Merkmalen gefitteter Kopf schlägt Persistenz auf 5/5 Gelenken. Nullprior entfernen allein degeneriert.
tags: [s1, pc-cvnn, lernziel, audit]
status: stable
evidenz: einzelmessung
ebene: pruefstand
sources:
  - resource: /messungen/s1-lernziel-audit.md
    title: Vorab festgelegter Diagnosevergleich
  - resource: ../../src/pc_cvnn/act23_s1_objective_audit.py
    title: Reproduzierbarer Vergleich mit Konvergenztor
  - resource: ../../src/pc_cvnn/test_s1_objective_audit.py
    title: Zielvergiftung, Replay und vertauschte Trainingsziele
  - resource: ../../log/s1-objective-20261003/result.json
    title: Metriken, Lernverläufe und Inferenzdiagnostik
  - resource: ../../log/s1-objective-20261003/manifest.json
    title: Datensatz, Normalisierung, Initialisierung und Skript-SHA
  - resource: ../../log/s1-objective-20261003/leakage-controls.json
    title: Bestandene nachträgliche Datenflusskontrollen
---

# Ergebnis

Der verbliebene S1-Fehler lässt sich durch konvergiertes Training allein nicht beheben.
Die gleiche eingefrorene, nur aus Kontext inferierte Repräsentation enthält aber ein sehr
gutes Vorhersagesignal: Ein anders trainierter Ausgabekopf mit gleicher Parametrisierung
erschließt es. **Der bisherige generative Lernweg ist damit kein belastbarer Test dafür,
ob das Netz aus diesen Übergängen vorhersagen lernen kann.**

Dies ist ein Offlinebefund auf dem bereits bekannten S1-Diagnosesplit. Der erfolgreiche Kopf
wurde per komplexem Least Squares im Batch gefittet, nicht durch die bisherige lokale
PC-Online-Lernregel. Noch kein neuer Rollout, keine autonome Motorpolicy, keine Integration.

# Festgelegter Vergleich und Zahlen

Alle Varianten: 24 komplexe latente Dimensionen, gleiche initiale W (Seed 17), zwölf Epochen,
Lernrate 0,004, 2.400 eigene Trainingsübergänge aus 40 ganzen Rollouts. 600 Testübergänge aus
zehn anderen Rollouts; kein Druck, Kontakt, IK oder Teacher. Zeitmodell aus, keine
Clipping-/Decay-Heuristik. Jede Inferenz muss vor Lernen/Auswertung Gradient <1e-5 erreichen.

| Variante | Test-MSE rad² | Faktor Persistenz | Bessere Gelenke |
|---|---:|---:|---:|
| tanh, Prior 1, konvergiertes generatives Training | 5,99232e-4 | 4,35548 | 2/5 |
| Gleicher tanh-Encoder, bedingter Kopf | **9,49378e-8** | **0,00069005** | **5/5** |
| Linear, Prior 1, generatives Training | 6,59153e-4 | 4,79102 | 1/5 |
| Gleicher linearer Encoder, bedingter Kopf | 7,82530e-9 | 0,00005688 | 5/5 |
| Linear, Prior 0, generatives Training | 9,29305e-2 | 675,459 | 0/5 |
| Gleicher priorfreier Encoder, bedingter Kopf | 7,82530e-9 | 0,00005688 | 5/5 |
| Direkte lineare Regression x→y | 7,82530e-9 | 0,00005688 | 5/5 |
| Persistenz q_next=q | 1,37581e-4 | 1 | — |

Das diagnostische Tor <=0,90 und mindestens 4/5 Gelenke bestehen die bedingten Köpfe und
die direkte lineare Referenz. Der tanh-Kopf ist auch auf jedem einzelnen Testrollout besser
als Persistenz. Es wurde kein Gewinner nachträglich weitergetunt. Train-MSE des tanh-Kopfs
8,07994e-8, direkte lineare Referenz 1,06892e-8; Test liegt in derselben Größenordnung.

# Was die Kontrollen trennen

## Konvergenz ist nicht der verbleibende Hauptfehler

Alle 28.800 Trainingsaufrufe je Variante (2.400 Zeilen mal zwölf Epochen) erreichen das Tor.
Beim tanh-Training maximaler Gradient 2,94e-7; Kontextinferenz für Training/Test maximal
3,79e-7. Lineare Varianten werden analytisch gelöst, Restgradienten etwa 1e-14.
Vorheriger tanh-Checkpoint mit teilweise unkonvergiertem Training: MSE 5,98980e-4;
jetzt 5,99232e-4. Der Restfehler bleibt praktisch gleich. Wegen möglicher unterschiedlicher
lokaler Lösungen ist dies keine universelle Aussage über jeden nichtlinearen Solver.

## Rekonstruktion mit bekanntem Ziel ist nicht gleich Vorhersage ohne Ziel

Im generativen Training wird z aus **x und y** inferiert. W_y lernt, dieses z(x,y) zu
dekodieren. Bei der Vorhersage ist y unbekannt; verfügbar ist nur z(x). Das Lernziel garantiert
nicht, dass der Decoder auf diesen anderen Zuständen präzise y vorhersagt.

Für die Gegenkontrolle bleibt W_x vollständig eingefroren. Für alle Zeilen werden Merkmale
f(z(x)) ohne Zielzugriff erzeugt. Nur W_y wird aus Trainingsmerkmalen und Trainingszielen neu
gefittet: gleiche komplexe lineare Kopfparametrisierung, kein zusätzlicher Bias, keine neue
Netzkapazität. Dies hebt den tanh-Kopf auf 9,49e-8 rad².

Belegt ist damit: Die Kontextrepräsentation enthält genügend Information, und ein geeigneter
Kopf kann sie nutzen. **Nicht isoliert** ist, welcher Anteil auf geänderte latente Trainingszustände,
bedingtes Vorhersageziel oder den globalen Least-Squares-Löser statt lokaler Onlineupdates
entfällt. Eine Behauptung „allein Zielzugriff war die Ursache“ wäre zu stark.

Die beiden linearen kontextbasierten Repräsentationen haben Rang 15; ein frei gefitteter
linearer Kopf kann daher die direkte lineare Abbildung der 15 Eingaben wiedergeben. Die
gleichen drei linearen Zahlen sind keine drei unabhängigen Bestätigungen und kein Vorteil
komplexer Architektur. Auf diesem kurzen, freien Simulator-Übergang ist die direkte lineare
Referenz sogar genauer als der tanh-Kopf. Aussagen über Kontakt, längere Horizonte oder
einen physischen Roboter folgen daraus nicht.

## Nullprior einfach entfernen ist keine Lösung

Ohne Prior und mit Identitätsaktivierung kann ein voller Rang 20 im Decoder aus 24 latenten
Dimensionen jede beobachtete 20er-Trainingszeile exakt rekonstruieren. Der explizit gewählte
Zustand kleinster Norm löst W.T z=[x,y]; der Fehler und damit die W-Lernrichtung verschwinden.

Gemessen: mittlere quadrierte Rekonstruktionsabweichung in Epoche zwölf **9,45e-29**,
gesamte W-Änderungsnorm nach zwölf Epochen nur **2,42e-12** (Anfangsnorm rund 4,98).
Trotz fast perfekter Rekonstruktion liegt der Vorhersagefehler bei 0,09293 rad².
Das ist eine konkrete Degeneration dieses übervollständigen linearen Modells, keine allgemeine
Aussage gegen priorfreie Modelle. Priorstärke null wird nicht als Reparatur übernommen.

# Prüfung des großen Gewinns

Zusätzlich nach dem Lauf, ohne Auswahl neuer Modellparameter:

* Collector-Code gelesen: q und qvel werden als eigene Arrays **vor** sim.step kopiert;
  ctrl_next wird vorher zufällig gewählt. q_next/qvel_next werden erst danach erfasst.
* Schrittfolgen und Anschlusszustände aller Rollouts geprüft; Trainings-/Testrollouts disjunkt.
* Testziele durch -999 und künftige Geschwindigkeiten durch +999 ersetzt: Eingaben bleiben
  exakt gleich, Training bleibt gleich, gefitteter Kopf bleibt exakt gleich.
* Training-only-Normalisierung gegen Manifest geprüft. Replay des bedingten tanh-Kopfs aus
  gespeicherten W und neu berechneten Merkmalen reproduziert die Vorhersagen **bitgleich**.
* Vertauschte Trainingsziele (fester Seed 918) verschlechtern Test-MSE auf **0,0638957**.
  Der Gewinn hängt also von der gelernten Zuordnung ab.
* W-/Kopf-/Vorhersagedateien bleiben bei den Kontrollen bytegleich.

Die Prüfungen schließen die untersuchten Datenflussfehler aus, machen aus dem wiederverwendeten
Testsatz aber keinen neuen Generalisierungsnachweis. Keine Signifikanzbehauptung oder
rechnerübergreifende/physische Übertragungsbehauptung aus diesen einzelnen Messungen.

# Entscheidung und nächster Schritt

Der Forschungszweig direkte Servo-Vorhersage bleibt offen, jetzt mit konkretem Lernsignalnachweis.
Nächster kontrollierter Schritt: Den bedingten Kopf auf denselben f(z(x))-Trainingsmerkmalen
mit einer lokalen Online-Lernregel trainieren, mit der Batch-Lösung als Referenz. Dadurch
trennen wir Lernziel und Optimierungsverfahren und prüfen den Weg zum laufenden Selbstlernen.
Ein neuer unabhängiger Satz ganzer Servo-Rollouts muss eine spätere Freigabe tragen.
Beides noch nicht gestartet; keine Motorpolicy auf Basis dieses Diagnosesplits freigegeben.

Hauptlauf 136,8 Sekunden, ein BLAS-Thread; vorab 4,06 GiB RAM frei. Keine Produktionsdatei,
PKL oder Simulation verändert. Eigene Artefakte unter `log/s1-objective-20261003/`.
