---
type: Befund
title: Die Direkt-Adresse verkuerzt die Aneignung eines neuen Koerpers auf 8 bis 22 Episoden - aber eine Adresse, die nur "Wuerfel" sagt, trifft den Koerper nicht
description: Nutzerauftrag - klaeren, ob die Adresse ohne Klasse (ACT23_EIG_DIREKT=1 EIG_STETIG=1) die Zeit bis zum ersten Kommando verkuerzt. Gepaart mit den vier Kettenlaeufen (Stern/V x Seed 11/23, gleicher Code, gleicher Zustand). Die Adresse entsteht in allen vier Laeufen in Episode 7, das erste Kommando folgt in Episode 8, 22, 8 und 20 - gegen nie, 43, 80 und 76 ueber Klasse und Knopf. Vier von vier Paaren in dieselbe Richtung (Vorzeichentest p = 0,125, mehr ist bei vier Paaren nicht moeglich), dazu 59 statt 16 Kommandos auf den neuen Koerper. Die Lieferquote darauf ist gleich (27 gegen 31 Prozent). Der Haken - wo die Wahrnehmung den Koerper als bekannte Klasse liest, heisst die Adresse "cube"; sie passt dann auch auf die echten Wuerfel, der Arm fasst nur in 2 von 15 Kommandos am V zu und liefert es nie.
tags: [act23, selbstlernen, kommando, lernen, nutzeridee, ab]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-09-26T00:00:00Z }
sources:
  - id: lauf
    resource: "Code 706c7f8. Kopien von act23_state.pkl (ad9d768c, danach unveraendert), ACT23_NOVEL_BODY=obj_Stern bzw. obj_V, Seeds 11 und 23, je 100 Ep; Arm Kette = Vorgaben (Laeufe vom 2026-09-25), Arm Direkt = zusaetzlich ACT23_EIG_DIREKT=1 ACT23_EIG_STETIG=1; zwei Prozesse je Block"
    title: Vier Paare Kette gegen Direkt
  - id: kette
    resource: /befunde/lerngeschwindigkeit-neuer-koerper.md
    title: Die Kettenlaeufe und der Engpass Geburt->Knopf
  - id: frueher
    resource: /befunde/adresse-ohne-klasse-gemessen.md
    title: Dieselbe Frage am 2026-09-16 im frischen Zustand (7 gegen 22 Episoden)
---

> **LUECKE GESCHLOSSEN 2026-09-26** (Abschnitt unten, Code b94bb66): mit `ACT23_EIG_DAUERHAFT=1`
> nennt die Direkt-Adresse Form UND Groesse, und mehrdeutige Treffer gehen an den naechsten zum
> Messwert. V/11: `'cube + mittel'`, 5 von 16 geliefert statt 0 von 15.

# Die Frage

Die [Kettenlaeufe](/befunde/lerngeschwindigkeit-neuer-koerper.md) zeigten: der Agent bildet die
Klasse eines neuen Koerpers frueh, kommandierbar wird er aber erst 30-56 Episoden spaeter, wenn
der Knopf vergeben ist. Die Adresse ohne Klasse (`ACT23_EIG_DIREKT`) braucht statt Geburt und
Bestaetigung nur EINE Sichtung. Am [16.09.](/befunde/adresse-ohne-klasse-gemessen.md) verkuerzte sie
das im **frischen** Zustand von 22 auf 7 Episoden. Gilt das auch im trainierten Zustand, fuer
Koerper, die die Wahrnehmung nur teilweise als neu liest?

**Vorher festgehalten** (Board): deutlich frueher; offen, ob Stern und V eine EINDEUTIGE
Formadresse bekommen.

