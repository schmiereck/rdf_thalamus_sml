---
type: Befund
title: Sieht die Uebersichtskamera die eigene Hand?
description: Ja, praktisch immer. 24 act23-Episoden mit Netz-Policy auf dem heutigen Zustand, 6352 Aufnahmen - mindestens eine Klauenspitze frei in 99 %, der Greifer nie unter 500 Pixeln (p10). Beim Tragen verdeckt das Objekt die zweite Spitze, eine bleibt in 90 % frei. Ueber den Arbeitsraum sind die Hoehen 0-70 mm gut abgedeckt (10-12 von 12 Feldern), ueber 70 mm haeuft sich alles vorne in der Mitte. Ungemessen bleibt, wie der Agent seine Hand OHNE Segmentierung im Bild findet.
tags: [act23, wahrnehmung, hand, kamera, perceive_all]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-10-14T00:00:00Z }
sources:
  - id: sonde
    resource: "Sonde im Scratchpad (nicht committet): Haken an BracketArmSim.step, jede 4. Schrittgruppe, eigener Renderer mit Segmentierung und Tiefe; Seeds 9701/9702 x 12 Ep, Aufbau wie Huellen-A/B, Kopie df320cd0, Stand f1360a4"
    title: Handsicht-Sonde
  - id: codex
    resource: /befunde/act23-arbeitsposen-kamera.md
    title: Codex-Audit der Arbeitsposen (FSM, 4 Episoden)
  - id: plan
    resource: /fragen/perceive-all-abloesen.md
    title: perceive_all abloesen
---

# Frage

Schritt 1 in [perceive_all abloesen](/fragen/perceive-all-abloesen.md) will die Umrechnung Bild ->
Tisch aus der eigenen Hand lernen: wo die Hand im Bild erscheint, ist sie laut Koerpermodell. Das
geht nur, wenn die Uebersichtskamera die Hand oft genug und ueber genug Orte und Hoehen sieht.
Nutzerauftrag 2026-10-14.

Codex hat die Sichtbarkeit schon einmal gezaehlt ([Arbeitsposen](/befunde/act23-arbeitsposen-kamera.md):
FSM, vier Episoden, ein aelterer Zustand, Klaue in allen 238 Ansichten sichtbar, beim Tragen im
Median nur 7 Klauenpixel). Hier neu: der heutige Zustand mit Netz-Policy, mehr Episoden, die
Verdeckung einzelner Messpunkte und die Abdeckung nach Ort und Hoehe.

# Aufbau

* Echte act23-Laeufe im Aufbau des [Huellen-A/B](/befunde/huellenkorrektur-ab.md): Seeds 9701 und
  9702 je 12 Episoden, Kopie des Hauptzustands, nichts zurueckgeschrieben.
* Die Sonde haengt sich an `BracketArmSim.step` und wertet jede 4. Schrittgruppe mit einem
  **eigenen** Renderer aus (Segmentierung und Tiefe, Arm sichtbar). Der Renderer des Agenten wird
  nicht beruehrt. **Geprueft:** die Ergebnisfolge beider Seeds ist mit dem echten Lauf identisch.
* Messpunkte: die Mitten der beiden Klauen-Geome und der Greifpunkt (Site zwischen den Fingern).
  Ein Punkt ist frei, wenn am Bildort nichts vor ihm liegt (Tiefentest, 6 mm Toleranz) oder dort
  der eigene Finger zu sehen ist.
* 6352 Aufnahmen. Sie sind zeitlich stark korreliert und nicht 6352 unabhaengige Faelle.

# Zahlen

    Lage                      n     mind. 1 Spitze frei  beide   Greifpunkt frei  Klauenpx Median (p10)  Greiferpx Median (p10)
    alle                     6352        99 %             77 %        60 %            233 (82)              1331 (689)
    Objekt gehoben (Tragen)   656        90 %              6 %         0 %             86 (51)               950 (636)
    Greifpunkt z  0-20 mm    1411        99 %             56 %        14 %            117 (48)               866 (512)
                 20-40 mm     728        98 %             46 %        31 %            107 (57)               960 (589)
                 40-70 mm    1667        98 %             76 %        63 %            193 (97)              1317 (873)
                 70-120 mm   1268        99 %             97 %        85 %            390 (249)             2273 (1567)
                 >120 mm     1278       100 %             99 %        99 %            680 (509)             1742 (1258)

