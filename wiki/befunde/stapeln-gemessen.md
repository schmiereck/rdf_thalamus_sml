---
type: Befund
title: Der Arm stapelt - 45 Stapel in 100 Episoden, und der Engpass war, dass der Agent den Sockel nicht kannte
description: Das korrigierte A/B, beide Arme identisch bis aufs Ziel. Mit der klassenlosen Adresse enden 45 von 100 Episoden in einem Stapel, 83 Prozent der Ablagen mit Sockelziel - gegen 49 Lieferungen im Marker-Arm (p = 0,67), die Aufgabe kostet also nichts Messbares. Der Kontrollarm ist zeichengenau identisch zum ersten A/B. Zwei Befunde darueber hinaus - der Lieferbegriff zaehlt nur 58 Prozent der Stapel, und der Selbstrichter sagt bei Fehlablagen neben dem Sockel ebenso 'geliefert' wie bei Stapeln. Der Weg dorthin enthielt zwei eigene Messfehler und eine selbst gebaute Ursache: der Sockel hatte keine Klasse, weil ich ihm die fremdeste Farbe gegeben hatte.
tags: [act23, stapeln, kommando, selbstlernen, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-19T00:00:00Z }
sources:
  - id: ab
    resource: "Zwei kopflose Laeufe je 100 Episoden, identische Zustandskopien (ad9d768c), Seed 4242, beide mit ACT23_SOCKEL=1 ACT16_GOAL_Z=1 ACT16_ERFOLG_RUHT=1 ACT16_ZIEL_SAEUBERN=0 ACT23_CHOREO=fsm ACT23_SCENE_N=4; Unterschied allein ACT23_ZIEL_ADRESSE=0 gegen =1 + ACT23_ZIEL_RELATION=auf"
    title: Stapeln gegen Marker-Ablage
  - id: diag
    resource: "Zwei Diagnoselaeufe im auf-Arm: 40 Episoden wie oben (neue Grundzeilen [Zielwurf]), dann 20 Episoden zusaetzlich mit ACT23_EIG_DIREKT=1 ACT23_EIG_STETIG=1"
    title: Warum die Adresse scheitert
---

# Das Ergebnis: das korrigierte A/B

Beide Arme identisch bis aufs Ziel, **beide** mit der klassenlosen Adresse (`EIG_DIREKT` +
`EIG_STETIG`), je 100 Episoden, Teacher fahrend:

    Arm   Ep   gegriffen  abgelegt  geliefert  Quote
    ort   100      74        64        49      49,0 %
    auf   100      68        62        44      44,0 %        Fisher p = 0,57

    auf-Arm:   Zielwurf 100 / 100        (erstes A/B: 17 / 100)
               aufgeloest auf den Sockel  86 / 100    (erstes A/B:  9 / 100)
               LIEGT DRAUF                45 von 54 beurteilten Ablagen = 83 %
               Stapel je Episode          45 / 100
               Versatz der Stapel         Median 17 mm, max 55 mm

> **Der Arm stapelt: 45 von 100 Episoden enden in einem Stapel.** Gegen 49 Lieferungen im
> Marker-Arm (p = 0,67) - die neue Aufgabe kostet auf Teacher-Niveau nichts Messbares.

**Der Kontrollarm ist zeichengenau identisch zum ersten A/B** - alle 100 Episodenausgaenge. Die
neuen Schalter beruehren den Marker-Arm also gar nicht; der einzige wirksame Unterschied ist das
Ziel.

## Der Lieferbegriff zaehlt Stapel nicht

Die Welt zaehlt nur **26 der 45 Stapel** als geliefert (58 %). Das Kriterium misst 25 mm zum
ZIELPUNKT, und der ist die wahrgenommene Sockelmitte; ein Objekt, das stabil auf der Platte liegt,
aber 30 mm von deren Mitte, gilt als nicht geliefert. **Die Quote 44 % unterschaetzt die Aufgabe
deshalb um fast die Haelfte.** Fuer "auf" waere der ehrliche Begriff "liegt auf der Auflage" - er
ist bewusst NICHT still umgestellt, weil das den Erfolgsbegriff dieser Aufgabe aendert. Das ist eine
Entscheidung, keine Korrektur.

## Der Selbstrichter unterscheidet nicht -- ENTWERTET

> **NACHTRAG 2026-09-20: diese Messung ist ungueltig.** Die Aufraeumschleife setzt das kommandierte
> Objekt nach der Episode auf seine Ruhehoehe vom Anfang zurueck (um gekippte L/U aufzustellen) --
> und baut damit den Stapel ab, BEVOR irgendein Selbsturteil die Szene sieht. Die Zahlen unten haben
> nicht gemessen, wie gut der Richter Stapel erkennt, sondern wie er auf eine Szene reagiert, in der
> kein Stapel mehr stand. Behoben und neu gemessen in
> [Der Stapel-Selbstrichter](/befunde/selbstrichter-stapel.md).
> **Die Stapelraten dieser Seite sind NICHT betroffen** - sie werden vor dem Aufraeumen gefaellt.

    Selbstrichter sagt "geliefert"   bei Stapeln                 40 von 45  (89 %)
                                     bei Ablagen NEBEN dem Sockel  6 von  9  (67 %)   p = 0,12

