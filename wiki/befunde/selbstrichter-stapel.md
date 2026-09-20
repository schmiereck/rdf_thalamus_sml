---
type: Befund
title: Der Stapel-Selbstrichter ist treffsicher, aber fast blind - und die Aufraeumschleife baute den Stapel ab, bevor er ihn sah
description: Der Agent beurteilt seinen eigenen Stapel ueber die Farbstreuung des Auflagen-Blobs, mit seinem eigenen Verschmelzungs-Massstab und ohne erfundene Schwelle. Ergebnis aus 40 Episoden - kein einziger Fehlalarm (7 von 7 richtig), aber nur 7 von 25 Stapeln erkannt. Alle 14 Fehlanzeigen scheitern an derselben Stelle: ein Sockel mit Wuerfel liest 0,20, der selbst gemessene Massstab liegt bei 0,34. Auf der 6-mm-Auflage wird kein einziger Stapel erkannt. Davor stand ein Messfehler, der alle frueheren Selbsturteile zum Stapeln entwertet - die Aufraeumschleife setzte das Objekt auf seine Ruhehoehe zurueck, bevor der Richter die Szene sah.
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

# Der naechste Schritt, und er braucht keine neue Schwelle

Der Richter vergleicht heute gegen einen **globalen** Massstab. Er hat aber einen **eigenen** zur
Hand: `cspread0`, die Farbstreuung DERSELBEN Auflage beim Adressieren derselben Episode. Leer 0,07
gegen belegt 0,20 ist ein Faktor von fast drei an demselben Blob, waehrend der globale Massstab
beide unterschreitet.

Was dafuer fehlt, ist der Massstab fuer "deutlich veraendert" - und den koennte der Agent messen,
statt ihn gesetzt zu bekommen: die Streuung wiederholter Messungen desselben Blobs ueber Frames. Das
ist die naechste Messung dieser Linie.

# Fallen

* **Die Empfindlichkeit haengt an der Auflagenhoehe** (0 von 6 bei 6 mm). Warum, ist nicht geklaert;
  naheliegend ist, dass ein flacher Sockel den Wuerfel weniger aus seiner Silhouette heraustreten
  laesst.
* **Ein Lauf, 31 Urteile.** Die Treffsicherheit von 7 aus 7 ist bei n = 7 kein Beweis fuer null
  Fehlalarme.
* **Die Objektfarbe wechselt je Episode** (`FARB_MISCHUNG`). Ein Wuerfel in Sockelnaehe der Farbe
  hebt die Streuung kaum - der Anteil solcher Faelle ist nicht ausgezaehlt.
* **Vorgabe bleibt 0.** Ein Urteil mit 28 % Empfindlichkeit taugt als Tor fuer die
  Selbst-Imitation (es laesst nur Sicheres durch), aber nicht als Erfolgsmass.

# Verwandt

* [Der Sockel verschluckt den Stapel](/befunde/sockel-verschluckt-den-stapel.md) - die Offline-Sonde und ihre sauberere Welt
* [Der Arm stapelt](/befunde/stapeln-gemessen.md) - dort ist die entwertete Beobachtung vermerkt
* [Die Policy stapelt selbst](/befunde/netz-stapelt-selbst.md) - warum das privilegierte Urteil bisher tragen musste
* [Kredit und Selbst-Urteil](/mechanismen/kredit-und-selbsturteil.md) - der gewoehnliche Selbstrichter
