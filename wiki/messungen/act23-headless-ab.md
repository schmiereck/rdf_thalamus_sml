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

# Gepaart je EPISODE, nicht nur je Seed (seit 2026-09-23)

Zwei Arme mit demselben Seed sehen ohne weitere Massnahme **nicht** dieselben Szenen: im
gepaarten Stufe-4-Sweep waren es 88 von 200 Episoden, meist trennten sie sich ab Episode 2-3.
Die gesamte Streuung zwischen den Szenen landete damit im Vergleich (Arm A: 20-60 % ueber
Seeds). Drei Quellen:

| Quelle | Abhilfe |
|---|---|
| `crng` laeuft ueber alle Episoden durch | `ACT23_SZENE_JE_EPISODE=1`: je Episode auf `default_rng([SEED, ep])` zurueckgesetzt |
| das kommandierte Objekt bleibt liegen, wo der Arm es hinlegte | derselbe Schalter baut die Szene jede Episode neu |
| die Neugier waehlt nach GELERNTEN Werten | `ACT23_AUTO_CURIOUS=0` - bewusst NICHT vom Schalter mitgezogen, der Start meldet es |

**Pruefen statt behaupten:** mit dem Schalter schreibt jede Episode einen `[Szenen-Abdruck]`,
eine Pruefsumme ueber Objektwahl, Ziel, alle Koerperlagen, Farben und Sockel. Zwei Arme sind
episodenweise gepaart, wenn ihre Abdruecke Zeile fuer Zeile uebereinstimmen. Gemessen auf Seed
8103 (im Sweep 5 von 25): **10 von 10 identisch**, bei nachweislich verschieden fahrenden Armen.

**Auswertung dann mit McNemar** auf den abweichenden Paaren (A geliefert / B nicht, und
umgekehrt) statt mit Fisher ueber zwei unabhaengige Stichproben. Gleich ausgehende Paare tragen
keine Information ueber den Unterschied und fallen heraus - genau das macht den Test scharf.

**Was die Paarung NICHT festhaelt:** den gelernten Zustand. Beide Arme lernen waehrend des Laufs
weiter, und zwar verschieden - das ist der Behandlungseffekt, der sich fortpflanzt, und gehoert
zur Frage "was tut der Schalter ueber die Zeit". Wer den reinen Momenteffekt will, braucht
zusaetzlich eine eingefrorene Auswertung (Codex hat fuer D0 eine gebaut, mit nachweislich leeren
Lernzustands-Diffs).

# Kriterium

* Zielgroesse: **gelieferte Episoden / Episoden**. Nebengroessen: Median-Endabstand,
  Riegel/Schritt, |Netz - Teacher|.
* Auswertung mit Fishers exaktem Test. Bei mehreren Objekten oder Formen
  **Bonferroni-Schranke** angeben (bei 7 Objekten 0,0071).
* Stichprobe: unter ~150 Episoden je Arm sind Unterschiede unter 10 Punkten nicht zu trennen -
  der Langlauf hat +2,1 Punkte bei n = 554 je Haelfte mit p = 0,51 geliefert.

# Fallen

* **`GELIEFERT` steht in GROSSBUCHSTABEN, `NICHT geliefert` klein.** Die Erfolgszeile lautet
  `[Auto 7] GELIEFERT | Abstand 22 mm`, die Misserfolgszeile `[Auto 8] NICHT geliefert`. Ein
  fallunterscheidendes `grep geliefert` trifft damit **ausschliesslich die Misserfolge** und
  zaehlt jeden Erfolg als Fehlschlag. Das sieht nicht wie ein Fehler aus, sondern wie ein
  durchgaengiges Null -- und weil es jeden Arm gleich trifft, ueberlebt es auch ein A/B.
  **Es hat mich am 2026-09-22 einen halben Tag Ursachensuche fuer einen Ausfall gekostet, den es
  nicht gab, und ein positives Stufe-4-Ergebnis als negatives ins Wiki gebracht**
  ([dort berichtigt](/befunde/stufe4-abstapeln-gemessen.md)).
  **Zwei unabhaengige Zeilen zaehlen dasselbe** und stimmen Episode fuer Episode ueberein --
  `[Auto N] GELIEFERT` und `[Selbst-Urteil] ... = Welt: geliefert`. Wer eine Quote meldet, zaehlt
  beide und vergleicht sie; weichen sie ab, stimmt die Auswertung nicht.
