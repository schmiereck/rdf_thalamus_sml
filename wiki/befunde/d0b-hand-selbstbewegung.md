---
type: Befund
title: D0b-Handlandmark - Eigenbewegung ist sichtbar, doch Punkt- und lokale Maskenauslese scheitern
description: Fingerimpulse erzeugen zuverlässig ein eigenes Kamerasignal. Weder ihr Schwerpunkt noch ein auf zurückgehaltenen Posen gelernter, räumlich geteilter Bildpatch-Ausleser lokalisieren die Klaue ausreichend; D0b braucht eine räumlich gebundene Repräsentation.
tags: [act23, dream-rsi, d0b, fovea, hand, selbstbewegung]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: codex, at: 2026-09-24T12:30:00Z }
sources:
  - id: probe
    resource: ../../src/pc_cvnn/act23_d0b_hand_landmark_probe.py
    title: Reproduzierbarer Kamera-/Aktuator-Prüfstand
  - id: visual
    resource: ../../log/d0b-hand-landmark/seed101-36pose/visual.jsonl
    title: Ausschließlich kamerabasierte Selbstbewegungsdaten
  - id: evaluation
    resource: ../../log/d0b-hand-landmark/seed101-36pose/eval.jsonl
    title: Getrennte Geometrie-Evaluation der Klauenposition
  - id: mask-probe
    resource: ../../log/d0b-hand-mask/seed101-96pose/self_motion_frames.npz
    title: 96 reine Kamera-/Selbstbewegungsbeobachtungen
  - id: mask-tool
    resource: ../../src/pc_cvnn/act23_d0b_hand_mask_audit.py
    title: Positionsgetrennter NumPy-Maskenausleser
  - id: mask-evaluation
    resource: ../../log/d0b-hand-mask/seed101-96pose/linear-mask-audit/result.json
    title: Getrennte Positionsauswertung des gelernten Maskenauslesers
---

# Behauptung

Der Greifer kann über seine **eigene sichtbare Bewegung** referenziert werden: Ein kurzer,
ausgeführter Öffnen/Schließen-Impuls verändert die Kamera in jeder gemessenen Pose. Das ist ein
zulässiger Selbstüberwachungskanal. Der handgeschriebene Schwerpunkt dieser Differenz ist dagegen
kein ausreichend genauer Landmark und wird nicht in den ACT23-Laufzeitpfad übernommen.

# Aufbau

`act23_d0b_hand_landmark_probe.py` fährt sechs feste und 30 mit Seed 101 gezogene
Arbeitsraumpositionen nacheinander an. Die Objekte stehen außerhalb des Bilds. In jeder Pose
friert der Prüfling die übrigen Armziele ein, führt den Greifer von 0,54 auf 0,05 und nimmt vor
und nach der realen Aktuatorbewegung ein 240×240-Kamerabild auf. `motion_landmark` sieht nur die
absolute RGB-Differenz der beiden Bilder.

Für die getrennte Evaluation werden ausschließlich nach dieser Beobachtung die beiden
Klauengeometrien in ein privates Magenta-Bild gerendert; dessen Schwerpunkt landet nur in
`eval.jsonl`. Weder die Rendererfarbe noch Objektpose, Kontakt, Weld, Homographie oder diese
Position gelangen in `visual.jsonl` oder in die Landmark-Funktion.

Ausführbar:

```powershell
..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_d0b_hand_landmark_probe.py `
  --output log\d0b-hand-landmark\seed101-36pose --random-poses 30 --seed 101
