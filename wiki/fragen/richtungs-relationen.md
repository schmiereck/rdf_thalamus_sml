---
type: Frage
title: Richtungs-Relationen - links, rechts, davor, dahinter, herunter
description: Nutzeridee 2026-09-24 - die Sprache um die Relationen links/rechts/davor/dahinter und die Aktion "herunter nehmen" erweitern. Analyse am Code und an den Stufe-4-Messungen. Kernpunkt - "herunter" gibt es als Aufgabe schon (Abstapeln), und die gepaarten Laeufe zeigen, dass eine Relation in der ADRESSE nur zaehlt, wenn die Eigenschaften allein nicht eindeutig sind. Richtungs-Relationen im BEZUG (Ablageziel) sind dagegen die erste Relation, fuer die es keinen anderen Weg gibt, das Ziel zu nennen. Mechanisch ist "links von Y" heute schon fast da (die Relation "an" zieht die Richtung zufaellig); offen sind das Bezugssystem und woher die Wortbedeutung gelernt wird. Vorschlag - Bedeutung aus der eigenen Ablage im Nachhinein etikettieren, das Wort ist die einzige Vorgabe.
tags: [act23, sprache, stapeln, relation, nutzeridee]
status: draft
evidenz: vermutung
ebene: code
generated: { by: claude/opus-5.5, at: 2026-09-24T00:00:00Z }
sources:
  - id: code
    resource: "src/pc_cvnn/pc_act23.py: ZIEL_RELATION (an|auf, Zeile ~789), die Richtung von 'an' als Zufallswinkel (~2707), ZIEL_ABSTAND 0,05"
    title: Die heutige Relation am Code
  - id: versatz
    resource: /befunde/stufe4-stapel-neben-der-mitte.md
    title: Die Relation in der Adresse traegt nicht, wenn die Eigenschaften eindeutig sind
---

> **GEBAUT UND GEMESSEN 2026-09-24** (Code b8a0f00), s.
> [Richtungswoerter selbst gelernt](/befunde/richtungswoerter-selbst-gelernt.md): Bezugssystem
> Kamerabild (Nutzerentscheidung). Aus 40 Spielepisoden mit "an" lernt der Agent die vier
> Bedeutungen selbst (3 von 4 innerhalb 1,5 Grad), und die gelernte Bedeutung traegt gepaart
> wie das Kamera-Geruest (Worttreffer 51 gegen 47, geliefert 35 gegen 35). Die Relation in der
> ADRESSE ("der Wuerfel links vom blauen") und "herunter" als Wort sind noch nicht gebaut.

# Die Idee

Zur Relation "auf" kommen **links von, rechts von, davor, dahinter** und die Aktion
**herunter nehmen**, damit Positionen relativ zu anderen Koerpern adressierbar werden. In der
Grammatik aus [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md):

    BEFEHL   := ADRESSE AKTION BEZUG
    BEZUG    := ORT | RELATION ADRESSE
    ADRESSE  := (Farbe?, Form?, Groesse?) | RELATION ADRESSE
    RELATION := an | auf | links | rechts | vor | hinter        <- neu: vier Richtungen
    AKTION   := bringen | herunter                              <- neu: herunter?

# Was die Messungen dazu schon sagen

