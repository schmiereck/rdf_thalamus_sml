---
type: Mechanismus
title: Laufzeitregeln - was noch geskriptet ist
description: Drei Kategorien von Handarbeit im act23-Lauf (Teacher als Label-Quelle, echte Laufzeitregeln, Schwellen) und wie weit die Entwoehnung gediehen ist. act21 hat sie gemacht, act23 nicht.
tags: [act23, prinzip, regeln]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-08-25T00:00:00Z }
verified: { by: human:thomas, at: 2026-08-25T17:23:00Z }
sources:
  - id: arch
    resource: ../ARCHITECTURE_2026-07-25.md
    title: ARCHITECTURE_2026-07-25.md
  - id: riegel
    resource: /raw/index.md
    title: Riegel-Messung, act23, 2026-08-25
---

# Behauptung

"Geskriptet" wird im Projekt oft in einen Topf geworfen. Es sind drei sehr verschiedene Dinge,
und nur eines davon widerspricht dem [Projektziel](/ziel.md).

# (a) Teacher als reine Label-Quelle - gewollt

`pc_act16.reactive_subgoal()` ist die markovsche Regelchoreographie. Bei "Choreo: Netz" faehrt
sie **nicht**; `run_combined:485` nimmt `policy_fn(state)`, der Teacher labelt nur die besuchten
Zustaende fuer DAgger. Das entspricht dem Prinzip: eine Regel darf die **Trainingsdaten**
geruestartig stuetzen, nie den Agenten zur Testzeit torwaechten.

# (b) Echte Laufzeitregeln - widersprechen dem Prinzip noch

Alle in act23 per Vorgabe **an**:

* `CLOSE_GUARD` - verhindert Schliessen, solange das Objekt nicht tief genug ist
* `REFLEX` - Greifreflex bei Hover-Stall
* `WRIST_ALIGN`, `SOFT_RELEASE`, `BASE_CLEAR`, `PHASE_STALL`, `MAX_REACQ`
* die FSM-Phasenmaschine (`over` / `lower` / `close` / `lift` / `carry` / `place`) laeuft als
  Buchhaltung mit und entscheidet Uebergaenge und Abbrueche

# (c) Infrastruktur und Schwellen, die als Wissen wirken

* Kredit-Routing: `lifted > 20 mm`, `world_tol 25 mm` (U: 22), `imit_tol 15 mm`
* Greifpunkt-Heuristiken: "naechstes Material zum Schwerpunkt", "dichtester Punkt"
* `carry_z = max(0.09, 2*obj_h + 0.02)`, `grasp_z = obj_h + 0.006`
* der privilegierte Rueckfall: schlaegt die Perzeption fehl, nimmt `perceive()` die wahre Position

# Der geloeste Praezedenzfall (act21)

Ein Laufzeit-`CLOSE_GUARD` reparierte "die Klaue schliesst bei langsamem Sinken zu hoch" - und
wurde vom Nutzer trotz Wirksamkeit zurueckgewiesen, weil eine feste Hoehenverriegelung nicht auf
andere Objekthoehen oder kuenftiges Stapeln verallgemeinert.

Loesung (Commit `dc92487`): `ACT21_RULES_TRAIN_ONLY` (Vorgabe 1). Riegel und Reflex sind nur
noch waehrend BC und Recovery-DAgger aktiv, dann fuer Auswertung **und** Steuer-GUI aus.
**Bewiesen, dass das Netz es gelernt hat:** mit Riegel und Reflex zur Laufzeit aus liefert der
volle Vorgabelauf identisch - B lifelong+curiosity 23/24, C eingefroren 10/10, genau wie mit
Regeln. Zur Laufzeit entscheidet also das gelernte `MotorModule` allein.

# Der offene Fall (act23)

**act23 hat die Entwoehnung nie mitgemacht** (geprueft 2026-08-25 am Code):
`ACT21_RULES_TRAIN_ONLY` steht ausschliesslich in `pc_act21.py`; in `pc_act23.py` kommt
`CLOSE_GUARD` nur in einem Kommentar vor ("guards stay on by default"). In der act23-GUI laufen
beide Regeln zur Laufzeit mit.

Gemessen wurde das dann auch: Riegel und Reflex sind ein **gekoppeltes Paar** - eines allein zu
entfernen ist schlimmer als beide zu entfernen. Die act23-Policy hat die Schliess-Entscheidung
nicht gelernt.[^riegel] Unabhaengig bestaetigt bei neunfacher Episodenzahl im
[Langlauf](/befunde/langlauf-ohne-fortschritt.md): der Riegel greift nach 1109 Episoden so oft
ein wie am Anfang.

[^riegel]: Riegel-Messung, act23, 2026-08-25

# Folgen

Offen. Der langfristige Weg (bisher nicht gebaut): das Schliessen aus einem **wahrgenommenen**
Objekt-im-Greifer- bzw. Kontaktsignal treiben (Active Inference) statt aus der Hoehenschwelle
des Teachers - dann traegt es ueber Objekthoehen und Stapeln, ohne auch nur eine
trainingszeitliche Hoehenregel.

Ein naheliegender Ersatz ist bereits **ehrlich negativ**: der Fingerdruck-Tastsinn kann die
Schliess-Entscheidung dreifach gemessen nicht tragen.

# Verwandt

* [Projektziel](/ziel.md)
* [Modullandschaft](/mechanismen/act23-modullandschaft.md)
