---
type: Befund
title: Loslassen am Ziel - der Agent laesst selbst los und lernt aus dem eigenen Ergebnis, wo es klappt
description: Die Policy liess am Ziel nie los (Teacher-Fehler ACT16_ABLAGE_FIX; ein Netz fuer alles). Ein Loslass-Kopf aus Einzelaspekten laesst selbst los, oeffnete aber zu frueh. Mit einem ERFOLGSNETZ, das aus dem eigenen Ergebnis lernt (Pose beim Loslassen -> Selbst-Urteil der Kamera) und ein Veto hat, gelingt das Loslassen in 81 statt 72 % der Faelle, und nach der Lernphase liefert der Agent genau so gut wie mit der Aufraeumbewegung (102/200 gegen 102/200, Intervall +-9,8, 4 Seeds). Die Lernphase kostet 11 Punkte (n. s.). Allein entscheidend liess das Erfolgsnetz wild los (93 mm daneben).
tags: [act23, loslassen, teacher, aspekte, nutzeridee, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-10-05T00:00:00Z }
sources:
  - id: code
    resource: "d8f100e (ACT16_ABLAGE_FIX, LoslassKopf, ACT23_LOSLASS_KOPF, ACT16_ENDE_HALTEN, Einrasten, losgelassen nur ueber dem eigenen Ziel)"
    title: Umbau
  - id: lauf
    resource: "Kopflos, Kopie des Zustands 7a3f7a2d, ACT23_NO_PERSIST=1, Seeds 9061-9062 je 50 Ep (9063 abgebrochen), Vorgaben inkl. ACT16_ENDE_SELBST; Arm E heute, Arm L ACT16_ABLAGE_FIX=1 ACT23_LOSLASS_KOPF=1 ACT16_ENDE_HALTEN=30; je Seed parallel"
    title: A/B 2026-10-05 (abgebrochen)
---

# Ausgangslage

Seit [Episodenende selbst](/befunde/episodenende-selbst.md) bekannt: die Policy senkt am Ziel ab
und haelt fest; geoeffnet hat immer die Aufraeumbewegung. Puffer: Ablage-Zustaende 1,7 % der
DAgger-Zeilen (Etikett 98 % "oeffnen", Netz 28 %), Selbst-Imitation 0 % "oeffnen".

# Ursache 1: der Teacher

`grasped = (cz > lift_thresh) and (j5 < J5_CLOSED_TH)`, `lift_thresh = obj_h + 14 mm`. Beim
Absenken auf die Ablagehoehe faellt die Objektmitte unter 26 mm, **bevor** die Hand die
Ablagehoehe erreicht - ab dort etikettierte der Teacher "Klaue zu -> anheben", als laege das
Objekt an der Greifstelle. Die Loslass-Regel war nur im Uebergang erreichbar. Sichtbar wurde das
in der Aspekt-Sicht: 240 widerspruechliche Etiketten in der Region "Hand am Ziel, unten, haelt".

`ACT16_ABLAGE_FIX`: in Zielnaehe (Objekt und Hand innerhalb `SENK_NAH`) mit geschlossener Klaue
gilt das Objekt als gegriffen. An der Greifstelle greift das nie (Ziel >= 6 cm entfernt). Beim
Laden werden die betroffenen Zeilen neu etikettiert: 461 DAgger, 128 Selbst-Imitation.

# Ursache 2: ein Netz fuer alles

Auch mit korrigierten Etiketten oeffnet die gemeinsame Policy am Ziel nicht (Greiferwert median
0,07; > 0,30 in 14 %). Ein eigener **Loslass-Kopf** ([Aspekt-Rueckmeldung](/fragen/aspekt-rueckmeldung.md)),
zeitlich gehaltener Pruefsatz, korrigierte Etiketten:

| Kopf | oeffnet am Ziel | oeffnet > 5 cm vom Ziel |
|---|---|---|
| ganzer Zustand | 35 % | 22 % |
| 5 Einzelaspekte | 99 % | 0 % |

Restliche Fehlalarme nur in Zielnaehe (<= 14 mm) und 16-18 mm ueber der Ablagehoehe.

Im Lauf: Entscheidung **eingerastet** (sonst pendelte die Klaue um 0,27, weil der Kopf nur bei
gehaltenem Objekt urteilt), Ende "losgelassen" **nur ueber dem eigenen Ziel** (sonst beendete ein
leerer Nachgriff nach verlorenem Objekt die Episode).

# Lauf (abgebrochen nach zwei Seeds)

| Seed | heute (E) | selbst loslassen (L) |
|---|---|---|
| 9061 | 28/50 | 24/50 |
| 9062 | 26/50 | 22/50 |

