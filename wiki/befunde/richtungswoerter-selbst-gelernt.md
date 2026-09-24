---
type: Befund
title: Richtungswoerter aus eigener Ablage gelernt - das Kamera-Geruest laesst sich entfernen, ohne dass etwas verloren geht
description: Erste Messung der Richtungs-Relationen (links/rechts/vor/hinter aus Sicht der Kamera). Der Agent spielt 40 Episoden mit "an" und Zufallspeilung und etikettiert jede Ablage neben einem Bezug im Nachhinein mit dem Wort, das er im Bild sieht - 27 Etiketten, kein vorgegebenes Wort-Ziel. Danach liegen drei der vier gelernten Bedeutungen innerhalb von 1,5 Grad der Kamera-Achse, "links" bei nur 5 Beispielen 18 Grad daneben. Gepaarter Test (75 Episoden mit gleicher Szene und gleichem Wort), Kamera-Bedeutung gegen gelernte - Welt-Worttreffer 47 gegen 51 (McNemar 5 zu 9, p = 0,42), geliefert 35 gegen 35 (p = 1,00), kein einziger Rueckfall auf das Geruest. Liegt der Koerper neben dem Bezug (bis 80 mm), trifft das Wort 49 von 52 bzw. 48 von 52; die Fehltreffer sind fast alle misslungene Ablagen weit weg vom Bezug, keine falsch verstandenen Woerter. Das Selbsturteil stimmt in 123 von 124 beurteilten Episoden mit der Welt ueberein.
tags: [act23, sprache, relation, weniger-teacher, nutzeridee]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-09-24T00:00:00Z }
sources:
  - id: lauf
    resource: "Code b8a0f00. Spielphase: Kopie von act23_state.pkl (ad9d768c, danach unveraendert), 40 Ep Seed 7101, ACT23_ZIEL_ADRESSE=1 ACT23_ZIEL_RELATION=an. Test: aus dem gespielten Zustand Seeds 9301-9303 je 30 Ep, ACT23_SZENE_JE_EPISODE=1 ACT23_AUTO_CURIOUS=0 ACT23_ZIEL_ADRESSE=1 ACT23_ZIEL_RELATION=richtung, Arm K ACT23_RICHTUNG_QUELLE=kamera, Arm G =gelernt; je Seed beide Arme parallel"
    title: Spielphase und gepaarter Test
  - id: frage
    resource: /fragen/richtungs-relationen.md
    title: Die Nutzeridee und der Plan
---

# Die Frage

Nach der [Nutzeridee](/fragen/richtungs-relationen.md) gibt es jetzt die Relationen **links,
rechts, vor, hinter**, Bezugssystem Kamerabild (Nutzerentscheidung). Das Wort ist die einzige
Vorgabe; was es in der Welt bedeutet, kommt aus einer von zwei Quellen
(`ACT23_RICHTUNG_QUELLE`):

* **kamera** - Geruest: die Bildachse ueber die eigene Homographie in eine Weltrichtung uebersetzt.
* **gelernt** - aus den eigenen Ablagen: nach jeder Ablage neben einem Bezug sieht der Agent, in
  welcher Bildrichtung sein Koerper liegt, und merkt die Weltverschiebung unter diesem Wort.

Gefragt: laesst sich das Geruest entfernen - traegt die selbst gelernte Bedeutung genauso?

# Vorab gemessen (Sonde, 9 Stellen)

Die vier Bildachsen liegen hier bis 3 Grad genau auf Weltachsen: links = +y, rechts = -y,
hinter = +x (weg von der Kamera, +50 mm Kameraabstand bei 50 mm Schritt), vor = -x. Der
Arbeitsraum ist in y nur 140 mm breit; das Wort wird deshalb nur unter den Richtungen
gewuerfelt, deren Ziel erreichbar ist (Aufgabenerzeugung, keine Laufzeitregel).

# Spielphase: 40 Episoden "an", nur Etiketten

    beurteilte Ablagen 36, enthalten 3, gemerkt (Abstand 20-100 mm) 27

    Wort     n   gelernte Richtung   neben der Kamera-Achse   Einzelbeispiele vom Mittel (Median)
    links    5   (+0,31,+0,95)            18,0 Grad                    18 Grad
    rechts   7   (+0,01,-1,00)             0,5 Grad                    15 Grad
    hinter   6   (+1,00,+0,03)             1,5 Grad                    23 Grad
    vor      9   (-1,00,+0,02)             1,1 Grad                    30 Grad

