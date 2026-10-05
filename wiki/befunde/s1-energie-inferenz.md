---
type: Befund
title: Korrekte isolierte PC-Inferenz - S1 bleibt hinter Persistenz
description: Ableitungen und zeitloser Lebenszyklus bestehen; auskonvergierte Testinferenz erreicht 4,35 statt höchstens 0,90 des Persistenzfehlers. Unabhängiger Solver bestätigt den Checkpoint.
tags: [s1, engine, pc-cvnn, audit, propriozeption]
status: stable
evidenz: einzelmessung
ebene: pruefstand
sources:
  - resource: /messungen/s1-energie-inferenz.md
    title: Vorab festgelegtes Rezept und mathematischer Vertrag
  - resource: ../../log/energy-pc-20261003/validation-extended.json
    title: Mathematische und Lebenszyklusprüfungen
  - resource: ../../log/s1-energy-20261003/result.json
    title: Training und S1-Test mit Inferenzdiagnostik
  - resource: ../../log/s1-energy-20261003/manifest.json
    title: Daten-/Code-SHA256, Initialisierung und Normierungsstatistik
  - resource: ../../log/s1-energy-checkpoint-20261003/result.json
    title: Unabhängige Optimierung nach exakter Elimination des freien Ausgabeknotens
  - resource: ../../src/pc_cvnn/act23_s1_energy_checkpoint.py
    title: Reproduzierbare Checkpoint-Gegenprüfung
---

# Urteil

Die isolierte Referenz implementiert die geprüften Energieableitungen korrekt und besteht
die Lebenszyklusprüfung für einen explizit zeitlosen Betrieb. Die alte Produktionsengine
ist damit noch nicht repariert: ihre Dateien und ihre Vektorimplementierung bleiben unverändert.

Der neue S1-Checkpoint verfehlt das Leistungstor auch bei ausreichend genauer Testinferenz.
Ein unabhängiger Solver bestätigt dessen Vorhersagen. **Zu kurze Testinferenz erklärt den
verbleibenden Fehler dieses Checkpoints nicht.** Das ist kein Urteil gegen PC-CVNN oder direkte
Servo-Steuerung insgesamt: Ein Trainingsrezept, ein Initialisierungsseed und ein bereits
benutzter Diagnosesplit wurden geprüft; zudem war nicht jede Trainingsinferenz konvergiert.

# Mathematische und Lebenszyklusprüfung

Die 18 Gradientenkontrollen bestehen (maximal 1,26e-9 relativer Fehler, Tor 1e-6).
Zusätzlich geprüft: Nullpunkt und Sättigung des tanh-Jacobians, zyklischer Graph samt
Selbstverbindung, analytisch lösbare lineare Inferenz und Lernen eines bekannten nichtlinearen
Decoders. Der alte Gegenfall steigt nicht mehr 0,50 → 0,61, sondern fällt **0,50 → 0,41**.

Clamp bleibt erhalten, Reset löscht Zustände und Clamp-Masken ohne W zu ändern; neue Proben
setzen die benötigten Clamps explizit. Fremde vorherige Ziele beeinflussen die nächste Probe
nach Reset nicht. Lernrate null verändert wirklich keine Parameter. Nichtendliche Zustände
führen zu einem Fehler statt stiller Nullsetzung. Keine temporalen Zufallsparameter existieren
in dieser Variante; nicht unterstützte Zeitmodi werden abgewiesen. Lernendes/eingefrorenes V,
Migration alter Pickles und Übertragung in den Produktions-Vektorpfad sind weiterhin offen.

# S1-Zahlen

2.400 Trainings-/600 Testübergänge, 40/10 ganze Rollouts, zwölf Epochen, 24 latente Dimensionen,
Seed 17. Druck, Kontakt, Teacher und IK bleiben ausgeschlossen. Daten-SHA256 unverändert:
`d4086fec6f20b12c447540a006767ca7e846bda357979d49b723eae6ced01ea0`.

| Vorhersage | MSE rad² | Faktor gegenüber Persistenz | Bessere Gelenke |
|---|---:|---:|---:|
| Altes Originalrezept (historisch) | 0,021131210 | 153,59 | 0/5 |
| Neue Energie-Inferenz, 128 Schritte | 0,003381279 | 24,58 | 0/5 |
| Derselbe neue Checkpoint, weitere 2.048 Schritte | 0,000598980 | 4,35 | 2/5 |
| Derselbe Checkpoint, unabhängiger reduzierter Solver | 0,000598980 | 4,35 | 2/5 |
| Persistenz q_next=q | 0,000137581 | 1,00 | — |
| Konstante Trainingsmitte | 0,065823147 | 478,43 | — |

Das Tor <=0,90 und mindestens 4/5 Gelenke wird verfehlt. Auch auf jedem der zehn ganzen
Testrollouts ist das Gesamt-MSE der langen Inferenz größer als Persistenz. Die zweite und
vierte Ausgabekomponente sind einzeln besser; die erste und fünfte dominieren den Restfehler.

