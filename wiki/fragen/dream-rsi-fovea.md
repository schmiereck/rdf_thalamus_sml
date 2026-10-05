---
type: Frage
title: Fovea fuer weitere Aufgaben und schrittweise mehr Detail
description: "Optionaler Forschungszweig F0-F3: Netzzustaende als Wahrnehmung nutzen, Detailbedarf messen und den bestehenden Lernstand beim Ausbau erhalten."
tags: [act23, dream-rsi, fovea, wahrnehmung, migration]
status: draft
evidenz: vermutung
ebene: code
generated: { by: codex, at: 2026-09-17T16:44:47Z }
sources:
  - id: auftrag
    resource: "Nutzerwunsch 2026-09-17: Fovea-Aufloesung schrittweise erhoehen und Sensoren fuer weitere Wahrnehmungsaufgaben verwenden"
    title: Optionaler Forschungswunsch
  - id: fovea
    resource: /mechanismen/fovea-und-blick.md
    title: Bisherige Fovea-Messungen und Grenzen
  - id: code
    resource: src/pc_cvnn/pc_act18.py
    title: F/K/Zoom, HexFovea, globales F und Kommentar zum Aufloesungsversuch vom August
  - id: persistenz
    resource: src/pc_cvnn/pc_act23.py
    title: RES, from_sim und bedingte Fovea-Persistenz in save_state
  - id: hoehe
    resource: /befunde/stapeln-bricht-die-tischebene.md
    title: Hoehenfehler der Tischebenen-Homographie
---

# Forschungsfrage

Kann das vorhandene Fovea-Netz weitere Aufgaben lernen, und hilft eine feinere zentrale
Abtastung bei einem zuvor gemessenen Informationsengpass? Dieser Zweig ist Teil des
[Gesamtplans](/fragen/dream-rsi-forschungsplan.md); der Status von F0-F3 steht dort.

Die erste Frage gilt **bei heutiger Aufloesung**. Sie trennt fehlende Aufgabenanbindung von
fehlenden Bilddetails. Danach folgt ein Ausbau, der den alten Lernstand kontrolliert erhaelt.

# Ausgangslage und Gegenbefunde

Die [Fovea-Seite](/mechanismen/fovea-und-blick.md) dokumentiert: zusaetzliche Zellen F24/F32
brachten gegen F16 keinen Winkelgewinn, weil sie dort nur Peripherie hinzufuegten. Die
Winkelablesung sitzt bislang auf abgetasteten Bildwerten, nicht auf eingeschwungenen
PC-Netzzustaenden. Der geschlossene Blickkreis beim langen Objekt hatte unter Verdeckung
einen negativen Lieferbefund. Ein groesseres Netz allein beantwortet diese Probleme nicht.

Zusaetzlich beschreibt der **Codekommentar** bei `pc_act18.py`, `F` (Stand b3a38bf), einen
F20/RES480-Versuch mit 91 GUI-Episoden: etwa 1,9-fache Episodenzeit und kein erkennbarer
Lokalisierungsgewinn. Der Kommentar nennt die frisch trainierte Fovea als Konfounder und eine
damals fehlende Anbindung ans Weltmodell. Das ist hier ein historischer Hinweis aus dem Code,
**kein neu nachgeprueftes kontrolliertes A/B**. Rohlogs und damalige Konfiguration sind in F0
nachzuschlagen, bevor daraus eine allgemeine Schranke abgeleitet wird.

Die heutige Basis verwendet Vorgaben `ACT_FOVEA_F=16`, `ACT_FOVEA_K=4` und `ACT23_RES=240`
sowie Zoom und abgestufte Zellabstaende. F bestimmt die Blattgroesse, K/Zoom die Abtastung.
Groesseres F allein bedeutet nicht automatisch mehr Zellen auf dem Objekt. Eine andere
Bildaufloesung beruehrt Kalibrierung und alle Pixel-/Weltumrechnungen.

# F0 - Aufgaben und Informationsbedarf messen

Moegliche Aufgaben, in dieser Reihenfolge zu pruefen:

| Aufgabe | Agenteneingaben / Lernsignal | Gehaltene Pruefung |
|---|---|---|
| Objektidentitaet und Wiederfinden | Zeitlich aufeinanderfolgende Blicke, Farb-/Formeinbettung, Gueltigkeit | Neue Farb/Form-Kombinationen, Ablenker, verdecktes langes Objekt; Fehlbindung und Wiederfindezeit. |
| Objekt im Greifer / getragen / losgelassen | Bildfolge plus eigene Gelenkbewegung; konsistente gemeinsame Bewegung als moegliches Selbstsignal | Neue Posen/Formen, verdeckt/leer; Precision/Recall und Kalibrierung gegen getrennte Sim-Grundwahrheit. |
| Relative Lage und Hoehe | Mehrere Blicke, eigene Bewegung und zeitliche Beobachtung | Neue Objektgroessen/Hoehen; Positions-/Hoehenfehler und Relationsentscheidung. |
| Ausrichtung / Greifgeometrie | Fovea-Netzzustaende plus Aufgabenkontext | Winkel-/Geometriefehler auf unbekannten Formen, unabhaengig von ihrer Farbe. |

