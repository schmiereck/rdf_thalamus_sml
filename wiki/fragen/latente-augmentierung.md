---
type: Frage
title: Latente Augmentierung - aus einem Griff viele vorgestellte Lagen
description: Nutzeridee, durchdacht und messtechnisch gestuetzt, aber nicht gebaut. RoPE macht die Verschiebung zu einer exakten Phasendrehung, das Fundament existiert. Enthaelt drei Einwaende, die Gegenmessung des Nutzers und die Voraussetzungsmessung, die vor dem Bauen steht.
tags: [act23, latent, augmentierung, idee]
status: stable
evidenz: vermutung
ebene: code
generated: { by: claude/opus-5, at: 2026-08-31T19:27:00Z }
verified: { by: human:thomas, at: 2026-08-31T19:27:00Z }
---

# Die Idee, in den Worten des Nutzers

"Ich bin mir ziemlich sicher, dass mein Gehirn bei jedem Griff nach einem Schraubendreher
gleichzeitig verschiedene Lagen des Objektes parallel aufnimmt - sich gleich vorstellt, wie die
Welt aussaehe, wenn das Objekt leicht verdreht dalaege (mit abnehmender Intensitaet), und meine
Finger dann danach greifen wuerden. ... Wenn der Greifer ein Objekt erfolgreich gegriffen hat,
koennen wir gleich zig Szenen fuer leicht verschobene und gedrehte Objekte erzeugen. ... Ich
wuerde mir das als Vorstellungen im Latent Space vorstellen, nicht hunderte Varianten rendern.
... Im Idealfall auf Ebene der Connectoren zwischen den Modulen - dafuer hatte ich die einmal
gedacht."

**Technische Fassung:** Datenaugmentierung ueber eine bekannte **Aequivarianz**. Die Aufgabe hat
eine naeherungsweise SE(2)-Symmetrie in der Tischebene: verschiebt oder dreht man die Szene um
g, verschiebt bzw. dreht sich die richtige Aktion um dasselbe g. Eine bestaetigte Stichprobe
(s, a, Erfolg) erzeugt damit eine Bahn {(g·s, g·a, Erfolg)} fuer g in einer Umgebung der
Identitaet, mit einem Gewicht, das mit |g| faellt.

# Warum es hier passt

Der gemessene Engpass ist genau das: ueber je mehr als 1000 Episoden **kein Lernfortschritt**,
und die grobe Gutschrift auf Episodenebene ist der Flaschenhals. Augmentierung vervielfacht die
nutzbaren Stichproben je physischer Episode, ohne neue Episoden.

# Das Fundament existiert bereits

`src/pc_cvnn/rope.py` sagt im Docstring woertlich: *"Shifting position by m is a pure rotation
(no new weights); the inner product of two codes depends only on the relative displacement."*
Position steckt in der **Phase** (`z_k = A · exp(i·p·theta_k)`).

**Eine Verschiebung ist im Latent also EXAKT eine Phasendrehung, per Konstruktion** - die vom
Nutzer genannte Voraussetzung ("wir muessten den Latent Space verstehen") ist fuer die
Ortskanaele bereits erfuellt. `ACT_GOAL_ROPE=1` ist seit dem 30.08. Vorgabe. Weiter vorhanden:
`LatentDynamicsModule`, `latent_goal` mit Latent-Inverse-Babble von 0,8 mm, `dream_seen` im
Zustand.

**Wo es hingehoert:** auf die typisierten Ports. Eine Augmentierungsschicht faengt das Tupel ab,
das in den Lernpuffer geht, und gibt N transformierte Kopien mit gedaempftem Gewicht aus. Kein
Eingriff in die Netze - genau der Zweck, fuer den die Ports eingezogen wurden.

# Drei ernste Einwaende

**1. Die Annahme gilt nicht ueberall, und ausgerechnet dort nicht, wo es zaehlt.** "Objekt 5 mm
nach links -> Arm 5 mm nach links, Erfolgswahrscheinlichkeit unveraendert" stimmt im freien
Raum. Sie bricht in der Naehe von Nachbarn, an der Arbeitsraumgrenze und an der Reichweite.
Gemessen: die Fehlschlaege des Kreuzes haeufen sich bei Nachbarabstand ~52 mm, Erfolge bei
~94 mm. Eine Augmentierung, die nur mit |g| daempft, erzeugt genau in den engen Szenen
selbstsicher **falsche** Etiketten. **Die Daempfung muss vom KONTEXT abhaengen, nicht nur vom
Betrag.**

**2. Augmentierung vervielfacht bestaetigte ERFOLGE**, der gemessene Mangel ist aber, dass aus
den schweren Faellen nicht gelernt wird.

