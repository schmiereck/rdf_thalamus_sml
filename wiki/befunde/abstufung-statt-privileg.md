---
type: Befund
title: Abstufung statt Privileg - gebaut, gemessen, und sie hat keine unprivilegierte Sicherung
description: Bei "kein Treffer" die Groessenachse fallen zu lassen statt zu privilegieren funktioniert technisch, greift aber selten (3 von 6 Gelegenheiten in 150 Episoden) und einer der drei Faelle adressierte einen fremden Wuerfel 65 mm daneben. Die vorgesehene Sicherung "nur bei genau einem Treffer uebernehmen" ist wirkungslos: beide Fassungen sind bitgleich, weil der mehrdeutige Fall genau einen Treffer meldet. Eindeutigkeit ist nicht Richtigkeit - zum dritten Mal.
tags: [act23, kommando, privilegien, negativ, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-13T00:00:00Z }
sources:
  - id: ab
    resource: "Drei kopflose Steuerungslaeufe je 150 Episoden aus derselben Kopie von act23_state.pkl (ad9d768c), ACT23_GROESSE_SPANNE=1 ACT23_EIG_IDENT=1, ACT23_EIG_ABSTUFUNG 0/1/2, gleichzeitig gefahren"
    title: Abstufungs-A/B, drei Arme
---

# Der Auftrag

Aus dem [Rasterbefund](/befunde/spannen-raster-7mm.md): der Preis der Groessenachse ist der
**privilegierte Rueckfall** (10,0 statt 4,7 % der Episoden), und ein groeberes Raster senkt ihn
nicht. Der vorgeschlagene Ausweg, hier gebaut: bei "kein Treffer" **die Groessenachse fallen
lassen** und mit `(Farbe, Form, beliebig)` erneut suchen, statt auf die wahre Lage aus dem
Simulator zu greifen. Die Adresse wird unschaerfer, bleibt aber eine **Wahrnehmung**.

Zwei Fassungen, weil ohne die Groessenachse mehrere Detektionen passen koennen:

    ACT23_EIG_ABSTUFUNG=1   fallen lassen, besten Treffer nehmen (groesste Flaeche)
    ACT23_EIG_ABSTUFUNG=2   fallen lassen, nur uebernehmen wenn genau EINER uebrig bleibt

# Zahlen

    Arm         Ep   Quote | Adr.Median   grobe Fehler >20mm | Rueckfall | Abstufungen
    ab_aus     150  66,0 % |   3,2 mm       5/159 =  3,1 %   |    15     |      0
    ab_best    150  54,7 % |   3,2 mm      23/175 = 13,1 %   |    11     |      3
    ab_eind    150  54,7 % |   3,2 mm      23/175 = 13,1 %   |    11     |      3

`ab_aus` reproduziert `g7_beide` und `r7_fein` **zifferngenau** (66,0 %, 5/159, 15 Rueckfaelle) -
der Einbau hat den Vorgabepfad nachweislich nicht angefasst.

# Die Sicherung existiert nicht

**`ab_best` und `ab_eind` sind bitgleich.** Alle drei Abstufungen meldeten `1 Treffer`, also hat
die Eindeutigkeitspruefung kein einziges Mal etwas abgefangen. Sie kann es auch nicht:

    Ep 14  obj_blue   Band 'mittelklein' weg -> (farbe-2, cube, beliebig)   15,3 mm   1 Treffer
    Ep 84  obj_green  Band 'winzig'      weg -> (None,    cube, beliebig)   65,0 mm   1 Treffer
    Ep 84  (dieselbe Episode, Wiederholung der Zeile)

Der Fall bei Ep 84 ist der Lehrfall. Das Tripel hatte **keine Farbachse**, nur `cube` - und im
Bild liegen drei Wuerfel. Nach dem Fallenlassen der Groesse heisst die Adresse "irgendein Wuerfel".
Dass sie trotzdem `1 Treffer` meldet, liegt daran, dass die anderen beiden Wuerfel in diesem Bild
gar nicht als eigene Detektion ankamen. **Die Mehrdeutigkeit ist unsichtbar, und deshalb schuetzt
kein Zaehlen davor.**

