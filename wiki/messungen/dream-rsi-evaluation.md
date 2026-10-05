---
type: Messvorschrift
title: Evaluationsvertrag fuer Dream-RSI und seine ACT23-Forschungszweige
description: Entwurf fuer Datenaufteilung, vollstaendige Checkpoints, Budgetvergleich, Lernmetriken und Entscheidungstore; vor der Implementierung in D0 zu konkretisieren.
tags: [act23, dream-rsi, messen, generalisierung, reproduzierbarkeit]
status: draft
evidenz: vermutung
ebene: code
generated: { by: codex, at: 2026-09-17T16:44:47Z }
sources:
  - id: plan
    resource: /fragen/dream-rsi-forschungsplan.md
    title: Forschungsplan und Paketstatus
  - id: invarianten
    resource: /mechanismen/invarianten.md
    title: Zustands-, Mess- und Betriebsinvarianten
  - id: ab
    resource: /messungen/act23-headless-ab.md
    title: Bestehendes ACT23-A/B-Verfahren
  - id: reproduktion
    resource: /befunde/laeufe-sind-reproduzierbar.md
    title: Seeds statt identischer Wiederholung als Replikate
---

# Status und Geltung

Dieser Vertrag gehoert zum [Forschungsplan](/fragen/dream-rsi-forschungsplan.md). Er ist noch
keine ausfuehrbare Messung: Runner, Replay und Auswertung werden erst in D1-D4 gebaut. D0
ergaenzt genaue Kommandos, Zahlen und Artefaktpfade, **bevor** Bestaetigungsergebnisse bekannt
sind. Ergebnisse erhalten eigene Seiten; diese Seite definiert das Verfahren.

Die bestehende A/B-Seite bleibt Herkunft. Fuer diese Reihe gelten die praeziseren
[Invarianten](/mechanismen/invarianten.md): Der kopflose Steuerungslauf braucht `ACT23_VIZ=1`
und `ACT23_VIZ_HEADLESS=1`. `ACT23_VIZ=0` startet die Diagnose und ersetzt den Steuerungslauf
nicht. `ACT23_DEBUG` in allen Armen gleich setzen, weil es den Zufallsstrom verschieben kann.
Auswertung mit einem Python-Parser, der Episode und Ergebnis paart, nicht mit `Select-String`.
Vor echten Vergleichslaeufen den Repository-Skill `run-comparison-runs` lesen.

# Versuchsvertrag vor jedem Paket

In der jeweiligen Messseite vorab ausfuellen:

| Feld | Verpflichtender Inhalt |
|---|---|
| Frage | Ein H-/D-/S-/F-Bezug aus dem Plan; eine primaere Hypothese. |
| Basis | Code-Commit und ggf. Patch-Hash, Welt/XML-Hash, Konfiguration, Bibliotheks-/Hardwarestand. |
| Zustand | Start-Checkpoint-Hash und Schema, Herkunft, Trainingshistorie, erlaubte Schreibpfade. |
| Entscheidung | Was genau variiert; welche Signale der Agent sehen darf. |
| Kontrolle | Staerkste passende einfache Referenz; gleicher Trainings-/Auswertungszugriff. |
| Daten | Unabhaengige Seeds, Szenenfamilien, Aufgaben und Aufteilung in Entwicklung/Validierung/Test. |
| Aufwand | Episoden/Simulationsschritte, Updatebudget, Rechenzeit, Kosten der Meta-Entwicklung und Evaluation. |
| Erfolg | Primaere Metrik, minimal relevanter Effekt, Erhaltsschranke, Konfidenzverfahren, Mehrfachtestkorrektur. |
| Ende | Feste Stichprobe oder vorab definierter sequenzieller Test; technische Abbruchbedingungen. |
| Reproduktion | Exakter PowerShell-Aufruf, venv-Python, Parser-Version, Rohlogs und Ergebnisdateien. |

Ein Pilot darf Schwellen und Messgroessen kalibrieren. Danach werden sie versioniert fixiert
und auf neuen Daten geprueft. Nachtraeglich passend gewaehlte Metriken bleiben explorativ.

# Drei Arten von Daten strikt trennen

