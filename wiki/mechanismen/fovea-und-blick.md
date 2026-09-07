---
type: Mechanismus
title: Fovea und Blicksteuerung
description: Wie der Blick vom Detektor entwoehnt wurde - identitaetsgetriebener Blick, Zoom-Suche, Objektgedaechtnis, Winkelablesung auf den Hexzellen. Drift 38 px auf 8,5 px; Lieferrate beruehrt es nicht.
tags: [act23, fovea, wahrnehmung]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-07T00:00:00Z }
verified: { by: human:thomas, at: 2026-07-16T00:00:00Z }
sources:
  - id: chronik
    resource: /chronik/act23.md
    title: act23-Chronik, Fovea-Eintraege 2026-07
---

# Behauptung

Der Blick ist detektorfrei geworden: er **findet** (Zoom-Suche), **haelt** (Chroma-Identitaet) und
**liest den Winkel** (Zellen-Yaw). Das ist ein architektonischer Gewinn - **kein Lieferhebel**.
Die Wahrnehmung war nie der Engpass.

# Die Stufen, jede gemessen

    Blickdrift (Gaze gegen Detektor, px)         Mittel   Max
    Detektor setzt den Blick (Ausgangslage)        ~15      -
    reine Identitaet (Kosinus auf Klassenfarbe)     22     46   bimodal, beste Ep 3-8 px
    Identitaet + sparsamer Anker                    36      -   das Netz traegt den Blick nicht allein
    HYBRID (Identitaet, bei Verlust Occupancy)      19     35
    ohne jeden Anker, klassentrainiert              44     -    8/24 Ep detektorfrei unter 12 px
    + Objektgedaechtnis                             37     77   Traage-Ausbruch 118 -> 77
    + bidirektionaler Zoom + Lock-Freigabe          24,7   109
    + Chroma-Gate statt Kosinus                    ** 8,5    50 **  jede Ep 2,7-15,8 px

**Der entscheidende Fund war das Identitaets-Gate, nicht die Zellzahl.** Die erste Zellenablesung
las in jeder Konfiguration 30-45 Grad Rauschen; Ursache war das **Kosinus-Gate**
(`MATCH_TH = 0,86`): der **graue Tisch** besteht es gegen ungesaettigte Klassenchromatizitaeten,
und seine Leuchtdichte dominiert die Gewichte. Mit dem Chroma-Abstands-Gate (der Metrik des
Farb-Open-Sets) trifft die F16-Zellenablesung die rohe PCA:

    Winkelfehler (Median)   lang 1,0 Grad | L 2,0 | T 7,4 | U 9,4   (U p90 sogar besser, Pooling entrauscht)
    Aufloesung: F24/F32 IDENTISCH zu F16 - zusaetzliche Zellen sind reine Peripherie

Dasselbe Kosinus-Gate hatte auch die **Blick-Identitaet** mit Tischzellen verduennt - ein
Gutteil des vom Nutzer beobachteten Umherwanderns.

# Objektgedaechtnis (`ObjectMemoryModule`)

Ein eigenes PC-Modul mit dem Vorhersagen-Korrigieren-Idiom des Koerpermodells, aber fuer das
**Objekt**, aus Sehen und Propriozeption ohne Detektor: **korrigiere** auf die Sichtung des Netzes,
wenn sichtbar; **sage vorher**, dass das gehaltene Objekt **an der Hand** ist, waehrend getragen
wird; sonst halten und abklingen.

Grenze, fundamental und nicht ein Trainingsmangel: der Active-Inference-Trieb zentriert nur, was
**gerade unter der Fovea** ist - er kann nicht wissen, wohin ein verschwundenes Objekt ging. Das
war die eigentliche Aufgabe des Ankers.

# Servo: was der Blick steuern darf

`ACT23_FOVEA_SERVO`: die Anfahrtskorrektur kommt aus der Blick-Ueberzeugung des Netzes, der
Detektor ist Rueckfall. Torschranken: **Identitaets-Lock** (eine Fehlfixation kann den Arm nie
steuern), 5-cm-Sprungtor, **Greifer-offen-Tor** (die Tischhomographie gilt fuer gehobene Objekte
nicht).

    Servo-A/B (100 Ep je Arm): Detektor 48/100 gegen Fovea 44/100 = GLEICHAUF
    Das Netz trug 51% aller Servo-Frames; Uebereinstimmung 4-12 mm

**Ehrliches Negativ, zurueckgenommen:** der geschlossene Kreis fuer das **lange Objekt** (100 %
Netz-Frames, erster reiner Netz-Kreis) lieferte 9/20 gegen 13/20 offen. Die Fehlschlaege haeufen
sich 40-60 mm ausserhalb der Mitte = **Verdeckungs-Schwerpunkt-Signatur** (der Greifer verdeckt
den Stab, der Schwerpunkt des sichtbaren Materials wandert entlang der Langachse). Kompakte
Objekte sind unbetroffen. Das lange Objekt behaelt `servo=False`.

# Fallen

* **Der Blick ist NICHT nur Aufmerksamkeit, wenn eine Variable doppelt benutzt wird.** Der
  Gedaechtnisblock verwendete das lokale `obs` als Kladde fuer die Pixelbeobachtung - `obs` ist
  aber zugleich die Welt-xy-Beobachtung des Greif-Servos. Der Servo bekam eine Pixelkoordinate
  (~50-200) als Meter: 0 Lieferungen, jede Episode "nicht gegriffen". Ich hatte das zuerst als
  Varianz fehlgedeutet. **Fovea-Aenderungen muessen auf LIEFERUNG rauchgetestet werden, nicht
  nur auf Drift.**
* **Ein Wahrnehmungs- oder Servofehler, der in einen LIFELONG-Puffer geloggt wird, vergiftet den
  Lerner dauerhaft.** Der obige Fehler schrieb 6250 von 24000 DAgger-Zeilen mit |Koordinate| > 1 m.
  Die Policy griff im Netz-Modus **nichts** (0/12), waehrend FSM auf demselben Zustand 6/12
  lieferte. Der Fix braucht **beides**: eine Quellwache (`observe` verwirft Zustaende ueber
  `SANE_M = 1 m`) und eine Ladeheilung (`runtime.sanitize()`). Danach 0/12 -> 5/12.
* **Ein Blick-Lock auf dem falschen Objekt haelt sich selbst.** Die Occupancy-Zentrierung rastet
  auf beliebigem Material ein; der Identitaetstrieb kann nicht zurueck, weil das richtige Objekt
  ausserhalb des Ausschnitts liegt. Fix: anhaltender Identitaetsverlust loest die Zentrierung und
  startet eine **Zoom-Suche**.
* **Die Ueberzeugung darf den Blick nur oberhalb einer Konfidenz treiben** - sonst parkt er nach
  dem Loslassen auf dem Roboter und kehrt nie zurueck.

# Offen

Die tiefste Stufe fehlt: die Ablesung auf den **eingeschwungenen PC-Netz-Zellzustaenden** statt
auf der abgetasteten Salienz. Die Winkelablesung ist heute ein technischer, fovea-lokaler Griff
auf Rohpixel - **nicht** das Hexnetz, das den Winkel sieht.

# Verwandt

* [Modullandschaft](/mechanismen/act23-modullandschaft.md)
* [Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md)
