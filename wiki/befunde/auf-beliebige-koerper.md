---
type: Befund
title: Auf beliebige Koerper ablegen - wenn der Arm den Koerper traegt, landet er in gut der Haelfte der Faelle auf dem Ziel
description: Erste Messung mit ACT23_AUF_ALLE (Nutzerwunsch) - "auf" darf jeden Koerper der Szene als Ziel nehmen, gewertet wird die Ablage beim Loslassen (ACT23_AUF_LOSLASSEN), Abrutschen danach ist verbesserungswuerdig, kein Fehler. Zwei Seeds, 80 Episoden, 72 davon mit Zielkoerper. Ein Drittel scheitert schon am Griff (nie angehoben), unabhaengig von der Zielart. Von den getragenen Koerpern landen auf der Platte 10 von 14, auf einem Wuerfel 9 von 16 und auf einer Balkenform 10 von 18 auf dem Ziel. Liegen bleiben sie auf der Platte immer, auf dem Wuerfel 4 von 9, auf Balken 3 von 10. Meine Vorhersage (auf Wuerfeln selten, auf Balken fast nie) war fuer die Ablage FALSCH und fuer das Liegenbleiben ungefaehr richtig. Nebenbei ein Wertungsfehler gefunden und behoben - Koerper, die am Ende stabil auf der Platte lagen, galten als nicht abgelegt.
tags: [act23, stapeln, sprache, nutzeridee, messen]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-09-24T00:00:00Z }
sources:
  - id: lauf
    resource: "Code 9edc3cc, Nachzaehlung mit der Wertung aus dem Folgecommit. Kopien von act23_state.pkl (ad9d768c, danach unveraendert), Seeds 9501 und 9502 je 40 Ep parallel, ACT23_ZIEL_ADRESSE=1 ACT23_ZIEL_RELATION=auf ACT23_ZIEL_MISCH=1.0 ACT23_AUF_ALLE=1 ACT23_AUF_LOSLASSEN=1 ACT23_SOCKEL=1 ACT23_EIG_DIREKT=1 ACT23_EIG_STETIG=1 Chroma-Schnitt+Konzentrisch, ACT16_GOAL_Z=1 ACT16_GRIFF_Z=1 ACT16_ERFOLG_RUHT=1 ACT16_ZIEL_SAEUBERN=0; kein Tasten"
    title: Zwei Seeds, auf alles
  - id: frage
    resource: /fragen/stapeln-als-aufgabe.md
    title: Der Nutzerwunsch und die Einschaetzung vorher
---

# Die Frage

Nutzerwunsch: nicht nur auf die Platte, sondern auf **jeden vorhandenen Koerper** ablegen. Es geht
um das Ziel und das Hinlegen, nicht um das Liegenbleiben: *"Wenn es beim Loslassen herunter
rutscht, finde ich das nicht schlimm ... verbesserungswuerdig, aber nicht als Fehler."*

Gebaut (alle Vorgaben aus):

* `ACT23_AUF_ALLE=1` - "auf" nimmt Platten UND alle Objekte der Szene als Ziel.
* `ACT23_AUF_LOSLASSEN=1` - eine "auf"-Ablage zaehlt als geliefert, wenn der Koerper **auf dem Ziel
  abgelegt** wurde: im letzten gehaltenen Augenblick seitlich innerhalb der Liefertoleranz (25 mm)
  und mit der Unterkante auf Hoehe der Oberkante des Zielkoerpers - oder er liegt am Ende oben auf
  ihm (innerhalb 45 mm seiner Mitte). Das Zweite kam nach diesem Lauf dazu, s. unten.
* `ACT23_ZIEL_RELATION=alle` - je Episode "auf" (1/5) oder eines der vier Richtungswoerter.

**Vorher aufgeschriebene Einschaetzung** ([Stapel-Seite](/fragen/stapeln-als-aufgabe.md)): ein
Wuerfel traegt bis ~12 mm Versatz, ein Balken bis ~7 mm, die Ablage liegt im Median 19-25 mm
daneben - "selten erfolgreich, auf Balken fast nie".

# Ergebnis

    Zielart      Ep   nie angehoben   auf dem Ziel abgelegt   davon liegt oben   davon rutscht ab
    Platte       22        8             10 von 14 getragen         10                 0
    Wuerfel      26       10              9 von 16 getragen          4                 5
    Balkenform   24        6             10 von 18 getragen          3                 7

    seitlicher Abstand beim Loslassen, Median: 24-26 mm, bei allen drei Zielarten gleich

**Die Ablage auf einem Koerper gelingt in gut der Haelfte der getragenen Faelle - auf Wuerfeln
und Balken fast gleich oft.** Meine Einschaetzung "selten, auf Balken fast nie" war fuer das
ABLEGEN falsch. Fuer das LIEGENBLEIBEN stimmt sie ungefaehr: auf der Platte bleibt jede Ablage
liegen, auf dem Wuerfel etwa jede zweite, auf dem Balken jede dritte.

Der Grund fuer den Unterschied: meine Einschaetzung rechnete mit dem Stabilitaetskriterium
(Schwerpunkt ueber der Auflage), die Wertung des Nutzers mit der Ablage. Bei 25 mm Toleranz und
einem Median von 25 mm liegt ungefaehr die Haelfte innerhalb - unabhaengig davon, worauf.

**Der groesste Verlust liegt vor der Ablage:** ein Drittel der Episoden (24 von 72) hebt den
Koerper nie an. Das ist der Griff, und er haengt nicht an der Zielart.

# Ein Wertungsfehler, gefunden und behoben

Die erste Fassung wertete nur "beim Loslassen innerhalb 25 mm". Zehn Episoden standen dann als
*"nicht auf dem Ziel | danach: bleibt oben"* im Protokoll, sieben davon auf der Platte: der Koerper
war 25-26 mm neben der Mitte losgelassen worden und lag stabil auf der 70-mm-Platte. Zweitens
pruefte "bleibt oben" nur die Hoehe, nicht ob der Koerper auf DIESEM Ziel liegt. Beides ist
behoben (liegt am Ende oben UND innerhalb 45 mm der Zielmitte zaehlt als abgelegt). Die Zahlen
oben sind mit der neuen Wertung aus denselben Protokollen nachgezaehlt (Endabstand aus der
`[Ablage]`-Zeile); nach der alten Wertung waeren es 4 / 7 / 9 gewesen.

# Fallen

* **Einzelmessung, zwei Seeds, kein Vergleich.** Beschreibt, was passiert; belegt keine Wirkung.
* **Waehrend des Laufs galt noch die alte Wertung** fuer das Lernetikett (`res["ok"]`): 11 Episoden
  wurden per `AUF_LOSLASSEN` zu "geliefert" hochgestuft, die nachgezaehlten Platten-Faelle nicht.
* **Die Hoehe des Zielkoerpers kommt noch aus dem Simulator** (Geruest). Nach Nutzervorgabe
  ([Kamera statt Tasten](/mechanismen/hoehe-ertasten.md)) ist der naechste Kandidat dafuer die
  Parallaxe im Kamerabild, nicht das Tasten.
* **Gleichfarbige Stapel** sind fuer die Wahrnehmung nicht trennbar; kam hier vor, ist nicht
  gesondert gezaehlt.

# Verwandt

* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - der Nutzerwunsch und die Einschaetzung
* [Beim Ablegen zaehlt nur die seitliche Genauigkeit](/befunde/ablage-und-platzieren.md) - die 19-25 mm
* [Richtungswoerter selbst gelernt](/befunde/richtungswoerter-selbst-gelernt.md) - der andere Teil des Spielfelds
