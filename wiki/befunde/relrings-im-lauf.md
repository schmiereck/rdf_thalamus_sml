---
type: Befund
title: Relative Ringe im Lauf - kein Aneignungsgewinn, und die Lokalisierung leidet
description: Zwei frische Laeufe zu je 300 Episoden, ACT_SHAPE_RELRINGS 0 gegen 1. Die Geburtenrate ist identisch (5 zu 5), das Ueberleben eher schlechter (3 zu 2), und die Adressierung wird messbar ungenauer - grobe Fehler 2,1 auf 9,8 Prozent (p = 0,0001). Die Lieferquote faellt von 20,3 auf 11,7 Prozent. Die Pruefstandsverbesserung schlaegt NICHT durch.
tags: [act23, wahrnehmung, formklassen, negativ, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-13T12:00:00Z }
sources:
  - id: ab
    resource: "Zwei kopflose Steuerungslaeufe je 300 Episoden, ACT23_FRESH=1 (beide bei null), ACT_SHAPE_RELRINGS 0/1, gleichzeitig gefahren"
    title: Relrings im vollen Lauf
---

# Behauptung

Die am Pruefstand gemessene Verbesserung ([18 % -> 69 % bei uebergrossen
Formen](/befunde/relrings-rueckhalt.md)) **schlaegt im Lauf nicht durch**. Sie kehrt sich in den
Groessen, die zaehlen, sogar um:

* **Geburtenrate identisch** - 5 zu 5 auf je 300 Episoden (p = 1,00). Die Vorhersage "sie sollte
  sinken, wenn Uebersegmentierung die Ursache war" trifft **nicht** zu.
* **Ueberleben eher schlechter** - 3 von 5 gegen 2 von 5.
* **Adressierung messbar ungenauer** - grobe Fehler (>20 mm) 2,1 % gegen 9,8 %, **p = 0,0001**.
* **Lieferquote** 20,3 % gegen 11,7 % (p = 0,0052).

# Aufbau

Beide Arme **bei null** (`ACT23_FRESH=1`), weil ein geaenderter Deskriptor mit dem gespeicherten
Bestand nicht vergleichbar ist - die 80 Exemplare je Klasse sind mit festen Ringen gerechnet.
Ein Vergleich gegen den gelernten Zustand waere unfair gewesen; er haette den frischen Agenten
aus Gruenden verlieren lassen, die nichts mit den Ringen zu tun haben.

Nebeneffekt, der den Lauf interessanter macht: ein frischer Agent kennt **keinen** der sieben
Koerper und muss alle selbst entdecken - genau die Aneignungssituation, um die es geht.

# Zahlen

    Arm        Ep   Quote | geboren  verhungert  ueberlebt | Farbklassen
    rr_fest   300  20,3 % |    5         2           3     |    10
    rr_rel    300  11,7 % |    5         3           2     |    11

    Quote je 100 Episoden      fest  4,0 | 25,0 | 32,0
                            relativ  5,0 |  9,0 | 21,0
      (beide noch im Hochlauf - der Vergleich trifft zwei unfertige Agenten)

    Je Klasse (max erreichte Wiedererkennung / Kommandos / Schicksal)
      fest     neu-1 92 % 15x lebt | neu-2 75 % 2x tot | neu-3 100 % 5x lebt
               neu-4 88 % 0x tot   | neu-5 67 % 0x lebt
      relativ  neu-1 92 % 14x lebt | neu-2 67 % 0x tot | neu-3 92 % 1x lebt
               neu-4  0 % 0x tot   | neu-5 50 % 0x tot

    ADRESSIERUNG (Kommando gegen wahre Lage)
      fest     n=290  Median 2,5 mm  >20 mm  6 =  2,1 %  eindeutig 285/290
      relativ  n=306  Median 3,4 mm  >20 mm 30 =  9,8 %  eindeutig 298/306
      Fisher p = 0,0001

    privilegierter Rueckfall   fest 25   relativ 52

# Warum die Lokalisierung leidet

