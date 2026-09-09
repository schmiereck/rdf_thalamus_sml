# Chronik

Neueste zuerst. Datumsueberschriften in ISO-Form `YYYY-MM-DD`. Ein Eintrag je Vorgang, das
fuehrende fette Wort ist Konvention: **Anlage**, **Ergaenzung**, **Widerlegung**, **Ruecknahme**.

Fuer eine schnelle Uebersicht: `grep "^## " wiki/log.md | head -5`

## 2026-09-09

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
