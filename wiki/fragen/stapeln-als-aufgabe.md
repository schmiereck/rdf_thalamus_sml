---
type: Frage
title: Stapeln als neue Aufgabe - das Ziel wird eine Adresse statt einer Koordinate
description: Nutzeridee. Machbar, und der Entwurf ist ungewoehnlich billig, weil das Ablageziel schon heute ein HAKEN ist und schon heute als Latent ausgefuehrt wird. Die Sprache waechst nicht um ein Verb, sondern um einen Typ - der Zielplatz bekommt denselben Typ wie das Objekt, naemlich eine Adresse, und die Relation wird eine Phasendrehung im Ziellatent. Drei harte Huerden sind benannt und beziffert: eine Regel gegen Stapel, ein flacher Erfolgsbegriff und eine Ablagegenauigkeit, die doppelt so grob ist wie der Wuerfel breit.
tags: [act23, kommando, aufgabe, latent, stapeln]
status: open
evidenz: vermutung
ebene: code
generated: { by: claude/opus-5, at: 2026-09-17T00:00:00Z }
sources:
  - id: idee
    resource: "Nutzer, 2026-09-17: als Ziel andere Objekte angeben koennen, also das Stapeln als neue Aufgabe einfuehren"
    title: Die Idee
  - id: messung
    resource: /befunde/stapeln-bricht-die-tischebene.md
    title: Die erste Messung dazu
---

# Die Idee

Bisher lautet ein Befehl: *nimm DIESEN Koerper und lege ihn AN DIESE STELLE*. Neu waere: *lege ihn
AUF JENEN KOERPER*. Damit ist das Ziel kein Ort mehr, sondern ein zweites Objekt.

# Antwort auf "ist das moeglich": ja, und die Verdrahtung steht schon

Vier Dinge, die man sonst bauen muesste, sind vorhanden:

* **Das Ablageziel ist ein HAKEN.** `run_combined(goal_fn=...)` ruft `goal_fn(cmd, obj_xy)` und
  legt sich auf das Ergebnis fest. Dort steht heute `state.goal_fn`, das `marker_xy(target_idx)`
  zurueckgibt - eine Funktion, kein fester Wert. Eine andere Quelle einzusetzen ist eine Zeile.
* **Das Ziel ist schon ein LATENT.** `post_goal_fn` kodiert den festgelegten Zielpunkt einmal
  (`lgoal.set_in("goal_xy", g)`), und `LatentGoalServo.set_goal_vector` nimmt sogar direkt einen
  ganzen Latentvektor entgegen. Der Ausfuehrungspfad fragt nie nach einer Koordinate.
* **Das Ziel wird waehrend des Tragens NEU GELESEN.** `place_servo_fn` laeuft in jedem Schritt,
  solange das Objekt getragen wird (act16:565). Ein Ziel, das WAHRGENOMMEN statt gesetzt wird und
  sich deshalb bewegen kann, hat seinen Aktualisierungspfad also schon.
* **Adressen aufloesen kann der Agent.** `EIGENSCHAFT` / `EIG_MESS` und
  `finde_nach_eigenschaften` finden einen Koerper aus der eigenen Wahrnehmung, seit
  [`ACT23_EIG_DIREKT`](/mechanismen/adresse-ohne-klasse.md) sogar aus einer einzigen Sichtung und
  ohne Klasse.

> **Der Nebengewinn ist groesser als er aussieht:** das Ablageziel ist heute das **einzige Stueck
> des Befehls, das der Agent nicht wahrnimmt**. `marker_xy` liest `sim.d.mocap_pos` - eine
> privilegierte Designer-Koordinate. Ein Ziel, das ueber eine Adresse aufgeloest wird, nimmt genau
> dieses Privileg weg. Das zaehlt nach [Projektziel](/ziel.md) fuer sich.

# Die Sprache: ein Typ mehr, kein Verb mehr

