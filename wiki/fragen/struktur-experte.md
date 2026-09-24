---
type: Frage
title: Ein Struktur-Experte - Aenderungen an der Netzstruktur vorschlagen, pruefen, verwerfen, ausbauen
description: Nutzeridee 2026-09-24 - die gewachsene Netzstruktur ist nicht statisch; ein "Experte" soll Strukturaenderungen vornehmen, an den Aufgaben pruefen, verwerfen oder ausbauen, und auch andere Ansaetze als PC-CVNN sind zugelassen. Analyse an den Messerfahrungen dieser Linie. Kernpunkt - der Engpass ist nicht das Vorschlagen, sondern das URTEIL. Eine act23-Episode kippt schon bei kleinen Aenderungen in rund einem Fuenftel der Faelle, ein gepaarter Vergleich ueber 90 Episoden loest erst ~15 Punkte auf und kostet ~1 h. Eine Suche, die nach Lieferquote ausliest, waehlt Rauschen (der Einzelseed 49 gegen 14 Prozent war genau das). Vorschlag - dreistufiges Urteil (Modul-Messgroesse als Vorfilter, gepaartes act23-A/B, Bestaetigung auf frischen Seeds), Fitness nach Projektziel als Lerngeschwindigkeit fuer NEUES statt Lieferquote, und zuerst ein Experimentverwalter statt einer freien Architektursuche.
tags: [act23, architektur, methode, nutzeridee]
status: draft
evidenz: vermutung
ebene: code
generated: { by: claude/opus-5.5, at: 2026-09-24T00:00:00Z }
sources:
  - id: streuung
    resource: /befunde/stufe4-drei-arme-gepaart.md
    title: Auf identischer Szene kippt eine kleine Aenderung den Ausgang in rund einem Fuenftel der Episoden
  - id: sweep
    resource: /befunde/stufe4-sweep-widerlegt.md
    title: Ein Einzelseed-Gewinner, der Rauschen war
  - id: falle
    resource: /mechanismen/pruefstandsfalle.md
    title: Pruefstandsergebnisse sagen act23 nicht vorher
---

# Die Idee

Die Struktur ist ueber Monate gewachsen und darf sich aendern. Ein "Experte" soll Aenderungen an
der Struktur vornehmen, sie an den Aufgaben beurteilen, Verlierer verwerfen und erfolgreiche Pfade
ausbauen. PC-CVNN ist eine Idee unter moeglichen; andere Ansaetze sind zugelassen.

# Was die Messerfahrung dazu sagt

**Der Engpass ist das Urteil, nicht das Vorschlagen.** Drei gemessene Tatsachen:

1. **Die Messung ist grob.** Auf identischer Szene kippt schon eine kleine Aenderung den Ausgang in
   rund einem Fuenftel bis Viertel der Episoden, in beide Richtungen gleich oft
   ([drei Arme](/befunde/stufe4-drei-arme-gepaart.md),
   [neben der Mitte](/befunde/stufe4-stapel-neben-der-mitte.md)). Ein gepaarter Vergleich ueber 90
   Episoden (~1 h bei zwei Prozessen) loest damit erst Unterschiede um 15 Punkte auf.
2. **Wer nach Lieferquote ausliest, waehlt Rauschen.** Der Einzelseed 49 gegen 14 % (p = 0,004)
   war ueber acht Seeds 38 gegen 33 ([Sweep](/befunde/stufe4-sweep-widerlegt.md)). Ein Experte, der
   viele Varianten probiert und die beste ausbaut, erzeugt solche Gewinner systematisch - der
   Fluch des Siegers.
3. **Billige Vorpruefungen sagen den Lauf nicht vorher** - in dieser Linie viermal
   ([Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)). Ein Vorfilter darf also nur
   AUSSORTIEREN, was schon lokal kaputt ist, nie einen Gewinner kueren.

Dazu die Rechnung: bei hoechstens zwei act23-Prozessen sind es rund 1 500 bis 2 000 Episoden am
Tag. Das sind etwa 10 bis 20 ehrlich beurteilte Strukturvarianten pro Tag - genug fuer eine
geleitete Suche, zu wenig fuer eine blinde.

# Vorschlag

## Das Urteil in drei Stufen

1. **Lokal (Minuten):** die Messgroesse des geaenderten Moduls selbst - Vorhersagefehler des
   PC-Moduls, Lokalisierungsfehler der Wahrnehmung, Treffgenauigkeit des Schaetzers. Nur zum
   Aussortieren.
2. **Gepaart (1 h):** drei Seeds x 30 Episoden, `ACT23_SZENE_JE_EPISODE`, McNemar gegen die
   aktuelle Struktur. Das ist genau die Reihe, die jetzt von Hand laeuft.
3. **Bestaetigung (1 h):** nur fuer Kandidaten, die Stufe 2 bestehen - frische Seeds, gleiches
   Protokoll. Erst wer beide besteht, wird ausgebaut. Das nimmt den Fluch des Siegers heraus.

## Die richtige Fitness

Nach [Projektziel](/ziel.md) ist die Lieferquote die falsche Zielgroesse. Besser ist, **wie
schnell die Struktur etwas NEUES lernt**: eine neue Farbe, eine neue Form, ein neues Wort. Das hat
zwei Vorteile - es misst, worauf es ankommt, und es ist haeufig schaerfer als die Quote, weil eine
Lernkurve viele Messpunkte je Lauf liefert statt eines Bits je Episode. Die
[Richtungs-Relationen](/fragen/richtungs-relationen.md) waeren ein natuerlicher erster Pruefstein:
"nach wie vielen Episoden benutzt der Agent 'links' richtig, und gilt es fuer einen neuen
Bezugskoerper?"

## Zuerst ein Experimentverwalter, keine freie Architektursuche

Ein Experte, der selbst Code umschreibt, wuerde mit der heutigen Messaufloesung vor allem Rauschen
ausbauen. Der naechste sinnvolle Schritt ist kleiner: ein Werkzeug, das eine als Schalter
formulierte Variante nimmt, die drei Urteilsstufen selbsttaetig faehrt, auswertet, den Wiki-Eintrag
entwirft und Verlierer verwirft. Die Vorschlaege kommen zunaechst von Nutzer und Agents. Wenn das
traegt, kann der Vorschlagsteil wachsen - bis hin zu Varianten, die nicht PC-CVNN sind, solange sie
an dieselben Ports passen.

# Was hier NICHT behauptet wird

Keine Messung. Die Zahlen oben sind Hochrechnungen aus den gepaarten Reihen vom 2026-09-23/24.

# Verwandt

* [Richtungs-Relationen](/fragen/richtungs-relationen.md) - die zweite Idee vom selben Tag, als Pruefstein
* [Gepaart je Episode](/messungen/act23-headless-ab.md) - das Werkzeug, auf dem Stufe 2 aufbaut
* [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) - warum Stufe 1 nur aussortieren darf
* [Projektziel](/ziel.md)