**Kein einziges Wort-Ziel wurde vorgegeben** - "an" legt in eine zufaellige Richtung. Die
Einzelbeispiele streuen 15 bis 30 Grad (eine Zufallspeilung faellt irgendwo in den 90-Grad-Sektor
ihres Wortes), der Mittelwert findet trotzdem die Achse. Nur "links" ist mit 5 Beispielen noch
18 Grad daneben.

# Test: je Episode gepaart

    gepaart (gleiche Szene UND gleiches Wort)   75 von 90
      die 15 anderen: gleiche Szene, anderes Wort - die gelernte "links"-Richtung macht andere
      Ziele erreichbar, und der Wurf faellt anders

    Arm   Wort aufgeloest   beurteilt   Welt trifft Wort   selbst = Welt   geliefert   Rueckfaelle
    K           75              60             47               60/60          35            -
    G           75              64             51               63/64          35            0

    McNemar Welt-Worttreffer:  nur K 5 | nur G 9   ->  p = 0,42
    McNemar geliefert:         nur K 8 | nur G 8   ->  p = 1,00

**Die gelernte Bedeutung traegt wie das Geruest.** Kein Unterschied, kein Rueckfall; G hatte ab der
ersten Testepisode fuer jedes Wort genug eigene Beispiele.

## Die Fehltreffer sind Ablagen, keine Woerter

    alle 90 Episoden je Arm        neben dem Bezug (<= 80 mm)       weiter weg
                                   n    Wort getroffen              n    Wort getroffen
    K                              52        49                    21         7
    G                              52        48                    24        10

**Wo der Koerper neben dem Bezug ankommt, stimmt das Wort in 94 bzw. 92 Prozent.** Was fehlt,
sind fast ausschliesslich misslungene Ablagen 100 mm und mehr vom Bezug weg - dort ist die
Richtung Zufall. Die Sprache ist also nicht der Engpass, sondern wie bisher die Ablage selbst.

## Das Selbsturteil

In 123 von 124 beurteilten Episoden sagt der Agent aus eigener Wahrnehmung dasselbe Wort, das die
privilegierte Weltlage ergibt. Damit taugt es als Etikettquelle - genau das, worauf die gelernte
Bedeutung beruht.

# Einordnung

Nach dem Prinzip "weniger Teacher ist immer besser" ist das der erwuenschte Fall: **die Bedeutung
von vier Richtungswoertern entsteht aus 40 Spielepisoden und dem eigenen Blick, und das
Geruest kann weg**. Von aussen kommen nur die Woerter und der Standpunkt.

Nicht ueberbewerten: in dieser Welt sind die Wortrichtungen ueberall fast dieselben Weltvektoren
(Sonde: 3 Grad). Eine gelernte Bedeutung als EIN Mittelwert je Wort reicht deshalb, und die
Uebertragung auf neue Bezugskoerper ist per Bauart gegeben, keine Leistung. Eine Kamera mit
starker Perspektive oder ein Bezugssystem am Koerper ("vor dem Kreuz") braucht eine ortsabhaengige
Bedeutung - dann waere der lokale Ansatz des [Hoehenschaetzers](/befunde/lokaler-schaetzer-im-lauf.md)
das Vorbild.

# Fallen

* **Die Bedeutung ist heute ein Weltvektor, keine Phasendrehung im Latent**, wie auf der
  [Stapel-Seite](/fragen/stapeln-als-aufgabe.md) vorgeschlagen. Das Ziel wird weiterhin als
  Koordinate an `run_combined` gegeben - wie bei "an" und "auf".
* **"links" mit 5 Beispielen 18 Grad daneben**, und trotzdem kein Treffernachteil: bei 50 mm
  Abstand sind 18 Grad 16 mm seitlich, das Wort bleibt im Sektor. Bei 45 Grad kippte es.
* **Drei Seeds, 75 gepaarte Episoden.** Fuer "gleich gut" ist das eine Nicht-Widerlegung, keine
  Aequivalenz: ein Unterschied unter ~15 Punkten waere nicht aufgeloest.

# Verwandt

* [Richtungs-Relationen](/fragen/richtungs-relationen.md) - die Nutzeridee
* [Tastetikett gegen Privileg](/befunde/tastetikett-gegen-privileg.md) - dasselbe Muster bei der Hoehe
* [Gepaart je Episode](/messungen/act23-headless-ab.md) - die Messvorschrift
* [Struktur-Experte](/fragen/struktur-experte.md) - die Woerter als Pruefstein
