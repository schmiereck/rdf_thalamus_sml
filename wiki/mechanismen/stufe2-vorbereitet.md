---
type: Mechanismus
title: Stufe 2 vorbereitet - Sockel, dritte Zieldimension, Erfolgsbegriff
description: Drei Teile gebaut, alle auf Schaltern mit Vorgabe 0. Der Sockel als breites flaches Stapelziel, ACT16_GOAL_Z fuer eine Ablagehoehe im Ziel und im Zustandsvektor der Policy, ACT16_ERFOLG_RUHT fuer einen Erfolgsbegriff, der nicht "liegt auf dem Tisch" heisst. Enthaelt die Begruendung, warum die 14. Zustandsspalte NICHT verhaltensneutral ist, und die Migration, deren Neutralwert ausnahmsweise die Wahrheit ist.
tags: [act23, aufgabe, stapeln, policy]
status: stable
evidenz: gemessen
ebene: code
generated: { by: claude/opus-5, at: 2026-09-17T00:00:00Z }
sources:
  - id: entwurf
    resource: /fragen/stapeln-als-aufgabe.md
    title: Stapeln als neue Aufgabe - die vier Stufen
  - id: sockel
    resource: /befunde/sockel-verschluckt-den-stapel.md
    title: Was der Sockel misst
---

# Was gebaut ist

| Teil | Schalter | Vorgabe |
|---|---|---|
| `sockel`: 70 x 70 x 8 mm Platte, tiefblau, schwer, geparkt | (XML, immer da) | geparkt |
| Ablagehoehe im Ziel und im Zustandsvektor | `ACT16_GOAL_Z` | 0 |
| Erfolgsbegriff "ruht" statt "liegt tief" | `ACT16_ERFOLG_RUHT` | 0 |
| Ruheschwelle | `ACT16_RUHT_V` | 0,005 m/s |

# Der Sockel

**Breit**, weil die Ablagegenauigkeit gemessen 21-25 mm betraegt: 70 mm Kantenlaenge geben
35 - 12 = 23 mm Toleranz, ein Wuerfel auf einem Wuerfel nur 12 mm. **Flach**, weil der
Parallaxenversatz mit der Hoehe waechst. **Schwer** (Dichte 3000) und rauh, damit er nicht
verrutscht, aber mit Freejoint, damit `sim.set_object` ihn wie jeden anderen Koerper setzt.

**Tiefblau** (`0.05 0.05 1.0`): der Farbraum ist voll. Das ist der Ton mit dem groessten
Mindestabstand in der Chromatizitaet zu allen belegten - **0,292 zu obj_blue**, und damit weiter
getrennt als das engste bestehende Paar (0,220). Er steht bewusst **nicht** in `_FARB_KOERPER`:
die Episoden-Permutation darf ihm keine Objektfarbe geben, sonst faellt die Signatur aus
[Der Sockel verschluckt den Stapel](/befunde/sockel-verschluckt-den-stapel.md) zusammen.

> **Was die Messung an ihm geaendert hat:** er loest das Toleranzproblem und schafft ein neues -
> ein Koerper auf ihm ist **unsichtbar**, nicht bloss ungenau lokalisiert. Die Route dahinter ist
> die Farbstreuung, nicht die Position. Siehe den Befund.

# Die dritte Zieldimension (`ACT16_GOAL_Z`)

`goal_fn` darf jetzt **drei** Werte liefern; der dritte ist die Ablagehoehe der Hand. Die
Ablagephase zielt auf `tgt_z` statt auf die Konstante `GRASP_Z`, ebenso das weiche Loslassen.

> Bis hierhin war das Ziel **ueberall** zweidimensional - `GoalModule2D`, `goal_xy`, `marker_xy`,
> und im Zustandsvektor der Policy `tgt_eff[0], tgt_eff[1]`. **Die Policy konnte "lass hoeher los"
> nicht einmal ausdruecken.** Stapeln ist die erste Aufgabe, die das braucht.

**Warum das auf einen Schalter gehoert, obwohl der Wert ohne Stapelaufgabe konstant `GRASP_Z`
waere:** eine 14. Spalte im Zustandsvektor ist **keine verhaltensneutrale Ergaenzung**. Der
Vorwaertsdurchlauf bleibt zwar bitgleich - gemessen, `max |diff| = 0.0` ueber 40 Zeilen nach der
Migration - aber ein FRISCHES Netz wird mit anderer Breite gezogen, und jeder Refit sieht eine
Spalte mehr. Mit dem Schalter auf 0 bleibt der Zustand 13-dimensional und der Vorgabelauf
derselbe Lauf.

**Die Migration, und warum sie hier kein Gueltigkeits-Flag braucht.** Beim Tastsinn (11 -> 13)
musste eines mit: der Druck WAR in den alten Episoden physisch da, wurde aber nicht aufgezeichnet,
und "0 N" zu behaupten waere die Luege *"Klaue leer"* gewesen. Die Ablagehoehe dagegen **war** in
jeder alten Episode `GRASP_Z` - die Ablagephase zielte auf genau diese Konstante. Der Neutralwert
ist hier die **Wahrheit**, nicht ein Platzhalter.

**Einbahnstrasse:** ein Lauf mit dem Schalter migriert den Puffer der Zustandsdatei dauerhaft auf
14 Spalten. Nur auf Kopien fahren.

# Der Erfolgsbegriff (`ACT16_ERFOLG_RUHT`)

    alt   rested = cpos[2] < cmd_half[2] + 0,010        # woertlich: LIEGT AUF DEM TISCH
    neu   rested = Geschwindigkeit < RUHT_V  und  Klaue offen

