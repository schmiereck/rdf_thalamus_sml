---
type: Mechanismus
title: Die latente Augmentierung, gebaut - nach der gemessenen Daempfungsfunktion, nicht nach der Annahme
description: ACT23_AUGMENT erzeugt aus einer bestaetigten Erfahrung N vorgestellte Lagen. Die Zulaessigkeit kommt aus der Messung: keine Daempfung nach dem Betrag, Schranke ist der Nachbarabstand minus 40 mm, gedeckelt bei 20 mm, nur Verschiebung. Im Rauchtest vervierfacht sich der Lernstoff je physischer Episode. Vorgabe 0, und sie braucht zwingend ACT23_NEIGHBOURS=1 - sonst bleibt sie wirkungslos, was beim ersten Rauchtest genau so passiert ist.
tags: [act23, latent, augmentierung, weltmodell]
status: stable
evidenz: gemessen
ebene: code
generated: { by: claude/opus-5, at: 2026-09-14T00:00:00Z }
sources:
  - id: code
    resource: "src/pc_cvnn/pc_act23.py -- augmentiere(), Einbau an der world.observe-Stelle"
    title: Der Bau
  - id: grund
    resource: /befunde/daempfungsfunktion.md
    title: Die Messung, aus der die Regeln stammen
---

# Was es tut

Nach jeder Episode, deren Ausgang dem Weltmodell zugeschrieben wird, entstehen zusaetzlich `N`
**vorgestellte** Zeilen: dieselbe Erfahrung an leicht verschobener Objektlage.

    ACT23_AUGMENT        Anzahl vorgestellter Lagen je Episode (Vorgabe 0 = aus)
    ACT23_AUGMENT_MAX    Deckel fuer |delta| (Vorgabe 0,020 m)
    ACT23_AUGMENT_FREI   Verschmelzungsschwelle (Vorgabe 0,040 m)
    ACT23_NEIGHBOURS=1   ZWINGEND, s. unten

# Die Regeln kommen aus der Messung

Aus [Die Daempfungsfunktion](/befunde/daempfungsfunktion.md), und sie widersprechen der
urspruenglichen Annahme:

* **Keine Daempfung nach dem Betrag.** Frei stehend ist die Aequivarianz bis 40 mm auf unter 1 %
  genau. Ein Gewicht, das mit `|delta|` faellt, wuerde das Falsche daempfen. Alle Vorstellungen
  bekommen deshalb `weight=1.0`, wie das Original.
* **Die Schranke ist der Nachbarabstand.** `delta < d_nah - 40 mm`, gedeckelt bei 20 mm. Dort
  bricht gemessen nicht der Median, sondern der Schwanz (p90 bis 17 mm) - also eine Minderheit
  VOLLSTAENDIG falscher Vorstellungen, und die sind schaedlicher als viele leicht schiefe.
* **Nur Verschiebung.** Die Drehung ist gemessen teurer (20 Grad kosten so viel Formdrift wie 40 mm
  Verschiebung), sie bewegt den Schwerpunkt, und nur `yaw4` traegt sie - mit umgekehrtem
  Vorzeichen. Ein eigener Bau, nicht eine Zeile nebenbei.

# Drei Entscheidungen im Bau

**Die Schranke liest, was der Agent ohnehin gesehen hat.** Der Nachbarabstand steht bereits im
Merkmalsvektor (NB-Block `[gueltig, d_nah, cos phi, sin phi, n_nah]`, ab `6+NH`). Kein
zusaetzliches Rendern, keine privilegierte Information. Ohne gueltigen Block wird **nicht**
augmentiert.

**Der neue Abstand wird konservativ gesetzt.** Die Richtung `phi` steht nur im Objektrahmen und der
Yaw nur mod pi - die Weltrichtung zum Nachbarn ist also um pi mehrdeutig. Statt zu raten wird der
schlimmste Fall angenommen (die Verschiebung ging genau auf den Nachbarn zu):
`d_nah_neu = d_nah - |delta|`. Eine untere Schranke, mit der die Zulaessigkeit garantiert gilt.

**Dieselbe Gruppe wie das Original.** `_groups` entscheidet, welche Zeilen beim Bootstrap und beim
Halteteil zusammenbleiben; Gruppen sind szenenweit (`lauf:szene`, hochgezaehlt in
`randomize_objects`). Mit eigener Gruppe landete eine Vorstellung im Testteil, waehrend ihr
Original trainiert - die Guete waere dann Selbstbetrug. Das ist die Messhygiene-Regel *"Halteteile
nie zufaellig ziehen"*, und sie war hier leicht zu verletzen.

