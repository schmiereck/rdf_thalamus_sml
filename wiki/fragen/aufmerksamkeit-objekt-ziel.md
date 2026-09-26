---
type: Frage
title: Aufmerksamkeit fuer Objekt und Ziel - das Objekt wird laufend angeschaut, das Ziel nur einmal
description: Nutzerfrage 2026-09-26 - hat das Netz eine Aufmerksamkeit fuer das zu tragende Objekt und eine fuer den Zielpunkt bzw. das Zielobjekt, auf die es sich konzentriert? Am Code geprueft. Das Objekt hat eine laufende Aufmerksamkeit (Fovea-Tracker alle 4 Schritte, Servo auf die Griff-Annahme beim Anfahren, Objektgedaechtnis beim Tragen). Das Ziel hat KEINE - goal_fn wird einmal je Episode aufgerufen, das Ziel wird als Koordinate bzw. Ziel-Latent festgelegt und beim Ablegen nie wieder angeschaut; die Ablage ist gegenueber dem Ziel ein offener Regelkreis. Die Policy hat zwar getrennte Eingaenge fuer Objekt und Ziel, der Zieleingang ist aber je Episode konstant. Der heutige Ablagefehler kommt allerdings zuerst aus einer groben Teacher-Schwelle, nicht aus der fehlenden Aufmerksamkeit.
tags: [act23, aufmerksamkeit, fovea, ziel, architektur, nutzeridee]
status: draft
evidenz: vermutung
ebene: code
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

# Was hier NICHT behauptet wird

Keine Wirkung. Alles ist Codeanalyse; die einzige Messung ist die Zerlegung des Ablagefehlers.

# Verwandt

* [Ablage-Schwelle im Teacher](/befunde/ablage-schwelle-im-teacher.md)
* [Der Tracker rastet auf dem Nachbarn ein](/befunde/ablenker-bindung-gemessen.md) - die Objekt-Aufmerksamkeit und ihr bekannter Fehler
* [act23-Modullandschaft](/mechanismen/act23-modullandschaft.md)
