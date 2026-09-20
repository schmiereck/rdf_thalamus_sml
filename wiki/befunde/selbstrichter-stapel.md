---
type: Befund
title: Der Stapel-Selbstrichter - mit der eigenen leeren Auflage als Bezug erkennt er 68 statt 28 Prozent
description: Der Agent beurteilt seinen eigenen Stapel ueber die Farbstreuung des Auflagen-Blobs, ohne von mir gesetzte Schwelle. Gegen einen globalen Massstab erkennt er nur 7 von 25 Stapeln; gegen die EIGENE leere Auflage derselben Episode, mit der gemessenen ueblichen Schwankung eines Einzelflecks als Mass, sind es 17 von 25 - bei null Fehlalarmen in beiden Faellen. Die verbleibenden Fehlanzeigen sind kein Schwellenproblem mehr: dort steigt die Farbstreuung gar nicht, weil das Objekt ueber den Rand haengt. Davor stand ein Messfehler, der alle frueheren Selbsturteile zum Stapeln entwertet - die Aufraeumschleife setzte das Objekt auf seine Ruhehoehe zurueck, bevor der Richter die Szene sah.
tags: [act23, stapeln, selbsturteil, wahrnehmung]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-20T00:00:00Z }
sources:
  - id: lauf
    resource: "Ein kopfloser Lauf, 40 Episoden auf einer Kopie von act23_state.pkl (ad9d768c), Seed 7001, ACT23_SELBST_STAPEL=1 ACT23_ZIEL_MISCH=0.8 ACT23_SOCKEL_WANDERT=1 ACT23_SOCKEL_HOEHEN=6,10,14 ACT23_SCENE_N=3 ACT23_SCENE_EVERY=2, Teacher fahrend"
    title: Stapel-Selbsturteil gegen das privilegierte Urteil
  - id: sonde
    resource: /befunde/sockel-verschluckt-den-stapel.md
    title: Die Offline-Sonde, deren saubere Trennung hier NICHT wiederkommt
---

# Warum es diesen Richter braucht

Ein gestapelter Koerper ist fuer diese Kamera **unsichtbar**: er liegt vollstaendig innerhalb der
Silhouette der Auflage, die Flaeche aendert sich um kein Pixel
([0 von 25 Stellen](/befunde/sockel-verschluckt-den-stapel.md)). Der gewoehnliche Selbstrichter
sucht den Blob am Ablagepunkt und findet dort die Auflage - er kann "liegt drauf" gar nicht von
"liegt daneben" unterscheiden.

# Erst ein Messfehler, der alle frueheren Selbsturteile zum Stapeln entwertet

Nach jeder Episode setzt die Aufraeumschleife jeden NICHT kommandierten Koerper auf seine Pose vom
Episodenanfang zurueck; das kommandierte Objekt behaelt seine Stelle, bekommt aber seine
**Ruhehoehe vom Anfang** - gedacht, um gekippte L/U-Formen wieder aufzustellen.

**Beim Stapeln baut das den Stapel ab, bevor irgendein Selbsturteil die Szene sieht.** Das Urteil
in der Ablage-Zeile faellt davor und ist unberuehrt; alles, was danach kommt, sah eine aufgeraeumte
Welt. In der ersten Messung meldete die Welt folgerichtig in **allen 15** Urteilszeilen "nicht
drauf", obwohl im selben Lauf 10 Stapel gelangen.

Korrektur, eine Zeile mit physikalischer Begruendung: liegt das Objekt **hoeher** als seine eigene
Ruhehoehe, steht es auf etwas - dann bleibt die Hoehe. Ein gekipptes Objekt liegt tiefer, nicht
hoeher; der Aufstell-Fall bleibt also unberuehrt, und ohne Auflage in der Szene gibt es nichts,
worauf ein Koerper ruhen koennte.

> **Betroffen ist auch der gewoehnliche Selbstrichter.** Die Beobachtung aus
> [Der Arm stapelt](/befunde/stapeln-gemessen.md) - "sagt bei 40 von 45 Stapeln geliefert, aber auch
> bei 6 von 9 Fehlablagen" - hat nicht gemessen, wie gut er Stapel erkennt, sondern wie er auf eine
> Szene reagiert, in der kein Stapel mehr stand. Sie ist dort als entwertet vermerkt.
>
> **Nicht betroffen** sind alle Stapelraten (45 von 100, 16 von 19 im Netz-Lauf) und die
> Hoehenmessungen: die faellt die Ablage-Zeile vor dem Aufraeumen.

