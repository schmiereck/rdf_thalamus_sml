---
type: Frage
title: Dream-RSI fuer ACT23 - Forschungs- und Entwicklungsplan
description: Schrittweiser Plan fuer replaygestuetzte Trainingssteuerung, mit Evaluation und optionalen Forschungszweigen fuer direkte Servosteuerung und eine lernend erweiterte Fovea.
tags: [act23, dream-rsi, forschungsplan, selbstlernen, curriculum]
status: draft
evidenz: vermutung
ebene: code
generated: { by: codex, at: 2026-09-17T16:44:47Z }
sources:
  - id: paper
    resource: https://arxiv.org/html/2609.14858v1
    title: Dream-RSI - Recursive Self-Improvement through Evolving Worlds, Abschnitte 2 und 3
  - id: auftrag
    resource: "Nutzerauftrag im Gespraech vom 2026-09-17: Forschungsplan; ACT23-Aenderungen offen; Servosteuerung und Fovea als optionale Wuensche"
    title: Forschungsauftrag von Thomas
  - id: ziel
    resource: /ziel.md
    title: Selbstlernen ist das Projektziel
  - id: code
    resource: src/pc_cvnn/pc_act23.py
    title: Gepruefter Codex-Stand b3a38bf, insbesondere save_state und run_one
---

# Ziel und Arbeitsstand

Wir wollen messen, ob ein Agent aus seiner Versuchsgeschichte lernen kann, **welche Erfahrung
er als Naechstes sammeln sollte**. Erfolg bedeutet bessere Aneignung und Uebertragung auf neue
Objekte, Situationen und Aufgaben bei nachvollziehbarem Aufwand. Lieferquote allein reicht
nicht. Die [Projektziele](/ziel.md) gelten auch fuer die beiden optionalen Zweige.

Dies ist ein Plan, keine implementierte Funktion und kein Nachweis einer Wirkung auf ACT23.
Der Plan ist dokumentiert; D0 wurde am 2026-09-17 gestartet. Zeit- und
Erfolgsschwellen sind vorgeschlagene Forschungsentscheidungen, keine gemessenen Eigenschaften.
Fuer D0 ist main `15c063e` im eigenen Commit `b351207` integriert. Spaetere parallele
Arbeit bleibt ausserhalb dieser fixierten Messbasis.

**Lesereihenfolge:** diese Seite -> [Evaluationsvertrag](/messungen/dream-rsi-evaluation.md)
-> bei Bedarf [Motorpfad](/fragen/dream-rsi-servosteuerung.md) oder
[Fovea](/fragen/dream-rsi-fovea.md). Der Arbeitsstand wird ausschliesslich in der Tabelle dieser
Seite gefuehrt; Messungen erhalten eigene Befundseiten mit Rohbelegen.

# Was wir aus dem Paper uebernehmen

