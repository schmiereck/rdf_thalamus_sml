---
type: Befund
title: Frisch bei null kehren sich beide Vorbefunde um - und die Wiedervorlage der Laufszenen erklaert, warum kein Armvergleich das entscheiden kann
description: Der frische Vergleich widerlegt den Quotenverlust (17,0 gegen 13,0 Prozent zugunsten des Schnitts), kehrt aber auch den Adressierungsgewinn um (3,0 gegen 0,7 Prozent). Beide Arme sind ungleich weit - 12 gegen 4 geborene Klassen. Die Wahrnehmung auf den SZENEN DES LAUFS gemessen ist dagegen eindeutig: der Schnitt beseitigt jede verfehlte Detektion (20 von 1024 auf 0, p = 2e-06) und kostet 0,5 mm Median. Und er zeigt, dass Verschmelzung im Lauf ein 2-Prozent-Phaenomen ist, nicht das 29-Prozent-Phaenomen meiner Handsonde.
tags: [act23, wahrnehmung, verschmelzung, methodik, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-14T00:00:00Z }
sources:
  - id: frisch
    resource: "Zwei kopflose Steuerungslaeufe je 300 Episoden, ACT23_FRESH=1 (beide bei null), ACT_SHAPE_CHROMA_SPLIT 0 gegen 1 bei TRENNUNG 1,0, gleichzeitig gefahren"
    title: Chroma-Split frisch bei null
  - id: wiedervorlage
    resource: "270 Szenen aus den Protokollen beider Arme nachgestellt ([dbg] after ep), 1024 Koerper, beide Segmentierungen auf denselben Lagen"
    title: Wiedervorlage der Laufszenen
---

# Der Anlass

[Die Verschmelzung an der Quelle](/befunde/verschmelzung-chroma-split.md) hatte einen benannten
Aufbaufehler: beide Chroma-Arme liefen auf einem Zustand, dessen Formklassen aus **ungeteilten**
Komponenten gelernt sind. Der Quotenverlust dort konnte ein Artefakt davon sein. Dieser Lauf
wiederholt den Vergleich so, wie es das [Relrings-A/B](/befunde/relrings-im-lauf.md) vorgemacht
hat: **beide Arme bei null**, jeder lernt seine Klassen unter seinem eigenen Schnitt.

# Beide Vorbefunde kehren sich um

    Arm         Ep   Quote | Adr.Median  grobe Fehler >20mm | Rueckfall | Geburten verhungert
    fr_fest    300  13,0 % |   2,2 mm       2/306 =  0,7 %  |    13     |     4        2
    fr_chroma  300  17,0 % |   3,6 mm       9/305 =  3,0 %  |    26     |    12        9

    chroma gegen fest   Quote p = 0,21   grobe Fehler p = 0,037   Rueckfall p = 0,046

    Quote je 100 Episoden    fest     6 % | 17 % | 16 %
                             chroma   2 % | 20 % | 29 %

* **Der Quotenverlust reproduziert NICHT.** Der Chroma-Arm liegt vorn und steigt im letzten Block
  noch steil (29 %), waehrend der feste abgeflacht ist (16 %). Das stuetzt die Vermutung, dass der
  Verlust im vorigen Lauf am veralteten Exemplarbestand lag.
* **Der Adressierungsgewinn reproduziert auch nicht - er kehrt sich um** (3,0 gegen 0,7 %,
  p = 0,037), und der Rueckfall ebenso (26 gegen 13, p = 0,046).

# Warum auch dieser Aufbau nicht entscheidet

Die Arme sind **nicht gleich weit**:

    geborene Klassen    fest  4  (2 verhungert, 2 ueberlebt)
                        chroma 12 (9 verhungert, 3 ueberlebt)

Der Chroma-Arm eignet sich dreimal so viel an - und adressiert entsprechend viele **junge,
unkonsolidierte** Klassen. Grobe Adressfehler messen in einem frischen Lauf deshalb mit, **wie
viel der Agent sich zutraut**, nicht nur, wie gut er wahrnimmt. Im geladenen Zustand gab es dieses
Problem nicht, dort war der Klassenbestand fest und reif.

> **Fuer eine geaenderte Wahrnehmung ist WEDER der geladene NOCH der frische Aufbau sauber.** Der
> geladene traegt gelernten Bestand, der zur neuen Wahrnehmung nicht passt; der frische erzeugt
> auseinanderlaufende Lernverlaeufe. Das ist neu und gehoert neben die
> [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md).

Nebenbefund gegen die Erwartung: die Groessen-Invarianz-Linie sagte, ein besserer Schnitt muesse
die **Geburtenrate senken** (weniger Uebersegmentierung -> weniger Phantomklassen). Er **verdreifacht**
sie. Der Schnitt erzeugt mehr, kleinere, variantenreichere Teile - also mehr neuartige
Deskriptoren. Drei von zwoelf ueberleben gegen zwei von vier.