# Ergebnis

    Koerper Seed   Kette: erstes Kommando   Direkt: Adresse   erstes Kommando   Kommandos   geliefert   Adresse
    Stern    11          nie                      Ep 7             Ep  8            17          6        '~gesehen' (Formvektor)
    Stern    23          Ep 43                    Ep 7             Ep 22            11          3        'neu-13 + dick'
    V        11          Ep 80                    Ep 7             Ep  8            15          0        'cube'
    V        23          Ep 76                    Ep 7             Ep 20            16          7        'cube + dick'

    zusammen            16 Kommandos, 5 geliefert (31 %)     59 Kommandos, 16 geliefert (27 %)
    Vorzeichentest: 4 von 4 Paaren frueher -> p = 0,125 (das Minimum bei vier Paaren)

    Lage des kommandierten Koerpers in der Klaue beim Zufassen ([InKlaue], privilegiert, nur Messung):
      Kette      in 15 von 16 Kommandos gemessen, Median 11-17 mm, nie ueber 30 mm
      Direkt     Stern 15/17, 11/11, V/23 10/16 gemessen, Median 11-17 mm
                 V/11 nur in 2 von 15 Kommandos -- der Arm fasste fast nie am V zu

# Was das heisst

1. **Die Zeit bis zum ersten Kommando schrumpft auf 8-22 Episoden**, in allen vier Paaren, im
   Mittel um mehr als 50 Episoden. Das bestaetigt die Messung vom 16.09. jetzt im trainierten
   Zustand und mit zwei weiteren Koerpern. Der neue Koerper wird dadurch auch fast viermal so oft
   kommandiert (59 gegen 16).
2. **Gekommen ist die Verkuerzung vor allem aus dem Warten.** Die Adresse steht in allen vier Laeufen
   in Episode 7 - beim ersten Blick nach dem ersten Hinstellen. Bis zum ersten Kommando vergehen
   dann 1 bis 15 Episoden, bis die Neugier den Koerper waehlt.
3. **Die Lieferquote auf dem neuen Koerper bleibt gleich** (27 gegen 31 %). Die Direkt-Adresse macht
   ihn frueher ansprechbar, nicht leichter greifbar.
4. **Eine Adresse, die nur eine BEKANNTE Klasse nennt, ist keine Adresse des neuen Koerpers.** Beim
   V liest die Wahrnehmung in vielen Lagen "Wuerfel" (s. die [Neuheits-Sonde](/befunde/lerngeschwindigkeit-neuer-koerper.md)).
   Mit Seed 11 hiess die Adresse deshalb `'cube'` - sie passt auf jeden Wuerfel der Szene. Der Arm
   fasste nur in 2 von 15 Kommandos am V zu und lieferte es nie. Mit Seed 23 hiess sie
   `'cube + dick'`; das Groessenband trennte das V von den echten Wuerfeln, und es klappte (7 von 16).
   Das ist die bekannte Grenze **"Eindeutigkeit ist nicht Richtigkeit"**: die Adresse wird beim
   Wuerfeln auf Eindeutigkeit in DIESER Szene geprueft, spaeter stehen andere Koerper da.

# Die Luecke geschlossen: ACT23_EIG_DAUERHAFT (Nutzerauftrag)

Die Ursache hatte zwei Teile (am Code):

1. **Anlegen.** `_adresse_wuerfeln` sucht die KUERZESTE Adresse, die in DIESER Szene eindeutig ist.
   Richtig fuer ein Kommando, das jede Episode neu gewuerfelt wird; falsch fuer eine Direkt-Adresse,
   die den ganzen Lauf steht. Beim V/11 stand im Moment der Sichtung kein Wuerfel in der Szene, also
   genuegte `'cube'`.
2. **Aufloesen.** `finde_nach_eigenschaften` nimmt bei mehreren Treffern still den
   FLAECHENGROESSTEN - bei `'cube'` also irgendeinen Wuerfel.

Nicht die Ursache war der Klassenname: bei stetiger Adressierung vergleicht `_eig_passt` die Form
ohnehin ueber den Vektor; `'cube'` ist dort nur das Etikett der Achse.

