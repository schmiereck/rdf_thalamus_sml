---
type: Befund
title: Klauenlage am Balken und Griffversatz beim Zufassen - die Wahl ist frei, der Versatz unsichtbar
description: Der Balken wird nicht quer gegriffen, weil das Weltmodell es nicht muss - Wahrnehmung (5 Grad) und Ausfuehrung (0 Grad) sind genau, gewaehlt wird ueber 30-90 Grad, und die Lieferung haengt nicht am Winkel (65 gegen 63 Grad, p = 0,98). Beim Zufassen sieht der Agent die Objektmitte auf 1-4 mm am Griffpunkt, tatsaechlich liegt sie 4-14 mm daneben - und nur dieser wahre Versatz sagt die Ablage vorher.
tags: [act23, wrist, weltmodell, greifen, ablage, messung]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-10-11T06:00:00Z }
sources:
  - id: kette
    resource: "Dasselbe, Seed 9404, 60 Episoden L/U/T/X, Messzeile [Versatzkette] aus dd701c5"
    title: Versatzketten-Lauf
  - id: balken
    resource: "GUI-Steuerung kopflos, Seed 9403, 60 Episoden ACT23_AUTO_OBJ=obj_blue, Szene je Episode, Farb-Mischung an, Kopie des Hauptzustands 2f70ac0d, NO_PERSIST, Messzeilen aus 158c866"
    title: Balkenlauf
  - id: versatz
    resource: "Dasselbe, Seed 9402, 60 Episoden ACT23_AUTO_OBJ=obj_L,obj_U,obj_T,obj_X"
    title: Griffversatz-Lauf
  - id: verluste
    resource: /befunde/verluste-nach-dem-anheben.md
    title: Verluste nach dem Anheben (Anlass, offener Punkt)
---

# Anlass

Nutzerfrage 2026-10-11: *"ob wir in einem Trainings-Lauf mit nur I Formen, in verschiedenen
Ausrichtungen, in verschiedenen Farben, die alle in gut erreichbarer Position liegen, beobachten
koennen, ob der Greifer sich immer quer zur Laengsachse ausrichtet. Nach meinen Beobachtungen hat
er da auch Probleme ... was ich mir nicht richtig erklaeren kann."* Dazu der offene Punkt aus
[Verluste nach dem Anheben](/befunde/verluste-nach-dem-anheben.md): sagt der selbst gewaehlte
Griffpunkt den seitlichen Versatz beim Absetzen vorher?

Zwei reine Log-Zeilen (158c866) beim ersten Zufassen, beide gehen in keine Entscheidung:

* `[Klauenlage]` - Winkel Fingertrennachse gegen wahre Laengsachse (gefaltet 0-90, 90 = quer) und
  die Kette **Achse gesehen -> Klaue geplant -> Klaue ausgefuehrt**.
* `[Griffversatz]` - Objektmitte gegen Reichpunkt im Klauenrahmen, einmal **gesehen** (Blob-
  Schwerpunkt gegen gewaehlten Griffpunkt + Versatz), einmal **wahr** (MuJoCo).

# Aufbau und Einschraenkungen

* Es gibt nur **einen** Balken (`obj_blue`, 68 x 18 mm). "Nur I-Formen" ist nicht ohne neue Koerper
  baubar; die Szene verlangt mindestens 3 Objekte, also lagen Ablenker daneben. Lage und Gier je
  Episode neu (gleichverteilt 0-pi), Farbe per Farb-Mischung je Episode getauscht.
