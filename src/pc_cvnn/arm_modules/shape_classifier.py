r"""ShapeClassifierModule — LEARNED perception of an object's FORM (cube / L / U), colour-agnostic AND
ROTATION-handled-by-the-complex-representation (the CVNN earns its keep here).

Design:

1. Colour-DECOUPLED: object -> OCCUPANCY mask from the per-pixel SATURATION (max(RGB)-min(RGB)) -- high on
   any coloured object, ~0 on the grey floor -- so hue is thrown away, only the FOOTPRINT (form) remains.

2. ROTATION = PHASE (the rotational analogue of RoPE).  The occupancy is sampled in POLAR rings around its
   centroid and angular-Fourier transformed -> COMPLEX harmonics F[ring,k].  A rotation by alpha shifts each
   harmonic's PHASE by k*alpha, so the MAGNITUDE |F| is ROTATION-INVARIANT by construction; the classifier
   reads |F| and never learns rotations.  The phase carries the orientation (shape_yaw, free).

3. WORKS ON THE ANGLED "overview" CAMERA via a calibrated TABLE-PLANE HOMOGRAPHY: a world rotation is not a
   clean IMAGE rotation under perspective, BUT the table is a plane, so the polar rings are sampled in WORLD
   (table) coordinates -- where rotation IS clean -- and each ring point is projected into the overview image
   by the homography (overview-px <-> world, fit by DLT in calibrate()).  So rotation = phase holds in the
   rectified world frame.  cam="top" instead samples directly in px (a straight-down view needs no rectify).

4. OPEN-SET (self-labelled classes): the trained classes are NOT a closed world.  Novelty gate = kNN
   DISTANCE TO THE TRAINING EXEMPLARS in the standardised |F| space, threshold calibrated LEAVE-ONE-OUT on
   the training set itself.  (Measured: class-prototype / diag-Mahalanobis distances OVERLAP -- the L class
   spreads as wide as a novel T sits far -- while kNN separates cleanly: held-out known max ~6.2 vs novel-T
   min ~7.7, p50 ~9.9, at LOO p99.5 = 6.0.)  A detection beyond the threshold from the training set AND
   every self-labelled class is a NOVEL form (shape=None); observe_scene() collects such sightings and,
   once several CONSISTENT ones agree (temporal consistency -- a persistent object, not a glint), COMMITS a
   new self-labelled class ("neu-1", ...) whose exemplar set keeps growing with every later view.  No truth
   label is ever involved: the agent discovers, names and afterwards selects/tracks/grasps the new form
   through the same pipeline.

Ports
  out : shape_logits (3)   cube / L / U class scores
        shape_id     (1)   argmax class index (0=cube, 1=L, 2=U)
        shape_yaw    (1)   object orientation (rad, mod pi) from the harmonic phase (world frame)
"""
from __future__ import annotations

import os

import numpy as np

from .base import ArmModule
from pc_cvnn.network import PCNetwork
from pc_cvnn.node import PCNode, SensorNode
from pc_cvnn.connection import ConnType

SHAPES = ["cube", "L", "U"]
SHAPE_BODY = {"cube": ("obj_red", np.array([0.012, 0.012, 0.012])), "L": ("obj_L", None), "U": ("obj_U", None)}
NOVEL_MARGIN = float(os.environ.get("ACT_SHAPE_NOVEL_MARGIN", "1.2"))   # novelty gate = LOO-kNN q99.5 * this
NOVEL_CONFIRM = int(os.environ.get("ACT_SHAPE_NOVEL_CONFIRM", "3"))     # consistent sightings before a class is born
NOVEL_K = 3                                                             # kNN order of the novelty distance
OPEN_MARGIN = float(os.environ.get("ACT_SHAPE_OPEN_MARGIN", "1.6"))     # claim radius for open classes, * novel_th
# AUFFRISCHUNG der Exemplarmengen bei OPEN_CAP, s. observe_scene.  Ohne sie friert eine
# Klasse bei 80 Eintraegen fuer immer ein und veraltet gegenueber dem, was die Kamera liefert.
# DICKEN-WACHE am Anspruchstor (2026-09-03).  Die MATERIALDICKE ist ein eigener,
# messtechnisch sauberer Kanal: gemessen ueber je 25 Lagen liegt sie bei Y10 7,07 px
# (Streuung 0,07), Y14 8,25 (0,16), Y20 10,00 (0,05), T14 8,49 (0,21).  Der Fehlerfall
# T14 gegen Y10 ist 1,42 px = das 7-fache der Streuung, der Grenzfall T14 gegen Y14 nur
# 0,24 px.  Eine Schwelle um 0,8 px verwirft den einen und laesst den anderen der FORM.
# WARUM HIER UND NICHT IM DESKRIPTOR: die Form laesst sich NICHT groessenfrei normieren --
# vier Varianten gemessen (feste Ringe / dickenskalierte Ringe / DC-normiert je Ring /
# global fuellungsnormiert), Kennzahl Groessen-Abstand durch Form-Abstand blieb bei
# 2,1-2,5 statt unter 1,0.  Die Groesse ist kein Skalenfaktor, sie ist eingewoben.
# VORGABE AUS seit 2026-09-04.  BEIDE Fassungen gemessen gescheitert:
#   Fassung 1 (hinter resolve, nur annullierend): Kandidat 1 Treffer in 8 Blicken, kein Knopf.
#   Fassung 2 (in der Kandidatenschleife): 567 Ansprueche verworfen, aber der Kandidat bekam
#     NULL Treffer statt 2 im Kontrollarm -- schlechter, nicht besser.  Lieferquote 48,0 -> 44,5%.
# Der Engpass liegt NICHT im Anspruchswettbewerb: mit UND ohne Wache holt der Kandidat 0-2
# Treffer in 12 Blicken.  Eine junge Klasse, aus 3 Sichtungen EINER Lage geboren, erkennt ihr
# Objekt in anderen Lagen schlicht nicht wieder -- das ist eine Repraesentations-, keine
# Wettbewerbsgrenze.  Die Dicke selbst bleibt ein sauberer Kanal (Y10/Y14/Y20 trennen mit dem
# 6- bis 40-fachen ihrer Streuung); nur ihre Verwendung am Anspruchstor traegt nicht.
DICKE_WACHE = os.environ.get("ACT_SHAPE_DICKE_WACHE", "0") != "0"
DICKE_TOL = float(os.environ.get("ACT_SHAPE_DICKE_TOL", "0.8"))     # px
DICKE_MIN_N = int(os.environ.get("ACT_SHAPE_DICKE_MIN_N", "8"))     # vorher faellt sie AUS
DICKE_CAP = 40
DICKE_LOG = os.environ.get("ACT_SHAPE_DICKE_LOG", "0") != "0"   # Vetos mitschreiben
# VORGABE AUS seit 2026-09-03: im Dicken-Wachen-A/B entstanden in BEIDEN Armen 0 Klassen,
# waehrend derselbe Aufbau (10-mm-Y, Seed 11, gleicher Zustand) VOR dieser Auffrischung
# 4 Geburten hatte.  Die Auffrischung ist die einzige Aenderung, die im Kontrollarm wirkt --
# der Verdacht, dass sie Geburten unterdrueckt (aufgefrischte Klassen beanspruchen besser
# und schlucken Neuheits-Belege), ist damit begruendet, aber NICHT isoliert gemessen.
# Bis das geklaert ist, gilt der alte Zustand.  Sie war ohnehin ohne Nutzennachweis an.
EX_REFRESH = os.environ.get("ACT_SHAPE_EX_REFRESH", "0") != "0"
EX_DUP_TH = float(os.environ.get("ACT_SHAPE_EX_DUP_TH", "0.01"))   # Abstand, ab dem zwei
#   Exemplare als verschieden gelten (gemessen: Duplikate liegen bei exakt 0.00)
#   (measured: the same novel form seen at DIFFERENT poses sits p50 ~8.3 / p90 ~11.2 apart while novel_th
#   is ~7.3 -- a sparse young exemplar set needs the relaxed radius or later poses would read novel again)
MERGE_MARGIN = 1.7                                                      # birth-time merge radius, * novel_th
#   (must sit BETWEEN same-form cross-pose spread (p90 ~11.2 -> merge pose-miss re-births) and the
#   DISTANCE BETWEEN TWO DIFFERENT novel forms (long-I vs T measured p10 ~12.6: 2.0*th=14.6 FUSED them
#   in the user's GUI session -> the T never got its own class); 1.7*th ~ 12.4 splits both measured sets)
NOVEL_CLUSTER = os.environ.get("ACT_SHAPE_NOVEL_CLUSTER", "1") != "0"   # Neuheits-Puffer als CLUSTER
#   statt als FIFO.  GEMESSEN 2026-08-14, zwei A/B-Laeufe ueber den Geburts-Radius lieferten BITGLEICHE
#   Arme -- der Radius war nie die bindende Bedingung.  Der Grund lag im Puffer: er hielt die LETZTEN 12
#   Sichtungen rein nach AKTUALITAET, ueber alle Objekte und Blicke hinweg.  In einem echten Lauf mischen
#   sich dort verformte Ansichten, verschmolzene Blobs und Randartefakte, also liegen drei SAUBERE
#   Sichtungen desselben neuen Objekts selten gleichzeitig darin.  Dass die Form selbst eng genug
#   clustert, ist gemessen: die neue Form 22x20 hat paarweisen Median 6.45 -- ENGER als der heutige
#   Radius 7.72, 76 von 165 Tripeln liegen darunter.  Waeren drei ihrer Sichtungen gleichzeitig im
#   Puffer, entstuende die Klasse schon mit den alten Werten.
#   Der Cluster-Puffer gruppiert nach UEBEREINSTIMMUNG und laesst eine Gruppe reifen; sie stirbt durch
#   ALTERN (kein neuer Beleg), nicht durch Verdraengung.  Das sollte zugleich die Phantome daempfen:
#   bisher entstand eine Klasse, wenn drei ZUFAELLIG benachbarte Fremdsichtungen zusammentrafen -- 5 von
#   8 Klassen im Zustand werden nie wieder geclaimt.  ACT_SHAPE_NOVEL_CLUSTER=0 stellt das FIFO her.
NOVEL_GROUP_AGE = int(os.environ.get("ACT_SHAPE_NOVEL_GROUP_AGE", "12"))   # Blicke ohne neuen Beleg
NOVEL_GROUP_MAX = int(os.environ.get("ACT_SHAPE_NOVEL_GROUP_MAX", "16"))   # Deckel fuer die Gruppenzahl
BIRTH_MARGIN = float(os.environ.get("ACT_SHAPE_BIRTH_MARGIN", "1.0"))   # GEBURTS-Radius, * novel_th.
#   WARUM ES DEN KNOPF GIBT (gemessen 2026-08-14, offline am gespeicherten Zustand): novel_th ist
#   LEAVE-ONE-OUT auf dem Trainingssatz kalibriert und beantwortet "gehoert das zu einer TRAINIERTEN
#   Klasse".  Fuer die ANDERE Frage "gehoeren diese zwei Sichtungen ZUSAMMEN" wurde es nie kalibriert.
#   Gemessen (je 10 Sichtungen obj_L/U/T/blue, alle Paarungen):
#       Pose-Streuung INNERHALB eines Objekts   Median  9.25
#       Abstand ZWISCHEN verschiedenen Objekten Median 14.58   Ueberlappung 0%
#   novel_th = 7.72 liegt also UNTER der eigenen Streuung -- drei Sichtungen desselben neuen Objekts
#   clustern nur zufaellig eng genug.  Ueber alle Tripel aus 14 Sichtungen eines neu proportionierten
#   Koerpers:  Radius 7.72 -> 2% der Tripel, 10.03 (x1.3) -> 23%, 12.34 (x1.6) -> 74%, 14.66 -> 97%;
#   Fremdpaare unter dem Radius entsprechend 0% / 4% / 28% / 74%.
#   Die CLAIM-Seite hat dieselbe Sache laengst gemerkt und rechnet mit OPEN_MARGIN (s. dort, und der
#   Kommentar oben: "p50 ~8.3 / p90 ~11.2 apart while novel_th is ~7.3") -- nur der Geburts-Pfad
#   benutzte weiter den rohen Wert.
#   SEIT 2026-08-16 IST DAS KEIN HANDGRIFF MEHR: der Radius wird in _fit_birth() vom Netz SELBST an
#   seinen eigenen Sichtungen gemessen (s. dort).  BIRTH_MARGIN multipliziert nur noch den gemessenen
#   Wert und dient dem A/B -- VORGABE 1.0 = rein selbst kalibriert, nichts eingestellt.
MERGE_GUARD = os.environ.get("ACT_SHAPE_MERGE_GUARD", "1") == "1"       # Verschmelzungs-Sperre, s. _merge_th
OPEN_CAP = 80                                                           # max stored exemplars per self-labelled class
# STARVATION / CAP (phantom over-birth control): scattered transient sightings (edge/occlusion/odd-pose
# renders) can birth open classes that then NEVER get claimed again -- the user's neu-* piled to 45+.  A
# class that goes STARVE_N glances without a fresh claim AND stays SMALL (<= STARVE_MIN_EX exemplars,
# i.e. was never reinforced by real repeated sightings) is a phantom and is pruned; a real object's
# class keeps getting claimed (age resets) and accumulates exemplars, so it survives.  Bound-command
# classes are additionally PROTECTED (passed in).  A hard CAP bounds the total (prune the most-starved).
# RELATIVE RINGE (ACT_SHAPE_RELRINGS=1, Vorgabe AUS).  Die Ringe von _harmonics_at liegen an
# FESTEN Weltradien (RW = 4..46 mm); Ring i misst bei einem doppelt so grossen Objekt eine voellig
# andere Stelle der Form -- das ist die gemessene Ursache dafuer, dass der Deskriptor jenseits des
# 1,3-fachen bekannten Masses alles als "neuartig" liest (wiki/befunde/form-rueckhalt.md).
# MIT dem Schalter haengen die Ringe an der EIGENAUSDEHNUNG des Objekts (95.-Perzentil des
# Abstands vom Schwerpunkt), Ring i sitzt also immer bei derselben RELATIVEN Position.
# Am Pruefstand halbiert das die Kennzahl "Groessen-Abstand / Form-Abstand" von 3,68 auf 2,08
# (wiki/befunde/groessen-invarianz-fuenfter-anlauf.md) -- vier fruehere Normierungen bewegten dort
# nichts.  ACHTUNG: ein damit gerechneter Deskriptor ist mit gespeicherten Exemplaren NICHT
# vergleichbar; wer umschaltet, muss train() neu fahren und das Open-Set neu aufbauen.
RELRINGS = os.environ.get("ACT_SHAPE_RELRINGS", "0") == "1"
# SECHSTER ANLAUF (ACT_SHAPE_RELRINGS=2): KLASSIFIKATION UND LOKALISIERUNG TRENNEN.
# Fassung 1 (RELRINGS=1) rechnete ALLES auf relativen Ringen und ist im Lauf gescheitert
# (wiki/befunde/relrings-im-lauf.md): die Klassifikation gewann (uebergrosse Formen 18 -> 69 %),
# aber die Lokalisierung verlor mehr -- grobe Adressierungsfehler 2,1 -> 9,8 % (p = 0,0001),
# privilegierter Rueckfall 25 -> 52.  Ursache: am selben F haengt auch die AUSRICHTUNG
# (_yaw_from / _yaw4_from), und relative Ringe verschieben deren Abtastung mit der Objektgroesse.
# WICHTIG: der GREIFPUNKT haengt NICHT an F -- er kommt direkt aus der Maske
# (naechstes Material zum Schwerpunkt / Distanztransformation).  Zu trennen ist also nur der Yaw.
# RELRINGS=2 rechnet deshalb ZWEI Harmonische je Detektion:
#     relative Ringe  -> desc  -> resolve/classify        (die Groessen-Invarianz)
#     feste Ringe     -> yaw   -> Ausrichtung             (die alte, gemessen gute Lage)
# Kostet einen zweiten FFT-Durchlauf je Detektion; gemessen ist perceive_all nicht der teure Teil.
RELRINGS_SPLIT = os.environ.get("ACT_SHAPE_RELRINGS", "0") == "2"
RELR_LO = float(os.environ.get("ACT_SHAPE_RELR_LO", "0.15"))   # innerster Ring, Bruchteil der Ausdehnung
RELR_HI = float(os.environ.get("ACT_SHAPE_RELR_HI", "1.35"))   # aeusserster Ring

