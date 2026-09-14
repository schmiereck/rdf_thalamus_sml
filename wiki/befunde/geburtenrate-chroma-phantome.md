---
type: Befund
title: Die verdreifachte Geburtenrate ist reines Phantom - der Chroma-Schnitt zerteilt Einzelkoerper in 28 Prozent der Szenen
description: Auf den Szenen des Laufs erzeugt der Schnitt 82 statt 14 neue Detektionen je 150 Szenen. Die Zahl der ECHTEN neuen Detektionen - solche, die einen ganzen Koerper bedecken - ist identisch: 13 gegen 13. Der ganze Zuwachs sind Bruchstuecke zerteilter Einzelkoerper und Detektionen, die bei keinem Koerper liegen. Damit ist die Entscheidung, den Schnitt auf Vorgabe zu stellen, auf einer unvollstaendigen Messung getroffen worden.
tags: [act23, selbstlernen, formklassen, wahrnehmung, negativ]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-14T00:00:00Z }
sources:
  - id: probe
    resource: "150 Szenen nach den Regeln des Laufs (pc_act16.scatter: 80 mm Mindestabstand, BASE_CLEAR, REACH_XY), 4 Koerper je Szene, Zustand ad9d768c, ACT_SHAPE_CHROMA_SPLIT 0/1 und TRENNUNG 1,0/1,6/2,2"
    title: Geburtsdruck auf der Lauf-Verteilung
---

# Die Frage

Aus [Frisch bei null](/befunde/chroma-split-frisch.md): der Chroma-Schnitt verdreifacht die
Geburtenrate (12 Klassen gegen 4, davon 9 gegen 2 verhungert). Ob das der Aneignung nutzt oder
schadet, war ungemessen - und es ist die fuer [das Projektziel](/ziel.md) wichtigste Zahl der
ganzen Serie.

# Die Antwort

    150 Szenen nach den Regeln des Laufs, 4 Koerper je Szene

                              CHROMA=0    CHROMA=1
      Detektionen je Szene       4,02        4,49      (erwartet 4)
      Szenen mit ZERTEILTEM Koerper  1,3 %     28,0 %
      neue Detektionen (shape=None)   14         82

        davon auf einem Koerper       13         13     <- unveraendert
        davon BRUCHSTUECK              0         54
        davon bei keinem Koerper       1         15

**Die Zahl der echten neuen Detektionen ist identisch: 13 gegen 13.** Der gesamte Zuwachs von 14
auf 82 besteht aus Bruchstuecken zerteilter Einzelkoerper (54) und Detektionen, die bei gar keinem
Koerper liegen (15).

> **Der Schnitt erzeugt keinen zusaetzlichen Aneignungsdruck. Er erzeugt Phantome.** Die 12
> geborenen Klassen des frischen Laufs sind damit nicht "dreimal so viel gelernt", sondern
> ueberwiegend Klassen auf Bruchstuecken - und die 9 Verhungerten sind ihr folgerichtiges Ende.

# Wie mir das entgangen ist

Zweimal habe ich die Zerteilung gemessen und zweimal die falsche Kennzahl genommen:

    Sonde "weite Szenen"        Detektionen je Szene  MEDIAN 2,0 bei 2 Koerpern   -> unauffaellig
    Wiedervorlage der Laufszenen Detektionen je Szene MEDIAN 4,0 bei 4 Koerpern   -> unauffaellig
    hier                        Detektionen je Szene  MITTEL 4,49 bei 4 Koerpern  -> auffaellig

**Der Median verdeckt eine Zerteilung, die jede vierte Szene trifft**, weil sie in der Mehrheit
der Szenen eben nicht auftritt. Dazu misst die Wiedervorlage den Abstand jedes Koerpers zur
NAECHSTEN Detektion - eine Kennzahl, die zusaetzliche Detektionen per Konstruktion nicht sehen
kann. Sie war richtig fuer die Frage "wird ein Koerper verfehlt" und blind fuer "wird einer
zerteilt".

# Der Schieber hilft, aber der Nutzen ist dann ungemessen

    TRENNUNG   zerteilte Szenen   neue Detektionen   davon echt   Bruchstuecke
      1,0           28,0 %              82               13            54
      1,6            8,0 %              35               12            14
      2,2            4,0 %              24               13             8
      (aus)          1,3 %              14               13             0

Die echten Neuheiten bleiben bei 12-13, die Phantome sinken mit der Schranke. **Aber der NUTZEN
des Schnitts - 20 von 1024 verfehlten Koerpern auf 0 - wurde bei TRENNUNG 1,0 gemessen. Ob er bei
2,2 erhalten bleibt, ist offen.**

Ein zweiter Punkt, der die Deutung stuetzt: auf DIESER Szenenverteilung verfehlt auch der feste
Schnitt **nichts** (0 von 600). Der gemessene Nutzen stammt aus den Szenen am EPISODENENDE, wo der
Arm Objekte zusammengeschoben hat; der Generator startet mit 80 mm Mindestabstand. Nutzen und
Schaden treten also in verschiedenen Phasen derselben Episode auf.

# Folge fuer die Entscheidung

[Der Chroma-Schnitt wurde auf Vorgabe gestellt](/entscheidungen/chroma-split-vorgabe.md) mit der
Begruendung, die Wahrnehmung werde belegbar besser. Das bleibt wahr fuer das gemessene Mass
(verfehlte Koerper) - und es war **unvollstaendig**: die Zerteilung von Einzelkoerpern war nicht
mitgemessen, obwohl genau sie die dort als "offen" notierte Geburtenrate erklaert.

Die Entscheidung steht damit **unter Vorbehalt**, bis eines von beidem gemessen ist:
der Nutzen bei einer Schranke, die nicht zerteilt (2,2), oder der Schaden der Phantomklassen im
Lauf.

# Fallen

* **`ebene: pruefstand`.** Die Zahlen sind Detektionen, keine Geburten - eine Geburt verlangt
  mehrfache Sichtung. Der Zusammenhang zu 12 gegen 4 geborenen Klassen ist plausibel, nicht
  bewiesen.
* **Die Bruchstueck-Zaehlung ist konservativ.** Die Bezugsflaeche je Koerper wird mit derselben
  Einstellung gemessen; wird ein allein stehender Koerper ebenfalls zerteilt, faellt der Bezug
  kleiner aus und Bruchstuecke werden als "ganz" gezaehlt. Die 54 sind also eher zu wenig.
* **Szenen bei Episodenbeginn**, nicht am Ende. Am Ende ist die Lage anders (s. oben).

# Verwandt

* [Frisch bei null](/befunde/chroma-split-frisch.md) - wo die offene Frage notiert wurde
* [Der Chroma-Schnitt wird Vorgabe](/entscheidungen/chroma-split-vorgabe.md) - die Entscheidung, die das betrifft
* [Die Geburtenrate hat zwei Ursachen](/befunde/geburtenrate-und-saettigung.md) - der aeltere Befund
* [Der blinde Fleck der Aneignung](/befunde/aneignung-blinder-fleck.md)