**Was NICHT gefaelscht wird:** Winkel, `desc_embed`, Fovea- und Armstellungs-Block bleiben
unveraendert. Blickpfad und Armstellung gehoeren zur AUSFUEHRUNG, nicht zur vorgestellten
Objektlage. Und die **Aktion** bleibt unveraendert, weil `action_vec` den Greifpunkt als OFFSET
gegen den wahrgenommenen Bezug traegt, nicht als Weltkoordinate - unter einer Verschiebung ist sie
invariant.

# Fehlschlaege werden mitaugmentiert, und das ist geprueft

Die Idee-Seite fordert, ein Negativ nur so weit zu uebertragen, wie **seine Ursache erklaert ist**.
Das ist bereits erfuellt, bevor hier augmentiert wird: die Kredit-Zuordnung laesst nur ursaechlich
zugeordnete Ausgaenge durch ("Griff hielt nicht (Drucksensor)", "verrutscht"), waehrend "daneben
platziert" und "nicht gegriffen" als `outcome=None` gar nicht ankommen. Die Filterung sitzt eine
Stufe frueher.

# Die Voraussetzung, an der der erste Rauchtest scheiterte

`ACT23_NEIGHBOURS` steht per Vorgabe auf **0** - der NB-Block wird dann gar nicht gefuellt
(gemessen 11640 von 12330 Pufferzeilen ohne gueltigen Block,
[Befund](/befunde/merkmale-kommen-zu-spaet.md)). Die Zulaessigkeitsschranke liest genau ihn, also
oeffnet sie nie.

    erster Rauchtest, ACT23_NEIGHBOURS aus:   8 Episoden -> 8 Zeilen, 0 Vorstellungen

**Ein A/B haette zwei Stunden gekostet und exakt nichts gemessen.** Der Schalter warnt jetzt laut
beim Start. **Nicht** still mitgeschaltet: ein Schalter, der einen zweiten heimlich umlegt, macht
jedes A/B mehrdeutig - dann waere hinterher nicht zu trennen, ob die Augmentierung wirkte oder der
Nachbar-Block. Beide Arme eines A/B brauchen deshalb `ACT23_NEIGHBOURS=1`; das ist vertretbar, weil
der Block gemessen nichts kostet und nichts bringt (+0,004 AUC).

# Rauchtest

    8 Episoden, ACT23_AUGMENT=4 ACT23_NEIGHBOURS=1
      7 Episoden mit zugeschriebenem Ausgang, davon 6 augmentiert
      Weltzeilen 12322 -> 12353  (+31 statt +7)

    letzte 5 Zeilen = 1 echte + 4 vorgestellte
      |delta| zur echten Zeile   0,0 | 17,9 | 14,3 | 17,6 | 10,9 mm
      d_nah                     62,9 | 45,0 | 48,5 | 45,3 | 52,0 mm   (nie unter 40)
      Label                      0,419 durchweg   (graduierter Erfolg, unveraendert)
      alle uebrigen 43 Spalten   identisch
      Gewicht                    1,0 durchweg

**Rund 4,4 Pufferzeilen je physischer Episode statt einer.** Das ist die Zielgroesse, die vor dem
Bau festgelegt wurde - ausdruecklich nicht die Lieferquote, die bei dieser Nachweisgrenze nichts
sagen kann.

# Was NICHT gezeigt ist

**Dass ein Griff an der vorgestellten Lage geglueckt WAERE.** Die Daempfungsmessung zeigt, dass die
WAHRNEHMUNG der verschobenen Szene der Vorhersage entspricht - nicht, dass der Ausgang derselbe
gewesen waere. Das ist die eigentliche Behauptung der Augmentierung, und sie ist offen.

`ebene: code`. Ob die vervierfachten Zeilen dem Weltmodell nuetzen, sagt erst ein A/B - und die
sinnvolle Zielgroesse dort ist die **Generalisierungs-AUC** (`generalisation_auc`, blockweise
Halteteile), nicht die Quote.

# Verwandt

* [Die Daempfungsfunktion](/befunde/daempfungsfunktion.md) - woher jede Zahl im Bau stammt
* [Latente Augmentierung](/fragen/latente-augmentierung.md) - die Idee
* [Der Nachbar-Block steht auf 6 Prozent der Zeilen](/befunde/merkmale-kommen-zu-spaet.md) - die Voraussetzung
* [Invarianten](/mechanismen/invarianten.md) - "ein Schalter, der unbemerkt nichts tut"
