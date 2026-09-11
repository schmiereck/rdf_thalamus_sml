# Chronik

Neueste zuerst. Datumsueberschriften in ISO-Form `YYYY-MM-DD`. Ein Eintrag je Vorgang, das
fuehrende fette Wort ist Konvention: **Anlage**, **Ergaenzung**, **Widerlegung**, **Ruecknahme**.

Fuer eine schnelle Uebersicht: `grep "^## " wiki/log.md | head -5`

## 2026-09-11

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
