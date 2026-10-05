---
type: Befund
title: D0 Seed 17 - erster 60er-Block ist technische Runner-Validierung
description: Die Rohdaten decken 40 volle Selbst-Kredite und fuenf Wrist-Zellen ab. Der zuerst verwendete Filter zaehlte positive Lieferungen nicht; der Block wird deshalb nicht als regulaere D0-Linie gewertet.
tags: [act23, dream-rsi, d0, wrist, kredit, technische-validierung]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: codex, at: 2026-09-18T14:00:59Z }
sources:
  - id: result
    resource: ../../log/d0-training/seed17-block60/result.json
    title: Urspruengliches Runner-Ergebnis
  - id: credit
    resource: ../../log/d0-training/seed17-block60/credit.jsonl
    title: Unveraendertes maschinenlesbares Kreditprotokoll
---

# Befund

Der erste 60-Episoden-Block auf einer eigenen Seed-17-Kopie lief technisch durch. Sein urspruengliches `result.json` meldete 4 statt 20 gueltiger Kreditzeilen, weil der neue Runner die positive Route `sicher geliefert` nicht als kausale Wrist-Erfahrung zaehlte.

Die Rohdatei wurde nicht geaendert. Mit dem korrigierten, getesteten Filter ergeben sich:

| Groesse | Wert |
|---|---:|
| Kreditzeilen insgesamt | 42 |
| volle Selbst-Kredite mit positiver oder kausaler negativer Aktionsroute | 40 |
| relative Wrist-Zellen | 5 von 8 |
| 60er-Tor | 20 Zeilen und 4 Zellen, in den Rohdaten erreicht |

Die 40 Zeilen bestehen aus 36 `sicher geliefert`, zwei Fehlgriffen am Objekt und zwei Drucksensor-Fehlgriffen. Die Pkl-Kopie unterscheidet sich erwartungsgemaess vom Startzustand; die Live-Pkl blieb unberuehrt.

# Entscheidung

Dies ist keine regulaere Seed-17-Trainingslinie und kein Lernwirkungsbefund. Der Abdeckungsfilter war bei Start nicht vertragskonform implementiert. Nach dem Fix wird Seed 17 auf einer neuen Startkopie als technischer Ersatzblock wiederholt; nur dieser kann in die D0-Auswertung eingehen. Die Rohdaten bleiben als Werkzeugvalidierung erhalten.
