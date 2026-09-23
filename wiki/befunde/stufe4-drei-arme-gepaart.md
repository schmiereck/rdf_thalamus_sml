---
type: Befund
title: Drei Arme je Episode gepaart - weder die Sichtbarkeit noch die Relation traegt messbar, und der Test war fuer die Kontrolle zu leicht
description: Die richtige Kontrolle fuer Stufe 4, als erste Anwendung der Episoden-Paarung. 89 von 90 Episoden sind in allen drei Armen szenengleich. Ohne Chroma-Schnitt 34 Prozent, mit Schnitt und Eigenschafts-Adresse 37, mit Schnitt und relationaler Adresse 43 - kein paarweiser Unterschied ist signifikant (McNemar p = 0,65 / 0,38 / 0,20). Die vorher aufgeschriebene Erwartung, der Sprung liege bei der Sichtbarkeit, ist FALSCH. Der Trichter zeigt warum - auch der Arm, fuer den der Stapel unsichtbar ist, greift den gestapelten Koerper in 51 von 90 Episoden. Vermutung, nicht gemessen - der Abstapel-Aufbau stellt den Koerper genau in die Plattenmitte, sodass der Schwerpunkt des verschmolzenen Flecks auf ihm liegt; der Test macht die Relation damit ueberfluessig.
tags: [act23, stapeln, sprache, gepaart, negativ, messen]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-09-23T00:00:00Z }
sources:
  - id: lauf
    resource: "Kopflose Laeufe auf Kopien von act23_state.pkl (ad9d768c): gemeinsamer warmer Hoehenschaetzer (40 Ep, 23 Tastwerte) in alle Arme verpflanzt; Seeds 9101-9103 je 30 Ep, ACT23_SZENE_JE_EPISODE=1 ACT23_AUTO_CURIOUS=0 ACT23_ABSTAPELN=1 ACT23_CHOREO=fsm ACT23_SOCKEL_N=1; K0 ACT_SHAPE_CHROMA_SPLIT=0, K1 Schnitt+Konzentrisch, K2 Schnitt+Konzentrisch+ACT23_ADR_RELATION=1; hoechstens zwei Prozesse gleichzeitig"
    title: Die drei gepaarten Arme
  - id: sweep
    resource: /befunde/stufe4-sweep-widerlegt.md
    title: Der Sweep, aus dem diese Kontrolle folgte
---

# Die Frage

Der [Sweep](/befunde/stufe4-sweep-widerlegt.md) hat nur die ADRESSE verglichen; der Chroma-Schnitt,
der den Stapel ueberhaupt sichtbar macht, lief in beiden Armen. Hier die vollstaendige Zerlegung:

    K0  ohne Chroma-Schnitt, Eigenschafts-Adresse   -- der Stapel ist unsichtbar (0 von 25)
    K1  mit  Chroma-Schnitt, Eigenschafts-Adresse   -- sichtbar, gewoehnlich adressiert
    K2  mit  Chroma-Schnitt, relationale Adresse    -- Stufe 4 vollstaendig

**Vorher aufgeschriebene Erwartung** (Chat und Board, 2026-09-23 10:00): der Sprung liegt zwischen
K0 und K1 (Sichtbarkeit), zwischen K1 und K2 wenig bis nichts.

# Die Paarung haelt

    Episoden gesamt                                  90
    davon in ALLEN DREI Armen szenengleich           89   (1 ausgeschlossen)

Geprueft ueber den `[Szenen-Abdruck]`, nicht vorausgesetzt - und zwar auch zwischen K0 und K1, die
verschieden WAHRNEHMEN. Die [Episoden-Paarung](/messungen/act23-headless-ab.md) ist damit im Einsatz
bestaetigt.

# Ergebnis

    Arm   geliefert
    K0    30 von 89 = 34 %
    K1    33 von 89 = 37 %
    K2    38 von 89 = 43 %

    McNemar auf den abweichenden Paaren (Bonferroni-Schranke 0,0167):
      K0 gegen K1   nur K0  8 | nur K1 11   ->  p = 0,65
      K1 gegen K2   nur K1  8 | nur K2 13   ->  p = 0,38
      K0 gegen K2   nur K0 11 | nur K2 19   ->  p = 0,20

    je Seed:  9101  K0 15  K1 14  K2 17
              9102  K0 11  K1 11  K2 11
              9103  K0  4  K1  8  K2 10

