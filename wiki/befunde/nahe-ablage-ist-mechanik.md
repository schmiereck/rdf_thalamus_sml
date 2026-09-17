---
type: Befund
title: Der Mindestabstand ist die Mechanik, nicht die Trainingsverteilung - der Teacher kann es auch nicht
description: Zwei Arme je 60 Episoden bei 30 mm Ablageabstand, alles gleich ausser wer die Ablage ausfuehrt. Der geskriptete Teacher hat kein Training und faehrt stur auf das Ziel - er legt genauso weit weg ab wie die Policy (Ueberschuss +25,0 gegen +21,0 mm, p = 0,14) und verschiebt den Nachbarkoerper dabei in 64 Prozent der Ablagen. Eine Ablage unter 35 mm OHNE den Nachbarn anzuruehren gelingt in 3 von 70 Faellen. Damit ist die Lesart "die Saeuberungsregel hat ihre eigenen Daten verhindert" widerlegt - und das Stapeln ruecken diese Zahlen naeher, nicht weiter.
tags: [act23, ablage, stapeln, teacher, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-17T00:00:00Z }
sources:
  - id: ab
    resource: "Zwei kopflose Laeufe je 60 Episoden aus identischen Kopien von act23_state.pkl (ad9d768c), Seed 4242, ACT23_ZIEL_ADRESSE=1 ACT23_ZIEL_ABSTAND=0.03 ACT16_ZIEL_SAEUBERN=0, nur ACT23_CHOREO fsm gegen netz"
    title: Teacher gegen Netz bei 30 mm
  - id: vorher
    resource: /befunde/mindestabstand-zur-ablage.md
    title: Die Dosis-Wirkung, deren Ursachen-Lesart hier widerlegt wird
---

# Die Frage

Der [gemessene Mindestabstand von ~37 mm](/befunde/mindestabstand-zur-ablage.md) hatte zwei
Erklaerungen, die dieselbe Kurve vorhersagen:

* **Trainingsverteilung** - `run_combined` saeubert seit jeher jedes Ziel auf 0,05 m Abstand zu
  jedem Koerper, also lag in der gesamten Vorgeschichte **kein einziges** Ablageziel naeher als
  50 mm an einem Koerper. Die Policy hat die Situation nie gesehen.
* **Klauenmechanik** - neben einem 24-mm-Koerper auf Greifhoehe abzusenken heisst, mit einem
  Finger in ihn hineinzufahren.

Ich hatte die erste als "naechstliegende Ursache" notiert. **Sie ist widerlegt.**

# Der Trennungstest

Der geskriptete Teacher ist eine **reaktive Funktion ohne jedes Training**
(`act16.reactive_subgoal`): er faehrt stur auf `[tgt, GRASP_Z]`, ohne jede Nachbarvermeidung.
Wenn der Mindestabstand aus fehlenden Demonstrationen kaeme, muesste er die 30 mm treffen - er hat
keinen Trainingsrand, von dem er extrapolieren muesste.

Also zwei Arme, alles gleich ausser `ACT23_CHOREO`:

    Arm    Ep  gegriffen  abgelegt  geliefert  Quote  | seitl. Med | zum Bezug Med  Ueberschuss
    lehr   60      42        39        28     46,7 %  |   21,0 mm  |    55,0 mm      +25,0 mm
    netz   60      45        32        20     33,3 %  |   25,0 mm  |    51,0 mm      +21,0 mm

    Ueberschuss (Ist - Soll):  Teacher +25,0 gegen Netz +21,0 mm,  Mann-Whitney p = 0,14
    zu weit in:                Teacher 97,4 %,   Netz 96,8 %
    5. Perzentil Endabstand:   Teacher 31,9 mm,  Netz 32,5 mm
    Quote:                     46,7 gegen 33,3 %,  Fisher p = 0,19

**Der Teacher kann es auch nicht** - er ist, wenn ueberhaupt, eine Spur schlechter. Damit faellt
die Trainingserklaerung: ein Verhalten, das ein untrainierter Regler genauso zeigt, ist nicht das
Ergebnis fehlender Daten.

# Und der Nachbar verraet, was stattdessen passiert

    BEZUGSKOERPER VERSCHOBEN?  (gemessen VOR der Aufraeumschleife, die ihn sonst zuruecksetzt)

      Teacher  25 von 39 = 64,1 %   Median 9 mm, max 45 mm
      Netz     12 von 31 = 38,7 %   Median 1 mm, max 37 mm      Fisher p = 0,053

**Der Arm ruehrt den Nachbarn an, und zwar mehrheitlich.** Dass der Teacher es haeufiger tut, passt
zu seiner Bauart: er senkt entschlossen auf Greifhoehe ab, waehrend die Policy frueher aufgibt.

Getrennt nach Beruehrung wird die Sache eindeutig:

    Arm    Nachbar    n   Ueberschuss  Endabstand   p5      unter 35 mm
    lehr     still   14      +55,5 mm     85,5 mm  38,5 mm      7,1 %
    lehr    bewegt   25      +21,0 mm     51,0 mm  32,6 mm      8,0 %
    netz     still   19      +22,0 mm     52,0 mm  38,3 mm      5,3 %
    netz    bewegt   12      +17,5 mm     47,5 mm  26,2 mm     16,7 %

