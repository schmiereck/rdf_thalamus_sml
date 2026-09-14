---
type: Befund
title: Die Verschmelzung an der Quelle - der Chroma-Schnitt senkt grobe Adressfehler und Rueckfall zugleich, kostet aber Quote
description: Ein unsupervised Chroma-Schnitt in perceive_all ersetzt eine verschmolzene Komponente durch ihre Teile, statt neben ihnen stehen zu bleiben. Grobe Adressierungsfehler 3,1 auf 0,6 Prozent, privilegierter Rueckfall 10,0 auf 5,0 Prozent - der erste Eingriff, der beide zugleich senkt. Die Lieferquote faellt dabei von 66,0 auf 55,7 Prozent. Alle drei liegen bei p um 0,04 bis 0,07 und ueberstehen die Bonferroni-Schranke nicht. Der Aufbau hat ausserdem einen bekannten Fehler: die gelernten Formklassen stammen aus ungeteilten Komponenten.
tags: [act23, wahrnehmung, verschmelzung, ab]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-14T00:00:00Z }
sources:
  - id: ab
    resource: "Drei kopflose Steuerungslaeufe je 150 Episoden aus derselben Kopie von act23_state.pkl (ad9d768c), ACT23_GROESSE_SPANNE=1 ACT23_EIG_IDENT=1, ACT_SHAPE_CHROMA_SPLIT 0/1/1 mit TRENNUNG 1,0 und 0,6"
    title: Chroma-Split-A/B, drei Arme
  - id: sonde
    resource: "40 dichte Szenen (5 Koerper) und 40 weite Szenen (2 Koerper, 90-130 mm) auf einer Zustandskopie"
    title: Kalibrierung von Tiefe und Trennungsschranke
---

# Warum an der Quelle

Drei Anlaeufe haben je einen VERBRAUCHER der Wahrnehmung repariert - Abstufung, Eig-Split,
Farbbindung - und alle drei sind gescheitert
([1](/befunde/abstufung-statt-privileg.md), [2](/befunde/eig-split-im-lauf.md),
[3](/befunde/farbbindung-pixelweise.md)). Der Befund, der sie ausgeloest hatte, sagt aber nicht
"ein Verbraucher ist kaputt", sondern: **26 von 26 groben Adressfehlern liegen im Band der
verschmolzenen Blobs** ([Befund](/befunde/adressfehler-sind-verschmelzung.md)). Also die Quelle.

# Zwei Vermutungen, unterwegs widerlegt

**Erstens**, die naheliegendste: es gibt laengst einen farbfreien Erosions-Split (`SPLIT_FUSED`),
er ist **an**, und er laesst die verschmolzene Komponente *zusaetzlich* in der Liste -
`finde_nach_eigenschaften` nimmt `max(area)`, also den Elternblob. Gemessen ist dieser Fall
**4,5 %**. Der eigentliche Fall ist ein anderer:

    dichte Szenen, 200 Koerper      ein Teil auf 20 mm liegt vor   davon nicht gewaehlt
      Erosions-Split (heute)                71,0 %                       4,5 %
      -> in 29,0 % liegt GAR KEIN Teil beim Koerper

**Zweitens**: pixelweise nach den gelernten Farbklassen zu trennen erreicht 99,5 % - und wurde
verworfen. Eine **neue** Farbe muss trennbar sein, BEVOR sie eine Klasse hat; sonst haengt die
Wahrnehmung eines neuen Objekts daran, dass es schon bekannt ist. Das widerspraeche
[dem Projektziel](/ziel.md) direkt.

# Gebaut: unsupervised, und es ersetzt

Zwei Mittel per Lloyd-Iteration auf der Chromatizitaet der Komponente, **ohne Klassen**.
Angenommen wird der Schnitt nur, wenn die Mittel weiter auseinanderliegen als die Schwelle des
Farb-Offenmengen-Moduls (`TH`) - also genau dann, wenn sie **als zwei Klassen gelten wuerden**.
Keine neue Zahl, die schon kalibrierte.

