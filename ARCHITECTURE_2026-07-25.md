Hier die Bestandsaufnahme, alles am Code verifiziert.

# 1. Die Modul-Landschaft

Alle Module erben von ArmModule (arm_modules/base.py) mit typisierten Ports; ein Teil hat intern ein echtes PCNetwork, andere sind MLPs oder analytisch — nach außen identisch steckbar.

Aktiv im act23-GUI-Lauf:

┌──────────────────────────────────────┬────────────────────────────────────────────────────────────┬────────────────────────────────┐
│                Modul                 │                          steuert                           │             intern             │
├──────────────────────────────────────┼────────────────────────────────────────────────────────────┼────────────────────────────────┤
│ VisualCortex + HexFovea              │ wohin geschaut wird — Blickpunkt, Zoom, Occlusion-Recovery │ echtes PCNetwork (komplex)     │
├──────────────────────────────────────┼────────────────────────────────────────────────────────────┼────────────────────────────────┤
│ ShapeClassifier                      │ Form erkennen/lokalisieren, Greifpunkt, offene Klassen     │ komplexe Harmonische +         │
│                                      │ (neu-*)                                                    │ MLP-Kopf                       │
├──────────────────────────────────────┼────────────────────────────────────────────────────────────┼────────────────────────────────┤
│ ColourOpenSet                        │ selbst-benannte Farbklassen (farbe-*)                      │ Chroma-Zentroide, reell        │
├──────────────────────────────────────┼────────────────────────────────────────────────────────────┼────────────────────────────────┤
│ BodyModel                            │ wo die Hand ist — gelernte FK, IK-Reach                    │ linear-in-Features, reell      │
│ (+LearnedInverseKinematics)          │                                                            │                                │
├──────────────────────────────────────┼────────────────────────────────────────────────────────────┼────────────────────────────────┤
│ RuntimePolicy                        │ die Choreographie — state(11) → subgoal(4)                 │ MLP (act19 Policy), reell      │
├──────────────────────────────────────┼────────────────────────────────────────────────────────────┼────────────────────────────────┤
│ WorldModel                           │ wie gegriffen wird — Wrist/Grip/Offset per Ensemble-LCB    │ Ensemble, reell                │
├──────────────────────────────────────┼────────────────────────────────────────────────────────────┼────────────────────────────────┤
│ GoalModule2D + LatentGoalServo       │ Platzierziel als Latent, Servo über Latent-Differenz       │ RoPE, komplex                  │
├──────────────────────────────────────┼────────────────────────────────────────────────────────────┼────────────────────────────────┤
│ LatentDynamics                       │ z_{t+1} = z_t + f(z,a), Surprise                           │ komplex                        │
├──────────────────────────────────────┼────────────────────────────────────────────────────────────┼────────────────────────────────┤
│ LatentAttractor                      │ Latent-Planung — gemessen negativ, nicht nutzen            │ komplex                        │
├──────────────────────────────────────┼────────────────────────────────────────────────────────────┼────────────────────────────────┤
│ DistanceNovelty                      │ Curiosity: welches Objekt, welches Traumziel               │ reell                          │
├──────────────────────────────────────┼────────────────────────────────────────────────────────────┼────────────────────────────────┤
│ SelfEval                             │ Selbst-Urteil „geliefert?" ohne Privileg                   │ reell                          │
├──────────────────────────────────────┼────────────────────────────────────────────────────────────┼────────────────────────────────┤
│ ObjectMemory                         │ prädiktives Objekt-Belief für den Blick beim Tragen        │ reell                          │
└──────────────────────────────────────┴────────────────────────────────────────────────────────────┴────────────────────────────────┘

Vorhanden, aber im act23-Lauf nicht verdrahtet: motor.py, planner_chain.py, obstacle.py/obstacle_vision.py, wrist.py, object_orientation.py (nur in Trainingsroutinen). Das ist tote Fläche, die bei Aufräumarbeiten auffallen wird.

# 2. Was noch hart gescripted ist

Drei sehr unterschiedliche Kategorien — die werden oft in einen Topf geworfen:

(a) Teacher als reine Label-Quelle — das ist gewollt. pc_act16.reactive_subgoal() ist die markovsche Regelchoreographie. Bei Choreo:Netz fährt sie nicht; run_combined:485 nimmt policy_fn(state), der Teacher labelt nur die besuchten Zustände für DAgger. Das entspricht Deinem Prinzip.

(b) Echte Laufzeit-Regeln — die widersprechen dem Prinzip noch. Alle default an:
- CLOSE_GUARD — verhindert Schließen, solange das Objekt nicht tief genug ist
- REFLEX — Greifreflex bei Hover-Stall
- WRIST_ALIGN, SOFT_RELEASE, BASE_CLEAR, PHASE_STALL, MAX_REACQ
- die FSM-Phasenmaschine (over/lower/close/lift/carry/place) läuft als Buchhaltung mit und entscheidet Übergänge/Abbrüche