Dream-RSI protokolliert Suchlaeufe als Baeume. Eine Steuerstrategie waehlt Startpunkte,
Fortsetzungen, Parallelitaet und Abbruch. Offline werden ihr die bereits aufgezeichneten
Ergebnisse schrittweise gezeigt. Ein Entwicklungsagent verbessert den Strategiecode anhand
dieser Rueckmeldungen; die ausgewaehlte Fassung steuert anschliessend neue Laeufe. Der innere
Agent und die Bewertung bleiben dabei fest. Replay erzeugt keine unbekannten Fortsetzungen.
Die Experimente betreffen Programm- und mathematische Optimierung; eine Uebertragung auf
Robotertraining ist unsere Hypothese. [Quelle: Methode und Experimente](https://arxiv.org/html/2609.14858v1).

**Praezisierung der ersten Gespraechsanalyse:** Ein Protokoll erlaubt nicht automatisch,
beliebige neue Curricula offline zu bewerten. Nach Training auf A besitzt das Netz andere
Gewichte und Puffer als nach B. Das Ergebnis von B aus dem alten Zustand ist kein Ergebnis von
B nach A. Auch ein gespeichertes ACT23-Lerner-Pickle ist noch kein vollstaendiger Simulator-
und Prozesszustand. Die [Invarianten](/mechanismen/invarianten.md) dokumentieren bereits
Unterschiede zwischen laufendem Prozess und Neustart.

Die erste Umsetzung verteilt deshalb Budget auf **unabhaengige Trainingslinien**. Jeder Ast
hat seine eigene Zustandsfolge und ein festes Trainingsrezept. Replay darf seine gemessenen
Fortsetzungen aufdecken und frueher stoppen. Ein anderes Rezept am selben Checkpoint erfordert
eine eigene, wirklich gefahrene Kante. Keine Vermischung von Gewichten verschiedener Aeste.
Ein adaptives Curriculum innerhalb eines einzelnen lernenden Arms folgt erst in D6.

# Forschungsfragen und Grenzen

| ID | Hypothese | Was sie widerlegen oder begrenzen wuerde |
|---|---|---|
| H1 | Replay hilft, Trainingsbudget besser auf Linien zu verteilen als eine feste Verteilung. | Vorteil verschwindet auf neuen Startzustaenden oder nach Einrechnung aller Entwicklungskosten. |
| H2 | Beobachteter Lernfortschritt und Verallgemeinerung erlauben bessere Entscheidungen als Neuheit allein. | Eine einfache Neuheits- oder Fortschrittsstrategie ist gleich gut; dann keine komplexere Steuerung. |
| H3 | Die Auswahl lernt ueber mehrere Runden weiter. | Nur einmaliger Suchgewinn, keine Verbesserung gegen eine danach eingefrorene Strategie. |
| HS | Ein gelernter Motorpfad kann einen Teil der kartesischen Ausfuehrung ersetzen und sich aus eigener Erfahrung anpassen. | Nur Imitation ohne eigene Anpassung, instabiler geschlossener Kreis oder kein Nutzen im vereinbarten Aufwandsrahmen. |
| HF | Fovea-Netzzustaende tragen zusaetzliche Wahrnehmungsaufgaben; echte Detailabtastung kann deren Engpaesse verringern. | Nur Rohpixel tragen das Signal oder mehr Detail verbessert die vereinbarte Aufgabe nicht. |

Die geschlossenen Wege in [offene Faeden](/fragen/offene-faeden-act23.md) bleiben geschlossen.
Insbesondere rechtfertigt Dream-RSI weder laengere unveraenderte Laeufe noch ein neues
Wrist-Argmax nahe dem Teacher-Deckel. Der
[Greif-Lerndeckel](/befunde/greif-lerndeckel.md) motiviert Aufgaben mit nachweisbarem Lernsignal.
Der [Latent-Attraktor](/befunde/latent-etappen.md) wird durch historisches Replay nicht repariert.

# Geplante Bausteine und Eingriffe

Alle Namen in dieser Tabelle sind **Entwurfsnamen**, noch keine vorhandenen APIs.

| Baustein | Auftrag und Anschluss an ACT23 |
|---|---|
| `TrainingSnapshot` | Versionierter Lernerzustand samt Simulator, Zufallsstroemen und noetigem Prozesskontext; an definierten Episodengrenzen. Ergaenzt `save_state`. |
| `EpisodeTrace` / `DiscoveryStore` | Unveraenderliche Manifeste, Eltern-Kind-Beziehung, Beobachtungen, Entscheidungen, Artefakt-Hashes und Kosten. Vorhandene Logs bleiben Rohbelege. |
| `TrainingRunner` | Startet einen begrenzten Block aus einer Kopie; gibt Checkpoint, Messvektor und Kosten zurueck. Gemeinsamer Anschluss fuer beide ACT23-Auto-Schleifen. |
| `ReplayWorld` | Zeigt nur bereits entdeckte Knoten; fuehrt dieselbe Strategie-Schnittstelle wie der Runner. Unbekannte Fortsetzung wird als fehlende Abdeckung gemeldet. |
| `ExplorationPolicy` | Waehlt zulaessige Fortsetzungen und Abbruch aus sichtbarer Geschichte. Zunaechst kleine Vergleichsstrategien, danach datenbasiert verbesserte Fassung. |
| `PolicyDeveloper` | Erzeugt begrenzt viele Strategiekandidaten zwischen Runden. Erst Parameter-/Programmsuche; spaeter optional ein Coding-Agent. Bewertungslogik und Testdaten sind schreibgeschuetzt. |
| `Evaluator` | Misst Lernen, Erhalt, Aufwand und Abhaengigkeit von Hilfen. Getrennter Messkanal fuer Simulator-Grundwahrheit; `SelfEval` bleibt als Agentensignal sichtbar. |

ACT23 darf dafuer umgebaut werden. Naheliegende Ansatzpunkte sind `run_one`, `save_state`,
die beiden Auto-Schleifen, `DistanceNovelty`, `SelfEval` und die Modul-Ports. Zuerst werden
Beobachtung und Trainingsauswahl entkoppelt; spaeter koennen Motorik und Wahrnehmung ersetzt
werden. Pro Wirksamkeitsvergleich bleibt der innere Lerner samt Sensorik und Evaluator fest.
Eine Aenderung erzeugt eine neue Versuchsserie, damit Scheduler- und Architekturwirkung
unterscheidbar bleiben.

# Arbeitspakete und Entscheidungstore

Jeder Status ist einer von `offen`, `in Arbeit`, `pruefbereit`, `angenommen`, `verworfen`,
`zurueckgestellt`. Ein Paket ist erst angenommen, wenn sein Tor mit einem Befundlink belegt
ist. Ein Nullresultat kann ein abgeschlossenes, verworfenes Paket ergeben.

| Paket | Inhalt | Voraussetzung | Status | Befund / Entscheidung |
|---|---|---|---|---|
| D0 | Gemeinsame Basis, messbare Lernaufgabe, vorab fixierter Versuch | keine | verworfen | Beide getrennten 120-Episoden-Linien verfehlen den Wrist-Pilotvertrag; Seed 29 bestätigt auf Seed 103 zwar Lieferung, aber nicht die erforderliche Ausrichtung. Neuer Kandidat nur mit neuem, vorab fixiertem Vertrag |
| D0b | Selbstbeobachteter visueller Greifzustand | D0 geschlossen; F0-Portaudit | zurückgestellt | [Hubantwort](/befunde/d0b-hubantwort.md): feste Rohantwort scheitert auf neuer Seed-103-Familie an Precision 0,786 statt 0,80. Kein Tuning und kein Greifzustandskopf |
| D1 | Beobachtung, Checkpoints, Neustart- und Nichtbeeinflussungsnachweis | D0 | offen | - |
| D2 | Kleine Bibliothek echter Trainingslinien | D1 | offen | - |
| D3 | Replay mit Abdeckungs- und Informationspruefung | D2 | offen | - |
| D4 | Offline-Verbesserung der Trainingssteuerung | D3 | offen | - |
| D5 | Neue ACT23-Laeufe und rekursive Verbesserung | D4 | offen | - |
| D6 | Curriculum fuer einen einzelnen lernenden Arm | D5 | offen | - |
| D7 | Verteilung auf getrennte Rechner | D1; Integration nach D5 | offen | - |
| S0 | Semantik und Messaufgabe fuer direkte Servosteuerung | D0 | in Arbeit | [S0-Servogrundaudit](/befunde/s0-servo-grundaudit.md): Aktuatorvertrag für fünf direkte, druckfreie Gelenkkanäle geprüft; Lernaufgabe und Kontrolle noch offen |
| S1 | Motorisches Lernsignal und autonomer kurzer Regelkreis | S0, D1 | in Arbeit | [Unabhängige Rollouts bestanden](/befunde/s1-unabhaengige-rollouts.md): Faktor 0,09224 gegen Persistenz, 5/5 Gelenke. [Positions-Latent-Port](/mechanismen/servo-latent-port.md) bereit; [erster visueller Verbraucher B1](/befunde/s1-visuelles-koerpermodell.md) verfehlt neue Posen (1,28× Mittelbild). [Abdeckung auditiert](/befunde/s1-koerpermodell-abdeckung.md): beide Klauen 145/224 außerhalb der Kamera. Vor B2 ACT23-Arbeitsposen bei bestehender Kamera prüfen (Korrektur 04.10.); geschlossener Regelkreis offen |
| S2 | Eigene Anpassung und ACT23-Integration | S1 | offen | - |
| S3 | Optional: Geschwindigkeit oder Drehmoment statt Winkelvorgabe | S2, eigener Befund zum Bedarf | offen | - |
| F0 | Vorhandene Netzzustaende fuer neue Wahrnehmungsaufgaben pruefen | keine | zurückgestellt | D0b-F1a/F1b und feste Hubantwort verworfen; ein neuer F0-Zweig braucht eine eigenständige Repräsentationshypothese und Vertrag |
| F1 | Zusaetzlichen gelernten Wahrnehmungskopf verdrahten | F0, D1 | offen | - |
| F2 | Detailstufe und Bestandserhalt | F1 | offen | - |
| F3 | Mehrere Aufgaben und Integration mit Motorik | F1/F2; S2 fuer Motorvergleich | offen | - |

## D0 - Vor dem ersten Umbau das Experiment festlegen

- [x] Code-Commit, Welt/Geometrie, Startzustand, Modell- und Sensorkonfiguration inventarisieren;
  mit der laufenden Zieladressen-Arbeit abgleichen. Die bislang unversionierten Dateien erst
  erfassen und referenzieren; den Live-Zustand nicht veraendern.
- [x] Pilotaufgabe waehlen: Aneignung neuer Koerper und Farb/Form-Kombinationen auf dem Tisch,
  getrennt nach Erkennen, Adressieren und Ausfuehren. Eine sofortige direkte Adresse zaehlt
  alleine nicht als Lernen. Zieladressen als Zusatzaufgabe erst nach ihrer Integration.
  Ausgewaehlt ist die [objektrelative Wrist-Lernaufgabe](/messungen/dream-rsi-d0-wrist-lernaufgabe.md);
  ihr ausfuehrbarer Vertrag bleibt vor einem Lauf zu pruefen.
- [x] Auf einer kleinen unabhaengigen Pilotmenge eingefrorenen Lerner gegen lernenden
  vergleichen. Bei Deckeneffekt, unerreichbarer Aufgabe oder ungueltigem Urteil die Aufgabe
  korrigieren, bevor ein Scheduler entsteht.
- [x] [Evaluationsvertrag](/messungen/dream-rsi-evaluation.md) fuer D0 konkret ausfuellen:
  Teilmengen, Budget, Kontrollarme, Metrik, kleinster relevanter Effekt und Statistik stehen in
  [D0-Wrist-Lernaufgabe](/messungen/dream-rsi-d0-wrist-lernaufgabe.md), Abschnitt
  "Fixierter D0-Pilotvertrag v1".

Stand 2026-09-18: Komponentenvertrag und zwei Formpilotvarianten ausgewertet; beide als
Scheduler-Aufgabe ungeeignet. Als naechster Kandidat ist die Wrist-Lernaufgabe ausgewaehlt,
weil sie bereits einen eigenen Lernbefund hat. Der Codeaudit belegt objektrelatives Gitter und
kausale Negativkredite, verlangt aber einen eigenen nichtmutierenden Evaluator und den Ausschluss
privilegierter Welt-Labels. Der Komponentenhash und das opt-in Kreditprotokoll sind gebaut; der
eingefrorene L-Preflight besteht und der D0-Pilotvertrag v1 ist vor dem ersten Lernlauf
festgelegt.

**Tor D0:** ein gemessener, zugaenglicher Lernspielraum und ein fixiertes Protokoll. Stapeln
ist wegen [Hoehenabbildung und Erfolgsurteil](/befunde/stapeln-bricht-die-tischebene.md) noch
kein geeigneter erster Benchmark. Ein dortiger Fehlschlag wuerde H1 nicht testen.

## D1 - Zustaende und Erfahrung reproduzierbar machen

- [ ] Pro Episode mindestens vorherigen Checkpoint, ausgeloeste Aufgabe, wahrgenommene Merkmale,
  SelfEval, Fehlertyp, Updates je Modul, Kosten und neuen Checkpoint speichern; Grundwahrheit
  in einen getrennten Messkanal legen.
- [ ] Vollstaendigkeit anhand des Zustandsvertrags in der Evaluationsseite pruefen.
  Insbesondere Fovea nur bedingt persistiert, lokale Zufallsgeneratoren, fluechtige Adressen,
  Simulator- und Trackerzustand untersuchen. Alte Pickles als Imports mit begrenzter Evidenz.
- [ ] Instrumentierung aus/an bei gleicher Konfiguration vergleichen; der Logger nutzt
  keinen Zufallsstrom der Aufgabe. Fortsetzung im selben Prozess gegen Speichern/Neustart
  vergleichen. Beide Auto-Schleifen und das echte GUI-Panel beruecksichtigen.

**Tor D1:** gleiche Aufgabe ergibt auf derselben Plattform dieselben Entscheidungen und
Lernergebnisse; nur Wandzeit/IDs duerfen abweichen. Falls exakte Fortsetzung nicht erreichbar
ist, duerfen alle Arme alternativ einen explizit identischen Neustart an jeder Blockgrenze
verwenden. Das ist ein eigenes Trainingsprotokoll und kein Beleg fuer nahtlosen Lifelong-Betrieb.

## D2 - Eine kleine, brauchbare Erfahrungssammlung

- [ ] Als Pilot zwei unabhängige Start-Seeds, je drei feste Trainingsrezepte und je drei
  Fortsetzungsbloecke zu zunaechst zehn Episoden planen: maximal 180 Trainingsepisoden plus
  separat budgetierte Evaluation. Dies ist ein Funktionspilot, kein Wirksamkeitsnachweis.
- [ ] Rezepte decken die in D0 festgelegten Varianten ab, etwa breites Training, neue Formen
  und neue Kombinationen. Alle wachsen aus gleichwertigen Startkopien; Weitertraining erhaelt
  nur den Zustand seines eigenen Elternknotens.
- [ ] Auch erfolglose, stagnierende und technisch abgebrochene Aeste protokollieren. Auswahl
  der Bibliothek nicht nur auf bereits erfolgreiche Laeufe beschraenken.

**Tor D2:** Der Runner kann jeden Ast korrekt fortsetzen. Mehrere Aeste zeigen unterscheidbaren
Fortschritt pro Aufwand; wenn alle gleich oder flach sind, wird das protokolliert und D4
zurueckgestellt. Die [Wiedervorlage](/mechanismen/wiedervorlage.md) hilft bei Sensoranalysen,
ersetzt aber wegen unvollstaendiger Posen/Zustaende keinen solchen Trainingsbaum.

## D3 - Replay als begrenzte, ehrliche Vorauswahl

- [ ] `continue(frontier)`, `start(recipe)` und `stop` fuer Online/Offline gleich definieren;
  groessere Aktionsraeume erst nach eigener Datenerhebung.
- [ ] Elternfolge, Kosten, Sichtbarkeit und Abdeckung pruefen. Endknoten ohne aufgezeichnete
  Fortsetzung sind kein Nachweis fuer Stagnation. Replay darf aus fehlenden Daten keinen
  Misserfolg und keinen erfundenen Gewinn machen.
- [ ] Strategien auf ganzen zurueckgehaltenen Baeumen vergleichen. Ein Skript, das spaetere
  Scores oder IDs erfolgreicher Aeste liest, muss bei der Informationspruefung durchfallen.

**Tor D3:** gleiche aufgedeckte Folge ergibt die protokollierten Kosten/Scores; keine verborgenen
Informationen gelangen zur Entscheidung. Abdeckung und unentscheidbare Anfragen werden
mitberichtet. Reicht die Abdeckung fuer einen Vergleich nicht, folgt Datenerhebung statt Ranking.

## D4 - Die Trainingssteuerung selbst verbessern

- [ ] Referenzen: feste gleichmaessige Budgetverteilung, einfache Neuheitsstrategie,
  einfache gemessene Fortschrittsstrategie; letztere erhalten dieselben Informationen.
- [ ] Zunaechst maximal 20 Strategiekandidaten im Entwicklungsanteil. Aktuelle Strategie
  immer mitbewerten; Validierung und Aufwand entscheiden ueber die Vorauswahl.
- [ ] Der Zwei-Seed-Pilot aus D2 genuegt nur zum Funktionstest. Fuer eine belastbare
  Vorauswahl weitere unabhaengige Baeume und ganze Validierungswelten mit eigenem Budget
  erheben; bei knapper Abdeckung Kandidatenzahl begrenzen statt mehrfach auf denselben
  wenigen Baeumen optimieren.
- [ ] Danach optional Code-Revision durch einen Entwicklungsagenten in separatem Prozess,
  mit festem Aufruf-/Zeitbudget und Zugriff nur auf Entwicklungsdaten. Keine Aenderungen am
  Evaluator oder an Robotergewichten durch diesen Meta-Schritt.

**Tor D4:** Vorteil auf zurueckgehaltenen Replay-Welten gegen die staerkste einfache Referenz,
ohne niedrigere Abdeckung als Erklaerung. Das rechtfertigt nur D5. Wenn die einfache Strategie
gleich gut ist, wird sie behalten und die zusaetzliche Entwicklungskomplexitaet verworfen.

## D5 - Nutzen in neuen ACT23-Laeufen belegen

- [ ] Vorausgewaehlte Strategie auf neuen Startzustaenden und Szenen ausfuehren, mit identischem
  Gesamtbudget wie die Kontrollen. Die anfangs gemeinsam erhobene Bibliothek gleich anrechnen.
- [ ] Mindestens drei aeussere Runden vorsehen: neue Erfahrung sammeln, Strategie offline
  ueberarbeiten, wieder ausfuehren. Kontrollarm mit nach Runde 1 eingefrorener Strategie prueft
  den Zusatznutzen der Rekursion.
- [ ] Alle Arme erhalten gleich haeufig neue Erfahrung und Evaluation. Der Vorteil darf
  nicht aus mehr Kandidaten, mehr Rechenzeit oder einem veraenderten inneren Lerner stammen.

**Tor D5:** der vorab festgelegte ACT23-Effekt auf neuen Aufgaben bzw. die gleichwertige
Lernleistung bei geringerem Aufwand ist belegt; Bestandserhalt und Anteil fremder Hilfen
sind ausgewiesen. Nur dann als wirksame Trainingssteuerung integrieren. Ein Suchgewinn bei
ausbleibendem Rekursionsgewinn wird genau so benannt.

## D6 - Vom Portfolio zum Curriculum eines Arms

- [ ] Jetzt Aufgabenwahl aus aktuellem Lernzustand, Unsicherheit und bisherigem Fortschritt
  lernen. Rueckmeldungen muessen tatsaechlichen Kompetenzgewinn von dauerhaft hohem Fehler
  unterscheiden; unloesbare Szenen duerfen das Budget nicht dauerhaft binden.
- [ ] Fuer autonome Aufgabenwahl im Arm einen lernenden PC-CVNN-Kopf entwickeln oder die
  erfolgreiche Trainingssteuerung dorthin destillieren und erneut pruefen. D4/D5 steuern
  extern das Training; ein dort entwickeltes Scheduler-Programm allein erfuellt noch nicht
  die Forderung nach einer gelernten, regelarmen Aufgabenwahl zur Laufzeit.
- [ ] Neue Aufgabenreihenfolgen wirklich ausfuehren. Historisches Replay bleibt nur dort
  gueltig, wo exakt passender Elternzustand und Aktion aufgezeichnet sind.
- [ ] Falls Aeste spaeter Wissen austauschen: eigenes Destillations-/Wiederlernexperiment mit
  Herkunft und Kosten; niemals einfach Gewichte oder Erfolge zusammenaddieren.

**Tor D6:** Lernvorteil eines einzelnen Agenten auf unbekannten Aufgaben ohne regelbasierte
Aufgabenhilfe zur Testzeit. D5 allein belegt nur gute Auswahl von Trainingslinien.

## D7 - Mehrere Rechner

Von D1 an portable IDs/Hashes statt lokaler Absolutpfade in Manifesten. Code und kleine
Manifeste koennen ueber Git verteilt werden, grosse Checkpoints und Bilder ueber einen
separaten Artefaktspeicher. Einmaliger Import wird per Hash verifiziert. Das vorhandene
Koordinations-Repository traegt Status und Uebergaben.

Ein zentraler Dispatcher besitzt anfangs die Jobvergabe; Workers schreiben nur eigene
unveraenderliche Ergebnisse. Job-ID plus Versuch-ID, Lease/Heartbeat und atomare Fertigmeldung
verhindern, dass Abbrueche zu doppeltem Weitertraining fuehren. Git-Pull ist keine Sperre.
Hardware, Bibliotheken und Laufzeiten je Worker protokollieren; gleiche Seeds garantieren
rechneruebergreifend keine Bitgleichheit. Bei Vergleichslaeufen Hardware ausbalancieren.

**Tor D7:** derselbe kleine Job laeuft auf zwei Rechnern mit geprueften Artefakten und
vorab definierter numerischer Toleranz; abgebrochene Jobs lassen sich wiederaufnehmen, ohne
Ergebnisse doppelt zu zaehlen. Trainingszeit und Rechenverbrauch werden getrennt ausgewiesen.

# Reihenfolge und Pflege

**Naechster konkreter Schritt ist D0.** Danach D1-D5 als Kern. S0 und F0 koennen unabhaengig
inhaltlich vorbereitet werden; ihre Umsetzung bekommt eigene Laeufe und Zustandskopien.
S2 und F1/F2 werden zuerst einzeln gegen dieselbe Basis bewertet; eine Kombination kommt
spaeter als eigenes Experiment. Kein gleichzeitiger Austausch aller Bausteine.

Nach jedem Paket: Status und Befundlink in dieser Tabelle, neue bzw. fortgeschriebene
Befundseite, Eintrag in `index.md` und `log.md`, eigene Statusdatei im Koordinations-Board.
Bei einem Negativbefund bleibt der Weg mit Begruendung dokumentiert. Eine Wiederaufnahme
braucht neue Daten, ein neues Signal oder eine geaenderte Forschungsfrage.
