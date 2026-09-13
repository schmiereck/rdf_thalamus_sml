---
type: Befund
title: Die pixelweise Farbbindung schliesst die Catch-22 vollstaendig - und es aendert nichts
description: Der zweite Bindungsdurchgang bindet 34 von 34 und 53 von 53 erreichbaren Koerpern, die der Komponenten-Durchgang wegen Verschmelzung ausgelassen hatte. Die Zielgroesse bewegt sich nicht (grobe Adressierungsfehler 3,1 auf 3,8 Prozent, p = 1,00), und der Eig-Split wird dadurch NICHT brauchbar (6,1 Prozent). Damit ist meine Erklaerung aus dem vorigen Lauf widerlegt: die fehlende Bindung war nicht der Grund, warum der Split scheiterte.
tags: [act23, wahrnehmung, verschmelzung, farbe, negativ, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-14T00:00:00Z }
sources:
  - id: ab
    resource: "Drei kopflose Steuerungslaeufe je 150 Episoden aus derselben Kopie von act23_state.pkl (ad9d768c), ACT23_GROESSE_SPANNE=1 ACT23_EIG_IDENT=1, ACT23_BINDUNG_SPLIT/ACT23_EIG_SPLIT 0/0, 1/0, 1/2"
    title: Bindungs-A/B, drei Arme
  - id: sonde
    resource: "25 dichte Szenen mit je 5 Koerpern auf einer Zustandskopie, Komponenten-Durchgang gegen Komponenten + Pixelschnitt"
    title: Deckung und Brauchbarkeit der Bindung
---

# Der Auftrag und die Abweichung davon

Bestellt war Weg 2 aus [dem vorigen Lauf](/befunde/eig-split-im-lauf.md): *"die Bindung
nachhalten, statt verschmolzene Blobs zu ueberspringen - wer verschmolzen war, bleibt an die
Klasse gebunden, die er in der letzten sauberen Episode trug."*

**Die zweite Haelfte des Satzes kann nicht funktionieren.** `_faerbe_neu` permutiert je Episode
alle sieben Farben unter den Koerpern ([Farb-Mischung](/befunde/farb-mischung.md)). Eine
uebernommene Klasse ist damit nicht veraltet, sondern **systematisch falsch** - der Koerper hat
inzwischen eine andere Farbe. Und es waere wieder die Tabelle, die `_farbbindung_neu` bewusst
abgeloest hat.

Gebaut wurde die erste Haelfte, mit der Wahrnehmung **derselben** Episode als Quelle: die
Mischchroma ist eine Eigenschaft des KOMPONENTENMITTELS, nicht des Bildes. Pixelweise gibt es
keine Mischung - jedes Pixel gehoert zu genau einer Klasse, auch wenn die Komponente zwei Koerper
enthaelt. `colour_parts_all` trennt alle Klassen in einem Rendern; der Zuordnungsschritt bleibt
unveraendert (Teil -> naechster Koerper, 40 mm, eine Klasse je Koerper).

# Der Mechanismus tut, wofuer er gebaut wurde - vollstaendig

    Arm        Bindung-Split feuerte   offen gemeldet   davon geparkt   erreichbar   gebunden
    bs_bind    in 31 von 150 Episoden       127              93             34          34
    bs_beide   in 53 von 150 Episoden       212             159             53          53

**34 von 34 und 53 von 53.** Die scheinbar magere Quote (34 von 127) ist ein Zaehlfehler in der
Meldung: `len(_offen)` enthaelt auch die **drei geparkten Koerper**, die in jeder Episode
ausserhalb des Bildes liegen und per Bauart nie gebunden werden koennen. Zieht man sie ab, bindet
der Pixelschnitt **jeden erreichbaren Koerper**, den der Komponenten-Durchgang ausgelassen hatte.

Am Pruefstand dasselbe Bild (25 dichte Szenen, je 5 Koerper):

    nur Komponenten   gebunden  79/125 = 63,2 %    brauchbar 50/79 = 63,3 %
    + Pixelschnitt    gebunden 121/125 = 96,8 %    brauchbar 82/121 = 67,8 %
    die 42 neuen Bindungen                         brauchbar 32/42 = 76,2 %

("brauchbar" = `perceive_colour` auf der gebundenen Klasse findet den Koerper auf 20 mm.) Die
neuen Bindungen sind **besser als die vorhandenen** - der Pixelschnitt greift dort, wo das
Komponentenmittel gar nichts liefern konnte.

# Und es aendert nichts

    Arm         Ep   Quote | Adr.Median  grobe Fehler >20mm | Rueckfall | Eig-Splits
    bs_aus     150  66,0 % |   3,2 mm       5/159 =  3,1 %  |    15     |     0
    bs_bind    150  64,0 % |   1,4 mm       6/160 =  3,8 %  |    19     |     0
    bs_beide   150  56,7 % |   7,3 mm      10/163 =  6,1 %  |    12     |   154

    gegen die Vorgabe   grobe Fehler   bind p = 1,00   beide p = 0,29
                        Rueckfall      bind p = 0,59   beide p = 0,69

