---
type: Befund
title: D0b-Portaudit - Fovea-Auswahl ist sichtbar, aber ohne Handbild kein Mitbewegungs-Etikett
description: In zwölf eingefrorenen Episoden sind Fovea-Auswahl und getrennte Simulator-Evaluation vollständig erfasst. Die Auswahl allein unterscheidet einen Fehlgriff jedoch nicht vom Tragen; für das geplante Mitbewegungs-Selbstetikett fehlt eine Bildraumreferenz der eigenen Hand.
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
  - id: selflabel-trace
    resource: ../../log/d0b-selflabel/seed101-12ep/fovea_frames.jsonl
    title: Fovea-Auswahl und Eigenpropriozeption, getrennt nach Trajektorie
  - id: selflabel-eval
    resource: ../../log/d0b-selflabel/seed101-12ep/eval_truth.jsonl
    title: Ausschließlich externe Simulator-Evaluation
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

# Gegenprüfung des Selbstetiketts

Die neue Wegwerfserie (Seed 101, zwölf Episoden) ist vollständig: **3.329** Trace- und genau
**3.329** Evaluationszeilen besitzen dieselbe äußere Episoden-ID und Phase. Alle Trace-Zeilen
sind eingefroren. Die Fovea schreibt nun ihre eigene, klassenkonditionierte Auswahl als
`selection_px` und `selection_mass`; Objektpose, Kontakt und Weld bleiben ausschließlich in
`eval_truth.jsonl`.

| Prüfung | Ergebnis |
|---|---:|
| Episoden-IDs | 1–12, ohne Lücke |
| Fovea-Auswahl vorhanden | 2.809 / 3.329 (84,4 %) |
| Fovea-Auswahl in Hubphase | 320 / 358 (89,4 %) |
| Fovea-Auswahl in Tragephase | 338 / 338 (100 %) |
| extern als getragen markierte Frames | 359 / 3.329 |
| zeitliche Trace-/Eval-Fehlzuordnung | 0 |

Die bloße Sichtbarkeit ist kein Greifzustand. Besonders deutlich ist Episode 9: Sie hat 125
Trageframes mit durchgehend vorhandener Fovea-Auswahl, aber **0 / 125** davon sind extern als
getragen markiert. Vier weitere Carry-Episoden sind dagegen vollständig getragen. Ein positives
Etikett aus „Carry + Auswahl sichtbar“ hätte somit in dieser kleinen Serie 4 von 5 Carry-Episoden
getroffen, würde aber gerade die FSM-Phase als Ersatz für Wahrnehmung verwenden und den
Fehlgriff nicht erkennen. Auch die Auswahlmasse trennt nicht stabil: in der Carryphase liegen die
125 negativen Frames mit 50,7–118,3 im Bereich der positiven Folgen (14,0–114,4).

Das beabsichtigte Kriterium „Kandidat bewegt sich mit der Hand“ kann der vorhandene Trace noch
nicht berechnen. `selection_px` ist eine Objektposition im Kamerabild; die eigene Hand liegt nur
als xyz-Propriozeption vor. Die vorhandene `world_to_px`-Homographie beschreibt ausdrücklich
die Tischfläche und ist oberhalb der Tischhöhe beim Hub ungültig. Eine nachträgliche Projektion
würde daher eine unzulässige, nicht geprüfte Geometrie einschleusen.

# Entscheidung für den nächsten Schritt

Ein lernender Kopf wird nicht angeschlossen. D0b bleibt offen, aber sein nächstes kleines Tor ist
eine **agentenzugängliche Bildraumreferenz der eigenen Hand**: entweder ein aus dem vorhandenen
Fovea-Bild gewonnenes Greifer-Landmark oder eine vorab kalibrierte 3D-Kameraprojektion, die auch
die Hubhöhe abbildet. Sie wird zunächst nur gegen die getrennte Evaluation auditiert. Erst dann
ist ein enthaltendes Mitbewegungs-Selbstetikett möglich. Die Sonde bleibt ein
Wegwerfprotokoll und kein Laufzeitverbraucher.