Er stimmt bei Stapeln fast immer zu - **und bei Fehlablagen neben dem Sockel zu zwei Dritteln
ebenso.** Die naheliegende Erklaerung: er findet am Zielort den Sockel-Blob, der ohnehin dort liegt,
statt das abgelegte Objekt. Der Unterschied ist bei n = 9 nicht signifikant, die Richtung aber
unangenehm: **ueber die Selbst-Imitation wuerde der Agent misslungene Stapel als gelungen lernen.**
Das ist die erste Zahl zu Frage 3.

# Der Weg dorthin

## Das erste A/B, wie es zuerst aussah

    Arm   Ep   gegriffen  abgelegt  geliefert  Quote
    ort   100      74        64        49      49,0 %
    auf   100      77        65        47      47,0 %        Fisher p = 0,89

    Stapelurteil im auf-Arm:  "LIEGT DRAUF" 3 von 12 beurteilten Ablagen = 25 %

**Beide Zahlen sagen nichts, und die zweite ist falsch.**

## Warum: nur 9 von 100 Episoden zielten auf den Sockel

    Episoden im auf-Arm              100
      Adresse gewuerfelt              17   = 17 %
      davon auf den Sockel aufgeloest  9   = 53 % der Wuerfe
      davon abgelegt                   6

Der Quotenvergleich vergleicht also in 91 von 100 Episoden **Marker gegen Marker**. Dass die Quoten
gleich sind, ist kein Befund ueber das Stapeln.

**Und das Stapelurteil war mein Messfehler, zweifach:**

1. Es wurde gefaellt, sobald der WURF gelang - auch wenn der AUFLOESER danach auf den Marker
   zurueckgefallen war. 6 der 12 "Stapelversuche" hatten gar nicht auf den Sockel gezielt. Die
   Signatur war deutlich: losgelassen **6 mm** vom Ziel, 7 mm Drift - und **116 mm** vom Sockel, auf
   Tischhoehe. Das Ziel war der Marker.
2. Es verlangte Versatz < 23 mm ("vollstaendig auf der Platte") und verwarf damit Stapel, die bei
   27 und 35 mm Versatz **stabil oben lagen** - die Platte ist 35 mm halbbreit.

Richtig gezaehlt, nur die 6 Episoden, die wirklich auf den Sockel zielten:

    Ep   seitl. vom Ziel  Objektmitte  Versatz
    37         9 mm          19 mm      22 mm   LIEGT AUF DEM SOCKEL
    38        24 mm          19 mm      27 mm   LIEGT AUF DEM SOCKEL
    62         7 mm          19 mm      35 mm   LIEGT AUF DEM SOCKEL
    63        13 mm          21 mm      23 mm   LIEGT AUF DEM SOCKEL
    72        34 mm          19 mm      17 mm   LIEGT AUF DEM SOCKEL
    97        30 mm          12 mm      56 mm   auf dem Tisch

**5 von 6.** Beides ist im Code korrigiert: das Urteil faellt nur noch, wenn der Aufloeser den Sockel
tatsaechlich geliefert hat, und es geht nach der Hoehe (Objektmitte ueber Auflage + 8 mm, die Mitte
zwischen Tisch 12 mm und Auflage 20 mm). Der Versatz bleibt als Messwert stehen.

## Warum die Adresse scheiterte

Der Wurf lieferte bei jedem Scheitern bisher still `None`. Jetzt sagt eine Zeile `[Zielwurf]`,
warum. Diagnoselauf, 40 Episoden:

    37 x  sockel: keine verfolgbare Achse (Farbe None, Form None, Groesse dick)