Der naheliegende Fehler waere ein neues Kommando "stapeln" mit eigenem Kopf und eigener
Choreographie. Sinnvoller ist, dem **Zielplatz denselben Typ zu geben, den das Objekt schon hat**:

    heute      BEFEHL   := ADRESSE  AKTION  ORT
    neu        BEFEHL   := ADRESSE  AKTION  BEZUG
               BEZUG    := ORT | RELATION ADRESSE
               RELATION := an | auf
               ADRESSE  := (Farbklasse?, Formachse?, Groessenband?)   -- unveraendert

Damit ist "Stapeln" kein Sonderfall, sondern der Normalfall mit einem anderen `BEZUG`. Drei
Eigenschaften machen das zum richtigen Schnitt:

1. **Ort und Adresse muenden ohnehin in dasselbe.** Beide werden zum Ziellatent, bevor irgendetwas
   ausgefuehrt wird. Die Sprache bekommt einen Aufloesungsschritt mehr, keinen zweiten
   Ausfuehrungspfad.
2. **Die Adresse ist schon erprobt**, samt ihrer gemessenen Regel: sie darf nur Achsen nennen, die
   Eigenschaften des Koerpers sind
   ([Farbe darf nicht hinein](/befunde/dauer-adresse-vertraegt-keine-farbe.md)). Dieselbe Regel
   gilt fuer ein Ziel - und beim Stapeln kommt eine zweite Achse dazu, die keine Eigenschaft mehr
   ist, s. unten.
3. **Die RELATION ist im Latentraum eine Verschiebung - und RoPE macht eine Verschiebung zur
   exakten Phasendrehung.** Genau diese Eigenschaft traegt schon die
   [latente Augmentierung](/fragen/latente-augmentierung.md). "auf B" waere dann: *nimm das Latent
   von B und drehe seine Phase um den Betrag, der einer Objekthoehe entspricht*. Der Betrag wird
   **gelernt**, nicht gerechnet - die Relation ist ein Wort mit einer lernbaren Bedeutung, kein
   Offset, den der Designer einsetzt.

**Das ist der eigentliche architektonische Ertrag**, und anders als beim
[komplexen Wrist-Kopf](/fragen/offene-faeden-act23.md) gibt es hier eine Hypothese, was besser
werden soll: eine Relation, die als Phasendrehung dargestellt wird, gilt fuer JEDEN Koerper an
JEDER Stelle, weil die Phase die Position traegt. Eine Relation als Koordinatenaufschlag muss fuer
jede Stelle neu gelernt werden.

# Drei Huerden, alle beziffert

**1. Es gibt eine ausdrueckliche Regel GEGEN Stapel.** `run_combined` saeubert das uebergebene
Ziel (act16:382-394): acht Durchgaenge, die es von jedem Koerper um 0,05 m **wegschieben**. Auch
das Zufallsziel wird ueber `clear(tgt, OBJS, 0.05)` gezogen. Ein Ziel AUF einem Koerper wird heute
also aktiv weggeschoben. Das ist eine Laufzeitregel und muss ohnehin fallen, wenn ein Ziel
"auf B" erlaubt sein soll - sie steht dem Stapeln nicht nur im Weg, sie ist selbst der
naechstliegende Kandidat fuer [Entskriptung](/mechanismen/laufzeit-regeln.md).

**2. Der Erfolgsbegriff ist flach - in beiden Richtungen.** Der privilegierte Richter prueft
`rested = cpos[2] < cmd_half[2] + 0,010`, woertlich *"liegt auf dem Tisch"*; ein gelungener Stapel
faellt darunter. Und der **Selbstrichter** faellt genauso aus: die Homographie ist eine
Ebenen-Abbildung, ein gestapelter Wuerfel liest gemessen **15,9 mm daneben** (4,6-25,3 mm, 12 %
der Stellen ueber der Liefertoleranz), s.
[Ein gestapelter Koerper liest 16 mm daneben](/befunde/stapeln-bricht-die-tischebene.md).
Zusaetzlich erscheint er 11-16 % groesser, wodurch das **Groessenband an einem Drittel der Stellen
kippt** - die scheinbare Groesse ist in einer Welt mit Stapeln keine Eigenschaft des Koerpers
mehr, sondern haengt an seiner Hoehe.