Mit `ACT23_EIG_DAUERHAFT=1` (Vorgabe 0) nennt die Direkt-Adresse alle gemessenen Eigenschaften des
Koerpers (Form und Groesse; die Farbe bleibt draussen, solange die Welt umfaerbt), und bei
mehreren Treffern gewinnt der, der dem gespeicherten Messwert am naechsten liegt (Abstand je Achse
auf ihre Toleranz normiert). Dieselben vier Laeufe, dazu `ACT23_DEBUG=1` fuer die echte
Aufloesung:

    Koerper Seed   Direkt                                   Direkt + Dauerhaft
    V        11    'cube'          0 / 15, Klaue am V  2/15  'cube + mittel'   5 / 16, Klaue 13/16
    V        23    'cube + dick'   7 / 16, Klaue 10/16       'cube + dick'     7 / 14, Klaue 13/14
    Stern    11    '~gesehen'      6 / 17, Klaue 15/17       '~gesehen + dick' 4 / 18, Klaue 14/18
    Stern    23    'neu-13 + dick' 3 / 11, Klaue 11/11       unveraendert (Adresse war schon vollstaendig;
                                                             der Lauf ist zeichengleich)
    zusammen       16 / 59 geliefert, Klaue 38/59            19 / 59 geliefert, Klaue 51/59
    erstes Kommando unveraendert: Ep 8 / 22 / 8 / 20

    echte Aufloesung (nur im Dauerhaft-Arm protokolliert):
      V/11      19x  Median 14 mm   > 40 mm: 6   mehrdeutig: 2
      V/23      25x  Median 14 mm   > 40 mm: 0   mehrdeutig: 15
      Stern/11  12x  Median  1 mm   > 40 mm: 3   mehrdeutig: 9

**Der Problemfall ist behoben** (0 -> 5 Lieferungen, Klaue am richtigen Koerper 2 -> 13 von 15/16),
die schnelle Aneignung bleibt, und der Arm fasst insgesamt deutlich oefter am richtigen Koerper zu
(51 gegen 38 von 59). Die Lieferungen auf den anderen drei sind im Rauschen gleich.

**Was bleibt:** in 9 von 56 protokollierten Aufloesungen landet die Adresse noch ueber 40 mm
daneben, also vermutlich auf einem anderen Koerper, und MEHRDEUTIG ist sie haeufig (26 von 56) - die
Wahl nach dem Messwert entscheidet diese Faelle meist richtig, nicht immer. Das zeigt die Grenze
einer Adresse aus EINER Sichtung: ein asymmetrischer Koerper sieht in jeder Lage etwas anders aus.
Naheliegende Fortsetzung: den gespeicherten Messwert mit weiteren eigenen Sichtungen nachfuehren
(die Adresse ist heute eingefroren).

**Einschraenkung:** ein Lauf je Koerper und Seed, 11-18 Kommandos. Der Schalter bleibt Vorgabe 0;
die Empfehlung ist, ihn ueberall dort zu setzen, wo `ACT23_EIG_DIREKT=1` gesetzt wird.

# Vorgabe und Nachfuehren (2026-09-27)

**`ACT23_EIG_DAUERHAFT` ist seit 82b9aa5 Vorgabe 1** (Nutzerentscheidung nach der Messung oben).
Er wirkt nur mit `ACT23_EIG_STETIG` bzw. `ACT23_EIG_DIREKT`; Laeufe ohne diese Schalter sind
unveraendert. Wer eine stetige Eigenschafts-Messung von vor 82b9aa5 nachstellen will, setzt ihn
auf 0.

