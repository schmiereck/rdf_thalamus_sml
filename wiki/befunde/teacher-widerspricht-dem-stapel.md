---
type: Befund
title: Der Teacher widersprach dem Stapel - die Ablagehoehe war per Bauart unlernbar
description: Vor dem Lernlauf fuer Frage 2 geprueft, ob die Policy die Ablagehoehe ueberhaupt lernen KANN. Sie konnte es nicht. choreo_log etikettiert jeden besuchten Zustand mit reactive_subgoal, auch in FSM-Laeufen, und diese Funktion las nur die ersten 11 Zustandswerte - die Ablagehoehe als 14. nie. Das Etikett sagte immer "auf 18 mm absenken", unabhaengig vom Ziel, waehrend die FSM auf 26 mm ablegte. Behoben, auf allen 36000 echten Pufferzeilen bitgleich, und der neue Teacher haelt ueber der Auflage dieselbe Freigabe-Marge wie auf dem Tisch.
tags: [act23, stapeln, policy, teacher, dagger]
status: stable
evidenz: gemessen
ebene: code
generated: { by: claude/opus-5, at: 2026-09-19T00:00:00Z }
sources:
  - id: code
    resource: "src/pc_cvnn/pc_act16.py reactive_subgoal, src/pc_cvnn/pc_act23.py choreo_log"
    title: Der DAgger-Teacher und wo er aufgerufen wird
  - id: anlass
    resource: /befunde/stapeln-gemessen.md
    title: Frage 2 - lernt die Policy die Ablagehoehe?
---

# Die Frage, die vor dem Lernlauf stand

Nach [Der Arm stapelt](/befunde/stapeln-gemessen.md) ist offen, ob die **Policy** die Ablagehoehe
lernt - bisher fuhr der Teacher, und die Hoehe kommt als Teacher-Geruest aus dem Simulator. Bevor
man dafuer Stunden rechnet, ist zu pruefen, ob sie es ueberhaupt **kann**. Das haengt nicht an der
Policy, sondern an ihren Etiketten.

# Woher die Etiketten kommen

    def choreo_log(s, _aim, _j5):
        runtime.observe(s, act16.reactive_subgoal(s))      # label the VISITED state, ignore the FSM's own

Jeder besuchte Zustand wird mit `reactive_subgoal` etikettiert - **auch in FSM-Laeufen**, und zwar
ausdruecklich unter Verzicht auf das, was die FSM gerade tut. Das hat einen guten Grund (die FSM hat
eine verborgene Phase, die reaktive Funktion ist markovsch und damit ein gueltiger DAgger-Experte).

Aber `reactive_subgoal` las:

    hx, hy, hz, cx, cy, cz, tx, ty, j5, obj_h, obj_fp = np.asarray(state, float)[:11]

**Die ersten elf Werte.** Die Ablagehoehe steht seit `ACT16_GOAL_Z` an Stelle 14. Der Teacher hat
sie nie gesehen.

# Was er stattdessen etikettierte

Eine Absenkung auf den Sockel, Schritt fuer Schritt, Klaue fest geschlossen, Hand ueber dem Ziel,
Ablagehoehe 22 mm (Sockel-Oberkante 8 mm):

    Hand z   Objekt z |  ALT aim_z  Klaue |  NEU aim_z  Klaue
     90 mm    88 mm   |    18 mm     zu   |    26 mm     zu
     60 mm    58 mm   |    18 mm     zu   |    26 mm     zu
     45 mm    43 mm   |    18 mm     zu   |    26 mm     zu
     38 mm    36 mm   |    18 mm     zu   |    26 mm    AUF
     30 mm    28 mm   |    18 mm    AUF   |      -

    Kontrolle, dieselbe Absenkung auf den TISCH: alt und neu in jeder Zeile gleich.

**Der alte Teacher kommandierte 8 mm in die Platte hinein** und oeffnete 8 mm spaeter - waehrend die
FSM im selben Moment auf der Auflage ablegte. In den 45 Stapel-Episoden des A/B stand damit neben
jedem ausgefuehrten Stapel ein Etikett, das etwas anderes verlangte.

Der **neue** zielt auf 26 mm und oeffnet 12 mm darueber - **genau dieselbe Marge wie auf dem Tisch**
(dort 30 mm ueber 18 mm), nur um die Auflagenhoehe verschoben.

# Der eigentliche Punkt, praezise

Die naheliegende Schlagzeile waere "die Policy haette gelernt, den Stapel in den Sockel zu rammen".
**So hart stimmt das nicht.** Die Platte stoppt die Hand physisch bei ~22 mm, dort oeffnet die Klaue
ohnehin - eine Policy mit alten Etiketten koennte trotzdem stapeln, nur mit Druck auf die Platte.

Der strikte Punkt ist ein anderer:

> **Im alten Etikett war `aim_z` in jeder Zeile 18 mm, voellig unabhaengig von der 14. Spalte.** Aus
> solchen Daten kann ein Netz per Konstruktion nicht lernen, dass die Ablagehoehe vom Ziel abhaengt -
> die Spalte traegt ueber das Etikett keinerlei Information. Frage 2 war damit nicht offen, sondern
> in der vorliegenden Form unbeantwortbar.

