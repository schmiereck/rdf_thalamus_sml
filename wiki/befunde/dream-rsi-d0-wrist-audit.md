---
type: Befund
title: D0-Wrist-Audit - Kreditpfad ist brauchbar, die Kontrolle noch nicht
description: Der aktuelle Code kann objektrelative Wrist-Aktionen und kausal zugeordnete Negativkredite bilden. Fuer D0 fehlen noch eine vollstaendig nachweisbare Einfrierung und ein Ausschluss privilegierter Welt-Labels.
tags: [act23, dream-rsi, d0, wrist, kredit, zustand, audit]
status: stable
evidenz: einzelmessung
ebene: code
generated: { by: codex, at: 2026-09-18T07:20:00Z }
sources:
  - id: current-code
    resource: C:/Users/thomas/Projekte/rdf_thalamus_sml/src/pc_cvnn/pc_act23.py
    title: Haupt-Worktree, Code-Audit vom 2026-09-18, Commit 11921d6
  - id: world
    resource: C:/Users/thomas/Projekte/rdf_thalamus_sml/src/pc_cvnn/arm_modules/world_model.py
    title: Weltmodell und objektrelatives Aktionsgitter
  - id: historic
    resource: /befunde/wrist-ausrichtung.md
    title: Historischer act23-A/B-Befund zur Wrist-Ausrichtung
  - id: invariants
    resource: /mechanismen/invarianten.md
    title: Persistenz- und Messinvarianten
---

# Behauptung

Die L-Wrist-Aufgabe bleibt ein geeigneter D0-Kandidat: Das aktuelle Weltmodell stellt
objektrelative Wrist-Kandidaten dar, und der Kreditpfad kann fehlende Griffe kausal der Aktion
zuordnen. Der historische Engpass "keine Gegenbeispiele" ist damit im Code teilweise
geschlossen.

Der vorhandene EXV-Einfriermodus reicht aber nicht als D0-Kontrolle. Ein gueltiger D0-Lauf
braucht einen eigenen Auswertungsweg, der alle lernenden Komponenten nachweisbar unveraendert
laesst, und darf als primaeren Lernbeleg nur Zeilen mit `Label Selbst` verwenden.

# Gepruefter Pfad

`WorldModelModule.candidates()` bildet bei `ACT23_WRIST_REL=1` das Wrist-Gitter um den aus der
Wahrnehmung kommenden Objekt-Yaw. Das Kreuzmerkmal liefert dabei `cos(2(w-yaw))` und
`sin(2(w-yaw))`; `SHARP` ergaenzt die Ausrichtungsschaerfe. Die Aufgabe ist damit im heutigen
Merkmals- und Aktionsraum repraesentierbar, ohne `ACT23_FORCE_WRIST`, das den Simulator-Yaw
privilegiert liest.

Der heutige Kreditpfad trennt die historischen Problemfaelle besser als der Befund vom Juli:

* Drucksensorverlust (`ACT23_GRIPLABEL=1`, Vorgabe) wird bei fehlender Lieferung mit vollem
  Negativgewicht als `Griff hielt nicht (Drucksensor)` gespeichert.
* Ein sauberer, aber nicht hebender FSM-Griff wird als `Griff am Objekt fehlgeschlagen (Aktion)`
  gespeichert. Im FSM ist sein Gewicht voll; im Netzpfad wird es wegen unsicherer Zurechnung
  gedrosselt.
* Nichtgreifen, unsichere Lieferung und falsches Platzieren enthalten sich. Sie werden nicht
  der Wrist-Aktion zugeschrieben.

Das Etikett stammt normalerweise aus `SelfEval`. Fällt `s_ok` aus oder ist
`ACT23_WORLD_LABEL=welt` gesetzt, ersetzt der Code es durch die privilegierte Simulator-Welt und
protokolliert `Label Welt`. Diese Zeilen koennen eine technische Pfadprobe stuetzen, aber keinen
primaeren D0-Nachweis des Selbstlernens.

# Konsequenz fuer den Versuchskern

Das Training soll zuerst den **FSM** als verlässlichen Ausfuehrungsarm verwenden. Er liefert
einen klaren Versuch am Objekt; die gelernte Aktion wird trotzdem nur als ausgefuehrte Aktion
gespeichert, nicht als Soll-Wrist. Im anschliessenden, eingefrorenen Test waehlt das Weltmodell
selbst aus seinem wahrnehmungsbasierten Kandidatengitter. Damit bleiben Teacher-Ausfuehrung und
eigene gelernte Aktionswahl getrennt sichtbar.

Die Trainingsabdeckung darf keine wahre Objektorientierung erzwingen. Insbesondere ist
`ACT23_FORCE_WRIST` fuer den D0-Lern- und Testarm ausgeschlossen. Jede auswertbare Kreditzeile
muss Aktion, relativen Wrist, Kreditroute, Gewicht und Labelquelle enthalten; der Hauptbefund
zaehlt nur `Label Selbst`.

# Kontrollluecke

`ACT23_EXV_FREEZE` blockiert Weltmodell-Update, Selbstimitation, Runtime-Training und die
episodische Speicherung. Er wird jedoch nur aktiv, wenn `ACT23_EXV_N > 1` gesetzt ist, und
veraendert damit die Ausfuehrungssemantik. Ausserdem ist er kein allgemeiner Nachweis, dass
Form-, Fovea-, Farb- und weitere Zustandsanteile unveraendert bleiben. `ACT23_NO_PERSIST=1`
unterbindet nur das Schreiben, nicht Updates im Speicher.

Vor einer D0-Serie ist deshalb ein eigener, wegwerfbarer Evaluator erforderlich. Er muss den
gleichen serialisierten Startzustand in Lern- und Kontrollarm laden, vor und nach der Evaluation
die relevanten Komponenten (mindestens Weltmodell-Daten und -Gewichte, Runtime, Form/Fovea,
Farbzustand und Zufallsgeneratoren) hashbar vergleichen und jede Aenderung als Fehler melden.
Ein Speichern-Neustart-Test bleibt Teil des spaeteren Zustandsvertrags.

# Bewertung

Dies ist ein Quelltextaudit, keine neue act23-Messung. Es bestaetigt weder den historischen
Effekt auf dem heutigen Stand noch eine ausreichende Menge selbstbeurteilter L-Zeilen. Es
praezisiert aber die naechste Implementierungsaufgabe: D0 zuerst als reproduzierbaren,
nichtmutierenden Evaluations- und Kreditprotokollpfad bauen; erst danach Budget, Seeds und
Abbruchkriterium festschreiben und fahren.

Der historische A/B-Befund bleibt die Motivation, nicht der Wirksamkeitsbeleg fuer diese neue
Serie.