`bs_aus` reproduziert zum fuenften Mal zifferngenau.

# Die Widerlegung meiner eigenen Erklaerung

Aus [dem vorigen Lauf](/befunde/eig-split-im-lauf.md) stammte die Deutung: der Eig-Split scheitere,
weil `colour_of_body` genau in den verschmolzenen Episoden fehle - *"die Rettung ist per Bauart
dort nicht verfuegbar, wo sie gebaut wurde"*. Ich nannte das den wertvollsten Teil des Befundes.

**Die Catch-22 ist real und jetzt geschlossen - und der Eig-Split wird trotzdem nicht brauchbar.**
`bs_beide` liegt mit 6,1 % groben Fehlern und 56,7 % Quote weiter unter der Vorgabe, obwohl jede
erreichbare Bindung vorliegt. Die fehlende Bindung war also **nicht** der Grund.

Was uebrig bleibt als Erklaerung, und es steht schon auf der vorigen Seite: der Split kostet
Feinheit auf den vielen NICHT verschmolzenen Szenen (Median hier 7,3 gegen 3,2 mm), und dieser
Preis faellt in jeder Episode an, waehrend der Nutzen nur in den wenigen verschmolzenen anfaellt.
Eine bessere Bindung vergroessert beides gleichzeitig.

# Der halbierte Median ist vermutlich Abdrift

`bs_bind` halbiert den Median-Adressfehler (3,2 -> 1,4 mm). Das sieht nach einem echten Gewinn aus,
und `colour_of_body` haengt tatsaechlich an mehr als dem Split (ckey-Tracker, Fovea-
Identitaetskanal, Selbst-Urteil). **Die Aufschluesselung spricht trotzdem dagegen:**

    bs_bind   Adressen in Episoden MIT Bindung-Split   n= 38   Median 1,4 mm
              Adressen in Episoden OHNE                n=122   Median 1,4 mm

Der Gewinn liegt **genauso in den 119 Episoden, in denen der Mechanismus gar nicht gefeuert hat**.
Waere er die Ursache, muesste er dort fehlen. Der Median ist damit kein Wirkungsnachweis, sondern
der uebliche Unterschied zwischen zwei Laeufen, die sich nach dem ersten Eingriff trennen.

> **Die Probe ist billig und haette bei frueheren Befunden geholfen:** wenn ein Gewinn auch dort
> auftritt, wo der Eingriff nicht gegriffen hat, ist er keiner.

# Bewertung

* **Der Mechanismus ist einwandfrei und wirkungslos.** Beides gehoert in denselben Satz: er bindet
  jeden erreichbaren Koerper, und die Zielgroesse bewegt sich nicht (p = 1,00).
* **Eine Ursache zu schliessen beweist nicht, dass sie die Ursache war.** Die Catch-22 existiert,
  ist beschrieben, ist jetzt zu - und war nicht der Engpass.
* **Die groben Fehler bleiben im Band `riesig`** (bs_aus 5/21, bs_bind 6/24). Die Verschmelzung ist
  weiterhin der ganze Restfehler, und keiner der drei bisherigen Eingriffe hat sie angefasst -
  sie haben nur um sie herum gearbeitet.

# Fallen

* **Ein Seed je Arm.** Der Bindungsbefund (34/34, 53/53) traegt, weil er innerhalb der Laeufe
  zaehlt; die Quoten- und Medianvergleiche tragen nicht.
* **Die Meldung `X von Y` ist irrefuehrend** und bleibt es, weil `_offen` die geparkten Koerper
  mitzaehlt. Wer sie kuenftig liest, muss 3 je Episode abziehen.
* **`ebene: pruefstand` fuer die Deckungszahlen** (63 -> 97 %), `act23-ab` fuer alles andere.

# Folgen

`ACT23_BINDUNG_SPLIT` bleibt auf `0`. Der Schalter bleibt im Code: er ist die einzige Fassung, die
verschmolzene Koerper ueberhaupt bindet, und der naechste Anlauf gegen die Verschmelzung wird ihn
brauchen.

Was NICHT mehr zu versuchen ist: den Eig-Split ueber eine bessere Farbquelle retten. Drei Anlaeufe,
drei Negative.

# Verwandt

* [Der Form-Split im Eigenschafts-Pfad schadet](/befunde/eig-split-im-lauf.md) - dessen Catch-22-Deutung hier widerlegt wird
* [Jeder grobe Adressfehler sitzt im obersten Band](/befunde/adressfehler-sind-verschmelzung.md) - der offene Kern
* [Beim Trennen entscheidet die Farbquelle](/befunde/eig-split-farbquelle.md)
* [Farb-Mischung](/befunde/farb-mischung.md) - warum die Bindung nicht uebernommen werden kann
