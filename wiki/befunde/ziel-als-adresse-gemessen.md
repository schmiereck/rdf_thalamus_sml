---
type: Befund
title: Die Zieladresse traegt - und der Quotenverlust ist die Geometrie, nicht die Sprache
description: Drei Arme je 140 Episoden aus derselben Zustandskopie. Die Adresse loest in 91 bis 97 Prozent der Episoden eindeutig auf und trifft den Bezugskoerper auf 1,0 mm im Median - das Ablageziel kommt jetzt aus der Kamera statt aus mocap_pos. Die Lieferquote faellt von 57,1 auf 35,7 Prozent, wenn die Ablage 50 mm neben einem Koerper liegt (p = 4,9e-4), aber nur auf 49,3 Prozent bei 90 mm - statistisch ununterscheidbar vom Marker-Arm. Die vorab benannte Nachbarnaehe erklaert 13,6 der 21,4 verlorenen Punkte, und sie war unabhaengig auf 13,9 beziffert. Der Verlust sitzt im OBEREN ZEHNTEL des Ablagefehlers (p90 86 gegen 31,5 mm), nicht im Median und nicht nach dem Loslassen.
tags: [act23, kommando, aufgabe, stapeln, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-17T00:00:00Z }
sources:
  - id: ab
    resource: "Drei kopflose Laeufe je 140 Episoden aus identischen Kopien von act23_state.pkl (ad9d768c), Seed 4242: ort / an05 (ACT23_ZIEL_ADRESSE=1) / an09 (zusaetzlich ACT23_ZIEL_ABSTAND=0.09)"
    title: Das Ablageziel als Adresse, A/B
  - id: bau
    resource: /mechanismen/ziel-als-adresse.md
    title: Der Bau
---

# Die Frage

[Stufe 1](/mechanismen/ziel-als-adresse.md) macht aus dem Ablageziel eine **Adresse**: der
Zielplatz bekommt denselben Typ wie das Objekt und wird aus der Kamera aufgeloest statt aus
`sim.d.mocap_pos` gelesen. Zwei Dinge waren zu messen - **traegt die Adresse**, und **was kostet
sie**.

Der Konfounder war [vorab benannt](/mechanismen/ziel-als-adresse.md): eine Ablage 50 mm neben
einem Koerper liegt in der Zone, in der [Nachbarnaehe](/befunde/nachbarnaehe-im-lauf.md) gemessen
13,9 Punkte kostet (Schwelle 55 mm). Deshalb lief ein **dritter Arm mit 90 mm** als Kontrolle.

# Zahlen

    Arm    Ep   geliefert   Quote  | Adresse geloest   Rueckfall | Bezugskoerper wahrgenommen
    ort   140      80      57,1 %  |        -               0    |          -
    an05  140      50      35,7 %  | 127/139 = 91,4 %      12    | Median 1,0 mm, p90 7, max 29
    an09  140      69      49,3 %  | 135/139 = 97,1 %       4    | Median 1,0 mm, p90 7, max 30

    Lieferquote, Fisher zweiseitig (Bonferroni-Schranke fuer 3 Vergleiche: 0,0167)
      ort  gegen an05    p = 4,9e-4   SIGNIFIKANT
      ort  gegen an09    p = 0,231
      an05 gegen an09    p = 0,029    (unter der Schranke, also nicht belastbar)

**Die Adresse traegt.** In 91 bis 97 % der Episoden ist der genannte Bezugskoerper eindeutig, und
er wird auf **1,0 mm** genau wahrgenommen. Das Ablageziel war bis hierhin das einzige Stueck des
Befehls, das der Agent nicht wahrgenommen hat; es ist es nicht mehr.

# Der Quotenverlust ist die Geometrie

    ort  57,1 %  -> an05  35,7 %      -21,4 Punkte
    ort  57,1 %  -> an09  49,3 %       -7,8 Punkte, p = 0,231 (nicht unterscheidbar)

**Die Ablagestelle von 50 auf 90 mm zu schieben holt 13,6 der 21,4 Punkte zurueck** - 64 % des
Verlusts, allein durch den Abstand, bei identischer Sprache. Und die Zahl war vorhergesagt:
die unabhaengige Messung der Nachbarnaehe beziffert den Effekt auf **13,9 Punkte**.

> Das ist der eigentliche Wert des dritten Arms. Ohne ihn stuende hier "die Zieladresse kostet
> 21 Punkte Lieferquote", und das waere falsch zugeordnet.

Belastbar ist die Aussage **nicht** ueber den direkten Vergleich an05 gegen an09 (p = 0,029 reisst
die Bonferroni-Schranke), sondern ueber die Lage zum Marker-Arm: an05 liegt klar darunter,
an09 ist von ihm nicht zu unterscheiden.

# Wo genau der Verlust sitzt

    Arm    gegriffen  getragen  geliefert | tragen|griff  liefern|ablage
    ort       129       106        80     |    82,2 %        75,5 %
    an05      120        91        50     |    75,8 %        54,9 %
    an09      126       107        69     |    84,9 %        64,5 %

    liefern|abgelegt:  ort gegen an05  p = 0,0027  SIGNIFIKANT
                       ort gegen an09  p = 0,100
                       an05 gegen an09 p = 0,192

