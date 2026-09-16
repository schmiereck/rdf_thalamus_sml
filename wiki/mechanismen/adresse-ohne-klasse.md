---
type: Mechanismus
title: Die Adresse ohne Klasse - eine Sichtung statt Geburt, Bestaetigung und Knopf
description: ACT23_EIG_DIREKT laesst den Lebenszyklus der Formklasse zum ersten Mal WEG, statt ihn zu ergaenzen. Ein Koerper ohne Eintrag, der in der Szene steht, wird aus EINER Detektion adressierbar - Chromatizitaet, Formeinbettung, Spanne. Diskret ist das verschlossen, weil resolve() fuer eine unbekannte Form keinen Namen liefert. Der Vorgabepfad bleibt zeichengenau unveraendert; auf dem gespeicherten Zustand des Nutzers findet der Schalter allerdings nichts vor, weil alle sieben Koerper laengst vergeben sind.
tags: [act23, kommando, latent, selbstlernen]
status: stable
evidenz: gemessen
ebene: code
generated: { by: claude/opus-5, at: 2026-09-16T00:00:00Z }
sources:
  - id: bau
    resource: src/pc_cvnn/pc_act23.py
    title: "_direkt_adressieren, _adresse_wuerfeln, _probe_entdeckt, EIG_DIREKT/EIG_GESEHEN"
  - id: gleich
    resource: "Zwei kopflose Laeufe je 12 Episoden, Vorgaben, Seed 4242, HEAD gegen Arbeitsstand"
    title: Gleichheitsprobe des Umbaus
  - id: anlass
    resource: /befunde/stetige-adressierung-im-lauf.md
    title: Der Befund, der diesen Schritt als naechsten benennt
---

# Warum

[Die stetige Adressierung](/befunde/stetige-adressierung-im-lauf.md) ist gebaut, verifiziert und
**neutral** - weil sie ADDITIV war: sie adressiert das Gemessene, aber die Formklassen entstehen
daneben weiter, bekommen weiter Knoepfe und verhungern weiter. Der erhoffte Gewinn sollte gerade
aus deren WEGFALL kommen, und solange sie danebenstehen, kann er nicht eintreten.

Hier faellt der Lebenszyklus zum ersten Mal weg:

    bisher   3 Sichtungen -> Klassengeburt -> 3 von 6 Blicken -> Knopf -> kommandierbar
    jetzt    1 Sichtung   -> Adresse       -> kommandierbar

# Der Bau

`_direkt_adressieren(dets)` ist das Gegenstueck zu `_try_bind` und laeuft im **selben Blick**
(`_scene_glance`), kostet also kein zusaetzliches Rendern. Es sucht Koerper, die in der Szene
stehen und **keinen Eintrag in `state.OBJECTS`** haben, und baut aus der Detektion eine Adresse:
Chromatizitaet, `desc_embed`, Spanne. Danach `add_eigenschaft` plus `EIG_MESS` - und derselbe
Zweizeiler in `act16.OBJS`/`SCENE_N`, mit dem `_try_bind` einen Knopf in die Szenenverwaltung
haengt.

**Der Koerper-Handle ist Verkabelung, kein Privileg.** Er beantwortet nur *"zu welchem Eintrag
gehoert diese Detektion"*, fuer Buchfuehrung und Szenenverwaltung. Die Adresse besteht
ausschliesslich aus Gemessenem, und die spaetere Lokalisierung sieht den Namen nie. Genauso
arbeiten `_try_bind`, die Farbbindung und `_namenlose_kandidaten` seit jeher.

## Drei Stellen, an denen es sonst gebrochen waere

**Der Platzhalter `~gesehen`.** `resolve()` liefert fuer eine unbekannte Form `(None, d)` - es gibt
schlicht keinen Namen, den die Formachse nennen koennte. **Genau daran ist dieser Weg diskret
verschlossen.** `_eig_passt` liest `namen[i] is not None` als *"diese Achse ist genannt"* und
vergleicht dann den Messwert; der Name wird beim stetigen Matchen nirgends gelesen. Der
Platzhalter traegt also nur die Anzeige und sagt dort das Richtige. Die eine Stelle, die ihn als
Klasse lesen WUERDE, ist der Fovea-Tracker - dort wird er uebersprungen und faellt auf den
Farb-Tracker durch, sonst ehrlich auf `servo=False`. Eine Fovea, die dem Einbettungsvektor selbst
folgt, existiert nicht; das waere ein eigener Bau.

**`_probe_entdeckt()`.** Der Neuheits-Erzeuger prueft `NOVEL_BODY in state.SHAPE_KEY`. Eine
Adresse ohne Klasse haette er nicht gesehen, den Koerper weiter fuer unentdeckt gehalten und ihm
einen reservierten Sonderplatz UND einen regulaeren gegeben - der Doppelplatz-Fehler, der am
2026-08-21 45-mal aufgetreten ist. Und die Probe-Rolle waere nie weitergewandert.

