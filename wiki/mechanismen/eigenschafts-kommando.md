---
type: Mechanismus
title: Kommando ueber Farbe, Form und Groesse
description: Ein Objekt wird ueber das Tripel (Farbklasse, Formklasse, Groessenband) adressiert statt ueber seinen Namen - ohne dass eine Formklasse geboren sein muss. In der GUI bedienbar. Grenze: Eindeutigkeit ist nicht Richtigkeit.
tags: [act23, kommando, wahrnehmung]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-05T20:03:00Z }
verified: { by: human:thomas, at: 2026-09-05T20:03:00Z }
sources:
  - id: commit
    resource: "Commits a11736c, 54b14df, 0d8c88f"
    title: Eigenschafts-Kommando, GUI-Bedienung, Fovea-Kopplung
---

# Die Idee (Nutzer)

"Koennen wir nicht den Gedanken aufgeben, dass das Netz ein neues Objekt als GANZES lernt? Ein
Objekt setzt sich zusammen aus Farbe, Form, Groesse. Wenn wir uns von den Objektklassen loesen,
koennen wir die drei getrennt angeben. Damit waere ein genereller Weg fuer beliebige neue
Objekte offen." - und: "Ich weiss nicht, wo die Geburt stattfindet, aber vielleicht brauchen wir
die gar nicht."

Das trifft den Kern: an der Geburt sind vier Eingriffe gescheitert
([Formklassen-Lebenszyklus](/mechanismen/formklassen-lebenszyklus.md),
[Formfaktorisierung](/befunde/formfaktorisierung.md)). Die Idee laesst den Umweg weg.

# Machbarkeit, vorab gemessen

Ueber die acht heutigen Koerper sind die Tripel (Farbklasse, Formklasse, Groessenband)
**eindeutig** - 8 verschiedene Tripel fuer 8 Koerper.

**Ehrlich:** die Eindeutigkeit kommt fast ganz aus der **Farbe** (7 Klassen; die einzige
Kollision `farbe-4` bei obj_L/obj_X loest die Form auf). Die **Groesse trennt unter den heutigen
Koerpern nichts** - alle liegen zwischen 5,39 und 6,03, weil alle Balken 14 mm breit sind. Sie
ist vorbereitet, nicht heute schon nuetzlich; bei den Y-Varianten trennte sie klar
(Y10 5,00 | Y14 5,83 | Y20 7,07).

# Gebaut

* Die **Dicke wird immer gemessen** (vorher an die abgeschaltete Wache gekoppelt) und ist
  aufloesungsunabhaengig (`px_scale`-normiert, Bezug 240).
* `GROESSEN_BAENDER` = duenn < 5,2 | mittel 5,2-6,5 | dick > 6,5, aus Messungen.
* `finde_nach_eigenschaften(sim, clf, colours, farbe, form, groesse)` - jede Angabe darf `None`
  sein ("beliebig"); gibt Position, Detektion **und alle Treffer** zurueck, damit Mehrdeutigkeit
  sichtbar wird statt verschluckt.
* `state.add_eigenschaft(body, ...)` macht ein Objekt kommandierbar **ohne Formklasse**. Der
  Koerpername dient nur der Buchfuehrung; die Lokalisierung laeuft rein ueber die Kamera.
* GUI: drei durchschaltbare Waehlfelder + "waehlen"; der Wortschatz kommt aus dem, was der Agent
  **selbst** benannt hat, und wird waehrend des Laufs nachgezogen. Der Farbknopf wird im selbst
  gelernten Prototyp eingefaerbt - **kein vergebener Name wie "rot"**.
* Schalter: `ACT23_EIG_BODY/_FARBE/_FORM/_GROESSE`, `ACT23_EIG_ONLY=1` (blendet die alte
  Objektzeile aus), `ACT23_AUTO_EIG=1` (schreibt im Auto-Lauf die Adressierung in ein Tripel um,
  Achsen werden nachgelegt, bis genau ein Treffer bleibt).

# Zahlen

    obj_Y nur ueber farbe-16 adressiert, KEINE Formklasse, KEIN Knopf (10 Ep):
      [Auto 3] Lokalisierung [-0,063; 0,219] (wahr [-0,063; 0,219]) -> GELIEFERT 23 mm
      [Auto 8] Lokalisierung [ 0,054; 0,157] (wahr [ 0,052; 0,157]) -> GELIEFERT 13 mm

    Mit Eindeutigkeitszwang: 10 von 10 Episoden genau ein Treffer, Lokalisierung 0-8 mm.
    Ohne Zwang wuerfelte Auto das Tripel "mittel" (nur Groesse) -> 3 Treffer, falsches
    Objekt adressiert, 152 mm daneben.

