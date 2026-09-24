---
type: Befund
title: D0b-Handlandmark - Eigenbewegung ist sichtbar, ihr Schwerpunkt kein Greiferpunkt
description: Ein ausgeführter Öffnen/Schließen-Impuls erzeugt in 36/36 Kamerapaaren ein eigenes Bildsignal. Der Schwerpunkt der Differenzmaske trifft die externe Klauenposition aber nur in 12/31 sichtbaren Fällen innerhalb 20 px; D0b braucht eine gelernte Bewegungsmaske statt dieser festen Auslese.
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

# Folgen

D0b/F0 bleibt vor einem Greifzustandskopf gesperrt. Der nächste Kandidat ist ein kleiner
**gelernter Ausleser einer verteilten Selbstbewegungsmaske**: Der Bildunterschied ist nur sein
selbst erzeugtes Trainingsziel, nicht der spätere Landmark. Er muss auf ganzen, zurückgehaltenen
Posen gegen dieselbe getrennte Evaluationsdatei mindestens Sichtbarkeit, Fehlerquantile und
Enthaltungen belegen. Erst danach darf seine Bildraumreferenz zusammen mit `selection_px` das
Mitbewegungs-Selbstetikett versuchen.
