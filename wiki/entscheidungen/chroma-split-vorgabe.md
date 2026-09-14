---
type: Entscheidung
title: Der Chroma-Schnitt wird Vorgabe - entschieden am Wahrnehmungsmass, nicht an der Lieferquote
description: ACT_SHAPE_CHROMA_SPLIT steht seit 2026-09-14 auf 1. Begruendet ist das mit der Wiedervorlage der Laufszenen (verfehlte Detektionen 20 von 1024 auf 0, p = 2e-06), nicht mit einem Quotengewinn - den gibt es nicht und wird es nicht geben, weil Verschmelzung im Lauf ein 2-Prozent-Phaenomen ist. Der bestehende act23_state.pkl hat seine Formklassen unter der ALTEN Segmentierung gelernt; ein Quoteneinbruch in den ersten Episoden waere erwartbar und kein Rueckschritt.
tags: [act23, wahrnehmung, verschmelzung, entscheidung]
status: widerlegt
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-14T00:00:00Z }
sources:
  - id: grund
    resource: /befunde/chroma-split-frisch.md
    title: Die Messung, auf der die Entscheidung beruht
---

> **ZURUECKGENOMMEN (2026-09-14, noch am selben Tag). `ACT_SHAPE_CHROMA_SPLIT` steht wieder
> auf `0`.** Der Nutzen ist an das aggressive Schneiden gekoppelt: bei einer Schranke, die
> nicht zerteilt (TRENNUNG 2,2), sind die verfehlten Koerper wieder bei 1,1 % - dem Wert
> ohne Schnitt. Es gibt keine Einstellung, die das eine ohne das andere hat.
>
> **UNTER VORBEHALT (der Zwischenstand, der dahin fuehrte).** Die Begruendung unten ist
> unvollstaendig: der Schnitt **zerteilt Einzelkoerper in 28 % der Szenen**, und die dort als
> "offen" notierte verdreifachte Geburtenrate ist dadurch reines Phantom - echte neue
> Detektionen 13 gegen 13, Bruchstuecke 54 gegen 0. Siehe
> [Die verdreifachte Geburtenrate ist reines Phantom](/befunde/geburtenrate-chroma-phantome.md).
> Der gemessene NUTZEN (verfehlte Koerper 20 -> 0) bleibt gueltig, wurde aber bei
> `TRENNUNG 1,0` gemessen; eine Schranke von 2,2 dritteln die Phantome, ihr Nutzen ist
> ungemessen.

# Was entschieden ist

`ACT_SHAPE_CHROMA_SPLIT` steht auf **1** (`shape_classifier.py`), mit `TRENNUNG 1,0` und
`TIEFE 3`. Abschalten: `ACT_SHAPE_CHROMA_SPLIT=0`.

Damit wird eine Komponente, die pixelweise nach Chroma in zwei tragende, raeumlich getrennte Teile
zerfaellt, **durch ihre Teile ersetzt**. Bleibt sie eine, wird sie nicht angefasst.

# Worauf sich die Entscheidung stuetzt - und worauf nicht

**Stuetzt sich auf** die Wiedervorlage der Laufszenen
([Befund](/befunde/chroma-split-frisch.md)): 270 nachgestellte Szenen aus den Protokollen, 1024
Koerper, beide Segmentierungen auf denselben Lagen, rein raeumlich gemessen.

    verfehlte Detektionen (>20 mm)   20 von 1024  ->  0 von 1024   Fisher p = 2e-06
    Median-Lokalisierung             1,3 mm       ->  1,8 mm
    Detektionen je Szene             4,0          ->  4,0          (bei 4 Koerpern)

**Stuetzt sich NICHT auf** die Lieferquote. Sieben Armvergleiche blieben uneindeutig, und der
Grund ist bekannt: Verschmelzung betrifft in den tatsaechlichen Szenen **2 %** der Wahrnehmungen -
weit unterhalb der [Nachweisgrenze](/befunde/rechnerlast.md) eines 150- bis 300-Episoden-Laufs.

> Das ist der Punkt, an dem [wiki/ziel.md](/ziel.md) die Entscheidung traegt: bewertet wird nach
> **Selbstaneignung und Wahrnehmung**, nicht nach Lieferquote. Ein Eingriff, der die Wahrnehmung
> belegbar verbessert und die Quote nicht bewegt, ist nach diesem Massstab ein Fortschritt.

# Was er kostet, vollstaendig

* **0,5 mm Median-Lokalisierung** (1,3 -> 1,8 mm). Der Preis dafuer, dass der Schwerpunkt eines
  geteilten Teils weniger exakt ist als der einer sauberen Komponente.
* **Rund 4 % Rechenzeit** je Episode.
* **Dreifache Geburtenrate mit hoher Sterblichkeit**: im frischen Lauf 12 geborene Klassen gegen 4,
  davon 9 gegen 2 verhungert. Mehr, kleinere, variantenreichere Teile erzeugen mehr neuartige
  Deskriptoren. Ob das fuer die Aneignung gut oder schlecht ist, ist **ungemessen** - ueberlebt
  haben 3 gegen 2, und das ist zu klein fuer eine Aussage.

# Die Warnung fuer den naechsten GUI-Lauf

**Der bestehende `act23_state.pkl` hat seine Formklassen unter der ALTEN Segmentierung gelernt.**
Die 80 Exemplare je Klasse wurden auf ungeteilten - teils verschmolzenen - Komponenten gerechnet.
Der Schnitt aendert die Deskriptorverteilung, also passen die gelernten Klassen zunaechst nicht
mehr ganz.

Gemessen ist genau dieser Unterschied:

    geladener Zustand, alte Klassen   Quote 66,0 -> 55,7 %
    beide Arme frisch bei null        Quote 13,0 -> 17,0 %  (zugunsten des Schnitts)

**Ein Quoteneinbruch in den ersten Episoden ist deshalb erwartbar und kein Rueckschritt** - die
Klassen konsolidieren sich unter dem neuen Schnitt neu. Wer das nicht will, faehrt mit
`ACT_SHAPE_CHROMA_SPLIT=0` weiter.

`STATE_SCHEMA` wurde **bewusst NICHT** hochgezaehlt. Die [Invariante](/mechanismen/invarianten.md)
gilt fuer STRUKTURaenderungen (Dimensionen, Felder); hier aendert sich die Verteilung der Eingaben,
nicht ihre Form. Hochzaehlen wuerde den 1053-Episoden-Zustand verwerfen und neu trainieren - das
waere ein weit groesserer Eingriff als der Schnitt selbst.

# Rueckholbarkeit

Eine Zeile: `ACT_SHAPE_CHROMA_SPLIT=0`. Der Zustand wird durch den Schnitt nicht umgeschrieben -
nur das, was der Agent von jetzt an dazulernt, entsteht unter der neuen Segmentierung.

# Verwandt

* [Frisch bei null](/befunde/chroma-split-frisch.md) - die Messung, auf der das beruht
* [Die Verschmelzung an der Quelle](/befunde/verschmelzung-chroma-split.md) - Bau und erster Lauf
* [Jeder grobe Adressfehler sitzt im obersten Band](/befunde/adressfehler-sind-verschmelzung.md)
* [Invarianten](/mechanismen/invarianten.md) - warum `STATE_SCHEMA` hier nicht hochgezaehlt wird
* [Die verdreifachte Geburtenrate ist reines Phantom](/befunde/geburtenrate-chroma-phantome.md) - der Vorbehalt
* [Ziel](/ziel.md) - der Massstab, nach dem hier entschieden wurde