1. **Entwicklung:** Trainingsszenen und historische Baeume fuer Strategievorschlaege, Fits und
   Fehleranalyse. Der Entwickler darf die darin enthaltenen Ergebnisse auswerten.
2. **Validierung:** ganze bisher unbenutzte Laeufe/Baeume bzw. Aufgabenfamilien fuer
   Kandidatenauswahl und Checkpoint-Auswahl. Wiederholt benutzte Validierung ist kein Test.
3. **Abschlusstest:** neue Seeds und zurueckgehaltene Kombinationen, Groessen, Lagen oder
   Aufgabenfamilien. Weder Scheduler noch Entwicklungsagent erhalten Testresultate fuer die
   Auswahl. Nach Einsicht wird ein Test fuer die naechste Entwicklungsrunde nicht wieder als
   unberuehrt ausgegeben.

Keine zufaelligen Zeilen-Splits aus Lifelong-Puffern. Eltern und Nachkommen derselben
Trainingslinie bleiben in einer Teilmenge. Bei zeitlichem Split eine Luecke verwenden.
Bestehende Checkpoints haben moeglicherweise alle sieben bekannten Koerper gesehen: diese
duerfen nicht als unbekannte Testformen etikettiert werden. Unbekannte Kombinationen und
unbekannte Formen sind getrennte Generalisierungsfragen.

Bewertungen laufen auf verworfenen Checkpoint-Kopien mit eingefrorenen Updates **aller**
Module, einschliesslich Fovea, SelfEval-Statistik, Neuheitsspeicher und laufender Normalisierung.
`NO_PERSIST` verhindert nur Schreiben und ist kein Lern-Aus-Schalter. Fuer Adaptationstests
wird Lernen explizit eingeschaltet und separat budgetiert. Neue Evaluation darf die
Trainings-Zufallsstroeme nicht verbrauchen.

# Was Erfolg bedeutet

Primaer wird ein **einzelner** ausgewaehlter Checkpoint je Trainingsportfolio geprueft.
Seine Auswahl erfolgt auf Validierung, nicht per Test-Orakel. Die Summe der Erfolge vieler
Spezialisten ist kein breit gelerntes Repertoire eines Arms.

| Groesse | Messung und Zweck |
|---|---|
| Aneignung | Versuche bis zur vorab fixierten Kompetenzgrenze auf einer neuen Aufgabenfamilie; Nichterreichen als zensiert behandeln, nicht weglassen. |
| Lernfortschritt | Leistung vor/nach eigener Erfahrung sowie Flaeche der Lernkurve gegen Trainingsaufwand. Vergleich mit eingefrorenem Lerner. |
| Generalisierung | Gleich gewichtete Leistung je zurueckgehaltener Aufgabenfamilie; Identitaet, Adressierung und Ausfuehrung getrennt berichten. |
| Bestandserhalt | Veraenderung auf bekannten Aufgaben und alten Sensorbedingungen nach neuem Lernen. |
| Selbststaendigkeit | Anteil Teacher-Labels, Laufzeitregeln, privilegierter Rueckfaelle und uebernommener Aktionen. Test ohne Aufgabenhilfe gesondert ausweisen. |
| Zuverlaessigkeit | Fehlgriffe, falsche Objektbindung, Abstuerze, ungueltige Aktionen, falsches SelfEval-Urteil. |
| Aufwand | Physikschritte, Episoden, Fits, Netzgroesse, Speicher/IO, Wandzeit und aggregierte Worker-Zeit; optionale Agentenaufrufe extra. |

**Vorgeschlagener Erfolg fuer H1/D5:** mindestens +5 Prozentpunkte mittlere Leistung auf neuen
Aufgaben bei gleichem Trainingsbudget; alternativ mindestens 20 % weniger Aufwand bis zur
gleichen vorab festgelegten Kompetenz. Welche Variante primaer ist, wird in D0 entschieden.
Als erste Erhaltsschranke hoechstens 5 Prozentpunkte Verlust auf bekannten Aufgaben. Die
Zahlen sind aenderbare Entwurfswerte; Nichtunterlegenheit braucht eine Konfidenzaussage,
nicht bloss einen nichtsignifikanten Unterschied.