Seed 9061 im Detail: L laesst in 18 von 19 Ankuenften selbst los (19 von 28 "losgelassen"-Enden
geliefert, E 25 von 34 "am Ziel abgesetzt"). Geoeffnet wird mit dem Objekt **14-15 mm ueber der
Ruhelage** und **15-43 mm seitlich** - der Kopf oeffnet am Rand seiner Zone und bildet den
grosszuegigen Teacher-Rand nach (bis 12 mm hoch, bis 20 mm seitlich). Dazu endet L oefter ueber
das Zeitbudget (19 gegen 15) mit doppelt so vielen "Griff hielt nicht" (10 gegen 5) -
Verdacht: das Nachtrainieren auf den umetikettierten Puffer hat das Greifen veraendert
(ungeprueft).

# Lesart

**Der Agent kann jetzt selbst loslassen** - aus einem gelernten Aspekt-Kopf, nicht aus einer
Regel. **Er ist dabei noch schlechter als die Aufraeumbewegung**, und das mit zwei benennbaren
Gruenden. Vorgabe bleibt aus (`ACT23_LOSLASS_KOPF=0`, `ACT16_ABLAGE_FIX=0`).

Naechste Schritte: (1) offline pruefen, ob die Umetikettierung das Greifen verschlechtert;
(2) erst loslassen, wenn die Hand einige Schritte ruhig ueber dem Ziel steht; (3) neu messen.

# Verwandt

* [Aspekt-Rueckmeldung](/fragen/aspekt-rueckmeldung.md)
* [Das Episodenende entscheidet der Agent selbst](/befunde/episodenende-selbst.md)

# Nachtrag 2026-10-06: Schritte 1 und 2

**1. Schadet die Umetikettierung dem Greifen?** Nein, kaum. Offline, beide Netze ohne die letzten
20 % nachtrainiert: Greifen 6,0 gegen 7,5 mm Median-Abstand zum Teacher, Anfahren 5,0 gegen 4,5,
Tragen und Ablegen gleich. Und im zweiten Seed war der Griff-Unterschied weg ("Griff hielt nicht"
17 heute gegen 15 selbst) - die Verdopplung in Seed 9061 war Zufall.

**2. Erst bei ruhiger Hand entscheiden** (`ACT23_LOSLASS_RUHIG=5`): im Rauchtest (6 Episoden)
**wirkungslos** - der Agent oeffnet weiter mit dem Objekt 14-15 mm ueber der Ruhelage und 19-30 mm
seitlich. Die Hand STEHT dort ruhig; die Policy haelt das Objekt so.

**Warum der Kopf dort oeffnet:** auf dem Pruefsatz gibt es keine Fehlalarme weiter als 25 mm
seitlich, im Lauf oeffnet er bei 28-43 mm. Die Haltepose im Lauf (ruhig, 14 mm hoch, 30 mm daneben)
liegt ausserhalb dessen, was der Teacher je etikettiert hat - dort extrapoliert der Kopf. Im Kern
ist er zudem unsicher (Ausgabe median 0,64), weil der Teacher selbst grosszuegig ist (oeffnet bis
12 mm hoch, 20 mm seitlich). Ein Hoehenaspekt nach `place_z` statt `tgt_z` aendert nichts, solange
alle Objekte gleich hoch sind.

