---
type: Befund
title: D0-Preflight - eine Episode mutiert neun Lernkomponenten
description: Die Pkl blieb bitgleich, doch eine kopflose FSM-Episode veraenderte Weltmodell, Runtime, Fovea, Wahrnehmung, Selbsturteil und weitere In-Process-Zustaende. NO_PERSIST ist keine eingefrorene Evaluation.
tags: [act23, dream-rsi, d0, preflight, zustand, mutation]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: codex, at: 2026-09-18T11:26:32Z }
sources:
  - id: result
    resource: ../../log/d0-preflight/fsm-l-1ep/result.json
    title: Maschinenlesbares Preflight-Ergebnis
  - id: log
    resource: ../../log/d0-preflight/fsm-l-1ep/act23.log
    title: Vollstaendiges ACT23-Protokoll
  - id: audit
    resource: /befunde/dream-rsi-d0-wrist-audit.md
    title: Vorheriger Kredit- und Zustandsaudit
  - id: l-result
    resource: ../../log/d0-preflight/fsm-l-form-1ep/result.json
    title: Korrigierter L-Form-Preflight
---

# Behauptung

Eine einzelne kopflose FSM-Autoepisode mit `ACT23_NO_PERSIST=1` veraendert im laufenden Prozess
neun von zehn beobachteten D0-Komponenten. Die Pkl-Kopie selbst blieb SHA-256-bitgleich. Damit
ist direkt gemessen: fehlendes Zurueckschreiben ist keine eingefrorene Evaluation.

# Zahlen

Start: D0-Basis `base.pkl`, SHA-256 `ad9d768c...c09b9e`, eine Episode, FSM, keine Persistenz.
Der Runner schrieb ein Vorher-/Nachher-Manifest im selben Prozess und meldete `FAIL` bei
Returncode 0.

| Unveraendert | Veraendert |
|---|---|
| `dream_seen`; Pkl-Dateihash | `bm`, `colours`, `fovea`, `latent_dynamics`, `latent_goal`, `runtime`, `self_eval`, `shape_clf`, `world` |

Die Kreditzeile hatte `Label Selbst`, Quelle `Selbst`, Route `sicher geliefert`, Gewicht 1,0;
das Selbsturteil war also fuer die Protokollierung gueltig. Der gepinnte Objektfilter war jedoch
zu breit: `ACT23_AUTO_OBJ=L` matchte den Buchstaben in "Rotes Wuerfel" und fuhr den roten Wuerfel.
Dieser Lauf ist deshalb **kein** L-Wrist-Vorversuch, sondern ausschliesslich ein
Zustandsintegritaetsbefund.

# Korrigierte L-Form-Wiederholung

Nach der Korrektur auf `ACT23_AUTO_OBJ=L-Form` fuhr der Preflight tatsaechlich `obj_L`.
Der FSM-Griff scheiterte kausal (`Griff am Objekt fehlgeschlagen (Aktion)`), mit
`action_source=Selbst`, `label_source=Selbst`, Gewicht 1,0 und relativem Wrist 22,5 Grad.
Die Pkl-Kopie blieb wiederum bitgleich; die identische Liste aus neun Komponenten mutierte.

Diese Wiederholung macht den Befund fuer den gewaehlten D0-Gegenstand gueltig. Sie zeigt nicht,
dass alle neun Differenzen jeweils Lernen sind: etwa `latent_goal` enthaelt auch den
episodischen Zielzustand. Der naechste Freeze-Audit trennt deshalb Update-Stellen von erlaubtem
Aufgaben-Zustand, bevor Methoden gesperrt werden.

# Bewertung

Der Runner und die In-Process-Manifeste funktionieren: sie machten genau die Mutationen sichtbar,
die der Audit vermutet hatte. Ein Freeze darf nicht als Auswahl aus diesen Komponenten erraten
werden; er muss jede dieser Lernstellen unterdruecken und denselben Preflight danach bestehen.

Die einzelne Episode traegt keinen Lern- oder Wirkungsnachweis und ersetzt weder die festgelegte
L-Aufgabe noch eine Kontrolle.
