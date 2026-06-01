# PC-Graph Architektur

Erweiterung des Predictive-Coding-Grundgerüsts aus `predictive-coding.md` zu einem
vollständig konfigurierbaren Graphen mit freien State-Dimensionen, lateralen Verbindungen
und beliebiger Konnektivität (N:M Über-/Unterknoten).

---

## 1. Kern-Konzepte

### 1.1 Node

Jeder Knoten `k` besitzt drei interne Vektoren:

| Symbol   | Bedeutung                                      | Dimension     |
|----------|------------------------------------------------|---------------|
| `μ_k`    | State (aktuelle Repräsentation)                | `dim_k`       |
| `π_k`    | Prediction (Vorhersage, die dieser Knoten empfängt) | `dim_k`  |
| `ε_k`    | Error (`μ_k − π_k`)                            | `dim_k`       |

`dim_k` ist pro Knoten frei wählbar und unabhängig von anderen Knoten.

### 1.2 Connection

Eine Verbindung verbindet zwei Knoten gerichtet und hat einen Typ:

| Typ        | Richtung                      | Bedeutung                                      |
|------------|-------------------------------|------------------------------------------------|
| `UP`       | tiefer Knoten → höherer Knoten | Fehler fließt aufwärts, Vorhersage abwärts    |
| `DOWN`     | höherer Knoten → tiefer Knoten | (Umkehrrichtung einer UP-Verbindung)           |
| `LATERAL`  | Nachbar → Nachbar (gleiche Ebene) | Kontextinformation im selben Layer          |

Jede Verbindung `c: source → target` trägt eine Gewichtsmatrix:

```
W_c : shape [dim_source × dim_target]
```

Sie berechnet die Vorhersage des Source-Knotens über den Target-Knoten:

```
predict_c = W_c · activation(μ_source)
```

### 1.3 Vier Berechnungsphasen

Identisch zu `predictive-coding.md`, jetzt über alle Verbindungstypen:

```
Phase 1 — Predict    : Alle Knoten schicken Vorhersagen entlang ihrer Ausgabe-Verbindungen
Phase 2 — Error      : Alle Knoten berechnen ε_k = μ_k − π_k
Phase 3 — Relax      : Iterativer Update von μ_k bis Konvergenz (oder feste Schritte)
Phase 4 — Learn      : Gewichts-Update aller W_c
```

---

## 2. Detaillierter Ablauf

### Phase 1: Predict

Für jede Verbindung `c: source → target` vom Typ `UP` oder `LATERAL`:

```
predict_c = W_c · activation(μ_source)
```

Der Zielknoten aggregiert alle eingehenden Vorhersagen:

```
π_target = Σ_c predict_c     (Summe über alle eingehenden Verbindungen)
```

*Normierung optional (z.B. Mittelwert statt Summe wenn viele Eingänge).*

### Phase 2: Error

Für jeden Knoten `k`:

```
ε_k = μ_k − π_k
```

### Phase 3: Relax (Inference-Schleife)

Wiederholt für `n_relax` Schritte:

```
dμ_k = −α · ε_k                                    # Eigener Fehler-Druck
     + β · Σ_{c: k→j, UP}    W_c^T · ε_j           # Druck von übergeordneten Knoten
     + γ · Σ_{c: k→j, LAT}   W_c^T · ε_j           # Druck von lateralen Nachbarn

μ_k  ← μ_k + η_inf · dμ_k
ε_k  ← μ_k − π_k                                   # Fehler neu berechnen
```

Hyperparameter: `α`, `β`, `γ` gewichten die drei Druckquellen. `η_inf` ist die Inferenz-Schrittweite.

*Abbruchkriterium: `||Δμ||² < ε_tol` oder feste Anzahl Schritte.*

### Phase 4: Learn

Für jede Verbindung `c: source → target`:

```
ΔW_c = η_learn · ε_target · activation(μ_source)^T
W_c  ← W_c − ΔW_c
```

Optionaler Weight-Decay: `W_c ← (1 − λ) · W_c`

---

## 3. Node-Spezifikation

```
Node:
    id:         str                   # Eindeutiger Name, z.B. "b1", "a1", "i1"
    dim:        int                   # State-Dimension (frei wählbar)
    activation: callable              # z.B. tanh, relu, identity
    μ:          ndarray [dim]         # State-Vektor
    π:          ndarray [dim]         # aggregierte Vorhersage
    ε:          ndarray [dim]         # Fehler-Vektor
```