Der alte Begriff verbucht **jeden gelungenen Stapel als Fehlschlag**. Der neue ist von der Aufgabe
unabhaengig und gilt fuer die alte genauso: er verlangt nur, dass die Sendung angekommen und zur
Ruhe gekommen ist, nicht wie hoch sie liegt. Die zweite Bedingung ist noetig, weil ein Objekt auch
in der Klaue ruht.

Vorgabe bleibt 0, bis die **Uebereinstimmung der beiden Begriffe** gemessen ist - ein noch
rollendes Objekt gilt jetzt als nicht geliefert, und das kann die alte Messreihe verschieben.

# Verifikation

* **Migration bitgleich:** 40 Zeilen 13 -> 14, Netz mit Nullspalten verbreitert, Vorwaertsdurchlauf
  `max |diff| = 0.0`, angehaengter Wert exakt `GRASP_Z`, Port-Dimension 14.
* **Vorgabepfad:** 5 frische Episoden (Seed 4242) gegen den Stand davor, gefahren aus einem
  `git worktree` auf `84a5d71`, damit Code UND Assets der alte Stand sind. Befehle identisch,
  Ausgaenge identisch, 4 von 5 Episoden millimetergenau gleich, eine 87 gegen 89 mm.
* **Nicht bitgleich - und die Ursache ist gemessen**, s. naechster Abschnitt.

# Die Falle, die dieser Einbau zutage gefoerdert hat

**Ein zusaetzlicher Koerper im Modell veraendert das gerenderte Bild, immer.** Zustand bitgleich
(`qpos` und `qvel` Zeichen fuer Zeichen identisch), Bild nicht: **2 von 57.600 Pixeln**, +44 im
Rotkanal an der Silhouettenkante des roten Wuerfels. Der Effekt bleibt **unveraendert 2 Pixel**,
wenn man den Sockel voellig durchsichtig, winzig oder in eine ausgeblendete Geom-Gruppe setzt - es
ist der Szenengraph, nicht sein Aussehen. Die ganze Wahrnehmung haengt am Bild, also driften zwei
Laeufe danach auseinander (im Warmup ab Schritt ~100, `sensor_err` 40,05 gegen 40,04).

> **Wer einen Koerper hinzufuegt, kann keinen Lauf mehr bitweise mit einem Lauf von davor
> vergleichen. Beide Arme eines A/B muessen dieselbe XML fahren.**

Steht jetzt in den [Invarianten](/mechanismen/invarianten.md).

# Was noch fehlt, bevor Stufe 2 gefahren werden kann

1. **`RELATION := auf`** in der Sprache - die Zieladresse liefert dann drei statt zwei Werte.
2. **Woher die Hoehe kommt.** Sie ist mit der flachen Wahrnehmung nicht messbar. Nach
   [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) ist der zulaessige Weg: der **Teacher**
   demonstriert die Ablagehoehe (privilegiert, wie `WRIST_ALIGN`), die Policy lernt sie aus der
   Wahrnehmung - und zur Testzeit verschwindet die Regel.
3. **Der Selbstrichter.** Er muss "A liegt auf B" aus der Farbstreuung lesen koennen, sonst
   beurteilt der Agent seinen eigenen Stapel nicht und die Selbst-Imitation bekommt falsche
   Etiketten.
4. **Der Transport muss ein Ziel aushalten, an dem ein Koerper steht.** -- **GEMESSEN**, s.
   [Der Arm hat einen Mindestabstand von rund 37 mm](/befunde/mindestabstand-zur-ablage.md). Er
   haelt es nicht aus: bei 90 mm Soll trifft er auf 0,5 mm genau, bei 30 mm legt er in 93 % der
   Faelle 20 mm zu weit weg ab, und ueber 254 Ablagen landen nur 1,2 % naeher als 20 mm an einem
   Koerper. **Die Drift nach dem Loslassen aendert sich dabei nicht** - das Objekt wird nicht
   weggestossen, sondern gar nicht erst hingebracht. Naechstliegende Ursache: die Saeuberungsregel
   hat ueber die gesamte Vorgeschichte garantiert, dass NIE ein Ziel naeher als 50 mm an einem
   Koerper lag - **die Regel, die das Stapeln verbietet, hat auch die Daten verhindert, mit denen
   man es lernen koennte.**

**Punkt 4 ist beantwortet und aendert die Reihenfolge:** vor allem anderen braucht Stufe 2 eine
Trainingsphase OHNE `ZIEL_SAEUBERN`, damit der Teacher nahe Ablagen ueberhaupt vorfuehrt. Offen
bleibt die Trennung der beiden Ursachen (Trainingsverteilung gegen Klauenmechanik); sie haengt an
einer billigen Frage - **bewegt sich der Bezugskoerper?**

# Verwandt

* [Der Sockel verschluckt den Stapel](/befunde/sockel-verschluckt-den-stapel.md) - die Messung am Sockel
* [Stapeln als neue Aufgabe](/fragen/stapeln-als-aufgabe.md) - die vier Stufen
* [Das Ablageziel als Adresse](/mechanismen/ziel-als-adresse.md) - Stufe 1
* [Die Zieladresse traegt](/befunde/ziel-als-adresse-gemessen.md) - woher Punkt 4 kommt
* [Invarianten](/mechanismen/invarianten.md) - die Renderer-Falle
* [Merkmale kommen zu spaet](/befunde/merkmale-kommen-zu-spaet.md) - warum eine neue Spalte im Lifelong-Puffer ein eigenes Problem ist
