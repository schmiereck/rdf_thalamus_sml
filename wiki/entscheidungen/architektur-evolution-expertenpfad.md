---
type: Entscheidung
title: Architektur darf wachsen, aber nur über isolierte Expertenpfade
description: PC-CVNN und die gewachsene act23-Struktur sind keine festen Vorgaben. Neue Strukturen treten zunächst in isolierten, vorregistrierten Aufgaben gegen klare Baselines an; erfolgreiche Pfade erhalten einen eigenen Integrationsvertrag.
tags: [architektur, selbstlernen, experten, evaluation]
status: stable
evidenz: vermutung
ebene: code
generated: { by: codex, at: 2026-09-24T19:00:00Z }
sources:
  - id: goal
    resource: /ziel.md
    title: Selbstlernen ist wichtiger als Lieferquote
  - id: d0b
    resource: /befunde/d0b-hand-selbstbewegung.md
    title: D0b zeigt die Notwendigkeit eines räumlichen Wahrnehmungszweigs
---

# Entscheidung

Die bestehende PC-CVNN-Struktur und ihre über Monate gewachsenen Module sind ein Bestand, kein
Dogma. Neue Architekturen dürfen entstehen, sich verändern und auch neben PC-CVNN stehen. Sie
werden jedoch nicht direkt in den laufenden Arm eingesetzt.

# Expertenpfad

Ein Architektur-Experte ist zunächst ein kleiner, isolierter Kandidat mit fünf überprüfbaren
Schritten:

1. Er formuliert eine konkrete Wahrnehmungs- oder Lernaufgabe samt eigener, zugänglicher
   Trainingsquelle.
2. Er erhält eine frische Zustandskopie und einen festen Vergleich gegen Konstante oder
   bestehenden Pfad.
3. Er wird nach Szenen, Trajektorien oder Positionen getrennt getestet, nie zeilenweise zufällig.
4. Er dokumentiert Gewinn, Rechenkosten, Enthaltungen und Fehlfälle; ein negatives Ergebnis
   verwirft den Kandidaten statt ihn nachträglich abzustimmen.
5. Nur ein wiederholt bestandener Kandidat erhält einen eigenen Integrationsvertrag: ein
   Verbraucher, Nichtbeeinflussungsnachweis, frischer A/B und Rückfallpunkt.

Die Rolle „Experte“ ist damit kein autonomer ungeprüfter Umbauer. Er erzeugt Varianten,
beurteilt sie gegen vorab gesetzte Tore, verwirft schwache Wege und vertieft nur reproduzierbare
Gewinne. Die Experten selbst können PC-CVNN-Köpfe, räumliche Fovea-Module, zeitliche Modelle oder
andere lernende Ansätze sein.

# Erster Einsatz

D0b-F1a ist der erste solche Pfad: ein separater räumlicher Fovea-Crop-Kopf lernt nur aus eigener
Fingerbewegung und tritt gegen den eingefrorenen Fovea-Zustand an. Seine Messvorschrift steht in
[D0b-F1a](/messungen/d0b-fovea-selbstbewegung.md). Er verändert weder Teacher noch ACT23, bevor
er sein Tor besteht.