> Der Fehler ist aber kein Rauschen: er zeigt zu 100 % radial von der Kamera weg und korreliert mit
> `r = +1,00` mit dem Kameraabstand. **Die Hoehe ist rekonstruierbar** - sie steckt im Widerspruch
> zwischen Ort und scheinbarer Groesse. Das ist die Aufgabe, nicht ihr Hindernis.

**NACHTRAG 2026-09-17, und er entkraeftet den Absatz oben fuer den gebauten Fall.** Der Weg
"Hoehe aus dem Widerspruch lesen" setzt voraus, dass der gestapelte Koerper ueberhaupt GESEHEN
wird. Auf einer BREITEN Auflage wird er es nicht: gemessen 0 von 25 Stellen, die Flaeche aendert
sich um kein Pixel, die Silhouette des Wuerfels liegt ganz innerhalb der Platte
([Der Sockel verschluckt den Stapel](/befunde/sockel-verschluckt-den-stapel.md)). Es gibt dann
keinen Ortsfehler, weil es keine Ortsmessung gibt. Der Absatz oben gilt weiter fuer Wuerfel auf
Wuerfel; fuer den Sockel traegt stattdessen die **Farbstreuung** der Auflage.

**3. Die Ablagegenauigkeit reicht geometrisch nicht.** Gemessen sind Median 25 mm seitlicher
Fehler beim Loslassen und 21 mm am Ende ([Ablage und Platzieren](/befunde/ablage-und-platzieren.md)).
Ein 24-mm-Wuerfel bleibt auf einem 24-mm-Wuerfel nur liegen, solange der Schwerpunkt ueber der
Auflage steht, also unter **12 mm** Versatz. **Die Aufgabe verlangt rund die doppelte Genauigkeit
dessen, was das System heute liefert** - die Erfolgsrate startet nahe null, und damit auch das
Lernsignal.

Die naheliegende Abhilfe ist die Welt, nicht der Algorithmus: **ein breiter, flacher Sockel als
erstes Stapelziel.** Auf einer 60-mm-Platte ist die geometrische Toleranz wieder groesser als die
vorhandene Genauigkeit, die Aufgabe ist von Anfang an loesbar, und man kann die Auflage spaeter
schrumpfen. Das ist derselbe Gedanke wie die Armbreiten-Reihe in
[Aneignung neuer Formen](/befunde/aneignung-neuer-formen.md) - eine Schwierigkeitsachse, an der
sich Uebertragung messen laesst.

# Die eine Stelle, an der es wirklich Arbeit wird

Das Ziel ist ueberall **zweidimensional**: `GoalModule2D`, `goal_xy`, `marker_xy`, und im
Zustandsvektor der Policy (act16:601) stehen `tgt_eff[0], tgt_eff[1]` - **kein `tgt_z`**. Die
Policy kann heute gar nicht ausdruecken *"lass hoeher los"*; die Ablagehoehe ist die Konstante
`GRASP_Z`. Stapeln ist damit die erste Aufgabe, die eine dritte Dimension im ZIEL verlangt.

Der kleinste Schnitt, der das nicht zur Grossbaustelle macht:

* `GoalModule2D` bekommt eine dritte RoPE-Achse fuer `z`. Die Kodierung ist bereits phasenbasiert,
  eine Achse mehr ist additiv, und die Relation "auf" ist dann eine reine Drehung in dieser Achse.
* Der Zustandsvektor der Policy bekommt `tgt_z`, die Ablagephase zielt auf `tgt_z` statt `GRASP_Z`.
* Der Erfolgsbegriff wechselt von *"liegt tief"* auf *"ruht"* (keine Bewegung, nicht in der Klaue).
  Diese Definition ist aufgabenunabhaengig und deshalb die ehrlichere, auch fuer die alte Aufgabe.

# Vorschlag fuer die Reihenfolge