Drei Eigenschaften, jede aus einem der drei Fehlschlaege gelernt:

* **Es ersetzt, statt danebenzustehen.** Zerfaellt die Komponente, verschwindet der Elternblob.
  `max(area)` kann ihn nicht mehr waehlen.
* **Es fasst nicht an, was eins bleibt.** Bleibt die Komponente eine, behaelt sie ihren exakten
  Schwerpunkt. Daran starb der Eig-Split: ein Schnitt, der auch dort schneidet, wo nichts zu
  schneiden ist, kostet in JEDER Episode und nuetzt nur in wenigen.
* **Es rekursiert** (Tiefe 3). Binaer reicht nicht - ein Blob aus drei Koerpern bliebe halb
  verschmolzen. Gemessen: Trefferquote 84,5 -> 100 %.

# Die Schranke, die noetig war

Der erste Wurf hatte genau die alte Krankheit: bei **weit getrennten** Koerpern 3 Detektionen fuer
2 Koerper, Lokalisierungsfehler 0,86 -> 3,85 mm. Ein einzelner Koerper zerfaellt chromatisch
naemlich auch - Deckflaeche und Seitenflaechen sind verschieden beleuchtet, und ihr Abstand
ueberschreitet `TH`.

Das Unterscheidungsmerkmal ist **raeumlich, nicht farblich**: zwei nebeneinander liegende Koerper
haben weit auseinanderliegende Schwerpunkte; eine Schattierung teilt denselben Koerper in
Schichten, deren Schwerpunkte fast zusammenfallen. Massstabsrelativ formuliert (Schwerpunktabstand
gegen groesseren Teilradius), damit keine Laenge in Pixeln festgeschrieben wird.

    TRENNUNG   weite Szenen (2 Koerper)        dichte Szenen (5 Koerper)
               Median   Detektionen je Szene   Teil liegt vor   gewaehlt > 20 mm
      aus      0,86 mm        2,0                  71,0 %            33,5 %
      0,6      3,85 mm        2,5                  99,0 %             7,0 %
      1,0      0,96 mm        2,0                  96,5 %            10,0 %
      1,4      0,90 mm        2,0                  90,0 %            17,5 %

# Der Lauf

    Arm         Ep   Quote | Adr.Median  grobe Fehler >20mm | Rueckfall | Band riesig
    vs_aus     150  66,0 % |   3,2 mm       5/159 =  3,1 %  |    15     |   5/21
    vs_streng  150  57,3 % |   2,2 mm       1/157 =  0,6 %  |     9     |   1/17
    vs_weich   150  54,0 % |   3,6 mm       1/161 =  0,6 %  |     6     |   0/10

    beide Chroma-Arme zusammen gegen die Vorgabe
      grobe Fehler   2/318 gegen 5/159    p = 0,044
      Rueckfall     15/300 gegen 15/150   p = 0,069     (10,0 -> 5,0 % der Episoden)
      Quote        167/300 gegen 99/150   p = 0,042     (66,0 -> 55,7 %)
      Bonferroni fuer zwei Vergleiche: 0,025 -- nichts davon uebersteht sie

**Der erste Eingriff, der Adressierung UND Rueckfall zugleich senkt.** Alle bisherigen haben
getauscht: die Groessenachse kaufte Adressierung mit Rueckfall, der Eig-Split verschlechterte
beides.

# Was traegt, auch ohne Signifikanz

Die Bandverteilung ist Mechanismus-Beleg und braucht keinen Test:

    Adressen im Band riesig    vs_aus 21   vs_streng 17   vs_weich 10
    Adressen im Band winzig    vs_aus  2   vs_streng  3   vs_weich 10

`riesig` ist das Band der verschmolzenen Blobs (kein einzelner Koerper misst so viel ausser
obj_U). **Die uebergrossen Detektionen verschwinden tatsaechlich**, und die Masse wandert in
kleinere Baender - genau das, was ein funktionierender Schnitt tun muss. Dass die Fehler dort von
5/21 auf 1/27 fallen (p = 0,073), passt dazu, traegt aber fuer sich allein nicht.