**`ACT23_EIG_NACHFUEHREN` (Vorgabe 0) - gemessen, bringt nichts, verschlechtert die Eindeutigkeit.**
Gebaut nach dem Muster von `_streuung`: hat der Agent den Koerper selbst getragen UND die Adresse in
dieser Episode eindeutig aufgeloest, und liegt am Loslass-Punkt genau ein sauberer Fleck, wird
dessen Sichtung als weiteres BEISPIEL der Adresse gespeichert (hoechstens 10; ein Treffer zaehlt,
wenn er zu irgendeinem Beispiel passt). Dieselben vier Laeufe:

                        Dauerhaft                         Dauerhaft + Nachfuehren
    geliefert           19 / 59                           21 / 61
    nachgefuehrt        -                                 7-mal in 400 Episoden (1, 0, 1, 4 je Lauf)
    Aufloesungen        56, davon > 40 mm 9, mehrdeutig 26    67, davon > 40 mm 16, mehrdeutig 51
    Abstand der neuen Sichtungen zur bisherigen Adresse: 0,15-0,62 Toleranzen

    (die Laeufe bleiben bis Episode 87 zeichengleich - das erste Beispiel aendert lange keine
     Entscheidung)

**Was das zeigt, und es ist wichtiger als der Schalter:** jede neue Sichtung lag NAHE an der alten
Adresse. Der eigene Koerper faellt also nicht aus der Toleranz heraus - die Lage ist nicht das
Problem. Die Fehlaufloesungen entstehen, weil ANDERE Koerper in die Toleranz fallen. Mehr Beispiele
erweitern den Bereich, der als Treffer zaehlt, und machen genau das schlimmer (mehrdeutig 26 ->
51). Die richtige Richtung ist die umgekehrte: die Adresse muss lernen, was sie NICHT treffen darf
- etwa die Mitbewerber einer mehrdeutigen Aufloesung als Gegenbeispiele merken, oder die Toleranz
aus dem Abstand zu ihnen ableiten statt aus dem globalen `eig_bezug`. Nicht gebaut.

Einschraenkung: ein Lauf je Koerper und Seed; die Mehrdeutigkeits-Zaehlung stammt aus dem
Debug-Protokoll und ist die belastbarste Zahl hier.

# Fallen

* **Vier Paare, 100 Episoden.** Die Richtung ist in allen vier gleich und gross; ein Nachweis im
  statistischen Sinn ist mit vier Paaren nicht moeglich.
* **Kette und Direkt sind nicht je Episode gepaart**, sondern je Lauf (gleicher Seed, gleicher
  Zustand); sobald ein Arm anders entscheidet, laufen die Szenen auseinander.
* **"Erstes Kommando" zaehlt das Kommando, nicht den Treffer.** Bei V/11 wurde der Koerper frueh
  kommandiert und nie getroffen - die Zahl 8 steht dort fuer eine falsche Adresse.
* **Die Hausquote sinkt im Direkt-Arm** (37-46 gegen 44-54 %), weil der schwerere neue Koerper
  oefter drankommt - kein Schaden an den alten Koerpern belegt, nicht getrennt ausgewertet.
* **Die Aufloesung selbst ist nicht protokolliert** (nur mit `ACT23_DEBUG=1`); `[InKlaue]` ist ein
  Ersatzmass.

# Was daraus folgt

Die Direkt-Adresse leistet, wofuer sie gebaut ist: sie beseitigt die Wartezeit der Vergabe. Vor
einer Vorgabe-Aenderung (heute 0) waere die Luecke aus Punkt 4 zu schliessen: eine Direkt-Adresse,
die nur eine bekannte Klasse ohne weitere Achse nennt, sollte nicht vergeben werden - oder beim
Aufloesen auf den Formvektor zurueckgreifen, der den neuen Koerper tatsaechlich beschreibt.

# Verwandt

* [Lerngeschwindigkeit mit neuem Koerper](/befunde/lerngeschwindigkeit-neuer-koerper.md) - die Kettenlaeufe
* [Aus einer Sichtung kommandierbar](/befunde/adresse-ohne-klasse-gemessen.md) - dieselbe Frage im frischen Zustand
* [Eine dauerhafte Adresse darf keine Farbe nennen](/befunde/dauer-adresse-vertraegt-keine-farbe.md)
* [Adresse ohne Klasse](/mechanismen/adresse-ohne-klasse.md) - der Mechanismus