**Die Identitaetspruefung ist hier nicht abschaltbar.** `ACT23_EIG_IDENT` ist Vorgabe 0, die
Wuerfelei prueft also normalerweise nur die ANZAHL der Treffer - und das hat schon einmal 316 von
318 Adressen als "eindeutig" durchgewinkt bei 8,8 % groben Fehlern. Fuer eine Adresse, die eine
Episode lang gilt, ist das vertretbar; eine Direkt-Adresse bleibt den **ganzen Lauf** stehen. Sie
prueft deshalb immer - und das kostet kein Privileg, weil sie gegen die DETEKTION prueft, aus der
sie gebildet wurde, nicht gegen die wahre Koerperlage: *"findet die Adresse dasselbe wieder, was
ich gerade gesehen habe?"*

## Eine Fassung statt zweier Kopien

Die Achsen-Wuerfelei steht jetzt als `_adresse_wuerfeln` fuer sich, statt kopiert zu werden.
Dieselbe Logik lag schon einmal doppelt im Code (kopflos und GUI), und die GUI-Kopie fehlte
**332 Episoden lang unbemerkt**. Zweimal derselbe Riss an derselben Naht war genug.

# Der Vorgabepfad ist zeichengenau unveraendert

Zwei kopflose Laeufe je 12 Episoden, Vorgaben, Seed 4242, aus derselben Zustandskopie - einmal mit
dem Stand aus `HEAD`, einmal mit dem Arbeitsstand:

    285 inhaltliche Zeilen, 0 Abweichungen

Die 14 Unterschiede im Rohvergleich sind der Pfadname der Zustandskopie und Wanduhr-Zeiten. Jede
Schrittzahl (311, 138, 140, 225, 181, 155, 268, 256, 151, 262), jede Position, jede Lernzeile und
jede der 12 Lieferentscheidungen stimmt. **Der Umbau der Wuerfelei hat nichts verschoben** - ein
spaeteres A/B misst den Schalter und nicht den Umbau.

# Worauf der Schalter angewiesen ist

Es muss ueberhaupt ein Koerper OHNE Eintrag in der Szene stehen. Die Szene wird aus
`state.OBJECTS` gebaut, also ist das heute genau einer: der Probe-Koerper des Erzeugers, und auch
der nur, solange er unentdeckt ist.

**Auf dem gespeicherten Zustand des Nutzers (`ad9d768c`) findet der Schalter deshalb nichts vor:**

    Basis-Knoepfe    obj_red, obj_green, obj_L, obj_U, obj_blue
    selbst erworben  obj_T ('Neue Form 7'), obj_X ('Neue Form 10')
    ohne Eintrag     KEINER

Ein Rauchtest auf diesem Zustand schwieg entsprechend. **Das ist kein Defekt des Baus, sondern die
[Saettigung](/befunde/kette-haelt-30-episoden.md) in ihrer schaerfsten Form** - die Welt hat
sieben Koerper, und alle sieben sind vergeben. Gemessen werden kann der Schalter deshalb nur
**frisch** (`ACT23_FRESH=1`), so wie die
[Erzeuger-Reparatur](/befunde/erzeuger-repariert.md) gemessen wurde.

Der Vergleich, fuer den er gebaut ist:

    Arm kette    NOVEL_WEITER=1 FREIE_VERGABE=1                     Klasse + Knopf, der bekannte Weg
    Arm direkt   NOVEL_WEITER=1 EIG_DIREKT=1 EIG_STETIG=1           eine Sichtung statt der Kette
    Arm beides   NOVEL_WEITER=1 FREIE_VERGABE=1 EIG_DIREKT=1 ...    stoert der neue den alten Weg?

# Der falsche Torwaechter, vom ersten Lauf entlarvt

Die erste Fassung benutzte `area_hi` als Verschmelzungssperre. **Der erste frische Lauf hat sie in
der allerersten Adresse widerlegt:**

    [dbg open-set] [('verschmolzen', [-0.082, 0.087], 603)]  Belege=0 in 0 Gruppen
    [Eig-Direkt] obj_T aus EINER Sichtung adressiert: 'farbe-1 + ~gesehen + duenn' (603px)

Die Formstufe hatte den Fleck **im selben Blick** als verschmolzen gemeldet; die Direkt-Adressierung
nahm ihn trotzdem. Danach loeste die Adresse in **keiner** Episode mehr auf - fuenf von fuenf
privilegierter Rueckfall. Sie beschrieb einen Blob aus zwei Koerpern, und den gibt es nur, solange
die beiden beieinanderliegen.

**Der Grund stand seit dem 2026-08-18 im Code, eine Datei weiter:**

> *"Der vorhandene Flaechen-Schutz area_hi (1411) kann das prinzipiell nicht: die Verschmelzungen
> messen 822-1390, die groesste TRAININGSform ~940."*

603 px liegen weit unter 1411. Die Flaechenschranke ist fuer diesen Zweck gemessen untauglich, und
das war dokumentiert - ich hatte den falschen der beiden nebeneinanderliegenden Torwaechter
genommen.

