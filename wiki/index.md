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
* [Merkmale kommen zu spaet](befunde/merkmale-kommen-zu-spaet.md) - der Nachbar-Block steht auf 6 % der Pufferzeilen; der Engpass ist die Puffer-Zusammensetzung, nicht der Merkmalssatz
* [Der Tracker rastet auf dem Nachbarn ein](befunde/ablenker-bindung-gemessen.md) - direkt gemessen: fremder Belief 31,2 gegen 4,2 % (p = 0,0086), auf 4 mm genau am FALSCHEN Koerper
* [Der Keim erreicht den Tracker nie](befunde/keim-erreicht-tracker-nicht.md) - Schluesselfehler, 120 von 120; bei mehreren Kandidaten 41 % Fehlstart, davon 0 geliefert
* [Keim-Fix, A/B](befunde/keim-fix-ab.md) - Fehlstarts 51,5 -> 6,7 % (p = 0,0001, gepaart ueber zwei Seeds); **Vorgabe seit 2026-09-09**, die Quote bleibt unbelegt
* [Keim im Rueckfall](befunde/keim-im-rueckfall.md) - Luecke zu (10 -> 0), Nutzen nicht nachweisbar, **wieder abgeschaltet**; die Rueckfall-Faelle sind Verschmelzungen
* [Verschmelzung: die Abstandskurve](befunde/verschmelzung-abstandskurve.md) - Split traegt ab 35 mm, bei 25 mm nur 72 %; die Formklasse ueberlebt viel schlechter als die Position
* [Nachbarnaehe im Lauf](befunde/nachbarnaehe-im-lauf.md) - unter 55 mm faellt die Quote um 13,9 Punkte (p < 0,0001, 7/7 Objekte gleich); betrifft 15,6 % der Episoden
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
* [Latente Augmentierung](fragen/latente-augmentierung.md) - Nutzeridee, durchdacht und gestuetzt, aber nicht gebaut; die Voraussetzungsmessung steht davor

# Chronik der Entwicklung

* [act23-Entwicklungslinie](chronik/act23.md) - Juni bis September 2026, verdichtet: Etappen, Anlaesse, Messungen
