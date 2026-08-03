"""ModuleViz — ein EIGENES Fenster, das die PCModule, ihre Verdrahtung und ihr Zusammenspiel zeigt.

Zwei Hälften:

  OBEN  der MODUL-GRAPH.  Jedes Kästchen ist ein ArmModule, darunter steht sein aktueller Wert.
        Pfeile sind die tatsächliche Verdrahtung — und zwar in drei Sorten, damit die LÜCKEN
        genauso sichtbar sind wie die Verbindungen:
          durchgezogen  = verdrahtet, Daten fliessen
          gestrichelt   = Information EXISTIERT im System, ist aber nicht angeschlossen
          gepunktet     = Modul vorhanden, im act23-Lauf aber nicht aktiv
        Die gestrichelte Kante ist der verbliebene gemessene Befund: das Koerpermodell kennt die
        Armstellung, das Welt-Modell erfaehrt sie nie.  (Zwei fruehere Luecken sind geschlossen --
        Nachbarobjekte und der Fovea-Zustand sind seit 2026-08-02/03 Situations-Features.)

  UNTEN vier Kurvenpaare, je Episode ein Punkt.  Bewusst gepaart, damit man ZUSAMMENSPIEL liest
        statt Einzelwerte:
          Wahrnehmung : Fovea-Surprise  +  Koerpermodell-Fehler (mm)
          Griffwahl   : Welt-Modell mu  +  sigma der gewaehlten Aktion
          Ausfuehrung : Policy-vs-Teacher-Divergenz (mm)  +  Ablage-Abstand (mm)
          Neigung     : gewaehlte Neigung  +  natuerliche Haltung (Grad)

Aufruf: ACT23_MODVIZ=1 beim GUI-Lauf.  Das Fenster ist rein passiv (nur Anzeige), kostet einen
Redraw je REDRAW_EVERY Episoden und beeinflusst den Lauf nicht.
"""
from __future__ import annotations

import os

import numpy as np

REDRAW_EVERY = int(os.environ.get("ACT23_MODVIZ_EVERY", "1"))
WINDOW = int(os.environ.get("ACT23_MODVIZ_WINDOW", "120"))       # Episoden im Sichtfenster

# (Name, Spalte, Zeile, Kurzbeschreibung des Beitrags)
_NODES = [
    ("VisualCortex",   0, 2.6, "Blick / Fovea"),
    ("ShapeClassifier", 0, 1.3, "Form + Greifpunkt"),
    ("ColourOpenSet",  0, 0.0, "Farbklassen"),
    ("BodyModel",      1, 2.6, "Hand + Kinematik"),
    ("WorldModel",     1, 1.3, "Wrist/Grip/Neigung"),
    ("SelfEval",       1, 0.0, "Selbst-Urteil"),
    ("RuntimePolicy",  2, 2.6, "Choreographie"),
    ("LatentGoal",     2, 1.3, "Platzier-Ziel"),
    ("Curiosity",      2, 0.0, "was wird geuebt"),
    ("LatentDynamics", 3, 1.3, "Uebergangsmodell"),
]
# (von, nach, art)   art: "wired" | "missing" | "idle"
_EDGES = [
    ("ColourOpenSet", "ShapeClassifier", "wired"),
    ("ShapeClassifier", "VisualCortex", "wired"),
    ("ShapeClassifier", "WorldModel", "wired"),
    ("VisualCortex", "BodyModel", "wired"),
    ("BodyModel", "RuntimePolicy", "wired"),
    ("WorldModel", "RuntimePolicy", "wired"),
    ("RuntimePolicy", "SelfEval", "wired"),
    ("SelfEval", "WorldModel", "wired"),
    ("LatentGoal", "RuntimePolicy", "wired"),
    ("Curiosity", "LatentGoal", "wired"),
    ("LatentDynamics", "LatentGoal", "idle"),
    ("VisualCortex", "WorldModel", "wired"),       # seit 2026-08-03: Fovea-Zustand (Surprise + |top|) IST
    #   ein Situations-Feature.  Vorher fehlte diese Kante -- vom Nutzer hier in der Grafik entdeckt.
    ("BodyModel", "WorldModel", "missing"),        # Armstellung/Klauen-Neigung erreicht das Modell nie
]
#   Die frueher gestrichelte Kante ShapeClassifier -> SelfEval (Nachbarobjekte gesehen, aber nicht
#   weitergegeben) ist geschlossen: die Nachbar-Information laeuft jetzt ueber ShapeClassifier ->
#   WorldModel mit (5 Dim, mit Gueltigkeits-Flag).
_STYLE = {"wired":   dict(ls="-",  color="#5fd7ff", lw=1.6, alpha=0.95),
          "missing": dict(ls="--", color="#ff7b6b", lw=1.4, alpha=0.9),
          "idle":    dict(ls=":",  color="#7a7a8a", lw=1.2, alpha=0.7)}