**Nutzervorgabe zur Groesse:** "Reine Groessen-Adressen brauchen wir nicht. Wenn ich etwas von
aussen vorgebe, wuerde ich immer sagen 'der grosse Wuerfel' oder 'der gelbe Wuerfel' oder 'der
Wuerfel'. Aber nie 'das groesste Objekt'." Die Wuerfelei nennt seither immer mindestens Farbe
ODER Form - was zugleich genau die Achsen sind, denen ein Tracker folgen kann.

# Die eigentliche Grenze

    kommandiert obj_red (farbe-16, --, mittel)     -> Detektion [0,011; 0,148], wahr [ 0,041; 0,155]
    kommandiert obj_red (--, neu-13, mittel)       -> Detektion [0,011; 0,148], wahr [ 0,041; 0,155]
    kommandiert obj_T   (farbe-16, neu-13, mittel) -> Detektion [0,011; 0,148], wahr [-0,008; 0,140]

Dreimal dieselbe Detektion, fast exakt auf der Mitte zwischen obj_red und obj_T, die 51 mm
auseinander lagen.

> **Eindeutigkeit ist nicht Richtigkeit.** Die Schleife kann nur zaehlen, wie viele Detektionen
> passen; werden zwei Objekte gar nicht erst als **zwei** gesehen, hilft keine Zusatzachse. Das
> trifft die Namensauswahl genauso, es faellt hier nur auf, weil die Detektion protokolliert wird.

Naechster Schritt waere, die Verschmelzung zu **messen** statt zu vermuten: ab welchem Abstand
versagt der Split, und wie oft passiert das. Siehe
[Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md).

# Fallen

* **Wer `perceive_all` ruft, muss `mocap_pos` zuruecksetzen - ausnahmslos.** `perceive_all` ruft
  `_park_markers` und raeumt die magenta Zielscheiben aus dem Bild; wer sie nicht wiederherstellt,
  bekommt ein **geparktes Ziel**. Endabstaende 627-968 mm. Der Fehler ist hier **zweimal** an
  verschiedenen Stellen aufgetreten. **Ein Endabstand jenseits des Arbeitsraums ist immer eine
  geparkte Groesse, nie schlechte Ausfuehrung.**
* **Ein neues Adressierungsverfahren muss an VIER Stellen angemeldet werden.** `method` wird nicht
  nur beim Wahrnehmen abgefragt, sondern auch bei der Trackerwahl und beim `servo=`-Argument von
  `run_combined`. `"eigenschaft"` fiel in den else-Zweig und lief mit `servo=False`: **zwei
  unabhaengige Glauben in einer Episode**, der Arm auf der korrekten Lokalisierung, die Fovea auf
  einem beliebigen Blob. Behoben, indem das Tripel dem Tracker seinen Schluessel gibt
  ([Fovea-Servo] vorher 0x, nachher 162 Frames).
* **act23 hat ZWEI Auto-Schleifen** - die kopflose (`ACT23_AUTO_N`) und die der GUI, mit eigenem
  Code. Ein Schalter nur in der kopflosen gebaut und dort geprueft sah sauber aus, waehrend er in
  der GUI nichts tat. Derselbe Riss hat schon einmal `NOVEL_EVERY`/`SCENE_EVERY` betroffen (der
  Probe-Koerper wurde in 332 GUI-Episoden kein einziges Mal hingestellt). Jetzt eine Fassung
  (`_auto_eig_umschreiben`), von beiden Schleifen gerufen.
* **Die Homographie haengt an der Bildbreite.** act23 rendert mit `ACT23_RES=240`; eine Probe mit
  360x360 lag 36-159 mm daneben. Jede kuenftige Probe muss dieselbe Aufloesung verwenden.
* **Vorbehalt zu `ACT23_EIG_ONLY`:** damit ist von Hand nur noch kommandierbar, was **sichtbar**
  ist; ein geparkter Koerper faellt raus.

# Verwandt

* [Formfaktorisierung](/befunde/formfaktorisierung.md) - die Messung, die die Idee stuetzt
* [Formklassen-Lebenszyklus](/mechanismen/formklassen-lebenszyklus.md)
