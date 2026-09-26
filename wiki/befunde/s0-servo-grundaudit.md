---
type: Befund
title: S0-Servogrundaudit - fünf druckfreie Gelenkkanäle sind direkt beobachtbar
description: Ein begrenzter direkter Stellimpuls bewegt alle fünf Armservos innerhalb ihrer Grenzen; der Kanal nutzt weder Druck, IK noch Teacher.
tags: [act23, dream-rsi, s0, servo, propriozeption]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: codex, at: 2026-09-26T08:30:00Z }
sources:
  - id: contract
    resource: /messungen/s0-servo-grundaudit.md
    title: S0-Vertrag und reproduzierbarer Befehl
  - id: tool
    resource: ../../src/pc_cvnn/act23_s0_servo_audit.py
    title: Direkter Propriozeptions-Audit
  - id: trace
    resource: ../../log/s0-servo-audit/baseline.json
    title: Ausgeführter druckfreier Basisimpuls
---

# Behauptung

Der Simulator besitzt einen klaren direkten, druckfreien Motorzugang für die fünf Armgelenke.
Er kann die Grundlage eines lernenden Servo-Moduls bilden, ohne kartesische Anfahrt, IK, Teacher
oder Kontakt-/Druckdaten als Voraussetzung zu verwenden.

# Aufbau

Aus Home sendet der Prüfstand einmalig begrenzte Stellwerte direkt über `sim.target` an `m0` bis
`m4`, führt 120 MuJoCo-Schritte aus und protokolliert nur Stellwerte und Encoderwinkel. `m5`
bleibt unverändert. Die Imports und der Ablauf enthalten weder `BodyModel` noch
`reach_velocity`, Objekt-, Kontakt- oder Druckabfragen.[^tool]

# Zahlen

| Größe | Wert |
|---|---:|
| aktive direkte Kanäle | m0–m4 / 5 |
| Gelenkbereich je Kanal | 0 bis π rad |
| Physiktakt / Beobachtungsdauer | 2 ms / 240 ms |
| größter Stellwertrest | 0,00327 rad (0,19°) |
| Greifer / Drucksensor / Teacher oder IK | ausgeschlossen / nein / nein |

Alle fünf Encoder folgten dem Impuls in angeforderter Richtung und blieben innerhalb der
Gelenkgrenzen.[^trace]

# Bewertung

Dies ist ein technischer Prüfstand, kein Nachweis eines Motorlerners oder einer realen
Robotikübertragung. Er entfernt aber eine unnötige Abhängigkeit vom Drucksensor und legt die
erstmals direkt verfügbare, selbst beobachtbare Aufgabe fest: aus eigenen Servoübergängen die
Folge der eigenen Stellwerte lernen.

# Folgen

Der **Aktuatorteil** von S0 ist technisch bestanden; das vollständige S0-Tor verlangt weiterhin
eine abgegrenzte Lernaufgabe und einen Vergleich gegen eine passende Kontrolle. Als nächstes
darf ein Übergangssammler für freie Bewegungen den S1-Entwurf vorbereiten, aber noch kein
lernender ACT23-Motorpfad integriert werden. Greifen, Schließen und Kontakt bleiben bewusst
außerhalb dieses ersten Versuchs.
