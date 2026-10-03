---
type: Messvorschrift
title: B1-Abdeckungsaudit - Kamerasicht und Gelenkraum getrennt prüfen
description: Diagnose der vorhandenen 224 Encoder-/Bildpaare ohne Nachtraining oder neue Erfolgsgrenze.
tags: [s1, koerpermodell, kamera, audit]
status: stable
evidenz: vermutung
ebene: pruefstand
generated: { by: codex, at: 2026-10-03 }
sources:
  - resource: ../../src/pc_cvnn/act23_s1_body_coverage_audit.py
    title: Ausführbarer isolierter Audit, inklusive Projektions-/Replaykontrollen
---

# Auftrag und Grenzen

Der [erste Körperdecoder B1](/befunde/s1-visuelles-koerpermodell.md) verfehlte sein Tor.
Jetzt werden **Sichtbarkeit und Posenabdeckung** diagnostiziert, ohne B1 umzudeuten oder
den Decoder nachzutrainieren. Testseed 409 ist bereits bekannt; alle neuen Auswertungen sind
beschreibende Diagnose, keine unabhängige Bestätigung und kein neuer Modellvergleich.

# Vorab festgelegte Auswertung

1. Originaldaten über Manifest-SHA256 prüfen. Im bestehenden Gelenkintervall nach dessen
   Breite skalierte euklidische Gelenkabstände messen: nächste Trainingspose je Testpose,
   nächste andere Trainingspose je Trainingspose, marginale Min/Max und konvexe Hülle.
   Fehler des eingefrorenen Decoders nach Abstand und innerhalb/außerhalb der Hülle zeigen.
   Diese Maße sind keine Belege, dass das Netz lokal interpoliert oder ein Abstand kausal ist.
2. Beide Erhebungen separat ab Initialzustand mit ihren gespeicherten direkten Stellwerten
   und je 400 Physikschritten wiederholen. Encoder, Greifer, Zeit und **jedes RGB-Bild** gegen
   Original prüfen. Bei Abweichung abbrechen; privilegierte Auswertung dann nicht zuordnen.
3. Erst nach erfolgreichem RGB-Vergleich pro Pose separat MuJoCo-Geometriesegmentierung
   rendern: sichtbare Pixel aller Körper unter `base_link` sowie `claw_left`/`claw_right`.
   Diese Masken bleiben ausschließlich in einem Evaluationsartefakt. Keine Lernetiketten,
   keine Veränderung der Originalbilder, keine handgeschriebene Laufzeitwahrnehmung.
4. Greifergeometrie zusätzlich in den **gleichen** Kameraraum projizieren: Zentren und
   Eckpunkte der beiden Klauenboxen. Vollständig außerhalb eines gemeinsamen Bildrands
   liegende Boxen von unsichtbaren, aber nicht eindeutig außerhalb liegenden Fällen trennen.
   Verdeckung wird ohne weiteren Nachweis nicht als Ursache behauptet.
5. Auswirkungen des 4×4-Poolings beschreiben: sichtbare Klauenfläche in äquivalenten
   24×24-Pixeln und Zahl der Zellen mit mindestens halber Klauenbelegung. Außerdem prüfen,
   wie viel Trainings-Bildvarianz auf Bereiche entfällt, die im Replay jemals Arm enthalten.
   Schatten oder Freilegung des Hintergrunds werden dadurch nicht semantisch segmentiert.

# Ressourcen und Interpretation

Sequentieller kleiner Headless-Replay mit einem BLAS-Thread, eigene Ausgabedateien,
keine gemeinsamen PKLs und keine produktiven Codeänderungen. Modell- und Originaldatenhashes
vorher/nachher vergleichen. Die bestehende Kamera und Bewegungsbox werden nicht nachgestellt.
Ein ungünstiger Blick kann das Lernziel für die Hand unbrauchbar machen, ohne allein den
allgemeinen RGB-Generaliserungsfehler des Decoders zu erklären.

# Ausführung

```powershell
$env:ACT21_HEADLESS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_s1_body_coverage_audit.py --source log\s1-visual-body-20261003 --output log\s1-body-coverage-20261003
```

Für Wiederholung neuen Ausgabeordner wählen. [Ergebnis](/befunde/s1-koerpermodell-abdeckung.md):
224/224 exakte Replays; beide Klauenboxen in 145/224 Fällen außerhalb des Bildes.
`coverage.png` zeigt zwei feste Beispiele (Testpose 0 und 1), Sichtbarkeitsquoten und
Fehler über Gelenkabstand. Geometriemasken sind als `*-evaluation-masks.npz` separat abgelegt.
