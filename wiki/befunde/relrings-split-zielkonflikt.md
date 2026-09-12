---
type: Befund
title: Der sechste Anlauf widerlegt meine Ursachenzuschreibung - Groessen-Invarianz und Adressierung stehen im Zielkonflikt
description: Klassifikation und Ausrichtung zu trennen behebt den Adressierungsschaden NICHT (8,8 gegen 9,8 Prozent, praktisch identisch). Der Schaden kam nie vom Yaw, sondern ist die direkte Folge der Groessen-Invarianz selbst: breitere Klassen tragen mehr Koerper, und ein Eigenschafts-Tripel trifft dann haeufiger den falschen. Gemessen: drei geteilte Klassen statt zwei, darunter eine mit drei Koerpern.
tags: [act23, wahrnehmung, formklassen, negativ, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-14T00:00:00Z }
sources:
  - id: ab
    resource: "Zwei kopflose Steuerungslaeufe je 300 Episoden, ACT23_FRESH=1, ACT_SHAPE_RELRINGS 0 gegen 2 (getrennt), gleichzeitig gefahren"
    title: Split-Modus im vollen Lauf
  - id: vorher
    resource: /befunde/relrings-im-lauf.md
    title: Fassung 1, an der die Diagnose entstand
---

# Was geprueft wurde

Aus [Relative Ringe im Lauf](/befunde/relrings-im-lauf.md) stammte meine Erklaerung fuer den
Adressierungsschaden: *"am selben Deskriptor haengt auch die Ausrichtung (`_yaw_from`), und
relative Ringe verschieben deren Abtastung."* Der sechste Anlauf trennt beides -
`ACT_SHAPE_RELRINGS=2` rechnet die Klasse auf relativen, den Yaw auf festen Ringen. (Der
**Greifpunkt** haengt ohnehin nicht an den Harmonischen; er kommt direkt aus der Maske.)

Am Pruefstand ist die Trennung sauber: die Klassifikations-Verbesserung bleibt **exakt** erhalten
(uebergrosse Formen 25,9 % -> 88,9 %, identisch zu Fassung 1).

# Die Widerlegung

    Arm         Ep   Quote | Adr.Median  grobe Fehler >20mm | Rueckfall | geb verh ueberl
    s6_fest    300  20,3 % |    2,5 mm     6/290 =  2,1 %   |    25     |  5   2    3
    s6_split   300  18,7 % |    3,4 mm    28/318 =  8,8 %   |    22     |  8   4    4

    Fisher p = 0,0003
    zum Vergleich Fassung 1 (alles relativ):  2,1 % -> 9,8 %,  p = 0,0001

**8,8 % gegen 9,8 % - der Split behebt nichts.** Meine Ursachenzuschreibung war falsch: der
Adressierungsschaden kam **nicht** vom Yaw.

Die Lieferquote ist diesmal unauffaellig (20,3 gegen 18,7 %, p = 0,68) - der Quotenverlust der
Fassung 1 ging also tatsaechlich auf die Ausrichtung zurueck. Nur die **Adressierung** nicht.

# Die wirkliche Ursache: ein Zielkonflikt

Welche Koerper teilen sich eine Formklasse?

    s6_fest    5 Klassen im Einsatz, 2 von mehreren Koerpern getragen
               L    <- obj_L, obj_T
               cube <- obj_green, obj_red

    s6_split   6 Klassen im Einsatz, 3 von mehreren Koerpern getragen
               L     <- obj_L, obj_red
               cube  <- obj_blue, obj_green, obj_red      (drei!)
               neu-3 <- obj_T, obj_U, obj_blue            (drei!)

**Das ist kein Defekt, sondern genau das Gewuenschte - und zugleich der Schaden.** Groessen-
Invarianz heisst: mehr Koerper fallen in dieselbe Klasse. Damit wird ein Eigenschafts-Tripel
haeufiger mehrdeutig, und die Adressierung trifft oefter den falschen Koerper.