1. **"Herunter nehmen" gibt es als Aufgabe schon** - das ist `ACT23_ABSTAPELN` ("nimm das, was auf
   Y liegt, und lege es auf den Tisch"). Neu waere nur, es als eigenes WORT im Befehl zu fuehren
   statt als Szenenaufbau. Als Wort ist es dann `ADRESSE := auf Y` plus `BEZUG := Tisch` - also
   keine neue Aktion, sondern eine Kombination vorhandener Teile. Das spricht fuer die Grammatik.
2. **Eine Relation in der ADRESSE zaehlt nur, wenn die Eigenschaften allein nicht eindeutig sind.**
   Gemessen zweimal: [zentriert](/befunde/stufe4-drei-arme-gepaart.md) und
   [neben der Mitte](/befunde/stufe4-stapel-neben-der-mitte.md) bringt "das, was auf Y liegt"
   nichts gegenueber "das rote Kreuz", weil es nur ein rotes Kreuz gibt. "Der Wuerfel links vom
   blauen" wird genauso folgenlos sein - ausser die Szene enthaelt **zwei gleiche Koerper**.
3. **Eine Relation im BEZUG ist dagegen unersetzlich.** "Lege es links neben den blauen" hat keinen
   anderen Ausdruck in der Sprache als eine Koordinate - und die Koordinate ist genau das Privileg,
   das die Adresse abschaffen soll. **Richtungs-Relationen im Ablageziel sind damit die erste
   Relation, deren Wirkung eine Aufgabe erzwingt**, und damit die richtige erste Stufe.
4. **Die Mechanik traegt den Abstand.** "an" legt heute 50 mm neben den Bezugskoerper, in einer
   ZUFAELLIGEN Richtung. Die gemessene Sperre liegt bei ~37 mm
   ([Nahe Ablage ist Mechanik](/befunde/nahe-ablage-ist-mechanik.md)), 50 mm ist darueber.
   "links von Y" ist mechanisch also "an Y" mit fester statt zufaelliger Richtung.

# Die zwei offenen Fragen

## Das Bezugssystem

"Links" braucht einen Standpunkt. Drei Kandidaten:

* **Kamerabild** - links im Bild des Agenten. Ist das, was der Agent sieht; natuerlichste Wahl fuer
  ein Wort, das er aus eigener Wahrnehmung lernen soll.
* **Armbasis** - links vom Arm aus gesehen. Koerperbezogen, wie beim Menschen.
* **Bezugskoerper** - "vor dem Kreuz" relativ zu seiner Ausrichtung. Schwerer, braucht die Lage
  (die Formklasse traegt sie als Phase, s. [Formwahrnehmung](/mechanismen/act23-modullandschaft.md)).

Zu entscheiden vom Nutzer; Vorschlag: Kamerabild.

## Woher die Wortbedeutung kommt

Heute RECHNET der Code das Ziel ("an" = Zufallswinkel x 50 mm). Nach
[Laufzeitregeln](/mechanismen/laufzeit-regeln.md) und dem Prinzip "weniger Teacher ist immer
besser" sollte "links" kein eingesetzter Winkel sein. Vorschlag, analog zum
[Tastetikett](/befunde/tastetikett-gegen-privileg.md):

* Der Agent legt ab (anfangs mit dem heutigen Zufallswinkel - das ist Spielen).
* Nach der Ablage SIEHT er, wo der Koerper relativ zum Bezug liegt, und etikettiert die Episode im
  Nachhinein mit dem Wort, dessen Richtung passt (Hindsight-Etikett aus eigener Wahrnehmung).
* Die einzige Vorgabe ist die Wortliste und das Bezugssystem - das ist die Sprache selbst, die von
  aussen kommen MUSS. Alles andere lernt er.
* Die Bedeutung wird als Phasendrehung im Latent gelernt (RoPE, s. Stapel-Seite Punkt 3) - dann
  gilt ein gelerntes "links" fuer jeden Bezugskoerper an jeder Stelle.

Pruefbar ist das an einer Generalisierung, die [Projektziel](/ziel.md)-nah ist: lernt der Agent
"links" an drei Koerpern, gilt es dann am vierten, den er nie als Bezug hatte?

# Was hier NICHT behauptet wird

Keine Quotenerwartung. Alles oben ist `ebene: code` bzw. Analyse. Die einzige gemessene Stuetze
ist, dass Relationen in der Adresse ohne Doppelgaenger folgenlos sind.

# Verwandt

* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - die Grammatik
* [Struktur-Experte](/fragen/struktur-experte.md) - die zweite Idee vom selben Tag; die Relationen waeren sein erster Pruefstein
* [Der Stapel neben der Mitte](/befunde/stufe4-stapel-neben-der-mitte.md) - warum eine Relation in der Adresse Doppelgaenger braucht
