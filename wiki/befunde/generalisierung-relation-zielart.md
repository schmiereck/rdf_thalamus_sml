---
type: Befund
title: Generalisierung Relation x Zielart - 100 Episoden Training verbessern nichts nachweisbar, die nie geuebten Zellen bewegen sich aber genauso wie die geuebten
description: Nutzerauftrag. 2x2-Aufbau (auf/links x Wuerfel/Balkenform), die Diagonale auf:balken und links:wuerfel im Training ausgelassen. Zwei unabhaengige Trainingsketten je 100 Episoden, danach Test auf den vier Zellen, untrainiert gegen trainiert, je Episode gepaart (59 Paare je Kette). Frage 1 - hat das Training etwas verbessert - ist mit diesen Daten nicht nachgewiesen - geuebte Zellen 34 gegen 41 bzw. 44 Prozent (p = 0,73 / 0,55), Lernkurve im Training flach. Damit ist Frage 2 nicht streng beantwortbar. Was die Daten zeigen - die nie geuebten Zellen verbessern sich in BEIDEN Ketten genauso stark wie die geuebten (33 gegen 41 bzw. 48 Prozent), am deutlichsten ausgerechnet die ausgelassene Zelle auf:balken (23 gegen 54 bzw. 62 Prozent, p = 0,22 / 0,06). Das passt zur Bauart - die Policy sieht Koordinaten und Zielhoehe, nicht die Art des Bezugs - ist aber nicht signifikant.
tags: [act23, generalisierung, stapeln, sprache, nutzeridee, gepaart]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-09-24T00:00:00Z }
sources:
  - id: lauf
    resource: "Code 5ec268b. Training: zwei Kopien von act23_state.pkl (ad9d768c, danach unveraendert), Seeds 7301/7302 je 100 Ep, ACT23_ZIEL_ZELLEN=auf:platte,auf:wuerfel,links:balken,rechts:*,vor:*,hinter:* (je wuerfel+balken). Test: B (untrainiert), T1, T2 auf Seeds 9601/9602 je 30 Ep, ACT23_SZENE_JE_EPISODE=1 ACT23_AUTO_CURIOUS=0 ACT23_ZIEL_ZELLEN=auf:wuerfel,auf:balken,links:wuerfel,links:balken. Beide Phasen: ACT23_ZIEL_RELATION=alle ACT23_RICHTUNG_QUELLE=kamera ACT23_AUF_ALLE=1 ACT23_AUF_LOSLASSEN=1 ACT23_SOCKEL=1 ACT23_EIG_DIREKT=1 ACT23_EIG_STETIG=1 Chroma-Schnitt+Konzentrisch ACT16_GOAL_Z=1 ACT16_GRIFF_Z=1 ACT16_ERFOLG_RUHT=1 ACT16_ZIEL_SAEUBERN=0; hoechstens zwei Prozesse"
    title: Training und gepaarter Test
---

# Die Frage

Nutzerauftrag: auf dem neuen Spielfeld (Relationen x beliebige Zielkoerper x zufaellige Farb-/
Formkombinationen) beobachten, ob Generalisierung auf **nie geuebte Kombinationen** stattfindet.

**Was hier ueberhaupt kombinationsspezifisch sein kann** (am Code geprueft, vor dem Lauf): die
Policy sieht `[Hand xyz, Objekt xy/z, Ziel xy, Greifer, Objekthoehe, Objektgrundflaeche,
Griffdruck, Zielhoehe, Greifhoehe]` - **keine Farbe und nicht die Art des Bezugskoerpers**. Die
Sprache wird vorher ueber die Wahrnehmung in Koordinaten uebersetzt. Generalisierung ueber
FARBkombinationen ist damit per Bauart gegeben (und die Farben werden ohnehin jede Episode neu
gewuerfelt). Echt offen ist die Ebene **Relation x Zielart**.

    Aufbau                Wuerfel          Balkenform
    auf                   geuebt           NIE GEUEBT
    links                 NIE GEUEBT       geuebt

Frage 1: verbessert das Training die geuebten Zellen? Frage 2: verbessern sich die nie geuebten
genauso?

**Vorher festgehaltene Erwartung** (Board, 21:00): der [Langlauf](/befunde/langlauf-ohne-fortschritt.md) zeigte
keinen Fortschritt; gut moeglich, dass Frage 1 mit Nein ausgeht und Frage 2 dann offen bleibt.

# Ergebnis

## Training: flach

    Kette   erste 50 Ep   zweite 50 Ep   ausgelassene Zellen gesehen
    T1        18            21                  0
    T2        23            22                  0