S- und F-Pakete legen eigene primaere Groessen fest: etwa Anpassung an unbekannte Lasten ohne
Teacher oder Erkennen von Objekt-im-Greifer unter Verdeckung. Ein architektonischer Gewinn
darf bei maessigerer Lieferquote angenommen werden, wenn Selbstlernen, Hilfenabbau und
akzeptierter Preis vorher so festgelegt sind. Es gibt keine Pflicht, den Teacher zu schlagen.

# Historisches Replay: Informations- und Zustandsvertrag

Ein Knoten beschreibt **einen gemessenen Zustand nach einer konkreten Trainingshistorie**.
Eine Kante enthaelt Eltern-Hash, festes Rezept, Trainings-/Evaluationsprotokoll, Kosten und
Kind-Hash. Physik-, Learner- und Aktionsschema muessen zusammenpassen. Architekturwechsel
erzeugen eine neue Serie; alte Ergebnisse duerfen nur mit expliziter Kompatibilitaet eingehen.

Vor einer Entscheidung sieht die Policy nur das bisher aufgedeckte Teilstueck: vergangene
Messungen/Kosten, zulaessige Aufgaben, ihre eigene Historie und das Budget. Keine zukuenftigen
Scores, tatsächlichen Astlaengen, versteckten Optimalwerte oder Dateinamen mit Ergebniscode.
Normierung ausschliesslich aus Entwicklungsdaten oder dem sichtbaren Praefix.

Fehlt eine passende Fortsetzung, meldet Replay **unbekannt**. Berichten: Anteil abgedeckter
Anfragen, erreichte Tiefe, Rezept-/Szenenverteilung, Kosten und bestaetigte Ergebnisse.
Strategien mit systematisch anderer Abdeckung nicht allein nach dem verbleibenden Score
ordnen. Neue Entscheidungen brauchen neue echte Laeufe. Historische Erfolgsraten sind keine
unverzerrte Vorhersage fuer beliebige neue Strategien.

Ein Checkpoint an einer Episodengrenze umfasst mindestens:

- alle lernenden Module, Gewichte, Puffer, Normalisierung, Lern-/Optimiererzaehler und Schema;
- Fovea-Netz, Selektion, Blick/Zoom, Objekt-/Tracker-Gedaechtnis, Selbsturteil und Neuheit;
- Zufallsstroeme von Python, NumPy und modullokalen Generatoren;
- MuJoCo-Zustand einschliesslich benoetigter Integrator-/Warmstartfelder, `qpos`, `qvel`,
  Aktuatorzustaenden, `ctrl`, Zeit, Mocap sowie veraenderter Modell-/Geometrieparameter;
- Objekte/Adressen/Farbzuordnung, Warteschlangen, laufende Statistiken und noetige Closure-
  bzw. Modulglobalen; oder nachgewiesen gleichwertige Rekonstruktion an der Blockgrenze.

Der genaue Umfang wird durch Fortsetzungsvergleich geprueft, nicht durch diese Liste behauptet.
Insbesondere persistiert `save_state` die Fovea bisher nur bei `FOVEA_NET`; ein Live-Pickle
enthaelt nicht automatisch Simulator und alle Zufallsstroeme. Alte Daten nie mit erfundenen
Zustandsfeldern vervollstaendigen. Fehlende Merkmale tragen ein Gueltigkeitsflag.

Testfaelle fuer D1/D3: Speichern/Neustart gegen ununterbrochene Fortsetzung; Logger aus/an;
Evaluation ohne Aenderung des Trainingszustands; verbotener Zugriff auf versteckte Scores;
fehlende Kante; erschoepftes Budget; doppeltes Job-Ergebnis; Checkpoint mit falschem Schema.
Das sind notwendige Integritaetspruefungen fuer spaetere Experimente, noch keine hier
implementierten Tests.

# Faire Kontrollen und Kosten

Kernvergleich: feste Verteilung vs. einfache adaptive Referenz vs. Replay-verbesserte
Strategie. Alle erhalten identische Ausgangskenntnis, Aufgabenmenge und Budget. Fuer H3
kommt ein nach der ersten Runde eingefrorener Scheduler hinzu. Die Parameter der Referenzen
duerfen auf denselben Entwicklungsdaten abgestimmt werden.