class ModuleViz:
    """Passives Anzeigefenster; `push(**werte)` einmal pro Episode aufrufen."""

    KEYS = ("fovea", "body_mm", "wm_mu", "wm_sd", "pol_div_mm", "place_mm", "tilt_deg", "nat_deg")

    def __init__(self, title="act23 — PCModule und ihr Zusammenspiel"):
        import matplotlib.pyplot as plt
        self.plt = plt
        plt.ion()
        self.fig = plt.figure(figsize=(11.5, 8.4))
        self.fig.patch.set_facecolor("#0e0e12")
        self.fig.suptitle(title, color="w", fontsize=11)
        gs = self.fig.add_gridspec(3, 2, height_ratios=[1.25, 1.0, 1.0], hspace=0.42, wspace=0.22)
        self.axG = self.fig.add_subplot(gs[0, :])
        self.ax = [self.fig.add_subplot(gs[1, 0]), self.fig.add_subplot(gs[1, 1]),
                   self.fig.add_subplot(gs[2, 0]), self.fig.add_subplot(gs[2, 1])]
        for a in self.ax:
            a.set_facecolor("#15151c")
            a.tick_params(colors="#9a9aa8", labelsize=7)
            for sp in a.spines.values():
                sp.set_color("#33333f")
        self.hist = {k: [] for k in self.KEYS}
        self.t = []
        self._k = 0
        self._pos = {n: (c, r) for n, c, r, _d in _NODES}
        self._draw_graph({})

    # ---------------------------------------------------------------- Graph
    def _draw_graph(self, vals):
        ax = self.axG
        ax.clear(); ax.set_facecolor("#15151c"); ax.axis("off")
        ax.set_xlim(-0.62, 4.55); ax.set_ylim(-0.55, 3.35)
        BW, BH = 0.86, 0.46                                    # Kaestchenbreite/-hoehe
        for a, b, kind in _EDGES:
            (x1, y1), (x2, y2) = self._pos[a], self._pos[b]
            ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                        arrowprops=dict(arrowstyle="-|>", shrinkA=17, shrinkB=17,
                                        connectionstyle="arc3,rad=0.06", **_STYLE[kind]))
        for name, c, r, desc in _NODES:
            v = vals.get(name)
            idle = name in ("LatentDynamics",)
            ax.add_patch(self.plt.Rectangle((c - BW / 2, r - BH / 2), BW, BH,
                                            facecolor="#1e1e28" if not idle else "#191920",
                                            edgecolor="#4a4a5c", lw=1.0, zorder=3))
            # nur Name + aktueller Wert: drei Textzeilen passen bei dieser Kaestchenhoehe nicht
            # lesbar hinein (die Kurzbeschreibung steht im Modul-Docstring).
            ax.text(c, r + 0.095, name, ha="center", va="center", color="w", fontsize=8.0,
                    zorder=4, fontweight="bold")
            ax.text(c, r - 0.105, v if v else desc, ha="center", va="center",
                    color="#7fe08a" if v else "#8a8a9a", fontsize=7.0 if v else 6.3, zorder=4)
        leg = [("verdrahtet", "wired"), ("Info da, NICHT angeschlossen", "missing"),
               ("Modul inaktiv", "idle")]
        for i, (lab, kind) in enumerate(leg):
            y = 3.15 - i * 0.26
            ax.plot([3.62, 3.86], [y, y], **_STYLE[kind])
            ax.text(3.92, y, lab, color="#9a9aa8", fontsize=6.5, va="center")

    # ---------------------------------------------------------------- Kurven
    def push(self, **vals):
        self._k += 1
        self.t.append(self._k)
        for k in self.KEYS:
            v = vals.get(k)
            self.hist[k].append(float(v) if v is not None else np.nan)
        if self._k % REDRAW_EVERY == 0:
            self.redraw(vals)

    def _plot(self, ax, title, series, ylab=""):
        ax.clear(); ax.set_facecolor("#15151c")
        ax.tick_params(colors="#9a9aa8", labelsize=7)
        for sp in ax.spines.values():
            sp.set_color("#33333f")
        t = self.t[-WINDOW:]
        for key, lab, col in series:
            y = self.hist[key][-WINDOW:]
            if np.all(np.isnan(y)):
                continue
            ax.plot(t, y, color=col, lw=1.3, label=lab)
        ax.set_title(title, color="w", fontsize=8.4, pad=4)
        if ylab:
            ax.set_ylabel(ylab, color="#9a9aa8", fontsize=7)
        lg = ax.legend(fontsize=6.4, loc="upper left", framealpha=0.25, labelcolor="#c8c8d4")
        if lg:
            lg.get_frame().set_facecolor("#1e1e28"); lg.get_frame().set_edgecolor("#33333f")

    def redraw(self, vals=None):
        cur = {}
        if self.hist["fovea"]:
            def last(k, fmt, scale=1.0):
                v = self.hist[k][-1]
                return "—" if (v is None or np.isnan(v)) else fmt.format(v * scale)
            cur = {"VisualCortex": last("fovea", "{:.3f}"),
                   "BodyModel": last("body_mm", "{:.1f} mm"),
                   "WorldModel": f"mu {last('wm_mu','{:.2f}')} / s {last('wm_sd','{:.2f}')}",
                   "RuntimePolicy": last("pol_div_mm", "{:.0f} mm"),
                   "SelfEval": last("place_mm", "{:.0f} mm")}
        self._draw_graph(cur)
        self._plot(self.ax[0], "Wahrnehmung: Fovea-Surprise + Koerpermodell",
                   [("fovea", "Fovea sensor_error", "#5fd7ff"), ("body_mm", "Koerper (mm)", "#ffd166")])
        self._plot(self.ax[1], "Griffwahl: Welt-Modell mu und sigma",
                   [("wm_mu", "mu (erwartete Guete)", "#7fe08a"), ("wm_sd", "sigma (Unsicherheit)", "#ff7b6b")])
        self._plot(self.ax[2], "Ausfuehrung: Policy-vs-Teacher und Ablage",
                   [("pol_div_mm", "|Policy-Teacher| mm", "#c792ea"), ("place_mm", "Ablage-Abstand mm", "#ffd166")])
        self._plot(self.ax[3], "Neigung: gewaehlt vs natuerliche Haltung",
                   [("tilt_deg", "gewaehlt (Grad)", "#5fd7ff"), ("nat_deg", "natuerlich (Grad)", "#8a8a9a")])
        try:
            self.fig.canvas.draw_idle(); self.fig.canvas.flush_events()
        except Exception:
            pass
