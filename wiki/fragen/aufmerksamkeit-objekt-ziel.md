---
type: Frage
title: Aufmerksamkeit fuer Objekt und Ziel - das Objekt wird laufend angeschaut, das Ziel nur einmal
description: Nutzerfrage 2026-09-26 - hat das Netz eine Aufmerksamkeit fuer das zu tragende Objekt und eine fuer den Zielpunkt bzw. das Zielobjekt, auf die es sich konzentriert? Am Code geprueft. Das Objekt hat eine laufende Aufmerksamkeit (Fovea-Tracker alle 4 Schritte, Servo auf die Griff-Annahme beim Anfahren, Objektgedaechtnis beim Tragen). Das Ziel hat KEINE - goal_fn wird einmal je Episode aufgerufen, das Ziel wird als Koordinate bzw. Ziel-Latent festgelegt und beim Ablegen nie wieder angeschaut; die Ablage ist gegenueber dem Ziel ein offener Regelkreis. Die Policy hat zwar getrennte Eingaenge fuer Objekt und Ziel, der Zieleingang ist aber je Episode konstant. Der heutige Ablagefehler kommt allerdings zuerst aus einer groben Teacher-Schwelle, nicht aus der fehlenden Aufmerksamkeit.
tags: [act23, aufmerksamkeit, fovea, ziel, architektur, nutzeridee]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-09-26T00:00:00Z }
sources:
  - id: code
    resource: "src/pc_cvnn/pc_act16.py run_combined: goal_fn einmal je Episode (Zeile ~483), track_fn alle 4 Schritte mit Servo in over/lower (~575), place_servo_fn beim Tragen (~754); pc_act23.py _plan_ueber_ports / _ziel_ueber_ports"
    title: Wer wann wohin schaut
---

# Die Frage

*"Ob wir die Aufmerksamkeiten richtig steuern. Also ob wir eine Aufmerksamkeit fuer das zu
transportierende Objekt und seine Position haben und eine Aufmerksamkeit fuer den Zielpunkt / das
Zielobjekt, auf die sich das Netz konzentriert."* (Nutzer, 2026-09-26)

# Was heute da ist (am Code)

    Objekt   LAUFEND. Die Fovea (HexFovea, komplexes PC-Netz) verfolgt das Objekt alle 4 Schritte.
             Beim Anfahren (over/lower) korrigiert die Sichtung die Griff-Annahme im geschlossenen
             Regelkreis (Servo), verliert sie es, sucht sie neu ("stochern").  Beim Tragen haelt ein
             praediktives Objektgedaechtnis den Blick.
    Ziel     EINMAL. goal_fn wird zu Beginn der Episode EINMAL aufgerufen; das Ziel wird aus der
             Wahrnehmung aufgeloest (Zieladresse) bzw. als Marker gesetzt und dann als Koordinate
             bzw. RoPE-Ziel-Latent festgehalten.  Beim Ablegen steuert der Latent-Servo die Hand
             gegen DIESES feste Latent.  Niemand schaut waehrend der Ablage auf das Ziel, und es gibt
             keinen Vergleich "Objekt in der Hand gegen Zielort" im Bild.
    Policy   hat getrennte EINGAENGE fuer Objekt (xy, z) und Ziel (xy, ggf. z) -- der Objekteingang
             folgt der laufenden Annahme, der Zieleingang ist je Episode KONSTANT.

Es gibt also EINE Blickquelle, und sie gehoert dem Objekt. Die Ablage ist gegenueber dem Ziel ein
offener Regelkreis.

# Was die Messung dazu sagt

Der bekannte Ablagefehler (Median 25-26 mm) kommt **zuerst nicht** aus der fehlenden
Ziel-Aufmerksamkeit, sondern aus einer groben Schwelle im Teacher: er laesst los, sobald die Hand
weniger als 20 mm vom Ziel entfernt tief genug ist
([Ablage-Schwelle im Teacher](/befunde/ablage-schwelle-im-teacher.md)). Die Wahrnehmung der Objektlage
ist mit 12 mm genauer als die Ablage.

**Erst wenn diese Schwelle faellt, wird die Aufmerksamkeit zum Engpass:** dann bestimmen der
Wahrnehmungsfehler des Objekts in der Hand (12 mm) und die Genauigkeit, mit der das Ziel EINMAL
gesehen wurde, die Ablage. Eine zweite Aufmerksamkeit, die beim Ablegen Objekt UND Ziel im Bild
haelt und ihren Abstand schliesst (Blick-Servo auf den relativen Versatz), waere der naechste Hebel.

# Moegliche Schritte, in dieser Reihenfolge

1. **Die Teacher-Schwelle messen** (`ACT16_NEAR_ABLAGE`, s. Befundseite) - billig, und sie entscheidet,
   ob Aufmerksamkeit ueberhaupt schon der Engpass ist.
2. **Das Ziel beim Ablegen wieder anschauen** - goal_fn/Zieladresse waehrend der Ablagephase erneut
   aufloesen und das Ziel-Latent nachfuehren. Kleinster Eingriff, testet den Nutzen.
3. **Relative Aufmerksamkeit** - Objekt-in-der-Hand und Ziel im selben Blick, gesteuert wird der
   Versatz. Braucht einen zweiten Blickpunkt oder einen Blick, der beide umfasst (Zoom); dort sitzt
   die eigentliche Architekturfrage.

# Gemessen 2026-09-27: das Ziel nochmal anschauen bringt nichts - das Ziel ist nicht das Problem