* **Hoechstens ZWEI act23-Prozesse gleichzeitig auf diesem Rechner.** Ein act23-Lauf braucht
  ~0,6 GB. Zwei parallele Arme liefen am 2026-09-22 acht Seeds lang sauber durch; **drei** brachten
  den Rechner am 2026-09-23 schon in der Startphase auf 2,9 von 11,8 GB frei, und Claude Code hat
  die Laufreihe wegen kritischen Speichers gestoppt. **Dabei liefen die Python-Kinder verwaist
  weiter**, und weil das Beenden ihrer Kinder das `wait` der Schleife freigab, startete die noch
  lebende Schleife sofort den naechsten Seed. Aufraeumen heisst deshalb: **zuerst die Wurzel
  der Schleife beenden, dann die Kinder**, und danach pruefen, dass nichts nachstartet.
* **Eine Quote von exakt 0 ist ein Verdachtsfall, kein Ergebnis.** Die gewoehnliche
  Transportaufgabe liefert auf dem gespeicherten Zustand 40 bis 66 % (gemessen 2026-09-22:
  `netz` 66 %, `fsm` 40 %). Wer 0 misst, hat mit hoher Wahrscheinlichkeit die Auswertung
  kaputt und nicht den Agenten. **Erst die Grundlinie mit demselben Befehl nachmessen, dann
  Ursachen suchen.**


* **McNemar ueber Episoden ueberschaetzt, weil der Agent im Lauf weiterlernt.** Eine fruehe
  Abweichung zwischen den Armen pflanzt sich in alle spaeteren Episoden desselben Seeds fort; die
  Episoden sind nicht unabhaengig. Gemessen am 2026-10-01 ([Platte ausblenden](/befunde/platte-ausblenden-ab.md)):
  3 Seeds gaben p = 0,099 in die eine Richtung, 6 neue p = 0,023 in die andere, zusammen
  p = 0,41. **Massgeblich ist das Vorzeichen ueber SEEDS**; Episoden-p nur als Beiwerk, und nie
  ohne Replikation auf neuen Seeds als Befund melden.
* **Gleicher Seed erzwingt in act23 keine gleiche Objektfolge** - das gilt fuer zwei
  **verschiedene** Konfigurationen: die Arme laufen identisch, bis der Schalter zum ersten Mal
  eine Entscheidung aendert, und danach voellig auseinander (gemessen: identisch bis Episode 18,
  ab 19 nur noch 10 % gleiche Szenen). Die Objektmischung gehoert deshalb in jede Auswertung.
  Bei **gleicher** Konfiguration erzwingt derselbe Seed sehr wohl dieselbe Folge, vollstaendig.
* **Die Replikate sind die SEEDS, nicht die Wiederholungen.** Denselben Lauf zweimal zu fahren
  bringt null neue Information - er ist bitgleich. Wer Streuung braucht, variiert `ACT23_SEED`;
  fuer einen belastbaren Vergleich einen **gepaarten Sweep**: je Seed beide Arme, dann
  Vorzeichentest ueber die Seeds. Siehe
  [Zwei Laeufe sind dieselbe Rechnung](/befunde/laeufe-sind-reproduzierbar.md).
* **`ACT23_SEED` nicht gesetzt heisst 7, obwohl die Kopfzeile `SEED=11` meldet.** Wer einen Lauf
  aus dem Protokoll nachstellen will, muss `ACT23_SEED=7` setzen, nicht 11.
* **Ein GUI-Lauf schreibt den Zustand zurueck**, wenn `ACT23_STATE_PATH` nicht gesetzt ist.
  Vor einem Langlauf einen Rueckfallpunkt sichern.
* Reine Messausgabe (`ACT23_DEBUG`, `ACT23_YAW_AB`, `ACT16_RULEDIAG/GLAUBDIAG/TASTDIAG`)
  beeinflusst das Verhalten nicht und darf zwischen den Armen abweichen.

# Verwandt

* [Wiederholungsmessung EXV](/messungen/exekutionsvarianz-exv.md)
* [Vorgaben 2026-08-30](/entscheidungen/defaults-2026-08-30.md) - was ohne Schalter gilt