Der historische Vergleich ist ausdrücklich **keine isolierte Kausal-Ablation** der
Gradientenkorrektur: Zeitbehandlung, Reset pro Probe, Schrittbudget und Regularisierung
unterscheiden sich ebenfalls. Es gab keine nachträgliche Wahl von Latentgröße, Lernrate oder
Trainingsdauer auf diesem Testsplit. Kein neuer unabhängiger Generalisierungsnachweis.

# Konvergenz: warum der zusätzliche Solver nötig war

Im Training erfüllen 27.163/28.800 Inferenzaufrufe die Toleranz 1e-5 innerhalb 128 Schritten.
In Epoche vier/fünf liegen einzelne Restgradienten deutlich darüber (Maximum 0,793);
in der letzten Epoche 1.647/2.400 bestanden, Maximum 1,03e-4. Das ist ein verbleibender
Trainingsvorbehalt. W wird nach jedem Aufruf einmal aktualisiert, auch bei erreichtem Schrittlimit.

Im Test erreichen 0/600 Proben nach 128 Schritten die Toleranz, Maximum 0,131. Zusätzliche
2.048 Schritte senken das Maximum auf 4,44e-7: damit liegen **alle unter der ursprünglichen
Toleranz 1e-5**, aber keine unter dem strengeren Diagnoseziel 1e-7. Die Änderung einer
Vorhersage durch zusätzliche Inferenz erreicht rund 0,10 rad. 128 Schritte sind hier klar zu kurz.

Die anschließende, als solche gekennzeichnete **nachträgliche Solver-Gegenprüfung** verändert
keine Gewichte und kein Lernrezept: Für einen freien Ausgabeknoten ohne Nachfolger gilt am
Minimum exakt `y = W_y.T @ f(z)`. Nach Einsetzen bleibt

`E(z) = 0.5 ||z||² + 0.5 ||x - W_x.T @ f(z)||²`.

L-BFGS-B (lokal installiertes SciPy 1.17.1) optimiert diese gleiche Energie ab z=0;
keine Testziele gehen in die Optimierung ein. Die reduzierte Ableitung stimmt mit zentralen
Differenzen auf 1,81e-10 überein. Alle 600 Proben erreichen 1e-5, 576 erreichen 1e-7,
maximaler Restgradient 2,68e-7. Der Optimierer meldet in allen Fällen Erfolg; wegen möglicher
Funktionswert-Abbruchkriterien wird zusätzlich der tatsächliche Gradient geprüft.

Maximale Vorhersageabweichung zur langen ursprünglichen Inferenz: **2,01e-8 rad**.
Beide erreichen dasselbe MSE bis weit unter die berichtete Genauigkeit. Das belegt eine
stabile Bewertung des Checkpoints, keinen globalen Optimalitätsbeweis für nichtlineare Energie.
Der NPZ-Checkpoint ist vor/nachher bytegleich (SHA256
`36c3c3e95f427faba92a619aeda78aeac322d86983686aabbe118a58e6734c98`).

# Claudes Normalisierungsfund und Ressourcen

Commit 59c85c4 (act19-Policy) und der dortige Befund wurden gelesen. S1 hat keine konstante
Eingabespalte: Trainings-Standardabweichungen 0,1375–0,6370 in den jeweiligen Einheiten;
alle 15 Spalten bleiben aktiv. Der neue Schutz gegen konstante Spalten verändert diesen
Datensatz daher nicht. Die 0,5-mm-Schwelle der Policy wurde nicht auf Winkel/Geschwindigkeiten
übertragen. Eine allgemeine Behandlung von späterem Nachtraining ist damit nicht bewiesen.

Vor Start 4,18 GiB RAM frei bei zwei aktiven fremden Python-Läufen. Eigener Hauptprozess mit
einem BLAS-Thread, zuletzt gemessener Spitzenverbrauch 81,4 MiB, weiterhin rund 4 GiB frei.
Hauptlauf einschließlich langer Testinferenz: 751,6 s. Kein Simulator und keine PKL benutzt.
Eigenes W-Checkpoint-NPZ unter `log/s1-energy-20261003/weights.npz`; Logs bleiben lokal.

# Entscheidung

Fortsetzung: Der [Lernziel-/Nullprior-Audit](/befunde/s1-lernziel-audit.md) ist abgeschlossen.
Konvergiertes Training allein behebt den Fehler kaum; ein bedingter Batch-Kopf auf denselben
Kontextmerkmalen erschließt dagegen das Vorhersagesignal. Die folgenden Entscheidungen
beschreiben den Stand vor diesem zusätzlichen Vergleich.

* Die isolierte mathematische Referenz wird behalten, aber nicht automatisch in ACT23 eingebaut.
* S1 erhält keine Motorpolicy-Freigabe: das festgelegte Leistungstor ist verfehlt.
* Kein weiteres blindes Verlängern der Testinferenz: der unabhängige Solver bestätigt deren Ergebnis.
* Nächste sachliche Untersuchung wäre ein kleiner kontrollierter Lernvergleich mit analytisch
  lösbarer linearer Referenz, vollständig konvergiertem Training und expliziter Trennung von
  Rekonstruktionsziel/Nullprior und Vorhersageziel. Erst damit die verbleibende Ursache eingrenzen;
  nicht aus diesem Einzelergebnis die gesamte Architektur verwerfen. Noch nicht gestartet.