**3. Die Aequivarianz gilt fuer die Ortskanaele, nicht fuer den ganzen Zustand.** Der
Policy-Zustand mischt Hand-xyz, Objekt-xy, Objekt-z, Ziel-xy, Greifer, `obj_h`, `obj_fp` und
Fingerdruck. Ein SE(2)-Schritt darf nur auf die Ortsanteile wirken.

# Der Nutzereinwand gegen Einwand 2 - und er trifft

"Die Fehlschlaege und ihre Varianten sind fuers Lernen genauso wichtig. Wenn ein Griff
fehlschlaegt, wird er es bei leicht veraenderten Positionen auch tun, und natuerlich auch, wenn
andere Objekte zu dicht in der Naehe lagen. Das hebt Dein Argument auf - naeher an einem anderen
Objekt ist dann parallel ein Lernzweig, eben negativ. Vermutlich ist das 'so nicht' sowieso sehr
unterrepraesentiert."

**Gemessen, und die Vermutung stimmt** (1053-Ep-Lauf, `[Kredit]`-Zeilen):

    550  sicher geliefert                            -> Weltmodell +1 POSITIV
    288  Griff fehlgeschlagen/hielt nicht/verrutscht -> Weltmodell +1 NEGATIV
    198  "daneben platziert (Policy)"   -- Weltmodell ENTHAELT SICH
      8  "nicht gegriffen (Policy)"     -- enthaelt sich
      9  unsichere Lieferung            -- enthaelt sich

**206 Fehlschlaege - ein Fuenftel aller Episoden, die groesste Fehlerklasse - werden verworfen.**
Der Mangel ist nicht, dass Erfolge vervielfacht wuerden, sondern dass **Negative gar nicht erst
ankommen**.

# Es bleibt eine gemessene Asymmetrie

Aus [Exekutionsvarianz](/befunde/exekutionsvarianz.md): ICC ~0,6, ehrliche Obergrenze 82 % bei
Grundrate 54 % - dieselbe Szene liefert unterschiedliche Ausgaenge. Daraus:

* Ein **Erfolg** ist ein **Existenzbeweis**. Diese Pose ist greifbar; auf 5 mm daneben uebertraegt
  man etwas Bewiesenes.
* Ein **Fehlschlag** ist **kein** Nichtexistenzbeweis. Er kann Rauschen gewesen sein; uebertraegt
  man ihn, verteilt man ein moeglicherweise falsches Negativ ueber eine ganze Umgebung.

> **Regel daraus:** ein Negativ wird so weit uebertragen, wie seine **Ursache erklaert ist** -
> nicht so weit, wie die Verschiebung klein ist. Die Logs liefern die Unterscheidung bereits:
> "Griff hielt nicht (Drucksensor)" mit `tragen 0,00 N` ist mechanisch erklaert und gut
> uebertragbar; "daneben platziert" bei 20 mm Endabstand ist ein Beinahe-Treffer und koennte
> reine Zielstreuung sein.

# Die Synthese mit der anderen Nutzeridee

Eingebildete Varianten sollten gegen das Welt- bzw. Latent-Dynamik-Modell **geprueft** werden,
und nur die mit niedriger vorhergesagter Ueberraschung gehen ins Training. Das entschaerft
Einwand 1: die Vorstellung darf nicht blind sein, sondern muss sich am eigenen Modell messen
lassen. **Ueberraschungsgesteuerte Konsolidierung und aequivariante Vorstellung sind dieselbe
Maschine von zwei Seiten.**

# Erster Schritt: die Voraussetzung MESSEN, nicht annehmen

Kostet keinen Lauf: Szene rendern -> Latent z. Objekt um delta verschieben -> rendern ->
Latent z'. Vergleichen mit dem RoPE-vorhergesagten z_pred. Ueber einen Bereich von delta und
mehrere Grundszenen.

**Das Ergebnis IST die Daempfungsfunktion**, die der Nutzer intuitiv angenommen hat ("mit
abnehmender Intensitaet") - nur gemessen statt geraten, inklusive der Stelle, wo sie bricht
(Nachbarnaehe, Rand).

Dasselbe fuer Drehungen; dort traegt `_yaw_from(F)` die Phase, waehrend der Formdeskriptor
`np.abs(F)` die Phase **wegwirft** und damit drehinvariant ist - **Verschiebung und Drehung sind
also nicht symmetrisch zu behandeln.**

# Status

Idee durchdacht, **nichts gebaut, nichts gemessen**. Vor dem Bauen steht die
Voraussetzungsmessung.

# Verwandt

* [Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md)
* [Imitationspuffer](/befunde/imitationspuffer.md)
* [Offene Faeden](/fragen/offene-faeden-act23.md)