* **Messaufbau-Falle (27 von 60 Episoden verloren):** Die Szenenrotation parkt in jeder zweiten
  Episode genau den kommandierten Balken. act16 stellt das Kommando-Objekt zwar zurueck auf den
  Tisch, die Farbbindung (`colour_of_body`) ist zu diesem Zeitpunkt aber schon ohne ihn gesetzt.
  Der Balken laeuft ueber die Farbklasse (`method == "long"`), findet keine und gibt auf
  (`Farbklasse None ungeboren -> NICHT GEFUNDEN`): **26 von 26 Episoden mit geparktem Balken nicht
  gefunden, 0 von 34 sonst.** Formen ueber die Formklasse trifft das nicht (im Versatz-Lauf liefern
  9 von 26 "geparkt" kommandierten Formen trotzdem). Betrifft nur erzwungene Kommandos
  (`ACT23_AUTO_OBJ`), nicht den Normalbetrieb. Ausgewertet sind die 34 Episoden mit Balken auf dem
  Tisch; davon 32 zugefasst, 24 geliefert (71 %).

# Zahlen: Klauenlage am Balken (n = 32 Zugriffe)

    Winkel Klaue gegen Laengsachse (90 = quer)
      0-15  15-30  30-45  45-60  60-75  75-90
       0      0      6      7     14      5        Median 65 Grad

    Achse gesehen gegen wahr     Fehler Median 5 Grad, Q90 20
    ausgefuehrt gegen geplant    Median 0 Grad, Q90 2
    geplant relativ zur GESEHENEN Achse (Rasterstufen 22,5 Grad):
      22,5: 3   45: 4   67,5: 7   90: 4   112,5: 6   135: 5   157,5: 3   (0 = laengs: nie)

    Lieferung nach Winkel:  30-45  5/6   45-75  15/21   75-90  4/5
    Winkel geliefert Median 65 gegen nicht geliefert 63   (Mann-Whitney p = 0,98)

**Die Abweichung von quer entsteht in der Wahl, nicht in der Wahrnehmung und nicht in der
Ausfuehrung.** Die Achse wird auf 5 Grad genau gesehen, die Klaue faehrt bis auf 0-2 Grad genau
dorthin, wo geplant. Geplant wird aber nur in 4 von 32 Faellen die Rasterstufe "quer" (90 Grad zur
gesehenen Achse), obwohl sie in jeder Episode zur Wahl steht.

**Warum - am Code und an den Zahlen:** Die Klauenstellung ist keine Regel. Das Weltmodell
(`candidates()`/`select_action`) bewertet ein Raster von 8 Winkeln **relativ zur gesehenen Achse**
und nimmt das LCB-Maximum der vorhergesagten Erfolgschance. "Quer" ist nur der Teacher-Wert
(`wrist_tgt = long_axis + pi/2`, pc_act16), und der Teacher ist im Netzbetrieb nicht dabei. Das
Modell hat gelernt, **laengs zu meiden** (0 Grad nie gewaehlt, kein Winkel unter 30), zwischen 30 und
90 Grad aber keinen Unterschied: am Balken liefern alle Baender gleich gut. Was nicht schadet, wird
nicht bestraft - und jede Lieferung bei 67 Grad geht als positives Etikett in Weltmodell und
Selbst-Imitation zurueck (`[Kredit] ... Wrist 28 Grad ... geliefert`). Es gibt also keinen Zug
Richtung 90 Grad. Das ist dieselbe Lage wie in [Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md)
("dem Weltmodell fehlen die Gegenbeispiele") - nur dass es am Balken nach diesen Zahlen auch keine
Gegenbeispiele **gibt**: schraeg greifen kostet hier nichts Messbares (n klein: 6 Zugriffe unter 45
Grad).

Die Beobachtung des Nutzers stimmt also, ist aber kein Fehler der Wahrnehmung: der Agent sieht die
Achse richtig und **entscheidet** sich fuer schraeg, weil es fuer ihn gleich gut ist.

**Fuer die anderen Formen ist der Winkel nur bedingt lesbar.** Bei L, T und X ist die "Laengsachse"
aus `obj_yaw` (Koerperrahmen) nicht die Achse, die die Wahrnehmung per PCA sieht (gemessener
"Fehler" L 73, T 53, X 36 Grad - Rahmenunterschied, kein Sehfehler). Nur U ist vergleichbar
(Fehler 8 Grad): Klaue Median 35 Grad, geliefert 1/6 unter 45 Grad gegen 4/4 darueber (Fisher
p = 0,048, n zu klein, ohne Bonferroni-Bestand).

