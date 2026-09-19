---
type: Befund
title: D0-Preflight - Lernzustand eingefroren, Episodenzustand sichtbar
description: Die Pkl blieb bitgleich. Ein 40-Episoden-Audit fand dennoch eine Fovea-Mutation; nach zentraler Fovea-Freeze-Grenze besteht der erneute FSM-L-Form-Preflight mit unveraendertem Lernzustand.
tags: [act23, dream-rsi, d0, preflight, zustand, mutation]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: codex, at: 2026-09-18T11:26:32Z }
sources:
  - id: result
    resource: ../../log/d0-preflight/fsm-l-1ep/result.json
    title: Maschinenlesbares Preflight-Ergebnis
  - id: log
    resource: ../../log/d0-preflight/fsm-l-1ep/act23.log
    title: Vollstaendiges ACT23-Protokoll
  - id: audit
    resource: /befunde/dream-rsi-d0-wrist-audit.md
    title: Vorheriger Kredit- und Zustandsaudit
  - id: l-result
    resource: ../../log/d0-preflight/fsm-l-form-1ep/result.json
    title: Korrigierter L-Form-Preflight
  - id: freeze-result
    resource: ../../log/d0-preflight/fsm-l-freeze-learning-1ep/result.json
    title: Bestandener gefrorener L-Form-Preflight
  - id: fovea-regression
    resource: ../../log/d0-evaluation/seed17/base-seed101-fovea-diagnostic/result.json
    title: 40-Episoden-Diagnose der Fovea-Mutation
  - id: fovea-fixed
    resource: ../../log/d0-evaluation/seed17/base-seed101-central-freeze-1ep/result.json
    title: Bestandener Gegenlauf nach zentralem Fovea-Freeze
  - id: fovea-fixed40
    resource: ../../log/d0-evaluation/seed17/base-seed101-central-freeze-40ep/result.json
    title: Bestandene 40-Episoden-Freeze-Wiederholung
---

# Behauptung

Eine einzelne kopflose FSM-Autoepisode mit `ACT23_NO_PERSIST=1` veraendert im laufenden Prozess
neun von zehn beobachteten D0-Komponenten. Die Pkl-Kopie selbst blieb SHA-256-bitgleich. Damit
ist direkt gemessen: fehlendes Zurueckschreiben ist keine eingefrorene Evaluation.

# Zahlen

Start: D0-Basis `base.pkl`, SHA-256 `ad9d768c...c09b9e`, eine Episode, FSM, keine Persistenz.
Der Runner schrieb ein Vorher-/Nachher-Manifest im selben Prozess und meldete `FAIL` bei
Returncode 0.

| Unveraendert | Veraendert |
|---|---|
| `dream_seen`; Pkl-Dateihash | `bm`, `colours`, `fovea`, `latent_dynamics`, `latent_goal`, `runtime`, `self_eval`, `shape_clf`, `world` |

Die Kreditzeile hatte `Label Selbst`, Quelle `Selbst`, Route `sicher geliefert`, Gewicht 1,0;
das Selbsturteil war also fuer die Protokollierung gueltig. Der gepinnte Objektfilter war jedoch
zu breit: `ACT23_AUTO_OBJ=L` matchte den Buchstaben in "Rotes Wuerfel" und fuhr den roten Wuerfel.
Dieser Lauf ist deshalb **kein** L-Wrist-Vorversuch, sondern ausschliesslich ein
Zustandsintegritaetsbefund.

# Korrigierte L-Form-Wiederholung

Nach der Korrektur auf `ACT23_AUTO_OBJ=L-Form` fuhr der Preflight tatsaechlich `obj_L`.
Der FSM-Griff scheiterte kausal (`Griff am Objekt fehlgeschlagen (Aktion)`), mit
`action_source=Selbst`, `label_source=Selbst`, Gewicht 1,0 und relativem Wrist 22,5 Grad.
Die Pkl-Kopie blieb wiederum bitgleich; die identische Liste aus neun Komponenten mutierte.

Diese Wiederholung macht den Befund fuer den gewaehlten D0-Gegenstand gueltig. Sie zeigt nicht,
dass alle neun Differenzen jeweils Lernen sind: etwa `latent_goal` enthaelt auch den
episodischen Zielzustand. Der naechste Freeze-Audit trennt deshalb Update-Stellen von erlaubtem
Aufgaben-Zustand, bevor Methoden gesperrt werden.

# Bestandener Freeze-Preflight

`ACT23_D0_FREEZE=1` sperrt die im Audit gefundenen Lernpfade: Weltmodell-Kredit,
Runtime-DAgger und -Imitation, Fovea-Lernen, Open-Set-Glance, Body-Modell-Refinement,
Latent-Dynamics sowie die Statistik des Selbsturteils. Der erneute L-Form-Lauf bestand:

| Pruefung | Ergebnis |
|---|---|
| Objekt, Episode | `obj_L`, eine FSM-Episode |
| Aktion / Label | Selbst / Selbst, Fehlgriff, Gewicht 1,0, relativer Wrist 22,5 Grad |
| Pkl-Kopie | vor/nach SHA-256 `ad9d768c...c09b9e` |
| Lernzustand | **0 geaenderte Komponenten** |
| Vollzustand | `fovea`, `latent_goal`, `runtime`, `self_eval`, `shape_clf`, `world` |

Der Vollzustand bleibt absichtlich sichtbar: Fovea-Aktivierungen, der episodische Zielvektor,
letzte Wahrnehmungsdiagnostik und die Zufallsfolge der Kandidaten aendern sich beim Lesen und
Ausfuehren. Der D0-Lernfingerabdruck umfasst dagegen Gewichte, Trainingspuffer und dauerhafte
Kalibrierungen. Der Werkzeugtest prueft beide Seiten: RNG-Fortschritt ist im Voll-Audit sichtbar,
eine Gewichtsveraenderung bleibt ein Freeze-Fehler.

# Bewertung

Der Runner und die In-Process-Manifeste funktionieren: sie machten genau die Mutationen sichtbar,
die der Audit vermutet hatte, und der getrennte Lernzustandsfingerabdruck besteht nach den
expliziten Wachen. Damit ist die notwendige D0-Voraussetzung fuer eine nichtlernende Kontrolle
erfuellt.

Die einzelne Episode traegt keinen Lern- oder Wirkungsnachweis. Das Kontrolltor wurde danach
mit der vorab vorgesehenen 40-Episoden-Familie wiederholt (siehe unten). Der naechste Schritt
ist die fachliche Auswertung von Basis- und Seed-17-Trainingscheckpoint auf dieser Familie;
erst dann darf die Wrist-Lernserie einen Wirkungsbefund beanspruchen.

# Fovea-Regression und Reparatur

Der erste geplante gefrorene 40-Episoden-Test (`Seed 101`, L-Form, eigene Pkl-Kopie) schlug
trotz unveraenderter Pkl fehl: Der Lernfingerabdruck nannte ausschliesslich `fovea`; die
Feindiagnose sah **1883/1883** Verbindungsgewichte W und **65** temporale Knotenmatrizen V
veraendert. Startup-Warmup und das explizite Klassen-Training liefen nach Log nicht. Ein
isolierter Realtest mit `HexFovea.step(..., learn=False)` und `step_id(..., learn=False)` hielt
W, V und Selektionskopf dagegen bitgleich. Der Fehler liegt damit nicht in der PC-Operation
`learn=False`, sondern in einem im Vollpfad erreichbaren Lernaufruf.[^fovea-regression]

Die Reparatur setzt die D0-Grenze direkt in `HexFovea.step()` und `step_id()`: Bei
`ACT23_D0_FREEZE=1` werden `learn` und bei `step()` auch `train_sel` immer auf `False`
gesetzt. Der Test deckt explizit den Fall ab, dass ein Aufrufer `learn=True` uebergibt.
Der anschliessende echte Gegenlauf auf einer **neuen** Kopie der identischen D0-Basis bestand:

| Pruefung | Ergebnis |
|---|---|
| Szenario | Seed 101, L-Form, FSM, 1 Episode |
| Lernzustand | **0 geaenderte Komponenten** |
| Pkl-Quelle und -Kopie | beide `ad9d768c...c09b9e` |
| Vollzustand | `fovea`, `latent_goal`, `runtime`, `self_eval`, `shape_clf`, `world` sichtbar veraendert |

Die danach auf genau derselben Basis gefahrene 40-Episoden-Wiederholung besteht ebenfalls:

| Pruefung | Ergebnis |
|---|---|
| Szenario | Seed 101, L-Form, FSM, 40 Episoden |
| Lernzustand | **0 geaenderte Komponenten** |
| Pkl-Quelle und -Kopie | beide `ad9d768c...c09b9e` |
| Vollzustand | `bm`, `fovea`, `latent_goal`, `runtime`, `self_eval`, `shape_clf`, `world` sichtbar veraendert |

Damit ist das D0-Freeze-Kontrolltor fuer die Seed-101-Testfamilie wieder offen. Es belegt nur
Nichtmutation der Kontrolle, keine Wrist-Lernwirkung.[^fovea-fixed40]

[^fovea-regression]: `log/d0-evaluation/seed17/base-seed101-fovea-diagnostic/result.json`
[^fovea-fixed]: `log/d0-evaluation/seed17/base-seed101-central-freeze-1ep/result.json`
[^fovea-fixed40]: `log/d0-evaluation/seed17/base-seed101-central-freeze-40ep/result.json`
