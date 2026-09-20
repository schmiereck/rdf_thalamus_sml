---
type: Befund
title: Die Policy stapelt selbst - so gut wie der Teacher
description: Erster Stapellauf, in dem die gelernte Choreographie faehrt statt der FSM. Aus demselben trainierten Stand je 50 Episoden - 16 von 19 beurteilten Ablagen liegen auf dem Sockel gegen 18 von 20 beim Teacher (p = 0,66), Objektmitte in beiden Armen +11 mm ueber der Auflage, Lieferquote 46 gegen 44 Prozent. Die Ausfuehrung des Teachers ist damit entbehrlich. Was NICHT gefallen ist, ist das Privileg - die Auflagenhoehe steht weiter im Zustand und kommt aus dem Simulator.
tags: [act23, stapeln, policy, selbstlernen, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-20T00:00:00Z }
sources:
  - id: ab
    resource: "Zwei kopflose Laeufe je 50 Episoden aus DERSELBEN Kopie eines 200-Episoden-Trainingsstands (Seeds 5242-5245 auf act23_state.pkl ad9d768c), Seed 6001, ACT23_ZIEL_MISCH=0.5 ACT23_SOCKEL_WANDERT=1 ACT23_SOCKEL_HOEHEN=6,10,14 ACT23_SCENE_N=3 ACT23_SCENE_EVERY=2; Unterschied allein ACT23_CHOREO netz gegen fsm"
    title: Netz gegen Teacher beim Stapeln
  - id: vorher
    resource: /befunde/gemischt-lernen-zweiter-lauf.md
    title: Der Trainingslauf, aus dem beide Arme starten
---

# Die Frage

Alle bisherigen Stapel-Messungen liefen mit dem Teacher am Steuer; gemessen wurde nur, was die
Policy **ausgeben wuerde**
([kontrafaktische Probe](/befunde/gemischt-lernen-zweiter-lauf.md)). Offen war, ob sie auch
stapelt, wenn sie **selbst faehrt**.

Beide Arme starten aus **derselben Kopie** desselben Trainingsstands und unterscheiden sich allein
in `ACT23_CHOREO`. Der Teacher-Arm ist noetig, weil der Stand sich waehrend der 50 Episoden
weiterentwickelt: ohne ihn waere nicht zu trennen, ob ein Unterschied am Fahrer liegt oder an der
Szenenfolge.

# Zahlen

    Arm            Ep | Marker | Stapelauftrag  Rueckfall | beurteilt  LIEGT DRAUF | geliefert
    netz           50 |   23   |      27            0     |    19       16 = 84 %  |    23
    Teacher (fsm)  50 |   24   |      26            0     |    20       18 = 90 %  |    22

    LIEGT DRAUF je beurteilter Ablage:  16/19 gegen 18/20   Fisher p = 0,66
    Stapel je Episode:                  16/50 gegen 18/50   Fisher p = 0,83
    Objektmitte ueber der Auflage:      +11 mm in BEIDEN Armen   (Soll +12)
    Lieferquote:                        46 % gegen 44 %

> **Die Policy stapelt selbst, und zwar so gut wie der Teacher.** Kein Unterschied in der
> Stapelrate, kein Unterschied in der Hoehe, auf der das Objekt zu liegen kommt.

Nebenbei: **beide Arme loesen die Zieladresse in 100 % der Stapelauftraege auf** (0 Rueckfaelle,
gegen 86 von 100 im Lauf davor). Der Sockel ist dem Agenten nach 200 Episoden vertraut genug, dass
die klassenlose Adresse ihn zuverlaessig trifft.

Ein Unterschied bleibt: die Policy **laesst hoeher los** (Fallhoehe im Median 23 gegen 15 mm) und
legt etwas weiter aus der Mitte ab (Versatz 16 gegen 12 mm). Beides ohne Folge - die Auflage ist
35 mm halbbreit, und dass die Fallhoehe nicht schadet, ist gemessen
([Ablage und Platzieren](/befunde/ablage-und-platzieren.md), r = 0,98 auf den seitlichen Fehler).

# Was damit gefallen ist - und was nicht

**Gefallen ist die Ausfuehrung des Teachers.** Die geskriptete Choreographie wird fuer das Stapeln
nicht mehr gebraucht; sie bleibt, was sie sein soll - ein Trainingssignal.

**Nicht gefallen ist das Privileg.** Die Auflagenhoehe steht weiter als 14. Wert im Zustand und
stammt aus dem Simulator (`GRASP_Z + Oberkante`, s.
[Die Relation "auf"](/mechanismen/relation-auf-gebaut.md)). Die Policy handelt danach, aber sie
ermittelt sie nicht. Nach [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) ist der Zustand damit
**noch nicht** privilegienfrei.

> Gezeigt ist: die Policy kann auf die Hoehe HANDELN. Nicht gezeigt: dass sie die Hoehe SEHEN
> kann. Das ist Stufe 3, und der gemessene Weg dorthin ist die Farbstreuung
> ([Der Sockel verschluckt den Stapel](/befunde/sockel-verschluckt-den-stapel.md)).

# Fallen

* **Ein Seed je Arm, 50 Episoden.** Bei p = 0,66 ist das eine Aussage ueber die ABWESENHEIT eines
  grossen Unterschieds, keine Gleichheitsaussage. Ein Rueckstand von zehn Prozentpunkten waere
  darin nicht zu sehen.
* **Beide Arme lernen weiter** (lifelong wie immer). Der Netz-Arm sammelt dabei Selbst-Imitation,
  der Teacher-Arm nicht - nach 50 Episoden ist das ein kleiner Unterschied, aber kein Nullunterschied.
* **Der Trainingsstand wurde neu erzeugt**, weil ich den alten beim Aufraeumen geloescht hatte.
  Deterministisch reproduziert, aber nicht bitweise gegen den dokumentierten Stand geprueft.
* **Die Stapelbewertung ist privilegiert** (Objektmitte ueber der Auflage). Der Selbstrichter
  taugt dafuer nicht, s. unten.
* **Der Selbstrichter bleibt offen.** Er sagte in einer frueheren Messung auch bei Fehlablagen
  neben dem Sockel "geliefert" ([Der Arm stapelt](/befunde/stapeln-gemessen.md), 6 von 9). Solange
  das gilt, darf die Selbst-Imitation dieser Aufgabe nicht getraut werden.

# Verwandt

* [Die Policy legt auf jeder Sockelhoehe richtig ab](/befunde/gemischt-lernen-zweiter-lauf.md) - der Trainingsstand und die kontrafaktische Probe
* [Die Relation "auf", gebaut](/mechanismen/relation-auf-gebaut.md) - woher die Hoehe im Zustand kommt
* [Der Sockel verschluckt den Stapel](/befunde/sockel-verschluckt-den-stapel.md) - der Weg zu Stufe 3
* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) - was "Geruest gefallen" heisst und was nicht