# Wie der Richter gebaut ist

Zwei Groessen, beide aus der Wahrnehmung des Agenten, **keine von mir gesetzte Schwelle**:

* **Traegt die Auflage etwas?** Die Farbstreuung `cspread` des Blobs am Ziel gegen `_merge_th()` -
  das 0,995-Quantil der Farbstreuung, die der Agent an seinen EIGENEN Einzelobjekt-Sichtungen
  gemessen hat. Darueber heisst: mehr als ein Ding im Blob.
* **Drauf oder daneben?** Zwei nebeneinander verschmolzene Koerper haben die SUMME der Flaechen, ein
  Stapel die der Auflage allein. Beide Bezugswerte kennt der Agent - die leere Auflage aus der
  Adressaufloesung, die eigene Objektflaeche aus der Startdetektion. Es gewinnt der naehere.

Enthalten darf er sich: ohne eigenen Massstab, ohne vermessene Auflage, ohne die Auflage
wiederzufinden.

# Zahlen

    Selbsturteil \ Welt    liegt drauf   nicht drauf
    liegt drauf                  7             0
    nicht drauf                 18             6
    enthalten                    0             0

    Uebereinstimmung 13 von 31 = 42 %
    Treffsicherheit  7 von 7  = 100 %
    Empfindlichkeit  7 von 25 =  28 %

**Kein einziger Fehlalarm.** Sagt er "liegt drauf", liegt es drauf. Aber er uebersieht mehr als zwei
Drittel der Stapel.

# Woran es liegt: eine einzige Stelle

    alle 14 Fehlanzeigen: Farbstreuung unter dem Massstab
    davon durch den Flaechentest verworfen: 0

    Farbstreuung   leerer Sockel   0,07
                   Stapel uebersehen 0,20      <- Massstab 0,339
                   Stapel erkannt    0,41

    nach Auflagenhoehe:   6 mm: 0 von 6 erkannt | 10 mm: 2 von 3 | 14 mm: 3 von 10

**Der Flaechentest ist unschuldig** - er hat keinen einzigen echten Stapel verworfen. Es haengt
allein am Massstab: ein Sockel mit Wuerfel liest im Median 0,20, und der eigene Massstab des Agenten
liegt bei 0,34.

Und das ist kein Zufall, sondern seine Bedeutung: `_merge_th()` beantwortet die Frage *"was
ueberschreitet ein EINZELNES Objekt praktisch nie?"*. Ein Blob, der zu 19 % aus einer zweiten Farbe
besteht, ueberschreitet das nicht - er sieht aus wie ein buntes Einzelobjekt. Der Massstab ist
richtig geeicht, aber fuer eine andere Frage.

**Die saubere Trennung der Offline-Sonde kommt nicht wieder.** Dort las leer 0,069 und belegt 0,149
bis 0,397, ohne einen Ueberlapp - aber in einer aufgeraeumten Szene mit einem einzigen Koerper. Im
Lauf ueberlappen die Verteilungen deutlich (belegt 0,071-0,460, leer 0,063-0,282). Nachbarn, Arm und
Schatten tragen mit; ein Wuerfel, dessen Farbe der Platte naeher liegt, hebt die Streuung kaum.

# Der zweite Anlauf: die eigene leere Auflage als Bezug

Der Richter verglich gegen einen **globalen** Massstab. Er hat aber einen **eigenen** zur Hand:
`cspread0`, die Farbstreuung DERSELBEN Auflage, gemessen beim Adressieren DERSELBEN Episode.

Und der Massstab fuer "deutlich veraendert" steckt in denselben Bezugswerten, aus denen
`_merge_th()` sein Quantil zieht (`shape_clf._cs_ref`, 400 Werte im gelernten Zustand):

    Median 0,085    95er-Quantil 0,120    0,995er-Quantil 0,339  (= der alte Massstab)
    uebliche Schwankung eines Einzelflecks := 95er - Median = 0,035

**Damit ist auch erklaert, warum der alte Massstab so grob war:** sein Quantil sitzt in einem
langen Auslaeufer, waehrend das Gros der Einzelsichtungen bei 0,085 liegt. Fuer seine
urspruengliche Aufgabe - Verschmelzungen sperren, lieber zu selten - ist er richtig geeicht; fuer
"liegt etwas drauf" ist er viermal zu hoch.

