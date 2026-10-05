---
type: Befund
title: S1-Propriozeptionsübergänge - sicherer, druckfreier Datensatz für den Motorlerner
description: 3.000 ganze freie Servoübergänge bleiben im Encoder-Sicherheitsbereich und enthalten ausschließlich Propriozeption und direkte Stellwerte.
tags: [act23, dream-rsi, s1, servo, propriozeption]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: codex, at: 2026-09-26T11:00:00Z }
sources:
  - id: contract
    resource: /messungen/s1-proprio-uebergaenge.md
    title: Messvertrag samt verworfener erster Erhebung
  - id: tool
    resource: ../../src/pc_cvnn/act23_s1_transition_collector.py
    title: Direkter Übergangssammler mit Encoder-Schranke
  - id: trace
    resource: ../../log/s1-proprio/seed101-50x60-safe/transitions.jsonl
    title: 50 trajektoriengetrennte freie Rollouts
  - id: manifest
    resource: ../../log/s1-proprio/seed101-50x60-safe/manifest.json
    title: Sammlerquittung und ausgeschlossene Eingaben
---

# Behauptung

Für den ersten direkten Motorlerner liegt ein sicherer, druckfreier Übergangssatz aus eigener
Servoerfahrung vor. Er trennt Trainieren und Bewerten nach ganzen Trajektorien und enthält keine
versteckten Objekt-, Kontakt-, IK- oder Teacherinformationen.

# Zahlen

| Größe | Wert |
|---|---:|
| Rollouts / Übergänge | 50 / 3.000 |
| Training / Test, ganze Rollouts | 40 / 10 |
| direkte Kanäle | m0–m4 |
| Stellwerte | 0,15–3,03 rad |
| beobachtete Encoder | 0,1339–3,0419 rad |
| äußerer Encoderbereich | 0,10–3,08 rad |
| Druck, Kontakt, Objekt, IK, Teacher | nein / nein / nein / nein / nein |

Der erste Sammlerversuch ist nicht Teil dieses Satzes: seine Encoder überschritten den damals
fehlenden Rand um höchstens 0,016 rad. Die neue harte Schranke und der innere Stellbereich
verhindern diesen Fehler.[^contract]

# Bewertung

Der Satz belegt keinen lernenden Regelkreis. Er ist die nötige, realitätsnähere Grundlage dafür:
Ein Vorwärtsmodell muss auf den 40 Trainingsrollouts die nächsten Encoderwerte vorhersagen und
auf den zehn unbekannten Rollouts bestehen. Erst dann wird eine direkte inverse Aktion oder
eine geschlossene Regelung erprobt.
