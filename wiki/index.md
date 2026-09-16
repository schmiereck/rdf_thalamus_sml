---
okf_version: "0.2"
---

# Einstieg

* [Das Verfahren](wiki.md) - wie dieses Wiki funktioniert: Aufbau, Frontmatter, Operationen
* [Projektziel und Erfolgskriterium](ziel.md) - die Architektur soll selbst lernen; den Teacher zu schlagen ist nicht verlangt
* [Chronik](log.md) - was wann ins Wiki eingetragen wurde
* [Rohbelege](raw/index.md) - Laufprotokolle, Werkzeuge, Zustaende, aeltere Dokumente

Fuer act23-Arbeit in dieser Reihenfolge:
[Modullandschaft](mechanismen/act23-modullandschaft.md) →
[Invarianten](mechanismen/invarianten.md) →
[offene Faeden](fragen/offene-faeden-act23.md).

# Mechanismen

* [act23 Modullandschaft](mechanismen/act23-modullandschaft.md) - welche Module aktiv sind, was jedes steuert, wo die komplexe Zahl traegt
* [Invarianten](mechanismen/invarianten.md) - was man nicht verletzen darf; jede Regel aus einem konkreten Schaden
* [Laufzeitregeln](mechanismen/laufzeit-regeln.md) - was noch geskriptet ist; act21 hat die Entwoehnung geschafft, act23 nicht
* [Die Pruefstandsfalle](mechanismen/pruefstandsfalle.md) - isolierte Messungen sagen act23 dreimal falsch vorher; deshalb das Feld `ebene`
* [Wahrnehmungs-Splits](mechanismen/wahrnehmungs-splits.md) - verschmolzene Blobs, drei Reparaturen, der am besten belegte Gewinn der Wahrnehmungslinie
* [Formklassen-Lebenszyklus](mechanismen/formklassen-lebenszyklus.md) - Geburt, namenloses Fenster, Bindung, Anspruch, Verhungern, Einfrieren
* [Kredit und Selbst-Urteil](mechanismen/kredit-und-selbsturteil.md) - der Agent beurteilt sich selbst und verteilt die Schuld; drei Regeln aus drei Vergiftungen
* [Fovea und Blicksteuerung](mechanismen/fovea-und-blick.md) - detektorfreier Blick, Drift 38 → 8,5 px; kein Lieferhebel
* [Eigenschafts-Kommando](mechanismen/eigenschafts-kommando.md) - Farbe + Form + Groesse statt Name; Eindeutigkeit ist nicht Richtigkeit
* [Ports und Takte](mechanismen/ports-und-takte.md) - der Port-Umbau und die Bitgleichheits-Pruefung; Traegheit nur im Planer

# Befunde