## Test: je Episode gepaart, untrainiert (B) gegen trainiert

    B gegen T1 (59 Paare)          B          T1        nur B | nur T1     McNemar
      geuebt        n = 32     11 (34 %)  13 (41 %)       3 |  5         p = 0,73
      ausgelassen   n = 27      9 (33 %)  11 (41 %)       4 |  6         p = 0,75
        auf:wuerfel    10       5          5              1 |  1
        links:balken   22       6          8              2 |  4
        auf:balken     13       3          7              1 |  5         p = 0,22
        links:wuerfel  14       6          4              3 |  1

    B gegen T2 (59 Paare)          B          T2        nur B | nur T2
      geuebt        n = 32     11 (34 %)  14 (44 %)       4 |  7         p = 0,55
      ausgelassen   n = 27      9 (33 %)  13 (48 %)       3 |  7         p = 0,34
        auf:wuerfel    10       5          6              2 |  3
        links:balken   22       6          8              2 |  4
        auf:balken     13       3          8              0 |  5         p = 0,06
        links:wuerfel  14       6          5              3 |  2

    "geliefert" mit ACT23_AUF_LOSLASSEN: bei "auf" zaehlt die Ablage auf dem Ziel

# Was das heisst

1. **Frage 1: kein Nachweis.** Beide Ketten liegen auf den geuebten Zellen 7 bzw. 10 Punkte ueber
   dem untrainierten Zustand, keine davon signifikant, und die Lernkurve im Training ist flach. Die
   Erwartung ist eingetreten.
2. **Frage 2 ist damit nicht streng beantwortbar.** Wo keine nachgewiesene Verbesserung ist, kann
   ihre Uebertragung nicht nachgewiesen werden.
3. **Was die Daten trotzdem zeigen:** die nie geuebten Zellen bewegen sich in BEIDEN Ketten
   mindestens so stark wie die geuebten (+8 / +15 gegen +7 / +10 Punkte). Am staerksten ausgerechnet
   die ausgelassene Zelle **auf:balken** (23 -> 54 / 62 %, 1:5 und 0:5 abweichende Paare). Die
   ausgelassene **links:wuerfel** faellt dagegen leicht (43 -> 29 / 36 %). Beides unter der
   Nachweisgrenze.
4. **Das Muster passt zur Bauart.** Fuer die Policy ist "auf Balken" dieselbe Aufgabe wie "auf
   Wuerfel": dieselbe Zielhoehe (24 mm), nur eine andere Koordinate. Wenn "auf Wuerfel" ueben das
   Ablegen in 24 mm Hoehe verbessert, muss "auf Balken" mitziehen. Umgekehrt ist "links vom
   Wuerfel" fuer sie nichts anderes als "links vom Balken".

**Nach [Projektziel](/ziel.md):** die Architektur generalisiert ueber Kombinationen, weil sie die
Sprache vor der Motorik in Koordinaten aufloest - das ist eine Eigenschaft der Bauart, keine
erlernte Leistung, und diese Messung kann sie weder bestaetigen noch widerlegen, solange das
Training selbst nichts Nachweisbares bewirkt.

# Fallen

* **Kleine Zellen.** 10 bis 22 Paare je Zelle; ein McNemar mit 5:0 erreicht bestenfalls p = 0,06.
  Ein Nachweis braeuchte etwa die vierfache Testmenge.
* **B ist in beiden Vergleichen derselbe Lauf.** T1 und T2 sind unabhaengige Replikate des
  Trainings, aber nicht des Tests; die gleiche Richtung in beiden ist deshalb schwaecher als zwei
  unabhaengige Befunde.
* **"geliefert" misst bei "auf" die Ablage, bei "links" Endlage innerhalb 25 mm.** Die Zeilen sind
  innerhalb einer Relation vergleichbar, zwischen den Relationen nicht.
* **100 Episoden.** Laengeres Training ist nach dem Langlauf kein aussichtsreicher Hebel; wenn,
  dann muesste sich am Lernen selbst etwas aendern.

# Verwandt

* [Auf beliebige Koerper](/befunde/auf-beliebige-koerper.md) - das Spielfeld
* [Richtungswoerter selbst gelernt](/befunde/richtungswoerter-selbst-gelernt.md) - die Wortbedeutungen
* [Struktur-Experte](/fragen/struktur-experte.md) - warum 90-Episoden-Vergleiche nur grobe Wirkungen aufloesen
* [Projektziel](/ziel.md)