> **Es gibt kein "nah UND sauber".** Entweder der Arm kommt hin und schiebt den Nachbarn weg, oder
> er bleibt weit weg. Direkt gezaehlt: eine Ablage unter 35 mm **ohne** den Nachbarn anzuruehren
> gelingt **1 von 39** (Teacher) und **1 von 31** (Netz) - zusammen **3 von 70**.

Das naechste Kommen ohne Beruehrung liegt bei 30 mm (Teacher) bzw. 32 mm (Netz), also genau an der
Vorgabe - es ist moeglich, aber selten.

# Was das fuer das Stapeln heisst, und es ist die Umkehrung des Erwarteten

Die Sperre ist **lateral**: die Klaue muss NEBEN einem Hindernis absenken, und dafuer ist sie zu
breit. Beim Stapeln gibt es dieses Hindernis nicht:

> **"auf B" nimmt den Nachbarn aus dem Absenkweg.** Der Bezugskoerper liegt dann UNTER dem
> getragenen Objekt, nicht daneben. Es gibt nichts, wogegen die Klaue seitlich stoesst - sie senkt
> auf die Oberseite ab und oeffnet dort.

Damit ist **"an B" bei kleinem Abstand mechanisch der schwierigere Fall**, nicht der leichtere, und
die Stufenfolge aus [dem Entwurf](/fragen/stapeln-als-aufgabe.md) ist an dieser Stelle falsch
sortiert: die 30-mm-Ablage ist keine Vorstufe des Stapelns, sondern eine eigene, haertere Aufgabe.

Vorausgesetzt ist dabei genau das, was gebaut ist: `ACT16_GOAL_Z` muss die Ablagehoehe auf
Sockeloberseite plus halbe Objekthoehe heben, sonst faehrt die Klaue auf Greifhoehe in die Platte.
Dass zu hoch losgelassen wird, ist unschaedlich - gemessen korreliert der Endfehler mit r = 0,98
am seitlichen Fehler beim Loslassen und **nicht** an der Hoehe
([Ablage und Platzieren](/befunde/ablage-und-platzieren.md)).

**Was damit entfaellt:** der geplante Trainingslauf ohne `ACT16_ZIEL_SAEUBERN`, der dem Teacher
nahe Ablagen abschauen sollte. Es gibt nichts abzuschauen - der Teacher kann sie nicht.

# Fallen

* **Die "stillen" Ablagen sind ausgewaehlt.** Der Teacher beruehrt den Nachbarn nur dann nicht,
  wenn er weit weg gelandet ist; deshalb steht dort +55,5 mm. Das ist kein Beweis, dass der
  Teacher ungenau ist, sondern die andere Seite derselben Muenze.
* **Der Endabstand waechst auch, WEIL der Nachbar wegrutscht.** Er wird zur Endlage beider Koerper
  gemessen. Genau deshalb steht die Aufteilung nach Beruehrung in der Tabelle.
* **Ein Seed je Arm, 60 Episoden.** Die beiden Schluesselzahlen tragen (Beruehrungsrate
  p = 0,053, und die 3 von 70 sind eine Abzaehlung), die Quoten nicht (p = 0,19).
* **Eine Dosis.** Nur 30 mm gefahren; der Uebergang zwischen "geht" und "geht nicht" ist aus der
  [Dosis-Wirkung](/befunde/mindestabstand-zur-ablage.md) bekannt, aber nicht mit diesem
  Beruehrungsmass durchgefahren.
* **`Bezug verschoben` muss VOR der Aufraeumschleife gemessen werden.** Sie setzt jeden
  nicht-kommandierten Koerper auf seine Pose vor der Episode zurueck; danach waere die
  Verschiebung per Bauart immer null. Wer das Mass spaeter abliest, bekommt lauter Nullen und
  schliesst das Gegenteil.
* **Nicht gemessen ist, WELCHES Teil beruehrt.** Finger, Handrueckseite oder das getragene Objekt
  selbst - das entscheidet, ob eine schmalere Klaue helfen wuerde.

# Verwandt

* [Der Arm hat einen Mindestabstand von rund 37 mm](/befunde/mindestabstand-zur-ablage.md) - die Zahlen stehen, die Ursachen-Lesart dort ist hier widerlegt
* [Stapeln als neue Aufgabe](/fragen/stapeln-als-aufgabe.md) - die Stufenfolge, die das hier umsortiert
* [Stufe 2 vorbereitet](/mechanismen/stufe2-vorbereitet.md) - `ACT16_GOAL_Z` ist die Voraussetzung
* [Ablage und Platzieren](/befunde/ablage-und-platzieren.md) - warum zu hoch loslassen nichts kostet
* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) - `ACT16_ZIEL_SAEUBERN` bleibt eine Regel, aber nicht die Ursache