* [Exekutionsvarianz](befunde/exekutionsvarianz.md) - ICC 0,61, Obergrenze 82 % gegen Grundrate 54 %; der Deckel sitzt in der Situationsrepraesentation
* [1109 Episoden ohne Lernfortschritt](befunde/langlauf-ohne-fortschritt.md) - 43 h GUI-Lauf, vier unabhaengige Groessen flach
* [Selbst-Aneignung stockt](befunde/selbstaneignung-stockt.md) - 17/17 und 14/14 selbst geborene Klassen verhungern, keine je kommandiert
* [Aneignung neuer Formen](befunde/aneignung-neuer-formen.md) - obj_Y selbst angeeignet in 15 Episoden; die Uebertragung traegt ueber die Armbreite
* [Greif-Lerndeckel](befunde/greif-lerndeckel.md) - der Teacher ist die praktische Decke; enthaelt die gelungene Gegenprobe im signalreichen Regime
* [Wrist-Ausrichtung](befunde/wrist-ausrichtung.md) - schraeg 17 % gegen 35 %; einmal selbst gelernt, live nicht, weil die Gegenbeispiele fehlen
* [U-Form-Engpass](befunde/u-form-engpass.md) - fuenf Anlaeufe im Aktionsraum, alle <= Ausgangslage; der Schlitz-Greifpunkt ist folgenlos
* [Imitationspuffer](befunde/imitationspuffer.md) - mehr und bessere Daten bringen beide nichts; die Nullsummen-Diagnose
* [Ablage und Platzieren](befunde/ablage-und-platzieren.md) - nur die seitliche Genauigkeit zaehlt (r = 0,98); die Ablegehoehe nicht
* [Nagelneigung](befunde/nagelneigung.md) - der Nagel traegt 95 % der Griffkraft und bewirkt auf act23-Ebene nichts
* [Griff-Glaube und Tastsinn](befunde/griff-glaube-und-tastsinn.md) - es gibt keinen Glaubensfehler, und der Fingerdruck traegt die Schliess-Entscheidung nicht
* [Formfaktorisierung](befunde/formfaktorisierung.md) - die Groesse dominiert die Form und laesst sich nicht herausnormieren
* [Latent-Etappen](befunde/latent-etappen.md) - eine tot, eine schlafend, der Attraktor schaedlich
* [Rechnerlast und Lieferquote](befunde/rechnerlast.md) - der alte Verdacht ist widerlegt; enthaelt die Nachweisgrenze: 50 Episoden schwanken um 26 Punkte
* [Episodendauer](befunde/episodendauer.md) - die Lernphase IST der Welt-Fit; Last kostet 53 s je Episode, Wachstum nichts
* [Welt-Fit: Warmstart](befunde/welt-fit-warmstart.md) - der Fit ist schon warm und nach EINER Epoche konvergiert; die 600 Epochen kaufen nur Aufnahmekraft
* [Sparsamer Welt-Fit, A/B](befunde/welt-fit-plan-ab.md) - 200 gegen 200 Episoden: Quote und Aneignung gleich, Laufzeit 2,95 statt 4,74 h
* [Zwei Laeufe sind dieselbe Rechnung](befunde/laeufe-sind-reproduzierbar.md) - gleiche Einstellung heisst bitgleicher Lauf; die Replikate sind die Seeds. Enthaelt die Seed-Falle in der Kopfzeile
* [Der Nachbar-Block traegt nichts](befunde/merkmale-kommen-zu-spaet.md) - steht auf 6 % der Zeilen, bringt aber auch unverduennt +0,004 AUC; meine Verduennungs-Erklaerung ist widerlegt
* [Der Tracker rastet auf dem Nachbarn ein](befunde/ablenker-bindung-gemessen.md) - direkt gemessen: fremder Belief 31,2 gegen 4,2 % (p = 0,0086), auf 4 mm genau am FALSCHEN Koerper
* [Der Keim erreicht den Tracker nie](befunde/keim-erreicht-tracker-nicht.md) - Schluesselfehler, 120 von 120; bei mehreren Kandidaten 41 % Fehlstart, davon 0 geliefert
* [Keim-Fix, A/B](befunde/keim-fix-ab.md) - Fehlstarts 51,5 -> 6,7 % (p = 0,0001, gepaart ueber zwei Seeds); **Vorgabe seit 2026-09-09**, die Quote bleibt unbelegt
* [Keim im Rueckfall](befunde/keim-im-rueckfall.md) - Luecke zu (10 -> 0), Nutzen nicht nachweisbar, **wieder abgeschaltet**; die Rueckfall-Faelle sind Verschmelzungen
* [Verschmelzung: die Abstandskurve](befunde/verschmelzung-abstandskurve.md) - Split traegt ab 35 mm, bei 25 mm nur 72 %; die Formklasse ueberlebt viel schlechter als die Position
* [Nachbarnaehe im Lauf](befunde/nachbarnaehe-im-lauf.md) - unter 55 mm faellt die Quote um 13,9 Punkte (p < 0,0001, 7/7 Objekte gleich); betrifft 15,6 % der Episoden
* [Warum der Split die Formklasse verliert](befunde/formsplit-warum.md) - halbe Silhouette (31-58 %), Deskriptor knapp ueber novel_th; der Ausfall ist eine Enthaltung
* [Kontinuitaet statt Neuklassifikation](befunde/kontinuitaet-statt-neuklassifikation.md) - **Vorgabe seit 2026-09-10**; sauber, aber das Loch ist klein (1-2 % der Schritte), Gegenprobe p = 1,0
* [Farb-Rueckhalte-Test](befunde/farbe-form-rueckhalt.md) - die Formerkennung kuerzt NICHT ueber die Farbe ab; dafuer wackelt obj_X schon in seiner eigenen Farbe (4/8 Lagen)
* [Farbe und Form entkoppelt](befunde/farb-mischung.md) - **Standardwelt seit 2026-09-10**: Farben je Episode permutiert, `colour_of_body` aus der Wahrnehmung; die Adressierung haelt
* [906 Episoden in der entkoppelten Welt](befunde/langlauf-entkoppelt.md) - Quote haelt (53,1 %), Form-Adressen tragen, 97 Kombinationen - und trotzdem keine einzige neue Formklasse
* [Der blinde Fleck der Aneignung](befunde/aneignung-blinder-fleck.md) - Zaehler und Verhungerungsschutz sehen nur den Knopf; der Zaehler-Fix ist gebaut und verifiziert
* [Der Eigenschafts-Schutz wirkt nicht](befunde/eig-schuetzt-null.md) - zwei 400-Ep-Arme BITGLEICH; der Schutz liest einen Schnappschuss statt einer Historie
* [Geburtenrate und Saettigung](befunde/geburtenrate-und-saettigung.md) - der Neuheits-Erzeuger laeuft gar nicht, und die Formklassen SIND bereits Grobkategorien
* [Form-Rueckhalte-Test](befunde/form-rueckhalt.md) - verallgemeinert wird ueber die Proportion, nicht ueber die Groesse; ab Faktor 1,3 ist alles "neuartig"
* [Groessen-Invarianz, fuenfter Anlauf](befunde/groessen-invarianz-fuenfter-anlauf.md) - Ringe an der Eigenausdehnung halbieren die Kennzahl; Ziel trotzdem nicht erreicht
* [Relative Ringe bestehen den Rueckhalte-Test](befunde/relrings-rueckhalt.md) - uebergrosse Formen 18 -> 69 % richtig erkannt, ohne Preis bei den bekannten
* [Relative Ringe im Lauf](befunde/relrings-im-lauf.md) - **entkraeftet den vorigen**: kein Aneignungsgewinn, und die Lokalisierung leidet (grobe Fehler 2,1 -> 9,8 %)
* [Sechster Anlauf: der Zielkonflikt](befunde/relrings-split-zielkonflikt.md) - Trennung behebt nichts; Groessen-Invarianz macht Klassen breiter und Adressen mehrdeutig
* [Die Groessenachse mass die falsche Groesse](befunde/groessenachse-spanne.md) - Spanne statt Dicke, plus Identitaetspruefung: grobe Fehler 10,8 -> 3,1 %, aber nur ZUSAMMEN
* [Das groebere 7-mm-Raster senkt den Rueckfall nicht](befunde/spannen-raster-7mm.md) - es verdreifacht ihn, wegen des zusaetzlichen OBERSTEN Bandes; Wiederholungsarm reproduziert den siebten Anlauf zifferngenau
* [Abstufung statt Privileg](befunde/abstufung-statt-privileg.md) - Groessenachse fallen lassen statt zu privilegieren: gebaut, aber selten wirksam und OHNE unprivilegierte Sicherung
* [Jeder grobe Adressfehler sitzt im obersten Band](befunde/adressfehler-sind-verschmelzung.md) - 26 von 26 in "riesig", 0 von 266 sonst: die Adressierung hat ein VERSCHMELZUNGS-Problem, kein Groessenproblem
* [Beim Trennen entscheidet die Farbquelle](befunde/eig-split-farbquelle.md) - Split auf der Tripel-Farbe macht den Fehler DREIMAL groesser, auf der gebundenen Farbe faellt er auf ein Viertel
* [Der Form-Split im Eigenschafts-Pfad schadet](befunde/eig-split-im-lauf.md) - das Abstands-Indiz siebt Verwechslungen statt Verschmelzungen; und die Farbbindung fehlt per Bauart genau bei verschmolzenen Blobs
* [Die pixelweise Farbbindung](befunde/farbbindung-pixelweise.md) - bindet 34 von 34 erreichbaren Koerpern, die der Komponenten-Durchgang auslaesst, und aendert an der Zielgroesse NICHTS (p = 1,00)
* [Die Verschmelzung an der Quelle](befunde/verschmelzung-chroma-split.md) - unsupervised Chroma-Schnitt in `perceive_all`: grobe Adressfehler 3,1 -> 0,6 %, Rueckfall 10,0 -> 5,0 %, aber Quote 66,0 -> 55,7 %; nichts uebersteht Bonferroni
* [Frisch bei null](befunde/chroma-split-frisch.md) - **die Wiedervorlage der Laufszenen entscheidet:** verfehlte Detektionen 20/1024 -> 0 (p = 2e-06), und Verschmelzung ist im Lauf ein 2-%-Phaenomen, nicht 29 %
* [Chroma-Schnitt wird Vorgabe](entscheidungen/chroma-split-vorgabe.md) - **zurueckgenommen am selben Tag**; `ACT_SHAPE_CHROMA_SPLIT` steht wieder auf 0
* [Die verdreifachte Geburtenrate ist reines Phantom](befunde/geburtenrate-chroma-phantome.md) - echte neue Detektionen 13 gegen 13, Bruchstuecke 54 gegen 0; und **Nutzen und Schaden sind gekoppelt** - es gibt keine Schranke, die das eine ohne das andere hat
* [Die Wiedervorlage](mechanismen/wiedervorlage.md) - **Werkzeug**: Wahrnehmungsaenderungen auf den echten Laufszenen pruefen, in Minuten statt Stunden; misst Nutzen UND Schaden zugleich
* [Spanne und Identitaetspruefung im Adress-Nachspiel](befunde/spanne-ident-wiedervorlage.md) - derselbe Handel wie im Lauf an 3000 statt 160 Adressen, plus die Erklaerung: die Schalter wirken NUR, weil die Adresse ihre Szene ueberlebt
* [Ablenker-Bindung in der Anfahrt](befunde/ablenker-anfahrt.md) - 6,8 % der Episoden fahren >80 mm daneben und liefern dann 1 von 63, obwohl die Adressierung stimmt