Zwei Kostenrechnungen berichten: (a) Nutzung einer bereits vorhandenen Bibliothek;
(b) Gesamtprojekt einschliesslich Aufbau, Replay, Policy-Suche, Evaluation und Fehlversuchen.
Ein Parallelitaetsbonus wird nicht als Lerngewinn gezaehlt. Wandzeit kann sinken, waehrend
Gesamtrechenzeit steigt. Bei unterschiedlichen Modulgroessen sowohl gleiche Datenmenge als
auch gleiches Rechenbudget vergleichen oder den nicht durchgefuehrten Vergleich benennen.

Ein gescheiterter technischer Lauf bleibt mit Fehlergrund sichtbar. Er darf nach Reparatur
ersetzt werden, aber nicht weil seine Lernleistung schlecht war. Kein stilles Nachfuellen
bis zu einem positiven Resultat. Standardstart lokal mit einem Worker, weitere Worker erst
nach Ressourcenabgleich mit den laufenden Agents.

# Stichprobe und Entscheidung

Der D2-Pilot mit zwei Seeds dient Funktion und Aufwandsschaetzung. Fuer D5 zunaechst mindestens
acht unabhaengige Seed-/Szenenbloecke budgetieren; endgueltige Anzahl anhand Pilotstreuung,
minimalem Effekt und Ziel-Power (z.B. 80 %) **vorab** fixieren. Acht sind keine Garantie fuer
ausreichende Teststaerke. Episodenzahl richtet sich nach Kompetenz und Nachweisgrenze.

Innerhalb jedes Blocks alle Arme aus derselben Basis; fuer die Bewertung feste, getrennte
Szenenlisten. Trainingsfolgen duerfen sich durch die Strategie unterscheiden. Gleicher Seed
allein paart keine unterschiedlichen ACT23-Trainingsfolgen. Unabhaengige Einheiten sind
Seeds/Laeufe/Szenenfamilien, nicht Tausende benachbarte Frames.

Effekt und 95-%-Konfidenzintervalle mit Bootstrap ueber unabhaengige Bloecke oder passendem
gepaarten Verfahren berichten; Vorzeichentest ueber Seeds als robuste Zusatzpruefung. Fuer
Quoten den vorgeschriebenen Fisher-Test angeben, bei abhaengigen Episoden aber nicht als
alleinigen Beleg verwenden. Mehrere bestaetigende Objekt-/Aufgabenvergleiche mit Bonferroni
korrigieren. Keine Wiederholung eines bitgleichen Laufs als neue Stichprobe zaehlen.

Entscheidung: **annehmen**, wenn relevanter Nutzen und Erhaltsschranken belegt sind;
**verwerfen**, wenn die Hypothese ausreichend genau widerlegt ist oder Kosten untragbar sind;
**unentschieden**, wenn die Messung keinen Schluss erlaubt. Ein p-Wert ueber 0,05 beweist weder
Gleichwertigkeit noch fehlenden Nutzen.

# Vorlage fuer den Paketabschluss

```text
Paket / Hypothese:
Protokoll-Version und vorab fixiertes Kriterium:
Code / Welt / Startzustand / Schema / Hardware:
Kommandos / Parser / Rohbelege / Artefakt-Hashes:
Arme / Seeds / Aufgaben / n / Datenaufteilung:
Primaerer Effekt / Intervall / Tests / Korrektur:
Bestandserhalt / Hilfen / Fehler / Gesamtkosten:
Replay-Abdeckung und Abweichung zum neuen ACT23-Lauf:
Entscheidung: angenommen | verworfen | unentschieden
Evidenz und Ebene:
Was als Naechstes folgt / Bedingung einer Wiederaufnahme:
```

Status im Plan aktualisieren; Befundseite, Index und Log gemeinsam fortschreiben. Nur neue
volle ACT23-Vergleiche tragen `ebene: act23-ab`, isolierte Replay-/Sensortests bleiben
`pruefstand`. Dieser Entwurf bleibt bis dahin `vermutung` / `code`.
