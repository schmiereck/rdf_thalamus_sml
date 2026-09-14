---
type: Mechanismus
title: Die Wiedervorlage - eine Wahrnehmungsaenderung auf den echten Szenen des Laufs pruefen, ohne einen Lauf
description: pc_act23 protokolliert je Episode die wahren Lagen aller Koerper. Damit laesst sich jede Szene nachstellen und mit bekannter Wahrheit befragen - auf der tatsaechlichen Lagenverteilung, beliebig viele Einstellungen auf denselben Szenen, in Minuten statt Stunden. Sie misst Nutzen und Schaden zugleich, weil genau deren Trennung zwei Anlaeufe gekostet hat.
tags: [act23, methodik, wahrnehmung, werkzeug]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-14T00:00:00Z }
sources:
  - id: code
    resource: src/pc_cvnn/act23_wiedervorlage.py
    title: Das Werkzeug
  - id: anlass
    resource: /befunde/geburtenrate-chroma-phantome.md
    title: Der Befund, aus dem es entstand
---

# Wozu

Sieben A/B-Laeufe zur Verschmelzung blieben nacheinander uneindeutig. Der Grund war nicht
Ungeschick, sondern Arithmetik: die gemessenen Wirkungen betreffen **rund 2 %** der Wahrnehmungen,
und die [Nachweisgrenze](/befunde/rechnerlast.md) eines 150- bis 300-Episoden-Laufs liegt weit
darueber. Jeder dieser Laeufe kostete 1,5 bis 5 Stunden.

Handgebaute Sonden waren keine Loesung, sondern eine eigene Fehlerquelle: eine mit fuenf eng
gestellten Koerpern **ueberzeichnete die Verschmelzung um Faktor 15** (29 gegen 2 %) und hat damit
eine ganze Baureihe in die falsche Richtung kalibriert.

Die richtige Lagenverteilung lag die ganze Zeit vor. `pc_act23` schreibt unter `ACT23_DEBUG=1`
je Episode:

    [dbg] after ep : {'obj_red': [-0.082, 0.089], 'obj_green': [0.508, -0.599], ...}

nach `log/pc_act23_*.txt`. Das ist die **wahre Lage jedes Koerpers am Episodenende** - also
Grundwahrheit fuer jede Wahrnehmungsmessung, aus jedem Lauf, der je gefahren wurde.

# Was es misst - beides zugleich

Das ist der Kern und die Lehre aus dem Chroma-Schnitt:

    VERFEHLT    keine Detektion naeher als 20 mm  ->  kostet einen privilegierten Rueckfall
    ZERTEILT    mehr als eine Detektion am selben Koerper  ->  gebiert eine Phantomklasse
    NEU         Detektionen mit resolve() = None  ->  das Rohmaterial der Geburt,
                aufgeteilt in "auf einem Koerper" / "Bruchstueck" / "bei keinem Koerper"

> **Ein Gewinn bei VERFEHLT, der ZERTEILT mitzieht, ist keiner.** Genau diese Verwechslung hat den
> Chroma-Schnitt zweimal als Erfolg erscheinen lassen
> ([Befund](/befunde/geburtenrate-chroma-phantome.md)).

Dazu der **Mittelwert** der Detektionen je Koerper, ausdruecklich nicht der Median: eine
Zerteilung, die nur jede vierte Szene trifft, ist im Median unsichtbar (4,0 bei 4,49 Mittel). Zwei
Sonden sind mir genau daran vorbeigelaufen.

# Aufruf

    ACT14_DOF=4 .venv/Scripts/python.exe src/pc_cvnn/act23_wiedervorlage.py

    WV_LOGS       Glob auf die Protokolle (Vorgabe log/pc_act23_*.txt)
    WV_N          Szenen, zufaellig gezogen (Vorgabe 200)
    WV_STATE      Zustandsdatei -- immer eine KOPIE
    WV_VARIANTEN  "Name:VAR=WERT,VAR=WERT|Name:..."  -- die erste ist der Bezug

Beispiel, die Schranke des Chroma-Schnitts durchfahren:

    WV_VARIANTEN="aus:|t1.0:ACT_SHAPE_CHROMA_SPLIT=1,ACT_SHAPE_CHROMA_TRENNUNG=1.0|t2.2:ACT_SHAPE_CHROMA_SPLIT=1,ACT_SHAPE_CHROMA_TRENNUNG=2.2"

    Variante           verfehlt       zerteilt  Lok-Med     p90  Det/Koerper
    Vorgabe         10 =   2,1 %     2 =   0,4 %    2,50    6,64         1,00
    t1.0             0 =   0,0 %    22 =   4,7 %    2,50    6,39         1,08
    t2.2             8 =   1,7 %     5 =   1,1 %    2,37    6,57         1,02

Die Varianten werden ueber ein Neuladen von `shape_classifier` gesetzt (dasselbe Verfahren wie in
`act23_relrings_ab.py`) - die Schalter sind Modulkonstanten und wuerden sonst von der ersten
Variante haengenbleiben. Fisher-Test gegen die erste Variante, fuer beide Spalten.

# Grenzen, ehrlich

* **Der Yaw steht nicht im Protokoll** und wird neu gewuerfelt. Verschmelzung haengt ueberwiegend
  an den Lagen, aber nicht nur - dieselbe Szene kann je nach Drehung verschmelzen oder nicht.
* **Die Zeile faellt am EPISODENENDE.** Bei Episodenbeginn garantiert `pc_act16.scatter` 80 mm
  Mindestabstand; dort verfehlt auch die feste Segmentierung nichts. Wer den Nutzen einer
  Verschmelzungs-Reparatur sucht, findet ihn nur am Ende - wer ihren Schaden sucht, ueberall.
* **Der Glob ist wichtig.** `log/pc_act23_*.txt` trifft 500+ Protokolle seit Projektbeginn, mit
  anderen Koerpersaetzen und anderer Geometrie. Der Vergleich ZWISCHEN Varianten bleibt gueltig
  (alle sehen dieselben Szenen), die absoluten Zahlen vermischen aber Projektphasen.
* **`resolve()` laeuft gegen den Exemplarbestand des geladenen Zustands.** Aendert eine Variante
  den Deskriptor, ist die Neuheitszahl relativ zu diesem Bestand zu lesen.
* **Es bleibt `ebene: pruefstand`.** Die Wiedervorlage misst die WAHRNEHMUNG auf echten Szenen -
  sie sagt nichts ueber Aneignung, Adressierung oder Quote. Die
  [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) ist damit nicht aufgehoben, nur eine ihrer
  Ursachen beseitigt: die falsche Lagenverteilung.

# Was sie nicht ersetzt

Einen act23-Lauf. Eine Wirkung auf Adressierung, Geburten oder Quote braucht weiter `ebene:
act23-ab`. Die Wiedervorlage sagt vorher, **ob ein Lauf ueberhaupt lohnt** - und bei 2 %
betroffener Wahrnehmungen lautet die Antwort meistens nein.

# Verwandt

* [Die verdreifachte Geburtenrate ist reines Phantom](/befunde/geburtenrate-chroma-phantome.md) - der Anlass
* [Frisch bei null](/befunde/chroma-split-frisch.md) - die erste Anwendung
* [Die Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)
* [Rechnerlast](/befunde/rechnerlast.md) - die Nachweisgrenze, die das noetig macht
