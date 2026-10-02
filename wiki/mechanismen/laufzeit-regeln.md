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

# Bestandsaufnahme 2026-10-02 (am Code geprueft)

Was sich seit dem 25.08. bewegt hat, und was nicht:

**Gefallen:** die Oberkante der Auflage (`geom_size`) beim Stapeln - der `HoehenSchaetzer` liest
sie aus der Detektion und lernt seine Etiketten aus der Beruehrung
([Oberkante ohne Privileg](/befunde/oberkante-ohne-privileg.md),
[Tastetikett gegen Privileg](/befunde/tastetikett-gegen-privileg.md)).

**Unveraendert zur Laufzeit an** (`pc_act16.py`): `CLOSE_GUARD` (:216), `REFLEX` (:122),
`SOFT_RELEASE` (:212), `WRIST_ALIGN`, `PHASE_STALL`, `MAX_REACQ`, die Phasen-Buchhaltung.

**Unveraendert privilegiert:** `obj_h = cmd_half[2]` und `obj_fp` aus der ECHTEN Geometrie
(`run_combined`, :484) - daran haengen `grasp_z`, `carry_z`, `lift_thresh` (:318-320) UND die
Hoehenschwelle des Riegels. Die Groesse kommt also beim GREIFEN noch aus MuJoCo, waehrend sie beim
ABLEGEN auf einen Stapel schon geschaetzt wird - dasselbe Werkzeug ist vorhanden, nur nicht auf
das Greifobjekt angewandt. Dazu der privilegierte Wahrnehmungs-Rueckfall (pc_act23 :5895/:5915,
zuletzt gemessen 4-6 %).

**Inzwischen gemessen negativ** fuer den Ersatz des Riegels: Fingerdruck (dreifach, 08/2026),
Codex D0b "visueller Greifzustand" mit fester Rohregel (Precision 0,786 unter dem Tor 0,80,
zurueckgestellt), Codex S1 komplexer PC-Vorwaertsexperte auf Servo-Uebergaengen (MSE 150-fach
schlechter als Persistenz).

**Geruest, nicht Regel, aber nach [Ziel](/ziel.md) abzubauen:** `perceive_all`
(CC-Segmentierung + Homographie + PCA), die Greifpunkt-Heuristiken, die Diskretisierung von
Farbe/Form/Groesse/Wrist (`wrist_grid=8`), die Kredit-Schwellen (20 mm Hub, 25/22/15 mm Toleranz).

Reihenfolge-Vorschlag nach Hebel und Risiko: (1) `obj_h`/`obj_fp` beim Greifen aus derselben
Detektion schaetzen wie die Oberkante beim Stapeln - kleinster Schritt, Werkzeug existiert, und er
ist die Voraussetzung dafuer, dass ein Riegel ueberhaupt ohne Privileg denkbar wird; (2) den
privilegierten Rueckfall durch "nicht gefunden -> erneut schauen" ersetzen und messen, was er
kostet; (3) erst danach die Schliess-Entscheidung selbst.
