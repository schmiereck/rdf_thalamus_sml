---
type: Befund
title: Kein Gewichtungsverlauf hilft bei beiden Luecken - und die Nullkontrolle zeigt, dass die VORHANDENE Daempfung etwas wert ist
description: Vier Abklingzeiten plus die harte Stufe, gegen Luecke 1500 und 4000, je fuenf Seeds gepaart. Jedes Schema, das nah hilft, schadet fern - es gibt kein tau, das beide Seiten hebt. Die Nullkontrolle war dabei nicht null: sie ersetzt die GESPEICHERTEN Gewichte durch gleichfoermige und kostet 0,0108, womit die vorhandene Daempfung von 946 unsicher zugeordneten Zeilen auf 0,3 erstmals beziffert ist. Damit sind alle Deltas des Vorbefundes gegen einen Bezug gemessen, der selbst schon gewichtet.
tags: [act23, weltmodell, puffer, methodik, negativ]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-15T00:00:00Z }
sources:
  - id: beide
    resource: "Offline auf einer Kopie von act23_state.pkl: 7 Schemata x 2 Luecken (1500 und 4000) x 5 Seeds, gepaart gegen den Bezug desselben Seeds, reiner Halteteil aus 500 echten Zeilen"
    title: Sanfter Abfall gegen beide Luecken
  - id: vorher
    resource: /befunde/alte-zeilen-abwerten.md
    title: Der Befund, dessen offene Frage hier beantwortet wird
---

# Die Frage

[Alte Pufferzeilen abwerten](/befunde/alte-zeilen-abwerten.md) liess offen, *"ob es einen
Gewichtungsverlauf gibt, der bei BEIDEN Luecken hilft - etwa ein sanfter Abfall statt einer harten
Stufe."* Gewicht = `0,1 + 0,9 * exp(-Alter/tau)`, vier Abklingzeiten, dazu die Stufe als
Bezugspunkt und eine Umkehrung als Gegenprobe.

# Zahlen

    Schema                 Luecke 1500            Luecke 4000
                        gepaart  besser        gepaart  besser
    Bezug              Median 0,7376          Median 0,7091
    Stufe ab 2000        +0,0156   5/5          -0,0070   0/5
    sanft tau=1000       +0,0089   5/5          -0,0049   1/5
    sanft tau=2500       +0,0056   5/5          -0,0042   1/5
    sanft tau=5000       -0,0016   1/5          -0,0030   1/5
    sanft tau=20000      -0,0108   0/5          -0,0013   0/5
    UMGEKEHRT tau=2500   -0,0221   0/5          -0,0031   0/5

**Kein tau hilft bei beiden Luecken.** Je schaerfer der Abfall, desto groesser der Gewinn nah und
der Verlust fern; je flacher, desto mehr verschwindet beides. Die Antwort auf die offene Frage ist
nein - die harte Stufe war nicht das Problem, die Positionsgewichtung selbst ist es.

# Die Nullkontrolle war nicht null, und das ist der Ertrag

`tau=20000` sollte bei 10322 Zeilen praktisch flach sein und folglich nichts bewirken. Sie kostet
**-0,0108** bei Luecke 1500, einstimmig ueber alle Seeds.

Der Grund ist ein Fehler in meinem Aufbau: der **Bezug benutzt die GESPEICHERTEN Gewichte**, und
die sind nicht gleichfoermig.

    gespeicherte Gewichte im Trainingsteil
      0,300   946 Zeilen =  9,2 %     <- gedaempfte, unsicher zugeordnete Ausgaenge (fail_w)
      1,000  9376 Zeilen = 90,8 %

Ein flaches Schema ersetzt sie durch gleichfoermige. Gemessen wird damit nicht "nichts", sondern
**"gespeicherte Gewichte gegen gleichfoermige"** - und die Antwort lautet: die gespeicherte
Daempfung ist **+0,0108 AUC wert**.

> Das ist die erste Bezifferung der vorhandenen `fail_w`-Daempfung, und sie faellt als Nebenprodukt
> einer Kontrolle an, die etwas ganz anderes pruefen sollte.

**Folge fuer die Deltas:** jedes Schema ersetzt die gespeicherten Gewichte, also enthaelt jedes
Delta zwei Anteile - die eigene Wirkung und den Verlust der gespeicherten. Gegen GLEICHFOERMIG
gerechnet stuenden die nahen Werte besser da (Stufe +0,0264 statt +0,0156), an der Kernaussage
aendert das nichts: bei Luecke 4000 bleiben alle Schemata unter null, auch gegen gleichfoermig.

Dasselbe gilt fuer die gespeicherte Daempfung selbst: +0,0108 nah, aber nur +0,0013 fern. **Auch
sie ist ueberwiegend ein Nahfeld-Effekt.**

# Die Gegenprobe ist nur eine halbe Spiegelung

Erwartet war: ist der Gewinn nah reine Naehe, muss die Umkehrung nah SCHADEN und fern NUETZEN.

    UMGEKEHRT   nah -0,0221 (0/5)      fern -0,0031 (0/5)

Die erste Haelfte trifft, und deutlich - die Umkehrung ist das schaedlichste Schema von allen. Die
zweite trifft **nicht**: fern nuetzt sie ebenfalls nichts.

Bei Luecke 4000 schadet jede Abweichung vom Bezug leicht, auch die fast flache. Entweder ist der
Bezug dort schon nahe am Besten, oder die Messung traegt bei dieser Luecke zu wenig Signal. **Die
Naehe-Deutung erklaert die nahe Seite gut und die ferne gar nicht** - und ich schreibe das so hin,
statt die halbe Spiegelung als ganze zu verkaufen.

# Folgen

Der Faden ist zu. **Positionsgewichtung im Puffer ist erledigt** - Stufe wie Verlauf, in beide
Richtungen. Was bleibt, ist ein neuer, ungeprueffter Faden aus der Nullkontrolle: die vorhandene
`fail_w`-Daempfung wirkt, und ihre Hoehe (0,3) ist nie kalibriert worden.

# Fallen

* **`ebene: pruefstand`**, stehender Puffer, ein Halteteil je Luecke.
* **Fuenf Seeds je Zelle**, gepaart ausgewertet. Die Vorzeichen sind fast ueberall einstimmig, die
  Betraege streuen.
* **Der Bezug enthaelt schon eine Gewichtung.** Das war mir beim Entwurf nicht bewusst; ein
  sauberer Aufbau haette GLEICHFOERMIG als dritte Bezugsgroesse mitgefuehrt. Die Kernaussage
  ueberlebt, die Einzelbetraege sind gegen den operativen Bezug zu lesen, nicht gegen null.
* **Nicht geprueft**, ob eine Gewichtung nach etwas anderem als der Position hilft - Guete,
  Neuheit, Zuordnungssicherheit. Nur die letzte existiert heute, und sie wirkt.

# Verwandt

* [Alte Pufferzeilen abwerten](/befunde/alte-zeilen-abwerten.md) - die offene Frage, hier beantwortet
* [Keine Hoehergewichtung bringt etwas](/befunde/gewichtung-bringt-nichts.md) - die Reihe davor
* [Guetebewusste Verdraengung](/befunde/imitationspuffer.md) - der aeltere Anlauf in derselben Richtung