STARVE_N = int(os.environ.get("ACT_OPEN_STARVE", "25"))
# FARBFREIER SPLIT verschmolzener Blobs, s. perceive_all.  ACT_SHAPE_SPLIT=0 stellt den alten
# Zustand her (nur der farbbasierte Form-Split, der ohne Farbklasse nicht laufen kann).
SPLIT_FUSED = os.environ.get("ACT_SHAPE_SPLIT", "1") != "0"
SPLIT_ERODE_MAX = int(os.environ.get("ACT_SHAPE_SPLIT_ERODE", "10"))
SPLIT_ALWAYS = os.environ.get("ACT_SHAPE_SPLIT_ALWAYS", "0") != "0"
STARVE_MIN_EX = int(os.environ.get("ACT_OPEN_STARVE_EX", "6"))
# DIE GROESSEN-AUSNAHME FAELLT BEI HOHEM ALTER.  Sie schuetzt junge, ECHTE Klassen davor, wegen einer
# Durststrecke geloescht zu werden -- ab einem gewissen Alter schuetzt sie aber nur noch Leichen.
# GEMESSEN am Zustand des Nutzers (2026-08-22, nach 275 Episoden):
#     lebende Klassen (werden beansprucht)   neu-9 Alter 8, neu-34 Alter 7, neu-285 Alter 8
#     immun durch Groesse, aber tot          neu-250 Alter 120 (55 Belege), neu-254 Alter 388 (25),
#                                            neu-266 Alter 998 (7), neu-256 Alter 1288 (9)
# neu-256 wurde also 1288 Blicke lang kein einziges Mal wiedererkannt und war trotzdem unantastbar,
# weil 9 > STARVE_MIN_EX.  Die Luecke zwischen lebend (7-8) und tot (>=120) ist riesig.
# WARUM 10x STARVE_N und nicht knapper: ein echtes Objekt steht bei ACT23_SCENE_N < Objektzahl zeitweise
# NICHT auf dem Tisch und sammelt dann voellig zu Recht Alter -- ueber die Szenen-Rotation sind das
# Dutzende Blicke.  250 liegt weit darueber und weit unter den gemessenen Leichen.
STARVE_OLD = int(os.environ.get("ACT_OPEN_STARVE_OLD", "10"))          # * STARVE_N; 0 = Ausnahme bleibt
MAX_OPEN = int(os.environ.get("ACT_OPEN_MAX", "12"))
SAT_TH = 0.15
GRIP_PX = 18                                             # gripper-sized window (px) for the densest-grip-point search
RED = np.array([0.9, 0.1, 0.1])
_MARKERS = ("target_marker", "target_sel_1", "target_sel_2", "target_sel_3")


def _softmax(z):
    z = z - z.max(-1, keepdims=True); e = np.exp(z); return e / e.sum(-1, keepdims=True)


class PCShapeHead:
    """Supervised shape classifier IN the complex PC engine (pc_cvnn PCNetwork): a SensorNode for the
    feature, a hidden PCNode and a class PCNode, wired generatively (class -> hidden -> feature) with
    COMPLEX weights and PC learning.  Reads the rotation-INVARIANT |F| descriptor: the complex harmonics F
    themselves are rotation-DEPENDENT (phase = rotation), so a flat net can't classify them invariantly
    (measured: ~chance on F vs 100% on |F|) -- the magnitude IS the invariant feature.  Trains supervised
    (clamp feature + one-hot class, relax, learn); infers the class by relaxing it free under the feature."""

    def __init__(self, din, n_cls=3, hid=24, rng=None):
        rng = rng or np.random.default_rng(0)
        net = PCNetwork(eta_inf=0.1, n_relax=40, eps_tol=1e-6, eta_learn=0.03, gamma=0.5, w_clip=3.0, rng=rng)
        self.x = net.add(SensorNode("sh_x", din))
        self.z = net.add(PCNode("sh_z", hid, activation="tanh", eta_temporal=0.0, rng=rng))
        self.y = net.add(PCNode("sh_y", n_cls, activation="identity", eta_temporal=0.0, rng=rng))
        net.connect("sh_z", "sh_x", ConnType.UP); net.connect("sh_y", "sh_z", ConnType.UP)
        self.net = net; self.n_cls = n_cls

    def fit(self, X, Y, epochs=8, rng=None):
        rng = rng or np.random.default_rng(0)
        for _ in range(epochs):
            for i in rng.permutation(len(X)):
                self.x.set_input(X[i])
                oh = np.zeros(self.n_cls); oh[int(Y[i])] = 1.0
                self.y.clamp(oh.astype(np.complex128)); self.net.step(learn=True)
            self.y.unclamp()

    def logits(self, feat):
        self.y.unclamp(); self.x.set_input(feat); self.net.step(learn=False)
        return np.real(self.y.mu).copy()