Das ist der Kern und er war nicht vorhergesehen. Der Deskriptor liefert nicht nur die
**Klasse**, sondern haengt am selben Pfad wie Greifpunkt und Ausrichtung
(`_harmonics_at` -> `_yaw_from`). Relative Ringe verschieben die Abtastung je nach
Objektgroesse - und damit auch, welche Bildstellen in die Lage- und Winkelschaetzung eingehen.

Belegt ist die Folge, nicht der Weg: grobe Adressierungsfehler vervierfachen sich, der
privilegierte Rueckfall verdoppelt sich (25 -> 52), und der Median-Endabstand steigt von 89 auf
104 mm. **Welcher Teilschritt genau leidet, ist ungemessen.**

# Bewertung

**Die Pruefstandsfalle ist doch zugeschnappt - nur eine Stufe spaeter als sonst.** Der
[Rueckhalte-Test](/befunde/relrings-rueckhalt.md) war bereits ein direktes Mass und zeigte einen
grossen, sauberen Gewinn (18 % -> 69 %, zwei Seeds, kein Preis bei den bekannten Formen). Er hat
trotzdem nicht vorhergesagt, was im Lauf passiert.

Der Grund ist im Nachhinein klar und haette vorher auffallen koennen: **der Rueckhalte-Test misst
nur die Klassifikation.** Im Lauf haengt am selben Deskriptor noch die Lokalisierung, und die
verliert mehr, als die Klassifikation gewinnt. Eine isolierte Messung kann das per Konstruktion
nicht sehen.

> **Die Lehre, praeziser als bisher:** ein direktes Mass ist nicht automatisch das richtige Mass.
> `ebene` sagt, **wo** gemessen wurde - nicht, ob **alles Betroffene** mitgemessen wurde.

**Was der Befund nicht sagt:** dass relative Ringe grundsaetzlich untauglich sind. Die
Klassifikation gewinnt nachweislich. Wer den Ansatz weiterverfolgen will, muesste die
Lokalisierung vom Klassen-Deskriptor **trennen** - feste Ringe fuer Greifpunkt und Yaw, relative
nur fuer `resolve()`. Das ist nicht gebaut und waere der sechste Anlauf.

# Fallen

* **Beide Arme sind unfertig.** 300 Episoden ab null reichen nicht; die Quote steigt in beiden
  monoton (4/25/32 gegen 5/9/21). Der Quotenvergleich trifft zwei Agenten mitten im Anlernen -
  die Richtung ist in allen drei Bloecken gleich, die absoluten Werte sagen wenig.
* **Ein Seed je Arm.** Nach [Zwei Laeufe sind dieselbe
  Rechnung](/befunde/laeufe-sind-reproduzierbar.md) ist das je eine Stichprobe. Der
  Adressierungsbefund (p = 0,0001 ueber ~300 Sichtungen je Arm) traegt trotzdem, weil er
  innerhalb der Laeufe misst.
* **Keine Klasse bekam einen Knopf** (0 in beiden Armen) - dieselbe Vergabe-Engstelle wie im
  gelernten Zustand, hier aber, weil `NOVEL_BODY` in der frischen Welt gar nicht erst gebunden
  ist. `neu-1` wurde dennoch 15- bzw. 14-mal kommandiert, ueber das Eigenschafts-Kommando; der
  [reparierte Zaehler](/befunde/aneignung-blinder-fleck.md) macht das erstmals sichtbar.

# Folgen

`ACT_SHAPE_RELRINGS` bleibt auf `0`. Der Schalter bleibt im Code samt gemessener Begruendung -
er ist die Grundlage fuer einen sechsten Anlauf, der Klassifikation und Lokalisierung trennt.

# Verwandt

* [Relative Ringe bestehen den Rueckhalte-Test](/befunde/relrings-rueckhalt.md) - der Pruefstand, hier entkraeftet
* [Groessen-Invarianz, fuenfter Anlauf](/befunde/groessen-invarianz-fuenfter-anlauf.md) - die Kennzahl
* [Die Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) - der vierte dokumentierte Fall
* [Der blinde Fleck der Aneignung](/befunde/aneignung-blinder-fleck.md)
