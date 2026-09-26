---
type: Messvorschrift
title: S1-Propriozeptionsübergänge - direkte freie Servoerfahrung
description: Ganze Freiraumtrajektorien aus Encoderzustand, direktem Stellwert und Folgezustand für einen künftigen lernenden Servo-Regelkreis; ohne Druck, Kontakt, Objekt, IK oder Teacher.
tags: [act23, dream-rsi, s1, servo, propriozeption]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: codex, at: 2026-09-26T10:00:00Z }
---

# Vertrag

Der Sammler erzeugt 50 freie Rollouts mit je 60 Übergängen. Jeder Rollout beginnt in einem
konservativen inneren Bereich der fünf Armgelenke. Danach werden begrenzte direkte Änderungen
von höchstens 0,025 rad an `m0`–`m4` ausgeführt; `m5` bleibt offen auf Home. Die Stellwerte
bleiben zusätzlich 0,05 rad innerhalb eines äußeren Encoder-Sicherheitsbereichs. Jeder
beobachtete Encoderzustand wird gegen diesen äußeren Bereich geprüft; eine Überschreitung bricht
den Sammler ab und erzeugt keinen Trainingssatz.

Eine Zeile enthält ausschließlich `(q, qvel, ctrl, ctrl_next, q_next, qvel_next)`. Die
Testteilung erfolgt über ganze Rollouts (`rollout_id % 5 == 0`), nie über Nachbarzeilen. Die
Objekte werden vorab außerhalb des Arbeitsraums geparkt, aber weder gelesen noch protokolliert.
Der Pfad enthält keine Druck-, Kontakt-, Kamera-, Objekt-, IK-, BodyModel- oder Teacher-Eingabe.

```powershell
..\rdf_thalamus_sml\.venv\Scripts\python.exe src\pc_cvnn\act23_s1_transition_collector.py `
  --output log\s1-proprio\seed101-50x60 --rollouts 50 --transitions 60 --seed 101
```

# Entscheidungstor

Die Erhebung besteht, wenn exakt 3.000 vollständige Zeilen entstehen, jeder beobachtete
Encoderzustand im äußeren Sicherheitsbereich liegt und der Manifest die ausgeschlossenen
Eingaben bestätigt.
Das ist noch kein Lernerfolg. Erst danach wird ein Vorwärtsmodell auf Trainingsrollouts und
gehaltenen ganzen Testrollouts geprüft; eine Policy oder ACT23-Integration bleibt gesperrt.

# Erste Erhebung verworfen

Die erste Ausführung mit Stellwerten unmittelbar am äußeren Bereich schrieb zwar 3.000 Zeilen,
doch die Encoder erreichten 0,0839 statt mindestens 0,10 rad beziehungsweise 3,0919 statt
höchstens 3,08 rad. Sie ist daher kein Trainingssatz. Der Sammler besitzt nun einen inneren
Stellbereich und eine harte Encoderprüfung; nur eine vollständig bestandene neue Erhebung darf
für das Vorwärtsmodell verwendet werden.

# Ergebnis Seed 101

Die neue Erhebung besteht: 50 ganze Rollouts mit je 60 Übergängen ergeben 3.000 vollständige,
endliche Zeilen. 2.400 stammen aus 40 Trainingsrollouts, 600 aus zehn vollständig getrennten
Testrollouts. Stellwerte liegen in `[0,15, 3,03]` rad, beobachtete Encoder in `[0,1339, 3,0419]`
rad und damit mit Abstand innerhalb des äußeren Bereichs `[0,10, 3,08]` rad.

Das Manifest bestätigt erneut `pressure_sensor_used=false`, `teacher_or_ik_used=false` und
`object_or_contact_observed=false`. Der gültige Trainingssatz liegt unter
`log/s1-proprio/seed101-50x60-safe`; der ältere, ungesicherte Satz bleibt von jedem Training
ausgeschlossen. Der Befund steht in [S1-Propriozeptionsübergänge](/befunde/s1-proprio-uebergaenge.md).