(c) Infrastruktur + Schwellen, die als Wissen wirken:
- Kredit-Routing: lifted > 20mm, world_tol 25mm (U: 22), imit_tol 15mm
- Greifpunkt-Heuristiken: „nächstes Material zum Schwerpunkt", „dichtester Punkt"
- carry_z = max(0.09, 2·obj_h + 0.02), grasp_z = obj_h + 0.006
- der privilegierte Rückfall: schlägt die Perzeption fehl, nimmt perceive() die wahre Position

# 3. Komplexe Zahlen

Der Kern ist komplex: node.py/connection.py/network.py — W ist complex128, Lernen ist konjugat-Hebbisch (Wirtinger, sonst divergiert es), Energien über |ε|², Clipping nach Betrag, mod-Aktivierungen statt tanh (nicht analytisch).

Wo die komplexe Zahl echte Arbeit leistet — und belegt ist:
- ShapeClassifier: F[ring,k] komplex, Rotation = Phasenverschiebung, |F| per Konstruktion rotationsinvariant. Das ist der sauberste Fall — Klassifikation 85,7 % → 100 %.
- RoPE-Goal (planner.py, latent_goal.py): Position lebt in der Phase, Decode über np.angle; Latent-Inverse D komplex, Aktion = np.real(e @ D). Gemessen 18× dichter, ~7× genauer.
- HexFovea: läuft im komplexen PC-Netz.

Wo es reell ist: RuntimePolicy (die Choreographie!), WorldModel, BodyModel/IK, SelfEval, ObjectMemory, ColourOpenSet. Und: der Shape-Kopf hat ein PC-Engine-Backend, aber default ist der MLP (ACT_SHAPE_ENGINE=pc schaltet um).

Wo es sinnvoll sein könnte — ein Kandidat sticht heraus:

▎ Der Wrist. Heute wird der Winkel im Aktionsvektor manuell als [cos2w, sin2w] kodiert (world_model.action_vec), und die Situationsfeatures tragen cos2yaw, sin2yaw. Das ist eine von Hand gebaute Phasenkodierung — genau das, wofür die komplexe Zahl da ist. Ein komplexer Wrist-Kopf würde z = e^{2iw} nativ tragen; die π-Periodizität der Greifer-Symmetrie ist das Quadrieren der Phase, nicht ein Feature-Paar. Auch die Invarianten cos2(w−yaw) wären schlicht z_w · conj(z_yaw).

Schwächere Kandidaten: ObjectMemory (Position + Bewegungsrichtung als Phase). Bei der RuntimePolicy sehe ich wenig Gewinn — deren Zustand ist überwiegend kartesisch; nur der Greifer-/Wrist-Anteil wäre ein Phasenkandidat.

# 4. Was lifelong lernt

Pro Episode im laufenden Betrieb:

┌────────────────────┬───────────────────────────────────────────────────────────────────────────────────┐
│        Was         │                                        wie                                        │
├────────────────────┼───────────────────────────────────────────────────────────────────────────────────┤
│ runtime            │ observe() labelt jeden besuchten Zustand; imitate() bei Selbst-Erfolg; train(200) │
├────────────────────┼───────────────────────────────────────────────────────────────────────────────────┤
│ world              │ observe(feats, action, outcome) + train(600)                                      │
├────────────────────┼───────────────────────────────────────────────────────────────────────────────────┤
│ bm.body            │ alle 3 Schritte observe(q3, hand) — FK aus echter Bewegung (lifelong=True)        │
├────────────────────┼───────────────────────────────────────────────────────────────────────────────────┤
│ vc.fovea           │ step(..., learn=True) pro Frame — das PC-Netz lernt durchgehend                   │
├────────────────────┼───────────────────────────────────────────────────────────────────────────────────┤
│ lat_dyn            │ 1 Übergang/Episode + train(5)                                                     │
├────────────────────┼───────────────────────────────────────────────────────────────────────────────────┤
│ colours, shape_clf │ observe/observe_scene beim Open-Set-Blick → neue Klassen                          │
├────────────────────┼───────────────────────────────────────────────────────────────────────────────────┤
│ seval, dream_nov   │ Statistik bzw. Neuheits-Gedächtnis                                                │
└────────────────────┴───────────────────────────────────────────────────────────────────────────────────┘

Persistiert über Läufe (save_state): bm, shape_clf, world, runtime (24000 DAgger + 12000 Selbst-Imitation), colours, latent_goal, latent_dynamics, dream_seen, self_eval, shape_key. Aktueller Stand: 6518 Selbst-Urteile bei 5889 Übereinstimmungen, 11 Farbklassen, 9 offene Formklassen.

Eine Korrektur an mir selbst: Ich hatte beim Attraktor-Negativ gesagt, die Latent-Dynamik „startet pro Lauf leer". Das stimmt nicht mehr — pack() speichert den Puffer, aktuell 183 Übergänge. Der Kern des Negativbefunds bleibt aber: bei einem Übergang pro Episode ist das für Planung immer noch viel zu dünn.

