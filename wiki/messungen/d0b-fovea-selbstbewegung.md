---
type: Messvorschrift
title: D0b-F1a - isolierter Fovea-Crop-Kopf für Selbstbewegung
description: Vorregistrierter Prüfstand für einen neuen, nicht steuernden Kopf: RGB-Fovea-Crops sagen das eigene Fingerbewegungsfeld voraus und wählen eine Sakkade auf vollständig zurückgehaltenen Armpositionen.
tags: [act23, dream-rsi, d0b, fovea, selbstbewegung, architektur]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: codex, at: 2026-09-24T19:00:00Z }
sources:
  - id: motion-data
    resource: ../../log/d0b-hand-mask/seed101-96pose/self_motion_frames.npz
    title: Reine Kamerabilder und selbst erzeugte Bewegungsfelder
  - id: evaluation
    resource: ../../log/d0b-hand-mask/seed101-96pose/eval.jsonl
    title: Getrennte Klauen-Evaluation
  - id: frozen-baseline
    resource: /befunde/d0b-hand-selbstbewegung.md
    title: Eingefrorene Fovea-Bindung, Median 53,5 px
---

# Behauptung

Ein kleiner, räumlich vollständiger Kopf über einem Fovea-Crop kann die lokale Fingeranordnung
besser binden als der bisherige Topzustand oder ein räumlich geteilter 3×3-Patchfilter. Das ist
eine Hypothese über eine **neue Netzstruktur**, nicht über den Teacher.

# Aufbau

Die Datenbasis bleibt unverändert: 96 leere Kalibrierpositionen, pro Position ein echtes offenes
Kamerabild und das durch den eigenen Öffnen/Schließen-Impuls entstandene Bewegungsfeld. Der Kopf
sieht nur RGB-Werte eines 16×16-Hex-Fovea-Crops aus dem offenen Bild. Sein Ziel ist die normierte
Bewegungsmasse in einem Radius von 24 px um eine von neun festen Sakkaden. Objektpose,
Klauengeometrie, Kontakt, Homographie und das Bewegungsbild selbst sind beim späteren Auslesen
kein Eingang.

Die Positionen mit `pose_id % 3 != 0` sind Training (64), `pose_id % 3 == 0` bleiben vollständiger
Test (32). Drei Initialisierungsseeds trainieren denselben kleinen MLP-Crop-Kopf. Die persistierte
Fovea in `base.pkl`, ihre Gewichte und der ACT23-Pfad werden nicht geöffnet oder beschrieben.
`eval.jsonl` wird erst nach Wahl der bestbewerteten Sakkade gelesen.

# Vertrag

Der Kopf darf nur als Kandidat für einen weitergehenden Landmark-Audit gelten, wenn mindestens
zwei von drei Seeds auf den sichtbaren Testpositionen **beide** Punkte erfüllen:

| Metrik | Tor |
|---|---:|
| Median Abstand der gewählten Sakkade zur externen Klaue | ≤ 40 px |
| sichtbare Testklauen innerhalb 24 px | ≥ 9 / 29 |

Diese Schwelle liegt deutlich über der Zufall-/Bildmittenbasis (80,5 px Median), aber unterhalb
eines produktiven Hand-Landmarks. Ein Bestehen erlaubt nur einen stärkeren Landmark-Prüfstand;
es schaltet weder Greifzustand noch Steuerung frei. Bei Verfehlen wird weder Epochenzahl noch
Schwelle nachoptimiert. Dann wird der Kopf als Strukturvariante verworfen und der Befund
fortgeschrieben.

# Grenzen

Die Selbstbewegung ist eine gezielte Kalibrierhandlung. Sie ist weder der bestehende Grasp-Teacher
noch ein Erfolgslabel. Der Kopf ersetzt keine ACT23-Entscheidung und wird nicht in eine Pkl
persistiert. Ein späterer erfolgreicher Architekturzweig braucht einen eigenen frischen
Checkpoint und eine erneute Freeze-/Nichtbeeinflussungsprüfung.

# Ergebnis

Der isolierte F1a-Crop-Kopf wurde exakt nach dem Vertrag mit den drei Initialisierungsseeds 11,
17 und 23 gefahren. Er ist eine neue, räumlich vollständige MLP-Struktur über 8×8×RGB-
Fovea-Crops; weder der Teacher noch die persistierte Fovea oder ACT23 wurden geändert.

| Seed | sichtbare Testpositionen | Median | ≤ 24 px |
|---|---:|---:|---:|
| 11 | 29 | 42,4 px | 5 / 29 |
| 17 | 29 | 42,4 px | 5 / 29 |
| 23 | 29 | 46,3 px | 5 / 29 |

Keiner der drei Seeds erreicht Median ≤40 px oder 9/29 innerhalb 24 px. F1a besteht das Tor
damit **0/3** und ist verworfen. Sein kleiner Abstandgewinn gegenüber der eingefrorenen Fovea
(53,5 px) ist kein Grund für Epochen-, Breiten- oder Schwellenvariationen auf derselben Aufgabe.
