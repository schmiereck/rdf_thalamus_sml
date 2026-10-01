---
type: Mechanismus
title: Die Steuer-GUI - drei Gruppen, Klapplisten, eine Aufgabenzeile
description: Umbau 2026-09-30 nach Nutzerbeobachtungen im GUI-Lauf. Die Wuerfel heissen farbneutral (Wuerfel A/B), weil FARB_MISCHUNG die Farben je Szene permutiert und "Gruenes Wuerfel" ein blauer Wuerfel sein konnte; Log und GUI zeigen die AKTUELLE Farbe und den Koerper in Klammern (nur Anzeige, privilegiert, geht in keine Entscheidung ein). Die GUI ist in drei Gruppen geteilt - Objekt (per Name oder per Eigenschaften), Ziel (Ort oder Relation zu einem Koerper, fest waehlbar), Ausfuehrung - alle Wahlen als Klapplisten; eine Aufgabenzeile sagt in einem Satz, was womit wohin geschieht.
tags: [act23, gui, bedienung, anzeige, nutzeridee]
status: stable
evidenz: einzelmessung
ebene: code
generated: { by: claude/opus-5.5, at: 2026-09-30T00:00:00Z }
sources:
  - id: code
    resource: "src/pc_cvnn/pc_act23.py: _Auswahl, CommandPanel23, CommandState23.anzeige/aufgabe/ziel_hinweis, FARB_NAMEN, KOERPER_NAME; _ziel_adresse_wuerfeln (state.ziel_art)"
    title: GUI-Umbau
  - id: log
    resource: "log/pc_act23_2026-09-30_08-21-56_16080.txt, Ep 82-89"
    title: Nutzerbeobachtung
---

# Warum

Nutzerbeobachtungen im GUI-Lauf vom 30.09.:

1. "[Auto 83] Gruenes Wuerfel" - kein gruener Wuerfel in der Szene. Kein Auswahlfehler: `obj_green`
   lag auf dem Tisch und wurde gegriffen; die festen Knopfnamen trugen Farbwoerter, waehrend
   `FARB_MISCHUNG` (Vorgabe 1) die Farben je Szene permutiert ([Farb-Mischung](/befunde/farb-mischung.md)).
2. "[Auto 89] Gruenes Wuerfel" - ein blauer Wuerfel, die GUI zeigte "Farbe: beliebig": die
   Eigenschaftsfelder gehoeren nur zur Eigenschafts-Adressierung, sahen aber aus wie Teil des
   Befehls.
3. Nicht erkennbar, was Objekt und was Ziel ist und welche Aktion laeuft (Transport, Stapeln,
   links/rechts); Durchschalten per Klick statt Auswahl.

# Was jetzt gilt

* **Namen**: `Würfel A` (obj_red), `Würfel B` (obj_green); Log und GUI haengen an, welcher Koerper
  es ist und welche Farbe er JETZT hat: `Würfel B (blau)`, `Neue Form 7 (T-Form, orange)`,
  Zieladressen `rechts von farbe-14 + mittel [= Kreuz, violett]`. Die Farbnamen stammen aus der
  RGBA (Palette `FARB_NAMEN`) - reine Beschriftung fuer den Beobachter. `ACT23_AUTO_OBJ` findet
  Objekte auch ueber Koerpernamen und die alten Namen "Rotes"/"Gruenes".
* **Gruppe 1 Objekt**: Klappliste "per Name" ODER Farbe/Form/Groesse + "per Eigensch."; darunter
  "adressiert per NAME/EIGENSCHAFTEN -> Koerper, Farbe". Bei Namenswahl sind die Eigenschaftsfelder
  blass.
* **Gruppe 2 Ziel**: "Art" = Ort (Marker) | Koerper, Relation zufaellig | an | auf | links von |
  rechts von | vor | hinter; bei Ort zusaetzlich "Ort: Marker 1-3". "Ziel neu wuerfeln" setzt den
  Marker neu bzw. wuerfelt den Bezugskoerper neu. Eine fest gewaehlte Relation gilt auch im
  Auto-Lauf (`state.ziel_art`; None = wie `ACT23_ZIEL_RELATION`); "auf" nimmt dann jeden Koerper
  als Auflage (wie `ACT23_AUF_ALLE`), fuer Richtungswoerter nur Bezuege, neben denen das Wort
  erreichbar ist.