### Temporale Erweiterung

Ein Knoten kann optional einen Temporal-Puffer tragen:

```
    μ_prev:     ndarray [dim]         # State des letzten Zeitschritts
    W_temp:     ndarray [dim × dim]   # Temporale Übergangsgewichte
```

Die temporale Vorhersage wird dann in Phase 1 wie eine weitere eingehende Verbindung behandelt:

```
π_temporal_k = W_temp_k · activation(μ_prev_k)
π_k         += π_temporal_k
```

---

## 4. Connection-Spezifikation

```
Connection:
    id:         str                   # z.B. "b1→a1", "a1↔a2"
    type:       UP | LATERAL          # Verbindungstyp
    source:     Node                  # Sendender Knoten
    target:     Node                  # Empfangender Knoten
    W:          ndarray [dim_source × dim_target]
```

---

## 5. Netzwerk-Spezifikation (Graph)

```
Network:
    nodes:       dict[str, Node]
    connections: list[Connection]

    α, β, γ:     float               # Relax-Gewichte (eigen, up, lateral)
    η_inf:       float               # Inferenz-Schrittweite
    η_learn:     float               # Lern-Schrittweite
    n_relax:     int                 # Relaxations-Schritte pro Zeitschritt
    ε_tol:       float               # Abbruchschwelle Relaxation
```

---

## 6. Beispiel-Topologien

### 6.1 Einfache vertikale Kette (wie predictive-coding.md)

```
[b1: dim=8] ──UP──> [a1: dim=16] ──UP──> [i1: dim=32]
                                              ↑
                                          Sensor-Input
```

`i1-state` wird direkt auf Sensor-Daten gesetzt (kein Error-Update für i1).

### 6.2 Kette mit Lateral-Verbindungen

```
[b1: dim=8] ──UP──> [a1l: dim=16] ──LAT──> [a1r: dim=16] ──UP──> [i1: dim=32]
                         ↑                       ↑
                     Sensor links            Sensor rechts
```

Jeder a1-Knoten empfängt: Fehler von i1 (UP), Vorhersage von b1 (DOWN), Kontext vom Nachbarn (LATERAL).

### 6.3 2D-Grid (spatial × lateral)

```
[b1_0]  [b1_1]  [b1_2]          # Abstraktions-Layer (dim=8 je Knoten)
   ↕  ↔    ↕  ↔    ↕            # ↕ = UP/DOWN-Verbindung, ↔ = LATERAL
[a1_0]  [a1_1]  [a1_2]          # Hidden-Layer (dim=16 je Knoten)
   ↕  ↔    ↕  ↔    ↕
[i1_0]  [i1_1]  [i1_2]          # Sensor-Layer (dim=32 je Knoten)
   ↑        ↑        ↑
 Input_0  Input_1  Input_2
```

Alle `bX`-Knoten teilen optional eine gemeinsame Gewichtsmatrix `W_ba`
(Weight-Sharing analog zu P3-C im bestehenden Projekt).

---

## 7. Initialisierung

| Komponente   | Methode                                 |
|--------------|-----------------------------------------|
| `μ_k`        | Nullvektor oder kleines Gaußsches Rauschen |
| `W_c`        | Xavier-Initialisierung: `±sqrt(6 / (dim_source + dim_target))` |
| `W_temp_k`   | Kleine Identität + Rauschen: `0.1·I + ε` |

---

## 8. Offene Design-Entscheidungen

| Frage | Optionen |
|-------|----------|
| Vorhersage-Aggregation bei mehreren Eingängen | Summe / Mittelwert / lernbare Gewichtung |
| Weight-Sharing zwischen gleichartigen Knoten | Global (ein `W` für alle) / Per-Layer / Keine |
| Aktivierungsfunktion | `tanh` (beschränkt, biologisch motiviert) / `relu` / `identity` |
| Lernregel | Lokales Hebbian (`ε·μ^T`) / Adam mit lokalem Gradienten |
| Sensor-Knoten | State fixiert auf Input (kein μ-Update) oder mit kleinem Fehler-Druck |
| Laterale Reichweite | Nur direkter Nachbar / k-Nachbarn / Alle im Layer |