# Die Messung, die entscheidet - und die ich zuerst haette machen sollen

Die Protokolle enthalten je Episode die wahren Lagen aller sieben Koerper (`[dbg] after ep`).
Damit lassen sich **die Szenen des Laufs nachstellen** und beide Segmentierungen auf denselben
Lagen befragen. Gemessen wird rein raeumlich - Abstand jedes Koerpers zur naechsten Detektion -,
also ohne Klassen, ohne Adressen, ohne gelernten Bestand.

    270 Szenen aus beiden Protokollen, 1024 Koerper, im Median 4 Koerper je Szene

                  Median   75 %    90 %   verfehlt (>20 mm)   Detektionen je Szene
      fest        1,3 mm   4,9     6,8          2,0 %                4,0
      Chroma      1,8 mm   4,9     6,5          0,0 %                4,0

      verfehlte Koerper   20/1024 gegen 0/1024    Fisher p = 2e-06

**Der Schnitt beseitigt jede verfehlte Detektion** und kostet 0,5 mm Median. Die Zahl der
Detektionen bleibt bei 4 fuer 4 Koerper - er zerschneidet keine Einzelkoerper, die raeumliche
Schranke haelt.

# Und das erklaert die ganze Serie

    Verschmelzung, verfehlte Koerper
      meine Handsonde, 5 Koerper eng gestellt        29,0 %
      die tatsaechlichen Szenen des Laufs             2,0 %
      -> die Handsonde ueberzeichnet um Faktor 15

**Im Lauf ist Verschmelzung ein Zwei-Prozent-Phaenomen.** Damit ist rueckblickend klar, warum
sieben Armvergleiche nacheinander uneindeutig blieben: eine Wirkung, die 2 % der Wahrnehmungen
betrifft, ist bei 150 bis 300 Episoden nicht aufzuloesen - die
[Nachweisgrenze](/befunde/rechnerlast.md) liegt weit darueber.

Das widerspricht dem Befund [Jeder grobe Adressfehler sitzt im obersten
Band](/befunde/adressfehler-sind-verschmelzung.md) **nicht**: dort ging es um die Zusammensetzung
der Fehler (alle Fehler sind Verschmelzung), hier um ihre Haeufigkeit (Verschmelzung ist selten).
Beides zusammen heisst: **die Adressierung ist bereits fast fehlerfrei, und der Rest ist ein
seltenes Wahrnehmungsereignis.**

# Bewertung

* **Die Wahrnehmung ist besser, nachweisbar und mit sauberem Mass** (p = 2e-06, gleiche Szenen,
  keine Lernverlaeufe im Spiel). Das ist der erste eindeutige Beleg dieser ganzen Linie.
* **Die Wirkung auf den Lauf ist und bleibt unentscheidbar** bei dieser Laufdauer. Kein weiterer
  Armvergleich wird das aendern.
* **Die Kosten sind klein und benannt:** 0,5 mm Median, rund 4 % Rechenzeit, dreifache
  Geburtenrate mit hoher Sterblichkeit.

# Folgen

`ACT_SHAPE_CHROMA_SPLIT` auf `0` belassen oder einschalten ist jetzt eine **Entscheidung, keine
Messfrage**. Fuer das Einschalten spricht, dass die Wahrnehmung belegbar besser wird und das
Projektziel an der Wahrnehmung haengt, nicht an der Quote; dagegen sprechen 0,5 mm Median und
dass die Lieferquote es nie bestaetigen wird.

**Nicht mehr zu versuchen:** die Wirkung des Schnitts ueber die Lieferquote nachzuweisen.

# Fallen

* **Die Wiedervorlage stellt Lagen nach, keine Drehungen** - der Yaw steht nicht im Protokoll und
  wird neu gewuerfelt. Die Verschmelzung haengt ueberwiegend an den Lagen, aber nicht nur.
* **Ein Seed je Arm**, und im frischen Aufbau laufen die Arme staerker auseinander als im
  geladenen.
* **Die Wiedervorlage benutzt den geladenen Klassifikator** fuer `perceive_all`. Auf die
  Segmentierung wirkt das nur ueber das `resolve`-Tor des Erosions-Splits, und beide Seiten teilen
  es sich.

# Verwandt

* [Die Verschmelzung an der Quelle](/befunde/verschmelzung-chroma-split.md) - der Lauf mit dem Aufbaufehler
* [Jeder grobe Adressfehler sitzt im obersten Band](/befunde/adressfehler-sind-verschmelzung.md) - Zusammensetzung gegen Haeufigkeit
* [Relative Ringe im Lauf](/befunde/relrings-im-lauf.md) - der frische Aufbau, hier uebernommen
* [Die Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)
* [Rechnerlast](/befunde/rechnerlast.md) - die Nachweisgrenze