# Die Korrektur

    h_auf = max(0.0, state[13] - GRASP_Z) if len(state) >= 14 else 0.0
    if h_auf > 0.0 and |objekt - ziel| < NEAR:
        lift_thresh = lift_thresh + h_auf
    place_z = grasp_z + h_auf

**Zwei Groessen verschieben sich, nicht eine.** Die zweite war beim Bauen nicht offensichtlich: setzt
das Objekt auf der Auflage auf (Mitte 20 mm), laege es unter der Hub-Schwelle (26 mm), gaelte als
"nicht mehr gehoben", und der Greifzweig zielte wieder auf Tischhoehe. Die Schwelle wandert deshalb
mit - **aber nur ueber dem Ziel**, denn nur dort steht die Auflage.

**Verifikation gegen den echten alten Code** (`git show HEAD:`), auf den echten Pufferzeilen des
gelernten Zustands:

    36000 Zeilen (13 Spalten)                          0 Abweichungen
    dieselben Zeilen mit 14. Spalte = GRASP_Z           0 Abweichungen

Ohne `ACT16_GOAL_Z` hat der Zustand 13 Werte, `h_auf` ist 0, und der Teacher ist zeichengenau der
alte.

# Was verseucht ist, und was nicht

**Die Live-Zustandsdatei ist sauber.** Jeder Stapel-Lauf fuhr auf einer Kopie (`ad9d768c`
unveraendert), und diese Kopien sind verworfen. Kein falsches Etikett hat den gelernten Zustand
erreicht.

**Die Messungen dieser Linie sind nicht betroffen.** Alle Stapel-Laeufe fuhren mit dem Teacher
(`ACT23_CHOREO=fsm`), und der folgt der FSM, nicht den Etiketten. Die 45 Stapel in 100 Episoden
stehen.

# Wie Frage 2 jetzt zu messen ist - ohne Freeze-Werkzeug

Die Absicht war ein Vergleich eingefroren gegen lernend am Arm. Es geht billiger und direkter, als
**kontrafaktische Probe am Netz**:

1. N Stapel-Episoden mit dem korrigierten Teacher fahren, Zustand sichern.
2. Aus dem Puffer ECHTE Zustaende der Ablagephase nehmen und nur die 14. Spalte tauschen:
   `GRASP_Z` (Tisch) gegen `GRASP_Z + 0,008` (Sockel).
3. Die gespeicherte Policy vorwaerts rechnen und `aim_z` vergleichen.

**Gelernt heisst: `aim_z` steigt um rund 8 mm, wenn nur die 14. Spalte steigt.** Vorher ist die
Differenz exakt 0, weil die Spalte bei der Migration mit Nullgewichten angehaengt wird. Wiederholt
nach 0, 20, 50, 100 Episoden ergibt das eine Lernkurve, und es braucht keinen Freeze, weil die
Probe ein reiner Vorwaertsdurchlauf ist.

**Die Datenlage ist knapp** und sollte vorher bekannt sein: die Ablagephase macht gemessen **4,4 %**
des Puffers aus ([Ablage und Platzieren](/befunde/ablage-und-platzieren.md)), und davon traegt nur
die Absenkung ueber dem Ziel die Information. Bei ~150-300 Zeilen je Episode sind das grob
**5-10 lehrreiche Zeilen je Stapel-Episode**, in einem Puffer von 24000 mit geschuetztem Kern von
8000. Wie viele Episoden es braucht, ist genau das, was die Lernkurve messen soll.

# Fallen

* **Zwei `pc_act16.py`.** Die `pc_cvnn`-Variante hat `J5_OPEN = 0,54`, also
  `J5_CLOSED_TH = 0,27`. Meine erste Probe setzte `j5 = 0,30` fuer "geschlossen" - das ist dort
  OFFEN, und beide Teacher landeten im Greifzweig. Die Falle stand schon in
  [Ablage und Platzieren](/befunde/ablage-und-platzieren.md); sie hat trotzdem zugeschlagen.
* **Die Probe prueft Etiketten, nicht Verhalten.** Unterhalb der Freigabehoehe zeigt sie bei fest
  geschlossener Klaue "anheben" - dieser Zustand kommt in der Ausfuehrung nicht vor, weil die Klaue
  vorher oeffnet. Er ist auf dem Tisch genauso und unveraendert.
* **Nur der Wuerfel.** Alle Koerper dieser Welt sind 24 mm hoch; fuer andere Hoehen muesste
  `place_z` nicht an `grasp_z`, sondern an der Ruhemitte haengen.

# Verwandt

* [Der Arm stapelt](/befunde/stapeln-gemessen.md) - woher Frage 2 kommt
* [Die Relation "auf", gebaut](/mechanismen/relation-auf-gebaut.md) - wo die 14. Spalte herkommt
* [Stufe 2 vorbereitet](/mechanismen/stufe2-vorbereitet.md) - die Migration auf 14 Spalten
* [Ablage und Platzieren](/befunde/ablage-und-platzieren.md) - 4,4 % Ablagephase im Puffer, und die J5-Falle
* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) - warum der Teacher Privileg haben darf und die Policy nicht
