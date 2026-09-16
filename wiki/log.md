# Chronik

Neueste zuerst. Datumsueberschriften in ISO-Form `YYYY-MM-DD`. Ein Eintrag je Vorgang, das
fuehrende fette Wort ist Konvention: **Anlage**, **Ergaenzung**, **Widerlegung**, **Ruecknahme**.

Fuer eine schnelle Uebersicht: `grep "^## " wiki/log.md | head -5`

## 2026-09-16

* **Ergaenzung**: [Die Adresse ohne Klasse](/mechanismen/adresse-ohne-klasse.md) - **der falsche
  Torwaechter, vom ersten Lauf entlarvt.** Meine erste Fassung benutzte `area_hi` als
  Verschmelzungssperre; der erste frische Lauf hat sie in der ALLERERSTEN Adresse widerlegt: der
  Fleck war im selben Blick von der Formstufe als `('verschmolzen', [-0.082, 0.087], 603)` gemeldet
  worden, die Direkt-Adressierung nahm ihn trotzdem, und die Adresse loeste danach in KEINER
  Episode mehr auf (5 von 5 privilegierter Rueckfall) - sie beschrieb einen Blob aus zwei Koerpern.
  **Der Grund stand seit dem 18.08. eine Datei weiter im Code:** *"Der vorhandene Flaechen-Schutz
  area_hi (1411) kann das prinzipiell nicht: die Verschmelzungen messen 822-1390, die groesste
  TRAININGSform ~940."* 603 px liegen weit darunter. Jetzt sperrt die FARBSTREUUNG (`_merge_th`,
  selbst gemessenes 0,995-Quantil), und solange die weniger als 12 Referenzwerte hat, wird gar
  nicht adressiert - die entfallende Bestaetigung WAR dieser Filter. Erste Adresse nach der
  Reparatur: `'~gesehen'` allein, also **nur der Formvektor**, ohne Farbe und Groesse (605px,
  Farbstreuung 0,097 < 0,111) - die reinste Fassung der Nutzeridee, zum Preis von `servo=False`,
  weil kein Tracker einem Vektor folgen kann. **Dazu eine getrennte Achsen-Messung** (40 echte
  Laufszenen, 90 Koerper-Szenenpaare, Pruefstand): chroma bricht 12,2 %, form 18,9 %, spanne 15,6 %
  der Faelle - **keine Achse ist der Ausreisser**, aber das UND kostet zusammen 28 Punkte, alle drei
  halten nur in 72,2 %. Eine eingefrorene Drei-Achsen-Adresse kann also halten, aber knapp; fuenf
  Rueckfaelle in Folge waren deshalb ein Signal und kein Rauschen. Drei frische Arme neu gestartet.

* **Anlage**: [Die Adresse ohne Klasse](/mechanismen/adresse-ohne-klasse.md) - `ACT23_EIG_DIREKT`
  gebaut, der Schritt, den der Befund davor als naechsten benannt hat. `_direkt_adressieren` sitzt
  als Gegenstueck zu `_try_bind` im selben Blick und macht einen Koerper OHNE Eintrag aus EINER
  Detektion adressierbar (Chromatizitaet, `desc_embed`, Spanne) - der Lebenszyklus faellt damit zum
  ersten Mal WEG statt ergaenzt zu werden. Drei Stellen mussten mit: der Platzhalter `~gesehen`
  (resolve() liefert fuer eine unbekannte Form keinen Namen -- genau daran ist der Weg diskret
  verschlossen; der Fovea-Tracker ueberspringt ihn ausdruecklich), `_probe_entdeckt()` (sonst haelt
  der Erzeuger den Koerper weiter fuer neu und gibt ihm einen zweiten Platz -- der Doppelplatz-Fehler
  vom 21.08.) und die Identitaetspruefung, die hier NICHT abschaltbar ist (eine Direkt-Adresse bleibt
  den ganzen Lauf stehen; geprueft wird gegen die Detektion, nicht gegen die wahre Lage, also ohne
  Privileg). Die Achsen-Wuerfelei steht jetzt als `_adresse_wuerfeln` fuer sich statt kopiert --
  dieselbe Logik lag schon einmal doppelt und die GUI-Kopie fehlte 332 Episoden unbemerkt.
  **GLEICHHEITSPROBE: der Vorgabepfad ist zeichengenau unveraendert** (2x12 Episoden, Seed 4242,
  HEAD gegen Arbeitsstand: 285 inhaltliche Zeilen, 0 Abweichungen; die 14 Rohunterschiede sind
  Pfadname und Wanduhr). **UND EIN BEFUND AUS DEM RAUCHTEST:** auf `ad9d768c` findet der Schalter
  NICHTS vor - alle sieben Koerper haben einen Eintrag (5 Basis-Knoepfe, obj_T und obj_X selbst
  erworben). Das ist die Saettigung in ihrer schaerfsten Form, kein Defekt; gemessen werden kann er
  nur frisch. Drei frische Arme je 140 Episoden laufen (kette / direkt / beides). **Vorgabe 0.**

* **Anlage**: [Die stetige Adressierung im Lauf](/befunde/stetige-adressierung-im-lauf.md) - der
  Einbau aus `ACT23_EIG_STETIG` zum ersten Mal in act23 gefahren, zwei Arme je 150 Episoden aus
  derselben Kopie von `ad9d768c`, sonst Vorgaben. **Nichts loest auf:** grobe Adressierungsfehler
  18/167 = 10,8 % gegen 14/164 = 8,5 % (p = 0,58), Quote 58,7 gegen 56,0 % (p = 0,73), Rueckfall
  7 gegen 10 (p = 0,62), Adress-Median 2,0 gegen 2,2 mm. **Das war die Vorhersage der Sonde** -
  bei `EIG_TOL_FORM=0,5` liegt die stetige Achse praktisch auf dem diskreten Bezug, und auch die
  Nebenrichtungen stimmen ueberein (Achsen je Adresse 1,81 -> 1,91, eindeutig 98,2 -> 99,4 %: die
  stetige Achse trennt minimal weniger, also legt die Wuerfelei haeufiger nach). **Zweck des Laufs
  war die Verifikation des Baus gegen seine Nachbildung, und die ist bestanden**; dazu reproduziert
  `st_aus` den bekannten Vorgabe-Bezug zifferngenau (58,7 %, 18/167, 7 Rueckfall - zum sechsten
  Mal). **Der Baustein ist bestaetigt, die These ist es nicht:** der Einbau ist additiv, die
  Formklassen entstehen weiter, bekommen weiter Knoepfe und verhungern weiter - der erhoffte Gewinn
  soll aber gerade aus dem Wegfall dieses Lebenszyklus kommen. Naechster pruefbarer Schritt waere,
  die Auto-Schleife eine Adresse fuer einen Koerper OHNE Klasse anlegen zu lassen; das ist stetig
  moeglich und diskret nicht. Offen bleiben eine Toleranz (nur 0,5 gefahren) und der GUI-Pfad
  (`_eig_setzen` schreibt kein `EIG_MESS`, faellt auf Namensvergleich zurueck). **Vorgabe bleibt 0.**

* **Anlage**: [Die stetige Formachse ist genauso trennscharf](/befunde/stetige-adressierung-erster-schritt.md)
  - der erste Schritt zur stetigen Adressierung, gemacht mit der Adress-Wiedervorlage: dieselben
  echten Laufszenen, dieselbe Wuerfelei, dieselbe Aufloesung, **nur die Matching-Regel getauscht**
  (Klassenname gegen Abstand im Einbettungsraum). Zwei der drei Toleranzen sind nicht geraten -
  die Farbschwelle ist `colour_openset.TH`, die Formtoleranz RELATIV zum je Lauf gemessenen
  Median-Abstand zweier verschiedener Koerper (1,858). **Ueber fuenf Toleranzen bleiben die groben
  Adressierungsfehler flach** (4,9 | 5,3 | 5,6 | 4,9 | 5,5 | 6,7 %), keine vom Bezug zu
  unterscheiden (p = 0,25 bis 1,00), bei `t0.50` sogar identisch (28 von 568 in beiden). **Der
  Einwand, ein Vektor sei nicht trennscharf genug, ist damit ausgeraeumt.** Was sich mit der
  Toleranz aendert, ist allein der **Rueckfall**: 60,2 % streng, 27,3 % diskret, 16,2 % locker -
  und die Achsenzahl daneben erklaert es (1,81 -> 1,89 -> 2,06): eine lockere Formachse trennt
  weniger, also legt die Wuerfelei mehr Achsen nach. `t1.00` ist nicht bessere Formerkennung,
  sondern fast "Form egal", kompensiert durch Farbe und Groesse. **Die stetige Achse ist also nicht
  besser, sondern ein anderer Punkt auf derselben Tauschkurve** - `t0.75` kauft 6,7 Punkte weniger
  Rueckfall mit 0,6 Punkten mehr groben Fehlern. **Fuer die Frage heisst das: der Weg ist frei, der
  Gewinn nicht belegt** - er muesste aus dem Wegfall des Klassen-Lebenszyklus kommen (Geburt,
  Bestaetigung, Knopf, Verhungern, Saettigung), und den misst die Adressierung per Konstruktion
  nicht. Werkzeug erweitert (`AW_VARIANTEN` kennt jetzt probe-lokale Schluessel STETIG/EMB_TOL/
  SPAN_TOL, die NICHT an pc_act23 durchgereicht werden).

