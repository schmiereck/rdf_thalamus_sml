---
type: Frage
title: Aspekt-Rueckmeldung und Zusammenfuehrung der Forschungszweige
description: Einordnung von Claudes Aspekt-Idee und Vorschlag fuer kontrollierte Git-Integration; noch keine Zusammenfuehrung oder neue Messung.
tags: [act23, aspekte, koordination, koerpermodell]
status: draft
evidenz: vermutung
ebene: code
generated: { by: codex, at: 2026-10-05T00:00:00Z }
sources:
  - id: claude
    resource: "main@efb3ae2:wiki/fragen/aspekt-rueckmeldung.md; wiki/befunde/loslassen.md"
    title: Gelesen im benachbarten Worktree rdf_thalamus_sml
  - id: git
    resource: "git merge-base main codex-worktree; git rev-list --left-right --count main...codex-worktree"
    title: Stand main efb3ae2, codex-worktree f9a6914
---

# Aspekt-Rueckmeldung

Die Nutzeridee trennt Rueckmeldung fuer einzelne Faehigkeiten von einem einzigen Urteil
ueber die ganze Episode. Das passt als Hypothese zu unserem
[Positionsport und Koerpermodell](/mechanismen/servo-latent-port.md): eigene Bewegung,
erwartete Bewegungsfolge und beobachtete Abweichung koennen unterscheidbare Lernziele sein.
Ein Koerpermodell kann spaeter solche Aspekte beliefern; es ersetzt damit noch keine
visuelle Hand-/Objektlokalisation. Diese ist fuer uns weiterhin nicht hinreichend geloest.

Claudes Loslass-Kopf aus fuenf Aspekten oeffnet laut dortigem Befund im zeitlich gehaltenen
Pruefsatz am Ziel zu 99 %, weiter als 5 cm entfernt zu 0 %. Im ACT23-Vergleich liegen jedoch
46/100 Lieferungen gegen 54/100 vor (zwei Seeds, vorzeitig wegen Speicher beendet).
Selbstaendiges Loslassen gelingt, aber zu frueh. Das ist ein Hinweis auf nuetzliche Zerlegung,
kein Nachweis einer besseren Gesamtarchitektur. Die Aspekt-Sicht deckte zudem widerspruechliche
Teacher-Etiketten auf; auch ein separater Kopf kann falsche Teacher-Grenzen lernen.

Fuer eine spaetere Untersuchung: Bedeutung, beobachtbare Zielgroesse und Unsicherheit jedes
Aspekts festlegen; nach ganzen Episoden trennen; Wahrnehmung, Vorhersage und Handlungsbewertung
unterscheiden. Der bisherige Kopf benutzt auch Druck. Entsprechend dem Nutzerwunsch darf eine
uebertragbare Variante davon nicht zwingend abhaengen; ohne Druck bzw. mit gestoertem Signal
gesondert pruefen. Noch kein neuer Kopf, keine Wiedereroeffnung geschlossener Forschungswege.

# Gelesener Git-Stand

Beide Verzeichnisse sind Worktrees desselben Repositorys, auf `main` bzw. `codex-worktree`.
Gemeinsamer Vorfahr: `15c063e` vom 2026-09-17. Seitdem 119 Commits nur auf main und 56 nur auf
codex-worktree; 77 bzw. 95 geaenderte Dateipfade gegen den Vorfahren.
Gemeinsam bearbeitet: `AGENTS.md`, `CLAUDE.md`, `src/pc_cvnn/pc_act16.py`,
`src/pc_cvnn/pc_act23.py`, `wiki/index.md`, `wiki/log.md`.
Das sind moegliche Integrationsstellen, keine bereits nachgewiesenen Merge-Konflikte.
Beide Worktrees hatten bei der Abfrage keine uncommitteten versionierten Aenderungen;
unversionierte lokale Artefakte sind vorhanden.

# Vorschlag, noch nicht ausgefuehrt

Das Board bleibt fuer Arbeitsabsprachen. Es uebertraegt weder Code noch Wiki-Aenderungen.
Regelmaessige Integration an abgeschlossenen Meilensteinen verhindert, dass Forschungslaeufe
dauerhaft auf unterschiedlichen Teacher-, Policy- und Simulationsstaenden beruhen.

1. Ueber das Board genaue Ausgangscommits und laufende Arbeiten abstimmen.
2. Beide Staende in einem dritten temporaeren Integrations-Worktree zusammenfuehren.
3. Textkonflikte und semantische Vertraege pruefen: Policy-Zustand, Teacher, Episodenende,
   Freeze, Datenerfassung, Ports und Zustand laden. Versuchsflags bleiben bewusst gesetzt.
4. Gezielte Tests und kurzen isolierten Lauf mit eigener Zustandskopie ausfuehren.
5. Erst den geprueften Stand in die Arbeitsbranches uebernehmen, zwischen Laeufen.

Fuer fortlaufende Zusammenarbeit ist ein regulaerer Merge die naheliegende Grundlage;
einzelne unabhaengige Fehlerkorrekturen koennen gezielt uebernommen werden. Kein pauschales
Kopieren eines Workspace ueber den anderen. Ein konfliktfreier Text-Merge belegt noch keine
funktionierende Kombination.

Unversionierte PKLs, Logs und Umgebungen werden dabei nicht zusammengefuehrt. Gelernte
Gewichte brauchen explizite Kopien und Kompatibilitaetspruefungen. Alte Messdaten behalten
ihren dokumentierten historischen Stand; neue Controller koennen andere Bewegungsdaten
erzeugen. Nach einer Integration ist daher die Aktualitaet der
[nativen ACT23-Datengrundlage](/befunde/act23-bewegungsdaten.md) zu pruefen, bevor neue
Ergebnisse auf den aktuellen Hauptzweig bezogen werden.

Diese Seite dokumentiert Analyse und Empfehlung, keine bereits beschlossene oder
ausgefuehrte Integration. Kein Code geaendert, kein Training gestartet.

## Nachtrag: Integration autorisiert und geprueft

Der Nutzer hat die Umsetzung danach autorisiert. Ergebnis, Pruefumfang und Uebernahmeweg
stehen im [Integrationsbefund](/befunde/act23-worktree-integration.md).