* **Gruppe 3 Ausfuehrung**: Aktion, Choreo, Greifer, Zielkodierung - je eine Klappliste.
* **Aufgabenzeile**: `Aufgabe: Würfel B (blau) greifen -> ablegen rechts von U-Form (türkis)`,
  darunter Choreo/Greifer/Zielkodierung/Auto.

Geprueft: Rendering ohne Fenster (Agg) mit offenen Klapplisten; kopfloser Lauf 3 Episoden ohne
Fehler. Das Verhalten des Agenten ist unveraendert, solange in der GUI keine Relation fest gewaehlt
wird (dann greift `ACT23_ZIEL_RELATION` wie bisher).

# Ergaenzung 2026-09-30: selbst waehlen statt nur wuerfeln

Nutzerfrage: "ich habe keine Moeglichkeit, den Zielkoerper oder Punkt manuell anzugeben". Neu:

* **Klappliste "Bezug"** (Gruppe Ziel): "zufaellig" oder ein Koerper auf dem Tisch
  (`state.ziel_body_fix`). Die ADRESSE bildet der Agent weiter selbst aus der Detektion; von
  aussen kommt nur, WELCHER Koerper. Passt der gewaehlte Koerper nicht (ist selbst das Objekt,
  geparkt, Relation dort nicht erreichbar), sagt `[Zielwurf] keine Adresse: gewaehlter Bezug ...`
  warum, und der Marker bleibt das Ziel.
* **Klicks ins Kamerabild**: links = zu transportierendes Objekt (naechster Koerper, <= 40 mm),
  rechts = Ziel (bei Koerper-Ziel der naechste Koerper als Bezug, bei "Art: Ort" wandert der Marker
  an die Stelle; ausserhalb des Arbeitsbereichs abgewiesen). Pixel -> Tisch ueber die Homographie
  der Wahrnehmung (`shape_clf._px_to_world`).
* Die Objektliste markiert Koerper, die nicht auf dem Tisch stehen.
* Klapplisten mit weisser Schrift (Nutzerbefund: schwarz auf dunkel unlesbar).

Geprueft ohne Fenster: Klicks mit synthetischen Ereignissen (Marker landet auf der geklickten
Tischstelle, Bezug wird gesetzt), Rendering der Listen; kopfloser Lauf 2 Episoden ohne Fehler.
Nicht am Bildschirm angeklickt.


# Ergaenzung 2026-10-01: Platte von Hand, nur EIN Marker sichtbar

Nutzerbefund: die blaue 70-mm-Platte (`sockel`, Stapelziel seit Stufe 2) steht mit
`ACT23_SOCKEL=1` in JEDER Szene an derselben Stelle `[-0.018, +0.149]`, nimmt viel Tisch ein
und duerfte das Netz verwirren; und von den Magenta-Zielscheiben sind immer alle sichtbar.

* **Klappliste "Platte"** (untere Leiste): sichtbar | ausgeblendet | an neue Stelle | per Klick
  setzen. **Mittelklick** ins Kamerabild setzt die Platte direkt. Ausgeblendet heisst geparkt wie
  ein nicht stehendes Objekt (`PARK_XY`); ein Bezug auf die Platte wird dabei geloescht.
  "an neue Stelle" nimmt dasselbe Raster wie `ACT23_SOCKEL_WANDERT` (>= 80 mm zu jedem stehenden
  Objekt, ausserhalb der Armfreiheit). Ein Klick naeher als Halbbreite + 17 mm an einem Objekt
  wird abgewiesen (die Platte laege im Objekt), unter 80 mm erlaubt, aber mit Warnung
  (gemessene Verschmelzungsschranke, [Sockel braucht 80 mm](/befunde/sockel-braucht-80mm-freiraum.md)).
