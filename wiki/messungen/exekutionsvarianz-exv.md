---
type: Messvorschrift
title: Wiederholungsmessung EXV
description: Dieselbe Szene mehrfach fahren, um Ausfuehrungsstreuung von Situationssignal zu trennen - ICC, Kipp-Anteil und die ehrliche Obergrenze eines situationsbasierten Vorhersagers.
tags: [act23, messen, varianz]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-08-11T12:29:00Z }
verified: { by: human:thomas, at: 2026-08-11T12:29:00Z }
---

# Zweck

Trennt zwei Fragen, die sonst verschmelzen: **streut die Ausfuehrung**, oder **sieht das Modell
die Situation nicht**? Ergebnis der ersten Anwendung:
[Exekutionsvarianz](/befunde/exekutionsvarianz.md).

# Aufbau

```powershell
$env:ACT23_EXV="4"              # M Wiederholungen je Szene
$env:ACT23_EXV_JITTER="0.05"    # optional, rad je Gelenk - fuer die Dosis-Wirkungs-Reihe
$env:ACT23_STATE_HEADLESS="1"   # PFLICHT, sonst frisches Bootstrap-Netz
$env:ACT23_VIZ="1"              # PFLICHT, sonst laeuft main_diag() statt der Messschleife
$env:ACT23_VIZ_HEADLESS="1"     # GUI-Pfad ohne Fenster
.venv/Scripts/python.exe src/pc_cvnn/pc_act23.py
```

Auswertung:

```powershell
.venv/Scripts/python.exe src/pc_cvnn/act23_exv_report.py
```

Unter EXV ist das **Lernen eingefroren**; der Zustand wird nur einmal vor der Messung gesichert.

# Kriterium

* **ICC** ueber die Wiederholungen (Erfolg und Endabstand getrennt)
* **Kipp-Anteil**: Szenen mit gemischtem Ausgang gegen 4/4 und 0/4
* **Ehrliche Obergrenze**: Leave-one-out *innerhalb* der Szene, gegen die Grundrate und eine
  Nullwelt aus Muenzwuerfen

# Fallen

* **Nicht `max(k,n-k)/n` verwenden.** Bei 4 Wiederholungen ist die Formel verzerrt - eine Welt
  aus reinen Muenzwuerfen misst damit schon 68,8 %.
* **Die Wahl ist nicht bitgleich wiederholbar.** Mit `ACT23_WRIST_REL=1` ist das Wrist-Gitter
  armrelativ; eine andere Armstellung verschiebt `w0` (gemessen ~0,1 Grad). Ein binaeres
  "identisch ja/nein" wertet das faelschlich als Aktionswechsel.
* **Die einzige natuerliche Streuquelle ist die Armstellung beim Start**, weil `run_combined`
  mit `arm_reset=False` faehrt. MuJoCo selbst ist hier deterministisch. Streuung heisst also
  immer: versteckte, beobachtbare Zustandsvariable - `sim.arm_angles_full()`.

# Verwandt

* [Kopfloses A/B](/messungen/act23-headless-ab.md)
