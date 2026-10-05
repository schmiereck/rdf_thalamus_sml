---
type: Befund
title: D0 - Ungebunden ist nicht unbekannt
description: Gewachsenes Formgedaechtnis lernt Y nicht neu; frisches Gedaechtnis erkennt Y schnell, verwechselt es aber mit T. Beide D0-Piloten verfehlen das vorab gesetzte Tor.
tags: [act23, dream-rsi, d0, negativ, lernaufgabe]
status: draft
evidenz: einzelmessung
ebene: pruefstand
generated: { by: codex, at: 2026-09-17T18:04:51Z }
sources:
  - id: vertrag
    resource: /messungen/dream-rsi-d0-pilot.md
    title: Vorab fixierter Pilotvertrag
  - id: daten
    resource: log/dream_rsi_d0_20260917/pilot_01/summary.json
    title: Zwei Seeds, Lern-/Freeze-Arme, 24 Y-Trainingssichten je Seed
  - id: einzelurteile
    resource: log/dream_rsi_d0_20260917/pilot_01/observations.jsonl
    title: Einzelurteile und Trainingsereignisse
---

# Behauptung

Der gewachsene Startzustand `ad9d768c` eignet sich fuer die vorgesehene neue Y-Klasse nicht als
Lernaufgabe: Y ist nicht an einen Befehl gebunden, wird aber schon fast immer einer alten
Formklasse zugerechnet. Zwei kurze Lernlinien bringen keine gehaltene Wiedererkennung einer
neuen Klasse. Das ist ein Negativ fuer diese Kombination aus Zustand und Aufgabe, kein
Negativ fuer Dream-RSI oder fuer Selbstlernen allgemein.

# Zahlen

| Seed | Y anfangs als neu gelesen | neue Y-Klasse nach 24 Sichten | Y-Wiedererkennung lernend / eingefroren | bekannte korrekt vorher / nachher |
|---|---|---|---|---|
| 1701 | 1/24 | keine | 0/24 / 0/24 | 26/28 / 26/28 |
| 1702 | 2/24 | keine | 0/24 / 0/24 | 27/28 / 27/28 |

Alle Evaluationsobjekte wurden lokalisiert. Keine Gewichtsveraenderung, eingefrorener
Zustand unveraendert; Lernerzustand aendert sich in seiner Buchhaltung, aber alle vorhandenen
Exemplarsaetze bleiben am Cap von 80. Beide vorab definierten Pilot-Tore sind verfehlt;
Fisher p = 1,0 fuer die jeweils identischen Nullquoten, nur deskriptiv. Messzeit 26,94 s
(ohne Interpreter-/Importstart), ein Worker.

# Aufbau

[Protokoll und Aufruf](/messungen/dream-rsi-d0-pilot.md). Runtime `15c063e`, eigener
Integrationscommit `b351207`; beide Arme verwenden dieselbe XML mit Sockel. Eingabe und
Original haben vor/nach dem Pilot denselben SHA256 `ad9d768c...`. Die archivierte `runner.py`
im Ergebnisordner entspricht dem im Manifest festgehaltenen Quellhash.

# Bewertung und Folgen

Die bisherige Annahme "Y ist ungebunden, also eine neue Lernaufgabe" ist nicht ausreichend.
Die Klasse `neu-9` beansprucht bereits zahlreiche Y-Trainingssichten, die vorhandenen
Exemplarsaetze sind voll. Es waere falsch, jetzt mehr unveraenderte Episoden zu fahren oder
das Nullergebnis als Lernfortschritt des Arms auszugeben.

45/48 gehaltene Y-Sichten zu Beginn und alle 48 Y-Trainingssichten werden `neu-9`
zugerechnet. Das Fehlen einer Befehlsbindung beweist somit keine unbekannte Wahrnehmung.

# Gegenprobe mit frischem Formgedaechtnis, 2026-09-18