# Zahlen: Griffversatz beim Zufassen (L/U/T/X, je 15 Episoden)

    Korrelation mit dem Ablage-Versatz (Klauenrahmen), n = Episoden mit beiden Zeilen
                    n  | gesehen -> Ablage  | wahr beim Zufassen -> Ablage | sd gesehen / wahr
    L  entlang      8  |  -0,39  p 0,34     |  +0,72  p 0,044              |  3 /  7 mm
       quer         8  |  +0,35  p 0,40     |  +0,45  p 0,26               |  1 /  7 mm
    U  entlang      8  |  +0,43  p 0,29     |  +0,84  p 0,010              |  4 /  9 mm
       quer         8  |  +0,35  p 0,40     |  +0,98  p < 0,001            |  2 / 14 mm
    T  entlang     11  |  +0,17  p 0,61     |  +0,43  p 0,19               |  2 /  6 mm
       quer        11  |  +0,02  p 0,95     |  +0,53  p 0,10               |  2 /  6 mm
    X  entlang     11  |  +0,20  p 0,55     |  +0,83  p 0,001              |  1 /  5 mm
       quer        11  |  +0,14  p 0,68     |  +0,46  p 0,16               |  1 /  4 mm
    Balken entl.   28  |  +0,25  p 0,21     |  +0,40  p 0,033              |  2 /  3 mm
           quer    28  |  -0,01  p 0,97     |  +0,36  p 0,060              |  1 /  2 mm

    Bonferroni ueber 10 Tests: Schranke 0,005 -> bestehen U quer (wahr) und X entlang (wahr).
    Keine einzige "gesehen"-Zeile kommt in die Naehe.

**Der offene Punkt ist beantwortet, negativ:** Was der Agent beim Zufassen sieht, sagt die Ablage
nicht vorher. Er sieht die Objektmitte fast genau unter seinem Griffpunkt (Streuung 1-4 mm);
tatsaechlich sitzt sie 4-14 mm daneben, und **dieser** wahre Versatz traegt sich bis in die Ablage
durch (U quer r = 0,98). Der seitliche Sitz der L/U-Form entsteht also **zwischen gesehenem Ziel
und tatsaechlichem Reichpunkt** - Lokalisierungsfehler des Schwerpunkts oder Reichfehler des Arms.
Welcher von beiden, trennen die beiden Zeilen nicht (gesehen - wahr = Wahrnehmungsfehler +
Ausfuehrungsfehler); dafuer fehlt die wahre Objektmitte gegen den gesehenen Schwerpunkt als
eigene Zeile.

# Nachtrag: die Versatzkette (Seed 9404, 48 Zugriffe L/U/T/X)

Nutzerauftrag: *"Bau die Logzeile gesehene gegen wahre Objektmitte und starte den Lauf."*
`[Versatzkette]` (dd701c5) zerlegt die Luecke zwischen gesehenem und wahrem Versatz exakt:
**wahr = gesehen - Sehfehler + Objektbewegung - Reichfehler**. Bezug ist die Grundrissmitte
(flaechengewichtete Mitte der Koerper-Geoms), weil der MuJoCo-Ursprung bei L/U/T 2-6 mm daneben
liegt und die Kamera die Flaeche sieht. Rauchtest: die Summe geht bis auf 1 mm Rundung auf.

    Klauenrahmen, mm         |Median| entlang / quer   Mittel entlang / quer   Anteil an Var(wahr) entl / quer
    Sehfehler (Blob-Mitte)        1 / 1                  -0,4 / +1,2                 0,03 / 0,02
    Objekt bewegt bis Zufassen    3 / 3,5                +6,2 / -0,9                 0,48 / 0,57
    Reichfehler (Hand-Griffpkt)   5 / 3                  -1,6 / -3,2                 0,45 / 0,35
    wahr (Grundriss - Hand)      10 / 4                  +8,7 / +1,1

    je Form, Mittel entlang: bewegt  L +0,6  T +5,6  U +17,4  X +5,6
                             Reich   L -4,4  T -4,8  U +13,6  X -4,8
    Vorhersage des Sitzes beim Ablegen ("Objekt-Reichpunkt" in [Ablage]), gepoolt n = 40:
      wahr -> Sitz   entlang r = +0,50 (p = 0,001)   quer r = +0,50 (p = 0,001)
      Sehfehler -> Sitz   r = +0,06 / +0,09 (n.s.)

