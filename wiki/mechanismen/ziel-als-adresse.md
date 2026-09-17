---
type: Mechanismus
title: Das Ablageziel als Adresse - ACT23_ZIEL_ADRESSE
description: Stufe 1 von "Stapeln als neue Aufgabe", gebaut. Der Zielplatz bekommt denselben Typ wie das Objekt, naemlich eine Eigenschafts-Adresse, und wird aus der eigenen Kamera aufgeloest statt aus mocap_pos gelesen. Damit verliert das Kommando sein letztes Privileg. Bewusst OHNE Hoehe - abgelegt wird NEBEN dem Bezugskoerper, der Erfolgsbegriff bleibt unveraendert, gemessen wird allein die Sprachaenderung.
tags: [act23, kommando, aufgabe, stapeln]
status: stable
evidenz: gemessen
ebene: code
generated: { by: claude/opus-5, at: 2026-09-17T00:00:00Z }
sources:
  - id: entwurf
    resource: /fragen/stapeln-als-aufgabe.md
    title: Stapeln als neue Aufgabe - der Entwurf, dessen Stufe 1 das hier ist
---

# Was gebaut ist

`ACT23_ZIEL_ADRESSE=1` (Vorgabe 0) macht aus dem Ablageziel eine **Adresse**:

    BEFEHL := ADRESSE  AKTION  BEZUG
    BEZUG  := ORT | RELATION ADRESSE
    RELATION := an                      -- Stufe 1; "auf" braucht eine Hoehe und ist Stufe 2

Ein Befehl liest sich dann *"nimm das duenne violette Kreuz und lege es NEBEN den blauen
Wuerfel"*. Der Bezug wird je Episode gewuerfelt und beim Abholen des Ziels aus der **Kamera**
aufgeloest.

# Warum das mehr ist als eine Bequemlichkeit

> Das Ablageziel war das **einzige Stueck des Befehls, das der Agent nicht wahrgenommen hat**.
> `state.goal_fn` lieferte `marker_xy(target_idx)`, und das liest `sim.d.mocap_pos` - eine
> privilegierte Designer-Koordinate. Mit einer Zieladresse laeuft es durch
> `finde_nach_eigenschaften`, also durch dieselbe Wahrnehmung wie das Objekt.

Das zaehlt nach [Projektziel](/ziel.md) fuer sich, unabhaengig von jeder Quote.

# Die Teile

| Stelle | was sie tut |
|---|---|
| `ZIEL_ADRESSE`, `ZIEL_ABSTAND` | Schalter (0) und Ablageabstand (0,05 m) |
| `CommandState23.ziel_modus` | `"ort"` (Marker, wie bisher) oder `"koerper"` (Bezug) |
| `CommandState23.ziel_bezug` | der Wurf DIESER Episode: Tripel, Messwerte, Peilungen, Bezugskoerper |
| `_ziel_adresse_wuerfeln()` | waehlt den Bezugskoerper und wuerfelt seine Adresse |
| `_ziel_aufloesen()` | findet ihn in der Szene wieder und gibt die Stelle DANEBEN zurueck |
| `CommandState23.goal_fn` | ruft den Aufloeser, faellt sonst auf den Marker zurueck |
| Knopf "Ziel: an Körper" | derselbe Umschalter in der GUI, mit sofortigem Wurf |

**Wurf und Aufloesung sind getrennt**, und das ist Absicht: der Wurf legt fest, WAS gesagt wird,
die Aufloesung findet es in der Szene wieder. Nur der zweite Schritt laeuft im Vollzug, und nur er
muss privilegienfrei sein.

# Die Entscheidungen, die nicht offensichtlich sind

**Warum NEBEN und nicht AUF.** Ein Ziel auf einem Koerper ist mit der heutigen Wahrnehmung nicht
beurteilbar: die Homographie ist eine Ebenen-Abbildung, ein gestapelter Wuerfel liest
[15,9 mm daneben](/befunde/stapeln-bricht-die-tischebene.md), und der Erfolgsbegriff heisst
woertlich *"liegt auf dem Tisch"*. Stufe 1 laesst beides unveraendert, damit **allein die
Sprachaenderung** gemessen wird.

**Warum 0,05 m.** Das ist keine neue Zahl, sondern dieselbe, mit der `run_combined` seit jeher
jedes Ziel von jedem Koerper wegschiebt (`clear(tgt, OBJS, 0.05)`). Damit bleibt die Saeuberung
wirkungslos statt zu stoeren, und ein geliefertes Objekt beruehrt den Bezugskoerper nicht.
`ACT23_ZIEL_ABSTAND` macht den Abstand verstellbar - man braucht ihn als Kontrolle, s. Fallen.

**Warum die Peilung gewuerfelt wird.** Ein fester Versatz waere eine geskriptete Konvention
("immer oestlich"). Gewuerfelt werden acht Richtungen ab einem zufaelligen Winkel; die erste
erreichbare gewinnt. Das ist dasselbe, was die Marker-Vorgabe mit `place_selected_random` ohnehin
tut.