**Kein paarweiser Unterschied ist signifikant. Meine Erwartung war falsch:** der Schritt von K0 zu
K1, die Sichtbarkeit, bringt 3 Punkte und keinen nachweisbaren Unterschied. Die Richtung
K0 < K1 < K2 ist durchgaengig, aber klein.

# Warum: auch der Arm ohne Sichtbarkeit greift den Stapel

    Arm   gegriffen >1 N   gehoben >1 N   losgelassen   geliefert
    K0          51              44            57            30
    K1          51              38            49            33
    K2          41              51            63            38

**K0 greift den gestapelten Koerper in 51 von 90 Episoden - obwohl er fuer diesen Arm gar keine
eigene Detektion hat.** Die Unsichtbarkeit, die auf dem Pruefstand gemessen war
([0 von 25](/befunde/sockel-verschluckt-den-stapel.md)), ist im Lauf keine Huerde.

## Vermutung, nicht gemessen: der Test macht die Relation ueberfluessig

Der Abstapel-Aufbau (`ACT23_ABSTAPELN`) stellt den Koerper **genau in die Mitte der Platte**. Damit
liegt der Schwerpunkt des verschmolzenen Flecks - Platte plus Koerper, das Einzige, was K0 sieht -
praktisch auf dem Koerper. Die gewoehnliche Adresse findet den verschmolzenen Fleck, zielt auf
seinen Schwerpunkt und trifft damit den Koerper, ohne ihn je gesehen zu haben.

**Pruefbar mit einem Stapel ausserhalb der Mitte.** Rechnerisch verschiebt ein Koerper von ~250 px
auf einer Platte von ~1400 px den Fleckschwerpunkt nur um rund ein Sechstel seines eigenen
Versatzes: bei 20 mm Versatz zielte K0 also etwa 16 mm neben den Koerper, waehrend K1 und K2 ihn
als eigenen Teil sehen. Erst dort muesste sich zeigen, ob Sichtbarkeit und Relation etwas tragen.

# Was die abweichenden Paare zusaetzlich zeigen

Auf **identischer Szene** gehen K0 und K1 in 19 von 89 Episoden verschieden aus - 8-mal zugunsten
von K0, 11-mal zugunsten von K1. Eine Wahrnehmungsaenderung kippt den Ausgang also in rund einem
Fuenftel der Episoden, und zwar **in beide Richtungen fast gleich oft**. Das ist keine Wirkung,
sondern die Empfindlichkeit der Ausfuehrung gegenueber kleinen Unterschieden - und es relativiert
die erste Pruefung der Paarung, bei der 10 von 10 Paaren gleich ausgingen: bei 21 abweichenden Paaren
unter 89 war das Zufall.

# Fallen

* **Kein Befund gegen den Mechanismus.** Die Adresse loest auf, der Arm greift richtig hoch - das
  steht unveraendert. Gemessen ist, dass die AUFGABE in dieser Form den Mechanismus nicht braucht.
* **Trennschaerfe.** K0 gegen K2 steht bei 11 zu 19 abweichenden Paaren. Waere das Verhaeltnis echt,
  braeuchte ein Nachweis etwa die dreifache Datenmenge. Das Nicht-Signifikant ist also auch eine
  Frage der Fallzahl - aber bei 9 Punkten Abstand ueber drei Arme hinweg kein vielversprechender.
* **Ein gemeinsamer Hoehenschaetzer**, nur von K2 benutzt. K0 und K1 greifen auf Tischhoehe
  (sie liefern zwei Werte an `run_combined`, nicht drei) - und schaffen es trotzdem in rund der
  Haelfte der Episoden, den Koerper zu heben. Wie, ist nicht untersucht.
* **Drei Seeds, 30 Episoden.** Die Streuung zwischen den Seeds (K0: 4 bis 15 von 30) ist durch die
  Paarung aus dem VERGLEICH genommen, aber nicht aus den absoluten Quoten.

# Verwandt

* [Der gepaarte Sweep](/befunde/stufe4-sweep-widerlegt.md) - aus dem diese Kontrolle folgte
* [Gepaart je Episode](/messungen/act23-headless-ab.md) - das Werkzeug, hier erstmals im Einsatz
* [Der Stapel wird sichtbar](/befunde/stapel-wird-sichtbar.md) - die Sichtbarkeit, deren Wirkung hier nicht nachweisbar ist
* [Der Sockel verschluckt den Stapel](/befunde/sockel-verschluckt-den-stapel.md) - die Pruefstands-Unsichtbarkeit, die im Lauf keine Huerde ist
* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - Stufe 4
