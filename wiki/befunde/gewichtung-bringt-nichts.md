---
type: Befund
title: Keine Hoehergewichtung ueber weight bringt etwas - und die Gegenprobe widerlegt meine Erklaerung des Augmentierungs-Befundes
description: Fuenf Gewichtungsschemata gegen den Bezug, je drei Seeds, auf demselben reinen Halteteil. Das beste liegt bei +0,004 AUC und damit in der Streuung des Bezugs selbst; Klassen-Umgewichtung schadet in BEIDEN Richtungen etwa gleich viel. Die wichtigste Zahl ist eine Gegenprobe: dieselbe Fuenffachgewichtung, die als Duplikat -0,051 kostete, kostet ueber weight nur -0,003 - meine Deutung des Augmentierungs-Verlusts als Umgewichtung ist damit falsch.
tags: [act23, weltmodell, puffer, negativ]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-15T00:00:00Z }
sources:
  - id: offline
    resource: "Offline auf einer Kopie von act23_state.pkl (12322 Weltzeilen): Training 0..10322, Luecke 1500, reiner Halteteil aus den letzten 500 echten Zeilen; 3 Seeds je Schema"
    title: Gewichtungsschemata
  - id: anlass
    resource: /befunde/augmentierung-wirkt-wie-wiederholung.md
    title: Der Befund, dessen Schlusssatz das hier geprueft hat
---

# Der Anlass

[Die Augmentierung wirkt wie eine Zeilenwiederholung](/befunde/augmentierung-wirkt-wie-wiederholung.md)
endete mit: *"Billiger zu haben waere dieselbe Wirkung ueber `weight` bei `observe` - eine Zahl
statt eines Mechanismus."* Das ist hier geprueft.

`weight` geht als echtes Stichprobengewicht in `member.fit`. **Gleichfoermige Gewichte werden in
`train()` uebersprungen** (`w=(W[idx] if not np.allclose(W, 1.0) else None)`) - nur die RELATIVE
Verteilung zaehlt, eine globale Skalierung ist wirkungslos.

# Zahlen

    Schema                 AUC Median     Delta    Einzelwerte (3 Seeds)
    wie gespeichert           0,7376    +0,0000    0,7376  0,7415  0,7346
    juengste 2000 nur         0,7419    +0,0043    0,7453  0,7385           (n=2)
    neuere schwerer           0,7388    +0,0012    0,7388  0,7404  0,7310
    NB-Zeilen 5x              0,7345    -0,0031    0,7345  0,7392  0,7304
    Fehlschlaege 3x           0,7273    -0,0103    0,7273  0,7279  0,7193
    Erfolge 3x                0,7239    -0,0137    0,7239  0,7283  0,7210

**Keines hilft.** Der Bezug streut ueber drei Seeds selbst um 0,007 (0,7346 bis 0,7415) - der
beste Kandidat liegt mit +0,0043 innerhalb dieser Streuung.

# Die Kontrolle war noetig und hat getragen

`Fehlschlaege 3x` kostet -0,0103, `Erfolge 3x` kostet -0,0137. **Beide Richtungen schaden, etwa
gleich viel.** Gemessen wird also nicht "die falsifizierende Klasse zaehlt mehr", sondern nur, dass
eine Stoerung des Klassenverhaeltnisses schadet. Ohne die Gegenrichtung haette der Wert von
`Fehlschlaege 3x` als schwacher Beleg fuer das Gegenteil gelesen werden koennen.

Nebenbei korrigiert das eine Annahme: der Puffer ist mit **5690 Erfolgen gegen 4632 Fehlschlaege**
weit ausgewogener, als das 1053-Episoden-Protokoll vermuten liess (550 gegen 288). Ein
Klassenungleichgewicht gibt es hier nicht zu reparieren.

# Die Gegenprobe widerlegt meine eigene Erklaerung

Im vorigen Befund kostete die Augmentierung -0,051, und ich deutete das als **Umgewichtung**: nur
690 der 10322 Zeilen sind augmentierbar, als Duplikate zaehlen sie danach fuenffach.

    dieselben 690 Zeilen, fuenffach als DUPLIKAT     -0,051
    dieselben 690 Zeilen, fuenffach ueber `weight`   -0,003

**Um mehr als eine Groessenordnung daneben.** Waere die Umgewichtung die Ursache, muesste sie sich
ueber `weight` reproduzieren lassen. Meine Deutung ist damit falsch.

> Was stehen bleibt, ist der KERNBEFUND des vorigen Tages - *vorgestellt ist von wiederholt nicht
> zu unterscheiden* (+0,0006) -, denn das ist ein direkter Vergleich zweier Varianten und von
> dieser Deutung unabhaengig. Widerlegt ist nur meine Erklaerung des VORZEICHENS.

**Was die -0,051 verursacht, ist damit offen.** Duplikat und Gewicht sind in dieser Umsetzung nicht
dasselbe: ein Duplikat aendert die Zeilenzahl und damit den Bootstrap-Zug (`_block_resample`) und
die Stichprobenzahl je Epoche, waehrend `weight` nur den Verlustbeitrag bei unveraendertem Zug
aendert. Welcher der beiden Unterschiede die Zahl traegt, ist **nicht gemessen** - und ich schreibe
das als offene Frage hin, nicht als zweite Erklaerung.

# Ein Faden, kein Befund

`juengste 2000 nur` (alles Aeltere auf Gewicht 0,1) ist der einzige Kandidat mit positivem
Vorzeichen (+0,0043, n=2).

> **GEZOGEN UND GEKIPPT (2026-09-15).** Mit 6 Seeds und vier Schnitten sah es zunaechst nach einem
> klaren Fund aus - +0,0115 gepaart bei 6/6 Seeds, mit sauberer Dosis-Wirkungs-Kurve. Bei einer
> Luecke von 4000 statt 1500 **kehrt sich dasselbe Schema um** (-0,0094, 0/4). Der Gewinn war
> NAEHE zum Halteteil, nicht Aktualitaet.
> Siehe [Alte Pufferzeilen abwerten](/befunde/alte-zeilen-abwerten.md).

# Fallen

* **`ebene: pruefstand`**, stehender Puffer, ein Halteteil. Kein geschlossener Kreis.
* **Drei Seeds**, und der Bezug streut selbst um 0,007. Unterschiede unter etwa 0,01 sind hier
  nicht lesbar - was die beiden Klassenschemata gerade noch ueberschreiten.
* **`juengste 2000 nur` hat nur zwei Seeds** (der dritte Durchgang wurde wegen Systemspeicher
  abgeraeumt). Deshalb steht es als Faden und nicht in der Bewertung.

# Folgen

Keine Aenderung. `weight` bleibt, wie es ist. Der Schlusssatz des vorigen Befundes -
*"billiger ueber `weight`"* - ist damit ebenfalls erledigt: es ist zwar billiger, bringt aber
genauso wenig.

# Verwandt

* [Die Augmentierung wirkt wie eine Zeilenwiederholung](/befunde/augmentierung-wirkt-wie-wiederholung.md) - der Anlass, dessen Deutung hier widerlegt wird
* [Der Nachbar-Block steht auf 6 Prozent der Zeilen](/befunde/merkmale-kommen-zu-spaet.md)
* [Alte Pufferzeilen abwerten](/befunde/alte-zeilen-abwerten.md) - der Faden, gezogen und gekippt
* [Guetebewusste Verdraengung](/befunde/imitationspuffer.md) - der aeltere Anlauf, Pufferzeilen nach Guete zu behandeln
