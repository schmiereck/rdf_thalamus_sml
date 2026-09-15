---
type: Befund
title: Alte Pufferzeilen abzuwerten kauft NAEHE und kostet VERALLGEMEINERUNG - der Gewinn kehrt sich um, sobald die Luecke waechst
description: Mit Luecke 1500 sieht es nach einem klaren Fund aus: die aeltesten Zeilen auf Gewicht 0,1, und die AUC steigt um 0,0115, bei 6 von 6 Seeds, mit sauberer Dosis-Wirkungs-Kurve. Mit Luecke 4000 kehrt sich dasselbe Schema um (-0,0094, 0 von 4 Seeds). Der Gewinn war NAEHE zum Halteteil, nicht Aktualitaet. Loeschen statt Abwerten kostet dagegen 0,04 bis 0,05 - die alten Zeilen tragen echte Information, sie sind nur ueberrepraesentiert.
tags: [act23, weltmodell, puffer, methodik, negativ]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-15T00:00:00Z }
sources:
  - id: luecke1500
    resource: "Offline auf einer Kopie von act23_state.pkl: Training 0..10322, Luecke 1500, Halteteil letzte 500 echte Zeilen, 7 Schemata x 6 Seeds, gepaart ausgewertet"
    title: Der Faden, mit Luecke 1500
  - id: luecke4000
    resource: "Dieselben Schemata mit Luecke 4000 (Training 0..7822), 4 Seeds"
    title: Die Kontrolle, mit Luecke 4000
---

# Der Faden

Aus [Keine Hoehergewichtung bringt etwas](/befunde/gewichtung-bringt-nichts.md) blieb ein einziger
Kandidat mit positivem Vorzeichen uebrig: alte Pufferzeilen abwerten. Dort mit zwei Seeds und
innerhalb der Streuung - also ein Faden, kein Befund. Hier gezogen: vier Schnitte, sechs Seeds,
gepaart ausgewertet (derselbe Seed, derselbe Bootstrap-Start).

# Mit Luecke 1500 sieht es ueberzeugend aus

    Bezug ueber 6 Seeds: Median 0,7361, Spanne 0,0110

    Schema                Zeilen   Median    Delta   gepaart  besser
    alt 0,1 ab 1000        10322   0,7453  +0,0092  +0,0075   6/6
    alt 0,1 ab 2000        10322   0,7501  +0,0141  +0,0115   6/6
    alt 0,1 ab 4000        10322   0,7448  +0,0087  +0,0043   4/6
    alt 0,1 ab 8000        10322   0,7387  +0,0026  -0,0019   2/6
    hart 2000 (Rest weg)    2000   0,6965  -0,0396  -0,0405   0/6
    hart 4000 (Rest weg)    4000   0,6870  -0,0491  -0,0471   0/6

Anstieg, Maximum bei 2000, Rueckkehr zur Null bei 8000 - `ab 8000` ist die eingebaute Kontrolle,
denn dort unterscheidet sich das Schema kaum noch vom Bezug, und prompt bewirkt es nichts. Eine
Dosis-Wirkungs-Kurve ist deutlich mehr wert als ein einzelner Punkt.

**Abwerten hilft, Loeschen ruiniert** (-0,04 bis -0,05, 0 von 6). Die alten Zeilen tragen also
echte Information; sie sind nur ueberrepraesentiert. Auch das klang stimmig.

# Mit Luecke 4000 kehrt es sich um

    Luecke 1500   Bezug 0,7361 | ab 1000 +0,0075 (6/6) | ab 2000 +0,0115 (6/6)
    Luecke 4000   Bezug 0,7092 | ab 1000 -0,0054 (0/4) | ab 2000 -0,0094 (0/4)

**Dasselbe Schema, entgegengesetztes Vorzeichen, und in beiden Faellen einstimmig ueber die Seeds.**

Der Grund steht im Docstring von `generalisation_auc` selbst: die AUC faellt mit der Luecke
(0 -> 0,860 | 1500 -> 0,746 | 3000 -> 0,656), weil benachbarte Zeilen aus derselben stehenden Szene
stammen. Die "juengsten" Trainingszeilen sind zugleich die dem Halteteil **naechsten**. Sie
hoeherzugewichten verbessert die Vorhersage von allem, was in ihrer Naehe liegt - und verschlechtert
sie, sobald der Halteteil weit genug weg ist.

> **Alte Zeilen abzuwerten kauft NAEHE und kostet VERALLGEMEINERUNG.** Das ist keine Aussage
> ueber das Alter der Daten, sondern ueber den Abstand zum Ziel.

# Was das wert ist, und was nicht

* **Als Befund ueber Datenalter: nichts.** Es gibt keinen Beleg, dass alte Pufferzeilen veralten.
  Der Loesch-Versuch sagt sogar das Gegenteil - ohne sie bricht die AUC um 0,05 ein.
* **Als Betriebsgroesse: nicht ganz nichts.** Zur Laufzeit sagt das Modell immer *jetzt* vorher,
  und "nah" heisst dort "gerade eben". Wer nur die naechste Episode treffen will, gewinnt
  tatsaechlich etwas. Aber das ist lokale Anpassung, nicht Lernen - und
  [das Projektziel](/ziel.md) misst Aneignung, nicht Tagesform.
* **Methodisch ist es der Ertrag des Tages.** Ein Gewinn mit sauberer Dosis-Wirkungs-Kurve und
  6/6 Seeds war ueberzeugend genug, dass ich ihn ohne die Luecken-Kontrolle aufgeschrieben haette.
  Genau diese Kontrolle hat ihn gekippt.

# Die Lehre, verallgemeinert

`generalisation_auc` hat den Luecken-Parameter, weil die Naehe schon einmal als Verallgemeinerung
missverstanden wurde (*"Die 0,86 waren nie die Verallgemeinerung, sondern die Naehe"*). Der
Parameter schuetzt aber nur, wenn man ihn **variiert**. Bei EINER festen Luecke ist jedes Schema,
das die Naehe betont, ununterscheidbar von einem, das die Verallgemeinerung verbessert.

> **Ein Schema, das Trainingszeilen nach ihrer POSITION im Puffer gewichtet, muss immer gegen
> mindestens zwei Luecken geprueft werden.** Sonst misst man den Abstand und nennt ihn Guete.

# Fallen

* **`ebene: pruefstand`**, stehender Puffer.
* **4 Seeds bei Luecke 4000** gegen 6 bei 1500. Das Vorzeichen ist in beiden Faellen einstimmig,
  die Betraege sind es nicht.
* **Der Bezug faellt mit der Luecke** (0,7361 -> 0,7092), wie erwartet. Verglichen werden deshalb
  nur die gepaarten Differenzen, nicht die Niveaus.
* **Nicht geprueft**, ob es einen Gewichtungsverlauf gibt, der bei BEIDEN Luecken hilft - etwa ein
  sanfter Abfall statt einer harten Stufe. Der Befund schliesst das nicht aus, er widerlegt nur
  die Stufe.

# Verwandt

* [Keine Hoehergewichtung bringt etwas](/befunde/gewichtung-bringt-nichts.md) - wo der Faden herkam
* [Die Augmentierung wirkt wie eine Zeilenwiederholung](/befunde/augmentierung-wirkt-wie-wiederholung.md)
* [Messhygiene in CLAUDE.md](/mechanismen/invarianten.md) - "Halteteile nie zufaellig ziehen"
