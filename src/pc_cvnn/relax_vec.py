"""VEKTORISIERTE RELAXATION -- dieselbe Rechnung, gebuendelt statt einzeln.

Anlass (2026-08-23, gemessen).  Ein Zeitprofil ueber 8 headless-Episoden von act23:

    PC-Netz step (alle Netze)   357,0s   73,4%   1172 Aufrufe   305 ms je Aufruf
    ShapeClassifier             27,3s     5,6%
    MuJoCo (Physik + Rendern)   14,3s     2,9%      <- NICHT der Kostenpunkt
    Rest (Python-Kitt)          86,6s    17,8%

Also steckt fast drei Viertel der Laufzeit in EINEM Netz (der Hex-Fovea).  Eine Mikromessung
desselben Netzes (321 Knoten, 1883 Verbindungen, n_relax=20) zeigt, warum:

    net.step(learn=True)          340,0 ms   davon relax 223 ms
    Python-Schleifen-Aufrufe      ~92.568    ->  3673 ns je Aufruf
    NOETIGE Arithmetik            16,8 MFlop ->  ~3,4 ms
    -> Faktor ~100 Overhead

Von 340 ms sind rund 3 ms Rechnung.  Der Rest ist Interpreter: `_phase_relax` laeuft je
Iteration viermal in Python ueber alle Knoten und Verbindungen und macht dabei winzige
numpy-Aufrufe auf Vektoren der Dimension 4 bis 12.  Das ist KEIN Parallelisierungsproblem --
Overhead verteilt sich nicht auf Threads (GIL) --, sondern ein Buendelungsproblem.

DER ANSATZ.  Das Netz ist ungewoehnlich regelmaessig: die 1883 Verbindungen des Fovea-Netzes
zerfallen in genau drei homogene Gruppen ((4,4) lateral, (12,4) up, (10,12) up), die 321 Knoten
in drei.  Gleiche Form heisst stapelbar: aus 1883 Einzel-Matrixprodukten werden drei einsum-
Aufrufe.  Ein `RelaxPlan` haelt diese Stapel; `PCNetwork._phase_relax` benutzt ihn, wenn er
gebaut werden konnte.

WAS BEWUSST NICHT GEAENDERT WIRD.  Die PCNode-/PCConnection-Objekte bleiben die Wahrheit ueber
das Netz: alles im Projekt liest `node.mu`, `node.epsilon`, `conn.W` (und die 49-MB-Pickles
enthalten genau diese Objekte).  Der Plan SAMMELT deshalb zu Beginn der Relaxation aus den
Objekten, rechnet gebuendelt und SCHREIBT am Ende zurueck.  Zwischen Sammeln und Zurueckschreiben
existiert kein Python-Objekt mehr.  Damit ist die Aenderung lokal auf Phase 3 und jederzeit
per ACT_PC_VEC=0 abschaltbar.

GLEICHHEIT.  Die Reihenfolge der Operationen ist Zug um Zug dieselbe wie in der Objekt-Fassung,
und die Summierung je Zielknoten laeuft ueber einen STABILEN Sortierschluessel -- innerhalb eines
Zielknotens behalten die Verbindungen also ihre Listenreihenfolge, genau wie beim sequentiellen
`_pred_sum += pred`.  Trotzdem wird hier KEINE Bit-Gleichheit BEHAUPTET: einsum und
np.add.reduceat duerfen intern anders zusammenfassen als eine Python-Schleife.  Was gilt, ist
gemessen -- s. `test_relax_vec.py`, das beide Pfade Schritt fuer Schritt gegeneinander haelt.
"""
from __future__ import annotations

import os

import numpy as np

from .connection import ConnType
from .node import _ACTIVATIONS

