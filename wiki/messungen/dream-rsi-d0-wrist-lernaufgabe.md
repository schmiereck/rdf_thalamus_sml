---
type: Messvorschrift
title: D0-Kandidat - Selbstlernen einer objektrelativen Wrist-Ausrichtung
description: Vorgeschlagene, signalreiche D0-Lernaufgabe: Das Weltmodell soll aus eigenen L-Form-Griffen die objektrelative Wrist-Ausrichtung bewerten und auf neuen Positionen und Yaws besser wählen als eingefroren.
tags: [act23, dream-rsi, d0, wrist, selbstlernen, lernaufgabe]
status: draft
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
L-Form**, nicht die Aneignung einer weiteren Formklasse. Das Netz erhaelt Wahrnehmung, eigene
ausgefuehrte Wrist-Aktion und sein bestehendes Selbst-/Erfolgsurteil; es erhaelt keine
Soll-Ausrichtung. Es soll nach eigenen, gezielt diversen Griffen auf zurueckgehaltenen
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
   Wrist-Abdeckung. Der Agent sieht nur den tatsaechlichen Ausgang. Negativkredit darf nur
   greifen, wenn die Anfahrt selbst sauber war; sonst wuerde ein Wahrnehmungs- oder
   Transportfehler der Wrist-Aktion zugeschrieben.
4. Eingefrorener Kontrollarm: identische Szenen und ausgefuehrte Aktionen, aber keine Updates
   des Weltmodells oder seiner Auswahlstatistik. Eine zusaetzliche Referenz mit fester,
   ausgerichteter Wrist-Aktion misst den physikalisch erreichbaren Spielraum, nicht die
   Lernleistung.
5. Nach jedem vorab festgelegten Block nur auf Wegwerfkopien bewerten. Der Test-RNG bleibt vom
   Training getrennt. Erfolg erfordert in **beiden** Seeds mindestens +20 Prozentpunkte
   ausgerichtete Wahl gegen den eingefrorenen Arm, mindestens +10 Punkte Lieferung ohne
   Verschlechterung des Selbsturteils und keinen Rueckgang gegen den eigenen Ausgangszustand.

Die Zahlen sind bewusst Pilot-Tore, keine Powerrechnung. 40 Testepisoden pro Seed und ein
Fisher-Test sind nur deskriptiv; eine nachfolgende Scheduler-Wirkung braucht unabhaengige
Startzustaende und die im Evaluationsvertrag geforderte Stichprobe.

# Anschluss an Dream-RSI

Diese Aufgabe bietet echte, unterschiedlich informative Fortsetzungen: breite Wrist-Abdeckung,
Wiederholung in unsicheren Winkelbereichen und frueher Abbruch bei gesaettigter Auswahl. D2 kann
darauf aus gemeinsamen Startkopien kleine Trainingslinien bauen, ohne die Gewichte zwischen
Aesten zu vermischen. Damit ist sie eine bessere erste Erfahrung fuer Replay als eine Aufgabe,
die schon bei der Wahrnehmung keine stabile Identitaet hat.

# Vor dem Lauf noch zu klaeren

Der aktuelle Code- und Kreditpfad muss gegen den historischen Wrist-Befund auditiert werden:
welche nicht-gegriffenen Faelle werden heute gelabelt, ob der objektrelative Wrist-Schalter in
beiden Armen identisch ist und ob die Evaluation wirklich alle Updates einfriert. Erst danach
wird dieser Entwurf zu einer ausfuehrbaren Messvorschrift. Keine Laufserie ist mit dieser Seite
gestartet.