# Entscheidungen

* [Vorgaben 2026-08-30](entscheidungen/defaults-2026-08-30.md) - der 1053-Episoden-Zustand wird Standard, samt ehrlichem Vorbehalt zur Greifergeometrie
* [Die Wissensbasis wird ein Wiki im Repo](entscheidungen/wissensbasis-als-wiki.md) - warum, und was daran noch offen ist
* [ACT23_WORLD_FULL_EVERY](entscheidungen/welt-fit-plan.md) - der Welt-Fit laeuft nur noch jede vierte Episode voll; **Vorgabe seit 2026-09-08**, Rueckfall mit n=1

# Messvorschriften

* [Kopfloses A/B im vollen act23-Lauf](messungen/act23-headless-ab.md) - die einzige Ebene, auf der Wirkung behauptet werden darf
* [Wiederholungsmessung EXV](messungen/exekutionsvarianz-exv.md) - trennt Ausfuehrungsstreuung von Situationssignal

# Offene Fragen

* [Offene Faeden in act23](fragen/offene-faeden-act23.md) - geordnet nach belegter Wichtigkeit, mit den ausdruecklich geschlossenen Faeden am Ende
* [Latente Augmentierung](fragen/latente-augmentierung.md) - die Nutzeridee; Voraussetzungsmessung gemacht, Bau erfolgt
* [Stetig adressieren statt Klassen vergeben](fragen/stetige-adressierung.md) - **Nutzeridee, zielnah:** die Aneignungsprobleme (Geburt, Knopf, Verhungern, Saettigung) sind Artefakte der Diskretisierung; `desc_embed` existiert fuer jedes Objekt und stirbt nie
* [Die stetige Formachse ist genauso trennscharf](befunde/stetige-adressierung-erster-schritt.md) - der erste Schritt: der Weg ist frei, ein Gewinn ist es (noch) nicht
* [Die stetige Adressierung im Lauf](befunde/stetige-adressierung-im-lauf.md) - gebaut und gefahren: neutral wie vorhergesagt (grob 10,8 -> 8,5 %, p = 0,58); der Bau ist damit verifiziert, die These nicht geprueft
* [Die latente Augmentierung, gebaut](mechanismen/latente-augmentierung-gebaut.md) - `ACT23_AUGMENT`, Regeln aus der Messung; Rauchtest: 4,4 Pufferzeilen je Episode statt einer. **Braucht zwingend `ACT23_NEIGHBOURS=1`**
* [Die Augmentierung wirkt wie eine Zeilenwiederholung](befunde/augmentierung-wirkt-wie-wiederholung.md) - **ehrliches Negativ:** der Beitrag der Vorstellung selbst ist +0,0006 AUC
* [Keine Hoehergewichtung bringt etwas](befunde/gewichtung-bringt-nichts.md) - fuenf Schemata, keines hilft; und die Gegenprobe widerlegt meine Deutung des Augmentierungs-Verlusts
* [Alte Pufferzeilen abwerten](befunde/alte-zeilen-abwerten.md) - **kauft Naehe, kostet Verallgemeinerung:** +0,0115 bei Luecke 1500, -0,0094 bei Luecke 4000. Ein Positionsgewicht muss gegen ZWEI Luecken geprueft werden
* [Kein Gewichtungsverlauf hilft bei beiden Luecken](befunde/sanfter-abfall.md) - Positionsgewichtung endgueltig erledigt; Nebenertrag: die vorhandene `fail_w`-Daempfung ist **+0,0108 AUC wert** und war nie beziffert
* [fail_w kalibriert](befunde/fail-w-kalibriert.md) - alle 946 gedaempften Zeilen sind Fehlschlaege; weniger ist nah besser, fern egal, und der beste Wert 0,0 **darf nicht eingestellt werden** (schaltet die Route gegen eine Weltmodell-Blockade ab)
* [Die Vergabe-Engstelle, diagnostiziert](befunde/vergabe-engstelle-diagnose.md) - **genau EIN Knopf je Lauf**, und das Eigenschafts-Kommando umgeht ihn nicht: die Auto-Schleife erweitert `state.OBJECTS` nie. obj_X wird in 300 Episoden nie adressiert
* [Die freie Vergabe oeffnet die erste Tuer](befunde/freie-vergabe-erste-tuer.md) - `ACT23_FREIE_VERGABE`: 2 Knoepfe statt 1, aber das Repertoire wird nicht breiter. **Dahinter stehen zwei weitere Tueren**, und die Reihenfolge ist jetzt klar
* [Der Erzeuger reicht die Probe-Rolle weiter](befunde/erzeuger-repariert.md) - **`ACT23_NOVEL_WEITER`: der Agent eignet sich zum ersten Mal einen Koerper an, den er strukturell nie erreichen konnte** (obj_X, 17-mal adressiert); 3 Knoepfe gegen 1
* [Die Aneignungskette traegt 29 Episoden](befunde/kette-haelt-30-episoden.md) - **400 Episoden: alle drei Knoepfe fallen bis Ep 29, danach 371 Episoden nichts.** Der Engpass ist nicht mehr die Maschinerie, sondern die Welt
* [Die Daempfungsfunktion](befunde/daempfungsfunktion.md) - **sie haengt nicht am Betrag, sondern am Nachbarabstand** und ist die Verschmelzungsschwelle: `delta < Nachbarabstand - 40 mm`; die DREHUNG traegt nur `yaw4` und **mit umgekehrtem Vorzeichen**

# Chronik der Entwicklung

* [act23-Entwicklungslinie](chronik/act23.md) - Juni bis September 2026, verdichtet: Etappen, Anlaesse, Messungen
