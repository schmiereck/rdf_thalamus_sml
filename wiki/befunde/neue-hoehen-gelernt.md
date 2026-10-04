---
type: Befund
title: Neue Objekthoehen - 32 mm lernt der Agent selbst, 16 mm nicht (die Teacher-Greifhoehe passt nicht)
description: Mit ACT23_HOEHEN=16,24,32 bricht die Policy auf den neuen Hoehen zunaechst ein (Hoehenspalte war im Training konstant und stumm). Zwei Seeds x ~140 Episoden - 32 mm lernt sie robust (27 -> 59 % mit gesagter, 26 -> 77 % mit geschaetzter Hoehe), 16 mm nicht (32 -> 45 %, 28 -> 34 %, n. s.). Gesagt und geschaetzt enden gleichauf (26/49 gegen 27/51 auf neuen Hoehen). Der 16-mm-Fehlschlag liegt beim Teacher - seine Greifhoehe Mitte + 6 mm liegt 2 mm unter der Oberkante.
tags: [act23, hoehe, generalisierung, selbst-lernen, privileg, nutzeridee]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-10-04T00:00:00Z }
sources:
  - id: code
    resource: "bac483e (ACT23_HOEHEN), GroessenSchaetzer (7b697ee), Policy-Schutz (59c85c4)"
    title: Umbau
  - id: lauf2
    resource: "Seed 9012 nachgeholt (je 150 Ep, beide Arme parallel, sonst gleich)"
    title: Zweiter Seed 2026-10-04
  - id: lauf
    resource: "Kopflos, Kopie des Zustands 7a3f7a2d, ACT23_NO_PERSIST=1, ACT23_HOEHEN=16,24,32, ACT23_SZENE_JE_EPISODE=1 ACT23_AUTO_CURIOUS=0 ACT23_EIG_DIREKT=1 ACT23_EIG_STETIG=1 ACT16_GOAL_Z=1 ACT16_GRIFF_Z=1, Choreo netz, Riegel/Reflex aus (Vorgabe). Vorprobe Seed 9001 je 40 Ep (FSM und Netz); Hauptlauf Seed 9011, Arm P ACT23_GROESSE_SEHEN=0 (133 Ep), Arm S =1 (126 Ep), wegen Speichermangels abgebrochen, Seed 9012 nicht gefahren"
    title: Laeufe 2026-10-04
---

# Frage

Nach [Groesse sehen statt wissen](/befunde/groesse-sehen-ab.md) war die Hoehe eine Konstante -
alle Koerper 24 mm, die Policy-Spalte stumm. Die eigentliche Probe auf das [Projektziel](/ziel.md):
greift der Agent Objekte neuer Hoehe, und lernt er sie, ohne dass ihm jemand die Hoehe sagt?

`ACT23_HOEHEN=16,24,32` wuerfelt je Szene fuer jedes stehende Objekt eine Hoehe; alle Teile eines
Koerpers werden gemeinsam gestreckt (Grundriss und Masse unveraendert).

# Vorprobe (Seed 9001, je 40 Episoden)

| Hoehe | Teacher (FSM) | Netz, Hoehe gesagt |
|---|---|---|
| 16 mm (neu) | 3/9 | 1/9 |
| 24 mm | 6/14 | 7/14 |
| 32 mm (neu) | 6/10 | 2/10 |

* **Physik**: alle Hoehen sind greifbar; der Teacher schafft 32 mm gut.
* **Netz ohne Lernen bricht auf neuen Hoehen ein** - die Hoehenspalte war im Training konstant
  ([stumm](/befunde/konstante-spalte-sprengt-policy.md)); die Policy greift auf 24-mm-Hoehe.
  32 mm scheitert ueberwiegend als "Griff hielt nicht".
* **Die Hoehe ist aus dem Bild lesbar**: geschaetzt im Mittel 15 / 25 / 30 mm fuer 16 / 24 / 32 mm
  (32 mm unterschaetzt).

# Hauptlauf (Seed 9011, ~130 Episoden je Arm)

Neue Hoehen = 16 und 32 mm.