| Stufe | was | wozu |
|---|---|---|
| 0 | die Hoehenmessung | **erledigt**, s. [Befund](/befunde/stapeln-bricht-die-tischebene.md) |
| 1 | `BEZUG := an ADRESSE` - das Ziel ist ein Koerper, abgelegt DANEBEN | **gebaut und gemessen**, s. [Das Ablageziel als Adresse](/mechanismen/ziel-als-adresse.md). Die Sprachaenderung allein, ohne Hoehe. Beurteilbar mit der heutigen flachen Wahrnehmung, und sie nimmt dem Befehl sein letztes Privileg |
| 2 | Sockel in die Welt, `BEZUG := auf ADRESSE`, Ziel dreidimensional | **vorbereitet**, s. [Stufe 2 vorbereitet](/mechanismen/stufe2-vorbereitet.md): Sockel, `ACT16_GOAL_Z`, `ACT16_ERFOLG_RUHT` stehen. Offen bleiben die Relation selbst, woher die Hoehe kommt, der Selbstrichter - und zuerst der Transport zu einem besetzten Ziel |
| 3 | ~~Hoehe aus dem Widerspruch Ort/Groesse lesen~~ -> **die Oberkante SEHEN statt wissen** | **gebaut und gemessen**, s. [Die Oberkante ohne Privileg](/befunde/oberkante-ohne-privileg.md): der `HoehenSchaetzer` liest sie aus Flaeche, Dicke und Ort derselben Detektion, die die Adresse aufloest. 85 gegen 83 % Stapel, p = 1,00 - **das letzte Privileg auf dem Pfad ist gefallen, ohne messbaren Verlust.** Die Relation aus der Farbstreuung traegt den SELBSTRICHTER, s. [dort](/befunde/selbstrichter-stapel.md) |

| 4 | **RELATION auch in der ADRESSE**: `ADRESSE := (Farbe?, Form?, Groesse?) \| RELATION ADRESSE` - *"nimm das, was auf Y liegt"* | **GEBAUT, Mechanismus belegt, WIRKUNG NICHT.** Ein Seed gab 49 gegen 14 % ([dort](/befunde/stufe4-abstapeln-belegt.md)), der gepaarte Sweep ueber acht Seeds reproduziert das nicht (38 gegen 33 %, p = 0,69, [dort](/befunde/stufe4-sweep-widerlegt.md)). Voraussetzung war, den gestapelten Koerper ueberhaupt zu FINDEN; das ist [gemessen geloest](/befunde/stapel-wird-sichtbar.md) (24 von 25 statt 0 von 25). Damit wird die Sprache **rekursiv** - dieselbe Relation im Subjekt wie im Ziel -, und Umstapeln wird moeglich |

# Stufe 4: die Relation gehoert auch in die Adresse

Bis Stufe 3 darf die Relation nur im **Ziel** stehen:

    BEFEHL   := ADRESSE AKTION BEZUG
    BEZUG    := ORT | RELATION ADRESSE          <- hier
    ADRESSE  := (Farbklasse?, Formachse?, Groessenband?)

Der naechste Schnitt ist derselbe Gedanke eine Ebene weiter - **derselbe Typ auch im Subjekt**:

    ADRESSE  := (Farbklasse?, Formachse?, Groessenband?) | RELATION ADRESSE

Damit ist *"nimm das, was auf dem Sockel liegt"* sagbar, und die Sprache wird **rekursiv**. Das ist
der eigentliche Beleg, dass es eine Sprache ist und kein Sonderfall: derselbe Bauplan traegt an
beiden Stellen, und aus ihm faellt das **Umstapeln** ohne ein weiteres Verb.

**Die Voraussetzung ist geloest.** Ein gestapelter Koerper war nicht adressierbar, weil er keine
eigene Detektion bekam. Die Ursache ist lokalisiert (die raeumliche Wache des Chroma-Schnitts, nicht
sein Klassentor) und behoben: [Der Stapel wird sichtbar](/befunde/stapel-wird-sichtbar.md), 24 von
25 gegen vorher 0 von 25, ohne dass die leere Platte zerfaellt.

**Was noch fehlt**, und in dieser Reihenfolge:

1. Die Aufloesung der Adresse muss die Relation lesen koennen - heute nimmt
   `finde_nach_eigenschaften` nur ein Eigenschafts-Tripel.
2. Der gefundene Koerper liegt **hoch**, nicht auf Greifhoehe. Der Griff braucht die dritte
   Dimension genauso wie die Ablage sie in Stufe 2 bekommen hat - und die Hoehe kommt aus dem
   [Hoehenschaetzer](/befunde/oberkante-ohne-privileg.md) oder aus dem
   [Ertasten](/mechanismen/hoehe-ertasten.md), die dafuer schon stehen.
