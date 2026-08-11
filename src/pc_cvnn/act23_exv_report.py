"""Auswertung eines ACT23_EXV-Laufs: wieviel der Ergebnis-Streuung sitzt in der AUSFUEHRUNG?

Der Lauf (pc_act23.py mit ACT23_EXV=M) faehrt jede Szene M-mal.  Objektpose, Ziel und die
Situationsmerkmale sind dabei bitgleich und das Lernen ist eingefroren -- die getroffene WAHL ist
damit praktisch fix (NICHT bitgleich: das Wrist-Gitter ist armrelativ, s. Kontrolle unten).  Was
innerhalb einer Szene streut, ist die Ausfuehrung: der Arm startet dort, wo drive_home ihn
gelassen hat, und die Fovea traegt ihren Zustand mit.

Ausgegeben wird die Varianzzerlegung des Erfolgs (0/1) und des Abstands (mm):

    innerhalb  = mittlere Streuung der M Wiederholungen EINER Szene   -> Ausfuehrung
    zwischen   = Streuung der Szenen-MITTELWERTE                      -> Situation + Wahl
    ICC        = zwischen / (zwischen + innerhalb)                    -> Anteil, den die Szene erklaert

ICC nahe 1: dieselbe Szene liefert dasselbe Ergebnis, die Ausfuehrung ist unschuldig und der
Hebel liegt bei Wahrnehmung/Wahl.  ICC nahe 0: die Szene sagt nichts vorher, weil die Bahn
entscheidet -- dann ist jedes weitere Merkmal im Welt-Modell vergebliche Muehe.

KONTROLLE (wird mitgeprueft): wie stark weicht der VOLLE Aktionsvektor ([EXV-Aktion]) zwischen
den Wiederholungen ab -- in Grad, Millimetern, Grip?  Ein Rest bleibt bauartbedingt (armrelatives
Wrist-Gitter, gemessen ~0.1 Grad).  Wird die Abweichung gross, misst die Zerlegung Wahl PLUS
Ausfuehrung statt der Ausfuehrung allein, und der Report sagt das.

    python src/pc_cvnn/act23_exv_report.py log/pc_act23_....txt        # ein Lauf, volle Zerlegung
    python src/pc_cvnn/act23_exv_report.py log/a.txt log/b.txt ...     # Dosis-Wirkung ueber Jitter
"""
import os
import re
import sys

import numpy as np

RE_EXV = re.compile(r"\[EXV\] Szene (\d+) \(([^)]*)\):\s+([01]+)\s+(\d+)/(\d+)")
RE_HEAD = re.compile(r"\[Auto (\d+)\](?: W(\d+))? (.+?) \.\.\.\s*$")
RE_RES = re.compile(r"\[Auto (\d+)\] (GELIEFERT|NICHT geliefert)\s+\|\s+Abstand (-?\d+) mm")
RE_ACT = re.compile(r"\[Kredit\].*Wrist (\d+) Grad, Grip ([\d.]+)")
RE_AVEC = re.compile(r"\[EXV-Aktion\] ([-+0-9. ]+)")     # VOLLER Aktionsvektor -- die scharfe Kontrolle
RE_GRIP = re.compile(r"\[Greifpunkt\]")