> Das ist woertlich derselbe Mechanismus wie im
> [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) (*Eindeutigkeit ist nicht
> Richtigkeit*) und im [sechsten Anlauf](/befunde/relrings-split-zielkonflikt.md). Zum dritten Mal,
> und diesmal mit der Folgerung, die vorher fehlte: **beim Schreiben einer Adresse laesst sich das
> mit der Identitaetspruefung loesen, beim LESEN nicht.** Die Identitaetspruefung vergleicht gegen
> die wahre Lage - als Buchfuehrung der Wuerfelei ist das vertretbar, im Wahrnehmungspfad waere es
> genau das Privileg, das die Abstufung abschaffen soll.

# Was die Abstufung erreichen kann, und was nicht

Die Obergrenze ist klein. Von den 15 Rueckfaellen in `ab_aus` tragen ueberhaupt nur 11 ein
Groessenband; die uebrigen 4 scheitern an einer Farb- oder Formklasse, die im Bild nicht vorkommt -
dort gibt es nichts abzustufen. Im abgestuften Arm selbst standen 6 Gelegenheiten, 3 wurden
genutzt, 3 scheiterten auch ohne Band (`farbe-15`, `farbe-6` - Farbklassen, die es nicht mehr gab).

**Der Rueckfall faellt entsprechend nur von 15 auf 11** (p = 0,54). Das Privileg wird nicht
abgeschafft, es wird leicht seltener.

# Die grossen Zahlen sind Abdrift, nicht Wirkung

Grobe Fehler 3,1 -> 13,1 % (p = 0,0012) und Quote 66,0 -> 54,7 % (p = 0,06) sehen dramatisch aus.
**Nur 2 der 23 groben Fehler sind Abstufungen.** Die uebrigen 21 stammen aus dem normalen Pfad -
der Lauf ist nach dem ersten Eingriff bei Ep 14 ein anderer Lauf
([Laeufe sind reproduzierbar](/befunde/laeufe-sind-reproduzierbar.md): eine Stoerung aendert alles
Folgende).

Was die Abdrift trifft, ist dafuer sehr scharf lokalisiert und in **beiden** Armen dasselbe: alle
groben Fehler sitzen im Band `riesig`, getragen von der verschmelzungsgeborenen Klasse `neu-13`.
Das ist der eigentliche Ertrag dieses Laufs und steht eigens in
[Jeder grobe Adressfehler sitzt im obersten Band](/befunde/adressfehler-sind-verschmelzung.md).

# Bewertung

* **Die Idee bleibt richtig und ist es wert, gebaut zu sein** - eine unschaerfere Adresse ist
  besser als ein Griff in den Simulator, und der Schalter steht fuer den Tag bereit, an dem die
  Verschmelzung geloest ist.
* **Heute traegt sie nicht.** Zu selten wirksam, ohne Sicherung, und ihr einziger klar
  beobachtbarer Fehlfall (Ep 84) griff einen fremden Koerper.
* **Der Befund ist ein Wegweiser, kein Endpunkt.** Er sagt, dass der Rueckfall nicht ueber die
  Groessenachse zu beheben ist - die 4 von 15 ohne Band und die 3 an fehlenden Farbklassen zeigen,
  dass der Rueckfall drei verschiedene Ursachen hat und "Achse fallen lassen" nur eine davon trifft.

# Folgen

`ACT23_EIG_ABSTUFUNG` bleibt auf `0`. Der Schalter und beide Fassungen bleiben im Code samt dieser
Begruendung.

Vorrang hat jetzt die Verschmelzung: der Form-Split existiert bereits auf dem FORM-Pfad und fehlt
dem Eigenschafts-Pfad ([Details](/befunde/adressfehler-sind-verschmelzung.md)).

# Verwandt

* [Jeder grobe Adressfehler sitzt im obersten Band](/befunde/adressfehler-sind-verschmelzung.md) - der eigentliche Ertrag
* [Das groebere 7-mm-Raster](/befunde/spannen-raster-7mm.md) - woher der Auftrag kam
* [Die Groessenachse mass die falsche Groesse](/befunde/groessenachse-spanne.md) - der Rueckfall-Preis
* [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) - "Eindeutigkeit ist nicht Richtigkeit"
