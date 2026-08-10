"""RunViz — der LERNFORTSCHRITT ueber ganze Laeufe hinweg, mit den vorherigen Laeufen im Hintergrund.

Die ModulViz-Kurven zeigen das Zusammenspiel INNERHALB eines Laufs.  Was dort fehlt, ist die
Frage, die nach Wochen zaehlt: bewegt sich ueberhaupt etwas von Lauf zu Lauf?  Genau dafuer ist
dieses Fenster -- jede Kennzahl als geglaettete Kurve ueber die Episoden, der aktuelle Lauf
kraeftig, die vorherigen mit abnehmender Helligkeit darunter.

DATENQUELLE: die LOGS selbst.  Es gibt bewusst KEINE zweite Aufzeichnung, die mitgepflegt werden
muesste -- jede Kennzahl steht schon im Log, und damit reicht die Historie rueckwirkend ueber
alle bisherigen Laeufe.  Geparste Laeufe landen als JSON in log/.runviz_cache/ (Schluessel =
Dateiname + Groesse + mtime), damit wiederholtes Oeffnen schnell ist.

DARSTELLUNG, umschaltbar (der Nutzer war sich unsicher, was sich besser liest):
  overlay  alle Laeufe ab Episode 0 uebereinander -- zeigt, ob ein Lauf ANDERS verlaeuft
  concat   die Laeufe hintereinander auf einer durchgehenden Achse -- zeigt die Entwicklung
           ueber die gesamte Projektzeit
Die X-Achse richtet sich im overlay-Modus nach dem laengsten Lauf.

Aufruf:
    python src/pc_cvnn/run_history.py                     # letzte 6 Laeufe, overlay
    python src/pc_cvnn/run_history.py --mode concat
    python src/pc_cvnn/run_history.py --runs 10 --window 40
    python src/pc_cvnn/run_history.py --watch 60          # alle 60 s neu einlesen (laufender Lauf)
    python src/pc_cvnn/run_history.py --png bild.png      # ohne Fenster in eine Datei
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import time

import numpy as np

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "log")
CACHE_DIR = os.path.join(LOG_DIR, ".runviz_cache")
MIN_EPISODES = 20                      # kuerzere Laeufe sind Rauchtests, nicht Lernlaeufe

# --------------------------------------------------------------------------- Parser
_RE = {
    "start":  re.compile(r"\[Auto (\d+)\] ([^|]+)\|.*Greifen"),
    "result": re.compile(r"\[Auto (\d+)\] (GELIEFERT|NICHT geliefert)\s*\|\s*Abstand (\d+) mm"),
    "grip":   re.compile(r"\[Griffdruck\] zufassen\s+([\d.]+) \| heben\s+([\d.]+) \(min ([\d.]+)\)"
                         r" \| tragen\s+([\d.]+)"),
    "fovea":  re.compile(r"\|Netz-Detektor\| mittel ([\d.]+) mm"),
    "shadow": re.compile(r"\|Netz-Teacher\| (\d+) mm"),
    "sigma":  re.compile(r"\[Neigung\] \w+: gewaehlt \d+ Grad \(natuerlich \d+, r=(\d+)cm\), sigma ([\d.]+)"),
    "credit": re.compile(r"\[Kredit\] (.+?) (?:->|--)"),
    "gripv":  re.compile(r"Label Selbst: Wrist \d+ Grad, Grip ([\d.]+)"),
    "time":   re.compile(r"\[Zeit\] gesamt ([\d.]+)s"),
}


def parse_log(path):
    """Ein Log -> Liste von Episoden-Datensaetzen (ein dict je Episode, in Reihenfolge)."""
    ep, cur = {}, None
    for line in open(path, encoding="utf-8", errors="replace"):
        m = _RE["result"].search(line)
        if m:
            e = int(m.group(1))
            ep.setdefault(e, {})["delivered"] = float(m.group(2) == "GELIEFERT")
            ep[e]["dist_mm"] = float(m.group(3))
            continue
        m = _RE["start"].search(line)
        if m:
            cur = int(m.group(1)); ep.setdefault(cur, {})["object"] = m.group(2).strip()
            continue
        if cur is None:
            continue
        d = ep.setdefault(cur, {})
        m = _RE["grip"].search(line)
        if m:
            d["close_n"], d["lift_n"] = float(m.group(1)), float(m.group(2))
            d["lift_min_n"], d["carry_n"] = float(m.group(3)), float(m.group(4))
            d["held"] = float(d["lift_n"] > 0)
        m = _RE["fovea"].search(line)
        if m:
            d["fovea_mm"] = float(m.group(1))
        m = _RE["shadow"].search(line)
        if m:
            d["shadow_mm"] = float(m.group(1))
        m = _RE["sigma"].search(line)
        if m:
            d["radius_cm"], d["wm_sigma"] = float(m.group(1)), float(m.group(2))
        m = _RE["credit"].search(line)
        if m:
            d["credit"] = m.group(1).strip()
        m = _RE["gripv"].search(line)
        if m:
            d["grip_cmd"] = float(m.group(1))
        m = _RE["time"].search(line)
        if m:
            d["secs"] = float(m.group(1))
    out = []
    for e in sorted(ep):
        r = ep[e]
        if "delivered" not in r:           # abgebrochene letzte Episode
            continue
        r["episode"] = e
        r["abstained"] = float("credit" not in r)
        out.append(r)
    return out


def _cache_key(path):
    st = os.stat(path)
    return hashlib.md5(f"{os.path.basename(path)}|{st.st_size}|{int(st.st_mtime)}".encode()).hexdigest()


def load_runs(n_runs=6, min_episodes=MIN_EPISODES):
    """Die letzten `n_runs` Laeufe als [(Name, Datensaetze), ...], aeltester zuerst."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(LOG_DIR, "pc_act23_*.txt")), key=os.path.getmtime)
    runs = []
    for f in reversed(files):
        cf = os.path.join(CACHE_DIR, _cache_key(f) + ".json")
        if os.path.exists(cf):
            recs = json.load(open(cf, encoding="utf-8"))
        else:
            recs = parse_log(f)
            growing = (time.time() - os.path.getmtime(f)) < 300     # noch beschrieben -> NICHT cachen:
            #   der Schluessel enthaelt Groesse und mtime, ein laufendes Log wuerde bei jedem
            #   Einlesen eine neue Cache-Datei anlegen (Muell, der nie wieder gelesen wird)
            if len(recs) >= min_episodes and not growing:
                json.dump(recs, open(cf, "w", encoding="utf-8"))
        if len(recs) < min_episodes:
            continue
        runs.append((os.path.basename(f)[9:-4], recs))
        if len(runs) >= n_runs:
            break
    return list(reversed(runs))


