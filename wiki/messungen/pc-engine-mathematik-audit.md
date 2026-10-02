---
type: Messvorschrift
title: Isolierter mathematischer PC-Engine-Audit
description: Energiegradienten, Aktivierungen, temporales Lernen und Ausführungsgleichheit ohne Robotersimulation prüfen.
tags: [pc-cvnn, engine, audit]
status: stable
evidenz: gemessen
ebene: pruefstand
sources:
  - resource: ../../src/pc_cvnn/pc_engine_math_audit.py
    title: Ausführbarer Audit
  - resource: /befunde/pc-engine-mathematik-audit.md
    title: Vertrag, Ergebnisse und Grenzen
---

# Ausführung

Aus dem Codex-Worktree in PowerShell; das vorhandene Environment genügt, kein pytest erforderlich:

```powershell
& ..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\pc_engine_math_audit.py --output log\pc-engine-audit-neu\result.json
& ..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\test_relax_vec.py
```

Der erste Befehl verweigert Überschreiben bestehender Ergebnisse. Er schreibt Engine-SHA256,
alle Messwerte und boolesche Urteile; keine PKL wird geladen oder gespeichert. Kleine künstliche
Netze existieren nur im Prozess. Der zweite Befehl ist die vorhandene standalone Regression.

# Bewertung

Zentrale Differenzen nach Real- und Imaginärteil, h=1e-6, relative Toleranz 1e-6.
Vier Fallfamilien mit je Seeds 11/17/23 trennen Konjugation, Aktivierung und Mittelung;
analytische Referenzen kontrollieren die numerische Ableitung unabhängig von der Engine.
Hinzu kommen exakter Energieanstieg, PCNode-Lebenszyklus, temporaler Gradient, bekannte
komplexe lineare Lernaufgabe und Objekt-/Vektorparität.

**Exitcode 0 bedeutet nur, dass der Audit ausgeführt wurde.** Der aktuelle Gesamtbefund
`energy_gradient_contract_passed=false` ist ein Fehlerbefund; bekannte Abweichungen werden
nicht als bestandene Engine-Tests umgedeutet. Einzelne Lebenszyklusfelder sind beschreibende
Beobachtungen, keine Freigabe. Alle Einzelwerte zusammen mit dem Referenzvertrag lesen.

Ergebnisse vom 2026-10-02 liegen in `log/pc-engine-audit-20261002/with-reference.json` und
`vector-regression.txt`. Die frühere `result.json` ist der erste Lauf vor Ergänzung der
analytischen Referenzen und bleibt erhalten. Rohlogs sind lokal; Skript und Befund sind versioniert.
