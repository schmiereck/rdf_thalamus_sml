---
type: Befund
title: Aneignung neuer Formen - was gelungen ist
description: Der Agent hat sich obj_Y in 15 bzw. 28 Episoden selbst angeeignet (Farbe, Formklasse, Knopf, ohne Etikett) und liefert danach besser als die meisten etablierten Objekte. Die Greif-Uebertragung traegt ueber die Armbreite. Mit den ehrlichen Abzuegen.
tags: [act23, selbstlernen, formklassen, erfolg]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-02T11:39:00Z }
verified: { by: human:thomas, at: 2026-09-02T11:39:00Z }
sources:
  - id: y
    resource: /raw/index.md
    title: obj_Y-Erstkontakt, 2 Seeds x 200 Ep, Wegwerfkopien, NO_PERSIST
  - id: breite
    resource: /raw/index.md
    title: ACT23_Y_ARM_W, 3 Arme x 200 Ep, eigene Kopien, Seed 11
---

# obj_Y: selbst angeeignet, in beiden Seeds

Neuer Koerper: drei Arme zu 120 Grad, je 14 x 26 mm, Spannweite 52 mm, Mitte **massiv** (kein
Schlitz wie beim U). Bewusst gewaehlt, weil **jede** bestehende Form aus achsparallelen Kaesten
bei 90 Grad gebaut ist - das Y bringt als erstes gedrehte Kaesten und 120-Grad-Winkel. Vorab
geprueft: `perceive_all` liefert `shape=None, prob 0,00`.

    Seed 11                        Seed 23
      Ep  9  Farbe gebunden          Ep  8   (farbe-16, 3 Blicke, d = 0,070 / 0,056)
      Ep 12  Formklasse geboren      Ep 26   (neu-338 / neu-339)
      Ep 15  KNOPF vergeben          Ep 28   -> Kommando "Neue Form 5"
      danach 19/31 = 61,3%           16/23 = 69,6% geliefert

**Ohne jedes Etikett, innerhalb von 15 bzw. 28 Episoden**, und danach ueber den meisten
etablierten Objekten (U 39/27 %, L 54/31 %, Form-7 44/24 %, Form-10 56/42 %).

**Ehrliche Abzuege:** (a) das Y ist geometrisch **guenstig** - duenne Arme, massive Mitte, kein
Schlitz; die hohe Quote kann daran liegen statt an Generalisierung. (b) Die Neuheit ist
**mittel**: neu sind 120-Grad-Winkel und gedrehte Kaesten, aber es besteht aus denselben duennen
Balken, auf die der Zustand lange trainiert ist. (c) n = 31 bzw. 23 fuer die Quote; belastbar
sind die **binaeren** Endpunkte, die in beiden Seeds uebereinstimmen.

# Die Kernlehre: die gerenderte Chroma zaehlt, nicht die RGBA

Das Rendern staucht den Farbraum stark:

    obj_X  rgba 0,65/0,95/0,15 (gelbgruen)  -> Chroma [0,414; 0,456; 0,130]
           -> faellt in farbe-4, die Klasse von obj_L (!), Abstand 0,042
    obj_Y  rgba 0,85/0,10/0,45 (purpurrot)  -> Chroma [0,500; 0,107; 0,393]
           -> faellt in farbe-16, Abstand 0,038 -- aber die ist FREI

**Wer eine Farbe waehlt, muss sie RENDERN und messen.** Eine Auswahl nach RGBA-Abstand ist
wertlos.

Damit ist auch obj_X' fehlende Farbklasse erklaert: seine Farbe ist im gerenderten Bild fast
identisch mit obj_L's, es wird also nie eine eigene Klasse fuer ihn geboren. **Ueber die Farbe
gibt es fuer obj_X keine Loesung** - der farbfreie Split ist der richtige und einzige Weg,
siehe [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md).

# Die Farbbindung wird nur EINMAL versucht

`colour_openset.observe()` gibt nur **neu geborene** Namen zurueck, und gebunden wird
ausschliesslich in dieser Schleife. **Die Bindung wird also genau einmal versucht, im Moment der
Klassengeburt.** Passt es dort nicht (naechster Koerper > 40 mm entfernt oder schon gebunden),
gibt es nie einen zweiten Versuch. Dasselbe "einmalig, kein Nachversuch"-Muster wie bei der
Klassenverhungerung.