VEC_ON = os.environ.get("ACT_PC_VEC", "1") == "1"     # Notausschalter: 0 = alte Objekt-Schleife
VEC_MIN_CONNS = int(os.environ.get("ACT_PC_VEC_MIN", "64"))
#   Unter dieser Verbindungszahl lohnt das Buendeln nicht: Sammeln/Zurueckschreiben kostet dann
#   mehr als die gesparten Schleifen.  Winzige Netze (Ziel-/Planer-Netze mit ein paar Knoten)
#   laufen weiter ueber den Objekt-Pfad -- gemessen, nicht geraten (s. netz_mikro).


def _act_key(node) -> str:
    """Den Aktivierungs-NAMEN eines Knotens finden.  PCNode speichert nur die Funktion (`_act`),
    und alte Pickles haben kein Namensfeld -- deshalb ueber Funktions-Identitaet nachschlagen."""
    for k, (f, _d) in _ACTIVATIONS.items():
        if node._act is f:
            return k
    raise ValueError(f"unbekannte Aktivierung an Knoten {node.id!r}")


def _segmente(idx: np.ndarray):
    """Stabile Sortierung + Segmentgrenzen fuer eine Streu-Summe.

    Liefert (order, starts, uniq): `werte[order]` liegt nach Zielindex sortiert, `starts` sind die
    Segmentanfaenge fuer np.add.reduceat, `uniq` die zugehoerigen Zielindizes.  Die Sortierung ist
    STABIL, damit die Summanden innerhalb eines Ziels ihre urspruengliche Listenreihenfolge
    behalten -- dieselbe Reihenfolge, in der die Objekt-Fassung `_pred_sum += pred` aufaddiert.
    """
    order = np.argsort(idx, kind="stable")
    s = idx[order]
    starts = np.flatnonzero(np.r_[True, s[1:] != s[:-1]])
    return order, starts, s[starts]


class _KnotenGruppe:
    """Alle Knoten gleicher Dimension UND gleicher Aktivierung als ein Stapel."""

    __slots__ = ("nodes", "dim", "act", "n", "MU", "PI", "EPS", "PRESS", "PSUM", "PCOUNT",
                 "CLAMP", "MU_ALT", "f", "V", "PRED_NEXT", "PREV_F", "ETA_T", "CLIP_V")

    def __init__(self, nodes, dim, act):
        self.nodes = nodes
        self.dim = dim
        self.act = act
        self.f = _ACTIVATIONS[act][0]
        self.n = len(nodes)
        z = lambda: np.zeros((self.n, dim), dtype=np.complex128)      # noqa: E731
        self.MU, self.PI, self.EPS = z(), z(), z()
        self.PRESS, self.PSUM, self.MU_ALT = z(), z(), z()
        self.CLAMP = np.zeros(self.n, dtype=bool)
        self.PCOUNT = np.zeros(self.n, dtype=np.int64)               # aus der Topologie, fest
        # -- nur fuer Phase 4 (zeitliches Vorwaertsmodell V je Knoten) --
        self.V = np.zeros((self.n, dim, dim), dtype=np.complex128)
        self.PRED_NEXT, self.PREV_F = z(), z()
        self.ETA_T = np.zeros(self.n, dtype=np.float64)
        self.CLIP_V = np.zeros(self.n, dtype=np.float64)


class _VerbGruppe:
    """Alle Verbindungen gleicher (Quell-Dim, Ziel-Dim) und gleichen Typs als ein Stapel."""

    __slots__ = ("conns", "W", "sg", "tg", "si", "ti", "pscale", "is_up",
                 "p_order", "p_starts", "p_uniq", "d_order", "d_starts", "d_uniq",
                 "eta", "decay", "wclip")

    def __init__(self, conns, W, sg, tg, si, ti, pscale, is_up):
        self.conns = conns
        self.W = W                      # (n, ds, dt) komplex
        self.sg, self.tg = sg, tg       # Index der Quell-/Ziel-Knotengruppe
        self.si, self.ti = si, ti       # Zeile in der jeweiligen Knotengruppe
        self.pscale = pscale            # (n,) pressure_scale
        self.is_up = is_up              # (n,) bool -> beta statt gamma
        n = len(conns)                  # -- nur fuer Phase 4 --
        self.eta = np.zeros(n, dtype=np.float64)
        self.decay = np.zeros(n, dtype=np.float64)
        self.wclip = np.zeros(n, dtype=np.float64)
        self.p_order, self.p_starts, self.p_uniq = _segmente(si)     # Druck  -> Quellknoten
        self.d_order, self.d_starts, self.d_uniq = _segmente(ti)     # Vorhersage -> Zielknoten


