# rdf_thalamus_sml

Forschungsprojekt: eine praediktiv codierende, komplexwertige Netzarchitektur (PC-CVNN), die
einen MuJoCo-Roboterarm steuert. Aktuelle Linie ist **act23** (`src/pc_cvnn/pc_act23.py`).

**Das Ziel ist nicht ein effizienter Arm, sondern eine Architektur, die neue Farben, Formen,
Umgebungen und Aufgaben selbst lernt.** Den geskripteten Teacher zu schlagen ist ausdruecklich
nicht verlangt. Lies [wiki/ziel.md](wiki/ziel.md), bevor du ein Ergebnis als Erfolg oder
Misserfolg bezeichnest.

---

# Die Wissensbasis

Unter `wiki/` liegt ein fortgeschriebenes Markdown-Wiki: Messergebnisse, Architektur-
entscheidungen und deren Bewertung. Es ist der **Gedaechtnisspeicher des Projekts** und geht
allen anderen Dokumenten im Wurzelverzeichnis vor.

**[wiki/wiki.md](wiki/wiki.md) beschreibt das Verfahren** - Aufbau, Frontmatter, Operationen.
Lies es einmal, bevor du eine Seite anlegst.

## Pflicht: lesen

Vor jeder inhaltlichen Arbeit an act23:

1. [wiki/index.md](wiki/index.md) - der Katalog
2. [wiki/mechanismen/act23-modullandschaft.md](wiki/mechanismen/act23-modullandschaft.md) - der Einstieg
3. [wiki/fragen/offene-faeden-act23.md](wiki/fragen/offene-faeden-act23.md) - besonders der
   Abschnitt **"Ausdruecklich geschlossen"**. Dort stehen Wege, die gemessen nicht funktioniert
   haben. Schlage sie nicht erneut vor, ohne den Befund zu entkraeften.

Suchen: erst `index.md` lesen, dann `grep -ri "<begriff>" wiki/`.

## Pflicht: schreiben

Nach jedem Lauf, jeder Messung, jeder Entscheidung - im selben Arbeitsgang, nicht "spaeter":

1. Seite unter `wiki/befunde/`, `wiki/mechanismen/`, `wiki/entscheidungen/`, `wiki/messungen/`
   oder `wiki/fragen/` anlegen **oder eine bestehende fortschreiben**.
2. Frontmatter setzen, insbesondere `evidenz` und `ebene` (siehe unten).
3. Zeile in [wiki/index.md](wiki/index.md) ergaenzen.
4. Eintrag in [wiki/log.md](wiki/log.md) ergaenzen, neueste zuerst.
5. Widerspricht das Neue einer bestehenden Seite: die alte **nicht loeschen**, sondern
   `status: widerlegt` setzen, den Widerspruch auf beiden Seiten benennen und verlinken.

Auch eine Analyse, die im Gespraech entstanden ist, gehoert ins Wiki - sie darf nicht im
Chatverlauf versickern.

## Die zwei Felder, auf die es ankommt

`evidenz`: `vermutung` | `einzelmessung` | `gemessen` | `widerlegt`

`ebene`: `code` | `pruefstand` | `act23-ab` | `langlauf`

> **Ein Pruefstandsergebnis sagt einen act23-Lauf nicht vorher.** Das ist hier dreimal
> schiefgegangen ([wiki/mechanismen/pruefstandsfalle.md](wiki/mechanismen/pruefstandsfalle.md)).
> Wer eine Wirkung auf act23 behauptet, braucht `ebene: act23-ab` oder `langlauf`. Alles darunter
> lokalisiert eine Ursache, belegt aber keine Wirkung.

Ehrliche Negative sind vollwertige Seiten. Ein gemessenes "bringt nichts" ist hier das
haeufigste und teuerste Ergebnis - es wird abgelegt, nicht relativiert und nicht weggeworfen.

---

# Arbeiten am Code

## Laufen lassen

