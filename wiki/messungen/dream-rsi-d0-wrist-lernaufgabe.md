---
type: Messvorschrift
title: D0-Kandidat - Selbstlernen einer objektrelativen Wrist-Ausrichtung
description: Vorgeschlagene, signalreiche D0-Lernaufgabe: Das Weltmodell soll aus eigenen L-Form-Griffen die objektrelative Wrist-Ausrichtung bewerten und auf neuen Positionen und Yaws besser wählen als eingefroren.
tags: [act23, dream-rsi, d0, wrist, selbstlernen, lernaufgabe]
status: pruefbereit
evidenz: vermutung
ebene: code
generated: { by: codex, at: 2026-09-18T06:55:00Z }
sources:
  - id: wrist
    resource: /befunde/wrist-ausrichtung.md
    title: Bereits gemessene Lernkette fuer objektrelative Wrist-Ausrichtung
  - id: goal
    resource: /ziel.md
    title: Selbstlernen statt Teacher-Ueberbietung
  - id: d0
    resource: /befunde/dream-rsi-yt-trennbarkeit.md
    title: Die Formaufgabe ist fuer D0 verworfen
  - id: ceiling
    resource: /befunde/greif-lerndeckel.md
    title: Greifen nahe der Teacher-Decke ist kein geeigneter Lernbeleg
---

# Entscheidung

Der naechste D0-Kandidat ist das **Lernen einer objektrelativen Wrist-Ausrichtung fuer die
L-Form**, nicht die Aneignung einer weiteren Formklasse. Das Netz erhaelt Wahrnehmung, die
tatsaechlich ausgefuehrte Wrist-Aktion und sein bestehendes Selbst-/Erfolgsurteil; es erhaelt
keine Soll-Ausrichtung. Es soll nach gezielt diversen Griffen auf zurueckgehaltenen
Objektpositionen und Yaws haeufiger ausgerichtete Aktionen waehlen und besser liefern als
sein eingefrorener Ausgangszustand.

Diese Wahl ist durch einen bereits gemessenen act23-Befund begruendet: Bei 600 gepinnten
L-FSM-Episoden und einem geeigneten Kreuz-Merkmal waehlt der lernende Arm in einer getrennten
40-Szenen-Auswertung 48 % ausgerichtete Aktionen und liefert 27/40; die Kontrolle waehlt 22 %
und liefert 18/40. Der Befund ist noch keine D0-Freigabe, weil Datenaufteilung, Startzustand,
Kredit und Budget fuer Dream-RSI neu festgelegt werden muessen.

# Warum diese Aufgabe und nicht die Alternativen

* **Y/T-Formklasse:** verworfen. Die Dreisichtklasse beansprucht 59/64 T-Sichten, obwohl ein
  diagnostischer Nachbar lokale Struktur findet. Weitere Episoden wuerden den fehlerhaften
  Anspruchspfad wiederholen.
* **Direkte Adresse eines neuen Koerpers:** technisch und wissenschaftlich interessant, aber
  die Adresse entsteht bereits aus einer Sichtung. Das erfuellt allein nicht D0s Forderung nach
  vor/nach gemessenem eigenen Lernfortschritt. Ihr Bestand ueber Szenenwechsel kann spaeter eine
  eigene Aufgabe sein, wenn ein selbststaendiger Aktualisierungspfad existiert.
* **Stapeln:** noch keine lernende Policy fuer die neue Hoehenzustandsspalte; der parallel
  laufende Versuch ist ein Teacher-Machbarkeitsvergleich. Ein Fehlschlag dort testet H1 nicht.
* **Fovea-Aufloesung:** ein Wahrnehmungsziel und ein vom Pixelkanal getrennter Erfolgsmassstab
  fehlen noch; das gehoert nach bestandenem D0 in F0.

# Vorgeschlagener Versuchskern

1. Zwei frische, voneinander unabhaengige ACT23-Startzustaende. In beiden liegt die L-Form vor;
   Objektposition und Objekt-Yaw werden vom Lern- und Testsplit getrennt gezogen. Das
   Wrist-Gitter ist objektrelativ, damit die gesuchte Aktion repraesentierbar ist.
2. Vor dem Training: feste, zurueckgehaltene L-Szenen auf Wegwerfkopien auswerten. Bericht:
   Anteil ausgerichteter Wahl, Lieferung, Nichtgriff, Selbsturteil und die Ausgabe des
   Weltmodells ueber alle Wrist-Kandidaten.
3. Lernen: gleiche Zahl realer, gepinnter L-Griffe mit bewusst breiter relativer
   Wrist-Abdeckung. Zuerst fuehrt der FSM den klaren Griffversuch aus; gespeichert wird allein
   seine tatsaechlich ausgefuehrte Aktion, keine Soll-Wrist. Der Lernbeleg verwendet nur
   `Label Selbst`. Negativkredit darf nur greifen, wenn die Anfahrt selbst sauber war; sonst
   wuerde ein Wahrnehmungs- oder Transportfehler der Wrist-Aktion zugeschrieben.
4. Eingefrorener Kontrollarm: identische Szenen und ausgefuehrte Aktionen, aber keine Updates
   irgendeiner auswertungsrelevanten Komponente. Er wird aus einer Wegwerfkopie erzeugt und
   vor/nach dem Test per Komponentenhash geprueft; `ACT23_NO_PERSIST` und `EXV_FREEZE` allein
   genuegen dafuer nicht. Eine zusaetzliche Referenz mit fester,
   ausgerichteter Wrist-Aktion misst den physikalisch erreichbaren Spielraum, nicht die
   Lernleistung.