Die Fehlerliste bestaetigt es. In `s6_split` entfallen 21 der 28 groben Fehler auf Adressen mit
einer **Formachse** (`Form` 8, `Farbe+Form` 6, `Farbe+Form+Gr` 5, `Form+Gr` 2), und die
haeufigsten Einzelfaelle sind genau die geteilten Klassen:

    obj_U     (None, neu-3, mittel)  -> 28 mm     neu-3 traegt auch obj_T und obj_blue
    obj_green (None, neu-3, None)    -> 32 mm
    obj_red   (None, L, None)        -> 25 mm     L traegt auch obj_L

Und die Eindeutigkeitspruefung merkt es nicht: 316 von 318 Adressen melden **genau einen
Treffer**. Das ist woertlich der alte Satz aus dem
[Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) - **Eindeutigkeit ist nicht
Richtigkeit** -, hier zum ersten Mal als *Folge einer Verbesserung* statt als Folge von
Verschmelzung.

# Bewertung

* **Die Groesse war ein nuetzliches Unterscheidungsmerkmal.** "Die Groesse dominiert die Form"
  ([Formfaktorisierung](/befunde/formfaktorisierung.md)) klang bisher nur nach einem Mangel.
  Gemessen ist sie zugleich das, was `cube` von `neu-3` und obj_T von obj_U trennt. Wer sie
  herausnormiert, verliert diese Trennung - **die Adressierung bezahlt, was die Klassifikation
  gewinnt.**
* **Drei Anlaeufe, drei verschiedene Lehren.** Fassung 1 verlor Quote UND Adressierung; der Split
  rettet die Quote (p = 0,68), die Adressierung nicht. Damit sind die beiden Schaeden **getrennt
  lokalisiert**: Quote am Yaw, Adressierung an der Klassenbreite.
* **Was das fuer die Aneignung heisst, bleibt offen.** Der Split gebiert mehr Klassen (8 gegen 5)
  und behaelt mehr (4 gegen 3) - beides zu klein fuer eine Aussage, aber es widerspricht der
  Erwartung "Groessen-Invarianz senkt die Geburtenrate".

# Was daraus folgt

Der Weg "Deskriptor groessen-invariant machen" ist damit **nicht gescheitert, aber teurer als
gedacht**: er verlangt, die verlorene Trennschaerfe woanders zurueckzuholen. Der naheliegende Ort
ist die **Groesse als eigener Kanal** - genau der Ausweg, den
[Formfaktorisierung](/befunde/formfaktorisierung.md) schon nannte (*"die Faktorisierung gehoert
NEBEN den Deskriptor, nicht hinein"*), und der im Eigenschafts-Kommando als Groessenband bereits
existiert, in der Adressierung aber nur als grobe Dreiteilung (duenn/mittel/dick).

Konkret und ungeprueft: mit groessen-invarianten Klassen muesste das Groessenband **feiner** und
in der Wuerfelei **verpflichtend** werden, sobald eine Klasse mehrere Koerper traegt. Das ist der
siebte Anlauf und er betrifft die Adressierung, nicht den Deskriptor.

# Fallen

* **Beide Arme sind unfertig** (Quote steigt monoton, 4/25/32 gegen 1/31/24) und ein Seed je Arm.
  Der Adressierungsbefund traegt, weil er innerhalb der Laeufe ueber ~300 Sichtungen misst.
* **Die Klassennamen sind zwischen den Armen nicht vergleichbar** - jeder Arm vergibt eigene
  `neu-*`. Verglichen wird nur, wie VIELE Klassen von mehreren Koerpern getragen werden.
* **Der Pruefstand hat auch diesmal nicht getaeuscht**, er war nur unvollstaendig: die
  Klassifikations-Verbesserung ist real und im Lauf erhalten. Was er nicht zeigen kann, ist die
  Wirkung auf die *Adressierung*, die es am Pruefstand gar nicht gibt.

# Verwandt

* [Relative Ringe im Lauf](/befunde/relrings-im-lauf.md) - Fassung 1, deren Diagnose hier widerlegt wird
* [Formfaktorisierung](/befunde/formfaktorisierung.md) - "die Faktorisierung gehoert NEBEN den Deskriptor"
* [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) - "Eindeutigkeit ist nicht Richtigkeit"
* [Die Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)