# Der Aufbaufehler, den ich benennen muss

**Beide Chroma-Arme liefen auf einem Zustand, dessen Formklassen aus UNGETEILTEN Komponenten
gelernt sind.** Die 80 Exemplare je Klasse wurden auf verschmolzenen Blobs mitgerechnet; ein
geaenderter Schnitt aendert die Deskriptorverteilung, und die gelernten Klassen sind dann teilweise
veraltet.

Genau dieser Fehler wurde bei den [relativen Ringen](/befunde/relrings-im-lauf.md) vermieden -
dort liefen **beide** Arme mit `ACT23_FRESH=1` bei null, mit der ausdruecklichen Begruendung, ein
geaenderter Deskriptor sei mit dem gespeicherten Bestand nicht vergleichbar. Hier habe ich es
nicht getan.

> **Der Quotenverlust kann deshalb ein Artefakt des veralteten Exemplarbestands sein und nicht
> eine Wirkung des Schnitts.** Die Adressierung ist davon weniger betroffen - sie haengt an Lage
> und Farbe, nicht an der Formklasse -, und das passt zum Befund, dass Adressierung und Rueckfall
> gewinnen, waehrend die Quote verliert.

Entschieden ist das nicht. Die Messung, die es entscheiden wuerde: beide Arme frisch bei null,
wie im Relrings-A/B.

> **AUFGELOEST (2026-09-14).** Der frische Vergleich bestaetigt den Verdacht: der
> Quotenverlust reproduziert NICHT, wenn beide Arme ihre Klassen unter ihrem eigenen Schnitt
> lernen (17,0 gegen 13,0 % zugunsten des Schnitts). Der Adressierungsgewinn reproduziert
> allerdings ebenfalls nicht - er kehrt sich um. Entschieden wird die Frage erst durch die
> Wiedervorlage der Laufszenen. Siehe [Frisch bei null](/befunde/chroma-split-frisch.md).

# Bewertung

* **`evidenz: einzelmessung`, nicht `gemessen`.** Drei Kennzahlen bei p = 0,04 bis 0,07, keine
  uebersteht die Bonferroni-Schranke, ein Seed je Arm.
* **Die Richtung ist konsistent und der Mechanismus belegt.** Fuenffach weniger grobe Fehler,
  halbierter Rueckfall, halbiertes `riesig`-Band - drei unabhaengige Groessen, alle stimmig.
* **Die Quote liegt im ueblichen Streubereich.** Ueber die bisherigen Arme dieser Sitzung reicht
  sie von 54,0 bis 66,0 % bei Konfigurationen, die sie teils gar nicht beruehren sollten.
* **`ACT_SHAPE_CHROMA_TRENNUNG=1,0` ist die richtige Fassung**, falls eingeschaltet wird: sie
  haelt die Feinheit bei getrennten Koerpern (0,96 gegen 0,86 mm) und gewinnt fast ebenso viel wie
  die weiche.

# Folgen

`ACT_SHAPE_CHROMA_SPLIT` bleibt auf `0`. Der naechste Schritt ist **nicht** ein weiterer Schalter,
sondern derselbe Vergleich frisch bei null - erst dann ist der Quotenverlust zu deuten.

# Verwandt

* [Jeder grobe Adressfehler sitzt im obersten Band](/befunde/adressfehler-sind-verschmelzung.md) - der Anlass
* [Der Form-Split im Eigenschafts-Pfad schadet](/befunde/eig-split-im-lauf.md) - woher die "nicht anfassen, was eins bleibt"-Regel stammt
* [Relative Ringe im Lauf](/befunde/relrings-im-lauf.md) - der Aufbau, den ich haette kopieren muessen
* [Frisch bei null](/befunde/chroma-split-frisch.md) - die Wiederholung, die den Aufbaufehler aufloest
* [Verschmelzungs-Abstandskurve](/befunde/verschmelzung-abstandskurve.md)
* [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md)