```

# Zahlen

| Größe | Wert |
|---|---:|
| ausgeführte Impulse | 36 |
| Kameradifferenz vorhanden | 36 / 36 |
| Klaue im Evaluationsbild sichtbar | 31 / 36 |
| gepaarte Landmark-/Eval-Fälle | 31 |
| Fehler, Median | 24,2 px |
| Fehler, Quartile 1 / 3 | 17,5 / 37,7 px |
| Fehler, Maximum | 63,0 px |
| ≤ 20 px | 12 / 31 |
| ≤ 30 px | 18 / 31 |

# Bewertung

Die Messung belegt noch keine Greifwirkung und auch keinen brauchbaren Punktdetektor; sie ist ein
Prüfstand, kein act23-A/B. Sie schließt aber die bisherige Beobachtungslücke: Ein Bildsignal der
eigenen Hand kann ohne Simulatorinformation erzeugt werden. Die ausgeblendeten fünf
Evaluationsfälle sind ehrliche Sichtenthaltungen, keine negativen Selbstetiketten.

Der einfache Schwerpunkt vermischt die sichtbaren Fingerflächen und ihre Schatten; er kann sich
um mehr als eine Greiferbreite vom Klauenzentrum verschieben. Ein fester Grauwert-Detektor war in
einem vorangehenden Sechs-Posen-Bildtest ebenfalls instabil (5–80 px) und wird ebenfalls nicht
verwendet. Damit ist eine Laufzeitregel „hellgrau = Hand“ ebenso ausgeschlossen wie
„Differenzschwerpunkt = Hand“.

# Gelernter Maskenausleser

Die Sonde speichert inzwischen zusätzlich zu den JSON-Protokollen die beiden echten Kamerabilder
und das kontinuierliche RGB-Differenzfeld in einer komprimierten, nur lokalen `.npz`-Datei. Auf
96 Positionen (Seed 101) werden alle Positionen mit `pose_id % 3 == 0` als vollständiger Test
zurückgehalten. Ein kleiner NumPy-Ausleser erhält nur das offene 40×40-RGB-Bild. Seine Gewichte
sind räumlich geteilt: jedes Ausgabepixel liest denselben 3×3-RGB-Patch. Trainiert wird es allein
auf dem selbst erzeugten Differenzfeld; die Klauenposition wird erst nach der Vorhersage aus der
getrennten Evaluation gelesen.

| Größe | Wert |
|---|---:|
| Trainings- / Testpositionen | 64 / 32 |
| sichtbare, gepaarte Testpositionen | 29 |
| Masken-MSE, Ausleser | 0,00607 |
| Masken-MSE, Konstante | 0,00675 |
| Landmarkfehler, Median | 57,8 px |
| Landmark ≤ 20 px | 5 / 29 |

Der Ausleser lernt somit etwas vom Bewegungsfeld (MSE −10,1 % gegenüber der Konstante), aber
nicht dessen Ort. Das ist keine widersprüchliche Aussage: Die geteilte lokale Filterregel erkennt
helligkeitsartige Bewegung, kann jedoch Armteile, Finger und Schatten ohne übergreifende
Geometrie nicht binden. Seine Landmark-Ausgabe ist deutlich schlechter als der gleichzeitig
gemessene Differenzschwerpunkt; dieser Unterschied ist erwartbar, weil der Schwerpunkt die
zweite, aktiv erzeugte Ansicht kennt, der Ausleser aber nur das offene Bild erhält.

# Folgen

D0b/F0 bleibt vor einem Greifzustandskopf gesperrt. Der nächste Kandidat ist ein kleiner
**räumlich gebundener** Ausleser einer verteilten Selbstbewegungsmaske. Der gerade verworfene
lokale Patch-Ausleser darf nicht durch mehr Epochen oder eine andere Schwelle nachgetunt werden.
Zuerst wird geprüft, ob der vorhandene Fovea-Zustand bei einer durch Selbstbewegung gesetzten
Sakkade die Fingerregion räumlich bindet; erst ein vorab formulierter, auf ganzen Posen
zurückgehaltener Vergleich gegen die lokale Baseline kann einen reicheren Kopf rechtfertigen.
Der Bildunterschied bleibt nur sein selbst erzeugtes Trainingsziel, nie ein Laufzeitlabel. Erst
nach einem bestandenen Landmark-Audit darf seine Bildraumreferenz zusammen mit `selection_px` das
Mitbewegungs-Selbstetikett versuchen.
