---
type: Messvorschrift
title: D0-Pilot - Lernspielraum bei der Wiedererkennung einer neuen Form
description: Vorab festgelegter, kopfloser Komponentenvergleich von selbstbeobachtendem und eingefrorenem ShapeClassifier auf getrennten Y-Sichtungen und bekannten Kontrollformen.
tags: [act23, dream-rsi, d0, pilot, wiedererkennung]
status: draft
evidenz: vermutung
ebene: code
generated: { by: codex, at: 2026-09-17T18:00:00Z }
sources:
  - id: plan
    resource: /fragen/dream-rsi-forschungsplan.md
    title: D0 - Basis und messbare Lernaufgabe
  - id: vorbefund
    resource: /befunde/aneignung-neuer-formen.md
    title: Die Y-Form wurde in frueheren ACT23-Laeufen selbst angeeignet
---

# Zweck und Grenze

Erste D0-Vorpruefung: Bringen eigene Sichtungen einer neuen Form **gehaltene Wiedererkennung**
gegenueber dem eingefrorenen Zustand, ohne bekannte Formen zu uebernehmen? Eine Klassengeburt
allein besteht die Pruefung nicht. Dies ist ein kopfloser Wahrnehmungs-Pruefstand mit dem
vorhandenen ACT23-Baustein, kein voller Arm-Lernlauf und kein Dream-RSI-Nachweis. Der
Open-Set-Pfad erweitert Exemplargedaechtnis und Klassen; er trainiert dabei nicht automatisch
neuronale Gewichte. Diese Grenze ist Teil der Messung.

Der komplette eingefroren/lernend-Vergleich des Arms folgt erst nach einem echten Freeze-
und Evaluationsvertrag. `EXV_FREEZE` ist kein globales Lern-Aus: es ist an `EXV_N > 1`
gebunden und verhindert nicht alle BodyModel-/Fovea-/Open-Set-Updates. Ihn hier als vollstaendig
eingefrorenen Kontrollarm zu verwenden waere eine falsche Beschriftung.

# Vorab festgelegte Basis

* Code: `b351207` (Integration von main `15c063e`, ohne Veraenderung von dessen Laufzeitcode).
* XML-SHA256: `4588D3E73A4F7DDBA995186E5B517FB549D41295A807000620458E31AEFCBF42`.
* Ausgang: Kopie von `act23_state.pkl`, SHA256
  `AD9D768C1F770C71E92954A303E1F905B3D1A96D0206CA04F6BB172E32C09B9E`.
  Schema 2, 4 DOF, 2500 Basis-Formbeispiele; obj_T/obj_X gebunden, obj_Y nicht gebunden.
* Eigene Kopie: `src/pc_cvnn/state/dream_rsi_d0_20260917/base.pkl`; keine Rueckschreibung.
* Python 3.12.10 aus der vorhandenen Projekt-venv im Haupt-Worktree; Importe aus Codex-`src`.
  NumPy 2.4.6, SciPy 1.17.1, MuJoCo 3.9.0. Ein Worker, BLAS/OpenMP je ein Thread.
* Unveraenderte Welt, einschliesslich geparktem Sockel; obj_Y in der XML-Originalform.
  Renderbild 240 x 240, overview. Keine Fovea-, Servo- oder Stapel-Erweiterung.

# Aufgabe, Daten und Arme

Der Kopf sieht stets eine isolierte Form auf dem Tisch. Die Lernroutine erhaelt nur das Bild
ueber `observe_scene`, keine Koerper-ID oder Sollklasse. Die Simulation stellt Szenen her;
Koerper-ID und Pose werden ausschliesslich im externen Messkanal genutzt.

* Pilot-Seeds **1701 und 1702**, Technik-Rauchtest separat Seed 1700.
* Je Pilot-Seed maximal **24 eigene Y-Sichtungen**, nach jeder dritten eine bekannte Form
  zur Bestandspflege. Checkpoints nach 0, 3, 6, 12 und 24 Y-Sichtungen.
* Training: x in [-0,05; 0,05], y in [0,14; 0,19], beliebiger Yaw, Farben aus drei festen
  gesaettigten RGB-Werten. Jede Sichtung hat eine neue Pose, keine Nachbarframes.
* Evaluation: eigener RNG-Strom, x in [-0,09; 0,09], y in [0,12; 0,21], beliebiger Yaw,
  drei andere Farben; 24 Y-Sichten plus vier je bekanntem Koerper (7 x 4 = 28).
  Training und Evaluation sind getrennte Szenen; Farbkombinationen sind zurueckgehalten.
* Zwei Arme aus bytegleicher Kopie: `frozen` ohne `observe_scene`, `learning` mit identischer
  Szenenfolge und eingeschaltetem `observe_scene`. Bewertung jeweils auf Wegwerfkopien.
* Die **erste im Y-Training geborene neue Klasse** ist der feste Anker fuer Y. Stirbt oder
  verschmilzt sie, wird sie nicht anhand der Testdaten umbenannt. Vor ihrer Geburt gilt
  die Wiedererkennung als null. Der eingefrorene Arm erhaelt keine neue Klasse.

# Metriken und Pilot-Tor

