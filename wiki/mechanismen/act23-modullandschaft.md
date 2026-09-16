---
type: Mechanismus
title: act23 Modullandschaft
description: Welche ArmModules im act23-GUI-Lauf aktiv sind, was jedes steuert, was intern ein echtes PC-Netz ist und was nur ein MLP - Einstiegspunkt fuer jede act23-Arbeit.
tags: [act23, architektur, module]
status: stable
evidenz: gemessen
ebene: code
generated: { by: claude/opus-5, at: 2026-07-25T00:00:00Z }
verified: { by: human:thomas, at: 2026-07-25T16:37:00Z }
sources:
  - id: arch
    resource: ../ARCHITECTURE_2026-07-25.md
    title: ARCHITECTURE_2026-07-25.md, am Code verifizierte Bestandsaufnahme
---

# Behauptung

Alle Module erben von `ArmModule` (`src/pc_cvnn/arm_modules/base.py`) mit typisierten Ports.
Ein Teil hat intern ein echtes `PCNetwork`, andere sind MLPs oder analytisch - nach aussen sind
sie identisch steckbar.[^arch]

[^arch]: ARCHITECTURE_2026-07-25.md

# Aktiv im act23-GUI-Lauf

| Modul | steuert | intern |
|---|---|---|
| `VisualCortex` + `HexFovea` | wohin geschaut wird - Blickpunkt, Zoom, Occlusion-Recovery | echtes PCNetwork (komplex) |
| `ShapeClassifier` | Form erkennen/lokalisieren, Greifpunkt, offene Klassen (`neu-*`) | komplexe Harmonische + MLP-Kopf |
| `ColourOpenSet` | selbst benannte Farbklassen (`farbe-*`) | Chroma-Zentroide, reell |
| `BodyModel` (+ `LearnedInverseKinematics`) | wo die Hand ist - gelernte FK, IK-Reach | linear in Merkmalen, reell |
| `RuntimePolicy` | die Choreographie - `state(11)` -> `subgoal(4)` | MLP (act19-Policy), reell |
| `WorldModel` | wie gegriffen wird - Wrist/Grip/Offset per Ensemble-LCB | Ensemble, reell |
| `GoalModule2D` + `LatentGoalServo` | Platzierziel als Latent, Servo ueber Latent-Differenz | RoPE, komplex |
| `LatentDynamics` | `z_{t+1} = z_t + f(z,a)`, Surprise | komplex |
| `LatentAttractor` | Latent-Planung - **gemessen negativ, nicht nutzen** | komplex |
| `DistanceNovelty` | Neugier: welches Objekt, welches Traumziel | reell |
| `SelfEval` | Selbst-Urteil "geliefert?" ohne Privileg | reell |
| `ObjectMemory` | praediktives Objekt-Belief fuer den Blick beim Tragen | reell |

**Vorhanden, aber im act23-Lauf nicht verdrahtet:** `motor.py`, `planner_chain.py`,
`obstacle.py` / `obstacle_vision.py`, `wrist.py`, `object_orientation.py` (nur in
Trainingsroutinen). Das ist tote Flaeche, die bei Aufraeumarbeiten auffaellt.

# Wo die komplexe Zahl echte Arbeit leistet

Der Kern ist komplex: `node.py` / `connection.py` / `network.py` - `W` ist `complex128`, Lernen
ist konjugat-Hebbisch (Wirtinger, sonst divergiert es), Energien ueber `|eps|^2`, Clipping nach
Betrag, mod-Aktivierungen statt `tanh`.

Belegt tragend:

* **`ShapeClassifier`**: `F[ring,k]` komplex, Rotation = Phasenverschiebung, `|F|` per
  Konstruktion rotationsinvariant. Sauberster Fall - Klassifikation 85,7 % -> 100 %.
* **RoPE-Goal** (`planner.py`, `latent_goal.py`): Position lebt in der Phase, Decode ueber
  `np.angle`; Latent-Inverse `D` komplex, Aktion = `np.real(e @ D)`. Gemessen 18x dichter,
  ~7x genauer.
* **`HexFovea`**: laeuft im komplexen PC-Netz.

Reell geblieben: `RuntimePolicy` (die Choreographie!), `WorldModel`, `BodyModel`/IK, `SelfEval`,
`ObjectMemory`, `ColourOpenSet`. Der Shape-Kopf hat ein PC-Engine-Backend, Vorgabe ist aber der
MLP (`ACT_SHAPE_ENGINE=pc` schaltet um).

