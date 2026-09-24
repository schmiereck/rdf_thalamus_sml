---
type: Mechanismus
title: Die Auflagenhoehe ertasten - das Etikett aus dem eigenen Koerper statt aus geom_size
description: Nutzerprinzip "weniger Teacher ist immer besser", umgesetzt fuer die letzte privilegiert gelabelte Groesse. Der Ausgang "Stapel haelt oder nicht" taugt dafuer nachweislich NICHT - er traegt keine Hoheninformation. Was traegt, ist die Beruehrung - die Hand senkt das getragene Objekt unter die Schaetzung und haelt an, sobald sie fuehlt, dass es nicht mehr sinkt. Die Aufsetzhoehe ist die gesuchte Groesse, gemessen aus site_xpos, also aus der Vorwaertskinematik. Gegen die Wahrheit, die nirgends eingeht - 7 Tastwerte, Median -0,50 mm, Betrag 1,10 mm, also so genau wie der Schaetzer, den es trainieren soll. Enthaelt zwei Konstruktionsfehler und ihre Behebung.
tags: [act23, stapeln, hoehe, privileg, tastsinn, propriozeption]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-21T00:00:00Z }
sources:
  - id: bau
    resource: "src/pc_cvnn/pc_act16.py (ACT16_TASTEN, TAST_TIEF, TAST_STILL, TAST_N, TAST_RAND) und src/pc_cvnn/pc_act23.py (ACT23_HOEHE_TASTEN), Stand bfab66f"
    title: Der Bau
  - id: mess
    resource: "Ein kopfloser Lauf, 16 Episoden auf einer Kopie von act23_state.pkl (ad9d768c), Seed 7001, ACT23_CHOREO=fsm ACT23_SOCKEL_N=3 ACT16_TASTEN=1 ACT23_HOEHE_TASTEN=1 ACT23_ZIEL_MISCH=1.0 ACT23_SOCKEL_HOEHEN=6,10,14; 17 Zieladressen -> 7 Tastwerte"
    title: Der Rauchtest gegen die Wahrheit
  - id: wunsch
    resource: "Nutzer, 2026-09-21: 'Ich faende Hoehe aus dem Ausgang statt vom Teacher lernen gut. Generell finde ich weniger teacher ist immer besser.'"
    title: Der Anlass
---

> **NUTZERVORGABE 2026-09-24: KAMERA STATT TASTEN.** Der Nutzer haelt die Beruehrung fuer keinen
> guten Eingang, weil offen ist, ob und wie sie am physischen Roboter traegt. Die Tast-Schalter
> bleiben im Code und diese Messung gilt weiter, aber **das Tasten wird nicht weiter ausgebaut**.
> Neue Etiketten sollen aus dem Kamerabild kommen (ggf. aus der Eigenpropriozeption des Arms).
> Ein Kandidat fuer die Hoehe ist gemessen vorhanden: ein erhoehter Koerper erscheint radial von der
> Kamera weg verschoben, mit r = 1,00 zur Hoehe ([Parallaxe](/befunde/stapeln-bricht-die-tischebene.md)).

# Warum

Der [HoehenSchaetzer](/befunde/oberkante-ohne-privileg.md) nahm der Laufzeit ihr letztes Privileg -
aber gelabelt wurde er weiter mit `sim.m.geom_size`. Nach
[Laufzeitregeln](/mechanismen/laufzeit-regeln.md) ist das zulaessig; nach dem Nutzerprinzip
**"weniger Teacher ist immer besser"** ist es Schuld, die man abtraegt.

# Der Ausgang "geliefert oder nicht" taugt NICHT - gemessen

Der naheliegende Weg waere, aus Erfolg und Misserfolg zu lernen. Er ist versperrt, und das steht
schon in den Zahlen des [Drei-Auflagen-Laufs](/befunde/drei-auflagen-im-lauf.md):

    gelungene Stapel     |Hoehenfehler| 2,20 mm    Versatz 15 mm
    misslungene Stapel   |Hoehenfehler| 2,30 mm    Versatz 65 mm

**Der Hoehenfehler ist in beiden Gruppen gleich gross.** Was einen Stapel kippt, ist der seitliche
Versatz. Auf Erfolg/Misserfolg zu lernen hiesse, auf Rauschen zu lernen.

> **Das Ausgangssignal muss koerperlich und ABGESTUFT sein**, kein binaeres Urteil. Das ist die
> uebertragbare Form dieses Befundes.

# Was traegt: die Beruehrung

Die Hand senkt das getragene Objekt und haelt an, sobald sie fuehlt, dass es nicht mehr sinkt.
**Die Aufsetzhoehe IST die gesuchte Groesse** - genau bei ihr ruht das Objekt auf der Auflage.

Gemessen wird sie an `sim.grasp_pos()`, also `site_xpos`: die **tatsaechliche** Handstelle aus der
Vorwaertskinematik. Das hat ein echter Roboter aus seinen Gelenkgebern, und dieses Projekt lernt
die Kinematik sogar selbst ([BodyModel](/mechanismen/act23-modullandschaft.md)). Kein
Simulatorwissen, kein Objektmass, keine Geometrie.