3. Erst dann das A/B: Umstapeln gegen den heutigen Sonderfall.

# Nutzerwunsch 2026-09-24: auf BELIEBIGE Koerper stapeln

Nicht nur auf die Platte, sondern auf jeden vorhandenen Koerper der Szene. Heute verhindert das
eine Zeile mit Begruendung: `_ziel_adresse_wuerfeln` nimmt fuer "auf" nur `state.STUETZEN`.
Einschaetzung am Code und an den Messungen (Analyse, nicht gemessen):

    Koerper            Grundriss (halbe Breite)     Versatz, bei dem ein 24-mm-Wuerfel noch traegt
    Sockelplatten      25-35 mm                     bis ~25-35 mm
    Wuerfel            12 mm                        unter 12 mm
    L/U/T/X/Y          Balken 7 mm breit            quer zum Balken unter ~7 mm

    gemessene Ablagegenauigkeit: Median 19-25 mm ([Ablage](/befunde/ablage-und-platzieren.md))

* **Der Engpass ist die seitliche Ablagegenauigkeit, nicht die Sprache.** Auf einem Wuerfel
  muesste der Arm etwa doppelt so genau ablegen wie heute im Median; auf den Balkenformen noch
  genauer. Erwartung: selten erfolgreich, auf Balken fast nie.
* **Wahrnehmung:** Koerper auf Koerper liest 16 mm Parallaxe
  ([dort](/befunde/stapeln-bricht-die-tischebene.md)); gleichfarbige Stapel sind ueber die
  Farbstreuung nicht trennbar. Die Hoehe ist dagegen einfach: alle Koerper sind 24 mm hoch.
* **Die Chance fuer das [Projektziel](/ziel.md):** WELCHER Koerper traegt, muss dem Agenten
  niemand sagen. Er kann es aus eigenen Versuchen lernen (liegt es danach oben oder nicht - das
  Stapel-Selbsturteil gibt es) und daraus eine gelernte Eigenschaft "traegt" je Koerper bzw.
  Form bilden. Das waere Aneignung einer neuen Eigenschaft, nicht nur einer neuen Aufgabe.

> **GEMESSEN 2026-09-24, s. [Auf beliebige Koerper](/befunde/auf-beliebige-koerper.md):** die
> Einschaetzung oben war fuer das ABLEGEN falsch - getragene Koerper landen auf Wuerfeln 9 von 16,
> auf Balken 10 von 18 auf dem Ziel; liegen bleiben sie dort seltener (4 bzw. 3). Der Nutzer wertet
> die Ablage, nicht das Liegenbleiben (`ACT23_AUF_LOSLASSEN`).

Vorschlag: ein Schalter, der "auf" fuer alle Koerper oeffnet, eine ehrliche Messung, welche
Paarungen gelingen, und die Tragfaehigkeit als selbst gelernte Eigenschaft.

# Wie es weitergehen kann (Stand 2026-09-23)

Nach dem [Sweep](/befunde/stufe4-sweep-widerlegt.md) ist das Hindernis nicht der Mechanismus,
sondern die **Messbarkeit**: Arm A streut ueber Seeds zwischen 20 und 60 %, und die Arme sehen
nach zwei, drei Episoden verschiedene Szenen. In der Reihenfolge des Nutzens:

1. **ERLEDIGT (`322972b`): Szenen-Zufall von den Entscheidungen entkoppeln** - die Szene je
   Episode aus `(Seed, Episodennummer)` ableiten statt aus dem laufenden `crng`
   (`ACT23_SZENE_JE_EPISODE`, geprueft: 10 von 10 Szenen-Abdruecken identisch). Dann sehen beide Arme in
   JEDER Episode dieselbe Welt, und der Vergleich wird ein McNemar-Test auf den abweichenden
   Paaren statt eines Vorzeichentests ueber acht Seeds. Das hilft jedem A/B im Projekt, nicht
   nur diesem.
