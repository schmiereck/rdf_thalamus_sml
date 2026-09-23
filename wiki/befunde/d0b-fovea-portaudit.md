---
type: Befund
title: D0b-Portaudit - eingefrorene Fovea-Frames und Hubabdeckung sind erfassbar
description: Zwölf eingefrorene Wegwerfepisoden schreiben 3.329 vollständige agentensichtbare Fovea-/Hand-Frames ohne Lernmutation, darunter 358 Hub- und 338 Trageframes. Der Trace trägt nun auch eine äußere Episoden-ID; ein Selbstetikett ist noch nicht bewertet.
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
  - id: coverage
    resource: ../../log/d0b-coverage/seed101-12ep/fovea_frames.jsonl
    title: Eingefrorene Hub-Abdeckung, zwölf Episoden
  - id: coverage-integrity
    resource: ../../log/d0b-coverage/seed101-12ep/result.json
    title: Integritätsnachweis der Abdeckungserhebung
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

# Abdeckungserhebung

Die anschließende, ebenfalls eingefrorene Erhebung mit zwölf Episoden besteht die Integritäts-
prüfung: Rückgabecode 0, 12/12 Episodenprotokolle, keine geänderte Lernkomponente und bitgleiche
Basisquelle/-kopie (`ad9d768c...c09b9e`). Sie liefert ausreichende Beobachtungsereignisse für die
nächste, noch rein diagnostische Prüfung:

| Größe | Wert |
|---|---:|
| Fovea-Frames | 3.329 |
| sichtbare Trackbeobachtungen | 3.175 (95,4 %) |
| Schließframes | 501 |
| Hubframes | 358 |
| Trageframes | 338 |
| Frames mit vollständigem 10D-Re/Im-Topzustand | 3.329 |
| Frames mit `frozen=true` | 3.329 |

Das widerlegt die Befürchtung aus dem ersten Rauchtest, die Hubphase sei für die Fovea nicht
beobachtbar. Es zeigt jedoch noch nicht, dass Sichtbarkeit Mitbewegung oder tatsächliches Tragen
trennt.

# Protokollkorrektur

`run_combined` startet seinen inneren Episodenzähler für jeden ACT23-Autoaufruf bei null. Deshalb
erhielten die ersten Trace-Zeilen keine unterscheidbare äußere Trajektorie. Der Trace trägt nun
eine monotone äußere `episode_id`; ein eingefrorener Zwei-Episoden-Rauchtest schreibt bereits die
IDs 1 und 2 ohne Lücke und enthält Hubframes. Damit kann der spätere Split nach ganzen
Trajektorien erfolgen, statt Beinah-Duplikate einer Szene auf Training und Test zu verteilen.

# Nächster Schritt

Auf diesen Gruppen wird nun **offline und ohne Lernupdate** ein Kandidatenetikett geprüft: zwei
sichtbare, aufeinanderfolgende Bildraum-Positionen müssen sich zusammen mit der eigenen Hand
bewegen; unzureichende Sicht bleibt Enthaltung. Erst die Gegenprüfung dieses Selbstetiketts gegen
getrennte Simulatorgrundwahrheit legt Sensitivität, Präzision, Kalibrierung und eine mögliche
Lernaufgabe fest. Die Sonde bleibt ein Wegwerfprotokoll und kein Laufzeitverbraucher.