Primaer: gehaltene Y-Wiedererkennung in der festen Ankerklasse, mit Lokalisierung innerhalb
20 mm; Nenner alle 24 Y-Szenen, auch fehlende Detektionen. Dazu: Fehlansprueche der Ankerklasse
auf bekannte Formen, uebrige Klassengeburten, initialer Neuheitsanteil, bekannte Klassifikation,
Positionsfehler, Laufzeit und Veraenderung von Gewichten vs. Exemplargedaechtnis.

Als vorab festgelegter **Pilot-Hinweis auf zugaengliches Signal** gelten in beiden Seeds:
mindestens 50 % Y-Wiedererkennung am Ende, mindestens +20 Prozentpunkte gegen eingefroren,
hoechstens ein falscher Y-Anspruch unter 28 bekannten Szenen und hoechstens eine zusaetzlich
falsch klassifizierte bekannte Szene gegen die eigene Ausgangslage. Wenn die Ausgangslage Y
bereits breit erkennt oder nach 3 Sichtungen praktisch gesaettigt ist, wird ein Deckeneffekt
festgehalten: dann traegt diese Aufgabe keine laengere Scheduler-Studie.

Diese Zahlen sind ein Screening-Tor, keine Powerrechnung. Zwei Seeds erlauben keine starke
Generalisierungsaussage. Quotentabellen und Fisher-Test sind deskriptiv; Szenen desselben
Lernlaufs sind keine unabhaengigen Replikate. Endpunktvergleich nicht nachtraeglich auf einen
guenstigeren Zwischencheckpoint verschieben. Negative Ergebnisse bleiben erhalten.

# Integritaet und Reproduktion

Der eingefrorene Zustand und beide Trainingszustaende muessen vor/nach jeder Evaluation
unveraenderte Hashes haben. Gewichts-Hash separat vom Gesamtzustand melden. Fehlende oder
ungueltige Daten als Fehler behandeln, nicht aus der Erfolgsquote entfernen. Original- und
Kopie-Hash vor und nach dem Versuch vergleichen.

Das Werkzeug `src/pc_cvnn/act23_dream_rsi_d0.py` wird als wiederverwendbares Messwerkzeug
erstellt. Es legt Szenen, Versionen, Quellhashes, Einzelurteile und Zusammenfassung in einem
neuen Ergebnisverzeichnis ab; existierende Ergebnisse werden nicht ueberschrieben. Der
genaue Aufruf und Ergebnisverweise werden nach dem Techniktest ergaenzt. Dieser Vertrag
wurde vor dem ersten Render-/Lernlauf geschrieben.

# Aufbau

Aus dem Codex-Worktree, PowerShell (vorhandene Projekt-venv, kein System-Python):

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
& '../rdf_thalamus_sml/.venv/Scripts/python.exe' src/pc_cvnn/act23_dream_rsi_d0.py `
  --state src/pc_cvnn/state/dream_rsi_d0_20260917/base.pkl `
  --out log/dream_rsi_d0_20260917/pilot_01
```

Technik-Rauchtest mit `--smoke` und separatem Ausgabeordner `smoke_01` bestanden:
alle 13 Evaluationsszenen je Abfrage detektiert, sieben bekannte korrekt, eingefrorener
Zustand und Eingabedatei unveraendert. Nach drei Y-Sichten noch keine neue Klasse; der
Rauchtest ist keine Wirkungsmessung und hat die Pilotkriterien nicht veraendert.
Belege: `log/dream_rsi_d0_20260917/smoke_01/{manifest,summary}.json` und
`observations.jsonl`. Die Lernstrecke betrifft das Exemplargedaechtnis, Gewichte unveraendert.

# Vorab ergaenzte Gegenprobe v2: frischer Grundform-Lerner

Nach dem [negativen v1-Pilot](/befunde/dream-rsi-d0-lernaufgabe.md), vor dem zweiten Lauf:
je Seed einen neuen `ShapeClassifierModule` mit 2500 gerenderten Beispielen von cube/L/U
trainieren (`bootstrap_rng = seed + 200000`). Das vorhandene `train` verwendet dafuer
Simulator-Sollklassen: **ueberwachter Bootstrap**, kein behauptetes Selbstlernen. Y/T/X
bleiben in diesem Bootstrap geparkt. Alte Klassen werden nicht aus dem Live-Zustand geloescht.

Danach derselbe eingefroren/lernend-Vergleich wie v1, gleiche Seeds, Posen, Farben, Budgets
und Kriterien. Bekannte Bestandspflege verwendet nur die fuenf Grundform-Koerper. T/X sind
zusaetzliche unbekannte Gegenformen: sie sollen nicht die neue Y-Identitaet uebernehmen.
Die 28 Kontrollsichten enthalten damit 20 bekannte plus 8 unbekannte Formen; beim
Feld `known_correct` werden fuer T/X korrekte Enthaltungen gezaehlt. Alle Kontrollarten
werden in den Einzelurteilen getrennt gespeichert. Ein gemeinsamer Klassenanspruch
wird nicht als individuelle Wiedererkennung verkauft.

Aufruf wie oben, zusaetzlich `--fresh-shape`, neuer Ordner `pilot_fresh_01`. Einmalige
Gegenprobe, keine iterative Suche nach passenden Seeds. Scheitert sie ebenfalls oder ist
die Aufgabe schon nach drei Sichten ausgeschoepft, bleibt das D0-Tor offen; vor einer
Scheduler-Implementierung muss eine andere messbare Lernaufgabe begruendet werden.
