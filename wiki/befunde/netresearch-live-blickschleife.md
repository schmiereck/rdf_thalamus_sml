---
type: Befund
title: NetResearch-Netze steuern den Blick live im Simulator - Rangfolge wie im Pruefstand, der Arm im Bild kostet ein Viertel
description: Erster Test der Bruecke Stufe b. 12 gespeicherte NetResearch-Netze suchen nacheinander drei gezeigte Koerper, Kamerabild bei jedem Schritt neu aus MuJoCo. Mit ruhendem Arm gleich dem NetResearch-Pruefstand (Abweichung hoechstens 0,04), die Rangfolge der Netze haelt auch mit bewegtem Arm (Spearman 0,97). Faehrt der Arm nach jedem Ziel ueber den angeblickten Koerper, verlieren die besten Netze 21-28 Prozent; das sagt der Pruefstand nicht vorher. Kinematischer Arm, kein act23-Lauf.
tags: [netresearch, fovea, blick, bruecke, simulator]
status: stable
evidenz: gemessen
ebene: simulator
generated: { by: claude/opus-5.5, at: 2026-11-19T00:30:00Z }
sources:
  - id: skript
    resource: "src/pc_cvnn/netresearch_live_loop.py (Commit 2c3f7e1) gegen ../NetResearch/scripts/policy_server.py (NetResearch-Commit 0e93819); 150 Szenen, Saat 77000"
    title: Simulator-Seite und Netz-Seite
  - id: daten
    resource: "../NetResearch/results/robot_live_loop.jsonl (26 Zeilen: Orakel und 12 Netze x 2 Bedingungen)"
    title: Rohdaten
  - id: logbuch
    resource: "../NetResearch/LOGBUCH.md, Eintrag 2026-11-19 'Erster Live-Test im Roboter-Simulator' (mit der vor dem Lauf notierten Vorhersage)"
    title: Laborbuch mit Vorhersage
---

# Aufbau

Zwei Prozesse, weil die Umgebungen getrennt sind: Die Simulator-Seite (diese Umgebung, mujoco) baut Szenen
wie der Export `gazeshapec`. Drei Koerper haben dieselbe Farbe und verschiedene Formen, liegen im inneren Ring,
und der Blick steht nahe ihrem Schwerpunkt. Dazu kommt je Koerper ein Zeigebild. Die Netz-Seite (NetResearch, torch) haelt
das Netz und seinen Zustand. Ablauf je Folge: drei Hinweis-Schritte mit den Zeigebildern, dann je Ziel drei
Blickschritte. Bei jedem Schritt wird das Kamerabild neu gerendert und die Fovea mit der NetResearch-Geometrie
neu abgetastet. Alle 12 Zielfolgen ohne direkte Wiederholung (A, B, C und A, B, A). Gemessen: am Ende jedes Ziels
hoechstens eine Zelle daneben; `near_all` = alle drei Ziele getroffen.

* `static`: Arm bleibt in der Ruhelage (entspricht dem Pruefstand).
* `live`: Nach jedem Ziel faehrt der Greifpunkt kinematisch (ohne Physik, die Koerper bleiben liegen) 5 cm ueber
  den Koerper, auf dem der Blick liegt, und bleibt dort, waehrend das naechste Ziel gesucht wird. Die Hand ist dann
  im Bild, was im Training nie vorkam.

Netze: layer_s_sp4 und layer_s (24000 Updates), vitmem und attnmem (12000 Updates), je drei Trainingslaeufe.
Kein Lernzustand gelesen oder geschrieben, act23 nicht beruehrt.

# Ergebnis

Orakel 1,00 in beiden Bedingungen. `near_all`:

| Netz | Pruefstand | static | live |
|---|---|---|---|
| layer_s_sp4 (3 Laeufe) | 0,71-0,75 | 0,72-0,77 | 0,55-0,56 |
| layer_s (3 Laeufe) | 0,64 / 0,72, einer eingebrochen 0,21 | 0,63 / 0,76 / 0,22 | 0,49 / 0,60 / 0,20 |
| vitmem (3 Laeufe) | 0,32 / 0,45, einer Zufall 0,07 | 0,31 / 0,43 / 0,07 | 0,26 / 0,38 / 0,07 |
| attnmem (3 Laeufe) | 0,32 / 0,37, einer Zufall 0,07 | 0,34 / 0,39 / 0,08 | 0,28 / 0,32 / 0,07 |