**Die Wahrnehmung ist es nicht.** Der gesehene Blob liegt im Median 1 mm neben der wahren
Grundrissmitte und erklaert 2-3 % der Streuung. Der Versatz entsteht zu etwa gleichen Teilen aus
zwei Quellen nach dem Sehen:

* **Das Objekt bewegt sich, bevor die Klaue schliesst** - im Mittel 6 mm **in Anfahrtrichtung
  der Klaue** (T und X je +5,6 mm). Die absenkende Klaue schiebt es vor sich her. Beim U kommen
  Ausreisser von 35-49 mm hinzu: das U wurde beim Anfahren weggestossen, die Hand ist ihm zum Teil
  nachgefahren (daher dort auch der grosse Reichfehler mit gleichem Vorzeichen).
* **Die Hand bleibt vor dem Griffpunkt stehen** - bei L/T/X im Mittel 4-5 mm zu kurz entlang.

Beides addiert sich bei T und X zu rund **+11 mm**: das Objekt sitzt systematisch eine Fingerbreite
vor der Klauenmitte, und dieser Sitz traegt sich bis in die Ablage durch (r = 0,50). Der Agent
sieht davon beim Zufassen nichts, weil er sein Ziel vor der Anfahrt festlegt. Der systematische
Teil (Mittel) ist der, den die Policy laut [Verluste nach dem Anheben](/befunde/verluste-nach-dem-anheben.md)
ausgleicht; die Streuung (sd 6-7 mm, beim U 11) gleicht sie nicht aus.

Einschraenkung: ein Seed, U nur 8 Zugriffe (1 geliefert). Die Korrelation wahr -> Ablage aus dem
ersten Lauf (U quer r = 0,98) repliziert gepoolt (r = 0,50), je Form bei n = 6-12 nicht stabil.

# Bewertung

* **Klauenlage:** kein Defekt, sondern eine fehlende Lernspannung. Eine Regel "immer quer" waere
  eine Laufzeitregel und ist ausgeschlossen. Wer Querlage will, braucht eine Welt, in der schraeg
  **schadet** (schmalere Klaue, rutschigere Oberflaeche, laengerer Balken) - dann muesste das
  Weltmodell es aus eigenen Fehlschlaegen lernen. Ob es das kann, belegt der Dosislauf in
  [Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md) (Kreuz-Merkmal, p ~ 0,03).
* **Griffversatz (durch den Nachtrag beantwortet: Schieben und Zu-kurz-Reichen, nicht Sehen):** die naechste Frage ist nicht mehr "sieht die Policy beim Tragen hin", sondern
  "wo entsteht der 4-14-mm-Versatz zwischen Sehen und Zufassen". Eine Zeile mit gesehenem gegen
  wahren Schwerpunkt beim Zufassen wuerde ihn in Wahrnehmung und Reichen zerlegen.
* `evidenz: einzelmessung` - ein Seed je Lauf, kleine n pro Form.

# Verwandt

* [Verluste nach dem Anheben](/befunde/verluste-nach-dem-anheben.md) - Anlass, offener Punkt hier beantwortet
* [Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md) - die Ausrichtung als selbst lernbare Policy
* [Das Wrist-Gitter kostet nichts](/befunde/wrist-gitter-kostet-nichts.md) - das 22,5-Grad-Raster
* [Farbe und Form entkoppelt](/befunde/farb-mischung.md) - die Farbbindung, die beim geparkten Balken leer bleibt