# --------------------------------------------------------------------------- Kennzahlen
#  key -> (Feld, Beschriftung, Panel-Index, als RATE glaetten?)
METRICS = [
    ("delivered",  "Lieferquote",            0, True),
    ("held",       "haelt beim Heben",       0, True),
    ("abstained",  "Enthaltung",             0, True),
    ("close_n",    "Zufassdruck (N)",        1, False),
    ("lift_n",     "Druck beim Heben (N)",   1, False),
    ("carry_n",    "Druck beim Tragen (N)",  1, False),
    ("fovea_mm",   "|Netz-Detektor| (mm)",   2, False),
    ("shadow_mm",  "|Netz-Teacher| (mm)",    2, False),
    ("dist_mm",    "Endabstand (mm)",        3, False),
    ("wm_sigma",   "Welt-Modell sigma",      4, False),
    ("grip_cmd",   "gewaehlte Griffweite",   4, False),
    ("secs",       "Episodendauer (s)",      5, False),
]
PANELS = ["Ergebnis (Anteile)", "Griffkraft", "Wahrnehmung / Policy-Naehe",
          "Ablagegenauigkeit", "Entscheidung", "Rechenzeit"]


def series(recs, key, window):
    """Geglaettete Kurve (gleitendes Mittel) + die Episoden-Indizes dazu."""
    x = [r["episode"] for r in recs if key in r]
    y = [r[key] for r in recs if key in r]
    if len(y) < 3:
        return np.array([]), np.array([])
    y = np.asarray(y, float); x = np.asarray(x, float)
    w = max(3, min(int(window), len(y)))
    k = np.ones(w) / w
    ys = np.convolve(y, k, mode="valid")
    xs = x[w - 1:]
    return xs, ys


