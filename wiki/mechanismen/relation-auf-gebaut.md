---
type: Mechanismus
title: Die Relation "auf", gebaut - ACT23_ZIEL_RELATION=auf
description: Stufe 2 steht. Das Ablageziel kann jetzt AUF einem Koerper liegen statt daneben - dieselbe Adresse, aber ohne Peilung und mit einer dritten Groesse, der Ablagehoehe. Sie ist GRASP_Z plus Oberkante der Auflage und das einzige Privileg auf diesem Pfad, zulaessig als Teacher-Geruest. Vier fremde Schalter muessen mit, und der Bau sagt laut, welcher fehlt. Rauchtest: zwei saubere Stapel in vier adressierten Episoden.
tags: [act23, kommando, aufgabe, stapeln]
status: stable
evidenz: gemessen
ebene: code
generated: { by: claude/opus-5, at: 2026-09-18T00:00:00Z }
sources:
  - id: entwurf
    resource: /fragen/stapeln-als-aufgabe.md
    title: Stapeln als neue Aufgabe
  - id: anlass
    resource: /befunde/nahe-ablage-ist-mechanik.md
    title: Warum "auf" vor "an" kommt
---

# Was gebaut ist

    BEZUG    := ORT | RELATION ADRESSE
    RELATION := an | auf          <- ACT23_ZIEL_RELATION, Vorgabe "an"

Ein Befehl liest sich jetzt *"nimm das duenne violette Kreuz und lege es AUF die blaue Platte"*.
Gegenueber `an` fallen zwei Dinge weg und eines kommt hinzu: **keine Peilung**, **kein Abstand**,
dafuer eine **dritte Zielgroesse** - die Ablagehoehe der Hand.

| Teil | Schalter | Vorgabe |
|---|---|---|
| die Relation | `ACT23_ZIEL_RELATION` | `an` |
| der Sockel in der Szene | `ACT23_SOCKEL` | 0 |
| seine Stelle | `ACT23_SOCKEL_XY` | `-0.018,0.149` (gesucht, s. unten) |
| `state.STUETZEN` | - | Moebel, nie kommandiert |

# Warum "auf" VOR "an" kommt

Die urspruengliche Stufenfolge hatte es umgekehrt. Gemessen ist die Sperre aber **lateral**: der
Arm kommt einem Koerper nicht naeher als ~37 mm, weil die Klaue NEBEN ihm absenken muss und dabei
in 64 % der Faelle gegen ihn stoesst - der **untrainierte Teacher genauso wenig wie die Policy**
([Der Mindestabstand ist die Mechanik](/befunde/nahe-ablage-ist-mechanik.md)).

> Beim Stapeln liegt der Bezugskoerper **unter** dem getragenen Objekt und gar nicht im Absenkweg.
> "auf B" ist damit der mechanisch **leichtere** Fall.

# Die Ablagehoehe, und das einzige Privileg auf diesem Pfad

    tgt_z = GRASP_Z + Oberkante des Bezugskoerpers

`GRASP_Z` (0,014) ist die HANDhoehe, bei der ein Koerper mit Ruhemitte 0,012 abgelegt wird, also
Handhoehe = Ruhemitte + 0,002. Steht der Koerper auf einer Auflage der Hoehe h, liegt seine
Ruhemitte bei h + 0,012 und die Hand bei `GRASP_Z + h`. Alle Koerper dieser Welt sind 24 mm hoch,
der Aufschlag ist deshalb fuer alle derselbe.

**Die Oberkante kommt aus dem Simulator.** Sie muss, denn eine Ebenen-Homographie gibt keine Hoehe
her. Nach [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) ist das als **Teacher-Geruest**
zulaessig - wie `WRIST_ALIGN` - und muss zur Testzeit verschwinden: die Policy hat die Hoehe seit
`ACT16_GOAL_Z` als 14. Eingang im Zustandsvektor und soll sie lernen. **Solange sie das nicht kann,
ist ein "auf"-Lauf ein Teacher-Lauf**, und das ist auf dieser Seite die ehrliche Bezeichnung.

Die Hoehe steht bewusst **nicht** in der Adresse und nicht im Ziel-Latent: eine Adresse nennt
Eigenschaften des Koerpers, und eine Hoehe ist keine.

# Vier fremde Schalter muessen mit - und der Bau sagt, welcher fehlt

`auf` ist ohne sie nicht wirkungslos, sondern **still falsch**. Deshalb prueft der Start und meldet
jeden einzeln:

| fehlt | Folge |
|---|---|
| `ACT16_GOAL_Z=1` | die dritte Zielgroesse wird verworfen, die Klaue faehrt auf Greifhoehe IN den Bezugskoerper |
| `ACT16_ZIEL_SAEUBERN=0` | `run_combined` schiebt das Ziel um 0,05 m weg, aus "auf" wird "daneben" |
| `ACT16_ERFOLG_RUHT=1` | "geliefert" heisst woertlich "liegt auf dem Tisch", jeder gelungene Stapel zaehlt als Fehlschlag |
| `ACT23_SOCKEL=1` | es gibt keine Stuetze, jede Episode faellt auf den Marker zurueck |

Kein Schalter legt einen anderen heimlich um - dieselbe Regel wie bei `AUGMENT`/`NEIGHBOURS` und
`EIG_DIREKT`: ein Schalter, der einen zweiten mitzieht, macht jedes A/B mehrdeutig.

# Stuetzen sind Moebel, keine Objekte

`state.STUETZEN` ist getrennt von `state.OBJECTS`. Ein Sockel in `OBJECTS` waere **kommandierbar**,
und die Neugier koennte ihn zum Greifen auswaehlen - 70 mm breit und mit Dichte 3000. Er wird
deshalb nur von der Szene aufgebaut, in den Posen-Schnappschuss aufgenommen (damit die
Aufraeumschleife ihn zurueckstellt, sonst wandert die Auflage ueber den Lauf davon) und als
Bezugskoerper fuer `auf` angeboten.

# Die Stelle ist gesucht, nicht geraten

Der Startcheck rechnet den Freiraum zu jedem Objekt-Slot nach und vergleicht ihn mit der
**gemessenen** Schranke von 80 mm; liegt er knapp, sucht er die beste Stelle im Raster und nennt
sie samt passender Szenengroesse. Warum das noetig war und warum die erste Schranke (66 mm) falsch
gerechnet war: [Der Sockel braucht 80 mm Freiraum](/befunde/sockel-braucht-80mm-freiraum.md).
Kurz: mit einem Sockel sind hoechstens **vier** Objekte moeglich.

# Rauchtest

Sechs Episoden auf einer Zustandskopie, Teacher fahrend, alle vier Schalter gesetzt:

    [Sockel] steht bei [-0.018,+0.149], naechster Objekt-Slot 86 mm (gemessen noetig 80 mm)
    [Zieladresse] 'auf farbe-14 + dick' 1 Treffer bei [-0.022,+0.142] (wahr 8mm)
                  -> DARAUF ablegen, Oberkante 8mm, Handhoehe 22mm
    [Ablage] obj_blue: ... | Stapel: Objektmitte 19mm (Auflage 8mm), Versatz 14mm -> LIEGT DRAUF

**Zwei saubere Stapel in vier adressierten Episoden**, Versatz 14 und 20 mm, beide als geliefert
gezaehlt. Der Sockel wurde auf 1-8 mm wahrgenommen.

Das ist ein Rauchtest, **keine Quote**: n = 6, ein Seed, Teacher fahrend, und das Stapelurteil
(`LIEGT DRAUF`) ist privilegiert gemessen (Objektmitte ueber der Auflage, Versatz unter 23 mm).

# Was als naechstes zu messen ist

1. **Ein A/B gegen die Marker-Ablage** - traegt die Aufgabe ueberhaupt, und was kostet sie?
2. **Ob die Policy die Hoehe lernt.** Das ist der Punkt, an dem das Teacher-Geruest fallen muss:
   Vergleich mit `ACT23_CHOREO=netz` nach genuegend Teacher-Episoden. Solange die Policy die
   14. Spalte nicht nutzt, legt sie auf Greifhoehe ab und schiebt den Stapel um.
3. **Der Selbstrichter.** Er sieht einen Stapel nicht als zweite Detektion, sondern nur als
   Farbstreuungs-Anomalie - ohne ihn bekommt die Selbst-Imitation falsche Etiketten.

# Verwandt

* [Der Sockel braucht 80 mm Freiraum](/befunde/sockel-braucht-80mm-freiraum.md) - die zwei Messungen, die diesen Bau konfigurieren
* [Der Mindestabstand ist die Mechanik](/befunde/nahe-ablage-ist-mechanik.md) - warum "auf" vor "an" kommt
* [Das Ablageziel als Adresse](/mechanismen/ziel-als-adresse.md) - Stufe 1, von der `auf` alles erbt
* [Stufe 2 vorbereitet](/mechanismen/stufe2-vorbereitet.md) - `ACT16_GOAL_Z`, `ERFOLG_RUHT`, der Sockel
* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) - warum die Oberkante ein zulaessiges Geruest ist