class ShapeClassifierModule(ArmModule):
    def __init__(self, n_ang=72, n_harm=8, hid=32, cam="overview", name="ShapeClassifier", rng=None, engine=None):
        super().__init__(name)
        self.NA = int(n_ang); self.NH = int(n_harm); self.cam = cam
        self.RW = np.arange(0.004, 0.046, 0.004)             # WORLD polar ring radii (m); reach ~44mm to cover
        self.RPX = np.arange(2, 26, 2)                       # px ring radii, used on the top cam
        self.rng = rng or np.random.default_rng(0)
        self.H = None; self.Hinv = None                      # table-plane homography world<->overview-px
        nr = len(self.RW)
        din = nr * self.NH
        # classifier backend: "mlp" (default, numpy) or "pc" (the complex PC engine, ACT_SHAPE_ENGINE=pc).
        # Both read the rotation-invariant |F|; the PC head reaches the same 100% (parity), in the PC paradigm.
        self.engine = (engine or os.environ.get("ACT_SHAPE_ENGINE", "mlp")).lower()
        self.W1 = self.rng.normal(0, 1 / np.sqrt(din), (hid, din)); self.b1 = np.zeros(hid)
        self.W2 = self.rng.normal(0, 1 / np.sqrt(hid), (len(SHAPES), hid)); self.b2 = np.zeros(len(SHAPES))
        self.head = PCShapeHead(din, len(SHAPES), rng=self.rng) if self.engine == "pc" else None
        self.fmu = np.zeros(din); self.fsd = np.ones(din)
        # OPEN-SET state: training exemplars in the standardised |F| space + the LOO-calibrated kNN
        # novelty threshold (both from train()); self-labelled classes + unclaimed novel sightings.
        self._ZX = None                                      # trained-class exemplars (z space, novelty gate)
        self.novel_th = None                                 # kNN z-distance beyond which a view is NOVEL
        self.area_hi = None                                  # blob-area sanity cap (merged-blob guard)
        self.open = {}                                       # self-labelled class name -> [z exemplars]
        self.open_names = []                                 # their names in creation order (ids after SHAPES)
        self._novel_buf = []                                 # novel z's awaiting temporal consistency
        self.last_events = []                                # last observe_scene glance trail (debugging)
        self._last = None
        self.add_in("shape_cmd", len(SHAPES), "one-hot shape command (cube/L/U) to select by FORM")
        self.add_out("shape_logits", len(SHAPES), "cube / L / U class scores")
        self.add_out("shape_id", 1, "argmax shape class index (0=cube,1=L,2=U)")
        self.add_out("shape_yaw", 1, "object orientation (rad, mod pi) from the harmonic phase")
        self.add_out("selected_xy", 2, "world xy of the object whose FORM matches shape_cmd")

    # ------------------------------------------------------------------
    # rendering / housekeeping
    # ------------------------------------------------------------------
    @staticmethod
    def _park_markers(sim):
        import mujoco
        moved = False
        for nm in _MARKERS:                                  # magenta markers corrupt the saturation mask
            try:
                bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, nm)
                sim.d.mocap_pos[sim.m.body_mocapid[bid]] = [0.4, -0.6, -0.05]; moved = True
            except Exception:
                pass
        if moved:
            mujoco.mj_forward(sim.m, sim.d)                  # CRITICAL: refresh xpos, else the markers still
            #   RENDER at their old spots (mocap_pos alone doesn't update the rendered pose) -> their magenta
            #   disks survive in the mask and classify as "cube", hijacking select('cube').

    def _render_u8(self, sim):
        import mujoco
        opt = mujoco.MjvOption(); opt.geomgroup[1] = 0       # hide the arm -> clean footprint
        sim._renderer.update_scene(sim.d, camera=self.cam, scene_option=opt)
        img = sim._renderer.render()                         # uint8
        self._last_w = int(img.shape[1])                     # aktuelle Bildbreite fuer px_scale()
        return img

    # ------------------------------------------------------------------
    # table-plane homography (overview px <-> world), fit by DLT
    # ------------------------------------------------------------------
    def _world_to_px(self, W):
        Wh = np.column_stack([np.atleast_2d(W), np.ones(len(np.atleast_2d(W)))])
        q = Wh @ self.H.T
        return q[:, :2] / q[:, 2:3]

    def _px_to_world(self, P):
        Ph = np.column_stack([np.atleast_2d(P).astype(float), np.ones(len(np.atleast_2d(P)))])
        q = Ph @ self.Hinv.T
        return q[:, :2] / q[:, 2:3]

    def calibrate(self, sim, n=40, rng=None):
        """Fit the overview-px <-> world table-plane homography (DLT), like setup_following_fovea: place a
        red marker object at known world spots, detect its px, solve the 8-DOF homography."""
        import mujoco
        from pc_cvnn.pc_act15 import detect_px
        from pc_cvnn.pc_act14 import _rand_xy
        rng = rng or np.random.default_rng(3)
        sim.reset_home(); self._park_markers(sim)
        for o in ("obj_green", "obj_blue", "obj_L", "obj_U"):
            sim.set_object(o, [0.5, -0.6], z=0.008)
        W, P = [], []
        for _ in range(n):
            p = _rand_xy(rng); sim.set_object("obj_red", p, z=0.012); mujoco.mj_forward(sim.m, sim.d)
            px = detect_px(self._render_u8(sim), RED)
            if px is not None:
                W.append([p[0], p[1]]); P.append([px[0], px[1]])
        Mh = []
        for (x, y), (u, v) in zip(W, P):
            Mh.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
            Mh.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
        self.H = np.linalg.svd(np.array(Mh))[2][-1].reshape(3, 3); self.Hinv = np.linalg.inv(self.H)
        self._cal_w = int(self._render_u8(sim).shape[1])       # Bildbreite, FUER DIE H gilt (s. needs_recal)
        return len(W)

    # Referenz-Bildbreite, auf die alle PIXEL-Schwellen dieser Klasse geeicht sind.
    PX_REF = 240.0

    def px_scale(self, img=None):
        """Skalierung der Pixel-Schwellen fuer die AKTUELLE Bildbreite (1.0 bei 240px).

        Laengen skalieren mit s, FLAECHEN mit s^2.  Ohne das laesst z.B. min_area=40 bei doppelter
        Aufloesung Blobs durch, die in Weltmassen nur ein VIERTEL so gross sind -- Glanzlichter und
        Splitter wuerden als Objekte gelten."""
        w = float(getattr(self, "_last_w", 0) or (img.shape[1] if img is not None else self.PX_REF))
        return w / self.PX_REF

    def needs_recal(self, sim):
        """Wurde H fuer eine ANDERE Bildbreite gefittet?  Dann ist sie unbrauchbar.

        DIE STILLE FALLE (2026-08-02): H wird im Zustand MITGESPEICHERT, und die Kalibrierung lief
        nur `if self.H is None` -- bei geaenderter Aufloesung waere die alte H weiterbenutzt worden
        und JEDE wahrgenommene Position um den Aufloesungsfaktor daneben gelegen.  Kein Absturz,
        keine Warnung, nur systematisch falsche Griffe."""
        if self.H is None:
            return True
        cal = int(getattr(self, "_cal_w", 0) or 0)
        return cal != int(self._render_u8(sim).shape[1])

    # ------------------------------------------------------------------
    # colour-agnostic occupancy + COMPLEX angular-harmonic descriptor
    # ------------------------------------------------------------------
    def _mask(self, img_u8):
        """uint8 HxWx3 -> hue-agnostic saturation occupancy mask (1 on any coloured object, 0 on floor)."""
        f = img_u8.astype(np.float32) / 255.0
        return ((f.max(2) - f.min(2)) > SAT_TH).astype(np.float32)

    def _centroid(self, mask):
        """Centre of `mask`: a WORLD centroid (overview, perspective-correct via H) or a PX centroid (top)."""
        ys, xs = np.nonzero(mask)
        if self.H is not None:
            return self._px_to_world(np.column_stack([xs, ys])).mean(0)
        return np.array([xs.mean(), ys.mean()])

    def _harmonics_at(self, mask, ctr, relativ=None):
        """Complex angular harmonics F[ring,k] of `mask`, sampled on polar rings around `ctr`.  Overview:
        rings in WORLD metres around the world centroid, projected to px by H (rotation is clean there).
        Top: rings in px around the px centroid.  Sampling ONLY this `mask` ignores neighbouring objects."""
        H, Wd = mask.shape
        th = np.arange(self.NA) / self.NA * 2 * np.pi
        ring = np.column_stack([np.cos(th), np.sin(th)])
        if self.H is not None:
            radien = self.RW
            _rel = (RELRINGS or RELRINGS_SPLIT) if relativ is None else relativ
            if _rel:                                         # s. RELRINGS oben: Ringe an der
                ys, xs = np.nonzero(mask > 0)                #   EIGENAUSDEHNUNG statt an festen
                if len(xs) >= 8:                             #   Weltradien
                    Wp = self._px_to_world(np.column_stack([xs, ys]))
                    dd = np.linalg.norm(Wp - np.asarray(ctr, float), axis=1)
                    R = float(np.percentile(dd, 95))
                    if np.isfinite(R) and R > 1e-6:
                        radien = np.linspace(RELR_LO, RELR_HI, len(self.RW)) * R
            F = np.empty((len(radien), self.NH), complex)
            for i, r in enumerate(radien):
                rp = self._world_to_px(ctr + r * ring)
                py = np.clip(rp[:, 1].astype(int), 0, H - 1); px = np.clip(rp[:, 0].astype(int), 0, Wd - 1)
                F[i] = np.fft.fft(mask[py, px])[:self.NH]
            return F
        F = np.empty((len(self.RPX), self.NH), complex)
        for i, r in enumerate(self.RPX):
            py = np.clip((ctr[1] + r * np.sin(th)).astype(int), 0, H - 1)
            px = np.clip((ctr[0] + r * np.cos(th)).astype(int), 0, Wd - 1)
            F[i] = np.fft.fft(mask[py, px])[:self.NH]
        return F

    def _harmonics(self, img_u8):
        """Single-object: harmonics of the whole occupancy mask (assumes one object in view)."""
        mask = self._mask(img_u8)
        return None if mask.sum() < 6 else self._harmonics_at(mask, self._centroid(mask))

    def yaw_at(self, sim, world_xy, mu=None, th=0.12, win_px=36, engine="cells"):
        """FOVEA-path orientation read (user's orientation-through-the-fovea goal): angular harmonics
        on a LOCAL window around `world_xy` (the gaze / tracked object), pixels optionally IDENTITY-
        gated by a self-labelled colour-class centroid `mu` (chromaticity distance < th, the colour
        open-set metric) so neighbours inside the window drop out.  This is what the fovea SEES at a
        lock -- local + identity-conditioned -- vs the overview path's global CC segmentation.
        Returns (yaw2, yaw4, n_px) or None if too little material in view.
        engine="cells" (default): yaw2 comes from the FOVEA'S OWN HEX CELLS (pc_act18.fovea_cell_yaw,
        identity-gated cell saliency + weighted PCA over cell world positions) -- measured equal to
        the raw-pixel PCA (U p90 even better: pooling denoises); falls back to the pixel PCA when
        the cell read has too little material.  engine="px" forces the raw-pixel path."""
        self._park_markers(sim)
        img = self._render_u8(sim)
        mask = self._mask(img).astype(float)
        try:
            px = np.asarray(self._world_to_px(np.asarray(world_xy, float))[0], float)
        except Exception:
            return None
        yaw_cells = None
        if engine == "cells" and mu is not None and self.H is not None:
            from pc_cvnn.pc_act18 import fovea_cell_yaw
            yaw_cells = fovea_cell_yaw(img, px, np.asarray(mu, float), self._px_to_world)
        Hh, Ww = mask.shape
        x0, x1 = max(0, int(px[0]) - win_px), min(Ww, int(px[0]) + win_px)
        y0, y1 = max(0, int(px[1]) - win_px), min(Hh, int(px[1]) + win_px)
        local = np.zeros_like(mask)
        local[y0:y1, x0:x1] = mask[y0:y1, x0:x1]
        if mu is not None:                                   # identity gate: keep MY material only
            rgb = img.astype(float)
            chroma = rgb / (rgb.sum(axis=2, keepdims=True) + 1e-6)
            local *= (np.linalg.norm(chroma - np.asarray(mu, float), axis=2) < th)
        if local.sum() < 6:
            return None
        ctr = self._centroid(local)
        F = self._harmonics_at(local, ctr)
        # PCA long axis of the local material in WORLD coords -- measured FAR more consistent than
        # the k=2 ring phase for elongated shapes (the act "STEP C" perceive_long_axis lesson).
        ys, xs = np.nonzero(local > 0)
        Wp = (self._px_to_world(np.column_stack([xs, ys])) if self.H is not None
              else np.column_stack([xs, ys]).astype(float))
        Wc = Wp - Wp.mean(0)
        _, _, Vt = np.linalg.svd(Wc, full_matrices=False)
        yaw_pca = float(np.arctan2(Vt[0, 1], Vt[0, 0])) % np.pi
        return (yaw_cells if yaw_cells is not None else yaw_pca), self._yaw4_from(F), float(local.sum())

    def descriptor(self, img_u8):
        F = self._harmonics(img_u8)
        return None if F is None else np.abs(F).ravel()

    @staticmethod
    def _yaw_from(F):
        return 0.5 * float(np.angle(F[:, 2]).mean())         # long axis = k=2 (undirected), yaw mod pi

    @staticmethod
    def _yaw4_from(F):
        """Orientation from the k=4 harmonic -- a SQUARE's symmetry: a rotation by alpha shifts the k=4
        phase by 4*alpha, so angle(F4)/4 reads a cube's yaw mod pi/2, where k=2 is DEGENERATE (a square
        has no long axis).  Complex SUM over the rings (wrap-safe; a rotation shifts every ring's phase
        equally).  The absolute zero is shape-dependent -- fine for a LEARNER, which needs a CONSISTENT
        orientation signal, not a calibrated one."""
        return 0.25 * float(np.angle(F[:, 4].sum()))

    # ------------------------------------------------------------------
    def _forward(self, X):
        Xn = (X - self.fmu) / self.fsd
        h = np.maximum(0.0, Xn @ self.W1.T + self.b1)
        return h @ self.W2.T + self.b2, h

    def classify(self, feat):
        if self.engine == "pc":                              # complex PC-engine head on the standardised |F|
            return self.head.logits((np.asarray(feat, float) - self.fmu) / self.fsd)
        return self._forward(np.atleast_2d(feat))[0][0]

    def train(self, sim, steps=4500, lr=0.05, bs=64, epochs=10, rng=None, viz_fn=None, viz_every=40):
        """Self-supervised: render each shape at random pos + yaw (others parked), take the rotation-
        INVARIANT complex descriptor, label by truth, fit the classifier.  Returns train accuracy.
        Calibrates the homography first if cam is the angled overview and not yet calibrated.
        viz_fn(i, steps): optional callback every viz_every steps (e.g. to show the training live)."""
        import mujoco
        rng = rng or self.rng
        if self.cam != "top" and self.needs_recal(sim):     # auch bei GEAENDERTER Bildbreite
            self.calibrate(sim, rng=np.random.default_rng(3))
        sim.reset_home(); self._park_markers(sim)
        allb = ["obj_red", "obj_green", "obj_blue", "obj_L", "obj_U"]
        X, Y, areas = [], [], []
        for i in range(steps):
            k = int(rng.integers(len(SHAPES))); body, half = SHAPE_BODY[SHAPES[k]]
            for o in allb:
                sim.set_object(o, [0.5, -0.6], z=0.008)
            bid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_BODY, body)
            if half is not None:
                sim.m.geom_size[sim.m.body_geomadr[bid]] = half
            zc = float(sim.m.geom_size[sim.m.body_geomadr[bid]][2])   # rest z = the object's half-height
            from pc_cvnn.pc_act14 import REACH_XY                     # train over the CURRENT workspace
            sim.set_object(body, [rng.uniform(REACH_XY[0][0] + 0.03, REACH_XY[1][0] - 0.03),
                                  rng.uniform(REACH_XY[0][1] + 0.01, REACH_XY[1][1] - 0.01)], z=zc,
                           yaw=rng.uniform(0, 2 * np.pi)); mujoco.mj_forward(sim.m, sim.d)
            if viz_fn is not None and i % viz_every == 0:        # show the form-training live (every N steps)
                viz_fn(i, steps, SHAPES[k])
            img = self._render_u8(sim)
            d = self.descriptor(img)
            if d is not None:
                X.append(d); Y.append(k); areas.append(float(self._mask(img).sum()))
        X = np.array(X); Y = np.array(Y); n = len(X)
        self.fmu = X.mean(0); self.fsd = X.std(0) + 1e-9
        self._X, self._Y = X, Y
        self.area_hi = float(np.quantile(areas, 0.995)) * 1.5   # merged-blob guard (see observe_scene)
        self._fit_novelty()                                  # open-set gate: exemplars + LOO kNN threshold
        if self.engine == "pc":                              # fit the complex PC head on standardised |F|
            self.head.fit((X - self.fmu) / self.fsd, Y, epochs=min(epochs, 8), rng=rng)
            chk = rng.choice(n, min(n, 300), replace=False)  # train acc on a subset (PC infer is per-sample)
            return float(np.mean([self.classify(X[i]).argmax() == Y[i] for i in chk]))
        for _ in range(epochs):
            idx = rng.permutation(n)
            for s in range(0, n, bs):
                b = idx[s:s + bs]; xb = X[b]; yb = Y[b]
                logits, h = self._forward(xb)
                p = _softmax(logits); p[np.arange(len(b)), yb] -= 1.0; p /= len(b)
                self.W2 -= lr * (p.T @ h); self.b2 -= lr * p.sum(0)
                dh = (p @ self.W2) * (h > 0)
                self.W1 -= lr * (dh.T @ ((xb - self.fmu) / self.fsd)); self.b1 -= lr * dh.sum(0)
        return float((self._forward(X)[0].argmax(1) == Y).mean())

    # ------------------------------------------------------------------
    # OPEN-SET layer: prototypes, novelty gate, self-labelled classes
    # ------------------------------------------------------------------
    def _z(self, desc):
        return (np.asarray(desc, float) - self.fmu) / self.fsd

    @staticmethod
    def _knn(z, Z, k=NOVEL_K):
        """Distance from z to its k-th nearest exemplar in Z (fewer exemplars -> the farthest available)."""
        d = np.sqrt(((np.asarray(Z) - z) ** 2).sum(1))
        return float(np.sort(d)[min(k, len(d)) - 1])

    def _fit_novelty(self):
        """Calibrate the open-set NOVELTY gate from the training views: keep them as EXEMPLARS (z space)
        and set the threshold LEAVE-ONE-OUT -- the kNN distance every training view has to the REST of the
        set, generous quantile * margin.  (Prototype / Mahalanobis distances measured NON-separating here:
        the L class alone spreads as far as a novel form sits away; kNN keeps the local manifold tight.)"""
        Z = (self._X - self.fmu) / self.fsd
        self._ZX = Z
        G = Z @ Z.T                                          # pairwise sq-distances via the Gram matrix
        sq = np.maximum(np.diag(G)[:, None] + np.diag(G)[None, :] - 2 * G, 0.0)
        loo = np.sqrt(np.sort(sq, axis=1)[:, NOVEL_K])       # k-th neighbour EXCLUDING self (index 0)
        self.novel_th = float(np.quantile(loo, 0.995)) * NOVEL_MARGIN
        self._fit_birth()

    def _fit_birth(self, cap=1200):
        """GEBURTSRADIUS -- vom Netz SELBST an den eigenen Sichtungen gemessen, nicht eingestellt.

        WARUM eine EIGENE Groesse (gemessen 2026-08-16, act23_split_probe, Objekt allein auf dem
        Tisch, 3x3 Positionen x 6 Drehungen): novel_th ist leave-one-out gegen den DICHTEN
        Trainingssatz kalibriert und misst "Abstand zu einem Mannigfaltigen aus 2500 Belegen"
        (Median 3.7 bei obj_L).  Der Geburtspfad benutzt ihn aber als "Abstand zwischen zwei
        EINZELNEN Sichtungen desselben Dings" -- und der liegt gemessen bei 9-11:
            Eigenstreuung p50   obj_X 9.00   obj_T 10.28   obj_L 10.30   (novel_th 7.72)
            davon Drehung        4.93         7.23          8.93         <- Rotation ist unschuldig
            davon Ort            9.45        10.35          9.68         <- die Perspektive treibt es
        65-86% der Paare ueberschreiten novel_th -- bei der TRAINIERTEN Form obj_L genauso wie beim
        neuen Kreuz.  obj_L zersplittert trotzdem nie, weil ihr dichter Belegsatz jede Sichtung
        auffaengt; eine junge Klasse mit drei Belegen kann das nicht und erfindet sich neu (das
        Kreuz gebar DREI Klassen).  Der Fehler war, beide Fragen mit derselben Zahl zu messen.

        SELBST GEMESSEN statt gedreht: der Klassifikator besitzt seine eigenen Sichtungen samt
        Zugehoerigkeit (_X/_Y).  Daraus die beiden Verteilungen, die den Radius definieren -- Paare
        DERSELBEN Form gegen Paare VERSCHIEDENER Formen -- und als Radius die Stelle, die sie am
        besten trennt (Youden J = Anteil-innen-drin minus Anteil-fremd-drin, maximiert).  Kein
        Zielwert, keine Handeinstellung, kein privilegiertes Wissen: verschiebt sich die Kamera oder
        kommen Formen dazu, verschiebt sich der Radius beim naechsten train() mit.  Genau dieselbe
        Rechnung wie novel_th -- nur an der Groesse, um die es hier wirklich geht.
        """
        Z, y = self._ZX, np.asarray(self._Y)
        if len(Z) > cap:                                     # Paarzahl waechst quadratisch; die
            idx = np.linspace(0, len(Z) - 1, cap).astype(int)   # Stichprobe reicht fuer Quantile
            Z, y = Z[idx], y[idx]
        G = Z @ Z.T
        D = np.sqrt(np.maximum(np.diag(G)[:, None] + np.diag(G)[None, :] - 2 * G, 0.0))
        iu = np.triu_indices(len(Z), 1)
        gleich = (y[:, None] == y[None, :])[iu]
        d_in, d_out = D[iu][gleich], D[iu][~gleich]
        if len(d_in) < 50 or len(d_out) < 50:                # zu duenn -> beim naechsten Mal
            self.birth_th = None
            return
        kand = np.quantile(d_in, np.linspace(0.05, 0.95, 91))
        j, t = max((float(np.mean(d_in <= c) - np.mean(d_out <= c)), float(c)) for c in kand)
        self.birth_th = t
        self._birth_j = (j, float(np.mean(d_in <= t)), float(np.mean(d_out <= t)))

    def _merge_th(self):
        """Schwelle der FARBSTREUUNG, ab der ein Fleck als verschmolzen gilt -- aus den eigenen
        Einzelobjekt-Flecken gemessen (0.995-Quantil, dieselbe Konvention wie novel_th), nichts
        eingestellt.  None, solange zu wenig Referenz vorliegt -> keine Sperre, das alte Verhalten.

        GRENZE, vorab gemessen und bewusst in Kauf genommen: Einzelobjekte streuen 0.046-0.107,
        Verschmelzungen 0.099-0.275.  Vier von fuenf Verschmelzungen liegen bei 0.20-0.27 und werden
        sicher erkannt; die Ausnahme ist obj_U+obj_blue (Cyan neben Blau, 0.099) -- bei AEHNLICH
        gefaerbten Nachbarn gibt es kaum Mischsignal und die Sperre greift nicht.  Sie faengt also
        etwa zwei Drittel der Phantom-Geburten, nicht alle.

        GEPAART NACHGEMESSEN (14 Seeds 911-924, je 30 Ep, SCENE_N=6 wie in der GUI, nur
        ACT_SHAPE_MERGE_GUARD unterschiedlich):
            Geburten gesamt      aus 23  ->  an 13   (43% weniger)
            besser 7   schlechter 0   gleich 7       Vorzeichentest p = 0.0156
            nur Laeufe, die in der Kontrolle ZERSPLITTERN (>=2 Geburten, n=6):  15 -> 7
            Lieferbilanz in 13 von 14 Paaren IDENTISCH -- die Sperre greift wie beabsichtigt nur in
            den Geburtspfad, nicht in Ansprueche oder Ausfuehrung.
        Die sieben Gleichstaende sind durchweg Laeufe mit nur EINER Geburt in der Kontrolle -- dort
        gibt es nichts zu verbessern, diese eine Klasse ist das echte Objekt.
        FEHLSPERRUNG, gemessen statt gehofft: 13 von 156 Sperren (8%) trafen ISOLIERTE, nicht
        aufgeblaehte Flecken -- alle an obj_U (786-1027px gegen ~762 allein).  obj_U ist eine
        TRAINIERTE Form und erreicht den Geburtspfad nur, wenn sie ohnehin schon als "neu" gelesen
        wurde; sie dort zu sperren verhindert eine Zweitklasse fuer ein bekanntes Objekt.  Vertretbar,
        aber es ist keine Null.
        WAS DABEI AUFFIEL und die Erzaehlung korrigiert: 29 der 64 Sperren betreffen ISOLIERTE Objekte
        (kein Nachbar naeher als 45mm).  Es sind also ueberwiegend nicht Objekt+Objekt-Verschmelzungen,
        sondern OBJEKT + ARM im Bild -- die Flaechen liegen beim 1.5- bis 3-fachen des Objekts allein
        (572px an einem Wuerfel von ~267, 1347px an obj_U von ~762).  Auch das sind zwei Dinge in einem
        Fleck und taugen nicht als Formsichtung, die Sperre arbeitet also richtig, nur breiter als
        urspruenglich angenommen.  KEIN sauberer Einzelfleck wurde gesperrt (geprueft ueber alle 64).

        WARUM SCHON AB 12 WERTEN (und nicht ab 40, wie zuerst gebaut): die Phantom-Geburten fallen
        gemessen in Episode 10-19, und bei nur ~2 trainierten Flecken je Blick war die Sperre mit 40
        Werten erst um Episode 20 scharf -- sie kam zu spaet und blockierte im ersten Lauf NICHTS.
        Bei 12 Werten ist das 0.995-Quantil praktisch das Maximum der bisherigen Einzelobjekte, also
        die konservative Richtung: lieber zu selten sperren als einen echten neuen Koerper verwerfen."""
        if not MERGE_GUARD:
            return None                                      # ACT_SHAPE_MERGE_GUARD=0 -> alter Stand
        ref = getattr(self, "_cs_ref", None)
        if not ref or len(ref) < 12:
            return None
        return float(np.quantile(np.asarray(ref, float), 0.995))

    def _birth_radius(self):
        """Der selbst gemessene Geburtsradius.  Faellt auf novel_th zurueck, solange nichts gemessen
        ist -- etwa bei einem Zustand aus dem Pickle von VOR dieser Aenderung; dort wird beim ersten
        Gebrauch nachgerechnet, ein Neu-Training ist nicht noetig."""
        b = getattr(self, "birth_th", None)
        if b is None and getattr(self, "_ZX", None) is not None and getattr(self, "_Y", None) is not None:
            try:
                self._fit_birth()
            except Exception:
                self.birth_th = None
            b = getattr(self, "birth_th", None)
        return float(b) if b else float(self.novel_th)

    def all_names(self):
        return SHAPES + self.open_names

    def _dicke_passt(self, nm, dicke):
        """Passt die gemessene Materialdicke zu dem, was die Klasse bisher gesehen hat?
        Faellt AUS (True), solange die Klasse < DICKE_MIN_N Messwerte hat -- ein geladener
        Zustand bringt keine mit."""
        if not DICKE_WACHE or dicke is None:
            return True
        h = (getattr(self, "open_dicke", None) or {}).get(nm) or []
        if len(h) < DICKE_MIN_N:
            return True
        passt = abs(float(dicke) - float(np.median(h))) <= DICKE_TOL
        if not passt:
            self._veto_n = getattr(self, "_veto_n", 0) + 1
        return passt

    def resolve(self, desc, dicke=None):
        """OPEN-SET classification of one |F| descriptor -> (name, kNN distance).  Stage 1: within
        novel_th of the TRAINING exemplars -> a base class, the trained head decides (it is the accurate
        boundary there).  Stage 2: nearest self-labelled class within the RELAXED claim radius
        (OPEN_MARGIN * novel_th -- young exemplar sets are sparse over poses, see OPEN_MARGIN above).
        Neither -> (None, d): a NOVEL form."""
        if self.novel_th is None:                            # not calibrated (train() not run) -> closed set
            return SHAPES[int(self.classify(desc).argmax())], 0.0
        z = self._z(desc)
        dk = self._knn(z, self._ZX)
        if dk <= self.novel_th:
            return SHAPES[int(self.classify(desc).argmax())], dk
        # DICKEN-WACHE IN DER KANDIDATENSCHLEIFE (Fassung 2, 2026-09-04).  Fassung 1 sass HINTER
        # resolve und konnte den Anspruch nur ANNULLIEREN, nicht UMLEITEN: neu-9 gewann hier den
        # Wettbewerb, die Wache machte daraus spaeter ein None, und die junge Klasse -- die schon
        # innerhalb dieser Schleife verloren hatte -- kam nie zum Zug.  GEMESSEN: der Kandidat
        # bekam in 8 Blicken GENAU EINEN Treffer, ein Knopf ist so unerreichbar (die Bestaetigung
        # in pc_act23.py:1991 zaehlt genau das Feld, das Fassung 1 leerte).
        # JETZT: unpassende Klassen werden UEBERSPRUNGEN, bevor bester und zweitbester feststehen.
        # Das leitet den Anspruch an die legitime naechste Klasse um UND entzerrt die relative
        # Wache unten, die sonst gegen einen Konkurrenten rechnet, der hinterher vetiert wird.
        best_nm, best_d, second_d = None, np.inf, np.inf
        for nm, ex in self.open.items():
            if not self._dicke_passt(nm, dicke):
                continue
            d = self._knn(z, ex, k=1)                        # nearest exemplar (young sets are small)
            if d < best_d:
                best_nm, best_d, second_d = nm, d, best_d
            elif d < second_d:
                second_d = d
        # claim gates (all MEASURED against the long-I vs T pair, the user-hit confusion):
        #  * absolute: within the relaxed radius (young sets are pose-sparse),
        #  * vs KNOWN: nearer than the trained manifold (T->known p50 9.9 < T->exI p10 12.6; without
        #    this the I's class ABSORBED every T sighting -> the T was never born, no button),
        #  * RELATIVE: clearly nearer than the second-best open class (kills tail cross-claims that
        #    would POLLUTE an exemplar set -- one wrong exemplar collapses future distances, cascade).
        if (best_nm is not None and best_d <= min(self.novel_th * OPEN_MARGIN, dk)
                and best_d <= 0.8 * second_d):
            return best_nm, best_d
        return None, min(dk, best_d)

    def observe_scene(self, sim, min_area=40, bounds=None, protect=None):
        """OPEN-SET self-labelling GLANCE: segment+resolve the scene; every NOVEL blob feeds the candidate
        buffer, and once NOVEL_CONFIRM sightings AGREE (mutual z-distance < novel_th -- the same PERSISTENT
        form, not a glint or an occlusion artefact) a new class is COMMITTED and self-named ("neu-1", ...).
        Sightings that match an already self-labelled class EXTEND its exemplar set (capped), so the
        self-label keeps improving with every later view/pose.  No truth label anywhere.  Call this at
        scene events (placement, after a command), NOT per tracked frame (near-duplicate frames would
        swamp the exemplar sets).  `bounds` (xmin,xmax,ymin,ymax): only sightings INSIDE this world region
        count -- the descriptor is only calibrated where training sampled; an object dropped at the
        workspace EDGE renders clipped/distorted and reads consistently "novel" for a boring reason
        (measured: a mis-delivered cube at y=0.24 bred a phantom class).  Returns newly created names."""
        born = []
        self.last_events = []                                # glance debug trail (novel/claim/born + where)
        _veto0 = getattr(self, "_veto_n", 0)                 # Vetos DIESES Blicks zaehlen (s. unten)
        if getattr(self, "_novel_groups", None) is None:      # LAZY: aus dem Zustands-Pickle geladene
            self._novel_groups = [{"ex": [b], "age": 0}       #   Instanzen haben das Feld nicht; die
                                  for b in (self._novel_buf or [])]   # alten Eintraege werden Einzelgruppen
        for det in self.perceive_all(sim, min_area=min_area):
            if self.area_hi is not None and det["area"] > self.area_hi:
                continue                                     # oversize blob = two objects MERGED (pushed
                #   together mid-scene) -- never a valid form sighting, would breed a phantom class
            if bounds is not None and det["pos"] is not None:
                x, y = float(det["pos"][0]), float(det["pos"][1])
                if not (bounds[0] <= x <= bounds[1] and bounds[2] <= y <= bounds[3]):
                    continue                                 # outside the calibrated workspace -> no verdict
            z = self._z(det["desc"]); nm = det["shape"]
            cs = det.get("cspread")
            if cs is not None and nm is not None:
                # SELBST-KALIBRIERUNG der Verschmelzungs-Sperre: ein Fleck, der eine BEKANNTE Form
                # beansprucht (trainiert ODER selbst benannt), ist so gut wie immer EIN Objekt -- ein
                # verschmolzener Fleck ist eine neue Silhouette und passt auf keine.  Seine Farbstreuung
                # ist damit die Referenz.  Nichts eingestellt, s. _merge_th.
                # WARUM NICHT NUR TRAINIERTE (erster Bau): davon gibt es in dieser Szene nur ~0.5 je Blick,
                # die Sperre war damit erst ab Episode 23 scharf -- die Phantom-Geburten fallen aber in
                # Episode 10-18, sie kam also IMMER zu spaet (gemessen: 13 Sperren, alle nach der letzten
                # Geburt, Geburtenzahl unveraendert 3).  Mit allen Anspruechen sind es ~4-5 je Blick.
                # RESTRISIKO, bewusst: existiert erst einmal eine Phantomklasse, koennen verschmolzene
                # Flecken SIE beanspruchen und die Referenz nach oben ziehen.  Genau das soll die Sperre
                # ja verhindern; solange sie greift, entsteht die Phantomklasse gar nicht erst.
                self._cs_ref = (list(getattr(self, "_cs_ref", []) or []) + [float(cs)])[-400:]
            if nm is not None and nm not in SHAPES:          # open-class match -> grow its exemplar set
                self.last_events.append(("claim", nm, None if det["pos"] is None
                                         else np.round(det["pos"], 3).tolist()))
                if getattr(self, "_age", None) is None:
                    self._age = {}
                self._age[nm] = 0                            # a fresh claim keeps the class alive (starvation)
                if len(self.open[nm]) < OPEN_CAP:
                    self.open[nm].append(z)
                elif EX_REFRESH and self._knn(z, np.asarray(self.open[nm]), k=1) <= self.novel_th:
                    # NUR SICHERE ANSPRUECHE FRISCHEN AUF (2026-09-02, nach einem gemessenen
                    # Fehlschlag meiner ersten Fassung).  Ohne diese Bedingung nimmt die Klasse auch
                    # BAND-Ansprueche auf (novel_th < d <= novel_th*OPEN_MARGIN) -- also genau die
                    # unsicheren -- und frisst sich an ihrem eigenen Irrtum fest.  GEMESSEN am
                    # 10-mm-Y gegen neu-9 (obj_T), 15 Sichtungen nacheinander:
                    #     ohne Auffrischung: Abstand 11,2 -> 10,3   (stabil)
                    #     MIT (erste Fassung): 7,0 -> 4,2           (kollabiert, Y wird einverleibt)
                    # Der erste Kontakt lag bei 13,4, also AUSSERHALB -- der Fehler beginnt erst mit
                    # der Aufnahme des unsicheren Anspruchs.  Mit dieser Schranke kann er nicht
                    # beginnen: was nur im Band liegt, haelt die Klasse am Leben (Alterszaehler),
                    # veraendert sie aber NICHT.
                    # AUFFRISCHUNG STATT ABWEISUNG (2026-09-02).  BEFUND: bei OPEN_CAP nahm eine
                    # Klasse NIE wieder ein Exemplar auf -- sie fror ein.  Alle vier Klassen im
                    # Nutzerzustand stehen bei exakt 80, ueber alle seitherigen Aenderungen hinweg
                    # (Greifergeometrie, Fovea-Zoom).  GEMESSEN: 85% der VERSCHIEDENEN Exemplare von
                    # neu-9 (obj_T) liegen weiter als novel_th von JEDER frischen Sichtung des T
                    # entfernt, Median 10,85.  Die Klasse ist damit eine breite VERALTETE Wolke --
                    # und eine breite Wolke beansprucht alles in ihrer Naehe.  Genau daran ist das
                    # 10-mm-Y gescheitert: es lag 9,47 von neu-9 entfernt, bei einem Eigendurchmesser
                    # der Klasse von 9,78.  Der Anspruch war nach ihrer eigenen Geometrie normal.
                    #
                    # ERSETZT WIRD ZUERST EIN DUPLIKAT: von 80 Eintraegen sind nur 18-36 verschieden,
                    # es ist also reichlich redundantes Material da, dessen Wegfall KEINE Abdeckung
                    # kostet.  Erst wenn keine Duplikate mehr da sind, weicht das aelteste.
                    # ACT_SHAPE_EX_REFRESH=0 stellt das Einfrieren wieder her.
                    ex = self.open[nm]
                    i_weg = 0
                    for i in range(len(ex)):
                        if self._knn(ex[i], np.asarray(ex[:i] + ex[i+1:]), k=1) <= EX_DUP_TH:
                            i_weg = i
                            break
                    ex.pop(i_weg)
                    ex.append(z)
                # DICKE der Klasse lernen -- NUR aus SICHEREN Anspruechen, aus demselben Grund wie
                # die Exemplar-Auffrischung: lernte sie aus Band-Anspruechen, fraesse sie sich an
                # ihrem eigenen Irrtum fest (gemessene Kaskade, s. EX_REFRESH).
                if (DICKE_WACHE and det.get("dicke") is not None
                        and self._knn(z, np.asarray(self.open[nm]), k=1) <= self.novel_th):
                    if getattr(self, "open_dicke", None) is None:
                        self.open_dicke = {}
                    self.open_dicke[nm] = (self.open_dicke.get(nm, [])
                                           + [float(det["dicke"])])[-DICKE_CAP:]
            elif nm is None:                                 # NOVEL sighting -> temporal-consistency buffer
                _mth = self._merge_th()
                if _mth is not None and cs is not None and cs > _mth:
                    # VERSCHMOLZENER FLECK -> KEIN Geburts-Material.  WARUM (gemessen 2026-08-18 ueber
                    # drei 50-Episoden-Laeufe): von drei geborenen Klassen waren ZWEI Phantome aus
                    # verschmolzenen Flecken (ausloesende Flaechen 1019 und 855 px, das echte Objekt
                    # misst ~450).  Und die Zersplitterung waechst mit der Lauflaenge -- 1.20 Klassen
                    # bei 30 Episoden, 2.00 bei 50 (~0.04 je Episode), auf einen 300-Episoden-Lauf
                    # hochgerechnet ueber zehn Klassen fuer EIN Objekt.  Der vorhandene Flaechen-Schutz
                    # area_hi (1411) kann das prinzipiell nicht: die Verschmelzungen messen 822-1390,
                    # die groesste TRAININGSform ~940.
                    self.last_events.append(("verschmolzen", None if det["pos"] is None
                                             else np.round(det["pos"], 3).tolist(), int(det["area"])))
                    continue
                self.last_events.append(("novel", None if det["pos"] is None
                                         else np.round(det["pos"], 3).tolist(), int(det["area"])))
                _br = self._birth_radius() * BIRTH_MARGIN     # selbst gemessen, s. _fit_birth()
                if NOVEL_CLUSTER:
                    # CLUSTER-PUFFER statt FIFO (s. NOVEL_CLUSTER oben).  Die Sichtung sucht sich
                    # eine GRUPPE, zu deren saemtlichen Mitgliedern sie naeher als _br liegt (nicht
                    # nur zum naechsten -- sonst kettet sich eine Gruppe ueber weite Strecken
                    # zusammen).  Passt keine, beginnt sie eine eigene.
                    grp = next((g for g in self._novel_groups
                                if all(float(np.linalg.norm(q - z)) < _br for q in g["ex"])), None)
                    if grp is None:
                        self._novel_groups.append({"ex": [z], "age": 0})
                        near = []
                    else:
                        grp["ex"].append(z); grp["age"] = 0
                        near = grp["ex"][:-1]
                        if len(grp["ex"]) >= NOVEL_CONFIRM:
                            self._novel_groups.remove(grp)     # reif -> unten Geburt/Wirt
                else:
                    near = [b for b in self._novel_buf if float(np.linalg.norm(b - z)) < _br]
                if len(near) + 1 >= NOVEL_CONFIRM:
                    ex = near + [z]
                    # birth-time MERGE: a claim can MISS a young class across a pose change (deterministic
                    # renders repeat the miss NOVEL_CONFIRM times) -- if the newborn cluster sits within
                    # MERGE_MARGIN of an existing open class it IS that class seen anew, absorb it.
                    # Same vs-KNOWN gate as claims: merging a cluster that is NEARER THE TRAINED MANIFOLD
                    # than the host class mixes two forms (a mis-merged T POISONED the I's exemplars --
                    # one wrong exemplar collapses future distances and the classes bleed together).
                    dko = min(self._knn(q, self._ZX) for q in ex)
                    host = next((onm for onm, oex in self.open.items()
                                 if min(float(np.linalg.norm(a - b)) for a in ex for b in oex)
                                 < min(self.novel_th * MERGE_MARGIN, dko)), None)
                    if host is not None:
                        self.open[host] = (self.open[host] + ex)[:OPEN_CAP]
                    else:
                        # UNIQUE name via a monotone counter, NOT len+1: consolidation SHRINKS the list,
                        # so len+1 can collide with a live class and silently overwrite it.  getattr =
                        # backward-compat with pickled instances (seeded from the highest existing number).
                        seq = getattr(self, "_name_seq", None)
                        if seq is None:
                            seq = max((int(nm.rsplit("-", 1)[1]) for nm in self.open_names), default=0)
                        self._name_seq = seq + 1
                        name = f"neu-{self._name_seq}"
                        self.open_names.append(name); self.open[name] = ex
                        born.append(name)
                    if not NOVEL_CLUSTER:
                        self._novel_buf = [b for b in self._novel_buf if not any(b is q for q in near)]
                elif not NOVEL_CLUSTER:
                    self._novel_buf.append(z)
        if NOVEL_CLUSTER:
            # ALTERN statt verdraengen: eine Gruppe stirbt, wenn sie NOVEL_GROUP_AGE Blicke lang
            # keinen neuen Beleg bekommt -- das ist dieselbe Absicht wie der alte 12er-Deckel
            # ("stale far-pose sightings must not pile up"), nur nach UEBEREINSTIMMUNG statt nach
            # Aktualitaet.  Eine Gruppe, die weiter belegt wird, ueberlebt beliebig lange; eine
            # zufaellige Einzelsichtung verfaellt.
            for g in self._novel_groups:
                g["age"] += 1
            self._novel_groups = [g for g in self._novel_groups if g["age"] <= NOVEL_GROUP_AGE]
            if len(self._novel_groups) > NOVEL_GROUP_MAX:     # groesste zuerst behalten
                self._novel_groups.sort(key=lambda g: (-len(g["ex"]), g["age"]))
                del self._novel_groups[NOVEL_GROUP_MAX:]
        else:
            self._novel_buf = self._novel_buf[-12:]          # stale far-pose sightings must not pile up
        # CONSOLIDATE duplicates: the dko merge gate can force a SECOND class for the same form (far-pose
        # re-birth); once both sets densify, same-form sets grow INTO each other (T-T p50 ~5.8) while
        # different forms stay >= the cross floor (~12.5) -> min cross-distance unter dem Radius = same form.
        # The OLDER name survives (it is the one act23 may have registered as a command).
        # WARUM HIER WEITER novel_th UND NICHT DER SELBST GEMESSENE RADIUS -- GEMESSENES NEGATIV
        # (2026-08-16, zwei gepaarte 50-Ep-Laeufe, Seed 907).  Die URSACHE der Zersplitterung ist sauber
        # isoliert (act23_split_probe, Kreuz obj_X, Klassen aus je 3 Belegen):
        #     Klasse aus 3 Sichtungen AM SELBEN ORT  -> beansprucht anderswo nur  47.2%
        #     Klasse aus 3 VERTEILTEN Sichtungen     ->                           77.8%
        # Die Geburt verlangt drei Sichtungen, die sich EINIG sind, also drei vom selben Fleck -- eine
        # neugeborene Klasse ist zwangslaeufig ortsgebunden, verfehlt ihr Objekt anderswo in der Haelfte
        # der Faelle, und die Fehlschlaege gebaeren die naechste ortsgebundene Klasse (das Kreuz erzeugte
        # DREI).  Die TORE sind unschuldig: mit realistischen 3 Belegen laesst der Anspruchspfad 82% der
        # eigenen Sichtungen durch und 0% fremde.
        # NAHELIEGEND UND FALSCH war daraufhin, hier den selbst gemessenen Radius (11.46) einzusetzen.
        # Das Fenster schien sauber -- gleiches Objekt min-Abstand p90 9.55, FREMDobjekt p10 12.50 --,
        # ABER es ist an 3-Beleg-Mengen gemessen.  Diese Zeile vergleicht das MINIMUM ueber zwei Mengen
        # mit bis zu OPEN_CAP=80 Belegen, also ueber bis zu 6400 Paare: eine viel extremere Groesse, die
        # der p10 aus 3x3 Paaren nicht abdeckt.  Ergebnis im Lauf: die Kreuz-Klasse wurde zwar stabiler
        # (Wiedererkennung 33% -> 100% der letzten 12 Blicke, 90% ihrer Ansprueche auf dem Kreuz), aber
        # DREI etablierte Altklassen (neu-34, neu-72, neu-256) wurden verschluckt, und der Kommando-Pfad
        # halbierte sich reproduzierbar von 8/8 auf 4/8 obj_X-Episoden "via Formklasse" (zwei Laeufe).
        # LEHRE: ein Schwellwert, der an einer Stichprobengroesse kalibriert wurde, uebertraegt sich NICHT
        # auf eine Extremwert-Statistik ueber viel groessere Mengen.  Wer das hier nochmal angeht, muss
        # den Schwellwert MENGENGROESSEN-ABHAENGIG messen (min-Abstand als Funktion von |A|,|B|).
        for a in list(self.open_names):
            for b in list(self.open_names):
                if (a in self.open and b in self.open                # a/b may have been MERGED AWAY by an
                        #   earlier pass of this very loop -- index() on a removed name raised ValueError
                        and self.open_names.index(a) < self.open_names.index(b)
                        and min(float(np.linalg.norm(p - q))
                                for p in self.open[a] for q in self.open[b]) < self.novel_th):
                    self.open[a] = (self.open[a] + self.open[b])[:OPEN_CAP]
                    del self.open[b]; self.open_names.remove(b)
                    born = [nm for nm in born if nm != b]
        # WACHE ZAEHLBAR MACHEN: ohne diese Zeile war "berechtigter Anspruch getoetet" nur
        # erschlossen (aus fallenden Anspruchszahlen), nie gemessen.  ACT_SHAPE_DICKE_LOG=1.
        if DICKE_LOG and getattr(self, "_veto_n", 0) > _veto0:
            print(f"    [Dicken-Wache] {getattr(self, '_veto_n', 0) - _veto0} Anspruch/Ansprueche "
                  f"verworfen (gesamt {getattr(self, '_veto_n', 0)}); Klassen-Mediane: "
                  + ", ".join(f"{k} {np.median(v):.1f}" for k, v in
                              sorted((getattr(self, "open_dicke", None) or {}).items())
                              if len(v) >= DICKE_MIN_N), flush=True)
        self._starve_and_cap(born, protect)
        return born

    def _starve_and_cap(self, born=(), protect=None):
        """Age every open class this glance; prune small, long-unclaimed phantoms (never a bound
        command); then enforce the hard cap by dropping the most-starved.  Newborns start at age 0,
        so a class gets STARVE_N glances to be reinforced before it can die."""
        prot = set(protect or ())
        if getattr(self, "_age", None) is None:
            self._age = {}
        for nm in self.open_names:
            self._age[nm] = 0 if nm in born else self._age.get(nm, 0) + 1

        def _prunable(nm):
            if nm in prot:                                   # gebundene Kommandos nie
                return False
            if len(self.open.get(nm, [])) <= STARVE_MIN_EX:
                return True
            return STARVE_OLD > 0 and self._age.get(nm, 0) > STARVE_N * STARVE_OLD   # s. STARVE_OLD

        for nm in [n for n in self.open_names if _prunable(n) and self._age.get(n, 0) > STARVE_N]:
            del self.open[nm]; self.open_names.remove(nm); self._age.pop(nm, None)
        if len(self.open_names) > MAX_OPEN:                  # HARD cap: over the limit, drop the most-
            over = len(self.open_names) - MAX_OPEN           #   STARVED UNPROTECTED classes -- ANY size
            #   (duplicate big classes of the same form that consolidation never merged pile up too; a
            #   bound command is protected, an unbound one is just re-discovered if it is ever seen again)
            for nm in sorted((n for n in self.open_names if n not in prot),
                             key=lambda n: -self._age.get(n, 0))[:over]:
                del self.open[nm]; self.open_names.remove(nm); self._age.pop(nm, None)

    def enforce_cap_on_load(self, protect=None):
        """Apply the hard MAX_OPEN cap to a LOADED phantom pile.  The per-glance starvation only runs in
        observe_scene, which is SKIPPED when a state is loaded (startup training skipped), so a persisted
        state keeps every phantom it ever bred.  Drops the THINNEST unprotected classes first (fewest
        exemplars = least-reinforced) until <= MAX_OPEN; bound commands (protect) are always kept.
        Returns the dropped names."""
        prot = set(protect or ())
        if getattr(self, "_age", None) is None:
            self._age = {}
        dropped = []
        while len(self.open_names) > MAX_OPEN:
            cand = [n for n in self.open_names if n not in prot]
            if not cand:
                break                                            # only protected commands left -> stop
            nm = min(cand, key=lambda n: len(self.open.get(n, [])))
            del self.open[nm]; self.open_names.remove(nm); self._age.pop(nm, None)
            dropped.append(nm)
        return dropped

    # ------------------------------------------------------------------
    def perceive(self, sim):
        """Perceive the (single, in-view) object's shape + orientation from the camera."""
        self._park_markers(sim)
        F = self._harmonics(self._render_u8(sim))
        if F is None:
            self._last = None
            for pn in ("shape_logits", "shape_id", "shape_yaw"):
                self.set_out(pn, None)
            return None
        logits = self.classify(np.abs(F).ravel()); k = int(logits.argmax()); yaw = self._yaw_from(F)
        self._last = (k, _softmax(logits), yaw)
        self.set_out("shape_logits", logits); self.set_out("shape_id", [k]); self.set_out("shape_yaw", [yaw])
        return SHAPES[k]

    def perceive_all(self, sim, min_area=40, cands=False, wpx=False):
        """Localise + classify EVERY object under distractors: segment the colour-agnostic occupancy into
        CONNECTED COMPONENTS (one blob = one object), then classify each by its own form descriptor (rings
        sampled ONLY on that component, so neighbours don't leak in).  Returns a list of detections:
        {shape, id, prob, pos (world xy, overview), yaw, px}.  No colour, no privileged positions.
        cands=True additionally samples GRASP-POINT CANDIDATES from the component's material (the user's
        goal: the agent DISCOVERS where to grip from its own perception + outcomes, the densest-point
        heuristic degrades to one candidate among them): distance-transform the component, keep locally
        THICK points (both fingers find material), greedily pick up to 6 diverse ones (>=12mm apart,
        thickest first) in world coords.  Off by default -- the form tracker calls this per frame."""
        from scipy import ndimage
        self._park_markers(sim)
        img = self._render_u8(sim)
        min_area = min_area * self.px_scale() ** 2          # FLAECHE -> s^2 (s. px_scale)
        mask = self._mask(img)
        labels, n = ndimage.label(mask)
        # FARBFREIER SPLIT verschmolzener Blobs (2026-08-31).  ANLASS: obj_X teilt seine RGBA mit
        # obj_T, bekam deshalb NIE eine eigene Farbklasse, und der farbbasierte Form-Split lief fuer
        # es in 0% der Episoden (L/U/T: 12-33%).  Jede Verschmelzung fiel damit auf den
        # PRIVILEGIERTEN Rueckfall durch -> Erkennung 80,7% statt 97-98%, 148 von 259 Rueckfaellen.
        # Gemessen ist auch die Ursache der Verschmelzung: der naechste Nachbar liegt bei Misserfolg
        # im Median 52 mm entfernt, bei Erfolg 94 mm.
        #
        # VERFAHREN, bewusst OHNE Farbe: eine Komponente, deren Deskriptor KEINE Klasse trifft
        # (resolve -> None), ist der Verdachtsfall.  Sie wird erodiert, bis sie in >= 2 Kerne
        # zerfaellt; dann bekommt jedes Ursprungspixel den naechstgelegenen Kern zugeschlagen
        # (Distanztransformation mit return_indices, kein skimage noetig).  Die Teile laufen durch
        # DENSELBEN Klassifikationsweg wie normale Komponenten -- kein zweiter Codepfad.
        # Die Original-Komponente bleibt zusaetzlich in der Liste: faellt der Split daneben, geht
        # nichts verloren, und der Aufrufer filtert ohnehin nach der gesuchten Form.
        _masks = []
        for lab in range(1, n + 1):
            _c = (labels == lab)
            if _c.sum() < min_area:
                continue                                     # drop specks / glints
            _masks.append(_c)
            if not SPLIT_FUSED or _c.sum() < 1.6 * min_area:
                continue                                     # zu klein, um zwei Objekte zu halten
            _cf = _c.astype(np.float32)
            if not SPLIT_ALWAYS and self.resolve(
                    np.abs(self._harmonics_at(_cf, self._centroid(_cf))).ravel())[0] is not None:
                continue                # loest auf -> nicht verschmolzen.  ABER: eine verschmolzene
                #   Komponente loest oft FALSCH auf die groessere Nachbarform auf, dann greift der
                #   Split nie.  ACT_SHAPE_SPLIT_ALWAYS=1 spaltet jede grosse Komponente.
            _er = _c
            for _ in range(SPLIT_ERODE_MAX):
                _er = ndimage.binary_erosion(_er)
                if not _er.any():
                    break
                _sl, _sn = ndimage.label(_er)
                _big = [i for i in range(1, _sn + 1) if (_sl == i).sum() >= 0.25 * min_area]
                if len(_big) >= 2:
                    _seed = np.isin(_sl, _big)
                    _, _idx = ndimage.distance_transform_edt(~_seed, return_indices=True)
                    _own = _sl[_idx[0], _idx[1]]
                    for _i in _big:
                        _p = _c & (_own == _i)
                        if _p.sum() >= min_area:
                            _masks.append(_p)
                    break
        out = []
        for comp in _masks:
            comp = comp.astype(np.float32)
            ctr = self._centroid(comp)                       # world (overview) or px (top)
            F = self._harmonics_at(comp, ctr)
            desc = np.abs(F).ravel()
            # SECHSTER ANLAUF (s. RELRINGS_SPLIT oben): die Klasse aus RELATIVEN Ringen, die
            # AUSRICHTUNG aus den FESTEN.  F oben ist im Split-Modus bereits relativ (fuer desc);
            # F_lage wird hier zusaetzlich fest gerechnet und NUR fuer yaw/yaw4 benutzt.
            F_lage = self._harmonics_at(comp, ctr, relativ=False) if RELRINGS_SPLIT else F
            # OPEN-SET resolve: a trained class (head decides), a self-labelled class (prototype claims
            # it), or None = NOVEL form.  prob for open classes = prototype proximity (no softmax exists).
            # MATERIALDICKE -- immer gemessen, nicht mehr an die (abgeschaltete) Wache gekoppelt.
            # Sie ist ein EIGENER Wahrnehmungskanal neben Farbe und Form: gemessen trennt sie
            # gleiche Formen verschiedener Breite mit dem 6- bis 40-fachen ihrer eigenen Streuung
            # (Y10 7,07 +-0,07 | Y14 8,25 +-0,16 | Y20 10,00 +-0,05).  Gebraucht wird sie fuer die
            # Auswahl nach EIGENSCHAFTEN (Farbe + Form + Groesse) statt nach Objektnamen --
            # damit ein neues Objekt adressierbar ist, OHNE dass eine eigene Klasse entstehen muss.
            # AUFLOESUNGSUNABHAENGIG: die Distanztransformation liefert PIXEL, und die skalieren mit
            # der Bildbreite (gemessen: dieselbe Szene 8,06-8,74 px bei 360er Rendern, 5,66-7,00 bei
            # 240er).  Bandgrenzen in Pixeln waeren damit stillschweigend an eine Aufloesung
            # gebunden gewesen.  px_scale() ist genau dafuer da (1.0 bei PX_REF=240).
            _dt = ndimage.distance_transform_edt(comp > 0)
            _dicke = (float(np.percentile(_dt[comp > 0], 90)) / max(self.px_scale(), 1e-6)
                      if comp.any() else None)
            name, ndist = self.resolve(desc, dicke=_dicke)
            if name is None:
                k, prob = -1, 0.0
            elif name in SHAPES:
                logits = self.classify(desc); k = int(logits.argmax())
                prob = float(_softmax(logits)[k])
            else:
                k = len(SHAPES) + self.open_names.index(name)
                prob = float(np.clip(1.0 - ndist / (2.0 * self.novel_th), 0.05, 1.0))
            ys, xs = np.nonzero(comp)
            # GRASP point: the MATERIAL point nearest the centroid -- central + on a (thin) bar, which the
            # gripper spans cleanly.  Best for the thin-bar shapes (the cube-built / tip / wrist variants were
            # all marginal; this v1 grasped the thin-bar L well).  No wrist (orientation gave no gain).
            grasp = ctr
            grasp_dense = ctr                                              # DENSEST material point (distance-
            #   transform max) = the solid BASE of a concave shape; the nearest-material grasp above lands on
            #   the THIN inner rim of a U (centroid sits in the concavity) -> "greift ins Leere".  Exposed so
            #   a caller can grip the base instead (ACT23_U_DENSEGRASP; 746-log U mechanism-ID 2026-07-24).
            gcands = []
            if self.H is not None:
                W = self._px_to_world(np.column_stack([xs, ys]))            # world coords of the component px
                grasp = W[int(np.argmin(np.linalg.norm(W - ctr, axis=1)))]  # nearest material to the centroid
                want_dense = cands or os.environ.get("ACT23_U_DENSEGRASP", "1") != "0"
                if want_dense:                                             # grasp-point candidate SAMPLING
                    dist = ndimage.distance_transform_edt(comp)             # local material thickness (px)
                    dv = dist[ys, xs]
                    grasp_dense = W[int(np.argmax(dv))]                     # thickest = solid base
                    if cands:                                              # grasp-point candidate SAMPLING
                        order = np.argsort(-dv)
                        for i in order:
                            if dv[i] < max(2.0 * self.px_scale(), 0.45 * float(dv[order[0]])):
                                break                                       # thin rim: fingers find no hold
                            p = W[i]
                            if all(float(np.linalg.norm(p - q)) > 0.012 for q in gcands):
                                gcands.append(p)
                            if len(gcands) >= 6:
                                break
            span = 0.0                                          # MATERIAL-HALBSPANNE in Metern: 95%-Perzentil
            if self.H is not None:                              #   des Abstands vom Schwerpunkt.  Damit kann ein
                _W = self._px_to_world(np.column_stack([xs, ys]))   # Aufrufer die zulaessige Greifpunkt-
                span = float(np.percentile(np.linalg.norm(_W - ctr, axis=1), 95))   # Verschiebung an die
            #   OBJEKTGROESSE koppeln statt an eine feste Zahl (s. ACT23_GRASP_CAND_FRAC in pc_act23).
            _pix = img[ys, xs].astype(float)
            rgb = _pix.mean(0) / 255.0                          # component CHROMATICITY (stage-3 colour
            csum = float(rgb.sum())                             #   open-set: brightness-normalised, so
            chroma = rgb / csum if csum > 1e-6 else rgb         #   shading/position largely cancel)
            # FARBSTREUUNG IM FLECK: mittlere Abweichung der Pixel-Chromatizitaet vom Fleck-Mittel.  Ein
            # VERSCHMOLZENER Fleck enthaelt zwei Farbpopulationen und streut deutlich staerker als ein
            # einzelnes Objekt -- und anders als der mittlere Farbabstand braucht das KEIN Vorwissen ueber
            # die Farbe (gemessen: das noch farblose Kreuz liegt beim Farbabstand mit 0.074 ueber einer
            # echten Verschmelzung mit 0.028, ein Erkenner darauf wuerde genau die NEUEN Objekte
            # verwerfen).  Wird in observe_scene als Geburts-Sperre benutzt, s. dort.
            _pc = _pix / (_pix.sum(1, keepdims=True) + 1e-6)
            cspread = float(np.sqrt(((_pc - _pc.mean(0)) ** 2).sum(1).mean()))
            out.append({"shape": name, "id": k, "prob": prob,   # shape=None + id=-1 = a NOVEL form (open set)
                        "pos": (ctr if self.H is not None else None), "grasp_xy": grasp, "grasp_yaw": 0.0,
                        "yaw": self._yaw_from(F_lage), "yaw4": self._yaw4_from(F_lage),
                        "area": float(comp.sum()),
                        "chroma": chroma, "cspread": cspread, "dicke": _dicke,
                        "px": np.array([xs.mean(), ys.mean()]),
                        "span": span,                          # Material-Halbspanne (m), s. oben
                        "grasp_cands": gcands,                 # perception-grounded grasp-point candidates
                        "grasp_dense": grasp_dense,            # densest (base) point; ACT23_U_DENSEGRASP griff
                        "wpx": (W[::3] if (wpx and self.H is not None) else None),   # component material in
                        "desc": desc})                         #   world coords (judge: merged-blob recovery)
        return out                                             #   OPEN-WORLD (any object yields one, no class slot)

    def perceive_colour(self, sim, colours, cname, min_px=40, with_form=False):
        """MERGED-BLOB RECOVERY for the COLOUR path: localise the objects of ONE self-labelled colour class
        by splitting the occupancy at PIXEL level, instead of trusting a component's MEAN chroma.

        WHY (measured, log/red_l_diag.png, 2026-07-24): perceive_all averages chroma over a whole connected
        component (:623).  Two objects closer than ~40mm fuse into ONE component, and the mean lands on
        whichever object has MORE pixels -- the red cube next to the (larger) orange L reads as the L's
        class 'farbe-4' (d=0.100 < TH), so the red command finds ZERO candidates, loses its fovea servo
        for the whole episode and falls back to the old trained vc hex code, which grasps the L (the
        user watched exactly this).  Measured over gaps 70/50/38/28mm: whole-component centroid error
        0/0/25/20mm, this pixel split 6/6/6/5mm, and it recovers ~180 red px in every case (the cube's
        true size) whether or not the blobs touch.

        Same CONTINUITY idea self_eval uses after a release, but anchored on COLOUR instead of the hand,
        so it works BEFORE the grasp (no hand anchor exists yet).  Kept as a FALLBACK, not a replacement:
        while the blobs are separate the component mean is exact (0mm) and this split is slightly worse
        (6mm -- it drops shaded/edge pixels), so callers use it only when the normal match came up empty.

        Returns perceive_all-shaped detections (form fields are None/0: this is a COLOUR localiser, and
        the fused occupancy carries no usable form descriptor for the part anyway)."""
        from scipy import ndimage
        from .colour_openset import TH as _CTH
        if self.H is None or colours is None or cname is None:
            return []
        names = [n for n in colours.names if n in colours.classes]
        if cname not in names:
            return []
        self._park_markers(sim)
        img = self._render_u8(sim)
        ys, xs = np.nonzero(self._mask(img) > 0)
        if len(xs) == 0:
            return []
        MU = np.array([colours.classes[n]["mu"] for n in names])
        rgb = img[ys, xs].astype(float)
        s = rgb.sum(1, keepdims=True)
        ch = np.divide(rgb, s, out=np.zeros_like(rgb), where=s > 1e-6)   # per-PIXEL chromaticity
        d = np.linalg.norm(ch[:, None, :] - MU[None, :, :], axis=2)      # (npx, nclass)
        keep = (d.argmin(1) == names.index(cname)) & (d.min(1) <= _CTH)  # unambiguously THIS colour
        if int(keep.sum()) < min_px:
            return []
        sub = np.zeros(img.shape[:2], bool)                    # re-label the kept pixels so that two
        sub[ys[keep], xs[keep]] = True                         #   objects of the SAME colour stay apart
        labels, n = ndimage.label(sub)
        out = []
        for lab in range(1, n + 1):
            comp = labels == lab
            if comp.sum() < min_px:
                continue                                       # speck / colour-bleed at a fusion seam
            cys, cxs = np.nonzero(comp)
            W = self._px_to_world(np.column_stack([cxs, cys]))
            ctr = W.mean(0)
            grasp = W[int(np.argmin(np.linalg.norm(W - ctr, axis=1)))]
            crgb = img[cys, cxs].astype(float).mean(0)
            csum = float(crgb.sum())
            # GROESSE DES GETRENNTEN TEILS -- genau wie in perceive_all gerechnet, nur auf `comp`
            # statt auf der ganzen (verschmolzenen) Komponente.  Ohne diese beiden Felder traegt
            # eine Split-Detektion KEINE Groesse, und groessen_band() liefert auf ihr None: die
            # Groessenachse eines Eigenschafts-Tripels koennte auf dem getrennten Teil nie passen.
            # Rein additiv -- resolve() bekommt die Dicke bewusst NICHT (der Form-Pfad ruft es seit
            # jeher ohne auf, und das soll dieser Einbau nicht veraendern).
            _dt = ndimage.distance_transform_edt(comp > 0)
            _dicke = float(np.percentile(_dt[comp > 0], 90)) / max(self.px_scale(), 1e-6)
            _span = float(np.percentile(np.linalg.norm(W - ctr, axis=1), 95))
            name, k, prob, yaw, yaw4, desc = None, -1, 0.0, 0.0, 0.0, None
            if with_form:
                # FORM on the SEPARATED part: the whole fused component's descriptor is destroyed by the
                # neighbour (measured, obj_T: recognised as its own class 56% alone but only 8.8% when
                # fused), so classify the harmonics of THIS colour's material only.  Same rings/resolve
                # as perceive_all -- the colour split just supplies a clean footprint.
                _cf = comp.astype(np.float32)
                F = self._harmonics_at(_cf, ctr)
                desc = np.abs(F).ravel()
                F_lage = self._harmonics_at(_cf, ctr, relativ=False) if RELRINGS_SPLIT else F
                name, ndist = self.resolve(desc)
                if name in SHAPES:
                    logits = self.classify(desc); k = int(logits.argmax())
                    prob = float(_softmax(logits)[k])
                elif name is not None:
                    k = len(SHAPES) + self.open_names.index(name)
                    prob = float(np.clip(1.0 - ndist / (2.0 * self.novel_th), 0.05, 1.0))
                yaw, yaw4 = self._yaw_from(F_lage), self._yaw4_from(F_lage)
            out.append({"shape": name, "id": k, "prob": prob,
                        "pos": ctr, "grasp_xy": grasp, "grasp_dense": grasp, "grasp_yaw": 0.0,
                        "yaw": yaw, "yaw4": yaw4, "area": float(comp.sum()),
                        "chroma": crgb / csum if csum > 1e-6 else crgb,
                        "px": np.array([cxs.mean(), cys.mean()]),
                        "grasp_cands": [], "wpx": None, "desc": desc,
                        "dicke": _dicke, "span": _span,        # s. oben: Groesse des GETRENNTEN Teils
                        "split": True})                        # marks a colour-split detection (diagnostics)
        return out

    def desc_embed(self, desc):
        """Compact OPEN-WORLD shape embedding from the raw |F| descriptor: standardise by the training
        stats (fmu/fsd), then average over the rings per harmonic -> NH dims.  Unlike a class one-hot this
        exists for ANY object -- known or novel -- so downstream models (e.g. the act23 world model) can
        condition on the FORM ITSELF and generalise to shapes that have no class slot."""
        z = (np.asarray(desc, float) - self.fmu) / self.fsd
        return z.reshape(len(self.RW), self.NH).mean(0)

    def select(self, sim, shape_cmd, min_area=40):
        """Command CONDITIONED on FORM (the colour-free analogue of the colour SelectionHead): among ALL
        objects detected by perceive_all, return the detection whose SHAPE matches the command -- its world
        xy + the full detection -- or None if no such shape is present.  shape_cmd: a class NAME (trained
        'cube'/'L'/'U' OR a self-labelled open class like 'neu-1') or its index into all_names(); if
        several match (e.g. two cubes) the most confident is returned.  Publishes selected_xy."""
        nm = self.all_names()[shape_cmd] if isinstance(shape_cmd, (int, np.integer)) else shape_cmd
        matches = [d for d in self.perceive_all(sim, min_area=min_area) if d["shape"] == nm]
        if not matches:
            self._sel = None; self.set_out("selected_xy", None); return None
        best = max(matches, key=lambda d: d["prob"])
        self._sel = best; self.set_out("selected_xy", best["pos"])
        return best

    def step(self):
        pass