Das neue Kriterium, weiterhin ohne eine von mir gesetzte Zahl:

    traegt etwas  :=  Farbstreuung jetzt  >  Farbstreuung der leeren Auflage + uebliche Schwankung

## Beide Massstaebe an denselben Episoden

Beide laufen in derselben Episode mit; das alte Kriterium steht als `global waere: ja/nein`
daneben. So vergleicht EIN Lauf beide, statt zwei Laeufe gegeneinander zu stellen, die nach der
ersten abweichenden Entscheidung ohnehin auseinanderlaufen.

    Bezug                          erkannt             Fehlalarm    Uebereinstimmung
    eigene leere Auflage      17 von 25 = 68 %        0 von 6            74 %
    globaler Massstab          7 von 25 = 28 %        0 von 6            42 %

**Zweieinhalbmal so empfindlich, und kein Fehlalarm mehr als zuvor.**

## Die verbleibenden Fehlanzeigen sind kein Schwellenproblem

Je Episode gepaart (19 Episoden mit Ablage- und Urteilszeile: 16 erkannt, 3 uebersehen):

    Anstieg der Farbstreuung gegenueber der eigenen leeren Auflage
      erkannt      Median +0,134
      uebersehen   Median +0,003        (noetig waeren 0,037)
    Versatz   uebersehen 23 mm  |  erkannt 10 mm
    Fehlanzeige wegen Flaechentest: 0 - er verwirft weiterhin keinen einzigen echten Stapel

Bei den uebersehenen Faellen steigt die Farbstreuung **gar nicht**. Das Objekt ist dann nicht im
Blob der Auflage - es haengt ueber den Rand und bildet einen eigenen Fleck. Eine niedrigere
Schwelle wuerde daran nichts aendern; das ist eine andere Frage (wo endet die Auflage) und
braucht eine andere Messgroesse.

Die Abhaengigkeit von der Auflagenhoehe hat sich dabei **umgekehrt**: 14 mm jetzt 10 von 10,
10 mm 2 von 3, 6 mm 4 von 6. Der flache Sockel ist nicht mehr der blinde Fleck - die frueheren
0 von 6 lagen am globalen Massstab, nicht an der Geometrie.

# Der erste Anlauf, und warum er zu grob war

Leer 0,07 gegen belegt 0,20 ist ein Faktor von fast drei an demselben Blob, waehrend der globale
Massstab beide unterschreitet. Genau das ist im Abschnitt darueber umgesetzt und gemessen.

# Fallen

* ~~**Die Empfindlichkeit haengt an der Auflagenhoehe**~~ - mit dem eigenen Bezug kehrt sich das
  um (14 mm 10 von 10, 6 mm 4 von 6). Die Hoehe war nicht die Ursache, der Massstab war es.
* **Ein Lauf, 31 Urteile.** Die Treffsicherheit von 7 aus 7 ist bei n = 7 kein Beweis fuer null
  Fehlalarme.
* **Die Objektfarbe wechselt je Episode** (`FARB_MISCHUNG`). Ein Wuerfel in Sockelnaehe der Farbe
  hebt die Streuung kaum - der Anteil solcher Faelle ist nicht ausgezaehlt.
* **Vorgabe bleibt 0.** Auch mit 68 % Empfindlichkeit ist es ein Tor fuer die Selbst-Imitation
  (es laesst nur Sicheres durch), kein Erfolgsmass - ein Drittel der Stapel bliebe ungezaehlt.
* **Zwei Auszaehlungen, zwei Nenner.** Die Quoten oben zaehlen alle 31 Urteilszeilen (25 davon mit
  Welt-Urteil "liegt drauf"); die Ursachenanalyse nur die 19 Episoden, in denen AUCH die
  Ablage-Zeile mit Versatz und Auflagenhoehe steht. Nicht jede beurteilte Episode hat eine
  Ablage-Zeile. Die Ursachen sind also an einer Teilmenge ausgezaehlt.

# Verwandt

* [Der Sockel verschluckt den Stapel](/befunde/sockel-verschluckt-den-stapel.md) - die Offline-Sonde und ihre sauberere Welt
* [Der Arm stapelt](/befunde/stapeln-gemessen.md) - dort ist die entwertete Beobachtung vermerkt
* [Die Policy stapelt selbst](/befunde/netz-stapelt-selbst.md) - warum das privilegierte Urteil bisher tragen musste
* [Kredit und Selbst-Urteil](/mechanismen/kredit-und-selbsturteil.md) - der gewoehnliche Selbstrichter