5. Nach jedem vorab festgelegten Block nur auf Wegwerfkopien bewerten. Der Test-RNG bleibt vom
   Training getrennt. Erfolg erfordert in **beiden** Seeds mindestens +20 Prozentpunkte
   ausgerichtete Wahl gegen den eingefrorenen Arm, mindestens +10 Punkte Lieferung ohne
   Verschlechterung des Selbsturteils und keinen Rueckgang gegen den eigenen Ausgangszustand.

Die Zahlen sind bewusst Pilot-Tore, keine Powerrechnung. 40 Testepisoden pro Seed und ein
Fisher-Test sind nur deskriptiv; eine nachfolgende Scheduler-Wirkung braucht unabhaengige
Startzustaende und die im Evaluationsvertrag geforderte Stichprobe.

# Fixierter D0-Pilotvertrag v1

Dieser Vertrag ist vor einer Lernserie festgelegt. Er nutzt die vorhandene Auto-Schleife; er ist
kein Ersatz fuer den vollstaendigen Szenen- und Checkpointvertrag aus D1.

| Feld | Festlegung |
|---|---|
| Code / Basis | Commit `7d4f444`, `src/pc_cvnn/state/dream_rsi_d0_20260917/base.pkl`, SHA-256 `ad9d768c...c09b9e` |
| Trainingslinien | zwei getrennte Kopien der Basis, `ACT23_SEED=17` und `29`; keine Kopie wird zwischen Linien geteilt |
| Training | je 120 gepinnte FSM-`L-Form`-Episoden mit [`act23_d0_training_runner.py`](../../src/pc_cvnn/act23_d0_training_runner.py), `ACT23_WRIST_REL=1`, kein `ACT23_FORCE_WRIST`; Updates nur im Linien-Checkpoint |
| Primaere Kreditdaten | nur JSONL-Zeilen mit `action_source=Selbst`, `label_source=Selbst`, Gewicht 1,0 und einer kausalen Aktionsroute |
| Testdaten | je Linie vor und nach Training zwei eingefrorene Familien a 40 Episoden mit `ACT23_SEED=101` und `103`, `ACT23_AUTO_OBJ=L-Form`, getrennte Wegwerfkopien |
| Kontrolle | dieselbe Basis auf denselben Testseeds mit `ACT23_D0_FREEZE=1`; vor/nach jeder Evaluation leerer Lernzustands-Diff und bitgleicher Pkl-Kopiehash |
| Zusatzreferenz | feste ausgerichtete Wrist bleibt als Machbarkeitsreferenz getrennt und zaehlt nicht zum Lernvergleich |
| Primaere Metriken | pro Linie und gepoolt: Anteil ausgerichteter relativer Wrist, Lieferung, Selbsturteil, gueltige Selbst-Kreditzeilen und deren Routen |
| Annahmetor | in **beiden** Linien mindestens +20 Prozentpunkte ausgerichtete Wahl gegen die eingefrorene Kontrolle, mindestens +10 Punkte Lieferung, kein Rueckgang des Selbsturteils und kein Test-Integritaetsfehler |
| Statistik | Quoten und Differenzen je 40er-Familie berichten; Fisher-Test deskriptiv, Linien als unabhaengige Einheiten, kein positiver Schluss allein aus gepoolten Episoden |

Die Testseeds sind fest und kommen nie im Training vor. Bis D1 gibt es keine serialisierte
Szenenliste: gleiche Seedfamilie bedeutet deshalb dieselbe Auto-Schleifen-Initialisierung auf
einer frischen, eingefrorenen Kopie, nicht den behaupteten Bit-fuer-Bit-Simulatorzustand.
Das ist als Pilotgrenze zu berichten, nicht wegzunormieren.

**Technische Abbruchregel:** Nach 60 Trainingsfolgen wird die Linie als technisch unzureichend
geschlossen, wenn weniger als 20 primaere Selbst-Kreditzeilen oder weniger als vier belegte
relative Wrist-Gitterzellen vorliegen. Nach 120 Folgen gilt dasselbe mit 40 Zeilen bzw. vier
Zellen. Ein solcher Arm wird als unentschieden dokumentiert und nicht bis zu einem guenstigen
Ergebnis nachgefuellt. ACT23-Abbruch, fehlender Kredit-JSONL, Pkl-Hashabweichung oder ein
Lernzustands-Diff im Test beendet nur die betroffene Messung als technisch fehlgeschlagen.

# Anschluss an Dream-RSI

Diese Aufgabe bietet echte, unterschiedlich informative Fortsetzungen: breite Wrist-Abdeckung,
Wiederholung in unsicheren Winkelbereichen und frueher Abbruch bei gesaettigter Auswahl. D2 kann
darauf aus gemeinsamen Startkopien kleine Trainingslinien bauen, ohne die Gewichte zwischen
Aesten zu vermischen. Damit ist sie eine bessere erste Erfahrung fuer Replay als eine Aufgabe,
die schon bei der Wahrnehmung keine stabile Identitaet hat.

# Audit und verbleibende Freigabe

Der Kredit- und Zustandsaudit ist abgeschlossen: [D0-Wrist-Audit](/befunde/dream-rsi-d0-wrist-audit.md).
Er bestaetigt das objektrelative Gitter und die kausalen Negativrouten, korrigiert aber den
Versuchskern bei Labelquelle und Kontrolle. Der [D0-Integritaetshelfer](/mechanismen/dream-rsi-d0-integritaet.md)
baut Komponentenhash und maschinenlesbares Kreditprotokoll bereits opt-in. Der
[`D0EvaluationRunner`](../../src/pc_cvnn/act23_d0_evaluation_runner.py) legt diese um feste
Episoden; der Lernzustands-Freeze besteht im L-Preflight. Keine Lernserie ist mit dieser Seite
gestartet.
