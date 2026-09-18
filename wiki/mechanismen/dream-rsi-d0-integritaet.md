---
type: Mechanismus
title: D0-Integritaet - Fingerabdruck und Kreditprotokoll
description: Der D0-Helfer erzeugt komponentenweise Zustandsfingerabdruecke und opt-in JSONL-Kreditzeilen; der erste volle Evaluator nutzt ihn erst im naechsten Schritt.
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
ACT23-Persistenz und bildet je Komponente einen SHA-256. Der D0-Satz umfasst Bodymodell,
Formklassifikator, Weltmodell, Runtime, Farben, optionale Fovea, Ziel-/Dynamikmodule,
Neuheitsspeicher und SelfEval. Fehlende optionale Komponenten werden als `absent` festgehalten,
nicht still ausgelassen.

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

# Naechster Schritt

Der noch fehlende `D0EvaluationRunner` erzeugt aus derselben geladenen Startkopie die beiden
Manifeste um einen festen Satz Testepisoden und bricht bei jeder Differenz ab. Erst dann kann die
Wrist-Messvorschrift Budget, Seeds und Abbruchregel endgueltig fixieren.