Die vorab dokumentierte v2 startet pro Seed mit einem eigenen, ueberwacht auf 2500 cube/L/U-
Beispielen trainierten Klassifikator. Danach lernt nur das Open-Set-Exemplargedaechtnis.
Die Bootstrap-Trainingsgenauigkeit betraegt jeweils 1,0; sie ist kein Testresultat.

| Seed | Y vorab neu | Y lernend / eingefroren nach 3 und nach 24 Sichten | falsche Y-Ansprueche | Kontrollurteile vorher / nachher |
|---|---|---|---|---|
| 1701 | 24/24 | 24/24 / 0/24 | 4/28, alle T | 27/28 / 23/28 |
| 1702 | 24/24 | 24/24 / 0/24 | 4/28, alle T | 28/28 / 24/28 |

Die Kontrollmenge enthaelt 20 bekannte Grundform-Sichten und acht unbekannte T/X-Sichten.
Die vier verschlechterten Urteile pro Seed sind T-Enthaltungen, die zu falschen Y-Anspruechen
werden; kein Beleg fuer Vergessen der Grundformen. An allen Checkpoints ab drei Sichten
bleiben die Quoten gleich. Damit scheitern beide Seeds an der vorab gesetzten Grenze von
hoechstens einem Fehlanspruch und hoechstens einem zusaetzlichen Kontrollfehler. Zusaetzlich
ist die positive Y-Quote schon am ersten Lerncheckpoint gesaettigt.

Fisher p = 6,20e-14 je Seed fuer Y allein, rein deskriptiv; bei zwei Seed-Vergleichen waere
die Bonferroni-Schranke 0,025. Die wiederverwendeten Szenen und nur zwei Trainingslinien
tragen keinen unabhaengigen populationsweiten Wirksamkeitsnachweis. Die verfehlten
Kontrollkriterien werden durch den kleinen p-Wert nicht aufgehoben.

Messzeit 86,69 s einschliesslich zweier Bootstraps (29,99 / 31,91 s), ohne Importstart.
Alle Objekte lokalisiert; Evaluation beeinflusst keine Trainingskopie, Freeze unveraendert,
neuronale Gewichte nach Bootstrap unveraendert. Eingabekopie und Live-Original bleiben bei
SHA256 `ad9d768c...`. Rohbelege: `log/dream_rsi_d0_20260917/pilot_fresh_01/`, insbesondere
`summary.json`, `observations.jsonl`, `manifest.json`, Szenen, archivierter Runner und Vertrag.

# Entscheidung und naechster D0-Schritt

**Beide untersuchten Aufgabenvarianten sind als Scheduler-Benchmark verworfen; D0 bleibt
in Arbeit, sein Tor ist nicht bestanden.** Inventar, eingefrorene Kontrollkopien und
Pilotvertrag sind vorhanden. D1 und Scheduler-Entwicklung sind nicht begonnen.

Die anschliessende [Y/T-Trennbarkeits-Sonde](/befunde/dream-rsi-yt-trennbarkeit.md) beantwortet
die offene Vorfrage: Der Deskriptor traegt ein lokales Signal (LOO-1-NN 90,6 bzw. 92,2 %), aber
die reale Dreisicht-Anspruchsregel beansprucht 29 bzw. 30 von 32 T-Sichten. Damit ist nicht die
vollstaendige geometrische Trennung widerlegt, sondern ihre ausreichende Nutzung im aktuellen
Lernpfad. Eine neue Lernaufgabe braucht weiterhin getrennte Entwicklungs-/Testszenen und
unveraenderte Fehlanspruchskriterien. Keine weiteren Seeds oder laengeren Laeufe desselben
Piloten.

Die parallele Nachricht von Claude (Board, 2026-09-17 22:15 UTC; main `2124e96`,
`wiki/befunde/nahe-ablage-ist-mechanik.md`) ordnet die nahe Ablage einem mechanischen Engpass
zu. Sie wird nicht als Beleg fuer fehlende Trainingsdaten oder als Ersatz-Lernaufgabe
verwendet. Diese D0-Messung bleibt auf Runtime `15c063e` und ist **kein Arm-Lernnachweis**.
