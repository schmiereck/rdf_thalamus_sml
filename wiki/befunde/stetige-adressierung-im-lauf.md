---
type: Befund
title: Die stetige Adressierung im Lauf - neutral, wie vorhergesagt, und damit als Baustein bestaetigt
description: Zwei Arme je 150 Episoden, nur die Matching-Regel getauscht. Grobe Adressierungsfehler 10,8 gegen 8,5 Prozent, Rueckfall 7 gegen 10, Quote 58,7 gegen 56,0 - nichts loest auf, genau wie die Offline-Sonde es vorhersagte. Der Vorgabearm reproduziert den bekannten Bezug zifferngenau. Damit ist der Bau verifiziert und die Adressierung funktioniert ohne Namen; der erhoffte Gewinn kann so aber nicht entstehen, weil die Klassen daneben weiterleben.
tags: [act23, kommando, latent, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-16T00:00:00Z }
sources:
  - id: ab
    resource: "Zwei kopflose Steuerungslaeufe je 150 Episoden aus derselben Kopie von act23_state.pkl (ad9d768c), ACT23_EIG_STETIG 0 gegen 1, sonst Vorgaben"
    title: Stetige Adressierung im Lauf
  - id: sonde
    resource: /befunde/stetige-adressierung-erster-schritt.md
    title: Die Offline-Sonde, deren Vorhersage hier geprueft wird
---

# Zahlen

    Arm       Ep   Quote  | Adr.Median  grobe Fehler >20mm | Rueckfall | Achsen | eindeutig
    st_aus   150  58,7 %  |   2,0 mm      18/167 = 10,8 %  |     7     |  1,81  |  98,2 %
    st_an    150  56,0 %  |   2,2 mm      14/164 =  8,5 %  |    10     |  1,91  |  99,4 %

    stetig gegen diskret:  grob p = 0,58 | Quote p = 0,73 | Rueckfall p = 0,62

**Nichts loest auf** - und genau das hatte die [Offline-Sonde](/befunde/stetige-adressierung-erster-schritt.md)
vorhergesagt: bei dieser Toleranz liegt die stetige Achse praktisch auf dem diskreten Bezug.

# Der Bau verhaelt sich wie seine Nachbildung

Das war der eigentliche Zweck des Laufs. Die Sonde ist eine **Replik** der Wuerfelei; der Einbau ist
der echte Pfad und holt seinen Massstab aus den eigenen Klassenwolken (`eig_bezug`) statt aus
hingestellten Koerpern. Beide kommen zum selben Ergebnis - der Unterschied zwischen Replik und
Original ist also klein genug, um der Sonde weiter zu glauben.

Dazu der zweite Beleg: **`st_aus` reproduziert den bekannten Bezug zifferngenau** - 58,7 % Quote,
18 von 167 groben Fehlern, 7 Rueckfaelle. Dieselben Zahlen wie `g7_aus` und `r7_aus` aus dem
siebten Anlauf. Am Aufbau liegt nichts.

Die Richtungen stimmen ebenfalls mit der Sonde ueberein: etwas weniger grobe Fehler, etwas mehr
Rueckfall, etwas mehr genannte Achsen (1,81 -> 1,91). Die stetige Achse trennt an dieser Stelle
minimal weniger, also legt die Wuerfelei haeufiger eine dritte Achse nach.

# Was der Bau kann - und was er nicht kann

**Er kann:** ohne Namen adressieren. Das Kommando greift auf Chromatizitaet, Formeinbettung und
Ausdehnung zu; die Namen tragen nur noch Anzeige und Protokoll. Der Rauchtest davor loeste 16
Adressen mit null Rueckfall und 0-1 mm Treffergenauigkeit auf.

**Er kann nicht**, worauf die [Frage](/fragen/stetige-adressierung.md) zielt. Der Einbau ist
**additiv**: die Formklassen entstehen weiter, bekommen weiter Knoepfe und verhungern weiter. Der
erhoffte Gewinn sollte gerade aus dem WEGFALL dieses Lebenszyklus kommen - und solange der
Lebenszyklus danebensteht, kann dieser Gewinn gar nicht eintreten.

> **Der Baustein ist bestaetigt, die These ist es nicht.** Um sie zu pruefen, muesste die
> Adressierung nicht nur ohne Namen AUSKOMMEN, sondern die Klassen muessten fuer das Kommando
> ueberfluessig WERDEN - also Geburt, Bestaetigung und Knopfvergabe entfallen, weil eine Adresse
> direkt aus einer Sichtung entsteht.

# Was das fuer den naechsten Schritt heisst

Die Klassen tragen heute mehr als das Kommando (Verhungerungsschutz, Konsolidierung, Fovea-
Identitaetskanal). Sie ersatzlos zu streichen ist kein kleiner Eingriff und waere mit dieser
Messung auch nicht gedeckt.

Der kleinere, pruefbare Schritt waere: **die Auto-Schleife eine Adresse fuer einen Koerper anlegen
lassen, der keine Klasse hat** - stetig ist das moeglich, diskret nicht, weil ohne Klasse kein Name
existiert. Damit waere die
[Vergabe-Engstelle](/befunde/vergabe-engstelle-diagnose.md) nicht repariert, sondern gegenstandslos,
und man saehe zum ersten Mal, ob das Kommando die Klassen ueberhaupt braucht.

# Fallen

* **Ein Seed je Arm, 150 Episoden.** Bei p = 0,58 bis 0,73 ist das keine Aussage ueber Wirkung,
  sondern ueber Abwesenheit einer grossen Wirkung.
* **Eine Toleranz.** Gefahren wurde nur `EIG_TOL_FORM=0,5`; die Sonde zeigt, dass der Rueckfall
  sich mit der Toleranz erheblich verschiebt (60 bis 16 %). Im Lauf ist das nicht durchgefahren.
* **Der GUI-Pfad ist nicht dabei.** `_eig_setzen` schreibt kein `EIG_MESS`, eine von Hand gesetzte
  Adresse faellt auf den Namensvergleich zurueck - sicherer Rueckfall, aber in der GUI ist der
  Schalter wirkungslos.
* **Vorgabe bleibt 0.**

# Verwandt

* [Die stetige Formachse ist genauso trennscharf](/befunde/stetige-adressierung-erster-schritt.md) - die Vorhersage
* [Stetig adressieren statt Klassen vergeben](/fragen/stetige-adressierung.md) - die These, hier NICHT geprueft
* [Die Vergabe-Engstelle, diagnostiziert](/befunde/vergabe-engstelle-diagnose.md) - was gegenstandslos wuerde