class RelaxPlan:
    """Kompilierte, gebuendelte Fassung von PCNetwork._phase_relax."""

    def __init__(self, net):
        # ---- Knoten nach (Dimension, Aktivierung) gruppieren -------------------------------
        knoten = list(net._nodes.values())
        schluessel, self.gruppen = {}, []
        self._grp_of, self._row_of = {}, {}
        for nd in knoten:
            k = (nd.dim, _act_key(nd))
            schluessel.setdefault(k, []).append(nd)
        for k, nds in schluessel.items():
            self._grp_of.update({nd.id: len(self.gruppen) for nd in nds})
            self._row_of.update({nd.id: i for i, nd in enumerate(nds)})
            self.gruppen.append(_KnotenGruppe(nds, k[0], k[1]))

        # ---- Verbindungen nach (Quell-GRUPPE, Ziel-GRUPPE, Typ) gruppieren -----------------
        # Nach GRUPPE, nicht nach Dimension: zwei Knotengruppen koennen dieselbe Dimension bei
        # verschiedener Aktivierung haben (dim 5 tanh neben dim 5 relu).  Ein Schluessel aus
        # Dimensionen wuerde beide in einen Stapel werfen und dann fuer alle die Aktivierung des
        # ERSTEN Knotens anwenden -- ein stiller Rechenfehler statt eines Absturzes.
        vs = {}
        for c in net._connections:
            vs.setdefault((self._grp_of[c.source.id], self._grp_of[c.target.id],
                           c.conn_type is ConnType.UP), []).append(c)
        self.verb = []
        for (sg, tg, _up), cs in vs.items():
            W = np.stack([c.W for c in cs]).astype(np.complex128)
            si = np.array([self._row_of[c.source.id] for c in cs], dtype=np.intp)
            ti = np.array([self._row_of[c.target.id] for c in cs], dtype=np.intp)
            ps = np.array([c.pressure_scale for c in cs], dtype=np.float64)
            self.verb.append(_VerbGruppe(cs, W, sg, tg, si, ti, ps, _up))
            # Vorhersage-ZAEHLER folgt allein aus der Topologie und aendert sich nie
            np.add.at(self.gruppen[tg].PCOUNT, ti, 1)

        self.n_conns = len(net._connections)

    # --------------------------------------------------------------------------------------
    def _sammeln(self) -> None:
        """Zustand aus den Objekten in die Stapel holen (mu/pi/eps + Klemm-Maske).

        Die Klemm-Maske wird JEDES MAL neu gelesen: clamp()/unclamp() koennen zwischen zwei
        Schritten von aussen aufgerufen werden (die Sensorzellen tun genau das je Bild).
        """
        for g in self.gruppen:
            g.MU[:] = [nd.mu for nd in g.nodes]
            g.PI[:] = [nd.pi for nd in g.nodes]
            g.EPS[:] = [nd.epsilon for nd in g.nodes]
            g.CLAMP[:] = [nd._clamped for nd in g.nodes]

    def _zurueckschreiben(self) -> None:
        """mu/pi/eps zurueck in die Objekte -- KOPIEN, damit die Stapel wiederverwendbar
        bleiben und niemand versehentlich einen View auf den Arbeitsspeicher haelt."""
        for g in self.gruppen:
            for i, nd in enumerate(g.nodes):
                nd.mu = g.MU[i].copy()
                nd.pi = g.PI[i].copy()
                nd.epsilon = g.EPS[i].copy()

    def _verbindungen_holen(self) -> None:
        """W UND pressure_scale aus den Verbindungsobjekten holen.

        W: Phase 4 (learn) laeuft weiter ueber die Objekte, also kann sich W zwischen zwei
        Relaxationen geaendert haben -- und planner_chain setzt W sogar direkt neu.

        pressure_scale: planner_chain.py:377 setzt die Skala JE PLANUNG neu (Fehler-Diskontierung
        gamma^k ueber die Kette).  Ein beim Bauen eingefrorener Wert waere dort still falsch --
        die Relaxation liefe mit der Diskontierung der vorigen Planung.
        """
        for vg in self.verb:
            vg.W[:] = [c.W for c in vg.conns]
            vg.pscale[:] = [c.pressure_scale for c in vg.conns]

    def _vorhersage_und_pi(self) -> None:
        """Top-down-Vorhersagen sammeln und zu pi mitteln.

        HERAUSGEZOGEN, weil Phase 1 und der Vorhersage-Teil jeder Relaxations-Iteration exakt
        dieselbe Rechnung sind.  Zweimal geschrieben wuerden die beiden Fassungen frueher oder
        spaeter auseinanderlaufen -- und der Unterschied waere still.

        pi = Summe der eingehenden Vorhersagen / ihre ANZAHL; Knoten ohne Eingang bekommen 0.
        Die Anzahl folgt allein aus der Topologie und steht vorberechnet in PCOUNT.
        """
        for g in self.gruppen:
            g.PSUM[:] = 0.0
        for vg in self.verb:
            qg = self.gruppen[vg.sg]
            akt = qg.f(qg.MU)[vg.si]                                   # f(mu_quelle)
            pred = np.einsum("nij,ni->nj", vg.W, akt)                  # W.T @ f(mu_quelle)
            seg = np.add.reduceat(pred[vg.d_order], vg.d_starts, axis=0)
            self.gruppen[vg.tg].PSUM[vg.d_uniq] += seg
        for g in self.gruppen:
            hat = g.PCOUNT > 0
            g.PI[hat] = g.PSUM[hat] / g.PCOUNT[hat][:, None]
            # Knoten OHNE Eingang: die Einzelfassung setzt pi hart auf null.  Hier ist die Zeile
            # praktisch ein No-op (PSUM wurde genullt und bekommt bei ihnen nie etwas dazu, und
            # aus den Objekten wird ohnehin null eingesammelt) -- sie steht als Absicherung fuer
            # ein von aussen gesetztes pi.  Eine Sabotage an ihr faellt deshalb nicht auf.
            g.PI[~hat] = 0.0

    # --------------------------------------------------------------------------------------
    def predict(self, net) -> None:
        """Phase 1, gebuendelt.  Zwei Schritte, in dieser Reihenfolge:

            1. load_predicted_state: freie Knoten starten mu beim eigenen Zeitmodell-Vorschlag
               (_predicted_next_mu aus dem letzten commit_step); GEKLEMMTE behalten ihren Wert --
               das ist der Sensor-Eingang und darf nicht ueberschrieben werden.
            2. Vorhersagen sammeln und mitteln -> pi.

        epsilon bleibt unberuehrt; das ist Phase 2.
        """
        self._sammeln()
        self._verbindungen_holen()
        for g in self.gruppen:
            g.PRED_NEXT[:] = [nd._predicted_next_mu for nd in g.nodes]
            frei = ~g.CLAMP
            g.MU[frei] = g.PRED_NEXT[frei]
        self._vorhersage_und_pi()
        self._zurueckschreiben()

    # --------------------------------------------------------------------------------------
    def relax(self, net) -> int:
        """Phase 3, gebuendelt.  Zug um Zug dieselbe Abfolge wie die Objekt-Fassung:

            1. propagate_error ueber alle Verbindungen   -> Druck auf die Quellknoten
            2. update_state    ueber alle Knoten         -> mu, Druck zurueck auf 0, max_delta
            3. predict         ueber alle Verbindungen   -> Vorhersage-Summe auf die Zielknoten
            4. finalize_prediction + compute_error       -> pi, eps
            5. Abbruch, sobald max_delta < eps_tol
        """
        self._sammeln()
        self._verbindungen_holen()
        eta, alpha = net.eta_inf, net.alpha
        beta, gamma = net.beta, net.gamma
        schritte = net.n_relax

        for schritt in range(schritte):
            # -- 1. Fehlerdruck zurueck auf die Quellen ------------------------------------
            for g in self.gruppen:
                g.PRESS[:] = 0.0
            for vg in self.verb:
                skala = (beta if vg.is_up else gamma) * vg.pscale          # (n,)
                eps_t = self.gruppen[vg.tg].EPS[vg.ti]                     # (n, dt)
                beitrag = np.einsum("nij,nj->ni", vg.W, eps_t)             # W @ eps_ziel
                beitrag *= skala[:, None]
                seg = np.add.reduceat(beitrag[vg.p_order], vg.p_starts, axis=0)
                self.gruppen[vg.sg].PRESS[vg.p_uniq] += seg

            # -- 2. Zustands-Aktualisierung ------------------------------------------------
            max_delta = 0.0
            for g in self.gruppen:
                g.MU_ALT[:] = g.MU
                neu = g.MU + eta * (-alpha * g.EPS + g.PRESS)
                # Die Objekt-Fassung nullt den GANZEN Knotenvektor, wenn EIN Element nicht
                # endlich ist -- also zeilenweise pruefen, nicht elementweise.
                ok = np.all(np.isfinite(neu), axis=1)
                frei = ~g.CLAMP                                            # geklemmte bleiben
                setz = frei & ok
                null = frei & ~ok
                g.MU[setz] = neu[setz]
                g.MU[null] = 0.0
                if g.n:
                    d = np.abs(g.MU - g.MU_ALT)
                    if d.size:
                        max_delta = max(max_delta, float(d.max()))

            # -- 3./4. Vorhersagen + pi (dieselbe Rechnung wie Phase 1), dann Fehler --------
            self._vorhersage_und_pi()
            for g in self.gruppen:
                g.EPS[:] = g.MU - g.PI

            # -- 5. Konvergenz --------------------------------------------------------------
            if max_delta < net.eps_tol:
                self._zurueckschreiben()
                return schritt + 1

        self._zurueckschreiben()
        return schritte


    # --------------------------------------------------------------------------------------
    # Phase 4 -- Lernen, gebuendelt
    # --------------------------------------------------------------------------------------
    def _lernwerte_holen(self) -> None:
        """Lernraten, Zerfall und Betrags-Deckel je Verbindung/Knoten, dazu V und die
        Zeitpuffer.  Die Hyperparameter sind nach dem Bau des Netzes zwar praktisch fest
        (nur PCNetwork.add setzt sie, und das macht den Plan ohnehin ungueltig), werden aber
        wie pressure_scale JEDES MAL gelesen -- eine eingefrorene Kopie war hier schon einmal
        ein stiller Fehler, und der Preis sind ein paar hundert Mikrosekunden."""
        for vg in self.verb:
            vg.eta[:] = [c.eta_learn for c in vg.conns]
            vg.decay[:] = [c.lambda_decay for c in vg.conns]
            vg.wclip[:] = [c.w_clip for c in vg.conns]
        for g in self.gruppen:
            g.V[:] = [nd.V for nd in g.nodes]
            g.PRED_NEXT[:] = [nd._predicted_next_mu for nd in g.nodes]
            g.PREV_F[:] = [nd._prev_f_mu for nd in g.nodes]
            g.ETA_T[:] = [nd.eta_temporal for nd in g.nodes]
            g.CLIP_V[:] = [nd.w_clip_V for nd in g.nodes]

    @staticmethod
    def _deckeln(M: np.ndarray, clip: np.ndarray) -> None:
        """_clip_mag fuer einen STAPEL, mit einem Deckel je Matrix.  clip <= 0 heisst 'kein
        Deckel' (so haelt es die Einzelfassung) -- dafuer unendlich einsetzen, dann greift der
        Vergleich nie."""
        C = np.where(clip > 0.0, clip, np.inf)
        C = np.broadcast_to(C.reshape((-1,) + (1,) * (M.ndim - 1)), M.shape)
        mag = np.abs(M)
        over = mag > C
        if np.any(over):
            M[over] *= C[over] / mag[over]

    def learn(self, net, modulation: float) -> None:
        """Phase 4, gebuendelt -- dieselben Regeln wie PCConnection.learn / PCNode.learn_temporal.

        Verbindungen:  dW = conj(f(mu_quelle)) x eps_ziel ;  W += eta*mod*dW ; W *= (1-zerfall) ;
                       Betrag deckeln.  Die Endlichkeits-Pruefung gilt fuer die GANZE Matrix dW
                       einer Verbindung -- ist ein Element nicht endlich, faellt das Update
                       dieser Verbindung komplett aus (Zerfall und Deckel greifen trotzdem).
        Knoten:        dV = (mu - vorhergesagt) x conj(f(mu_vorher)) ; geklemmte Knoten haben
                       kein V und werden uebersprungen -- auch nicht gedeckelt.
        """
        self._sammeln()
        self._verbindungen_holen()
        self._lernwerte_holen()

        for vg in self.verb:
            qg, zg = self.gruppen[vg.sg], self.gruppen[vg.tg]
            akt = qg.f(qg.MU)[vg.si]                                   # f(mu_quelle)  (n, ds)
            eps = zg.EPS[vg.ti]                                        # eps_ziel      (n, dt)
            dW = np.conjugate(akt)[:, :, None] * eps[:, None, :]       # aeusseres Produkt
            ok = np.all(np.isfinite(dW), axis=(1, 2))                  # je Verbindung, nicht je Element
            if np.any(ok):
                vg.W[ok] += (vg.eta * modulation)[ok, None, None] * dW[ok]
            # (1 - 0) = 1.0 ist ein exaktes No-op, deshalb ohne Fallunterscheidung
            vg.W *= (1.0 - vg.decay)[:, None, None]
            self._deckeln(vg.W, vg.wclip)
            for c, W in zip(vg.conns, vg.W):
                c.W = W.copy()

        for g in self.gruppen:
            frei = ~g.CLAMP
            if not np.any(frei):
                continue
            delta = g.MU - g.PRED_NEXT                                 # (n, d)
            dV = delta[:, :, None] * np.conjugate(g.PREV_F)[:, None, :]
            ok = frei & np.all(np.isfinite(dV), axis=(1, 2))
            if np.any(ok):
                g.V[ok] += (g.ETA_T * modulation)[ok, None, None] * dV[ok]
            # Deckeln trifft ALLE freien Knoten, auch die ohne Update -- wie in der Einzelfassung
            teil = g.V[frei]
            self._deckeln(teil, g.CLIP_V[frei])
            g.V[frei] = teil
            # Nur freie Knoten zurueckschreiben.  Fuer geklemmte waere dV ohnehin exakt null
            # (_prev_f_mu bleibt bei ihnen null, weil commit_step frueh zurueckkehrt) -- die
            # Wache ist also Absicherung, nicht die eigentliche Begruendung.
            for nd, V, f in zip(g.nodes, g.V, frei):
                if f:
                    nd.V = V.copy()


def plan_fuer(net) -> RelaxPlan | None:
    """Einen Plan bauen, wenn sich das Buendeln fuer dieses Netz lohnt; sonst None
    (dann laeuft weiter der Objekt-Pfad)."""
    if not VEC_ON or len(net._connections) < VEC_MIN_CONNS:
        return None
    try:
        return RelaxPlan(net)
    except Exception:
        return None                      # unbekannte Aktivierung o.ae. -> stiller Rueckfall
