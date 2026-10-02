---
type: Befund
title: Eine im Training konstante Eingabespalte sprengt die Policy
description: Die act19-Policy normiert ihre Eingaben mit std + 1e-6. Spalten, die im Training nie variierten - obj_h (immer 12,0 mm) und die Greifhoehe (Spalte 14) -, verstaerken damit jede Laufzeitabweichung um 10^6. 0,1 mm mehr obj_h verschiebt die Ausgabe um 813 mm (im Lauf 848 mm, Episode 0 scheitert). Behoben mit ACT19_KONST_SPALTEN (Vorgabe 1): Spalten mit weniger als 0,5 mm Streuung sind stumm - die erste Fassung (Schwelle 1e-5) hielt nur bis zum ersten Nachtraining. Betraf ausserdem latent jeden Netz-Griff auf einer Auflage.
tags: [act23, policy, normierung, fehler, groesse]
status: stable
evidenz: gemessen
ebene: code
generated: { by: claude/opus-5.5, at: 2026-10-02T00:00:00Z }
sources:
  - id: code
    resource: "src/pc_cvnn/pc_act19.py: Policy.fit/predict, KONST_SPALTEN"
    title: Normierung und Schutz
  - id: lauf
    resource: "Scratchpad gr_9962_P/S.log (A/B Groesse sehen, Seed 9962, Episode 0); Zustand c80448f3"
    title: Fund im A/B
---

# Fund

Im A/B [Groesse sehen](/mechanismen/laufzeit-regeln.md) (Bestandsaufnahme 2026-10-02) scheiterte
der Arm mit geschaetzter Objektgroesse ab **Episode 0** mit 120-240 mm Abstand, der Arm mit dem
Privileg lieferte. Die Schaetzung wich dabei hoechstens 0,5 mm ab. Das Protokoll zeigte den Ort:
`|Netz-Teacher| 848 mm` gegen 10 mm.

# Ursache

`pc_act19.Policy.fit` setzt `isd = X.std(0) + 1e-6`. Im gelernten Zustand sind zwei Spalten im
Training **nie** variiert:

| Spalte | Groesse | isd |
|---|---|---|
| 9 | `obj_h` (alle Koerper 24 mm hoch) | 1e-6 |
| 14 | Greifhoehe `griff_z` (Objekt immer auf dem Tisch) | 1e-6 |

Die kleinste echte Streuung liegt bei 2,0e-3 (Policy) bzw. 1,1e-3 (Welt-Modell, dort keine
konstante Spalte). Eine Abweichung von 0,1 mm wird zu 100 Standardabweichungen.

Offline am gespeicherten Netz, 40 Pufferzeilen:

| | obj_h + 0,1 mm | obj_fp + 0,5 mm |
|---|---|---|
| ohne Schutz | Ausgabe verschiebt sich median **813 mm** (max 899) | 1,42 mm |
| mit Schutz | 0,0 mm | 1,42 mm |

Unveraenderte Eingaben: Ausgaben mit und ohne Schutz gleich bis 2e-10.

# Behebung (zweite Fassung - die erste hielt nur bis zum ersten Nachtraining)

`ACT19_KONST_SPALTEN` (Vorgabe 1), `MIN_SD = 5e-4`: eine Spalte, deren Streuung im
Trainingspuffer unter einem halben Millimeter liegt, ist **stumm** - sie geht mit ihrem Mittelwert
ein (0 nach der Normierung), in `fit` und `predict`, nach jedem Nachtraining neu entschieden.

Die Geschichte dahin, weil sie lehrreich ist:

| Fassung | gespeichertes Netz, obj_h + 0,3 mm | nach Nachtraining mit verrauschtem obj_h |
|---|---|---|
| ohne Schutz | 915 mm | 64 mm (max 167) |
| 1: stumm, wenn isd < 1e-5 | 0 mm | **versagt** - das Schaetzrauschen (0,15 mm) hebt isd auf 3e-5 ueber die Schwelle; im Lauf Episoden 2-8 mit 38-130 mm Netz-Teacher-Abstand |
| Bodenstreuung 1e-3 | 37 mm | 28 mm - die Gewichte einer immer-null-Spalte sind nie trainiert |
| **2: stumm, wenn isd < 5e-4** | **0 mm** | **0 mm** |

Unveraenderte Eingaben: gleich bis 2e-10. Die Grundflaeche (Spalte 10, Streuung 2e-3) bleibt
aktiv (0,5 mm -> 1,4 mm Ausgabe). Die kleinste echte Streuung im Zustand (1,1e-3, Welt-Modell)
liegt ueber der Schwelle. Eine Groesse, die wirklich zu variieren beginnt (Greifhoehe auf
Auflagen, kuenftig verschieden hohe Objekte), wird aktiv, sobald ihre Streuung im Puffer 0,5 mm
uebersteigt - dann muss das Netz sie ab da lernen.

# Folgen

* Das erste A/B "Groesse sehen" ist **ungueltig** (Seed 9961 vollstaendig, 9962 halb, beide mit
  dem Fehler im Arm S), ebenso der Neustart mit Fassung 1 (abgebrochen nach ~33 Episoden je Arm).
  Neu gefahren mit Fassung 2.
* **Latent auch ausserhalb dieses Umbaus:** die Greifhoehe (Spalte 14) weicht ab, sobald ein Objekt
  auf einer Auflage liegt. Ein Netz-Griff auf einem Stapel (Choreo `netz`, `ACT16_GRIFF_Z=1`) lief
  damit in dieselbe Explosion. Die Stufe-4-Messungen liefen mit `ACT23_CHOREO=fsm` und sind davon
  **nicht** betroffen - die Phasenmaschine liest die Policy nicht. Ob GUI-Laeufe mit Choreo Netz
  beim Abstapeln daran scheiterten, ist nicht nachgeprueft (`evidenz: vermutung` fuer diesen Teil).
* Allgemein: wer eine neue Groesse in den Policy-Zustand bringt, die im Puffer konstant war, muss
  mit diesem Schutz rechnen - die Spalte wird ignoriert, bis sie im Training variiert hat.

# Verwandt

* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) - Bestandsaufnahme, Schritt 1
* [Modullandschaft](/mechanismen/act23-modullandschaft.md) - RuntimePolicy