* `static` gleich Pruefstand: Abweichung -0,02 bis +0,04 je Netz.
* Rangfolge haelt live: Spearman Pruefstand gegen live ueber die 12 Netze 0,97.
* Der Arm kostet die geloesten Gitter-Netze 0,14-0,21 (21-28 Prozent), vitmem und attnmem 0,05-0,07 (13-18
  Prozent). layer_s_sp4 verliert am meisten: Live liegt es knapp unter dem besten layer_s-Lauf.

# Deutung

Die Bruecke ist sauber: Fovea, Szenenbau und Schrittdeutung des Pruefstands stimmen mit dem Simulator ueberein.
Der Pruefstand sagt die Rangfolge der Netze vorher, aber nicht, wie stark ein Arm im Bild stoert. Ob der Verlust
vom Verdecken kommt oder von Ablenkung, klaert die Kontrolle unten: Ablenkung. Fuer act23 heisst das: Der Arm ist dort immer im Bild. Ein Blick-Netz aus NetResearch muesste
mit Arm-Bildern trainiert oder geprueft werden, bevor es in act23 eingesetzt wird.

# Kontrolle: Verdecken oder Ablenkung

Bedingung `away` (Commit 7d8f0ad): Nach dem ersten Ziel schwebt die Hand ueber einer freien Stelle im Bild
(mindestens 15 px, knapp 4 Zellen, von jedem Koerper), die fuenf geloesten Gitter-Laeufe, dieselben 150 Szenen.
Der Verlust ist so gross wie in `live` (0,96- bis 1,17-fach). Verdecken traegt nichts Messbares bei; es stoert das
unbekannte Bild des Arms im Blickfeld. Mit Arm im Bild bleibt der Blick ausserdem oefter auf dem gerade
gefundenen Koerper haengen (verfehlte Strecken 0,07-0,16 statt 0,01-0,05), ob die Hand dort liegt oder nicht.
Folgerung: Ein Blick-Netz muss mit Arm-Bildern im Blickfeld trainiert oder geprueft werden; die Lage der Hand ist
dabei nicht entscheidend.

# Grenzen

Kinematischer Arm, feste Schwebehoehe, keine Greifbewegung, 150 Szenen (Standardfehler von `near_all` etwa
0,01). Stufe b der Bruecke, keine act23-Aussage.

## Nachtrag 2026-11-21: Szenenfarbe falsch, Video-Aufzeichnung

**Fehler in der Messung.** `make_scene` malt die drei Koerper jeder Szene in einer eigenen Zufallsfarbe, speichert
die Farbe aber nicht. Die Farbe steht in `geom_rgba`, nicht in `qpos`. Weil zuerst alle 150 Szenen erzeugt und
danach gerechnet wurden, lief jede Szene in der Farbe der zuletzt erzeugten. Die Zeigebilder dagegen wurden beim
Erzeugen aufgenommen, also in der eigenen Farbe der Szene. In 149 von 150 Szenen hatten Zeigebild und Szene damit
verschiedene Farben. Das gilt fuer alle Live-Zahlen dieser Seite (`static`, `live`, `away`, auch den Lauf mit der
Pruefstands-Regel). Korrigiert: Die Szene traegt ihre Farbe (`rgb`), `show_scene` malt vor jeder Szene neu; neue
Zeilen tragen das Feld `scene_colour: own`. Die Szenen selbst (Lage, Blick, Zeigebilder) sind unveraendert, die
Farbe verbraucht keine Zufallszahlen. Neu gemessen ist noch nichts; die Zahlen oben gelten bis dahin nur unter
Vorbehalt. Dass `static` trotzdem nahe am Pruefstand lag (Abweichung hoechstens 0,04), spricht dafuer, dass die
Netze vor allem nach der Form suchen.

**Video.** `src/pc_cvnn/netresearch_live_video.py` zeichnet einzelne Laeufe als .mp4 (ffmpeg) oder .gif auf:
gleiche Szenen (gleiche Saat), Regeln und Bedingungen wie die Messung, ein Lauf statt zwoelf im Gleichschritt.
Links das Kamerabild mit den Abtastpunkten der Fovea, der Mitte, der Blickspur und dem gesuchten Koerper; rechts
die Zeigebilder in der Reihenfolge der Folge mit getroffen / verfehlt und die aktuelle Fovea. Fahrten des Arms
werden mit Zwischenbildern gezeigt (fuer die Messung springt er). Misst nichts, schreibt keine Ergebnisse.
Erster Test: layer_s_sp4 (24000 Updates, Seed 0), `live`, Szenen 0-2, Folgen A B C und A B A: 5 von 6 Laeufen
treffen alle drei Ziele. Die Videos liegen unter `log/video/` (nicht im Repo).