| Episoden | Hoehe gesagt (P) | Hoehe geschaetzt (S) |
|---|---|---|
| 0-49 | 4/27 = 15 % | 8/34 = 24 % |
| 50-99 | 15/30 = 50 % | 10/35 = 29 % |
| 100-~130 | 12/21 = 57 % | 12/19 = 63 % |

* Lernen auf neuen Hoehen: P p = 0,005, S p = 0,007 (Fisher, erster gegen letzten Block).
* Am Ende kein Unterschied gesagt gegen geschaetzt (12/21 gegen 12/19, p = 0,76); gesamt 57/133
  gegen 46/126 (p = 0,31) - S lernte in der Mitte langsamer.
* Die bekannte Hoehe 24 mm schwankt in beiden Armen stark (kleine Bloecke).

# Zweiter Seed und beide zusammen

Seed 9012 (je 150 Episoden): gesagt 72/150, geschaetzt 63/150; neue Hoehen 11/25 -> 14/28 bzw.
10/33 -> 15/32 - er startete hoeher und lernte weniger als 9011.

Beide Seeds, je Hoehe, erstes Drittel (Ep 0-49) gegen letztes (Ep 100+):

| Hoehe | gesagt | geschaetzt |
|---|---|---|
| **32 mm** | 8/30 = 27 % -> 16/27 = **59 %** (p = 0,017) | 8/31 = 26 % -> 17/22 = **77 %** (p < 0,001) |
| 24 mm (bekannt) | 57 % -> 75 % (p = 0,19) | 37 % -> 52 % (p = 0,29) |
| **16 mm** | 7/22 = 32 % -> 10/22 = 45 % (p = 0,54) | 10/36 = 28 % -> 10/29 = 34 % (p = 0,60) |

Neue Hoehen zusammen: gesagt 29 % -> 53 % (p = 0,016), geschaetzt 27 % -> 53 % (p = 0,005);
letztes Drittel gesagt gegen geschaetzt 26/49 gegen 27/51 (p = 1,0).

**16 mm scheitert ueberwiegend als "Griff hielt nicht"** (ab Episode 50: 17 bzw. 20 der
Fehlschlaege) - und der Teacher selbst schaffte in der Vorprobe nur 3/9. Ursache sehr
wahrscheinlich die Teacher-Geometrie: `grasp_z = obj_h + GRASP_OFFSET` greift **6 mm ueber der
Mitte**, bei 16 mm also 14 mm - 2 mm unter der Oberkante, ein Griff an der Kante. Ein Schueler, der
den Lehrer imitiert, wird hier nicht besser als der Lehrer ([Greif-Lerndeckel](/befunde/greif-lerndeckel.md)).
Nicht gemessen: ob eine Greifhoehe "Mitte, hoechstens Oberkante - x" den 16-mm-Fall loest.

# Lesart

**Der Agent lernt neue Objekthoehen selbst** - fuer 32 mm robust, aus DAgger und
Selbst-Imitation im laufenden Betrieb, in rund 100 Episoden - und er tut es auch, wenn er die
Hoehe nur aus dem Kamerabild schaetzt. **Fuer 16 mm nicht**, weil schon der Lehrer dort an der
Kante greift. Das ist das erste Ergebnis dieser Reihe, das direkt auf das [Projektziel](/ziel.md)
zahlt: eine neue Eigenschaft der Welt, ohne Etikett zur Laufzeit gelernt.

Vorbehalte, ehrlich:

* **Zwei Seeds**, der erste nach ~130 Episoden durch einen Speicherabbruch beendet; die Seeds
  unterscheiden sich deutlich (9012 startete hoeher und lernte weniger).
* **Der Teacher kennt die Hoehe privilegiert** (`obj_h` im Etikett) - das ist Trainings-Geruest
  nach [laufzeit-regeln.md](/mechanismen/laufzeit-regeln.md). Gelernt ist "aus den Etiketten eines
  hoehenkundigen Lehrers", nicht "aus eigener Beruehrung".
* Der Schaetzer bekam seine Etiketten ebenfalls aus der Geometrie.

# Verwandt

* [Groesse sehen statt wissen](/befunde/groesse-sehen-ab.md)
* [Konstante Spalte sprengt die Policy](/befunde/konstante-spalte-sprengt-policy.md)
* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md)