2. **ERLEDIGT, s. [Drei Arme je Episode gepaart](/befunde/stufe4-drei-arme-gepaart.md): weder
   Sichtbarkeit noch Relation traegt messbar (34 / 37 / 43 %), und der Test war fuer die
   Kontrolle zu leicht -- der Koerper steht genau in der Plattenmitte.** Naechster Schritt: ein
   Stapel AUSSERHALB der Mitte. **ERLEDIGT 2026-09-24, s. [Der Stapel neben der
   Mitte](/befunde/stufe4-stapel-neben-der-mitte.md): 30 / 41 / 42 %, nichts signifikant, und der
   Versatz schadet dem blinden Arm auf gleicher Szene nicht (12 gegen 9) - die Mitten-Vermutung
   faellt. "Herunterholen" braucht die Relation nicht, weil der obere Koerper ueber seine
   Eigenschaften eindeutig ist; eine Aufgabe, die sie braucht, muesste zwei GLEICHE Koerper
   enthalten, von denen nur einer auf etwas liegt.** Urspruenglich: **Die richtige Kontrolle fuer Stufe 4:** drei Arme - ohne Chroma-Schnitt | mit Schnitt,
   Eigenschafts-Adresse | mit Schnitt, relationale Adresse. Der Sweep hat nur die letzten beiden
   verglichen; der grosse Schritt (Sichtbarkeit) steckte in beiden.
3. **Danach die Richtungsfrage:** Umstapeln mit der Relation auf BEIDEN Seiten ("nimm das, was
   auf X liegt, und lege es auf Y") - oder zurueck zum belegten Engpass
   Klassenkonsolidierung, der naeher am [Projektziel](/ziel.md) liegt.

> **UMSORTIERT 2026-09-17.** Stufe 1 bei KLEINEM Abstand ist keine Vorstufe von Stufe 2, sondern
> die haertere Aufgabe. Gemessen: der Arm kommt nicht unter ~37 mm an einen Koerper heran, und die
> Ursache ist die Klauenmechanik - sie muss NEBEN einem Hindernis absenken
> ([Teacher-Test](/befunde/nahe-ablage-ist-mechanik.md): der untrainierte Teacher kann es genauso
> wenig und verschiebt den Nachbarn in 64 % der Ablagen; nah UND beruehrungsfrei gelingt 3-mal in
> 70 Ablagen). Beim Stapeln liegt der Bezugskoerper UNTER dem Objekt und gar nicht im Absenkweg.
> **Der naechste Schritt ist deshalb direkt `RELATION := auf` mit `ACT16_GOAL_Z`**, nicht ein Umweg
> ueber nahe Seitenablagen. Stufe 1 bei GROSSEM Abstand (90 mm) bleibt gemessen unauffaellig und
> traegt die Sprachaussage.

**Stufe 1 ist fuer sich wertvoll** und kostet fast nichts: sie ist ein sauberes A/B gegen die
Marker-Koordinate, mit unveraendertem Erfolgsbegriff.

# Was hier NICHT behauptet wird

Keine Quotenerwartung. Nach [Projektziel](/ziel.md) waere der Ertrag die neue AUFGABE und die
dritte Dimension in der Wahrnehmung, nicht eine Zahl. Und nach
[Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) ist alles oben `ebene: code` - die einzige
Messung dazu ist die Hoehensonde, und die sagt nur, was die Wahrnehmung tut.

# Verwandt

* [Ein gestapelter Koerper liest 16 mm daneben](/befunde/stapeln-bricht-die-tischebene.md) - die erste Messung
* [Die Adresse ohne Klasse](/mechanismen/adresse-ohne-klasse.md) - der Adresstyp, den das Ziel erben soll
* [Eine dauerhafte Adresse darf keine Farbe nennen](/befunde/dauer-adresse-vertraegt-keine-farbe.md) - die Regel, die fuer Zieladressen genauso gilt
* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) - die Saeuberung des Ziels ist eine davon
* [Ablage und Platzieren](/befunde/ablage-und-platzieren.md) - woher die 21-25 mm stammen
* [Latente Augmentierung](/fragen/latente-augmentierung.md) - dieselbe RoPE-Eigenschaft, andere Nutzung