Der Nachversuch (`ACT23_BIND_RETRY`, Vorgabe AUS) war **noetig**: ohne ihn haette obj_Y keine
Farbklasse bekommen. Der erste Entwurf richtete jedoch Schaden an - er band obj_X an `farbe-15`
mit Abstand 0,239, also die beste **freie** statt der **passenden** Klasse, auf einer einzigen
Sichtung. Repariert mit drei Wachhunden, jeder aus einem beobachteten Fehlschlag:

    (1) die Klasse darf an KEINEN anderen Koerper gebunden sein
    (2) HOECHSTDISTANZ 0,12 (= colour_openset.TH) -- eine falsche Bindung ist schlimmer als keine
    (3) BESTAETIGUNG ueber 3 uebereinstimmende Blicke

# Die Greif-Uebertragung traegt ueber die Bauteile

Frage: wurde das Y ohne Lernkurve gegriffen, weil die Uebertragung wirklich traegt - oder nur,
weil es eine neue **Anordnung vertrauter 14-mm-Balken** ist? `ACT23_Y_ARM_W` aendert **nur** die
Armbreite; verglichen wird gegen die etablierten Formen **desselben Laufs**.

    Breite  Klasse  Knopf   Y-Quote        Haus           Differenz     Fisher p
     10 mm   JA     NEIN    -- nie kommandiert, Endpunkt gegenstandslos --
     14 mm   JA     JA      19/28 = 67,9%  58/112 = 51,8%   +16,1 P     0,142
     20 mm   JA     JA      16/23 = 69,6%  42/93  = 45,2%   +24,4 P     0,061

Bei 14 **und** 20 mm liegt die neue Form deutlich ueber den Formen, die der Agent seit Hunderten
von Episoden uebt. Eine aeltere OOD-Aussage ("der Agent generalisiert nicht auf neue Geometrie")
gilt in dieser Form nicht mehr. Einschraenkung: n = 23-28, p = 0,06 bzw. 0,14 - die Richtung ist
in beiden Armen gleich und gross, aber keiner allein ist signifikant.

**10 mm scheitert an der WAHRNEHMUNG, nicht am Greifen** (die Voranmeldung verlangte diese
Trennung ausdruecklich):

    10 mm  gesehen 15/15,  878 px, aber als neu-9 BEANSPRUCHT in 11 von 15  (obj_T's Klasse)
    14 mm  gesehen 15/15, 1054 px, durchgehend NEUARTIG
    20 mm  gesehen 15/15, 1292 px, durchgehend NEUARTIG

Der duenne Y-Blob faellt in den Anspruchsradius der T-Klasse: `OPEN_MARGIN = 1,6 x 7,72 = 12,34`,
gemessener Abstand 9,47. Er ist **zugleich** neuartig (9,47 > 7,72) **und** beanspruchbar
(9,47 < 12,34) - und der Anspruch gewinnt.

# Fallen

* **Je Geometrie-Variante ein eigener Prozess.** Der Formklassifikator bindet sich an die zuerst
  gebaute Simulation; mehrere Breiten in EINEM Prozess liefern Unsinn (nur die erste wird
  gesehen). Meine erste Tabelle war dadurch in **beide** Richtungen falsch.
* **Der Erst-Treffer ist nicht robust.** Ich hatte "beim allerersten Griffversuch geliefert" als
  Merkmal genannt (so war es in beiden fruehen Seeds); im 14-mm-Lauf ging der erste Versuch mit
  147 mm daneben. Robust ist der **Aggregat-Vorsprung** ueber den Hausdurchschnitt.
* **Die Lauf-zu-Lauf-Streuung ist gross** (Hausdurchschnitt 45-52 % hier, 31-48 % in frueheren
  Laeufen). Deshalb wird immer gegen den **eigenen** Lauf verglichen.
* **Der Erstkontakt mit einem neuen Koerper ist eine EINMAL-Ressource.** `ACT23_NOVEL_BODY` muss
  darauf zeigen; die Vorgabe `obj_T` ist verbraucht.
* Nicht gewaehlt und warum: das **O** (Schlitz-Risiko wie beim U) und **Z/S** - der Deskriptor
  rechnet mit `np.abs(F)`, wirft also die Phase weg und ist **spiegelinvariant**; ein Z und sein
  Spiegelbild waeren fuer ihn identisch. Als spaeterer, absichtlicher Grenztest interessant.

# Verwandt

* [Formklassen-Lebenszyklus](/mechanismen/formklassen-lebenszyklus.md)
* [Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md) - die Gegenseite
* [Projektziel](/ziel.md)