**Ein einziger Grund.** Der Sockel hat weder eine Farbklasse noch eine Formklasse, und eine reine
Groessenangabe ist nach der Nutzervorgabe keine Adresse ("der blaue Wuerfel", nie "das groesste
Objekt").

> **Der Agent kannte den Sockel nicht.** Und die Ursache habe ich selbst gebaut: fuer den Sockel
> habe ich die Farbe mit dem **groessten** Abstand zu allen bekannten gewaehlt, damit er sich von
> ihnen abhebt - und genau deshalb gehoert er zu keiner Farbklasse. Eine 70-mm-Platte ist zudem
> eine neuartige Form. Die Bloecke, in denen das A/B doch Adressen hatte (Ep 37-39, 61-63,
> 72-79, 97-99), waren die Zeiten, in denen zufaellig eine Farbklasse in seiner Naehe existierte.

## Die Loesung war schon gebaut

`ACT23_EIG_DIREKT` + `ACT23_EIG_STETIG` - die [Adresse ohne Klasse](/mechanismen/adresse-ohne-klasse.md),
aus einer einzigen Sichtung, ueber den gemessenen Formvektor statt ueber einen Klassennamen. Sie
wurde diese Woche fuer genau diesen Fall gebaut: einen Koerper, den der Agent nicht benennen kann.

Diagnoselauf, 20 Episoden, mit beiden Schaltern:

    Wurf gescheitert                  0 von 20      (vorher 37 von 40)
    auf den Sockel aufgeloest        19 von 20      (1 mehrdeutig)
    Stapel gelungen ("LIEGT DRAUF")  12 von 12 Ablagen
    Sockel als Objekt registriert     0

**10 der 20 Adressen lauten nur `auf ~gesehen` oder `auf ~gesehen + dick`** - der Sockel wird ohne
jede Klasse adressiert, allein ueber seinen gemessenen Formvektor.

> **Zusammen: wo der Sockel das aufgeloeste Ziel war, stapelte der Teacher in 19 von 20 Faellen**
> (A/B 5/6, erster Diagnoselauf 2/2, zweiter 12/12).

Eine Stelle musste dafuer vorher dicht werden: `_direkt_adressieren` haette den Sockel als
unentdeckten Koerper gesehen und als **kommandierbares Objekt** registriert - er steht in `scene`,
aber nicht in `state.OBJECTS`. Dann haette die Neugier ihn zum Greifen auswaehlen koennen. Stuetzen
sind dort jetzt ausgenommen.

# Zwei Beobachtungen, die offen bleiben

**Die Welt zaehlt nur 7 der 12 Stapel als geliefert.** Das Lieferkriterium misst 25 mm zum
ZIELPUNKT, und der ist die wahrgenommene Sockelmitte. Ein Objekt, das stabil auf der Platte liegt,
aber 30 mm von deren Mitte, gilt als nicht geliefert. **Fuer das Stapeln ist das der falsche
Begriff** - richtig waere "liegt auf der Auflage". Er ist bewusst NICHT still umgestellt: das waere
eine Aenderung am Erfolgsbegriff, die alle Quoten dieser Aufgabe verschiebt.

**Der Selbstrichter sagte bei allen 12 Stapeln "geliefert".** Vorhergesagt hatte ich das Gegenteil:
ein Stapel ist fuer die Kamera [verschluckt](/befunde/sockel-verschluckt-den-stapel.md), der
Selbstrichter sucht aber eine Detektion in der Farbe des Objekts. Ob er aus dem richtigen Grund
zustimmt oder nur den Sockel-Blob am Zielort findet, ist **nicht geklaert** - dafuer braucht es die
Gegenprobe, in der der Sockel am Ziel steht, das Objekt aber NICHT darauf liegt. Das ist Frage 3.

# Was das fuer das Ziel des Projekts heisst

Nach [Projektziel](/ziel.md) zaehlt Selbstaneignung, nicht Quote. Genau daran lag es hier: **der Arm
konnte stapeln, der Agent konnte den Sockel nicht nennen.** Und geloest wurde es nicht durch eine
neue Regel, sondern durch die Adresse aus einer einzigen Sichtung - also dadurch, dass der Agent
einen unbekannten Koerper ohne vorherige Klassengeburt ansprechen kann.

**Was das NICHT ist:** ein Nachweis, dass der Agent stapeln GELERNT hat. Gefahren hat der Teacher,
und die Ablagehoehe kommt als Teacher-Geruest aus dem Simulator. Das ist Frage 2 und die naechste
Messung dieser Linie.

# Fallen

* **Ein Seed.** Die Stapelrate 19 von 20 ist eine Abzaehlung ueber drei Laeufe, keine Quote mit
  Konfidenzintervall.
* **Teacher fahrend.** Machbarkeit auf Teacher-Niveau, nicht Lernerfolg.
* **Die Quote des A/B ist wertlos** und steht nur hier, damit niemand sie woanders zitiert.
* **`EIG_DIREKT` adressiert auch neue OBJEKTE direkt**, nicht nur den Sockel. In einem A/B muss es
  deshalb in beiden Armen gleich stehen.

# Verwandt

* [Die Relation "auf", gebaut](/mechanismen/relation-auf-gebaut.md) - der Bau, der hier gemessen wird
* [Die Adresse ohne Klasse](/mechanismen/adresse-ohne-klasse.md) - die Loesung, eine Woche frueher gebaut
* [Der Sockel verschluckt den Stapel](/befunde/sockel-verschluckt-den-stapel.md) - warum der Selbstrichter eigentlich scheitern muesste
* [Der Sockel braucht 80 mm Freiraum](/befunde/sockel-braucht-80mm-freiraum.md) - die Szene, in der gemessen wurde
* [Stapeln als neue Aufgabe](/fragen/stapeln-als-aufgabe.md) - der Entwurf
