---
type: Frage
title: Bruecke zu NetResearch - was in welche Richtung uebertragbar ist
description: Analyse 2026-11-10 aus dem Lesen von Wiki und Code - was NetResearch von hier uebernimmt (Fovea, Phasen-Code, Wiki-Disziplin), was von dort hierher passt (Bibliotheks-Verwaltung, schnelle Gewichte, Orakel-Messlatte), der Stufenplan fuer implantierte Netze und Vorschlaege zum Reduzieren auf Foveas und Latent-Kommandos. Nichts davon ist hier gemessen.
tags: [architektur, netresearch, fovea, reduktion, benchmark]
status: draft
evidenz: vermutung
ebene: code
generated: { by: claude/fable-5.2, at: 2026-11-10T12:00:00Z }
sources:
  - id: auftrag
    resource: "Nutzerauftrag 2026-11-10: Projekt ansehen - was uebernehmen, was abgeben, Netze implantieren und die Aufgaben als End-Benchmark; Projekt reduzieren, Wahrnehmung nur ueber Fovea(s); Ziel: Roboter, der Ziele als Latent-Kommandos annimmt, spaeter von einem LLM gesteuert"
    title: Auftrag
  - id: netresearch
    resource: "../NetResearch (github.com/schmiereck/net_research): STAND.md, PLAN_TRAINER.md, AGENDA.md, Stand c2c5fd0"
    title: NetResearch, Stand der Forschung
  - id: gelesen
    resource: "wiki/ziel.md, mechanismen/act23-modullandschaft.md, mechanismen/fovea-und-blick.md, fragen/offene-faeden-act23.md, fragen/perceive-all-abloesen.md, fragen/stetige-adressierung.md, fragen/dream-rsi-fovea.md, fragen/dream-rsi-servosteuerung.md, befunde/generalisierung-relation-zielart.md, befunde/selbstaneignung-stockt.md, befunde/d0b-fovea-portaudit.md; Code pc_act18.py (HexFovea)"
    title: Gelesene Seiten und Code
---

# Einordnung

Diese Seite ist eine Einschaetzung aus dem Lesen. **Hier ist nichts gebaut und nichts gemessen.**
Zahlen aus NetResearch sind dort gemessen (isolierte Aufgaben, also hoechstens `pruefstand` in der
Zaehlung dieses Wikis) und sagen nach der [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)
keinen act23-Lauf vorher.

NetResearch in einem Absatz: eine Benchmark-Plattform, in der jede Aufgabe ein Bild 16x16x3 als
Eingabe und 64 Ausgaben hat, alle Netze etwa 100k Parameter. Schwerpunkte sind Gedaechtnis-
Architekturen und schnelles Nachlernen ohne Vergessen ("Bibliothek" aus Saetzen schneller Gewichte
auf einem eingefrorenen Netz, Auswahl per Fehlervergleich).

# Von hier nach NetResearch

* **Fovea.** NetResearch hat gemessen, dass alle Netze scheitern, wenn sich die Figur in einem
  festen Bild bewegt, und dieselbe Welt loesen, wenn das Bild auf die Figur zentriert ist. Der
  gelernte Blick von hier ([Fovea und Blick](/mechanismen/fovea-und-blick.md)) ist die allgemeine
  Antwort darauf.
* **Phasen-Code.** Das RoPE-Ziel ist hier 18x dichter und ~7x genauer gemessen. In NetResearch
  scheitert die lokale Lernregel an Servo-Kalibrierungen mit Vorzeichen und Versatz, weil der
  Bit-Code dafuer Uebertraege braucht; in einem Phasen-Code waeren das Drehung und Konjugation.
* **Wiki-Disziplin.** `evidenz` / `ebene`, die Liste "ausdruecklich geschlossen", ehrliche Negative.
* **Relation x Zielart** als Muster fuer Generalisierungstests
  ([Befund](/befunde/generalisierung-relation-zielart.md)).

# Von NetResearch nach hier