Python **immer** aus der venv: `.venv/Scripts/python.exe`. Shell ist PowerShell.

```powershell
# act23 mit GUI
$env:ACT23_VIZ="1"; .venv/Scripts/python.exe src/pc_cvnn/pc_act23.py

# act23 kopflos (main_diag)
$env:ACT23_VIZ="0"; $env:ACT23_STATE_HEADLESS="1"
.venv/Scripts/python.exe src/pc_cvnn/pc_act23.py
```

Einsprungpunkt: `pc_act23.py:4820`. `ACT23_VIZ=1` -> Steuer-GUI, sonst `ACT23_MODE`
(`diag` ist Vorgabe, `shapes` fuer den Formenlauf). Rund 120 `ACT23_*`-Schalter, alle als
Umgebungsvariablen.

Fuer A/B-Vergleiche gilt
[wiki/messungen/act23-headless-ab.md](wiki/messungen/act23-headless-ab.md). Der aeltere
act16/act21-Aufbau mit Mess-Hooks (`macro_log_fn`, `episode_end_fn`) steht in
[.agents/skills/run_comparison_runs/SKILL.md](.agents/skills/run_comparison_runs/SKILL.md).

## Zustand

`src/pc_cvnn/state/*.pkl` ist unversioniert und enthaelt das gelernte Wissen (aktuell 1053
Episoden, 70 MB). Ein GUI-Lauf **schreibt zurueck**, wenn `ACT23_STATE_PATH` nicht gesetzt ist.
Vor einem Langlauf einen Rueckfallpunkt sichern; alte Staende werden **nie geloescht**.
`ACT23_NO_PERSIST=1` verhindert das Zurueckschreiben.

## Zwei Architekturregeln des Projekts

1. **Alles laeuft durch ein lernendes Netz.** Keine Positionen, die von mathematischen
   Algorithmen erkannt und eingespeist werden. `perceive_all` (CC-Segmentierung + Homographie +
   PCA) ist geduldetes Uebergangsgeruest, kein Vorbild.
2. **Keine festen Regeln zur Laufzeit ausserhalb des Trainings.** Eine Regel darf Trainings-
   daten geruestartig stuetzen (Teacher, DAgger) und muss zur Testzeit verschwinden. Details und
   der geloeste Praezedenzfall: [wiki/mechanismen/laufzeit-regeln.md](wiki/mechanismen/laufzeit-regeln.md).

## Messhygiene

* Fisher-Test fuer Quotenvergleiche; bei mehreren Objekten Bonferroni-Schranke angeben.
* Halteteile **nie zufaellig** ziehen - nach Zeit mit Luecke, nach Lauf oder nach Szene teilen.
  Benachbarte Pufferzeilen stammen aus derselben stehenden Szene und sind Beinah-Duplikate.
* Gleicher Seed erzwingt in act23 **keine** gleiche Objektfolge.
* MuJoCo ist hier deterministisch. Streut ein Ergebnis, ist die Ursache kein Rauschen, sondern
  eine beobachtbare versteckte Zustandsvariable - meist die Armstellung beim Start.
* Temporaere Sondenskripte (`_probe.py` und dergleichen) nach Gebrauch aufraeumen, nicht
  committen. Fuer Zwischendateien das Scratchpad-Verzeichnis nutzen.

---

# Altbestand

Im Wurzelverzeichnis liegen aeltere Dokumente aus frueheren Projektphasen
(`RESEARCH-RESULT-*.md`, `experiment_log.md`, `manager_log.md`, `goal.md`,
`current_state.md`, `phase_0..5/`). Sie sind **Herkunft, nicht Wahrheit** - im Zweifel gilt das
Wiki. `ARCHITECTURE_2026-07-25.md` ist die Ausnahme: eine am Code verifizierte Bestandsaufnahme,
aus der die Mechanismus-Seiten stammen. Uebersicht: [wiki/raw/index.md](wiki/raw/index.md).