def parse(path):
    """-> Liste von Szenen, jede eine Liste von Episoden-dicts.

    Zeilenreihenfolge je Episode: Kopf '[Auto n] Wk <Label> ...', dann irgendwann '[Kredit] ...
    Wrist X Grad, Grip Y' (die gefahrene Aktion), dann '[Auto n] GELIEFERT | Abstand Z mm'.  Die
    Episode wird an der ERGEBNIS-Zeile abgelegt -- die '[EXV] Szene'-Zeile kommt nur einmal je
    Szene und taugt deshalb nur als Szenengrenze, nicht als Episodengrenze.
    """
    scenes, cur, pending = [], [], {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if (m := RE_HEAD.search(line)):
                pending = {"label": m.group(3), "rep": m.group(2)}
            elif (m := RE_AVEC.search(line)):
                pending["avec"] = tuple(round(float(v), 4) for v in m.group(1).split())
            elif (m := RE_ACT.search(line)):
                pending["wrist"] = float(m.group(1)); pending["grip"] = float(m.group(2))
            elif (m := RE_RES.search(line)):
                pending["ok"] = m.group(2) == "GELIEFERT"
                pending["mm"] = float(m.group(3))
                cur.append(pending); pending = {}
            elif "[EXV] Szene" in line and cur:            # Szenengrenze
                scenes.append(cur); cur = []
    if cur:
        scenes.append(cur)
    return [s for s in scenes if s]


def decompose(vals):
    """vals: Liste gleich langer (oder ungleich langer) Wiederholungsgruppen -> (innerhalb, zwischen, ICC)."""
    groups = [np.asarray(g, float) for g in vals if len(g) >= 2]
    if len(groups) < 2:
        return float("nan"), float("nan"), float("nan")
    # Varianzkomponenten nach der Einweg-ANOVA (ungleiche Gruppengroessen erlaubt).
    ni = np.array([len(g) for g in groups], float)
    mi = np.array([g.mean() for g in groups])
    N, k = ni.sum(), len(groups)
    gm = float(np.concatenate(groups).mean())
    ssw = float(sum(((g - g.mean()) ** 2).sum() for g in groups))
    ssb = float((ni * (mi - gm) ** 2).sum())
    msw = ssw / max(1.0, N - k)                     # Varianz INNERHALB der Szene = Ausfuehrung
    msb = ssb / max(1.0, k - 1)
    n0 = (N - (ni ** 2).sum() / N) / (k - 1)
    vb = max(0.0, (msb - msw) / n0)                 # Varianz ZWISCHEN den Szenen
    icc = vb / (vb + msw) if (vb + msw) > 0 else float("nan")
    return np.sqrt(msw), np.sqrt(vb), icc


def main(path):
    scenes = parse(path)
    if not scenes:
        raise SystemExit(f"keine EXV-Szenen in {path} gefunden")
    print(f"  {os.path.basename(path)}: {len(scenes)} Szenen, "
          f"{sum(len(s) for s in scenes)} Episoden\n")

    # --- Kontrolle: war die Wahl ueber die Wiederholungen wirklich fix? -----------------------
    # Die Wahl ist NICHT exakt fix, und das ist kein Fehler, sondern Bauart: mit ACT23_WRIST_REL=1
    # wird das Wrist-Gitter ARMRELATIV aufgespannt (grid = w0 + linspace).  Der Arm steht zwischen
    # zwei Wiederholungen nie bitgleich (arm_reset=False, erst recht unter Jitter), also verschiebt
    # sich w0 und mit ihm der gewaehlte Wrist -- im Rauchtest um 0.1 Grad.
    # Ein binaeres "identisch ja/nein" wuerde 0.1 Grad wie einen echten Aktionswechsel behandeln.
    # Berichtet wird deshalb die GROESSE der Abweichung in den interpretierbaren Einheiten; erst
    # wenn die gross wird, misst die Zerlegung Wahl PLUS Ausfuehrung statt der Ausfuehrung allein.
    def _spread(sc):
        """max. Abweichung innerhalb einer Szene -> (Wrist-Grad, Offset-mm, Grip, Neigungs-Grad)."""
        av = [e["avec"] for e in sc if e.get("avec") and len(e["avec"]) >= 6]
        if len(av) < 2:
            return None
        A = np.asarray(av, float)
        w = np.degrees(np.arctan2(A[:, 3], A[:, 2]) / 2.0) % 180.0
        dw = max(min(abs(a - b), 180.0 - abs(a - b)) for a in w for b in w)   # zyklisch mod 180
        off = np.hypot(A[:, 0], A[:, 1]) * 1000.0
        doff = float(np.max([np.linalg.norm(A[i, :2] - A[j, :2]) for i in range(len(A))
                             for j in range(len(A))]) * 1000.0)
        dgrip = float(A[:, 4].max() - A[:, 4].min())
        dtilt = (float(np.ptp(np.degrees(np.arctan2(A[:, 7], A[:, 6])))) if A.shape[1] >= 8 else 0.0)
        return dw, doff, dgrip, dtilt, float(off.mean())

    sp = [x for x in (_spread(sc) for sc in scenes) if x is not None]
    if sp:
        S = np.asarray(sp, float)
        print(f"  [Kontrolle] Aktions-Abweichung innerhalb einer Szene ({len(sp)} Szenen, Median | max):")
        print(f"      Wrist  {np.median(S[:, 0]):5.2f} | {S[:, 0].max():5.2f} Grad     "
              f"Offset {np.median(S[:, 1]):5.2f} | {S[:, 1].max():5.2f} mm")
        print(f"      Grip   {np.median(S[:, 2]):5.3f} | {S[:, 2].max():5.3f}          "
              f"Neigung {np.median(S[:, 3]):5.2f} | {S[:, 3].max():5.2f} Grad")
        if S[:, 0].max() > 5.0 or S[:, 1].max() > 2.0:
            print("      ACHTUNG: das ist keine Rundung mehr -- die Zerlegung misst dann Wahl PLUS "
                  "Ausfuehrung.")
        else:
            print("      -> vernachlaessigbar (armrelatives Wrist-Gitter); die Wahl gilt als fix.")
    else:
        n_var = n_chk = 0
        for sc in scenes:
            acts = {(e.get("wrist"), e.get("grip")) for e in sc if e.get("wrist") is not None}
            if acts:
                n_chk += 1; n_var += len(acts) > 1
        if n_chk:
            print(f"  [Kontrolle] altes Log ohne [EXV-Aktion]: Wrist/Grip identisch in "
                  f"{n_chk - n_var}/{n_chk} Szenen (Offset und Neigung UNGEPRUEFT)")

    ok_g = [[1.0 if e["ok"] else 0.0 for e in s] for s in scenes]
    mm_g = [[e["mm"] for e in s] for s in scenes]

    for name, groups, unit in (("Erfolg", ok_g, ""), ("Abstand", mm_g, " mm")):
        sw, sb, icc = decompose(groups)
        print(f"\n  {name}:")
        print(f"    Streuung INNERHALB der Szene (Ausfuehrung) : {sw:.3f}{unit}")
        print(f"    Streuung ZWISCHEN den Szenen (Situation)   : {sb:.3f}{unit}")
        print(f"    ICC (Anteil, den die Szene erklaert)       : {icc:.2f}")

    # --- wie oft kippt eine Szene ueberhaupt? -------------------------------------------------
    mixed = [s for s in scenes if len({e["ok"] for e in s}) > 1]
    full = [s for s in scenes if all(e["ok"] for e in s)]
    none = [s for s in scenes if not any(e["ok"] for e in s)]
    print(f"\n  Szenen-Ausgang: {len(full)} immer geliefert, {len(none)} nie, "
          f"{len(mixed)} GEMISCHT ({100.0 * len(mixed) / len(scenes):.0f}%)")
    sp = [max(e["mm"] for e in s) - min(e["mm"] for e in s) for s in scenes if len(s) >= 2]
    if sp:
        print(f"  Abstands-Spanne INNERHALB einer Szene (alle {len(sp)} Szenen): "
              f"Median {np.median(sp):.0f} mm, max {np.max(sp):.0f} mm")


RE_JIT = re.compile(r"Startpose-Jitter ([\d.]+) rad")


def compare(paths):
    """DOSIS-WIRKUNG: mehrere Laeufe (verschiedene ACT23_EXV_JITTER) in einer Tabelle.

    Ein einzelner Lauf sagt nur "wiederholt es sich".  Erst die Reihe ueber wachsenden Jitter sagt,
    WIE EMPFINDLICH der Ausgang gegen die Startpose ist -- und damit, ob eine ruhigere Startpose
    ueberhaupt ein Hebel waere."""
    print(f"  {'Jitter':>10}  {'Szenen':>6}  {'Erfolg':>7}  {'innerh.':>8}  {'zwisch.':>8}  "
          f"{'ICC':>5}  {'gemischt':>8}")
    for p in paths:
        scenes = parse(p)
        if not scenes:
            print(f"  {os.path.basename(p):>10}  -- keine EXV-Szenen"); continue
        jit = "0.000"
        with open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if (m := RE_JIT.search(line)):
                    jit = m.group(1); break
        ok_g = [[1.0 if e["ok"] else 0.0 for e in s] for s in scenes]
        sw, sb, icc = decompose(ok_g)
        rate = np.mean([e["ok"] for s in scenes for e in s])
        mixed = sum(len({e["ok"] for e in s}) > 1 for s in scenes)
        print(f"  {jit:>10}  {len(scenes):>6}  {rate:>6.0%}  {sw:>8.3f}  {sb:>8.3f}  "
              f"{icc:>5.2f}  {mixed / len(scenes):>7.0%}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if len(sys.argv) > 2:
        compare(sys.argv[1:])
    else:
        main(sys.argv[1])