Der Griff ist fast unberuehrt (129/120/126). **Der Verlust sitzt in der letzten Etappe** - ob eine
abgelegte Sendung auch ankommt.

Und dort sitzt er **nicht im Median, sondern im oberen Zehntel**:

    seitlicher Fehler beim Loslassen    Median   p75    p90
      ort                                25,0   26,0   31,5
      an05                               25,0   30,0   86,0
      an09                               25,0   27,5   43,4

    Drift NACH dem Loslassen            Median   p90   Anteil > 25 mm
      ort                                12,0   21,0      2,8 %
      an05                               12,0   23,0      8,8 %
      an09                               11,0   20,0      2,8 %

**Der Arm legt genauso genau ab wie immer** - der Median ist in allen drei Armen exakt 25,0 mm,
und die Drift danach ist praktisch identisch. Was sich aendert, ist der Schwanz: in einem von zehn
Faellen kommt das Objekt 86 statt 31 mm daneben **an**.

> Es wird also **falsch hingetragen, nicht weggestossen.** Waere der Nachbar ein mechanisches
> Hindernis, muesste die Drift NACH dem Loslassen explodieren; sie tut es nicht (8,8 gegen 2,8 %,
> und der Median ist gleich). Der Fehler steht schon beim Oeffnen der Klaue in den Zahlen.

Das ist die Signatur der [Ablenker-Bindung in der Anfahrt](/befunde/ablenker-anfahrt.md), nur an
der anderen Seite der Episode: dort fahren 6,8 % der Episoden >80 mm am OBJEKT vorbei, hier landet
das obere Zehntel 86 mm neben dem ZIEL - und zwar genau dann, wenn am Ziel ein Koerper steht.

**Das ist nicht bewiesen, sondern die naechstliegende Erklaerung.** Der Gegenkandidat waere die
Anfahrgeometrie (die Klaue muss ueber den Nachbarn hinweg absenken). Die Unterscheidung braucht
die Schrittdaten des Transports und ist nicht gemessen.

# Was das fuer Stufe 2 heisst

Stapeln verlangt **per Definition** ein Ziel, an dem ein Koerper steht - nicht 50 mm daneben,
sondern 0 mm. Der hier gemessene Effekt ist damit kein Randproblem der Stufe 1, sondern die
**Vorbedingung der Stufe 2**:

> Bevor gestapelt werden kann, muss der Transport ein Ziel aushalten, an dem ein Koerper steht.
> Heute haelt er 90 mm Abstand aus und 50 mm nur schlecht.

Das ist ein konkreter, messbarer Zwischenschritt - und er war vor dieser Messung nicht sichtbar.

# Fallen

* **Ein Seed je Arm.** Die Quotenaussagen ruhen auf je einem Lauf. Belastbar sind die
  Adress-Kennzahlen (n = 139 Adressen je Arm), nicht die 7,8 Punkte zwischen ort und an09.
* **Die Arme laufen nach der ersten abweichenden Entscheidung auseinander.** Insbesondere ist die
  Aufloesungsrate 91,4 gegen 97,1 % (p = 0,068) **nicht** sauber dem Abstand zuzuschreiben: wer
  50 mm neben Koerper ablegt, verdichtet die Szene und erzeugt damit die Verschmelzungen, an denen
  die Adresse dann scheitert. Plausibel und selbstkonsistent, aber nicht getrennt gemessen.
* **8 von 139 Adressen in an05 waren beim Aussprechen eindeutig und beim Aufloesen "nicht
  gefunden".** Zwischen Wurf und Aufloesung laufen 40 Physikschritte (`sim.step(40)` in
  `run_combined`); die Szene setzt sich also noch. Kein Fehler, aber die Adresse wird vor der Ruhe
  gesprochen.
* **Kein Fall von "keine erreichbare Ablage daneben"** in beiden Armen - die acht gewuerfelten
  Peilungen haben immer eine gefunden. Die Schranke ist also ungetestet.
* **Die Lieferquote ist nicht das Kriterium** ([ziel.md](/ziel.md)). Sie steht hier, weil sie der
  Preis der Sprachaenderung ist, nicht weil sie ihr Zweck waere.
* **Vorgabe bleibt 0.**

# Verwandt

* [Das Ablageziel als Adresse](/mechanismen/ziel-als-adresse.md) - der Bau
* [Stapeln als neue Aufgabe](/fragen/stapeln-als-aufgabe.md) - die vier Stufen
* [Nachbarnaehe im Lauf](/befunde/nachbarnaehe-im-lauf.md) - die 13,9 Punkte, die hier als 13,6 wiederkommen
* [Ablenker-Bindung in der Anfahrt](/befunde/ablenker-anfahrt.md) - dieselbe Signatur am anderen Ende der Episode
* [Ablage und Platzieren](/befunde/ablage-und-platzieren.md) - warum der Median beim Loslassen 25 mm ist