**Ehrliche Einordnung des Episodenendes:** das selbst entschiedene Ende ist eine von Hand
geschriebene Regel auf eigener Wahrnehmung ("Hand innerhalb 25 mm ueber dem eigenen Ziel, unten,
haelt"), kein gelerntes Urteil. Es ersetzt ein Privileg, ist aber selbst eine Laufzeitregel.

Schritt 3 (neues A/B) **nicht gefahren** - es haette mit hoher Wahrscheinlichkeit den Verlust
wiederholt. Der naheliegende Weg ist die volle [Aspekt-Rueckmeldung](/fragen/aspekt-rueckmeldung.md):
den Kopf mit dem **eigenen Ergebnis** etikettieren (Kamera nach dem Loslassen: liegt es im Ziel?)
statt mit dem Teacher - genau in der Haltepose, die im Lauf vorkommt.

# Nachtrag 2026-10-06: aus dem eigenen Ergebnis lernen (Nutzeridee, volle Form)

`ACT23_LOSLASS_SELBST` (Vorgabe 0): nach jeder Episode, in der getragen wurde, bekommt die Pose,
in der losgelassen wurde (vom Kopf, oder die letzte Haltepose vor der Aufraeumbewegung), das
**Selbst-Urteil der Kamera** als Etikett. Ein zweites kleines Netz im `LoslassKopf` lernt daraus
"klappt Loslassen hier?" aus denselben fuenf Aspekten. Kein Teacher.

**Sammellauf** (heutiges Verhalten, 36 Episoden): 19 von 20 Faellen gut - die Aufraeumbewegung
oeffnet nur ueber dem Ziel, Gegenbeispiele entstehen so kaum. Abgebrochen; die 20 Faelle bleiben
als Startwissen.

**Erste Fassung - das Erfolgsnetz entscheidet allein:** gescheitert. Aus 30 guten und 6
schlechten Faellen nahe am Ziel lernte es pauschal "klappt schon" und liess bei 93 und 54 mm
neben dem Ziel und 41 mm hoch los (11/30 gegen 18/30). Es weiss nicht, was es nicht weiss.

**Zweite Fassung - Veto:** der Teacher-Kopf schlaegt vor, das Erfolgsnetz streicht Posen, an
denen Loslassen nach eigener Erfahrung scheiterte. Gepaartes A/B, Arm E heute (Ende selbst,
Aufraeumbewegung oeffnet), Arm S Teacher-Kopf + Erfolgs-Veto (+ ABLAGE_FIX, ENDE_HALTEN 30),
75 Episoden je Seed aus einem Zustand mit den 20 gesammelten Faellen; der dritte Seed wurde nach
70 Episoden wegen Speichermangels abgebrochen:

| Seed | Ep 0-24 E / S | Ep 25+ E / S |
|---|---|---|
| 9081 | 14 / 11 | 28/50 / 29/50 |
| 9082 | 15 / 11 | 21/50 / 25/50 |
| 9083 | 14 / 12 | 25/45 / 23/45 |
| **gesamt** | **57 % / 45 %** (p = 0,19) | **51,0 % / 53,1 %** (p = 0,81) |

Wie gut das eigene Loslassen gelingt (Selbst-Urteil): Teacher-Kopf allein (Lernphase) 28 von 39 =
72 %, mit Erfolgs-Veto **59 von 71 = 83 %**; seitlich gleich (median 11-14 mm).

**Lesart:** der Agent laesst am Ziel **selbst** los und lernt **aus dem eigenen Ergebnis**, wo das
klappt - die Erfolgsrate des Loslassens steigt von 72 auf 83 %. Nach der Lernphase liefert er so
gut wie mit der Aufraeumbewegung; die Lernphase selbst kostet (45 gegen 57 %, n. s.). Das ist die
erste Komponente, die eine Entscheidung aus eigener Erfahrung ohne Teacher-Etikett verfeinert
([Aspekt-Rueckmeldung](/fragen/aspekt-rueckmeldung.md)). Vorgabe bleibt vorerst aus; mit
persistiertem Zustand (GUI) faellt die Lernphase nur einmal an.

# Vollstaendiger Durchgang (2026-10-06, nach Speicherfreigabe)

Seed 9083 komplett neu (der abgebrochene Teil war bis Episode 69 identisch), Seed 9084 dazu;
9081/9082 wie oben (deterministisch, ein erneuter Lauf waere bitgleich).

| Seed | gesamt E / S | Ep 25-74 E / S |
|---|---|---|
| 9081 | 42 / 40 | 28 / 29 |
| 9082 | 36 / 36 | 21 / 25 |
| 9083 | 41 / 35 | 27 / 23 |
| 9084 | 42 / 39 | 26 / 25 |
| **Ep 0-24** | **59 % / 48 %** | Differenz -11 [-24,7, +2,7], p = 0,16 |
| **Ep 25-74** | | **102/200 / 102/200**, Differenz 0,0 [-9,8, +9,8], Seeds 2:2, McNemar 26:26 |

Loslassen gelungen (Selbst-Urteil): Teacher-Kopf allein 36/50 = 72 %, mit Erfolgs-Veto
**80/99 = 81 %**.

**Endgueltige Lesart:** nach der Lernphase laesst der Agent selbst los und liefert genau so gut
wie mit der Aufraeumbewegung; ein Schaden ueber 10 Punkte ist ausgeschlossen. Das Erfolgsnetz
macht das eigene Loslassen messbar treffsicherer (72 -> 81 %). Die Lernphase (rund 25 Episoden)
kostet etwa 11 Punkte - in der GUI mit persistiertem Zustand faellt sie einmal an.

**In der Steuer-GUI eingeschaltet (Nutzerentscheid 2026-10-06):** `ACT16_ABLAGE_FIX=1`,
`ACT23_LOSLASS_KOPF=1`, `ACT23_LOSLASS_SELBST=1`, `ACT16_ENDE_HALTEN=30` werden nur bei
`ACT23_VIZ=1` ohne `ACT23_VIZ_HEADLESS` gesetzt; kopflose Messlaeufe behalten die alten Vorgaben.
Die Umetikettierung beim Start fasst nur noch nicht korrigierte Zeilen an (sonst trainierte jeder
GUI-Start die Policy nach). Die Erfahrung des Erfolgsnetzes wird mit dem Zustand gespeichert.
