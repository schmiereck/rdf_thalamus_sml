---
type: Befund
title: Groesse des Greifobjekts sehen statt wissen - das Privileg faellt ohne Verlust
description: Die Policy bekam obj_fp/obj_h (halbe Kurzachse und Hoehe des Greifobjekts) aus MuJoCo - faktisch die Kategorie Wuerfel/Balken/Form. Ein GroessenSchaetzer liest beides aus der Detektion (95-98 % richtige Gruppe, Fehler median 0,1 mm). Gepaartes A/B, 8 Seeds x 50 - Privileg 52,2 %, Schaetzung 53,8 %, Seeds 3:3:2 (p = 1,0). Seit 2026-10-03 Vorgabe. Der Weg dorthin fand einen Normierungsfehler in der Policy.
tags: [act23, privileg, groesse, wahrnehmung, ab, laufzeit-regeln]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-10-03T00:00:00Z }
sources:
  - id: code
    resource: "7b697ee (GroessenSchaetzer, ACT23_GROESSE_SEHEN, ACT23_GROESSE_SAMMELN, pc_act16.GROESSE_FN), 59c85c4 (Policy-Schutz Fassung 2)"
    title: Umbau
  - id: lauf
    resource: "Kopflos, Kopie des GUI-Zustands c80448f3 (2026-10-02 16:31), ACT23_NO_PERSIST=1, Seeds 9961-9968 je 50 Ep, ACT23_SZENE_JE_EPISODE=1 ACT23_AUTO_CURIOUS=0 ACT23_EIG_DIREKT=1 ACT23_EIG_STETIG=1 ACT16_GOAL_Z=1 ACT16_GRIFF_Z=1 ACT23_GROESSE_SAMMELN=200, Choreo netz, Marker-Ablage; Arm P ACT23_GROESSE_SEHEN=0, Arm S =1; je Seed parallel"
    title: A/B-Lauf 2026-10-02/03
---

# Frage

Schritt 1 aus der [Bestandsaufnahme der Laufzeitregeln](/mechanismen/laufzeit-regeln.md): die
Groesse des Greifobjekts kam im Policy-Zustand aus der echten Geometrie (`geom_half` in
`run_combined`). Am Code geprueft, bevor gebaut wurde:

* **`obj_h` ist eine Konstante** - alle acht greifbaren Koerper sind 24 mm hoch. Ein Schaetzer
  dafuer allein haette nichts gemessen.
* **`obj_fp` ist das eigentliche Privileg**: 12 mm (Wuerfel), 9 mm (Balken), 6-7 mm (Formen). Die
  Policy bekam damit die Kategorie gesagt.

Ersetzt wird nur, was die POLICY sieht (Spalten 5, 9, 10). Phasen-Buchhaltung, Kredit-Schwellen
und die Laufzeit-Riegel bleiben privilegiert - Geruest bzw. eigener Faden.

# Der Schaetzer

`GroessenSchaetzer` (arm_modules/groessen_schaetzer.py), Bauweise wie der HoehenSchaetzer: lokal
linear aus den 12 naechsten Nachbarn, Merkmale Flaeche, Materialdicke, Spanne, Ort derselben
Detektion. Etiketten aus der Geometrie (Geruest). Gelernt aus allen Tischkoerpern der Szene.
`ACT23_GROESSE_SAMMELN=n` waermt ihn auf n Szenen ohne Arm an (200 Szenen ~40 s; Open-Set-Blick
dabei abgeschaltet - ohne das gebar das Sammeln drei neue Formklassen).

Gehalten ueber die Zeit (je Szene erst schaetzen, dann merken): nach 25 Szenen 86 %, ab 50 Szenen
95-98 % richtige Gruppe, Fehler 0,13 mm. Im Lauf (400 Episoden Arm S): benutzt 400/400, kein
Rueckfall, fp-Fehler median 0,1 mm, 95 % unter 0,5 mm, maximal 5,2 mm.

# Der Umweg: ein Normierungsfehler

Die ersten zwei Anlaeufe waren ungueltig. Die Policy normierte mit `std + 1e-6`; `obj_h` (immer
12,0 mm) hatte damit 1e-6, und 0,1 mm Schaetzabweichung sprengte die Ausgabe (848 mm Netz-Teacher).
Die erste Behebung hielt nur bis zum ersten Nachtraining. Ganze Geschichte:
[Konstante Spalte sprengt die Policy](/befunde/konstante-spalte-sprengt-policy.md). Mit Fassung 2
lag der Netz-Teacher-Abstand in beiden Armen gleich (ueber 40 mm: P 3, S 4 von 400 Episoden).

# Ergebnis

Vorab festgelegt: Seed als Einheit, 8 Seeds, danach Schluss. Paarung 400/400 identische Aufgaben;
Selbst-Urteil widerspricht in keiner Episode (1-4 fehlende Urteilszeilen je Seed, in beiden Armen
dieselben).

| Seed | Privileg | Schaetzung | nur P | nur S |
|---|---|---|---|---|
| 9961 | 22/50 | 28/50 | 4 | 10 |
| 9962 | 27/50 | 27/50 | 4 | 4 |
| 9963 | 28/50 | 27/50 | 8 | 7 |
| 9964 | 27/50 | 24/50 | 8 | 5 |
| 9965 | 26/50 | 26/50 | 6 | 6 |
| 9966 | 18/50 | 22/50 | 5 | 9 |
| 9967 | 28/50 | 32/50 | 5 | 9 |
| 9968 | 33/50 | 29/50 | 7 | 3 |
| **gesamt** | **209/400 = 52,2 %** | **215/400 = 53,8 %** | **47** | **53** |

Seeds 3:3 bei 2 Gleichstaenden (p = 1,0); McNemar p = 0,62; Endabstand 24 gegen 23 mm. Je Objekt
nichts trennbar.

# Lesart

**Das Privileg faellt ohne messbaren Verlust.** Das war die Erwartung - die Schaetzung trifft die
Gruppe fast immer -, und genau das war zu zeigen: ein Stueck Weltwissen, das von aussen kam, kommt
jetzt aus der eigenen Wahrnehmung. Ein Gewinn an Quote war nicht zu erwarten und ist nicht da.

Seit 2026-10-03 ist `ACT23_GROESSE_SEHEN=1` Vorgabe; mit weniger als 200 Zeilen sammelt act23
beim Start selbst.

# Was offen bleibt

* **Etiketten aus dem Tasten** statt aus der Geometrie (Klauenoeffnung beim Halten = gefuehlte
  Breite). Erst dann ist das Privileg auch aus dem Training heraus.
* **`obj_h` ist stumm**, solange alle Koerper gleich hoch sind (Policy-Schutz, Streuung < 0,5 mm).
  Bedeutung bekommt die Hoehe erst mit verschieden hohen Objekten - das ist die eigentliche Probe
  auf Verallgemeinerung.
* Phasen-Buchhaltung, Kredit und Riegel lesen `obj_h` weiter aus MuJoCo (Schritt 3).

# Verwandt

* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md)
* [Konstante Spalte sprengt die Policy](/befunde/konstante-spalte-sprengt-policy.md)
* [Oberkante ohne Privileg](/befunde/oberkante-ohne-privileg.md) - dasselbe Muster beim Stapeln
