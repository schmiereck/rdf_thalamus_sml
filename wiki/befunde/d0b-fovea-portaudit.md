---
type: Befund
title: D0b-Portaudit - eingefrorene Fovea-Frames sind erfassbar, Hubdaten fehlen noch
description: Eine eingefrorene Wegwerfepisode schreibt 200 vollständige agentensichtbare Fovea-/Hand-Frames ohne Lernmutation. Sie erreicht jedoch weder Schließen noch Hub; damit ist die Instrumentierung, nicht das Objekt-im-Greifer-Signal, geprüft.
tags: [act23, dream-rsi, d0b, fovea, instrumentation]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: codex, at: 2026-09-23T18:40:00Z }
sources:
  - id: trace
    resource: ../../log/d0b-smoke/seed101-1ep/fovea_frames.jsonl
    title: Ein-Episoden-Fovea-Protokoll
  - id: integrity
    resource: ../../log/d0b-smoke/seed101-1ep/result.json
    title: Eingefrorener Rauchtest
---

# Auditbefund

Die D0b-Sonde schreibt nach einem echten Fovea-Trackschritt ausschließlich agentenzugängliche
Größen: FSM-Phase, Handpose und Gelenkwinkel, Bildraum-Blick und -Folgeposition,
Trackkonfidenz, Fovea-Überraschung sowie Real- und Imaginärteile des zehn-dimensionalen
Topzustands. Objektpose, Kontakt, Weld-Status und Simulatorurteile fehlen.

Gehobene Objekte werden bewusst nicht über die Tischhomographie gelesen. D0b wertet spätere
Mitbewegung im Bildraum zusammen mit eigener Handbewegung aus.

# Rauchtest

Die Wegwerfkopie von `base.pkl` lief mit `ACT23_D0_FREEZE=1`, Seed 101 und einer Episode:

| Prüfung | Ergebnis |
|---|---:|
| Rückgabecode / Runner | 0 / bestanden |
| Episodenprotokoll | 1/1 |
| geänderte Lernkomponenten | keine |
| Fovea-Frames | 200 |
| vollständiger 10D-Re/Im-Topzustand | 200 |
| `frozen=true` | 200 |
| Phasen `over` / `lower` | 75 / 125 |
| Phasen `close` / `lift` / `carry` | 0 / 0 / 0 |

Die Instrumentierung und der Freeze sind bestätigt. Die Episode schloss jedoch nicht und liefert
keinen Hubabschnitt. Das ist kein negatives D0b-Ergebnis: Ohne zwei gültige Blicke über eine
eigene Hubbewegung existiert weder ein Mitbewegungs- noch ein Nicht-Mitbewegungs-Etikett.

# Nächster Schritt

Eine kleine, eingefrorene Abdeckungserhebung zählt zuerst gültige `close`-/`lift`-Bildfolgen und
Enthaltungen. Erst dann werden Split, Selbstetikett, Metriken und Budget für einen Lernvergleich
vorab festgelegt. Die Sonde bleibt ein Wegwerfprotokoll und kein Laufzeitverbraucher.
