---
type: Messvorschrift
title: S0-Servogrundaudit - direkte, druckfreie Propriozeptionsimpulse
description: Erfasst Aktuatorgrenzen und die ausgeführte Gelenkantwort auf einen begrenzten direkten Stellimpuls, ohne IK, Teacher, Objekt, Kontakt oder Drucksensor.
tags: [act23, dream-rsi, s0, servo, propriozeption]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: codex, at: 2026-09-26T08:00:00Z }
---

# Vertrag

S0 beginnt nicht mit Greifen. Der Prüfstand sendet einmalig einen festen, begrenzten
Stellwertimpuls direkt an die fünf Arm-Positionsservos `m0` bis `m4`. Der Greifer `m5` bleibt
auf Home und ist nicht Teil des Aktionsraums. Es werden ausschließlich eigene Stellwerte und
Encoderwinkel vor/nach dem Impuls gelesen.

Der Pfad ruft weder `BodyModel`, `reach_velocity`, kartesische Ziele, Teacher, Objektpose,
Kontaktstatus noch einen Drucksensor auf. Die handgegebene Impulsfolge ist nur eine sichere
Instrumentierungskontrolle und kein Motorlerner.

Ausführbar:

```powershell
..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_s0_servo_audit.py `
  --output log\s0-servo-audit\baseline.json
```

# Entscheidungstor

Das Audit besteht technisch, wenn alle fünf Aktuatoren eindeutige Gelenkgrenzen besitzen, die
ausgeführten Winkel nach 120 Physikschritten endlich und innerhalb ihrer Grenzen liegen und der
Trace nachweist, dass kein ausgeschlossener Eingang gelesen wurde. Erst dann folgt S1 mit
selbst gesammelten Übergängen `(q, ctrl, q')` und einem lernenden, direkten Gelenkpfad.

Ein bestandener Impuls beweist weder Lernen noch Greifen oder Übertragbarkeit auf Hardware. Er
legt nur den sicheren, druckfreien Kanal fest, auf dem diese Fragen später geprüft werden.

# Ergebnis

Der Audit läuft in 120 Schritten zu je 2 ms vollständig durch. `m0` bis `m4` steuern die fünf
Armjoints `joint_0` bis `joint_4`, jeweils mit Bereich `[0, π]`. Der Greifer bleibt bei 0,76 rad
ausgeschlossen. Die direkte Anregung `(+0,06, +0,04, +0,04, −0,03, +0,05)` rad erzeugt an allen
fünf Encodern eine gleichgerichtete Bewegung; der größte Rest zum angeforderten Stellwert liegt
nach 240 ms bei 0,00327 rad (0,19°) an `joint_1`.

Der JSON-Trace weist `pressure_sensor_used=false` und `teacher_or_ik_used=false` aus. Damit ist
der technische S0-Kanal offen. Als nächstes wird kein Handziel vorgegeben, sondern ein
Übergangssammler für eigene Tupel `(q, ctrl, q')` mit getrennten Startlagen gebaut.
