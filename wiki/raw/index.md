# Rohbelege

Diese Schicht wird **nicht kopiert**, nur referenziert. Sie ist unveraenderlich: was hier steht,
wird nie umgeschrieben, nur ergaenzt. Jede Zahl im Wiki soll von hier aus nachvollziehbar sein.

# Laufprotokolle

`log/pc_act23_<datum>_<zeit>.txt` - je ein GUI- oder kopfloser act23-Lauf, angelegt von
`_start_session_log()` in `pc_act23.py`. Nicht in git (`log/` ist unversioniert), liegt nur
lokal. Die im Wiki zitierten Laeufe:

* `log/pc_act23_2026-08-11_10-52-00.txt` - EXV, 40 Szenen x 4, 6732 Weltzeilen, Lernen
  eingefroren -> [Exekutionsvarianz](/befunde/exekutionsvarianz.md)
* `log/pc_act23_2026-08-11_20-17-49.txt` - derselbe Aufbau mit geloggter Weltvorhersage
* `log/pc_act23_2026-08-26_13-44-26.txt` - Langlauf, 1109 Episoden, 43 h, Commit `7ca0657`
  -> [1109 Episoden ohne Lernfortschritt](/befunde/langlauf-ohne-fortschritt.md)
* `log/pc_act23_2026-08-28_17-20-45.txt` - Nachfolgelauf, 1053 Episoden, 56,4 %
  -> [Vorgaben 2026-08-30](/entscheidungen/defaults-2026-08-30.md)
* `log/pc_act23_2026-09-05_22-06-51_5152.txt` - GUI-Langlauf, 932 Episoden, 41 h, mit
  `ACT23_EIG_ONLY=1 ACT23_AUTO_EIG=1`, zwei `run_history`-Lastfenster (Ep 196-278, Ep 796-897)
  -> [Rechnerlast](/befunde/rechnerlast.md), [Episodendauer](/befunde/episodendauer.md),
  [Ablenker-Bindung](/befunde/ablenker-anfahrt.md)
* `log/pc_act23_2026-09-07_18-12-30_9556.txt` (Arm A, `FULL_EVERY=1`, 0 kurze Fits) und
  `log/pc_act23_2026-09-07_18-12-30_22068.txt` (Arm B, `FULL_EVERY=4`, 117 kurze Fits) - das A/B
  zum Welt-Fit-Plan, je 200 Episoden kopfloser Steuerungslauf, gleichzeitig gefahren, je eine
  eigene Zustandskopie -> [Sparsamer Welt-Fit, A/B](/befunde/welt-fit-plan-ab.md)

# Auswert- und Messwerkzeuge

* `src/pc_cvnn/act23_exv_report.py` - Auswertung der Wiederholungsmessung
* `src/pc_cvnn/act23_exec_variance.py` - Exekutionsvarianz
* `src/pc_cvnn/act23_wm_regime.py` - Weltmodell-Regime, die vier Nullrezepte
* `src/pc_cvnn/act23_split_probe.py`, `act23_colour_split_ab.py` - Form- und Farbsplit
* `src/pc_cvnn/act23_fusion_probe.py` - Verschmelzung ueber den Nachbarabstand (Abstandskurve)
* `src/pc_cvnn/act23_attractor_ab.py`, `act23_u_densegrasp_ab.py`, `act23_dose_workers.py`
* `src/pc_cvnn/run_history.py` - Laufhistorie

# Gelernte Zustaende

`src/pc_cvnn/state/*.pkl` - unversioniert (`.gitignore`). Aktuell `act23_state.pkl` = 1053
Episoden, 56,4 %. Rueckfallpunkte liegen datiert daneben; **nichts wird geloescht**.

# Aeltere Projektdokumente im Wurzelverzeichnis

Aus frueheren Phasen, noch nicht ins Wiki ueberfuehrt - Herkunft, nicht Wahrheit:

* `ARCHITECTURE_2026-07-25.md` - am Code verifizierte Bestandsaufnahme der act23-Module.
  Quelle fuer [Modullandschaft](/mechanismen/act23-modullandschaft.md) und
  [Laufzeitregeln](/mechanismen/laufzeit-regeln.md)
* `RESEARCH-RESULT-001..008.md`, `experiment_log.md`, `manager_log.md`, `research_journal.md`,
  `phase3_diagnostic_report.md`, `current_state.md`, `goal.md` - Phase 0-5, Mai 2026
* `pc-architecture.md`, `predictive-coding.md`, `temporal_hierarchy_design.md`,
  `README_ACT11.md`, `test_pc_act1.md` - aeltere Entwuerfe

# Agenteneigener Memory-Bestand

`~/.claude/projects/C--Users-thomas-Projekte-rdf-thalamus-sml/memory/` - 46 Dateien, ausserhalb
des Repos, nicht mitversioniert.

**Der act23-Teil ist ins Wiki uebertragen** (Nutzerentscheid 2026-09-07); die Dateien bleiben als
Quelle stehen und enthalten mehr Detail als die Verdichtungen - insbesondere
`act23-gui-and-fovea-goal.md` (1001 Zeilen, alle Commit-Hashes und Zwischenmessungen), verdichtet
zu [act23-Entwicklungslinie](/chronik/act23.md).

**Die aelteren Akte act5 bis act22 bleiben dort** und sind nicht ins Wiki uebertragen - an ihnen
wird nicht mehr gearbeitet. Sie sind ueber `MEMORY.md` erreichbar. Siehe
[Die Wissensbasis wird ein Wiki im Repo](/entscheidungen/wissensbasis-als-wiki.md).

# Externe Quellen

* [LLM Wiki (Karpathy)](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
* [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