**Jetzt sperrt die Farbstreuung** (`_merge_th`): aus den eigenen Einzelobjekt-Flecken gemessen,
0,995-Quantil, nichts eingestellt. Sie faengt gemessen etwa zwei Drittel der Phantom-Geburten und
hat in 64 von 64 geprueften Faellen keinen sauberen Einzelfleck gesperrt. **Und solange sie nicht
scharf ist** (weniger als 12 Referenzwerte), wird gar nicht adressiert - ohne eigenen Massstab fuer
"zwei Dinge in einem Fleck" ist eine Adresse, die den ganzen Lauf stehen bleibt, unkalkulierbar.
`area_hi` bleibt als zweites, groeberes Tor stehen.

Die erste Adresse nach der Reparatur:

    [Eig-Direkt] obj_T aus EINER Sichtung adressiert: '~gesehen'
                 (605px, Farbstreuung 0.097 < 0.111, Formvektor)

**Nur der Formvektor** - keine Farbe, keine Groesse. Das ist die reinste Fassung der Nutzeridee
("nimm das, was diesem hier aehnlich ist"), und sie entsteht so, weil im frischen Lauf zu diesem
Zeitpunkt noch keine Farbklasse existiert. Der Preis steht im Fovea-Zweig: eine reine
Formvektor-Adresse hat keinen Schluessel, dem ein Tracker folgen koennte, also laeuft sie ehrlich
mit `servo=False`.

# Kann eine eingefrorene Adresse einen Szenenwechsel ueberhaupt ueberstehen?

Getrennt gemessen, 40 echte Laufszenen, 90 Koerper-Szenenpaare, Zustand `ad9d768c`
(Pruefstand - der frische Lauf hat eine andere Deskriptorstatistik):

    Achse     Median     p90      Toleranz   ueberschritten
    chroma    0.0283   0.1251     0.1200        12,2 %
    form      0.7709   1.8715     1.4563        18,9 %
    spanne    0.0017   0.0067     0.0050        15,6 %

    alle drei Achsen halten gleichzeitig:  72,2 %

**Keine Achse ist der Ausreisser** - alle drei brechen etwa gleich oft, und das UND kostet
zusammen 28 Punkte. Eine eingefrorene Drei-Achsen-Adresse kann also halten, aber knapp. Genau
deshalb waren fuenf Rueckfaelle in Folge ein Signal und kein Rauschen.

# Fallen

* **Die Adresse ist eingefroren.** Sie entsteht aus EINER Lage; der Deskriptor driftet mit Pose
  (gemessen 13-16 % der Klassentrennung schon bei 2 mm, 21-35 % bei 20 Grad -
  [Daempfungsfunktion](/befunde/daempfungsfunktion.md)). Dass sie einen Szenenwechsel ueberlebt,
  ist bei dieser Toleranz gemessen
  ([Wiedervorlage mit Versatz](/befunde/stetige-adressierung-erster-schritt.md): 4,9 % grobe Fehler,
  aber 30 % Rueckfall). Eine Adresse, die sich mit spaeteren Sichtungen NACHFUEHRT, ist nicht
  gebaut - und waere der naechste Schritt, denn die Nutzeridee sieht sie ausdruecklich vor
  (*"der Vektor kann sich mit der Zeit aendern"*).
* **Die Bestaetigung war ein FILTER, und der faellt mit weg.** Sie hat verschmolzene Blobs und
  Eintagsdetektionen aussortiert. Dagegen stehen hier nur bereits gemessene Tore, keine neuen.
  Welche das sein muessen, hat der erste Lauf entschieden - siehe unten.
* **Nicht persistiert.** Eigenschafts-Adressen werden bewusst nicht gespeichert (ein Messwert von
  gestern beschreibt die heutige Szene nicht). Eine Direkt-Adresse gilt fuer den Lauf, nicht
  darueber hinaus.
* **Der Schalter ersetzt die Geometriequelle nicht.** Der Erzeuger verteilt weiter Rollen, er
  erfindet keine Objekte. Nach sieben Koerpern ist auch dieser Weg zu Ende.
* **Die Farbstreuungs-Sperre ist keine Null.** Gemessen faengt sie etwa zwei Drittel der
  Verschmelzungen; bei aehnlich gefaerbten Nachbarn (obj_U neben obj_blue, 0,099) greift sie kaum.
  Die erste Adresse nach der Reparatur lag mit 0,097 knapp unter der Schwelle 0,111 - also im
  Ueberlappungsbereich der beiden Verteilungen.
* **Vorgabe bleibt 0.**

# Verwandt

* [Die stetige Adressierung im Lauf](/befunde/stetige-adressierung-im-lauf.md) - der Schritt davor
* [Stetig adressieren statt Klassen vergeben](/fragen/stetige-adressierung.md) - die These
* [Der Erzeuger reicht die Probe-Rolle weiter](/befunde/erzeuger-repariert.md) - liefert den Koerper ohne Eintrag
* [Die Aneignungskette traegt 29 Episoden](/befunde/kette-haelt-30-episoden.md) - die Saettigung
* [Die Vergabe-Engstelle, diagnostiziert](/befunde/vergabe-engstelle-diagnose.md) - was gegenstandslos wuerde