`ACT23_ZIEL_NACHSEHEN` (980d305, Vorgabe 0): sobald der Agent traegt und die Hand 40 mm vor dem Ziel
steht, loest er die Zieladresse ein zweites Mal ueber die Kamera auf. Neu im Protokoll der Abstand
zum WAHREN Ziel (wahre Bezugslage plus Versatz). Zieladresse "an", FSM, Ablage-Naehe 8 mm, je
Episode gepaart, Seeds 9811/9812 je 60 Ep, 120 Paare:

                                        ein Blick        zwei Blicke
    geliefert                           52 / 120         52 / 120      (8 | 8, p = 1,00)
    Ziel beim ersten Blick daneben      Median 1 mm      2 mm
    zweiter Blick                       -                46x ausgeloest, 14x gescheitert (verdeckt);
                                                         gegen den ersten: 10 besser, 32 gleich, 4 schlechter
    Endlage zum WAHREN Ziel             Median 20 mm     21 mm         (gepaart 28 besser, 31 schlechter)
    beim Loslassen seitlich             12 mm            14 mm
    Objektlage: Annahme gegen Wahrheit  16 mm            17 mm

**Das Ziel wird schon beim ersten Blick auf 1-2 mm genau gesehen.** Ein zweiter Blick hat nichts zu
korrigieren und scheitert nahe am Arm oft an der Verdeckung. Der verbleibende Fehler steckt beim
OBJEKT: die Annahme ueber seine Lage in der Hand weicht um 16-17 mm ab, und nach dem Loslassen
rutscht es weiter (12 mm beim Loslassen, 17-20 mm am Ende).

**Die Antwort auf die Nutzerfrage** lautet damit, Stand heute: eine zweite Aufmerksamkeit fuer das
ZIEL lohnt nicht - es wird schon genau genug gesehen. Lohnen koennte eine Aufmerksamkeit fuer das
OBJEKT IN DER HAND waehrend der Ablage (seine Lage wird beim Tragen 16 mm falsch geglaubt), und die
Ablage selbst (Drift nach dem Loslassen). Die Teacher-Schwelle war der erste und groesste Posten
([dort](/befunde/ablage-schwelle-im-teacher.md)).

# Gemessen 2026-09-27: das Objekt in der Hand ansehen

Beim Tragen gilt die Objektlage im Code als GLEICH der Hand (sobald der Fingerdruck > 0,3 N ist);
der Teacher bringt die HAND zum Ziel. Der tatsaechliche Versatz Hand-Objekt beim Loslassen
("Glaube") ist 12-16 mm und landet in der Ablage. Also: das Objekt ansehen und die Hand so fuehren,
dass das OBJEKT aufs Ziel kommt (`ACT23_OBJ_SEHEN`, `ACT16_OBJSICHT_Z`, `ACT16_OBJ_VERSATZ`, alle
Vorgabe 0, zeichengleich).

**Vorpruefung, woher der Blick kommen muss** (je 30 Ep, FSM, Zieladresse):

    Blick aus Traghoehe (Hand 60-93 mm)   8 von 17 verdeckt; gesehen 7-30 mm daneben (Median ~16) --
                                          MEHR als der Versatz selbst (Median ~13); der gesehene
                                          Versatz liegt fast immer bei 17-22 mm (Parallaxe)
    Blick aus der Tiefe (Hand < 35 mm)    8 von 8 gesehen, 2-18 mm daneben (Median ~5-6) --
                                          weniger als der Versatz (Median ~10)

**A/B** (FSM, Ablage-Naehe 8 mm, Blick unter 35 mm, Seeds 9811/9812 je 60 Ep, 120 Paare):

                                          Hand aufs Ziel    Objekt aufs Ziel
    geliefert                             51 / 120          51 / 120        (11 | 11, p = 1,00)
    Endlage zum WAHREN Ziel (alle Ablagen) 22 mm            20 mm
    Blick ausgeloest                      -                 26 von 80 Ablagen, 3x nicht gesehen
    nur Episoden mit gesehenem Objekt     18 mm       ->    12 mm zum wahren Ziel (n = 22)

**Wo die Korrektur greift, wirkt sie** (18 -> 12 mm). Sie greift aber nur bei einem Drittel der
Ablagen: die uebrigen Objekte fallen schon AUS DER HOEHE ("beim Oeffnen 65 mm ueber Ruhelage") -
der Griff loest sich beim Tragen, bevor die Hand unten ist. Die Lieferquote aendert sich nicht.

**Stand der Aufmerksamkeitsfrage:** die Objekt-Aufmerksamkeit ist der richtige Posten und wirkt,
aber der naechste groessere Verlust liegt davor - im Halten beim Tragen und in der Drift nach dem
Loslassen. Einschraenkung: zwei Seeds, einfache Korrektur (ein Blick, ein Versatz), nur FSM.

# Was hier NICHT behauptet wird

Keine Wirkung. Alles ist Codeanalyse; die einzige Messung ist die Zerlegung des Ablagefehlers.

# Verwandt

* [Ablage-Schwelle im Teacher](/befunde/ablage-schwelle-im-teacher.md)
* [Der Tracker rastet auf dem Nachbarn ein](/befunde/ablenker-bindung-gemessen.md) - die Objekt-Aufmerksamkeit und ihr bekannter Fehler
* [act23-Modullandschaft](/mechanismen/act23-modullandschaft.md)