* **Verwaltung des Klassen-Lebenszyklus.** Der Engpass hier
  ([Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md)) ist ein Verwaltungsproblem:
  geborene Klassen verhungern. Die Bibliothek dort verwaltet Eintraege fast auf Orakel-Niveau mit
  vier Bausteinen: Arbeitspuffer fuer junge Eintraege (ein junger Eintrag verdraengt nie einen
  reifen), Verdraengung nur nach bestaetigter Nutzung, Konsistenztest gegen schaedliches Teilen,
  Abspalten bei schleichender Veraenderung. Uebertragbar ist das Konzept, nicht der Code.
  Beruehrt [stetige Adressierung](/fragen/stetige-adressierung.md): faellt die Benennung weg,
  faellt auch der Lebenszyklus weg.
* **Schnelle Gewichte mit Kontext** statt Nachtrainieren je Episode. Eine Kopf-Regel zweiter
  Ordnung (rekursive kleinste Quadrate) lernt dort in einem Durchgang aus wenigen hundert
  Beispielen und vergisst mit Kontext nichts. Kandidaten hier: Koepfe auf Objekt-Latents, das
  Koerpermodell (schon linear in Merkmalen).
* **Orakel als Messlatte je Mechanismus**: trennt, ob eine Luecke am Verwalten oder am Lernen
  liegt. Hier koennte es Lieferquote und Aneignung trennen.
* **Notizblock-Gedaechtnis** (wenige Werte je Modul, `m <- mult*m + add`) fuer Objekt-Belief
  unter Verdeckung.

# Netze implantieren, Roboter als End-Benchmark

Zulaessig nach [Regel "lernendes Netz"](/entscheidungen/lernendes-netz-statt-pc-cvnn.md), Weg
nach [Expertenpfade](/entscheidungen/architektur-evolution-expertenpfad.md). Die Fovea hat 16x16
Zellen, der NetResearch-Eingang ist 16x16x3.

| Stufe | Inhalt | braucht |
|---|---|---|
| a | Fovea-Bilder und Etiketten exportieren, in NetResearch als Aufgabe einhaengen (Blick zentrieren, Hand zum Objekt) | Export-Skript hier, kein MuJoCo dort |
| b | MuJoCo-Welt als Regelkreis-Aufgabe, Teacher als Experte (beide Projekte nutzen DAgger) | MuJoCo-Anbindung dort |
| c | End-Benchmark: Lieferquote auf zurueckgehaltenen Relation-x-Zielart-Zellen, gepaart | act23-ab |

Stand: Stufe a ist am 2026-11-10 beauftragt.

# Reduzieren: Vorschlaege, ungeprueft

Kernpfad: Fovea(s) -> Objekt-Vektor -> Ziel-Latent mit Relation als Phasendrehung -> Policy ->
Servo. Das Kommando waere (Objekt-Vektor, Relation, Ziel-Vektor); ein LLM braucht dann nur ein
kleines Woerterbuch auf diese Vektoren.

* **Streichkandidaten**: die nicht verdrahteten Module (`motor.py`, `planner_chain.py`,
  `obstacle*.py`, `wrist.py`, `object_orientation.py`), der gemessen negative `LatentAttractor`,
  das doppelte `src/pc` neben `src/pc_cvnn`, die Alt-Phasen im Wurzelverzeichnis, entschiedene
  A/B-Schalter.
* **Mehrere Foveas statt `perceive_all`**: eine weite fuer das Wo, eine feine fuer das Was, eine,
  die der Hand per Propriozeption folgt. Die dritte lieferte das Handbild, das in
  [D0b](/befunde/d0b-fovea-portaudit.md) fehlte. Der Ort kaeme aus Blickrichtung und
  Propriozeption statt aus der Homographie.
* **Aufloesung**: F24/F32 brachten nichts, weil nur Peripherie dazukam. Feiner abtasten bei
  gleicher Zellzahl oder eine zweite Fovea ist der andere Weg; das ist keine Wiederholung des
  geschlossenen Versuchs, aber auch nicht belegt.
* **Erfolgsmass** wie in [perceive_all abloesen](/fragen/perceive-all-abloesen.md): gleiche
  Lieferquote mit weniger Geruest.

# Verwandt

* [Projektziel](/ziel.md)
* [Dream-RSI: Fovea](/fragen/dream-rsi-fovea.md), [Dream-RSI: Servosteuerung](/fragen/dream-rsi-servosteuerung.md)