* Der Greifer liegt nie ausserhalb des Bildes und ist nie ganz verdeckt.
* Verdeckt wird eine Klauenspitze fast nur durch den **eigenen Greifer** (87 % der Aufnahmen
  haben eine Spitze hinter Greiferteilen) und beim Tragen durch das **Objekt** (62 %). Der uebrige
  Arm verdeckt praktisch nie.
* Der Greifpunkt selbst ist oft verdeckt, weil er zwischen den Fingern liegt; als Etikettpunkt
  taugt er schlechter als die Klauenspitzen.

**Abdeckung des Arbeitsraums** (4 x 3 Felder, Aufnahmen mit freier Spitze und >= 20 Klauenpixeln):

    Hoehe        brauchbar   Felder mit >= 10
    0-20 mm        1067        10 / 12
    20-40 mm        604        11 / 12
    40-70 mm       1397        12 / 12
    70-120 mm      1085         7 / 12
    > 120 mm        933         2 / 12   (fast alles vorne in der Mitte - Ruhe- und Transitstellung)

Ungleich verteilt: in den unteren Hoehen haben einzelne Felder 0-8 Aufnahmen, andere ueber 200.

# Bewertung

* **Sichtbarkeit ist kein Hindernis fuer Schritt 1.** In jeder Aufnahme ist der Greifer mit
  Hunderten Pixeln im Bild, eine Klauenspitze praktisch immer frei. Das bestaetigt den Codex-Befund
  auf dem heutigen Zustand und mit Netz-Policy.
* **Die Hoehen, auf die es ankommt, sind abgedeckt.** Objekte sind 12-60 mm hoch; genau dort
  (0-70 mm) gibt es rund 3000 brauchbare Aufnahmen aus 24 Episoden ueber fast alle Felder. Ueber
  70 mm ist die Abdeckung schmal, das braucht nur das Tragen.
* **Nicht gemessen und jetzt die eigentliche Frage:** wie der Agent seine Hand im Bild **ohne**
  Segmentierung findet. Die Segmentierung hier ist nur Pruefer. Moegliche eigene Wege: was sich
  mit der eigenen Bewegung veraendert (Bilddifferenz bei bekannter Gelenkbewegung) oder ein
  Detektor, den der Agent aus dieser Mitbewegung selbst lernt. Heute blendet die Wahrnehmung den
  Arm beim Rendern aus; fuer Schritt 1 muss er im Bild bleiben.

# Berichtigung am eigenen Messaufbau

Der erste Durchgang wertete die Klauenspitzen nur mit dem Tiefentest an der Geom-Mitte. Die
eigene Oberflaeche der Klaue liegt aber vor ihrer Mitte, deshalb meldete er "mindestens eine
Spitze frei" nur in 45 % und "verdeckt durch den Arm" in 87 %. Mit dem Zusatz "am Bildort ist der
eigene Finger zu sehen" ergab der zweite Durchgang 99 %. Nur die Zahlen des zweiten Durchgangs
gelten.

Beim Bau fiel ausserdem ein Fehler in **frueheren** Sonden auf: wer `pc_act14` vor act23 importiert,
friert den 3-Gelenk-Arm ein, bevor act23 `ACT14_DOF=4` setzt. Der Zustand passt dann nicht, und
act23 trainiert frisch. Diese Sonde haengt sich deshalb erst beim Laden von `pc_act14` ein.
Betroffen war die Zaehlsonde im [Huellen-A/B](/befunde/huellenkorrektur-ab.md) (dort berichtigt).

# Verwandt

* [perceive_all abloesen](/fragen/perceive-all-abloesen.md)
* [Wie genau sind die Tisch-Homographien?](/befunde/homographie-genauigkeit.md)
* [ACT23-Arbeitsposen](/befunde/act23-arbeitsposen-kamera.md) (Codex)