Erkannt wird der Widerstand rein propriozeptiv: die gefuehlte Handhoehe wird mit **sich selbst**
verglichen (sinkt sie noch?), nicht mit dem Befehl.

    ACT16_TASTEN=1        schaltet das Tasten in der Ablagephase ein     (Vorgabe 0)
    ACT16_TAST_TIEF       wie weit unter die Schaetzung gezielt wird     (8 mm)
    ACT16_TAST_STILL      was "sinkt nicht mehr" heisst                  (0,4 mm/Schritt)
    ACT16_TAST_N          so viele Schritte in Folge                     (6)
    ACT16_TAST_RAND       trennt Widerstand von blosser Ankunft          (2 mm)
    ACT23_HOEHE_TASTEN=1  labelt den Schaetzer damit statt mit geom_size (Vorgabe 0)

# Zwei Konstruktionsfehler, beide gemessen und behoben

## 1. Ohne Uebertasten waere das Signal EINSEITIG

Zielte die Hand nur auf die Schaetzung, entstuende eine Beruehrung **nur dann, wenn die Schaetzung
zu tief lag**. Zu hohe Schaetzungen blieben unbemerkt, der Lerner saehe nur Beispiele einer
Richtung und driftete. Deshalb zielt die Phase `TAST_TIEF` unter die Schaetzung und haelt auf
Widerstand hin an.

Das ist ein **Reflex, kein Plan**: gestoppt wird auf ein Sinnessignal hin. Er ist an einen
Schalter gebunden und darf zur Testzeit abgeschaltet werden - dann steht die gelernte Schaetzung
allein.

## 2. Die Aufsetzhoehe ist die beim BEGINN des Stillstands

Die erste Fassung nahm die Handhoehe am **Ende** des Bestaetigungsfensters. Waehrend dieser
`TAST_N` Schritte kriecht die Hand aber weiter (je Schritt unter der Schwelle, in Summe nicht):

    Aufsetzhoehe am Ende des Fensters    Median -2,65 mm   Spanne -4,30..-0,20
    Aufsetzhoehe am BEGINN               Median -0,50 mm   Spanne -3,40..+1,10

**Der Beginn ist der Augenblick der Beruehrung, das Ende nur der Augenblick, in dem ich ihr
glaube.** Der systematische Unterschlag verschwindet damit.

# Wie genau es ist

    7 Tastwerte gegen die Wahrheit (die nirgends eingeht)
      Median      -0,50 mm
      |Median|     1,10 mm
      Spanne      -3,40 .. +1,10 mm

    nach Auflagenhoehe:  wahr  5,6 -> ertastet  5,1
                         wahr  9,6 -> ertastet  8,6
                         wahr 13,6 -> ertastet 12,2

Zum Vergleich: der Schaetzer, den diese Etiketten trainieren sollen, liegt im Lauf bei 0,7 bis
2,2 mm. **Das Etikett aus dem eigenen Koerper ist also so genau wie das, was daraus gelernt
werden soll** - und braucht kein Privileg.

# Fallen

* **Es braucht die FSM-Choreographie.** Das Tasten sitzt im Ablage-Zweig der gescripteten
  Choreographie, und `ACT23_CHOREO` steht per Vorgabe auf `netz` - dann wird der Zweig nie
  betreten und es faellt **kein einziges** Lernbeispiel. Genau daran ist der erste Versuch
  gescheitert, s. [Invarianten](/mechanismen/invarianten.md). Fuer einen Lernlauf ist das kein
  Hindernis (die DAgger-Daten entstehen ohnehin unter dem FSM), fuer einen Testlauf schon.
* **Die Ausbeute ist knapp die Haelfte.** 17 Zieladressen ergaben 7 Tastwerte: 3-mal wurde kein
  Aufsetzen gefuehlt, 1-mal sah die Auflage belegt aus, der Rest erreichte das Loslassen nicht.
  Der privilegierte Weg labelte rund 70 % der Adressen. **Weniger Teacher kostet hier Datenmenge.**
* **Leichter Unterschlag, der mit der Hoehe waechst** (-0,5 / -1,0 / -1,4 mm bei 5,6 / 9,6 /
  13,6 mm). Ursache ungeklaert; naheliegend ist, dass ein laengerer Absenkweg mehr Schwung
  mitbringt, bevor der Stillstand anspricht. Bei n = 1, 4 und 2 ist das eine Beobachtung, keine
  Messung.
* **Das Uebertasten ist eine Verhaltensaenderung.** Die Hand faehrt bis zu 8 mm unter die
  Schaetzung. In dieser Welt ist das folgenlos (die Platte ist schwer, der Arm stallt), aber es
  ist nicht nichts - und es ist der Grund, warum der Schalter auf 0 steht.
* **Der eigentliche Vergleich fehlt noch.** Ob ein Schaetzer, der aus Tastwerten gelernt hat, im
  act23-Lauf so gut abschneidet wie einer, der aus dem Privileg gelernt hat, ist **nicht
  gemessen**. Dieser Befund zeigt nur, dass das Etikett stimmt - nicht, dass der Lerner damit
  ankommt. Das ist der naechste Lauf.
* **n = 7.** Alles hier steht auf sieben Beruehrungen aus einem Lauf.

# Verwandt

* [Die Oberkante ohne Privileg](/befunde/oberkante-ohne-privileg.md) - der Schaetzer, dessen Etikett hier ersetzt wird
* [Drei Auflagenformen im Lauf](/befunde/drei-auflagen-im-lauf.md) - woher die Zahlen stammen, die den Ausgang "geliefert" als Hoehensignal ausschliessen
* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) - warum ein Geruest faellt
* [Invarianten](/mechanismen/invarianten.md) - `ACT23_POLICY` ist nicht `ACT23_CHOREO`
* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - Stufe 3