* **Anlage**: [Stetig adressieren statt Klassen vergeben](/fragen/stetige-adressierung.md) - aus
  einer Nutzerfrage nach der urspruenglichen Vorstellung ("dem Netz ein Bild zeigen, die
  Repraesentation abgreifen, damit kommunizieren -- die Sprache des Netzes lernen, ohne ein
  Language-Model zu trainieren"). **Die Haelfte davon ist gebaut:** `desc_embed` liefert genau
  diesen Vektor, existiert fuer JEDES Objekt auch ohne Klassenslot, verschiebt sich mit dem
  Lernen mit, und das Weltmodell konditioniert bereits darauf. **Die andere Haelfte fehlt:** das
  Kommando vergleicht `str(det.get("shape")) != str(form)`, also Klassen-NAMEN aus `resolve(desc)`.
  Erst dieses Etikett hat einen Lebenszyklus - Geburt, Bestaetigung, Knopf, Verhungern; der Vektor
  hat davon nichts. **Und es gilt fuer alle drei Achsen** (Farbe ueber `colours.classify`, Form
  ueber `resolve`, Groesse ueber `groessen_band`). Damit erklaert sich rueckblickend ein ganzer
  Arbeitstag: Bandgrenzen und das oberste Band im 7-mm-Raster, verschmelzungsgeborene Farbklassen
  (`farbe-50`), die ganze Kette aus Vergabe-Engstelle und 29-Episoden-Saettigung - **durchweg
  Diskretisierungsartefakte, keine Wahrnehmungsfehler.** Die Frage ist, ob das Kommando direkt auf
  den stetigen Groessen arbeiten kann (Zielpunkt plus Toleranz statt Tripel aus Namen; bedient per
  "zeig auf das Objekt, nimm den Vektor"). Dann waeren Geburt, Knopfvergabe, Verhungerungsschutz,
  `NOVEL_BODY` und die Saettigung bei sieben Koerpern gegenstandslos. **Dagegen spricht nicht
  wenig:** eine Klasse entscheidet, wann zwei Dinge DASSELBE sind - beim Vektor wird daraus eine
  Schwelle, und Schwellen haben an dieser Stelle schon dreimal eigene Fehler produziert; dazu die
  Verrechnung dreier verschiedener Masse zu einer Entfernung und der gemessene Rauschboden des
  Deskriptors (13-16 % der Klassentrennung schon bei 2 mm). **Billigster erster Schritt, ohne
  Lauf:** die Adress-Wiedervorlage kann beide Adressierungen auf denselben echten Laufszenen
  gegeneinanderstellen. Idee, nichts gebaut, nichts gemessen.

* **Anlage**: [Die Aneignungskette traegt 29 Episoden](/befunde/kette-haelt-30-episoden.md) - der
  Langlauf zur Kette (400 frische Episoden, Erzeuger + freie Vergabe). **Alles Wesentliche passiert
  bis Episode 29:** drei Knoepfe (Ep 21, 26, 29), dazwischen bei Ep 23 die Meldung
  `Probe-Rolle weitergereicht: obj_T ist entdeckt -> obj_X (noch offen: keiner)`. **Danach 371
  Episoden ohne einen weiteren Knopf.** Fuenf Geburten nach der Saettigung (neu-5 bis neu-8), alle
  mit derselben Begruendung verhungert - *"nie stabil wiedererkannt"*, nach 24 bis 27 Episoden;
  freie Koerper gaebe es (obj_red, obj_green, obj_L, obj_U tragen keine Formklasse), aber keine
  Klasse bestaetigt sich dreimal auf demselben. **Eine der drei GEBUNDENEN Klassen stirbt:** neu-4
  auf obj_X nach 145 Episoden - ausgerechnet die, wegen der die Kette gebaut wurde. Der Koerper
  bleibt trotzdem adressierbar (Bloecke nach dem Tod: 10 und 18 Adressierungen), weil der Eintrag
  in `state.OBJECTS` das Sterben der Klasse ueberlebt und Farbe/Groesse weiter greifen - **verloren
  ist der selbst gegebene Name, nicht der Zugriff.** Quote je 100 Ep: 3/17/16/16 %, also Hochlauf
  und dann flach wie im 1109-Episoden-Langlauf. **Der Engpass ist damit nicht mehr die Maschinerie,
  sondern die Welt:** sieben Koerper sind die Obergrenze der Aneignung, erreicht in 29 Episoden;
  alles danach ist Churn. Das ist die schaerfste Fassung von *"laenger laufen lassen bringt
  nichts"* - jetzt mit einem Grund statt einer Beobachtung. **Naechster Schritt ist kein Schalter,
  sondern eine Quelle neuer Geometrie.** Beide Schalter bleiben auf 0.

## 2026-09-15

* **Anlage**: [Der Erzeuger reicht die Probe-Rolle weiter](/befunde/erzeuger-repariert.md) -
  `ACT23_NOVEL_WEITER` gebaut (Vorgabe 0) und zusammen mit der freien Vergabe gemessen.
  `spawn_novel_shape` hatte einen Riegel mit echtem Grund (nach der Entdeckung verwaltet
  `randomize_objects` den Koerper, zusaetzliches Hinstellen fuellte die Szene ueber SCENE_N) - mit
  der Folge, dass es NIE eine zweite neue Form gab. Die Reparatur ist klein, weil der schwierige
  Teil schon dastand: die else-Verzweigung behandelt einen Probe-Koerper ungleich obj_T bereits
  richtig, es fehlte nur die Weitergabe der Rolle. **Und genau der Erzeuger musste es sein** - er
  ist der einzige Pfad, der einen Koerper OHNE Knopf in die Szene stellt (das dritte Rad aus dem
  vorigen Befund).
  **Ergebnis, zwei frische Arme je 140 Episoden:** Knoepfe 1 gegen **3**, adressierte Koerper 6
  gegen **7**. `[Neuheit] Probe-Rolle weitergereicht: obj_T ist entdeckt -> obj_X`, und
  `'neu-4' -> 'Neue Form 5' auf obj_X`. **obj_X wird zum ersten Mal in die Szene gestellt, selbst
  benannt, kommandierbar und 17-mal adressiert** - kein einmaliger Treffer, sondern ein regulaerer
  Teilnehmer. Geburten 4 zu 4: **der Gewinn sind nicht mehr Geburten, sondern dass eine Geburt den
  Knopf erreicht.**
  **Die verhungerte Klasse stirbt erstmals aus dem richtigen Grund:** `neu-2: verhungert nach 27 Ep
  (nie stabil wiedererkannt)`. Die Null im Vorgabearm ist kein gutes Zeichen - dort wird nach dem
  ersten Knopf niemand mehr Kandidat, also kann auch niemand als Kandidat sterben; die
  13-von-13-Meldung aus dem Langlauf war Buchhaltung, keine Auslese. Zum ersten Mal wird der
  Verhungerungsschutz an der Sache gemessen statt an einer Engstelle davor.
  **Ehrliche Grenze, in der Meldung selbst:** "noch offen: keiner" - nach obj_X ist der Vorrat
  leer, die Welt hat sieben Koerper. Der Erzeuger verteilt Rollen, er erfindet keine Objekte.
  Nebenbei nachgemessen: nur die drei Wuerfel sind einzeln-geometrisch; `obj_T` hat zwei Geoms,
  `obj_U` drei - die Verformung trifft also stets nur das erste, was der Kommentar am Erzeuger
  bisher nur fuer obj_X nennt. Quote 7,1 gegen 5,7 % = 10 gegen 8 Lieferungen, sagt nichts.
  **Drei Schalter, eine Kette:** Erzeuger bringt in die Szene, freie Vergabe gibt den Knopf, der
  Verhungerungsschutz entscheidet ueber Leben. Einzeln bewegt keiner etwas.

* **Anlage / Korrektur**: [Die freie Vergabe oeffnet die erste Tuer](/befunde/freie-vergabe-erste-tuer.md)
  - `ACT23_FREIE_VERGABE` gebaut (Vorgabe 0) und gemessen. Der Eingriff ist absichtlich KEIN neuer
  Mechanismus: die Bestaetigungsschranke bleibt, entfernt ist nur die Festverdrahtung auf
  `NOVEL_BODY` - bestaetigt wird gegen den Koerper, auf dem die Klasse sitzt.
  **Der Riegel ist auf:** 2 vergebene Knoepfe gegen 1 (`neu-1` auf obj_T, `neu-3` auf obj_blue mit
  3 von 3 Blicken), zum ersten Mal einer auf einem anderen als dem Probe-Koerper.
  **Das Repertoire wird trotzdem nicht breiter:** der zweite Knopf ging an obj_blue, der ohnehin in
  `state.OBJECTS` steht; die adressierten Koerper sind in beiden Armen dieselben sechs.
  **Zwei weitere Tueren wurden dabei sichtbar.** (a) Drei Kandidaten verhungern vor der
  Bestaetigung (Vorgabearm: 0 - dort wird nach dem ersten Knopf niemand mehr Kandidat, also kann
  auch niemand verhungern). (b) **Korrektur an meiner eigenen Diagnose:** ich hatte geschrieben,
  obj_X werde nie adressiert, "obwohl er die ganze Zeit sichtbar auf dem Tisch liegt" - **im
  frischen Lauf steht er gar nicht in der Szene** (die `after ep`-Zeile fuehrt nur fuenf Koerper,
  obj_X kommt 0 mal im Protokoll vor). Er erscheint nur in Laeufen aus dem gespeicherten Zustand,
  weil `_try_bind` bei der Vergabe den Koerper in `act16.OBJS` eintraegt. Damit schliesst sich ein
  drittes Rad: **ein Koerper braucht die Szene fuer den Knopf und den Knopf fuer die Szene**, und
  als neues Objekt eingefuehrt wird nur der eine Probe-Koerper.
  **Die Reihenfolge ist damit klar:** erst muss die Welt etwas Neues anbieten (`spawn_novel_shape`,
  der tote Erzeuger), dann muss eine junge Klasse lange genug leben (Verhungerungsschutz), und erst
  dann traegt die freie Vergabe. Ich hatte die drei fuer EIN Problem gehalten.
  Eigener Fehler unterwegs: der erste Anlauf stuerzte ab, weil die Mitbewerber-Zeile weiter
  `sum(h)` rechnete, waehrend `hits` jetzt Koerpernamen traegt - behoben durch eine gemeinsame
  Zaehlhilfe `_zaehl` fuer beide Modi. Der Absturz kam ausgerechnet im Moment der zweiten Vergabe.

* **Anlage**: [Die Vergabe-Engstelle, diagnostiziert](/befunde/vergabe-engstelle-diagnose.md) -
  Nutzerauftrag "erst diagnostizieren, nicht bauen". **Die Engstelle liegt eine Ebene tiefer als
  der Langlauf-Befund sagt.** Der Knopf ist fest an `NOVEL_BODY` verdrahtet; ist er vergeben, kehrt
  `_register_open_class` zurueck, BEVOR die Klasse Kandidatin wird (`_bind_hits` bleibt leer), also
  kann `_try_bind` sie nie binden - **genau EINE selbst geborene Klasse je Zustand kann
  kommandierbar werden.** Entscheidend ist aber: **das Eigenschafts-Kommando umgeht das nicht**,
  obwohl es genau dafuer gebaut wurde. Seine drei Aufrufer sind eine Startvariable, die GUI-Felder
  (brauchen einen Menschen) und `_auto_eig_umschreiben`, das nur den BEREITS gewaehlten Koerper
  umetikettiert (`_b = state.selected()[1]`); und `curious_pick` zieht ausschliesslich aus
  `state.OBJECTS`. **Im autonomen Lauf gibt es keinen Pfad, der die Objektliste erweitert** - das
  Werkzeug gegen die Geburt ist nur fuer Objekte benutzbar, die die Geburt hinter sich haben.
  Bezeichnend: `_eig_setzen` (GUI) sucht seinen Koerper aus
  `OBJECTS + SHAPE_KEY + [NOVEL_BODY]` und KANN einen neuen einfuehren - der Mensch kann es, die
  Schleife nicht. Dasselbe Muster wie der zweimal dokumentierte Riss zwischen den zwei
  Auto-Schleifen. **Empirisch bestaetigt** an zwei frischen 300-Episoden-Laeufen: 12 bzw. 4
  Geburten, je **genau 1 vergebener Knopf**, und die adressierten Koerper sind in beiden Laeufen
  dieselben sechs (die fuenf Anfangseintraege plus obj_T, der den einen Knopf bekam) - **obj_X wird
  in 300 Episoden kein einziges Mal adressiert**, obwohl er die ganze Zeit sichtbar auf dem Tisch
  liegt. **Reparaturrichtung:** nicht mehr Probe-Koerper, sondern die Auto-Schleife muss eine
  Eigenschafts-Adresse fuer einen noch nicht gelisteten Koerper anlegen koennen - genau das, was
  `_eig_setzen` fuer den Menschen tut. Offen: ob eine so eingefuehrte Klasse dann auch ueberlebt
  (der Verhungerungsschutz zaehlt ueber Eigenschaften kommandierte als ungeschuetzt) - die
  Engstelle koennte zwei Tueren haben.

* **Anlage**: [fail_w kalibriert](/befunde/fail-w-kalibriert.md) - die Hoehe der `fail_w`-Daempfung,
  nie kalibriert, jetzt gemessen: 6 Werte x 2 Luecken x 5 Seeds, gepaart. **Unerwartetes zuerst:
  alle 946 gedaempften Zeilen sind Fehlschlaege** (davon positiv: 0) - bauartbedingt, weil die
  Route nur `outcome=False` vergibt, aber nirgends notiert. fail_w zu senken heisst also, unsichere
  NEGATIVE leiser zu stellen. **Bei Luecke 1500 monoton fallend, ohne Optimum in der Mitte:**
  0,0 +0,0079 (5/5), 0,1 +0,0031 (5/5), 0,5 -0,0031, 1,0 -0,0092 (je 0/5). Deutung: die unsicher
  zugeordneten Fehlschlaege sind verrauschte Etiketten, weniger ist besser. **Bei Luecke 4000
  flach** - ganze Spanne 0,0016, Vorzeichen Muenzwuerfe. **Der beste Wert darf nicht eingestellt
  werden:** `att_ok = att_full or fail_w > 0.0`, mit 0 wird die Route GANZ abgeschaltet, und der
  Kommentar dort sagt, wogegen sie gebaut wurde - *"a grasp-PREVENTING wrist was unfalsifiable ...
  the world model froze on it (L-Form wrist-112 deadlock)"*. **Die Route existiert gegen eine
  gemessene Blockade, nicht fuer die AUC**, und diese Messung kann die Blockade nicht sehen. Ein
  Optimum am Rand ist hier also kein Einstellwert, sondern eine Warnung, dass die Kennzahl nicht
  misst, wofuer die Sache gebaut wurde. **Empfehlung 0,1 statt 0,3**, falls ueberhaupt - es behaelt
  die Route und die Falsifizierbarkeit; nicht ohne einen Lauf aendern, der auf die Blockade schaut.
  **Bilanz der vier Gewichtungsfragen:** jeder Gewinn ist Nahfeld (Stufe nah +0,0156 / fern -0,0070,
  Verlauf +0,0089 / -0,0049, gespeicherte Daempfung +0,0108 / +0,0013, fail_w 0,3->0,0 +0,0079 /
  +0,0007). Keine Gewichtung verbessert die Verallgemeinerung; die inhaltlichen schaden fern
  wenigstens nicht, die positionsbasierten schon.

* **Anlage**: [Kein Gewichtungsverlauf hilft bei beiden Luecken](/befunde/sanfter-abfall.md) - die
  offene Frage des Vorbefundes, beantwortet mit **nein**. Vier Abklingzeiten
  (`0,1 + 0,9*exp(-Alter/tau)`), dazu die harte Stufe und eine Umkehrung, gegen Luecke 1500 UND
  4000, je 5 Seeds gepaart. **Jedes Schema, das nah hilft, schadet fern** (Stufe +0,0156 / -0,0070,
  tau=1000 +0,0089 / -0,0049, tau=2500 +0,0056 / -0,0042); je flacher, desto mehr verschwindet
  beides. Nicht die Stufe war das Problem, sondern die Positionsgewichtung selbst. **Damit ist der
  Faden zu.**
  **Der Ertrag steckt in der Nullkontrolle, und sie war nicht null:** `tau=20000` ist bei 10322
  Zeilen praktisch flach und kostet trotzdem -0,0108 (0/5). Grund ist ein Fehler in meinem Aufbau -
  der Bezug benutzt die GESPEICHERTEN Gewichte, und die sind nicht gleichfoermig (946 Zeilen auf
  0,3, das ist die `fail_w`-Daempfung unsicher zugeordneter Ausgaenge, 9,2 % des Trainingsteils).
  Ein flaches Schema ersetzt sie durch gleichfoermige, gemessen wird also "gespeichert gegen
  gleichfoermig" - und **die vorhandene Daempfung ist +0,0108 AUC wert**, erstmals beziffert, als
  Nebenprodukt einer Kontrolle fuer etwas anderes. Folge: alle Deltas dieser Reihe enthalten zwei
  Anteile (eigene Wirkung + Verlust der gespeicherten Gewichte); gegen gleichfoermig gerechnet
  stuenden die nahen Werte besser da, an der Kernaussage aendert das nichts, weil bei Luecke 4000
  auch dann alles unter null bleibt. Auch die gespeicherte Daempfung selbst ist ueberwiegend
  Nahfeld (+0,0108 nah, +0,0013 fern).
  **Die Gegenprobe ist nur eine halbe Spiegelung:** die Umkehrung (altes Ende schwer) schadet nah
  wie vorhergesagt und am staerksten von allen (-0,0221), nuetzt fern aber NICHT (-0,0031). Bei
  Luecke 4000 schadet jede Abweichung leicht. Die Naehe-Deutung erklaert die nahe Seite gut und die
  ferne gar nicht - so hingeschrieben, statt die halbe Spiegelung als ganze auszugeben.
  **Neuer Faden:** die Hoehe der `fail_w`-Daempfung (0,3) ist nie kalibriert worden.

* **Anlage**: [Alte Pufferzeilen abwerten](/befunde/alte-zeilen-abwerten.md) - der einzige Faden aus
  dem Gewichtungsbefund, gezogen mit 6 Seeds und vier Schnitten. **Mit Luecke 1500 sah es
  ueberzeugend aus:** alte Zeilen auf Gewicht 0,1, gepaart +0,0075 (ab 1000) und **+0,0115 (ab
  2000), bei 6 von 6 Seeds**, mit sauberer Dosis-Wirkungs-Kurve - Anstieg, Maximum bei 2000,
  Rueckkehr zur Null bei 8000, wobei `ab 8000` die eingebaute Kontrolle ist. Dazu: **Loeschen
  ruiniert** (-0,04 bis -0,05, 0/6), die alten Zeilen tragen also echte Information und sind nur
  ueberrepraesentiert. **Mit Luecke 4000 kehrt sich dasselbe Schema um:** -0,0054 und -0,0094, 0 von
  4 Seeds. Der Grund steht im Docstring von `generalisation_auc` selbst - die "juengsten"
  Trainingszeilen sind zugleich die dem Halteteil NAECHSTEN. **Alte Zeilen abzuwerten kauft NAEHE
  und kostet VERALLGEMEINERUNG**; es ist keine Aussage ueber das Alter der Daten. Fuer den Betrieb
  bleibt ein Rest (zur Laufzeit sagt das Modell immer *jetzt* vorher), aber das ist lokale
  Anpassung, nicht Lernen. **Die Lehre, verallgemeinert:** der Luecken-Parameter schuetzt nur, wenn
  man ihn VARIIERT - bei einer festen Luecke ist ein Schema, das die Naehe betont, nicht von einem
  zu unterscheiden, das die Verallgemeinerung verbessert. *Ein Schema, das Trainingszeilen nach
  ihrer POSITION im Puffer gewichtet, muss immer gegen mindestens zwei Luecken geprueft werden.*
  Ohne diese Kontrolle haette ich den Gewinn aufgeschrieben.

* **Anlage / Widerlegung**: [Keine Hoehergewichtung bringt etwas](/befunde/gewichtung-bringt-nichts.md)
  - der Schlusssatz des Augmentierungs-Befundes ("billiger ueber `weight`") geprueft, fuenf
  Schemata gegen den Bezug, je 3 Seeds, gleicher reiner Halteteil. **Keines hilft:** bestes
  `juengste 2000 nur` +0,0043 (n=2) bei einer Bezugs-Streuung von 0,007, `neuere schwerer` +0,0012,
  `NB-Zeilen 5x` -0,0031, `Fehlschlaege 3x` -0,0103, `Erfolge 3x` -0,0137. **Die Kontrolle hat
  getragen:** beide Klassenrichtungen schaden etwa gleich viel - gemessen wird also nicht "die
  falsifizierende Klasse zaehlt mehr", sondern nur, dass eine Stoerung des Klassenverhaeltnisses
  schadet. Nebenbei korrigiert: der Puffer ist mit 5690 Erfolgen gegen 4632 Fehlschlaege weit
  ausgewogener als das 1053-Ep-Protokoll vermuten liess (550 gegen 288) - es gibt kein
  Klassenungleichgewicht zu reparieren.
  **Die wichtigste Zahl ist eine Gegenprobe, und sie widerlegt mich:** dieselbe Fuenffachgewichtung
  der 690 augmentierbaren Zeilen kostet als DUPLIKAT -0,051, ueber `weight` aber nur **-0,003**.
  Meine Deutung des Augmentierungs-Verlusts als "Umgewichtung" ist damit falsch und auf der
  [Vorseite](/befunde/augmentierung-wirkt-wie-wiederholung.md) als widerlegt gekennzeichnet; ihr
  KERNBEFUND (vorgestellt = wiederholt, +0,0006) bleibt, weil er ein direkter Vergleich ist und an
  keiner Deutung haengt. **Was die -0,051 verursacht, ist offen** - Duplikat und Gewicht sind hier
  nicht dasselbe (Zeilenzahl, Bootstrap-Zug und Stichprobenzahl je Epoche gegen blossen
  Verlustbeitrag), und welcher Unterschied die Zahl traegt, ist ungemessen. Als offene Frage
  hingeschrieben, nicht als zweite Erklaerung.
  Methodisch: zwei Durchgaenge wurden wegen Systemspeicher abgeraeumt. Der erste hinterliess
  NICHTS, weil er erst am Ende druckte; danach auf laufende Ausgabe und eine einzige wiederverwendete
  Modellkopie umgebaut - der zweite Abbruch kostete dadurch nur den letzten Fit.

## 2026-09-14

* **Anlage / ehrliches Negativ**: [Die Augmentierung wirkt wie eine Zeilenwiederholung](/befunde/augmentierung-wirkt-wie-wiederholung.md)
  - statt des bestellten A/B-Laufs offline geprueft, weil die Augmentierung eine reine Funktion
  einer Pufferzeile ist: Minuten statt Stunden, und schaerfer, weil beide Seiten denselben Puffer
  sehen. Halteteil von Hand gebaut (nur echte Zeilen), weil `generalisation_auc` die LETZTEN Zeilen
  testet und eine Vorstellung dort ihr Original im Training haette. **Ergebnis: eine vorgestellte
  Zeile ist von einer exakten Kopie nicht zu unterscheiden.** Voller Puffer: vorgestellt -0,0502,
  wiederholt -0,0513 (Differenz **+0,0011**). Im Regime, fuer das gebaut wurde (nur die 690 Zeilen
  mit gueltigem NB-Block): vorgestellt +0,0154, wiederholt +0,0148 (Differenz **+0,0006**). Das
  erklaert auch das Vorzeichen: im vollen Puffer sind nur 6,7 % augmentierbar und zaehlen danach
  fuenffach - der Verlust ist **Umgewichtung**, kein Fehler der Vorstellung. **Zwei eigene
  Erklaerungen dafuer sind gemessen falsch:** (1) "das Modell ignoriert die Lage" - nein, sie ist
  der zweitwichtigste Block (+0,1458 AUC-Verlust beim Vertauschen, nach der Aktion mit +0,1920);
  (2) "es nutzt sie nur grob" - nein, schon 5 mm Verschiebung des Halteteils kosten +0,0226, 20 mm
  kosten +0,0731. Es bleibt ein Befund ohne bequeme Erklaerung: das Modell behandelt 20 mm als
  deutlich andere Situation und reagiert trotzdem nicht darauf, ob man ihm diese Situation zeigt
  oder die alte wiederholt. **Nebenbefund, dritte unabhaengige Bestaetigung:** der Nachbar-Block
  kostet beim Vertauschen **+0,0000** - das Weltmodell benutzt ihn nicht, und ausgerechnet ihn
  braucht die Augmentierung als Zulaessigkeitsschranke. **Kein A/B-Lauf:** +0,0006 ist bei 150-300
  Episoden nicht aufzuloesen, ein Lauf waere genau das Muster, an dem diese Sitzung schon sieben
  Vergleiche verloren hat. `ACT23_AUGMENT` bleibt auf 0; der Bau bleibt im Code, weil er korrekt
  und unschaedlich ist. Billiger zu haben waere dieselbe Wirkung ueber `weight` bei `observe` --
  eine Zahl statt eines Mechanismus.

* **Anlage**: [Die latente Augmentierung, gebaut](/mechanismen/latente-augmentierung-gebaut.md) -
  `ACT23_AUGMENT` (Vorgabe 0) erzeugt aus einer bestaetigten Erfahrung N vorgestellte Lagen. **Jede
  Regel kommt aus der Daempfungsmessung, keine aus der Annahme:** keine Daempfung nach dem Betrag
  (alle Vorstellungen `weight=1.0`), Schranke ist `delta < d_nah - 40 mm` gedeckelt bei 20 mm, nur
  Verschiebung. **Die Schranke liest, was der Agent ohnehin gesehen hat** - der Nachbarabstand steht
  im NB-Block des Merkmalsvektors, kein zusaetzliches Rendern, keine privilegierte Information.
  Der neue Abstand wird konservativ gesetzt (`d_nah - |delta|`), weil die Richtung zum Nachbarn nur
  mod pi bekannt ist. **Dieselbe Gruppe wie das Original** - sonst landete eine Vorstellung im
  Halteteil, waehrend ihr Original trainiert, und die Guete waere Selbstbetrug. Fehlschlaege werden
  mitaugmentiert, und die Forderung der Idee-Seite ("ein Negativ nur so weit, wie seine Ursache
  erklaert ist") ist dabei schon erfuellt: die Kredit-Zuordnung laesst nur ursaechlich zugeordnete
  Ausgaenge durch, "daneben platziert" kommt als `outcome=None` gar nicht an.
  **Der erste Rauchtest hat den entscheidenden Fehler gefunden:** `ACT23_NEIGHBOURS` steht per
  Vorgabe auf 0, der NB-Block wird dann nie gefuellt (11640 von 12330 Pufferzeilen ohne gueltigen
  Block) - die Schranke oeffnet nie, 8 Episoden ergaben 8 Zeilen und 0 Vorstellungen. **Ein A/B
  haette zwei Stunden gekostet und exakt nichts gemessen.** Der Schalter warnt jetzt laut beim
  Start; bewusst NICHT still mitgeschaltet, weil ein Schalter, der einen zweiten heimlich umlegt,
  jedes A/B mehrdeutig macht. Beide Arme brauchen `ACT23_NEIGHBOURS=1`.
  **Zweiter Rauchtest bestanden:** 8 Episoden -> Weltzeilen 12322 -> 12353, also **+31 statt +7**,
  rund **4,4 Pufferzeilen je physischer Episode**. Im Puffer geprueft: |delta| 10,9-17,9 mm, d_nah
  nie unter 40 mm, Label und alle uebrigen 43 Spalten identisch, Gewicht 1,0.
  **Was NICHT gezeigt ist:** dass ein Griff an der vorgestellten Lage geglueckt WAERE - die
  Daempfungsmessung zeigt nur, dass die WAHRNEHMUNG der Vorhersage entspricht. Die sinnvolle
  Zielgroesse eines A/B ist die Generalisierungs-AUC, nicht die Lieferquote.

* **Ergaenzung**: [Die Daempfungsfunktion](/befunde/daempfungsfunktion.md) um die **Drehung**
  erweitert (`DF_MODUS=dreh`), die auf der Idee-Seite als eigene Messung angekuendigt war.
  **Der praktisch wichtigste Fund ist ein Vorzeichen:** `yaw4` traegt die Drehung sauber (2 bis
  5 Grad Rest ueber alle Koerper), aber **mit UMGEKEHRTEM Vorzeichen** - eine Spiegelung im
  Kamera-/Homographie-Pfad. Die Vorzeichenprobe zeigt es eindeutig: mit `+theta` ist der Rest genau
  `2*theta` (10,0 / 19,2 / 38,1 Grad bei 5 / 10 / 20 Grad), mit `-theta` sind es 1,9 / 2,3 /
  3,3 Grad. **Wer das Vorzeichen raet, faelscht jede vorgestellte Drehung um den doppelten
  Winkel** - und das ist mir beim Bauen der Sonde selbst passiert, weshalb sie jetzt beide
  Konventionen prueft statt eine anzunehmen. **`yaw` (k=2) ist unbrauchbar:** auf den drei Wuerfeln
  ist der Rest gleich theta (die k=2-Phase ist auf einem Quadrat entartet), auf den laenglichen
  Koerpern noch die Haelfte des Winkels. Zwei weitere Vorhersagen fallen: **die Lage ist NICHT
  invariant** (der wahrgenommene Schwerpunkt wandert bei asymmetrischen Koerpern bis 2,5 mm bei
  20 Grad, bei Wuerfeln 0,3 mm), und **der "drehinvariante" Deskriptor ist es nicht** (21 bis 35 %
  der Klassentrennung bei 20 Grad gegen einen Rauschboden von 13 bis 16 %). **Verschiebung und
  Drehung sind wirklich nicht symmetrisch - aber anders als vermutet:** die Idee-Seite gab als
  Grund an, dass der Deskriptor die Phase wegwirft; gemessen ist der Grund, dass die Drehung
  schlicht TEURER ist - 20 Grad kosten so viel Formdrift wie 40 mm Verschiebung. Fuer den Bau:
  Drehungen nur ueber `yaw4` und mit umgekehrtem Vorzeichen, `yaw` herauslassen, den Greifbezug
  mitdrehen, Winkelbereich klein halten.

* **Anlage**: [Die Daempfungsfunktion](/befunde/daempfungsfunktion.md) +
  `src/pc_cvnn/act23_daempfung.py` - die Voraussetzungsmessung der [latenten
  Augmentierung](/fragen/latente-augmentierung.md), seit dem 31.08. offen, jetzt gemacht: 80 echte
  Laufszenen, rund 2400 gepruefte Verschiebungen. **Das Ergebnis kehrt die Annahme um.** Frei
  stehend (Nachbar > 90 mm) ist die Aequivarianz praktisch exakt - 0,33 mm Restfehler bei 40 mm
  Verschiebung, p90 0,76 mm, also **unter einem Prozent von delta**. Eine Daempfung nach dem BETRAG,
  die Intuition hinter "mit abnehmender Intensitaet", waere dort fast ueberfluessig. **In
  Nachbarnaehe bricht nicht der Median, sondern der Schwanz:** der Median bleibt bei 0,52 mm, der
  p90 springt auf 17 mm - keine sanfte Verschlechterung, sondern eine Minderheit vollstaendig
  falscher Vorstellungen. Einwand 1 der Seite ist damit bestaetigt UND verschaerft: der Kontext ist
  nicht *auch* eine Achse, er ist die **einzige**. **Und die Schwelle ist eine bekannte:** es bricht
  genau dort, wo die Verschiebung den Koerper in Verschmelzungsnaehe traegt (>90 mm: bis 40 mm
  sauber | 60-90 mm: bricht bei 30 | <60 mm: bricht bei 10). Brauchbare Regel:
  **`delta < Nachbarabstand - 40 mm`** - die Daempfungsfunktion IST die Verschmelzungsschwelle, in
  delta ausgedrueckt, und damit je Stichprobe aus der Szene selbst berechenbar statt zu schaetzen.
  **Zwei Nebenbefunde fuer den Bau:** (a) die Formeinbettung hat einen **Rauschboden** - schon bei
  2 mm driftet sie um 13-16 % der Klassentrennung und steigt bis 40 mm nur auf 23-27 %; die
  Formkanaele unveraendert zu uebernehmen ist also so genau, wie der Deskriptor ueberhaupt ist.
  (b) **Das Ziel-Latent ist NICHT exakt linear**, sondern auf 12-14 % genau, konstant relativ -
  das **korrigiert die Idee-Seite**, die "EXAKT eine Phasendrehung, per Konstruktion" sagt: das gilt
  fuer den RoPE-Code, aber `encode_world` ist eine Gitter-Interpolation ueber das trainierte
  Zielmodul. Bei 5 mm sind das 0,6 mm und belanglos, bei 40 mm 5,5 mm und damit mehr als die
  Greiftoleranz. Die Drehung ist NICHT mitgemessen und bleibt eine eigene Messung.
  `ebene: pruefstand`: gemessen ist die Wahrnehmung einer verschobenen Szene, nicht der Ausgang
  eines Griffs - und genau das ist die Behauptung, auf der die Augmentierung beruht.

* **Anlage**: [Spanne und Identitaetspruefung im Adress-Nachspiel](/befunde/spanne-ident-wiedervorlage.md)
  + `src/pc_cvnn/act23_adress_wiedervorlage.py`. Nutzerauftrag war, die beiden Schalter mit der
  Wiedervorlage zu pruefen - **die kann das nicht:** sie misst die WAHRNEHMUNG und laedt
  `shape_classifier` neu, waehrend beide Schalter in `pc_act23` sitzen und `perceive_all` gar nicht
  beruehren. Sie haette fuer alle Einstellungen dieselben Zahlen geliefert, und zwar nicht weil die
  Schalter wirkungslos sind, sondern weil das Instrument blind fuer sie ist. Deshalb dieselbe
  Methode eine Ebene hoeher: Adresse auf einer echten Laufszene bilden (Nachbildung der Wuerfelei)
  und aufloesen. **Der Fund, der die Sache erklaert:** in DERSELBEN stehenden Szene bewirken beide
  Schalter **nichts** (2,3 gegen 2,1 %, p = 0,65). Erst mit `AW_VERSATZ=1` - Adresse auf Szene i
  gebildet, auf Szene i+1 aufgeloest - erscheint der Handel: grobe Fehler 3,3 -> 1,8 % (p = 0,0001),
  Rueckfall 27,1 -> 32,7 % (p < 0,0001). **Die Schalter wirken also nicht, weil die Wahrnehmung
  besser wird, sondern weil eine spezifischere Adresse laenger gueltig bleibt** - das beantwortet
  eine seit dem siebten Anlauf offene Frage. Beziffert: je 3000 Adressen 47 vermiedene Fehladressen
  gegen 169 zusaetzliche privilegierte Rueckfaelle, also **rund 3,6 Rueckfaelle je vermiedener
  Fehladresse**. Derselbe Handel wie im Lauf (10,8 -> 3,1 % bei 4,7 -> 10,0 %), nur an 3000 statt
  160 Adressen und in Minuten. **Entschieden ist er damit nicht, nur beziffert.** Zwei eigene
  Fehler dokumentiert: das Neuladen ueber `from pc_cvnn import pc_act23` liefert das ATTRIBUT des
  Paketobjekts, also die alte Instanz - alle vier Varianten waren zifferngenau gleich, bis auf
  `importlib.import_module` umgestellt; und in der ersten Versatz-Fassung lief die
  Identitaetspruefung gegen die ZIEL-Szene, also gegen Information, die die Wuerfelei nicht hat
  (grob fiel dadurch auf 0,1 % - ein Artefakt des Privilegs). Beide Schalter bleiben auf 0.

* **Anlage**: [Die Wiedervorlage](/mechanismen/wiedervorlage.md) + `src/pc_cvnn/act23_wiedervorlage.py`
  - aus der Erkenntnis des Chroma-Nachspiels ein festes Werkzeug gemacht. `pc_act23` protokolliert
  unter `ACT23_DEBUG=1` je Episode die **wahren Lagen aller Koerper** (`[dbg] after ep`) nach
  `log/`; damit laesst sich jede je gefahrene Szene nachstellen und mit bekannter Wahrheit
  befragen - auf der TATSAECHLICHEN Lagenverteilung, beliebig viele Einstellungen auf DENSELBEN
  Szenen, in Minuten statt Stunden. Beliebige Schalter ueber `WV_VARIANTEN`
  ("Name:VAR=WERT,...|Name:...", die erste ist der Bezug), gesetzt per Neuladen von
  `shape_classifier` wie in `act23_relrings_ab.py`, Fisher gegen den Bezug.
  **Es misst absichtlich beides zugleich:** VERFEHLT (keine Detektion am Koerper -> privilegierter
  Rueckfall) und ZERTEILT (mehrere Detektionen am selben Koerper -> Phantomklasse), dazu die
  Neuheits-Aufteilung "auf einem Koerper / Bruchstueck / nirgends". *Ein Gewinn bei VERFEHLT, der
  ZERTEILT mitzieht, ist keiner* - genau diese Verwechslung hat den Chroma-Schnitt zweimal als
  Erfolg erscheinen lassen. Die Detektionen je Koerper werden als **Mittel** ausgewiesen, nicht als
  Median: eine Zerteilung, die nur jede vierte Szene trifft, ist im Median unsichtbar. Gegenprobe
  bestanden - das Werkzeug reproduziert den Befund vom selben Tag aus einem einzigen Aufruf
  (`t1.0` verfehlt 0,0 % bei 4,7 % zerteilt, `t2.2` 1,7 % bei 1,1 %). Grenzen auf der Seite: der
  Yaw steht nicht im Protokoll, die Zeile faellt am Episodenende, der Vorgabe-Glob vermischt 500+
  Protokolle aus allen Projektphasen. **Es ersetzt keinen Lauf** - es sagt vorher, ob einer lohnt.

* **Ruecknahme**: [Der Chroma-Schnitt wird Vorgabe](/entscheidungen/chroma-split-vorgabe.md) auf
  `status: widerlegt`, `ACT_SHAPE_CHROMA_SPLIT` zurueck auf **0**. Die bestellte Nachmessung
  (Nutzen bei TRENNUNG 2,2) ist gemacht, und zwar erstmals **beide Seiten auf denselben Szenen** -
  200 Szenen am Episodenende aus den Laufprotokollen, 783 Koerper:
  `aus 1,1 % verfehlt / 0,6 % zerteilt | 1,0 -> 0,0 / 4,9 | 1,6 -> 0,9 / 1,9 | 2,2 -> 1,1 / 1,1 |
  3,0 -> 1,1 / 1,0`. **Bei 2,2 sind die verfehlten Koerper wieder auf dem Wert OHNE Schnitt.**
  Der Gewinn verschwindet exakt so schnell wie der Schaden - **es gibt keine Einstellung, in der
  der Nutzen bleibt und die Zerteilung weg ist**, weil der Nutzen DAS aggressive Schneiden IST:
  dieselbe Schranke, die einen verschmolzenen Blob trennt, trennt auch einen schattierten
  Einzelkoerper. In Stueckzahlen ist jede Einstellung ein Verlustgeschaeft (bei 1,0: neun
  vermiedene verfehlte Koerper gegen 33 zusaetzlich zerteilte), und ein zerteilter Koerper gebiert
  eine Phantomklasse, waehrend ein verfehlter nur einen privilegierten Rueckfall kostet.
  Schalter und beide Schranken bleiben samt Begruendung im Code. **Methodisch:** die Szenen waren
  nicht verloren - `pc_act23` schreibt sein eigenes Protokoll nach `log/`, und dort stehen die
  `after ep`-Lagen jeder Episode. Das macht die Wiedervorlage zu einem jederzeit verfuegbaren
  Werkzeug, das keinen Lauf kostet.

* **Anlage / Vorbehalt**: [Die verdreifachte Geburtenrate ist reines Phantom](/befunde/geburtenrate-chroma-phantome.md)
  - Nutzerfrage "untersuche die Geburtenrate", 150 Szenen nach den Regeln des Laufs
  (`pc_act16.scatter`, 80 mm Mindestabstand). **Der Chroma-Schnitt erzeugt keinen zusaetzlichen
  Aneignungsdruck, sondern Phantome:** neue Detektionen 14 -> 82, aber die ECHTEN (die einen
  ganzen Koerper bedecken) bleiben bei **13 gegen 13**; der ganze Zuwachs sind 54 Bruchstuecke
  zerteilter Einzelkoerper und 15 Detektionen bei keinem Koerper. Er **zerteilt Einzelkoerper in
  28 % der Szenen** (gegen 1,3 %). **Wie mir das zweimal entgangen ist:** ich habe beide Male den
  MEDIAN der Detektionen je Szene genommen (2,0 bei 2 Koerpern, 4,0 bei 4) - der verdeckt eine
  Zerteilung, die nur jede vierte Szene trifft; das Mittel zeigt sie (4,49). Dazu misst die
  Wiedervorlage den Abstand zur NAECHSTEN Detektion und kann zusaetzliche per Konstruktion nicht
  sehen. **Damit steht die Entscheidung vom selben Tag unter Vorbehalt** - der gemessene Nutzen
  (verfehlte Koerper 20 -> 0) bleibt gueltig, war aber unvollstaendig. `ACT_SHAPE_CHROMA_TRENNUNG`
  2,2 drittelt die Phantome (82 -> 24) bei unveraendert 13 echten, aber ob der Nutzen dort erhalten
  bleibt, ist ungemessen. Nebenbefund: auf den Szenen bei EPISODENBEGINN verfehlt auch der feste
  Schnitt nichts (0 von 600) - der Nutzen stammt aus den Szenen am Episodenende, wo der Arm Objekte
  zusammengeschoben hat. Nutzen und Schaden treten in verschiedenen Phasen derselben Episode auf.

* **Entscheidung**: [Der Chroma-Schnitt wird Vorgabe](/entscheidungen/chroma-split-vorgabe.md) -
  `ACT_SHAPE_CHROMA_SPLIT` steht auf **1** (Nutzerentscheid), mit TRENNUNG 1,0 und TIEFE 3.
  **Begruendet am Wahrnehmungsmass, nicht an der Lieferquote:** Wiedervorlage der Laufszenen,
  1024 Koerper, verfehlte Detektionen 20 -> 0 (p = 2e-06), Preis 0,5 mm Median und ~4 %
  Rechenzeit. Eine Quotenbestaetigung gibt es nicht und wird es nicht geben - Verschmelzung ist
  im Lauf ein 2-%-Phaenomen. Nach [ziel.md](/ziel.md) ist das der richtige Massstab: bewertet
  wird nach Wahrnehmung und Selbstaneignung. **Warnung fuer den naechsten GUI-Lauf:** der
  bestehende `act23_state.pkl` hat seine Formklassen unter der ALTEN Segmentierung gelernt
  (geladen gemessen 66,0 -> 55,7 %, frisch dagegen 13,0 -> 17,0 % zugunsten des Schnitts) - ein
  Quoteneinbruch in den ersten Episoden ist erwartbar und kein Rueckschritt. `STATE_SCHEMA`
  bewusst NICHT hochgezaehlt: die Invariante gilt fuer Strukturaenderungen, hier aendert sich die
  Verteilung der Eingaben, nicht ihre Form - hochzaehlen wuerde den 1053-Episoden-Zustand
  verwerfen. Rueckholbar mit `ACT_SHAPE_CHROMA_SPLIT=0`. Offen und ungemessen: die verdreifachte
  Geburtenrate (12 gegen 4 Klassen, 9 gegen 2 verhungert) - ob das der Aneignung nutzt oder
  schadet.

* **Anlage / Aufloesung**: [Frisch bei null](/befunde/chroma-split-frisch.md) - der Vergleich noch
  einmal mit `ACT23_FRESH=1`, 300 Episoden je Arm, damit jeder Arm seine Formklassen unter seinem
  eigenen Schnitt lernt. **Beide Vorbefunde kehren sich um:** der Quotenverlust reproduziert NICHT
  (17,0 gegen 13,0 % zugunsten des Schnitts, und er steigt im letzten Block noch steil: 29 gegen
  16 %) - der Verlust im vorigen Lauf lag also am veralteten Exemplarbestand. Der
  Adressierungsgewinn reproduziert aber ebenfalls nicht, er kehrt sich um (3,0 gegen 0,7 %,
  p = 0,037), und der Rueckfall auch (26 gegen 13, p = 0,046). **Grund: die Arme sind nicht gleich
  weit** - 12 geborene Klassen gegen 4. Ein frischer Arm, der sich dreimal so viel aneignet,
  adressiert entsprechend viele junge, unkonsolidierte Klassen; grobe Adressfehler messen dort mit,
  *wie viel der Agent sich zutraut*. **Damit ist fuer eine geaenderte Wahrnehmung WEDER der
  geladene NOCH der frische Aufbau sauber** - der eine traegt unpassenden Bestand, der andere
  erzeugt auseinanderlaufende Lernverlaeufe. **Entschieden hat es eine Messung ohne Lauf:** die
  Protokolle enthalten je Episode die wahren Lagen aller Koerper, also lassen sich **die Szenen des
  Laufs nachstellen** und beide Segmentierungen auf denselben Lagen befragen, rein raeumlich.
  Ergebnis ueber 1024 Koerper: **verfehlte Detektionen 20 gegen 0 (p = 2e-06)**, Preis 0,5 mm
  Median, Detektionszahl unveraendert (4 fuer 4 Koerper - es zerschneidet keine Einzelkoerper).
  **Und es erklaert die ganze Serie:** im Lauf ist Verschmelzung ein **2-%**-Phaenomen; meine
  Handsonde mit 5 eng gestellten Koerpern ueberzeichnete sie um **Faktor 15**. Eine Wirkung auf 2 %
  der Wahrnehmungen ist bei 150-300 Episoden nicht aufzuloesen - deshalb blieben sieben
  Armvergleiche nacheinander uneindeutig. Kein Widerspruch zu "alle groben Fehler sind
  Verschmelzung": das war die Zusammensetzung, dies ist die Haeufigkeit. Einschalten ist jetzt eine
  **Entscheidung, keine Messfrage**. Nicht mehr zu versuchen: die Wirkung des Schnitts ueber die
  Lieferquote nachzuweisen.

* **Anlage**: [Die Verschmelzung an der Quelle](/befunde/verschmelzung-chroma-split.md) - nach drei
  gescheiterten Reparaturen an VERBRAUCHERN der Wahrnehmung diesmal an der Segmentierung selbst.
  **Zwei Vermutungen unterwegs widerlegt:** (a) der vorhandene farbfreie Erosions-Split laesst den
  Elternblob in der Liste, und `max(area)` waehlt ihn - gemessen nur 4,5 % der Faelle; der
  eigentliche Fall ist, dass in 29 % GAR KEIN Teil beim Koerper liegt. (b) Pixelweise nach den
  GELERNTEN Farbklassen zu trennen erreicht 99,5 % und wurde trotzdem verworfen: eine neue Farbe
  muss trennbar sein, BEVOR sie eine Klasse hat, sonst haengt die Wahrnehmung eines neuen Objekts
  daran, dass es schon bekannt ist. **Gebaut ist ein unsupervised Chroma-Schnitt** (Lloyd auf der
  Chromatizitaet, Annahmeschranke = `TH` des Farb-Offenmengen-Moduls, also keine neue Zahl), mit
  drei Eigenschaften, jede aus einem der Fehlschlaege gelernt: er **ersetzt** den Elternblob statt
  daneben zu stehen, er **fasst nicht an, was eins bleibt** (exakter Schwerpunkt erhalten), und er
  **rekursiert** (Tiefe 3: Trefferquote 84,5 -> 100 %). **Eine zweite Schranke war noetig und ist
  der interessante Teil:** ein EINZELNER Koerper zerfaellt chromatisch ebenfalls (Deckflaeche gegen
  Seitenflaechen), das kostete bei weit getrennten Koerpern 0,86 -> 3,85 mm und 3 Detektionen fuer
  2 Koerper. Das Unterscheidungsmerkmal ist **raeumlich, nicht farblich** - zwei Koerper haben weit
  getrennte Schwerpunkte, eine Schattierung teilt denselben Koerper in Schichten, deren
  Schwerpunkte fast zusammenfallen. **Lauf (3 Arme je 150 Ep): grobe Adressfehler 3,1 -> 0,6 %
  (p = 0,044), privilegierter Rueckfall 10,0 -> 5,0 % (p = 0,069) -- der erste Eingriff, der beide
  ZUGLEICH senkt** (alle bisherigen tauschten). **Aber die Quote faellt 66,0 -> 55,7 % (p = 0,042),
  und mit Bonferroni 0,025 uebersteht keine der drei Zahlen die Schranke.** Mechanismus-Beleg ohne
  Test: die Adressen im Band `riesig` fallen 21 -> 17 -> 10, die im Band `winzig` steigen 2 -> 3 ->
  10 - die uebergrossen Detektionen verschwinden wirklich. **Eigener Aufbaufehler benannt:** beide
  Chroma-Arme liefen auf einem Zustand, dessen Formklassen aus UNGETEILTEN Komponenten gelernt
  sind; beim Relrings-A/B wurde genau das vermieden (beide Arme `ACT23_FRESH=1`). Der
  Quotenverlust kann deshalb ein Artefakt des veralteten Exemplarbestands sein.
  `evidenz: einzelmessung`. `ACT_SHAPE_CHROMA_SPLIT` bleibt auf 0; der naechste Schritt ist
  derselbe Vergleich frisch bei null, nicht ein weiterer Schalter.

* **Anlage / Widerlegung**: [Die pixelweise Farbbindung](/befunde/farbbindung-pixelweise.md) -
  Weg 2 (Nutzerauftrag), gebaut und gemessen. **Die woertliche Fassung war unmoeglich:** die
  Bindung aus der letzten sauberen Episode zu uebernehmen scheitert daran, dass `_faerbe_neu` je
  Episode alle sieben Farben permutiert - eine uebernommene Klasse ist nicht veraltet, sondern
  systematisch falsch, und es waere wieder die abgeloeste Tabelle. Gebaut wurde die erste Haelfte
  des Wegs mit derselben Episode als Quelle: die Mischchroma ist eine Eigenschaft des
  KOMPONENTENMITTELS, pixelweise gibt es sie nicht. Neue Methode `colour_parts_all` trennt alle
  Farbklassen in EINEM Rendern; `perceive_colour` bleibt unangetastet. **Der Mechanismus ist
  einwandfrei: 34 von 34 und 53 von 53 erreichbaren Koerpern gebunden** (die gemeldeten "34 von
  127" taeuschen - `_offen` zaehlt die drei je Episode geparkten Koerper mit, die nie bindbar sind).
  Pruefstand: Deckung 63 -> 97 %, und die neuen Bindungen sind brauchbarer als die vorhandenen
  (76 gegen 63 %). **Und es aendert nichts:** grobe Adressierungsfehler 3,1 -> 3,8 % (p = 1,00),
  Rueckfall 15 -> 19 (p = 0,59). **Damit ist meine eigene Catch-22-Deutung aus dem vorigen Lauf
  widerlegt** - die Bindung fehlte tatsaechlich bei verschmolzenen Blobs, war aber nicht der Grund,
  warum der Eig-Split scheiterte: mit vollstaendiger Bindung liegt er weiter bei 6,1 % groben
  Fehlern. Die Erklaerung bleibt die aus dem vorigen Lauf: der Split kostet Feinheit in JEDER
  Episode und nuetzt nur in den wenigen verschmolzenen. **Methodisch neu und billig:** der
  halbierte Median (3,2 -> 1,4 mm) sieht nach Gewinn aus, liegt aber genauso in den 119 Episoden,
  in denen der Mechanismus gar nicht gefeuert hat - *wenn ein Gewinn auch dort auftritt, wo der
  Eingriff nicht gegriffen hat, ist er keiner.* `ACT23_BINDUNG_SPLIT` bleibt auf 0, der Schalter
  bleibt: er ist die einzige Fassung, die verschmolzene Koerper ueberhaupt bindet. Ausdruecklich
  geschlossen: den Eig-Split ueber eine bessere Farbquelle retten (drei Anlaeufe, drei Negative).

* **Anlage**: [Der Form-Split im Eigenschafts-Pfad schadet](/befunde/eig-split-im-lauf.md) - der
  Nutzerauftrag, gebaut und gemessen. Drei Arme je 150 Episoden (`ACT23_EIG_SPLIT` 0/1/2),
  Vorgabearm reproduziert zum vierten Mal zifferngenau. **Ehrliches Negativ, beide Fassungen
  schlechter:** grobe Adressierungsfehler 3,1 -> 9,9 % (Indiz, p = 0,022) bzw. 8,7 % (immer,
  p = 0,056). **Der Kern ist ein Konstruktionsfehler, kein Kalibrierfehler:** bei der Indiz-Fassung
  erzeugten **alle fuenf** Splits einen groben Fehler, und der Adressfehler ist jedes Mal genau die
  Verschiebung des Splits (93/54/217 mm) - vorher war die Adresse richtig. Das Indiz prueft einen
  ABSTAND, und weit weg liegt das farbreine Material aus zwei Gruenden: Verschmelzung *oder* ein
  falsch gewaehltes Objekt derselben Farbklasse - wobei das falsche Objekt **weiter** weg liegt
  (215 gegen 20-30 mm). **Ein Abstands-Schwellwert siebt also bevorzugt die Verwechslungen heraus,
  nicht die Verschmelzungen.** Ep 119 ist der Lehrfall: obj_X und obj_L teilen sich `farbe-4`, die
  gestufte Form-/Groessenfilterung faengt es nicht ab, weil die Formklasse des verschmolzenen Blobs
  auf keinem der beiden Teile passt. Die Immer-Fassung ist dagegen gutartig (Splits 3,1 % grob),
  kostet aber Feinheit (Median 5,8 statt 1,4 mm) - und ihre schlechten Adressen sind die **ohne**
  Split (30,3 % grob). **Daraus die Catch-22, der wertvollste Teil:** der Split braucht
  `colour_of_body`, und `_farbbindung_neu` ueberspringt verschmolzene Blobs per Bauart - **die
  Rettung ist genau in den Episoden nicht verfuegbar, fuer die sie gebaut wurde.** Das gilt fuer
  jeden Rettungsweg ueber die gebundene Farbklasse, auch fuer den Form-Pfad. Dazu die **fuenfte
  Pruefstandsfalle, erstmals mit Vorwarnung**: die Kalibrierseite sagte "immer trennen ist besser"
  (8,5 -> 5,8 mm, 11,9 -> 1,5 %), im Lauf kehrt sich beides um, und der Grund (Lagenverteilung der
  Sonde) stand vorher unter *Fallen* auf derselben Seite. **Eine benannte Einschraenkung ersetzt
  keine Messung.** `ACT23_EIG_SPLIT` bleibt auf 0.

* **Ergaenzung**: [Beim Trennen entscheidet die Farbquelle](/befunde/eig-split-farbquelle.md) -
  Nebenbefund "immer trennen ist besser" als im Lauf entkraeftet gekennzeichnet. Die Hauptaussage
  (gebundene Farbe statt Tripel-Farbe) bleibt gueltig: sie wurde im Lauf nicht gegeneinander
  geprueft, sondern durchgehend gebunden verwendet.

* **Anlage**: [Beim Trennen entscheidet die Farbquelle](/befunde/eig-split-farbquelle.md) -
  Kalibrierung vor dem Einbau des Form-Splits in den Eigenschafts-Pfad (Nutzerauftrag). Gesucht war
  nur der Schnitt fuer das Verschmelzungs-Indiz; gefunden wurde, dass meine erste Fassung die Sache
  **verschlimmert** haette. Ueber 480 Lagen, nur die verschmolzenen Faelle (n = 148): nichts tun
  18,2 mm Median und 38,5 % ueber 20 mm; Split auf der **Tripel-Farbe** 33,2 mm und **98,4 %** -
  schlechter als gar nichts; Split auf der **gebundenen** Farbe (`colour_of_body`) 6,7 mm und
  1,4 %. Grund: die Farbachse des Tripels hat die Wuerfelei AUS der Verschmelzung geschrieben, sie
  ist die Mischchroma-Klasse (im Lauf an den hohen Nummern `farbe-50/59/64` erkennbar) und trennt
  genau das falsche Material heraus. `_farbbindung_neu` ueberspringt verschmolzene Blobs bei der
  Bindung und ist deshalb per Bauart sauber - **der Form-Pfad hat das immer schon richtig gemacht.**
  Schnitt fuer das Indiz auf **0,8** gemessen (72 % erkannt bei 10 % Fehlalarm); mein geratener Wert
  0,7 lag auf einer falschen Groessenordnung. Nebenbefund: ueber ALLE 480 Lagen ist *immer* zu
  trennen besser als der heutige Pfad (8,5 -> 5,8 mm Median, ueber 20 mm 11,9 -> 1,5 %) - deshalb
  sind beide Fassungen gebaut (`ACT23_EIG_SPLIT` 1 = mit Indiz, 2 = immer). `ebene: pruefstand`,
  die Lagenverteilung der Sonde ueberwiegt nahe Nachbarn; welche Fassung traegt, entscheidet das
  laufende A/B, nicht diese Seite.

* **Anlage**: [Jeder grobe Adressfehler sitzt im obersten Band](/befunde/adressfehler-sind-verschmelzung.md)
  - beim Auswerten abgefallen, nicht gesucht, und der wichtigere der beiden Befunde des Tages.
  **26 von 26 groben Adressierungsfehlern liegen im Band `riesig`** (Spanne ab 36 mm); in den
  uebrigen **266 Adressen ueber alle anderen Baender: null** (p = 3,4e-21, und in jedem Arm einzeln
  auch). `riesig` ist faktisch das Band der VERSCHMOLZENEN Blobs - der groesste einzelne Koerper,
  obj_U, misst 37,4 mm. Getragen wird der Fehler von einer einzigen Klasse: `neu-13`, auf einem
  verschmolzenen Blob geboren (17/23 grobe Fehler in einem Arm). **Damit ist der Restfehler des
  siebten Anlaufs lokalisiert und er ist keine Frage der Achse:** die Spanne hat den Fehler nicht
  behoben, sondern ihn an einen Ort gelegt, an dem man ihn sehen kann. Das erklaert rueckwirkend
  auch, warum der Identitaetscheck erst ZUSAMMEN mit der Spanne wirkte. Naechster Schritt, billiger
  als jede weitere Arbeit an der Groessenachse: der **Form-Split existiert bereits** auf dem
  FORM-Pfad (verschmolzener Blob -> Form auf dem farb-getrennten Teil, gemessen 8,8 -> 81 %) und
  **fehlt dem Eigenschafts-Pfad**. Kein neuer Mechanismus, ein vorhandener an zweiter Stelle.

* **Anlage**: [Abstufung statt Privileg](/befunde/abstufung-statt-privileg.md) - der Nutzerauftrag,
  gebaut und gemessen: bei "kein Treffer" die Groessenachse fallen lassen statt auf die wahre Lage
  aus dem Simulator zu greifen. Drei Arme je 150 Episoden (`ACT23_EIG_ABSTUFUNG` 0/1/2), Vorgabearm
  reproduziert `g7_beide` zifferngenau - der Einbau hat den Vorgabepfad nicht angefasst.
  **Ehrliches Negativ.** Die Abstufung greift selten (3 von 6 Gelegenheiten; nur 11 der 15
  Rueckfaelle tragen ueberhaupt ein Band, der Rest scheitert an Farb- oder Formklassen), senkt den
  Rueckfall nur 15 -> 11 (p = 0,54), und einer der drei Faelle adressierte einen **fremden Wuerfel
  65 mm daneben**. **Die vorgesehene Sicherung existiert nicht:** Fassung 1 und 2 sind bitgleich,
  weil der mehrdeutige Fall `1 Treffer` meldet - die anderen zwei Wuerfel kamen gar nicht erst als
  eigene Detektion an. *Eindeutigkeit ist nicht Richtigkeit* zum dritten Mal, mit der neuen
  Folgerung: **beim SCHREIBEN einer Adresse loest die Identitaetspruefung das, beim LESEN nicht** -
  sie vergleicht gegen die wahre Lage und waere im Wahrnehmungspfad genau das Privileg, das die
  Abstufung abschaffen soll. Die grossen Zahlen des Arms (grobe Fehler 3,1 -> 13,1 %, Quote
  66,0 -> 54,7 %) sind **Abdrift, nicht Wirkung**: nur 2 der 23 groben Fehler sind Abstufungen, der
  Lauf ist nach dem ersten Eingriff bei Ep 14 ein anderer Lauf. `ACT23_EIG_ABSTUFUNG` bleibt auf 0.

* **Anlage**: [Das groebere 7-mm-Raster senkt den Rueckfall nicht](/befunde/spannen-raster-7mm.md)
  - die offene Frage des siebten Anlaufs, beantwortet mit **nein**. Drei Arme je 150 Episoden
  (Vorgabe / gemessene Liste / 7-mm-Raster). Der Adressierungsgewinn bleibt (**2,6 gegen 3,1 %**
  grobe Fehler, beide weit unter den 10,8 % der Vorgabe, p = 0,0038), aber der privilegierte
  Rueckfall wird nicht kleiner, sondern **groesser: 20 statt 15, gegen 7 in der Vorgabe**
  (p = 0,0142). **Die Ursache ist nicht die Rasterweite, sondern die Bandzahl:** das gleichmaessige
  Raster haengt ein siebtes Band `gewaltig` (ab 52,5 mm) an. Kein einzelner Koerper wird so gross
  - der groesste, obj_U, misst 37,4 mm -, also landet dort nur ein **verschmolzener Blob**. Wird
  `gewaltig` einmal in ein Eigenschafts-Tripel geschrieben, passt es im naechsten Bild nie wieder:
  6 der 20 Rueckfaelle gehen darauf zurueck, ohne sie waeren es 14 und damit wie beim feinen Arm.
  **Ein offenes oberstes Band ist keine Nachlaessigkeit, sondern haelt den Ausreisser im
  adressierbaren Bereich** - das Aufraeumen zum gleichmaessigen Raster hat es entfernt.
  Nebenbefund: `r7_aus` und `r7_fein` wiederholen `g7_aus` und `g7_beide` **zifferngenau**
  (58,7/66,0 %, 18/167 und 5/159, 7 und 15 Rueckfaelle) - der siebte Anlauf war kein Ausreisser.
  Eigene Falle dokumentiert: ein zweiter Auswerter, der gleiche `[dbg]`-Zeilen entdoppelte, kam
  auf 8/148 statt 18/167 - plausibel aussehend und mit der gemessenen Seite nicht vergleichbar.
  `ACT23_SPANNE_RASTER` bleibt auf `0`.

* **Anlage**: [Die Groessenachse mass die falsche Groesse](/befunde/groessenachse-spanne.md) -
  der siebte Anlauf. **Der Auftrag verschob sich:** bestellt war "das Groessenband feiner",
  gemessen ist die Achse aber nicht zu grob, sondern die **falsche**. Sie nutzte die
  MATERIALDICKE - und alle sieben Koerper liegen dort zwischen 5,61 und 6,08, also im selben Band
  "mittel"; Trennung 0,3-0,7 Streuungen. Die **Spanne** (Ausdehnung, in `perceive_all` laengst
  gerechnet, nie als Adressachse herausgefuehrt) trennt alle fuenf Formen mit 2,2-4,8 Streuungen.
  Dazu ein zweiter Fund beim Lesen: die Wuerfelei prueft beim Achsen-Nachlegen nur die **Anzahl**
  der Treffer, nicht die **Identitaet** - daher 316 von 318 "eindeutigen" Adressen bei 8,8 %
  groben Fehlern. **Faktorielles A/B (4 Arme je 150 Ep) zeigt eine Wechselwirkung:** `span` allein
  p = 0,58, `ident` allein **bitgleich zur Vorgabe** (nie gegriffen), **beide zusammen 10,8 ->
  3,1 %, p = 0,0086**. Grund: der Identitaetscheck kann nur nachlegen, wenn es eine trennende
  Achse gibt - mit der Dicke-Achse landen 75 von 89 Adressen im Band "mittel". *Schloss und
  Schluessel; wer sie einzeln misst, misst zweimal null.* **Preis, real:** der privilegierte
  Rueckfall verdoppelt sich (4,7 -> 10,0 % der Episoden). Beide Vorgaben bleiben 0.

* **Anlage + Selbstkorrektur**:
  [Sechster Anlauf: der Zielkonflikt](/befunde/relrings-split-zielkonflikt.md) - Klassifikation
  und Ausrichtung getrennt (`ACT_SHAPE_RELRINGS=2`: Klasse relativ, Yaw fest; der Greifpunkt
  haengt ohnehin nicht an den Harmonischen). Am Pruefstand bleibt die Klassifikations-Verbesserung
  **exakt** erhalten (25,9 -> 88,9 %). Im Lauf aber: **grobe Adressierungsfehler 2,1 -> 8,8 %
  (p = 0,0003)** gegen 9,8 % bei Fassung 1 - **der Split behebt nichts, meine Ursachenzuschreibung
  war falsch.** Die Quote ist diesmal unauffaellig (20,3 gegen 18,7 %, p = 0,68), der
  Quotenverlust der Fassung 1 ging also wirklich auf den Yaw. **Die wirkliche Ursache der
  Adressierungsfehler ist ein ZIELKONFLIKT:** Groessen-Invarianz macht Klassen breiter - im
  Split-Arm tragen drei Klassen mehrere Koerper statt zwei, darunter `cube` (3 Koerper) und
  `neu-3` (obj_T, obj_U, obj_blue) - und ein Eigenschafts-Tripel trifft dann oefter den falschen.
  21 der 28 groben Fehler haben eine Formachse. **Und 316 von 318 Adressen melden trotzdem "genau
  ein Treffer"** - woertlich "Eindeutigkeit ist nicht Richtigkeit", erstmals als Folge einer
  *Verbesserung*. Lehre: die Groesse war nicht nur ein Mangel des Deskriptors, sondern das, was
  obj_T von obj_U trennt. relrings-im-lauf.md traegt die Korrektur im Kopf.

## 2026-09-13

* **Anlage, ehrliches Negativ**: [Relative Ringe im Lauf](/befunde/relrings-im-lauf.md) - zwei
  FRISCHE Laeufe je 300 Episoden (der gespeicherte Bestand ist mit festen Ringen gerechnet, ein
  Vergleich gegen ihn waere unfair gewesen). **Die Pruefstandsverbesserung schlaegt nicht durch:**
  Geburtenrate identisch (5 zu 5, p = 1,00), Ueberleben 3 gegen 2, **Adressierung messbar
  schlechter** - grobe Fehler >20 mm von 2,1 auf 9,8 % (p = 0,0001), privilegierter Rueckfall
  25 -> 52, Lieferquote 20,3 -> 11,7 %. **Grund:** am selben Deskriptor haengt nicht nur die
  Klasse, sondern auch Greifpunkt und Yaw (`_harmonics_at` -> `_yaw_from`); die Lokalisierung
  verliert mehr, als die Klassifikation gewinnt. **Vierter Fall der
  [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)** - und diesmal war die Vorstufe bereits
  ein direktes Mass. Praezisere Lehre daraus: *ein direktes Mass ist nicht automatisch das
  richtige Mass; `ebene` sagt, WO gemessen wurde, nicht ob ALLES BETROFFENE mitgemessen wurde.*
  [relrings-rueckhalt.md](/befunde/relrings-rueckhalt.md) traegt die Entkraeftung im Kopf.
  Der Schalter bleibt auf 0; ein sechster Anlauf muesste Klassifikation und Lokalisierung
  trennen (feste Ringe fuer Greifpunkt/Yaw, relative nur fuer `resolve()`).

* **Anlage**: [Relative Ringe bestehen den Rueckhalte-Test](/befunde/relrings-rueckhalt.md) - die
  Pruefstandszahl aus [dem fuenften Anlauf](/befunde/groessen-invarianz-fuenfter-anlauf.md) ist am
  direkten Mass geprueft. Zwei **frisch angelernte** Klassifikatoren je Seed (der alte Bestand ist
  mit festen Ringen gerechnet und nicht vergleichbar), getestet an den drei trainierten Formen in
  0,7x bis 2,0x. **Bei den uebergrossen Faellen (>=1,4x): 18,1 % richtig mit festen Ringen, 68,8 %
  mit relativen**, ueber zwei Seeds stabil. Trainingsgenauigkeit bleibt 1,000, `novel_th`
  kalibriert sich gleich, bei 1,0x sind beide gleich gut - **kein Preis bei den bekannten
  Formen.** Ehrlich dazu: Verwechslungen steigen von exakt 0 auf 0,6-1,2 % (der feste Deskriptor
  irrt nie, er **enthaelt sich**; der relative trifft fast immer und irrt gelegentlich), und auch
  relativ bleiben 31 % der uebergrossen Faelle unerkannt - **verbessert, nicht hergestellt.** Neuer
  Schalter `ACT_SHAPE_RELRINGS` (Vorgabe 0). **Die Pruefstandsfalle ist diesmal nicht
  zugeschnappt** - was in diesem Projekt die Ausnahme ist.

## 2026-09-12

* **Anlage**: [Groessen-Invarianz, fuenfter Anlauf](/befunde/groessen-invarianz-fuenfter-anlauf.md)
  - der Hebel aus [Form-Rueckhalte-Test](/befunde/form-rueckhalt.md), neues Werkzeug
  `act23_groessen_invarianz.py`. Die vier bisherigen Fassungen normieren **Amplituden** oder
  skalieren Radien **global**; die Ringe liegen aber weiter an festen Weltradien, also misst
  Ring i bei einem groesseren Objekt eine andere Stelle der Form. Der fuenfte Ansatz haengt die
  Ringe an die **Eigenausdehnung**. Kennzahl K = groesster Groessen- / kleinster Form-Abstand,
  drei Seeds:
  `heute 3,68 | dicke 3,93 | dc 4,25 | fuellung 3,62` gegen `rms 2,37 | sqrtA 2,55 | rmax 2,08`.
  **Die vier alten Fassungen bewegen im selben Aufbau nichts** (ihr Misserfolg ist hier
  repliziert), **die relativen Ringe halbieren die Kennzahl** - und zwar in die richtige
  Richtung: der Form-Abstand *steigt*, der Groessen-Abstand faellt. **Das Ziel unter 1,0 ist
  trotzdem nicht erreicht.** Zwei wichtige Vorbehalte in der Seite: der Aufbau ist haerter als
  der urspruengliche (deshalb wurden die vier alten Fassungen nachgerechnet - sonst waere "2,37
  gegen 2,13" ein scheinbarer Rueckschritt), und ein geaenderter Deskriptor **entwertet den
  gesamten gelernten Klassenbestand** (die 80 Exemplare je Klasse sind mit festen Ringen
  gerechnet, die Masken nicht gespeichert). Empfehlung: nicht einbauen, sondern zuerst den
  Form-Rueckhalte-Test auf einem frisch angelernten Bestand fahren.

* **Anlage**: [Form-Rueckhalte-Test](/befunde/form-rueckhalt.md) - Weg 3 aus
  [Geburtenrate und Saettigung](/befunde/geburtenrate-und-saettigung.md), neues Werkzeug
  `act23_form_rueckhalt.py`. Statt Geburten zu zaehlen wird gefragt, ob eine nie gesehene Form in
  die **passende bestehende** Kategorie faellt. Bilanz ueber 72 Sichtungen: **36,1 % richtig,
  54,2 % neu (uebersegmentiert), 9,7 % falsch.** Aufgeschluesselt eine scharfe Asymmetrie -
  laengliche Formen 69,4 % richtig und **null** Verwechslungen, quadratische 2,8 %. Die
  Groessen-Kontrolle erklaert es: **beide** Kategorien brechen bei rund dem **1,3-fachen** des
  bekannten Masses, unabhaengig von der Form; der Wuerfel ist mit 12 mm nur der kleinste Koerper
  und hatte deshalb keine Luft nach oben. **Der Deskriptor verallgemeinert ueber die PROPORTION**
  (2,9:1 bis 8,5:1 alle als derselbe Balken - genau die Grobkategorie aus der Nutzerfrage)
  **und nicht ueber die GROESSE.** Das bestaetigt
  [Formfaktorisierung](/befunde/formfaktorisierung.md) und beziffert erstmals, was daran haengt:
  die Haelfte aller Verallgemeinerungsfaelle.
* **Klarstellung (Nutzerfrage)**: die Formklassen entstehen **nicht** aus der Fovea, sondern aus
  dem vollen Kamerabild - `perceive_all` -> `_render_u8` (240x240, Arm ausgeblendet) ->
  Saettigungsmaske -> CC-Segmentierung -> komplexe Winkelharmonische auf Polarringen (`RW`
  4-46 mm in Weltmassen). Die Fovea (16x16 Zellen) liefert den BLICK, nicht die Form. Das ist
  genau das Uebergangsgeruest, das [das Projektziel](/ziel.md) abbauen will.

* **Anlage**: [Geburtenrate und Saettigung](/befunde/geburtenrate-und-saettigung.md) - auf zwei
  Nutzerfragen. **(a) Der Neuheits-Erzeuger laeuft seit Langem nicht:** `spawn_novel_shape` kehrt
  in der ersten Zeile zurueck, weil `NOVEL_BODY` (Vorgabe `obj_T`) laengst in `SHAPE_KEY` steht -
  im 906-Episoden-Langlauf kommt `[Neuheit]` **null Mal** vor. Das erklaert auch, warum
  `NOVEL_EVERY=3` im [Schutz-A/B](/befunde/eig-schuetzt-null.md) nichts bewirkte.
  **(b) Die Saettigungshypothese des Nutzers ist bestaetigt, schaerfer als formuliert:** die
  Formklassen SIND bereits Grobkategorien - `cube` fasst drei Koerper zusammen, und `neu-9`
  (obj_T, 21x7) und `neu-285` (obj_X, 21x6) liegen mit 0,66 x novel_th **naeher beieinander als
  die Streuung innerhalb einer einzelnen Klasse** (neu-13: 1,14). Zwei Klassen, eine Kategorie.
  **(c) Die Haelfte des Neuheitsvorrats ist gar nicht neu:** die langen duennen Varianten
  (30x4, 32x5) werden als `neu-9` erkannt - korrekte Verallgemeinerung, keine Fehlfunktion.
  **Folge fuer die Messweise:** "mehr Geburten" ist kein gutes Ziel; in einer Welt mit vier
  Grobformen ist eine hohe Geburtenrate ein Zeichen von Uebersegmentierung. Die richtige Frage
  ist, ob ein NEUES Objekt in die passende bestehende Kategorie faellt - ein Form-Rueckhalte-Test
  nach dem Muster des [Farb-Tests](/befunde/farbe-form-rueckhalt.md), und der kostet keinen Lauf.

## 2026-09-11

* **Anlage, ehrliches Negativ**: [Der Eigenschafts-Schutz wirkt nicht](/befunde/eig-schuetzt-null.md)
  - der Langlauf mit `ACT23_EIG_SCHUETZT=1` gegen einen Kontrollarm, je 400 Episoden. Die Arme
  sind **bitgleich** - nicht "statistisch gleich", sondern jede Zeile identisch. Der Schalter hat
  nie eine Entscheidung geaendert. **Ursache ist ein Konstruktionsfehler meines Entwurfs:**
  `state.EIGENSCHAFT` ist ein Verzeichnis Koerper -> Tripel und wird je Koerper ueberschrieben,
  der Schutz liest also einen Schnappschuss statt einer Historie - und haelt genau so lange, wie
  die Klasse ohnehin zu jung zum Sterben ist. **Damit ist auch meine Begruendung entkraeftet**
  ("der Aufraeumer entfernt, was der Agent benutzt"): gemessen ueberleben die adressierten Klassen
  ohnehin, und die sterbenden werden schlicht nie adressiert - 5 Kommandos auf 5 junge Klassen
  gegen 107 auf die vier etablierten. Der Zaehler-Fix aus Schritt 1 hat sich trotzdem bezahlt
  gemacht: erst durch ihn ist "stirbt trotz Benutzung" von "stirbt mangels Benutzung"
  unterscheidbar. Nebenbefund, ungeklaert: trotz verdoppelter Neuheitsrate (`NOVEL_EVERY=3`) nur
  5 Geburten auf 400 Episoden - die Geburtenrate haengt kaum an diesem Schalter.

* **Anlage**: [Der blinde Fleck der Aneignung](/befunde/aneignung-blinder-fleck.md) - die zwei
  kleinen Schritte vor der latenten Augmentierung. Es sind **zwei Stellen mit demselben Fehler**:
  der Aneignungs-Zaehler (`pc_act23.py:4547`) verfaelscht die MESSUNG, der Verhungerungsschutz
  (`:2896`) veraendert das VERHALTEN - `_starve_and_cap` loescht nach 25 Blicken jede
  ungeschuetzte Klasse, und ueber Eigenschaften kommandierte gelten als ungeschuetzt. **Die
  Aufraeum-Mechanik entfernt damit genau die Klassen, die der Agent benutzt.** Der Zaehler-Fix
  ist unbedingt (eine Reparatur, kein Wahlrecht) und im Rauchtest verifiziert: `neu-285 57 %
  (5x kdo)`, wo vorher `0x` stand; dafuer wurde die Zahl fuer bestehende Klassen ueberhaupt erst
  sichtbar gemacht. Der Schutz liegt hinter `ACT23_EIG_SCHUETZT` (Vorgabe 0) und ist **noch nicht
  messbar**: 13 Geburten auf 906 Episoden = 1,4 %, ein 120-Ep-A/B saehe zwei - keine auswertbare
  Stichprobe. Das steht so in der Seite.

* **Korrektur (eigene, am selben Tag)**:
  [906 Episoden in der entkoppelten Welt](/befunde/langlauf-entkoppelt.md) nachgeschaerft. Die
  erste Fassung sagte "kein Lernproblem, sondern eine Vergabe-Engstelle" - zu grob. Nachgemessen:
  **sechs der dreizehn verhungerten Klassen erreichen 50-75 % Wiedererkennung**, sie funktionieren
  also und sterben trotzdem nach ~25 Episoden. Und: **der Aneignungs-Zaehler hat einen blinden
  Fleck** - er liest `state.SHAPE_KEY` (`pc_act23.py:4547`) und sieht das Eigenschafts-Kommando
  nicht. `neu-373` steht in allen 363 Zeilen mit `kommandiert 0x` und wurde fuenfmal adressiert.
  [Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md) traegt deshalb jetzt einen
  Vorbehalt: fuer die dortigen August-Laeufe gilt die Aussage, wer sie heute nachmisst, misst am
  blinden Fleck vorbei.

* **Anlage**: [906 Episoden in der entkoppelten Welt](/befunde/langlauf-entkoppelt.md) - erster
  Langlauf des Nutzers mit `ACT23_FARB_MISCHUNG=1`, 26,8 h. **Die Quote haelt: 53,1 %**, also das
  alte Niveau - der im [A/B](/befunde/farb-mischung.md) gemessene Einbruch auf 47,6 % tritt NICHT
  ein, die dortige Warnung ("die Seeds widersprechen einander, der Vergleichsarm lag zu hoch")
  war richtig. Adressierung ueber 906 Episoden stabil (1,4 mm, 98,9 % eindeutig). **Eine reine
  FORM-Adresse liefert so gut wie eine Farb-Adresse** (49,8 gegen 53,0 %, p = 0,46) - eine
  Aussage, die es vor der Entkopplung nicht geben konnte. **97 Farb/Form-Kombinationen statt 7.**
  Und trotzdem: 13 Klassen geboren, **keine setzt sich fest**, Bestand am Ende identisch mit dem
  Anfang, unzuordenbare Sichtungen linear 16 -> 227. Alle 13 Geburten melden "kein Knopf zu
  vergeben" - **eine Vergabe-Engstelle, kein Wahrnehmungsproblem.** Nebenbefund: drei neue
  FARBklassen geboren (erwartet waren null), eine davon an obj_U gebunden - bei den Farben
  funktioniert, was bei den Formen stockt.
* **Relativierung**: [Farbe und Form entkoppelt](/befunde/farb-mischung.md) - der dortige
  Quotenbefund (57,5 -> 47,6 %) ist durch den Langlauf entkraeftet.

## 2026-09-10

* **Entscheidung**: `ACT23_FARB_MISCHUNG` steht auf Nutzerentscheid auf **1** - **die entkoppelte
  Welt ist ab jetzt die Standardwelt.** Farbe und Form sind unabhaengig, `colour_of_body` kommt je
  Episode aus der Wahrnehmung. Das ist eine Entscheidung ueber das **Szenario**, nicht ueber eine
  Verbesserung. **Alle Quotenzahlen ab hier sind mit denen davor nicht vergleichbar** - es ist
  eine andere Aufgabe, und wer die Vorgabe zurueckdreht, weil "die Quote gefallen ist", misst das
  Szenario statt eines Fehlers. Geprueft ohne Umgebungsvariable: `[Farbe]`-Zeile je Episode, 0
  neue Farbklassen. Rueckfall: `ACT23_FARB_MISCHUNG=0`. Seite:
  [Farbe und Form entkoppelt](/befunde/farb-mischung.md).

* **Anlage**: [Farbe und Form entkoppelt](/befunde/farb-mischung.md) - auf Nutzerauftrag gebaut
  (`ACT23_FARB_MISCHUNG`, Vorgabe 0): die sieben vorhandenen Koerperfarben werden je Episode
  **permutiert** (keine neuen Farben, sonst gebaeren sie Farbklassen - Kontrolle: 0 neue), und
  **`colour_of_body` kommt je Episode aus der Wahrnehmung** statt aus der persistierten Tabelle,
  mit den drei Wachen der Erstbindung. **Die Adressierung haelt** - Median 1,0-1,4 mm in allen
  vier Armen, Eindeutigkeit unveraendert, privilegierter Rueckfall 4-5 -> 6 %. Die Lieferquote
  faellt gepoolt 57,5 -> 47,6 % (p = 0,039), aber die Seeds widersprechen einander (-1,3 gegen
  -18,3 Punkte) und der Vergleichsarm m23_aus lag mit 63,8 % ohnehin weit ueber dem Ueblichen.
  **Wichtiger Vorbehalt in der Seite:** das ist ein WELT-Wechsel, kein Eingriff - "besser oder
  schlechter" ist die falsche Frage, "haelt die Maschinerie" die richtige, und die Antwort ist ja.
  Nebenwert: unzuordenbare Sichtungen 26 -> 45 in einem Arm, passend zu "vertraute Formen in
  ungewohnten Farben sind neu".

* **Anlage**: [Farb-Rueckhalte-Test](/befunde/farbe-form-rueckhalt.md) - auf Nutzerbeobachtung
  ("die Objekte haben immer die gleiche Farbe"). Nachgezaehlt stimmt sie und ist enger als
  vermutet: der Wuerfel gibt es in **drei** Farben, alle anderen Formen in genau einer, und in
  5 von 6 Farbklassen bestimmt die Farbe die Form eindeutig. Der Rueckhalte-Test (336
  Umfaerbungen) sagt aber: **die Wahrnehmung kuerzt NICHT ueber die Farbe ab** - bei allen
  trainierten Formen haelt die Klasse zu 100 %, der Deskriptor ist farbblind wie konstruiert.
  Freigelegt hat der Test etwas anderes: **obj_X haelt seine Formklasse schon in der EIGENEN
  Farbe nur in 4 von 8 Lagen** und wird meist als "cube" gelesen - die "wandernde
  Deskriptor"-Hypothese, erstmals ausserhalb einer Verschmelzungsszene belegt. Folge fuer die
  Entkopplung: sie wuerde die Formerkennung nicht brechen, sondern diese Schwaeche **aufdecken**.
* **Widerlegung (eigene)**: [Der Nachbar-Block traegt nichts](/befunde/merkmale-kommen-zu-spaet.md)
  - Weg 2a gefahren (Fit nur auf den 690 gueltigen Zeilen, Halteteil nach Zeit mit Luecke, 5
  Seeds): MIT Block AUC 0,603 +- 0,025, OHNE Block 0,599 +- 0,023. **+0,004, also nichts.** Meine
  Erklaerung "das Merkmal ist bloss verduennt" ist damit fuer diesen Block widerlegt. Die
  allgemeine Puffer-Frage bleibt offen, ihr Beispiel faellt weg - wer die Puffer-Architektur
  angeht, braucht ein Merkmal, von dem vorher gezeigt ist, dass es Signal traegt.

* **Entscheidung**: `ACT23_TRACK_KONTINUITAET` steht auf Nutzerentscheid auf **1** - der Tracker
  folgt bei ausgefallener Formklasse dem naechsten Farb-Teil, statt fuer dieses Bild blind zu
  werden. Kein grundsaetzlicher Preis (kein Privileg, rein wahrnehmungsbasiert), Gegenprobe
  sauber (p = 1,0000). **Ausdruecklich kein Quotengewinn** (p = 0,41, Seeds gegenlaeufig).
  Rueckfall: `ACT23_TRACK_KONTINUITAET=0`.

* **Anlage**: [Kontinuitaet statt Neuklassifikation](/befunde/kontinuitaet-statt-neuklassifikation.md)
  - der aus [der Diagnose](/befunde/formsplit-warum.md) empfohlene Weg ist gebaut
  (`ACT23_TRACK_KONTINUITAET`, Vorgabe 0) und im gepaarten Seed-Sweep gemessen. **Die
  Sicherheitsfrage ist sauber**: fremder Belief 8,8 -> 9,2 %, p = 1,0000 - die Ablenker-Bindung
  kommt ueber den klassenfreien Pfad nicht zurueck, die beiden Wachen tragen. **Das Loch ist
  aber kleiner als meine Begruendung nahelegte**: kein einziger Lauf war je ganz blind (0/120 in
  allen vier Armen), der Servo hatte auch ohne die Aenderung in 31-32 % der Anfahrschritte eine
  Beobachtung, und die Kontinuitaet fuellt 1,3-2,2 %. Lieferquote nicht aufgeloest, die Seeds
  widersprechen einander (-3,3 und +11,7 Punkte, gepoolt p = 0,41). Vorgabe bleibt `0`; anders
  als beim Rueckfall-Keim gibt es hier aber **keinen grundsaetzlichen Preis** - die Abwaegung
  steht in der Seite.

## 2026-09-09

* **Anlage**: [Warum der Split die Formklasse verliert](/befunde/formsplit-warum.md) - Diagnose
  vor der Reparatur, mit dem neuen Werkzeug `src/pc_cvnn/act23_formsplit_probe.py`. Beide
  Verdachte bestaetigt, und der eine verursacht den anderen: der Splitteil behaelt nur
  **31-58 %** der Pixel, und der Deskriptor dieser halben Silhouette springt von 0,44-0,53 auf
  **0,94-1,55 x novel_th**, also knapp darueber. **Der Ausfall ist eine ENTHALTUNG, keine
  Verwechslung** - in 55 von 58 Fehlern antwortet `resolve()` mit "neuartig", nur dreimal mit
  einer fremden Klasse. Drei Reparaturwege in der Seite, Empfehlung: **Kontinuitaet statt
  Neuklassifikation** im Tracker (die Identitaet steht seit dem Keim fest, je Bild wird nur die
  Position gebraucht - und die rettet der Split ab 35 mm vollstaendig). Nichts gebaut.

* **Anlage**: [Nachbarnaehe im Lauf](/befunde/nachbarnaehe-im-lauf.md) - die zweite Haelfte der
  Verschmelzungsfrage, ausgezaehlt ueber **1868 Episoden** aus den Protokollen. Der kritische
  Bereich unter 35 mm ist selten (2,1 %), der wirksame ist breiter: **unter 55 mm sind es 15,6 %
  der Episoden, und dort faellt die Quote von 54,9 auf 41,1 % (-13,9 Punkte, p < 0,0001)**, bei
  **7 von 7 Objekten gleichgerichtet** (Vorzeichentest p = 0,0156). Hochgerechnet ~2,2 Punkte der
  Gesamtquote - ausdruecklich als **Obergrenze**, denn Verschmelzung, Rammen des Nachbarn und
  schlechtere Greifpunktwahl sind hier nicht getrennt. **Der interessanteste Teil:** die Schwelle
  im Ausgang (55 mm) folgt der FORMKLASSEN-Rettung (ab 65 mm), nicht der Positions-Rettung (ab
  35 mm) - zu wissen wo etwas ist genuegt nicht, wenn unklar bleibt was es ist. Falle in der
  Seite: die protokollierten `[Farb-Split]`-Zeilen taugen NICHT als Haeufigkeitsmass (eine
  einzige in 1868 Episoden).

* **Anlage**: [Verschmelzung: die Abstandskurve](/befunde/verschmelzung-abstandskurve.md) - der
  seit August offene Faden ist gemessen, mit dem neuen Werkzeug
  `src/pc_cvnn/act23_fusion_probe.py` (864 Konstellationen). Verschmelzung reicht bis ~75 mm
  Mittenabstand und beherrscht alles unter 35 mm; der **Farb-Split rettet ab 35 mm zu 100 %**,
  bei 25 mm nur zu 72 %, bei 15 mm zu 29 %. Die **Formklasse** ueberlebt die Rettung viel
  schlechter als die Position (42 % bei 35 mm, erst ab 65 mm sicher) - das trifft die Formachse
  des Eigenschafts-Kommandos. Zwei Einschraenkungen in der Seite: **ein Paar (obj_X/obj_green)
  verschmilzt bei keinem Abstand**, Verschmelzung ist also paarabhaengig; und die 15-mm-Zeile ist
  ueberwiegend unphysikalisch, weil sich die Koerper dort durchdringen. Ebene `pruefstand` - wie
  oft das im Lauf vorkommt, ist damit NICHT gemessen.

* **Ruecknahme**: `ACT23_KEIM_RUECKFALL` steht auf Nutzerentscheid wieder auf **0**. Die
  Messung hatte keinen Nutzen gezeigt (Fehlstart p = 0,47, Quote p = 0,93), und der Keim kaeme
  aus dem Privileg - das in den Blick-Regelkreis zu lassen widerspricht
  [dem Projektziel](/ziel.md), ohne sich zu bezahlen. Der Schalter bleibt fuer die
  Reproduzierbarkeit stehen. Seite fortgeschrieben:
  [Keim im Rueckfall](/befunde/keim-im-rueckfall.md).

* **Anlage**: [Keim im Rueckfall](/befunde/keim-im-rueckfall.md) - auf Nutzerauftrag setzt der
  privilegierte Rueckfall jetzt auch einen Keim (`ACT23_KEIM_RUECKFALL`, Vorgabe 1). Die Luecke
  ist zu: **Episoden ohne Keim 10 -> 0**. Ein Nutzen ist **nicht nachweisbar** (Fehlstart
  2,9 -> 4,2 %, p = 0,47; Quote 52,9 -> 53,6 %, p = 0,93). Der Grund ist der eigentliche Ertrag:
  die sieben Rueckfall-Episoden sind **Verschmelzungsfaelle** - der gewaehlte Blob sitzt bei
  21 gegen 23 mm bzw. 19 gegen 23 mm fast genau zwischen zwei Koerpern. Gegen einen
  verschmolzenen Blob hilft kein Ortsanker. Der Keim ist privilegiert und wird deshalb als
  `Keim JA (PRIVILEGIERT)` protokolliert. Guenstiger Nebeneffekt: die 5-cm-Sprungschranke greift
  jetzt schon im ersten Bild.

* **Entscheidung**: `ACT23_KEIM_FIX` steht auf Nutzerentscheid jetzt auf **1** - der Tracker
  bekommt beim Eigenschafts-Kommando seinen Keim. Grundlage ist
  [Keim-Fix, A/B](/befunde/keim-fix-ab.md) (Fehlstarts unter mehrdeutigen Szenen 51,5 -> 6,7 %,
  p = 0,0001, beide Seeds gleichgerichtet). Ohne Umgebungsvariable geprueft: `Keim JA`, und der
  Schalter erscheint nicht mehr unter den Abweichungen. **Ausdruecklich nicht mitgekauft:** ein
  Quotengewinn (gepoolt 50,4 -> 52,9 %, p = 0,65). Rueckfall mit `ACT23_KEIM_FIX=0`.

* **Anlage**: [Keim-Fix, A/B](/befunde/keim-fix-ab.md) - der Schluesselfehler aus
  [Der Keim erreicht den Tracker nie](/befunde/keim-erreicht-tracker-nicht.md) ist hinter
  `ACT23_KEIM_FIX` (Vorgabe 0) repariert und gemessen. **Gepaarter Seed-Sweep** nach der Lehre
  aus [Zwei Laeufe sind dieselbe Rechnung](/befunde/laeufe-sind-reproduzierbar.md): 4 Laeufe je
  120 Episoden, zwei Seeds, ein Schnappschuss. Direkte Zielgroesse (Fehlstart unter mehrdeutigen
  Szenen) **51,5 -> 6,7 %, Fisher p = 0,0001**, beide Seeds gleichgerichtet; Keim greift 0 ->
  95/97 %. Lieferquote gepoolt 50,4 -> 52,9 %, **p = 0,65 - die eigene Hochrechnung von 3,5
  Punkten ist damit nicht bestaetigt**. Zwei benannte Restluecken: der privilegierte Rueckfall
  veroeffentlicht keinen Keim (3-5 % der Episoden), und die Kennzahl saettigt, wenn zwei Koerper
  wenige Millimeter auseinanderliegen. Vorgabe bleibt `0`.

## 2026-09-08

* **Anlage**: [Der Keim erreicht den Tracker nie](/befunde/keim-erreicht-tracker-nicht.md) - die
  Anschlussmessung zur Ablenker-Bindung, und sie findet einen **Schluesselfehler**: der
  Eigenschafts-Pfad veroeffentlicht die Erst-Wahrnehmung als `eig:{body}`, der Tracker fragt sie
  unter der Formklasse ab - **120 von 120 Episoden ohne Keim**. Der Tracker startet deshalb auf
  dem wahrscheinlichsten gleichklassigen Blob; bei mehreren Kandidaten (14,2 % der Episoden) sind
  das 41,2 % Fehlstarts, und **kein einziger Fehlstart wurde je geliefert** (0/8 gegen 67/112,
  Fisher p = 0,0011). Herkunft: `0d8c88f` - die "vier Stellen" des Eigenschafts-Kommandos waren
  fuenf. Neue Diagnose `ACT23_KEIMDIAG=1` (Vorgabe aus, rein messend). Reparaturvorschlag und
  geschaetzte Wirkung (~3,5 Punkte, Hochrechnung) stehen in der Seite; **nicht gebaut**.

* **Anlage**: [Der Tracker rastet auf dem Nachbarn ein](/befunde/ablenker-bindung-gemessen.md) -
  auf Nutzerauftrag der erste Schritt an der Ablenker-Bindung. Neue Diagnose
  `ACT16_ABLENKDIAG=1` (Vorgabe aus, privilegiert und rein messend wie `GLAUBDIAG`) zaehlt je
  Episode, auf welchen Koerper der Anfahr-Belief zeigt. Ergebnis ueber 64 Episoden: fremder
  Belief in 31,2 % der gescheiterten gegen 4,2 % der gelieferten Episoden, **Fisher p = 0,0086**
  - und der Belief steht dabei rund **4 mm** neben dem FALSCHEN Koerper, ist also eine sichere
  Bindung, keine Drift. In Episode 48 ab dem ersten Anfahrschritt. Damit ist die schwache
  Permutationskontrolle des Vorlaeuferbefunds ersetzt. Lauf bei 64 statt 150 Episoden beendet
  (Speichernot, GUI des Nutzers hatte Vorrang). Offen bleibt das **Warum** - naechster Schritt
  in der Seite benannt.

* **Anlage**: [Merkmale kommen zu spaet](/befunde/merkmale-kommen-zu-spaet.md) - bei der Suche
  nach naechsten Schritten ausgezaehlt: der Nachbar-Merkmalsblock ist auf **690 von 11563**
  Pufferzeilen gefuellt (6,0 %), der Rest traegt den neutralen "nie gemessen"-Wert. Die in
  [Exekutionsvarianz](/befunde/exekutionsvarianz.md) als "nicht pruefbar" vermerkte Frage ist
  nach 4800 weiteren Episoden immer noch fast nicht pruefbar. Auf den gueltigen Zeilen zeigt der
  Nachbarabstand ausserdem in die **unerwartete** Richtung (naeher = besser, vermutlich
  Lagen-Konfundierung). Folgerung fuer die Architektur: ein nachtraeglich eingefuehrtes Merkmal
  erreicht das Modell nicht - der Engpass ist die Zusammensetzung des Puffers.

* **Anlage**: [Zwei Laeufe sind dieselbe Rechnung](/befunde/laeufe-sind-reproduzierbar.md) - aus
  einer Nutzerbeobachtung in `run_history` ("die letzten drei Laeufe sehen extrem aehnlich aus").
  Sie sind nicht aehnlich: Arm B des Welt-Fit-A/B und der GUI-Lauf vom 08.09. sind ueber alle
  200 Episoden **identisch** - Szene, Objekt, Ausgang, Millimeter. Innerhalb eines Laufs
  wiederholt sich dagegen nichts (94,5 % verschiedene Szenen). Ein Lauf ist damit **eine**
  Stichprobe; die Replikate sind die Seeds.
* **Ergaenzung/Praezisierung**: [Rechnerlast](/befunde/rechnerlast.md) (die 26 Punkte sind
  Schwankung INNERHALB eines Laufs, es gibt keine Wiederholungsstreuung),
  [Kopfloses A/B](/messungen/act23-headless-ab.md) (die Seed-Warnung praeziser gefasst, plus die
  Regel "die Replikate sind die Seeds") und [Sparsamer Welt-Fit,
  A/B](/befunde/welt-fit-plan-ab.md) (beide Arme mit gleichem Seed - bis Ep 18 identisch,
  Reichweite enger als dargestellt).
* **Befund, nicht behoben**: ohne gesetztes `ACT23_SEED` meldet die Kopfzeile `SEED=11`,
  gefahren wird aber mit **7** (`_source_defaults()` nimmt den ersten von drei Treffern im
  Quelltext; die 11 stammt aus zwei Diagnose-Pruefstaenden, die im Steuerungslauf nicht laufen).
  Reproduktionsfalle fuer jeden Lauf ohne Seed. Eine Reparatur erzwingt eine Wahl und ist
  deshalb offen.

* **Entscheidung**: `ACT23_WORLD_FULL_EVERY` steht auf Nutzerentscheid jetzt auf **4** - der
  Welt-Fit laeuft nur noch jede vierte Episode voll, dazwischen 20 Epochen. Grundlage ist
  [das A/B](/befunde/welt-fit-plan-ab.md) (je 200 Episoden, p = 0,92, Selbst-Aneignung gleich,
  61 % mehr Episoden je Stunde). Ohne Umgebungsvariable geprueft: Lernphase 73,1 s voll gegen
  16,3-16,5 s kurz im Muster voll-kurz-kurz-kurz-voll. Sichtbare Alltagsfolge: drei von vier
  Kredit-Zeilen tragen jetzt `, Fit 20 Epochen`. Rueckfall in einer Zeile mit
  `ACT23_WORLD_FULL_EVERY=1`. Seite: [ACT23_WORLD_FULL_EVERY](/entscheidungen/welt-fit-plan.md).

## 2026-09-07

* **Anlage**: [Sparsamer Welt-Fit, A/B](/befunde/welt-fit-plan-ab.md) - `FULL_EVERY=4` gegen die
  Vorgabe `1`, je 200 Episoden im vollen Steuerungslauf, gleichzeitig gefahren. Lieferquote
  51,5 gegen 52,5 % (p = 0,92), Selbst-Aneignung ununterscheidbar (beide Arme gebaeren **keine**
  neue Klasse), Laufzeit 2,95 statt 4,74 h. **Die Pruefstandsvorhersage haelt diesmal auf
  act23-Ebene.** Vorbehalte in der Seite: "Griff hielt nicht" 11,0 gegen 17,0 % (p = 0,11) ist
  der einzige Wert, der gegen B lehnt, und die Anfahrgenauigkeit wurde mangels
  `ACT16_GLAUBDIAG` nicht mitgemessen. Vorgabe bleibt `1`.

* **Anlage**: [ACT23_WORLD_FULL_EVERY](/entscheidungen/welt-fit-plan.md) - auf Nutzerauftrag
  gebaut. Jede n-te Episode voller Fit, dazwischen kurz; **Vorgabe 1 = zifferngenau das
  bisherige Verhalten** (der kurze Zweig wird nicht betreten, `EPOCHS_SHORT` nicht gelesen).
  Umgestellt ist genau eine der sechs `epochs=600`-Stellen; der Anfangsfit (2055) bleibt voll.
  Im echten Lauf auf einer Kopie des 11273-Zeilen-Zustands: Lernphase 73,0/73,1 s voll gegen
  16,6/16,8 s kurz, Kontrolle ohne Schalter 73,4/73,7 s und 0 Markierungen. Die ersten beiden
  Episoden sind in beiden Laeufen zifferngenau gleich.

* **Anlage**: [Welt-Fit: Warmstart](/befunde/welt-fit-warmstart.md) - auf Nutzerfrage zum Hebel
  aus [Episodendauer](/befunde/episodendauer.md). Antwort: `Policy.fit` setzt die Gewichte nie
  zurueck, **der Fit ist bereits ein Warmstart**. Die MSE steht nach EINER Epoche
  (0,0854 -> 0,0844, danach +-0,001 ueber 599 weitere); mu und sigma weichen bei 5 bis 200
  Epochen **weniger** vom 600er-Fit ab als zwei 600er-Fits mit verschiedenen Seeds voneinander.
  Einziger gemessener Vorteil der 600 Epochen: rund dreifache Aufnahmekraft fuer
  widersprechende Erfahrung. Ein Plan "voll alle 4 Episoden, sonst 20" kostet 16,7 statt
  61,1 s je Episode bei ungeklaertem Abstand in der Aufnahme. Nebenbefund: das Modell folgt
  widersprechenden Etiketten in **keiner** Einstellung nennenswert - passt zu AUC 0,489.
  `ebene: pruefstand`, also **kein** Beleg fuer eine Wirkung auf act23.

* **Anlage**: [Rechnerlast und Lieferquote](/befunde/rechnerlast.md) - der lange gehegte Verdacht
  des Nutzers, die Lieferquote haenge an der CPU-Auslastung, ist mit zwei natuerlichen
  Lastfenstern (185 gegen 747 Episoden, p = 0,41, **die beiden Fenster widersprechen einander**)
  und einem Bitgleichheitstest der Physik unter 12-Kern-Volllast widerlegt. Auch die
  Nutzerhypothese "unter Last aendert sich Reibung oder Gravitation" faellt: Rutschquote flach
  (p = 0,51), Griffdruck je Objekt in verschiedene Richtungen, `qpos` auf 17 Stellen identisch.
  Die Seite traegt die **Nachweisgrenze fuer act23-A/Bs**: ein 50-Episoden-Fenster schwankt
  allein aus Zufall um 26 Punkte.
* **Anlage**: [Episodendauer](/befunde/episodendauer.md) - die `Lernen`-Phase ist exakt
  `world.train(600)` (173/173 gegen 759/759 trennscharf) und steigt unter Last von 77 auf 130 s.
  Ein Sprung, keine Rampe: **die Verlangsamung kommt nicht vom wachsenden Wissen.** Nennt den
  ungenutzten Hebel - 600 Epochen ueber 10500 Zeilen je Episode fuer eine neue Zeile.
* **Anlage**: [Ablenker-Bindung in der Anfahrt](/befunde/ablenker-anfahrt.md) - aus einer
  Nutzerbeobachtung zu `[Auto 810]`. Die Adressierung ist entlastet (Median 2 mm, 914/920
  eindeutig), der Fehler sitzt in der Ausfuehrung: 63 von 932 Episoden fahren die erste Anfahrt
  >80 mm daneben und liefern dann 1 von 63. Enthaelt die ehrliche Schwaeche der
  Permutationskontrolle.
* **Ergaenzung**: [Invarianten](/mechanismen/invarianten.md) um zwei Regeln aus dem Startabsturz
  vom 06.09. - `state.OBJECTS` haelt **Adressen, nicht Koerper**, und eine Aenderung am
  persistierten Zustand braucht eine Speichern-Neustart-Runde (alle Sonden liefen mit
  `ACT23_NO_PERSIST=1` und konnten den Fehler prinzipiell nicht finden).

* **Ergaenzung**: die Belege, auf die das Wiki zeigt, sind jetzt selbst versioniert -
  `ARCHITECTURE_2026-07-25.md` (Quelle von [Modullandschaft](/mechanismen/act23-modullandschaft.md)
  und [Laufzeitregeln](/mechanismen/laufzeit-regeln.md)) sowie `act23_exec_variance.py` und
  `act23_split_probe.py` (in [Rohbelege](/raw/index.md) als Messwerkzeuge gelistet, bis dahin als
  einzige der acht nicht im Repo). Ein frischer Klon kann die
  [Messvorschriften](/messungen/exekutionsvarianz-exv.md) damit nachvollziehen.
* **Ergaenzung**: Nutzerentscheid zur offenen Frage aus
  [Wissensbasis als Wiki](/entscheidungen/wissensbasis-als-wiki.md) - **der act23-Teil des
  Memory-Bestands wandert ins Wiki**, die aelteren Akte (act5-act22) bleiben liegen; die alten
  Markdown-Dateien im Wurzelverzeichnis bleiben, wo sie sind, und werden nur referenziert.
* **Anlage**: Uebertragung der act23-Notizen. Neue Mechanismus-Seiten
  [Invarianten](/mechanismen/invarianten.md),
  [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md),
  [Formklassen-Lebenszyklus](/mechanismen/formklassen-lebenszyklus.md),
  [Kredit und Selbst-Urteil](/mechanismen/kredit-und-selbsturteil.md),
  [Fovea und Blick](/mechanismen/fovea-und-blick.md),
  [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md),
  [Ports und Takte](/mechanismen/ports-und-takte.md).
* **Anlage**: neue Befunde [Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md),
  [U-Form-Engpass](/befunde/u-form-engpass.md), [Imitationspuffer](/befunde/imitationspuffer.md),
  [Ablage und Platzieren](/befunde/ablage-und-platzieren.md),
  [Nagelneigung](/befunde/nagelneigung.md),
  [Griff-Glaube und Tastsinn](/befunde/griff-glaube-und-tastsinn.md),
  [Aneignung neuer Formen](/befunde/aneignung-neuer-formen.md),
  [Formfaktorisierung](/befunde/formfaktorisierung.md),
  [Latent-Etappen](/befunde/latent-etappen.md); dazu
  [Latente Augmentierung](/fragen/latente-augmentierung.md).
* **Anlage**: neues Verzeichnis `chronik/` mit der
  [act23-Entwicklungslinie](/chronik/act23.md) - Verdichtung der 1001-zeiligen Volltext-Chronik
  aus dem Memory-Bestand.
* **Anlage**: Wiki aufgesetzt nach [Das Verfahren](/wiki.md) - Struktur, Frontmatter mit
  `evidenz` und `ebene`, Katalog und Chronik. Vorlagen: LLM Wiki (Karpathy) fuer die Idee,
  Open Knowledge Format v0.2 fuer das Format; angepasst darauf, dass das Wissen hier selbst
  erzeugt wird statt von aussen zu kommen.
* **Anlage**: [Projektziel](/ziel.md), [Die Wissensbasis wird ein Wiki im Repo](/entscheidungen/wissensbasis-als-wiki.md).
* **Anlage**: Mechanismen - [Modullandschaft](/mechanismen/act23-modullandschaft.md),
  [Laufzeitregeln](/mechanismen/laufzeit-regeln.md),
  [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md).
* **Anlage**: Befunde - [Exekutionsvarianz](/befunde/exekutionsvarianz.md),
  [1109 Episoden ohne Lernfortschritt](/befunde/langlauf-ohne-fortschritt.md),
  [Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md),
  [Greif-Lerndeckel](/befunde/greif-lerndeckel.md). Alle vier verdichtet aus dem
  Memory-Bestand, nicht neu gemessen.
* **Anlage**: Messvorschriften [kopfloses A/B](/messungen/act23-headless-ab.md) und
  [EXV](/messungen/exekutionsvarianz-exv.md); [offene Faeden](/fragen/offene-faeden-act23.md);
  [Rohbelege](/raw/index.md).
* **Anlage**: `CLAUDE.md` im Wurzelverzeichnis als Schemaschicht - sie verpflichtet jeden
  Agenten, das Wiki zu lesen und fortzuschreiben.

## Davor

Das Projektwissen lag bis hierher im agenteneigenen Memory-Bestand und in verstreuten
Markdown-Dateien im Wurzelverzeichnis. Deren Chronik ist nicht rueckwirkend aufgearbeitet;
`generated.at` auf den einzelnen Seiten traegt das Datum der urspruenglichen Messung.