**Warum die Adresse hier die FARBE nennen darf.** Sie wird **jede Episode neu gewuerfelt**, nach
`_farbe_wuerfeln`, und gilt genau fuer diese eine Episode.
[Eine dauerhafte Adresse darf keine Farbe nennen](/befunde/dauer-adresse-vertraegt-keine-farbe.md)
trifft nur DAUERHAFTE Adressen - derselbe Grund, aus dem `_auto_eig_umschreiben` nie betroffen war.

**Warum mehrdeutig wie nicht gefunden behandelt wird.** Passt die Adresse auf mehrere Detektionen,
wird NICHT die flaechengroesste genommen. Genau das hat in der Objekt-Adressierung 152 mm
danebengegriffen; "eindeutig ist nicht richtig" steht seit
[Adressfehler sind Verschmelzung](/befunde/adressfehler-sind-verschmelzung.md) im Wiki. Der
Rueckfall auf den Marker wird **laut** protokolliert, sonst waere eine still zurueckgefallene
Episode in der Auswertung von einer geloesten nicht zu unterscheiden.

**Die Marker muessen zurueckgelegt werden.** `perceive_all` parkt sie; ohne Wiederherstellung
liefert ausgerechnet der Rueckfall `marker_xy()` eine **geparkte** Koordinate. Dieselbe Falle wie
in `_adresse_wuerfeln`, deshalb dasselbe Sichern/Zuruecklegen von `mocap_pos`.

# Verifikation

**Der Vorgabepfad ist unveraendert.** Fuenf frische kopflose Episoden (`ACT23_FRESH=1`, Seed 4242)
gegen denselben Lauf auf dem Stand vor dem Einbau (`git show HEAD:...`): **64 Inhaltszeilen,
0 Unterschiede** - jede Episode, jede Entscheidung, jeder Abstand gleich. Ohne
`ACT23_ZIEL_ADRESSE` kehrt `_ziel_adresse_wuerfeln` sofort zurueck, ohne eine einzige Zufallszahl
zu ziehen, und `goal_fn` liefert wie zuvor `marker_xy`.

Die 18 Kopfzeilen unterscheiden sich, und zwar vollstaendig erklaerbar: der Vergleichsstand lief
aus dem Scratchpad, also fand `_source_defaults()` (es liest die Dateien NEBEN `__file__`) keine
Vorgaben und meldete jeden Schalter als "keine Vorgabe im Quelltext"; aus demselben Grund ist die
`Kern`-Zeile kuerzer und die Commit-Zeile eine andere. Das ist ein Artefakt des Messaufbaus, kein
Verhaltensunterschied - **beim Vergleich zweier act23-Staende muss der Vergleichsstand IM
Paketverzeichnis liegen**, sonst weicht der Kopf immer ab.

Rauchtest mit dem Schalter, vier Episoden auf einer Kopie des gelernten Zustands: **4 von 4
Zieladressen eindeutig aufgeloest**, der Bezugskoerper auf 1-5 mm genau wahrgenommen, die Ablage
jeweils 50 mm daneben und im Arbeitsraum.

# Fallen

* **Die Aufgabe wird geometrisch schwieriger, und zwar aus einem SCHON GEMESSENEN Grund.** Ein Ziel
  50 mm neben einem Koerper legt die Ablage in die Zone, in der
  [Nachbarnaehe die Quote um 13,9 Punkte druckt](/befunde/nachbarnaehe-im-lauf.md) (Schwelle
  55 mm). Ein Quotenverlust in einem A/B waere damit **nicht** ohne Weiteres der Sprache
  zuzuschreiben. Die noetige Kontrolle ist billig und eingebaut: derselbe Arm mit
  `ACT23_ZIEL_ABSTAND=0.09` liegt ausserhalb der Zone.
* **Das Ziel wird nach `goal_fn` noch gesaeubert** (act16:382-394). Faellt die Ablagestelle unter
  50 mm an einen ANDEREN Koerper oder zu nah an den Sockel, verschiebt `run_combined` sie - das
  Protokoll zeigt die Stelle VOR der Saeuberung.
* **Der Bezugskoerper wird privilegiert AUSGEWAEHLT** (`sim.obj_pos`, um die Detektion auf ihm zu
  finden und die Identitaet zu pruefen). Das ist Aufgabenerzeugung wie die Wahl des Objekts, genau
  wie in `_auto_eig_umschreiben`; im Vollzug wird nichts Privilegiertes gelesen. Die "wahr"-Angabe
  im Protokoll ist reine Messung.
* **Stufe 1 stapelt nicht.** Wer eine Stapelaussage sucht, braucht Stufe 2 und 3 aus
  [dem Entwurf](/fragen/stapeln-als-aufgabe.md).
* **Vorgabe bleibt 0.**

# Verwandt

* [Stapeln als neue Aufgabe](/fragen/stapeln-als-aufgabe.md) - der Entwurf mit allen vier Stufen
* [Ein gestapelter Koerper liest 16 mm daneben](/befunde/stapeln-bricht-die-tischebene.md) - warum Stufe 1 ohne Hoehe bleibt
* [Die Adresse ohne Klasse](/mechanismen/adresse-ohne-klasse.md) - der Adresstyp, den das Ziel erbt
* [Nachbarnaehe im Lauf](/befunde/nachbarnaehe-im-lauf.md) - der Konfounder, den ein A/B kontrollieren muss
* [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) - die Maschinerie dahinter
