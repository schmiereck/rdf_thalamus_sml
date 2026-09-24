---
type: Befund
title: D0b-Handlandmark - Eigenbewegung ist sichtbar, doch auch die eingefrorene Fovea bindet die Finger nicht ausreichend
description: Fingerimpulse erzeugen zuverlässig ein eigenes Kamerasignal. Schwerpunkt, lokaler Maskenausleser und der komplexe Topzustand der eingefrorenen Fovea verfehlen auf zurückgehaltenen Posen die Klaue; eine neue Fovea-Aufgabe braucht einen eigenen, isolierten Lernvertrag.
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
  - id: fovea-tool
    resource: ../../src/pc_cvnn/act23_d0b_fovea_binding_audit.py
    title: Eingefrorener Fovea-Topzustand auf Selbstbewegungs-Sakkaden
  - id: fovea-evaluation
    resource: ../../log/d0b-fovea-binding/seed101-96pose/result.json
    title: Positionsgetrennter Audit der Fovea-Sakkadenwahl
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

# Eingefrorener Fovea-Zustand

Der dritte Audit liest die persistierte `HexFovea` aus `base.pkl` nur aus einer serialisierten
Arbeitskopie. Für jede Position startet sie wieder im gleichen Zustand und bleibt über
`ACT23_D0_FREEZE=1` ohne Lernupdate. Neun feste, zulässige Sakkaden decken den inneren
240×240-Bildraum ab. Ein kleiner Ridge-Ausleser sieht ausschließlich Real- und Imaginärteile des
zehndimensionalen Fovea-Topzustands und lernt aus dem eigenen Bewegungsfeld, welche Sakkade die
Fingerbewegung enthält. Testpositionen (`pose_id % 3 == 0`) bleiben vollständig zurückgehalten.
Erst nach Auswahl der Sakkade wird sie gegen das getrennt gerenderte Klauenzentrum bewertet.
Die gelesene Basisdatei behielt SHA-256 `ad9d768c...c09b9e`.

| Größe | Wert |
|---|---:|
| Trainings- / Testpositionen | 64 / 32 |
| sichtbare, gepaarte Testpositionen | 29 |
| Fovea-Sakkadenfehler, Median | 53,5 px |
| feste Bildmitte, Median | 80,5 px |
| Fovea-Sakkaden ≤ 24 px | 4 / 29 |

Der eingefrorene Zustand trägt demnach schwache räumliche Information: seine Wahl ist besser als
eine konstante Bildmitte. Sie erreicht aber nicht annähernd die für eine Handreferenz nötige
Abdeckung. Der kleine Gewinn rechtfertigt weder einen Greifzustandskopf noch nachträgliches
Tuning des linearen Auslesers. Er zeigt nur, dass die Fovea-Aufgabe nicht informationsleer ist.

# Folgen

D0b/F0 bleibt vor einem Greifzustandskopf gesperrt. Der nächste Kandidat ist keine Änderung am
Teacher, sondern ein **neuer, isolierter Fovea-Lernzweig für Selbstbewegung**. Sein einziges
Trainingsziel ist das vom eigenen Fingerimpuls erzeugte Bewegungsfeld; bestehende Fovea-Gewichte,
die D0-Basis und der ACT23-Steuerpfad bleiben unangetastet. Vor der ersten Lernzeile muss sein
Vertrag ganze Positionssplits, einen frischen Checkpoint, die getrennte Klauen-Evaluation und
eine vorab festgelegte Landmark-/Enthaltungsmetrik enthalten. Erst nach bestandenem
Landmark-Audit darf seine Bildraumreferenz zusammen mit `selection_px` das
Mitbewegungs-Selbstetikett versuchen.