Die ersten beiden Aufgaben passen zu bekannten Bindungs- und Schliessproblemen. Hoehe folgt
spaeter: ein einzelnes groesseres Bild kann scheinbare Groesse und physische Groesse nicht
allgemein auseinanderhalten. Erst Beobachtbarkeit durch Bewegung, Mehrblick oder einen
anderen lernenden Sensor pruefen. Mehr Aufloesung repariert keine falsche Homographie.

- [ ] Bestehende Zellzustaende und Hidden-Zustaende auslesen, zeitlich sauber aus echten
  Laufszenen speichern; Szenen/Trajektorien als Gruppen teilen.
- [ ] Kleinen gelernten Auslesekopf auf eingefrorenen Netzzustaenden trainieren. Kontrollen:
  Rohzellwerte, gleich grosses untrainiertes Netz und einfache Konstantvorhersage.
- [ ] Zunaechst genau eine Aufgabe priorisieren. Sim-Grundwahrheit ist als Messetikett erlaubt;
  ein damit trainierter Diagnosekopf wird als ueberwacht markiert. Selbstlernen erfordert
  danach einen eigenen beobachtbaren Lernkanal.
- [ ] F20/RES480-Versuch rekonstruieren; heutige Ports zur Weltmodell-/Handlungsseite pruefen.

**Tor F0:** Netzzustaende tragen das benoetigte Signal auf gehaltenen Szenen und die Aufgabe
hat einen messbaren Engpass. Tragen nur Rohpixel das Signal, lautet der Befund genau so;
zunaechst Repraesentationslernen verbessern, keinen PC-Wahrnehmungserfolg behaupten.

# F1 - Eine neue Wahrnehmungsfunktion lernen und nutzen

- [ ] Gelernten Kopf ueber `VisualCortexModule`-Ports anbinden: Merkmalsvektor, Gueltigkeit,
  Konfidenz, Zeitstempel und Einheiten. Instanz- und Beobachtungsidentitaet mitfuehren.
- [ ] Zunaechst parallel vorhersagen, ohne Handlungen zu steuern. Auf gespeicherten echten
  Szenen Nutzen und Schaden zusammen messen; seltene Phantom-/Fehlbindungsfaelle nicht
  durch einen Median verdecken.
- [ ] Selbstsignale wie zeitliche Konsistenz nur mit Gueltigkeit verwenden. Verdeckungs- und
  Fehlbindungsfehler duerfen nicht in dauerhafte Trainingsetiketten umgedeutet werden.
- [ ] Erst danach genau einen Verbraucher einschalten, etwa Objektgedaechtnis oder
  Griffzustandsvorhersage. Alte Puffer haben neue Merkmale nicht: fehlende Werte markieren,
  frische gueltige Daten getrennt bewerten; keine erfundenen Merkmale in Altzeilen.

**Tor F1:** gehaltene Wahrnehmung verbessert sich und die Funktion wirkt im vollen ACT23-Lauf
auf ihren eigenen Zielkanal, ohne inakzeptablen Schaden. Lieferquote als Regression mitmessen;
eine verbesserte Diagnose ersetzt keinen Nachweis gelernter Schliessentscheidungen.

# F2 - Echte Detailstufe mit erhaltenem Altpfad

**Bevorzugter Entwurf:** alte Fovea mit ihrem Checkpoint zunaechst einfrieren; einen lernenden
Detailzweig fuer denselben Blickbereich ergaenzen. Der alte Ausgang bleibt waehrend seiner
Vorbereitung unveraendert. Neue Funktionen erhalten einen zunaechst abgeschalteten, separat
trainierbaren Zugang. Spaeter kontrolliert koppeln und alte Aufgaben weiter mitpruefen.

1. **Messbare Aufloesung definieren:** Pixel pro physischem Detail und tatsaechliche
   Abtastpunkte auf dem Objekt messen. Vergleiche bei gleichem Sichtfeld/Kamerabild, damit
   Detail nicht mit mehr Kontext verwechselt wird. Hochskalieren alter Pixel erzeugt keine
   neue Information; fuer echte Details ggf. hoeher rendern und die Kalibrierung mitfuehren.
