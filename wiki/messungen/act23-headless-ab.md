---
type: Messvorschrift
title: Kopfloses A/B im vollen act23-Lauf
description: Der Standardaufbau, um eine Aenderung an act23 zu bewerten - kopfloser Lauf, ein Schalter als einzige Abweichung, Auswertung ueber die Lieferquote mit Fisher-Test.
tags: [act23, messen, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-07T00:00:00Z }
sources:
  - id: skill
    resource: ../.agents/skills/run_comparison_runs/SKILL.md
    title: Skill run-comparison-runs (act16/act21-Aufbau, Hooks, Skelettskript)
---

# Zweck

Die einzige Ebene, auf der eine **Wirkung auf act23** behauptet werden darf. Alles darunter ist
Lokalisierung - siehe [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md).

# Aufbau

Python immer aus der venv. PowerShell:

```powershell
$env:ACT23_VIZ="0"           # kopflos: main_diag() statt GUI
$env:ACT23_STATE_HEADLESS="1" # sonst startet ein frisches Bootstrap-Netz
.venv/Scripts/python.exe src/pc_cvnn/pc_act23.py 2>&1 | Select-String -Pattern "delivered|geliefert|Quote"
```

Fuer das A/B genau **einen** Schalter zwischen den beiden Laeufen aendern, alles andere gleich
lassen, und beide Laeufe aus demselben Zustand starten:

```powershell
$env:ACT23_STATE_PATH="src/pc_cvnn/state/act23_state.pkl"   # gemeinsamer Ausgangszustand
$env:ACT23_NO_PERSIST="1"                                   # nicht zurueckschreiben
```

Der Einsprungpunkt entscheidet sich in `pc_act23.py:4820`:
`ACT23_VIZ=1` -> Steuer-GUI, sonst `ACT23_MODE` (`diag` ist Vorgabe, `shapes` fuer den
Formenlauf).

# Kriterium

* Zielgroesse: **gelieferte Episoden / Episoden**. Nebengroessen: Median-Endabstand,
  Riegel/Schritt, |Netz - Teacher|.
* Auswertung mit Fishers exaktem Test. Bei mehreren Objekten oder Formen
  **Bonferroni-Schranke** angeben (bei 7 Objekten 0,0071).
* Stichprobe: unter ~150 Episoden je Arm sind Unterschiede unter 10 Punkten nicht zu trennen -
  der Langlauf hat +2,1 Punkte bei n = 554 je Haelfte mit p = 0,51 geliefert.

# Fallen

* **Gleicher Seed erzwingt in act23 keine gleiche Objektfolge.** Zwei Arme sehen nicht
  automatisch dieselben Szenen; das gehoert in die Auswertung (Objektmischung vergleichen).
* **Ein GUI-Lauf schreibt den Zustand zurueck**, wenn `ACT23_STATE_PATH` nicht gesetzt ist.
  Vor einem Langlauf einen Rueckfallpunkt sichern.
* Reine Messausgabe (`ACT23_DEBUG`, `ACT23_YAW_AB`, `ACT16_RULEDIAG/GLAUBDIAG/TASTDIAG`)
  beeinflusst das Verhalten nicht und darf zwischen den Armen abweichen.

# Verwandt

* [Wiederholungsmessung EXV](/messungen/exekutionsvarianz-exv.md)
* [Vorgaben 2026-08-30](/entscheidungen/defaults-2026-08-30.md) - was ohne Schalter gilt
