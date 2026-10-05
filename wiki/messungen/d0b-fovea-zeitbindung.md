---
type: Messvorschrift
title: D0b-F1b - zeitlicher Fovea-Crop auf eigene Fingerbewegung
description: Vorregistrierter zeitlicher Gegenversuch: Ein frischer Kopf sieht nur die zwei Kamerabilder eines eigenen Fingerimpulses und wählt daraus eine Sakkade auf zurückgehaltenen Positionen.
tags: [act23, dream-rsi, d0b, fovea, zeitlich, selbstbewegung]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: codex, at: 2026-09-24T20:00:00Z }
sources:
  - id: data
    resource: ../../log/d0b-hand-mask/seed101-96pose/self_motion_frames.npz
    title: Offene und geschlossene echte Kamerabilder
  - id: eval
    resource: ../../log/d0b-hand-mask/seed101-96pose/eval.jsonl
    title: Getrennte Klauenevaluation
---

# Vertrag

F1b ist eine andere Hypothese als der verworfene F1a-Einzelbildkopf: Ein frischer räumlicher MLP
sieht pro Sakkade die RGB-Differenz zwischen offenem und geschlossenem Kamerabild. Dieses Paar
entsteht durch die eigene Kalibrierhandlung; weder Geometrie noch Kontakt, Homographie oder
Teacher treten als Eingang auf. Ziel bleibt die selbst sichtbare Bewegungsmasse im 24-px-Kreis.

Der Split bleibt 64/32 vollständige Positionen (`pose_id % 3`). Drei feste Initialisierungsseeds
11, 17, 23 werden einmal ausgeführt. Erst nach der Sakkadenwahl wird getrennte Klauengeometrie
bewertet. F1b besteht nur, wenn mindestens zwei Seeds auf den 29 sichtbaren Testpositionen
Median ≤24 px **und** mindestens 12/29 innerhalb 24 px erreichen. Ein Bestehen erlaubt nur einen
folgenden Landmark-Audit, keinen Greifzustandskopf oder Steuerpfad. Bei Verfehlen keine
Hyperparametersuche.

# Ergebnis

F1b verfehlt den Vertrag in allen drei Seeds: Seed 11 erreicht 2/29, Seed 17 5/29 und Seed 23
4/29 innerhalb 24 px; der Median beträgt jeweils 42,4 px. Damit bestehen 0/3 Seeds die
vorgegebenen Tore. Der zeitliche Crop-Kopf wird nicht nachgetunt oder integriert.