2. **Instanzen faehig machen:** `F` und mehrere Fovea-Funktionen sind derzeit modulglobal.
   Zwei verschieden grosse Netze koennen daher nicht einfach nebeneinander gesteckt werden.
   Geometrie/Kalibrierung instanzgebunden refaktorieren und den alten Pfad auf Gleichheit
   pruefen; vor diesem Umbau nur getrennte Prozesse fuer Vergleiche verwenden.
3. **Klein ausbauen:** vorgeschlagene Stufen 16 -> 20 -> 24 oder eine dichte zentrale
   Zusatzabtastung. Nicht jede Stufe muss genommen werden. Zellzahl, physisches Sichtfeld,
   Sampling-Abstand, Bildaufloesung und Trainingszeit als getrennte Variablen behandeln.
4. **Wissen uebertragen:** gemeinsame Beobachtungen fuer alten und neuen Zweig, alte
   Aufgaben als Erhaltssatz, optional Destillation der alten Ausgaben neben neuem Lernsignal.
   Alte komplexe Gewichte nicht pauschal interpolieren: Zellorte, Nachbarschaften und ggf.
   Positionsphasen muessen zusammenpassen. Neue Verbindungen duerfen nicht sofort die
   Inferenz der eingefrorenen alten Zellen veraendern.
5. **Migration pruefen:** eigener Checkpoint und erhoehtes Schema bei Strukturwechsel;
   Zellgeometrie/Ports/Phasen-/Kamerakalibrierung versionieren, Speichern-Neustart und Rueckkehr
   zur alten Datei testen. Keine automatische Ueberschreibung oder Voll-Neutrainierung des
   restlichen gewachsenen Agenten als versteckter Teil des Vergleichs.

Kontrollen: unveraenderte alte Fovea, alter Pfad mit gleichem zusaetzlichem Training,
Detailzweig ohne Wissensuebertragung und mit Wissensuebertragung. Datenmenge und Kosten
ausweisen; Pixelzahl und Netzgroesse nicht zugleich unkontrolliert aendern. Der groessere
Kandidat muss sowohl neue Aufgabe als auch alte Blick-/Lokalisierungsaufgaben bestehen.

**Tor F2:** Mehr Detail bringt auf der vorher festgelegten Aufgabe einen relevanten Gewinn,
der ueber laengeres Training hinausgeht; der Erhaltssatz besteht die Nichtunterlegenheitsgrenze
und Kosten bleiben im Rahmen. Wenn der eingefrorene Altpfad stabil ist, aber eine gemeinsame
Feinabstimmung vergisst, bleiben die Zweige getrennt. Schrittweises Wachstum garantiert
keinen Bestandserhalt; gemessen wird nach jeder Stufe.

# F3 - Mehrere Aufgaben, Motorik und Hoehe

Erst nach dem Einzelaufgabenvergleich gemeinsame oder getrennte Koepfe fuer Identitaet,
Greifzustand und relative Lage erproben. Gegen getrennt trainierte Koepfe vergleichen, damit
negative Wechselwirkungen sichtbar werden. Ein gelerntes Blick-/Detailbudget kann entscheiden,
wann zusaetzliche Wahrnehmung lohnt; fixe Regeln sind nur Versuchskontrollen.

Fovea und [direkter Motorpfad](/fragen/dream-rsi-servosteuerung.md) zuerst einzeln pruefen,
danach Basis / nur Motor / nur Fovea / beide. Fuer Stapeln braucht es ausser einer
Hoehenrepraesentation ein gelerntes Relations-/Erfolgsurteil, das einen getragenen Koerper von
einem abgestellten Stapel unterscheidet. Das bisherige Tisch-SelfEval genuegt nicht.

**Tor F3:** Transfer auf gehaltene Aufgaben ohne nachtraegliche Sonderregeln, einschliesslich
Bestandserhalt und ausgewiesenen Hilfen. Keine Hoehe beobachtbar oder kein Detailgewinn:
Aufloesungszweig zurueckstellen; ein nuetzlicher Wahrnehmungskopf aus F1 kann trotzdem bleiben.

# Anschluss an Dream-RSI

Die Trainingssteuerung kann Aufgaben-, Aufloesungs- und Lernbudgetvarianten als getrennte
Linien bewerten. Ein neuer Sensorraum erzeugt neue Zustands-/Merkmalsversionen; alte Logs
erhalten nicht rueckwirkend die unsichtbaren Details. Gespeicherte echte Bilder koennen
erneut abgetastet werden, innerhalb ihrer urspruenglichen Informationsgrenze.