# --------------------------------------------------------------------------- Fenster
class RunViz:
    def __init__(self, n_runs=6, window=25, mode="overlay", figsize=(13.5, 8.6)):
        import matplotlib.pyplot as plt
        self.plt = plt
        self.n_runs, self.window, self.mode = n_runs, window, mode
        self.fig, axes = plt.subplots(3, 2, figsize=figsize)
        self.ax = axes.ravel()
        self.fig.patch.set_facecolor("#0e0e12")
        self.fig.canvas.manager.set_window_title("act23 — Lernfortschritt ueber Laeufe")
        # Tastatur: m = Modus umschalten, +/- = Glaettungsfenster, r = neu einlesen
        self.fig.canvas.mpl_connect("key_press_event", self._key)
        self.draw()

    def _key(self, ev):
        if ev.key == "m":
            self.mode = "concat" if self.mode == "overlay" else "overlay"
        elif ev.key in ("+", "="):
            self.window = min(200, int(self.window * 1.5) + 1)
        elif ev.key == "-":
            self.window = max(3, int(self.window / 1.5))
        elif ev.key != "r":
            return
        self.draw()

    def draw(self):
        runs = load_runs(self.n_runs)
        if not runs:
            return
        n = len(runs)
        # Farbe je Kennzahl, HELLIGKEIT je Alter: der neueste Lauf voll, aeltere blasser
        cols = ["#5fd7ff", "#7fe08a", "#ffd166", "#ff7b6b", "#c792ea", "#9aa0b4"]
        for a, title in zip(self.ax, PANELS):
            a.clear(); a.set_facecolor("#15151c")
            a.tick_params(colors="#9a9aa8", labelsize=7)
            for sp in a.spines.values():
                sp.set_color("#33333f")
            a.set_title(title, color="w", fontsize=9, pad=4)
            a.grid(True, color="#22222c", lw=0.6)
        offset = 0
        xmax = 0
        for ri, (name, recs) in enumerate(runs):
            age = n - 1 - ri                                    # 0 = neuester
            alpha = 1.0 if age == 0 else max(0.13, 0.62 * (0.62 ** (age - 1)))
            lw = 1.9 if age == 0 else 1.1
            ci = 0
            for key, label, pi, _rate in METRICS:
                xs, ys = series(recs, key, self.window)
                if len(xs) == 0:
                    ci += 1
                    continue
                xp = xs + (offset if self.mode == "concat" else 0)
                self.ax[pi].plot(xp, ys, color=cols[ci % len(cols)], lw=lw, alpha=alpha,
                                 label=(label if age == 0 else None))
                xmax = max(xmax, float(xp[-1]))
                ci += 1
            if self.mode == "concat":
                for a in self.ax:
                    a.axvline(offset, color="#3a3a48", lw=0.8, ls=":")
                offset += (recs[-1]["episode"] + 1)
        for a in self.ax:
            a.set_xlim(0, max(xmax * 1.01, 1))
            lg = a.legend(fontsize=6.6, loc="upper left", framealpha=0.25, labelcolor="#c8c8d4", ncol=2)
            if lg:
                lg.get_frame().set_facecolor("#1e1e28"); lg.get_frame().set_edgecolor("#33333f")
        for a in self.ax[-2:]:
            a.set_xlabel("Episode" + ("" if self.mode == "overlay" else " (fortlaufend)"),
                         color="#9a9aa8", fontsize=7.5)
        sub = " | ".join(f"{'>' if i == len(runs) - 1 else ' '}{nm} ({len(rc)} Ep)"
                         for i, (nm, rc) in enumerate(runs))
        self.fig.suptitle(f"Lernfortschritt — {self.mode}, Glaettung {self.window} Episoden"
                          f"   [m] Modus  [+/-] Glaettung  [r] neu lesen\n{sub}",
                          color="w", fontsize=8.5)
        self.fig.tight_layout(rect=(0, 0, 1, 0.93))
        try:
            self.fig.canvas.draw_idle(); self.fig.canvas.flush_events()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs", type=int, default=6)
    ap.add_argument("--window", type=int, default=25)
    ap.add_argument("--mode", choices=("overlay", "concat"), default="overlay")
    ap.add_argument("--watch", type=float, default=0.0, help="Sekunden zwischen Neu-Einlesen (0 = aus)")
    ap.add_argument("--png", default="", help="statt Fenster in diese Datei schreiben")
    a = ap.parse_args()
    if a.png:
        import matplotlib
        matplotlib.use("Agg")
    v = RunViz(n_runs=a.runs, window=a.window, mode=a.mode)
    if a.png:
        v.fig.savefig(a.png, dpi=110, facecolor=v.fig.get_facecolor())
        print(f"geschrieben: {a.png}")
        return
    import matplotlib.pyplot as plt
    if a.watch > 0:
        # TIMER statt time.sleep: eine Schlafschleife BLOCKIERT die GUI-Ereignisschleife, das
        # Fenster reagiert dann waehrend der ganzen Wartezeit nicht und laesst sich nicht einmal
        # in den Vordergrund holen (vom Nutzer beobachtet -- derselbe Mechanismus wie bei der
        # eingefrorenen Kamera-Anzeige).  Der Timer wird von der Ereignisschleife selbst getaktet.
        v.timer = v.fig.canvas.new_timer(interval=int(a.watch * 1000))
        v.timer.add_callback(v.draw)
        v.timer.start()
    plt.show()


if __name__ == "__main__":
    main()
