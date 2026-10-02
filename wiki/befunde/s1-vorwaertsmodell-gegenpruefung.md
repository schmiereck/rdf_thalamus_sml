---
type: Befund
title: S1-Gegenprüfung - Inferenzasymmetrie und komplexe Rückgabe begrenzen das Architektururteil
description: Alter Fehler reproduziert; commit_step im Test senkt ihn deutlich. Numerischer Gradiententest findet fehlende Konjugation in der linearen Fehlerrückgabe.
tags: [s1, pc-cvnn, audit, propriozeption]
status: stable
evidenz: einzelmessung
ebene: pruefstand
sources:
  - resource: ../../src/pc_cvnn/act23_s1_forward_crosscheck.py
    title: Reproduzierbare Gegenprüfung
  - resource: ../../log/s1-forward-crosscheck-20261002/result.json
    title: Messergebnis vom 2026-10-02
  - resource: /befunde/s1-pc-vorwaertsmodell.md
    title: Ursprünglicher Befund und korrigierte Ursachenbewertung
---

# Aufbau

Fortsetzung: Der [isolierte Engine-Audit](/befunde/pc-engine-mathematik-audit.md) bestätigt
die Konjugationsabweichung und ergänzt fehlenden Aktivierungs-Jacobian sowie Mittelungsfaktoren.
Die globale Engine ist weiterhin unverändert; die Reparaturfolge ist dort dokumentiert.

Unverändertes S1-Rezept: Seed 17, 24 latente Dimensionen, zwölf Epochen, 40/10 ganze
Trainings-/Testrollouts. Vier Diagnosen verwenden Kopien desselben trainierten Modells.
Datensatz-SHA256: d4086fec6f20b12c447540a006767ca7e846bda357979d49b723eae6ced01ea0.
Keine Aktuatorbefehle, keine PKL und keine gemeinsame Engine-Datei geändert.

# Zahlen

| Inferenz nach identischem Training | Test-MSE rad² |
|---|---:|
| Original: ohne commit_step, mu lesen | 0,02113120953 |
| Ohne commit_step, pi lesen | 0,00809727315 |
| Mit commit_step, mu lesen | 0,00155737114 |
| Mit commit_step, pi lesen | 0,01594597095 |
| Persistenz q_next=q | 0,00013758111 |

Die Originalrechnung reproduziert den alten Wert. Alle vier Varianten bleiben schlechter als
Persistenz. Die Varianten sind Fehlerdiagnosen, keine erneute Auswahl auf einem unabhängigen
Testsatz; keine davon erhält eine Integrationsfreigabe.

# Technische Befunde

* Daten: 40/10 getrennte Rollouts, Schrittfolge 0–59 und Anschluss q_next/q sowie qvel_next/qvel
  sind geprüft. Normalisierung stammt nur aus Training; die Vorhersage erhält keine Testziele.
* Reset und Test verändern weder W noch V (SHA-Vergleich). Reset löscht flüchtige Zustände.
* Training ruft commit_step auf, Test nicht. load_predicted_state lädt dadurch im ursprünglichen
  Test nach jedem Rollout-Reset erneut Null als latenten Startzustand. Zweimalige Vorhersage
  desselben Eingangs liefert exakt dasselbe Ergebnis: unbeabsichtigt kein zeitlicher Fortschritt.
* eta_temporal=0 schaltet das Lernen von V ab, nicht dessen Nutzung beim Warmstart. Ein einfaches
  Nachtragen von commit_step ist deshalb noch keine vollständig definierte Reparatur: das dann
  freie Ausgabesensor-V ist untrainiert und dessen Initialisierung im SensorNode nicht über den
  Modellseed kontrolliert. Der gemessene Gewinn ist ein Diagnoselauf, keine stabile neue Vorgabe.
* mu und pi sind bei endlicher Relaxation verschiedene Größen. Ihr Austausch allein stellt die
  Leistungsfähigkeit nicht wieder her; eine Konvergenzprüfung fehlt im ursprünglichen Audit.

# Komplexer Gradient

Für die lineare Vorhersage p=W.T @ z und E=0,5*sum(abs(t-p)**2) muss die negative
Gradientenrichtung bezüglich z `conj(W) @ (t-p)` sein. connection.py verwendet in
propagate_error dagegen `W @ epsilon`. Die zentrale Differenz nach Real- und Imaginärteil
ergibt relativen Fehler 0,157845 für die bestehende Formel, aber 1,52e-9 für die konjugierte
Formel. Dies prüft den linearen Verbindungsanteil; für tanh ist zusätzlich die passende
Aktivierungsableitung zu auditieren. Eine vollständige Engine-Reparatur ist damit noch nicht
validiert. Der Name pressure bezeichnet hier interne Fehlerweitergabe, keinen Drucksensor.

# Synthetische Kontrolle

Eine unabhängige normalverteilte Eingabe mit bekanntem Ziel y=x[:5] ergibt bei derselben
Architektur und zwölf Epochen MSE 0,400542 gegen 1,041940 für die Nullvorhersage. Lernen findet
statt, die einfache Identität wird aber nur grob rekonstruiert. Das lokalisiert die Schwäche
bereits außerhalb der Roboterdaten; es isoliert ihre Ursache nicht auf einen einzelnen Defekt.

# Entscheidung

Die gemessene Niederlage des ursprünglichen Rezeptes bleibt gültig. Die Behauptung, seine
Architektur sei damit als Ursache identifiziert oder allgemein ungeeignet, wird zurückgenommen.
Nächster Schritt: isolierter mathematischer Engine-Vertrag mit linearen und nichtlinearen
Gradiententests, definierter zeitlicher Semantik und synthetischen Lernkontrollen. Erst danach
eine reparierte S1-Serie mit neuer vorab fixierter Evaluation. Bestehende Testrollouts sind
inzwischen Diagnosedaten. Die gemeinsame Engine wird vor Abstimmung mit Claude nicht geändert.
