---
type: Mechanismus
title: D0-Integritaet - Fingerabdruck und Kreditprotokoll
description: Der D0-Helfer erzeugt getrennte Fingerabdruecke fuer Voll- und Lernzustand sowie opt-in JSONL-Kreditzeilen; der gefrorene FSM-L-Preflight besteht.
tags: [act23, dream-rsi, d0, zustand, kredit, reproduzierbarkeit]
status: stable
evidenz: einzelmessung
ebene: code
generated: { by: codex, at: 2026-09-18T07:45:00Z }
sources:
  - id: module
    resource: ../../src/pc_cvnn/arm_modules/d0_integrity.py
    title: Komponentenfingerabdruck und JSONL-Schreiber
  - id: test
    resource: ../../src/pc_cvnn/test_d0_integrity.py
    title: Deterministischer Werkzeugtest
  - id: audit
    resource: /befunde/dream-rsi-d0-wrist-audit.md
    title: Audit, der den Mechanismus verlangt
---

# Behauptung

Der neue Helfer `d0_integrity.py` macht zwei fuer D0 getrennte Tatsachen pruefbar: ob eine
wegwerfbare Evaluation einen deklarierten Lerneranteil veraendert hat, und welche Kreditquelle
eine konkrete Weltmodellzeile hatte. Er aendert keinen ACT23-Vorgabepfad.

# Aufbau

`component_fingerprints()` serialisiert die Komponenten in derselben Darstellungsfamilie wie
ACT23-Persistenz und bildet je Komponente einen SHA-256. Das Vollmanifest umfasst Bodymodell,
Formklassifikator, Weltmodell, Runtime, Farben, optionale Fovea, Ziel-/Dynamikmodule,
Neuheitsspeicher und SelfEval. Fehlende optionale Komponenten werden als `absent` festgehalten,
nicht still ausgelassen.

Daneben schreibt jedes Manifest `learning_components`. Dieser Fingerabdruck umfasst nur
Gewichte, Trainingspuffer und persistente Kalibrierung. Fovea-Aktivierungen, Portwerte,
Diagnosehistorien, episodisches Ziel und Generatorfortschritt bleiben im Vollmanifest sichtbar,
zaehlen aber nicht als Lernen. Der Runner legt beide Diffs ab; `passed` verlangt einen leeren
Lernzustands-Diff und einen bitgleichen Pkl-Kopiehash.

`snapshot()` schreibt diese Fingerabdruecke samt Kontext in ein Manifest. `changed_components()`
liefert die betroffenen Namen mit Vorher-/Nachher-Werten, `assert_unchanged()` verwirft eine
falsch als eingefroren bezeichnete Auswertung.

`ACT23_D0_CREDIT_JSONL=<wegwerfbarer Pfad>` aktiviert zusaetzlich zu den normalen
`[Kredit]`-Zeilen ein JSONL-Protokoll. Jede gespeicherte Weltmodellzeile enthaelt mindestens
Aktions- und Labelquelle, Route, Ausgang, Gewicht, Wrist und relativen Wrist, Griff, SelfEval-
Distanz, Einfrierstatus und Pufferzeilen. Ohne den Schalter wird keine Datei angelegt und der
Steuerpfad bleibt unveraendert.

# Pruefung

`src/pc_cvnn/test_d0_integrity.py` hat Komponentenfingerabdruck, erkannte Weltmodellmutation,
Manifest-Schreiben und JSONL-Kreditzeile in der gemeinsamen venv ausgefuehrt: `D0 integrity:
OK`. `py_compile` pruefte ausserdem Helfer und `pc_act23.py`.

Das ist ein Werkzeugtest, kein ACT23-Lauf und kein Nachweis, dass die komplette Evaluation
einfriert. Ein Volltest wird erst nach Abschluss der parallelen Stapelreihe auf einer
Zustandskopie gefahren.

# Wegwerfbarer Preflight-Runner

`src/pc_cvnn/act23_d0_evaluation_runner.py` kopiert einen explizit genannten Startzustand nach
`log/d0-preflight/<Zeit>/state-input.pkl`, setzt `ACT23_NO_PERSIST=1` und startet eine feste Zahl
kopflose FSM-Autoepisoden. Die Quelle wird nie als `ACT23_STATE_PATH` verwendet.

Der Steuerpfad schreibt bei gesetztem `ACT23_D0_MANIFEST_DIR` im **gleichen Prozess** ein
`before.json` und `after.json`. Der Runner legt Voll- und Lernzustands-Diff ab, prueft zusaetzlich
den Hash seiner Zustandskopie und schreibt `result.json`, Log und Kredit-JSONL. Eine Lernmutation,
ein fehlendes Manifest oder ein geaenderter Pkl-Kopiehash ergibt `FAIL` und Exit-Code 2. Damit ist
ein stilles `NO_PERSIST`-Ergebnis ausgeschlossen: fehlendes Schreiben genuegt nicht zum Bestehen.

`ACT23_D0_FREEZE=1` sperrt die Update-Stellen fuer Weltmodell, Runtime, Fovea, Form-/Farb-
Open-Set, Body-Refinement, Latent-Dynamics und SelfEval-Statistik. Die Steuerung und das
Selbsturteil bleiben lesend aktiv, damit die eingefrorene Kontrolle dieselbe Aufgabe ausfuehrt.

# Naechster Schritt

Der gefrorene FSM-L-Preflight besteht, siehe [D0-Preflight](/befunde/dream-rsi-d0-preflight-mutation.md).
Als Naechstes werden Wiederholungen, Seeds, Budget und Abbruchregel der Wrist-Messvorschrift
festgelegt. Erst dann beginnt eine Lernserie.