**Der Wrist - und was daran WIRKLICH offen ist (korrigiert 2026-09-16).** Der Winkel wird im
Aktionsvektor von Hand als `[cos2w, sin2w]` kodiert (`world_model.action_vec`), die
Situationsmerkmale tragen `cos2yaw`, `sin2yaw`.

**Die Invariante `cos2(w-yaw)` ist NICHT offen - sie ist gebaut, Vorgabe an und gemessen.**
`world_model.cross_augment` rechnet genau das komplexe Produkt, Zeile fuer Zeile:

    c = cw * cy + sw * sy     # cos2(w-yaw)  -- Re(z_w * conj(z_yaw))
    s = sw * cy - cw * sy     # sin2(w-yaw)  -- Im(...)

Dazu die Schaerfe `|cos2(w-yaw)|` (`ACT23_WORLD_SHARP`), dasselbe Produkt gegen die ARMRICHTUNG
`z_w * conj(z_alpha)` samt Distanz-Interaktion (`ACT23_WORLD_ARMREL`) und die Neigung gegen die
kinematisch erzwungene als `z_tilt * conj(z_kin)`. Belegt ist es zweifach: im Kapazitaetstest
findet das MLP die bilineare Regel ohne die Invariante erst bei ~3000 sauberen Zeilen, mit ihr bei
**n ~ 150**; im Lauf 27/40 = 67,5 % gegen 45 % (Kontrolle: ausgerichtete Griffe 89 %, nicht
ausgerichtete 48 %, der Gewinn ist also die Konditionierung).

**Offen bleibt nur die andere Haelfte, und sie ist kleiner, als sie klingt:** `WorldModel` laeuft
auf `Policy`, einem **reellen** MLP (`np.tanh`, reelle Gewichte) - es ist kein CVNN. Dort IST
`[cos2w, sin2w]` bereits `e^{2iw}` als (Re, Im); es als komplexe Zahl zu schreiben aendert keine
einzige Zahl. Ein wirklich nativer Wrist-Kopf hiesse, den Kopf in die komplexe PC-Engine zu
verlegen - ein eigener Bau ohne bisher formulierte Hypothese, was er besser machen soll.

Wovon der Wrist dagegen NICHT frei ist: er wird ueber ein **Gitter** gewaehlt
(`wrist_grid=8` ueber pi, also 22,5-Grad-Stufen) und per Ensemble-Argmax gescort - die vierte
diskretisierte Achse neben Farbe, Form und Groesse. Siehe
[stetige Adressierung](/fragen/stetige-adressierung.md) fuer dieselbe Frage an den drei anderen.

# Was pro Episode lifelong lernt

| Was | wie |
|---|---|
| `runtime` | `observe()` labelt jeden besuchten Zustand; `imitate()` bei Selbst-Erfolg; `train(200)` |
| `world` | `observe(feats, action, outcome)` + `train(600)` |
| `bm.body` | alle 3 Schritte `observe(q3, hand)` - FK aus echter Bewegung (`lifelong=True`) |
| `vc.fovea` | `step(..., learn=True)` pro Frame - das PC-Netz lernt durchgehend |
| `lat_dyn` | 1 Uebergang/Episode + `train(5)` |
| `colours`, `shape_clf` | `observe` / `observe_scene` beim Open-Set-Blick -> neue Klassen |
| `seval`, `dream_nov` | Statistik bzw. Neuheits-Gedaechtnis |

Ueber Laeufe persistiert (`save_state`): `bm`, `shape_clf`, `world`, `runtime` (24000 DAgger +
12000 Selbst-Imitation), `colours`, `latent_goal`, `latent_dynamics`, `dream_seen`, `self_eval`,
`shape_key`.

# Fallen

Die Latent-Dynamik startet **nicht** pro Lauf leer - `pack()` speichert den Puffer (Stand der
Bestandsaufnahme: 183 Uebergaenge). Der Negativbefund zum Attraktor bleibt trotzdem: ein
Uebergang pro Episode ist fuer Planung viel zu duenn.

# Verwandt

* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) - was daran noch hart geskriptet ist
* [Vorgaben 2026-08-30](/entscheidungen/defaults-2026-08-30.md)