* **Klappliste "Farbe"**: fuenf GESAETTIGTE Plattenfarben (`PLATTEN_FARBEN`: tiefblau, mint,
  lachs, oliv, himmelblau). Gelb flog nach der Probe raus: auf der RGBA 0,14 von Orange entfernt,
  gerendert aber von der orangen L-Form kaum zu unterscheiden. Grau gibt es mit Absicht nicht: die Saettigungsmaske
  (`SAT_TH=0,15`) sieht keine graue Platte, sie waere fuer den Agenten weg. Die Meldung nennt den
  Chroma-Abstand zur naechsten Objektfarbe und warnt unter 0,12 (= `colour_openset.TH`): dann
  teilt die Platte die Farbklasse eines Objekts. Gerechnet auf der RGBA - massgeblich ist die
  gerenderte Chroma (Lehre aus obj_Y).
* **"Objekte neu" respektiert die Wahl**: `_sockel_setzen` laesst eine ausgeblendete Platte
  geparkt und behaelt eine versetzte Stelle; stellt die neue Szene ein Objekt naeher als 80 mm
  daneben, rueckt die Platte auf die naechste freie Rasterstelle. Ohne GUI-Eingriff unveraendert.
* Waehrend einer Episode wird vorgemerkt und danach ausgefuehrt (wie "Objekte neu").
* **EIN Marker** (`ACT23_EIN_MARKER`, Vorgabe 1): die drei waehlbaren Scheiben `target_sel_1..3`
  liegen unter dem Tisch (z = -0,05, auch im Modell, weil `mj_resetData` die mocap-Lage aus
  `body_pos` neu laedt) und behalten ihre xy als Ortsgedaechtnis. Sichtbar ist nur die aktive
  Scheibe `target_marker`; bei Koerper-Ziel vor dem Start gar keine, bis `run_combined` sie beim
  Festlegen auf die aufgeloeste Stelle holt. `ACT23_EIN_MARKER=0` stellt das alte Bild her.

**Gemessen:** [Nur ein Marker - A/B](/befunde/ein-marker-ab.md) - kein Effekt (58,2 gegen 55,8 %
zugunsten "vier sichtbar", Seeds 5:3, p = 0,73).

**Erwartung, ehrlich:** fuer die WAHRNEHMUNG aendert der Marker-Umbau wenig - `perceive_all`,
`select` und die Fovea-Einstiege parken die Marker ohnehin vor jedem Blick (`_park_markers`).
Er wirkt auf das Kamerabild der GUI und auf Pfade, die nicht parken. Die Platte dagegen ist ein
echter Koerper in jeder Detektion; ob ihr Ausblenden etwas an Quoten aendert, ist NICHT gemessen
(`ebene: code`).

**Nachtrag, gemessen:** [Platte ausblenden - A/B](/befunde/platte-ausblenden-ab.md) -
erster Durchgang ohne Platte 60,0 gegen 53,3 %, in der Replikation umgekehrt;
ueber 9 Seeds 52,9 gegen 54,9 %, p = 0,41 - **kein Effekt**. Startschalter dafuer:
`ACT23_SOCKEL_AUS=1` (Platte beginnt ausgeblendet, in der GUI wieder einblendbar).

Geprueft ohne Fenster (echte GUI, Agg, synthetische Aufrufe und ein Mittelklick ueber die
Homographie): ausblenden (0 blaue Pixel, Platte aus `_tisch()`), einblenden an alter Stelle,
wuerfeln, Mittelklick auf [0,08; 0,17] -> Platte bei [0,082; 0,168] mit 80-mm-Warnung, Umfaerben,
Vormerken waehrend `busy` und Nachholen, "Objekte neu" mit Ausweichen auf die naechste freie
Stelle. Marker: bei "Ort" genau eine Scheibe, bei Koerper-Ziel keine (alle z = -0,05). Kein
Lauf mit Episoden, nicht am Bildschirm angeklickt.
