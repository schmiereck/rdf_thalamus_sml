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

# BERICHTIGUNG und Wiederholung (2026-09-28): es fiel nichts aus der Hoehe

Die "Objekte, die schon aus der Hoehe fallen" (oben) waren **kein Griffverlust**: mit
Ablage-Naehe 8 mm erreichte die FSM beim Tragen die Absenkbedingung oft nie, lief in die
Tragezeitgrenze und oeffnete am Episodenende ueber dem Ziel - der Griff hielt bis dahin (Druck beim
Tragen 5-7 N). Deshalb loeste der Blick nur bei einem Drittel der Ablagen aus. Details und Abhilfe
(`ACT16_SENK_NAH`, 11c651a): [Ablage-Schwelle](/befunde/ablage-schwelle-im-teacher.md), Berichtigung.

**Wiederholt mit SENK_NAH = 20 mm** (sonst wie oben: FSM, Zieladresse, Ablage 8 mm, Blick unter
35 mm, Seeds 9811/9812 je 60 Ep, 120 Paare):

                                          Hand aufs Ziel    Objekt aufs Ziel
    Zeitgrenzen-Abwuerfe                  2                 4   (vorher 30 / 40)
    Ablagen / Objekt gesehen              78 / 55           79 / 57
    seitlich beim Loslassen               20 mm             21 mm
    zum WAHREN Ziel (alle Ablagen)        22 mm             21 mm
    nur mit gesehenem Objekt (n = 53)     21 mm      ->     15 mm zum wahren Ziel
                                          (seitlich 19 -> 17)
    geliefert                             56 / 120          49 / 120   (18 | 11, p = 0,27)

**Der Blick loest jetzt bei drei Vierteln der Ablagen aus, und wo er das Objekt sieht, rueckt es
6 mm naeher ans wahre Ziel (21 -> 15 mm).** Die Lieferquote folgt nicht: 7 Lieferungen weniger,
nicht signifikant. Der Gewinn ist kleiner als der gesehene Versatz (14-15 mm) - der Blick ist rund
5 mm genau, und das Objekt verschiebt sich beim Nachfuehren unten in der Klaue weiter (Vermutung,
nicht gemessen: die Hand korrigiert, waehrend das Objekt schon den Tisch beruehrt).

Stand: die Objekt-Aufmerksamkeit ist der richtige Posten fuer den Ablagefehler, bringt als
einfache Korrektur (ein Blick, ein Versatz) aber keine Lieferungen. Schalter bleiben aus.

# Gemessen 2026-09-28: in der Luft korrigieren - kein Schleifen, das Fehlerbudget ist 8 + 8 mm

`ACT16_LUFT_H` (Vorgabe 0, zeichengleich): die Hand haelt beim Nachfuehren 15 mm ueber der
Ablagehoehe, bis sie naeher als 8 mm an der verschobenen Stelle steht, und senkt erst dann ab.
Neu im Protokoll: beim Loslassen der Abstand Hand-Sollstelle und wie weit das Objekt seit dem Blick
in der Klaue gewandert ist. Wie oben (FSM, SENK_NAH, Blick unter 35 mm, Seeds 9811/9812, 120 Paare):

                                          Blick            Blick + Luft
    geliefert                             49 / 120         51 / 120    (12 | 14, p = 0,85)
    zum WAHREN Ziel, Objekt gesehen       17 mm            15 mm       (n = 49)
    Objekt seit dem Blick gewandert       3 mm (Q75 8-9)   3 mm (Q75 6-10)

**Die Vermutung "das Objekt wird unten mitgeschleift" ist widerlegt**: es wandert zwischen Blick
und Loslassen nur 3 mm, in beiden Armen. Die Schwebe bringt 2 mm und keine Lieferungen.

**Das Fehlerbudget beim Loslassen** (Objekt gesehen, Mediane je Seed und Arm):

    Blick daneben (Richtungsfehler des gesehenen Versatzes)   7-9 mm
    Hand von der Sollstelle                                    7-8 mm  (= NEAR_ABLAGE: sie laesst
                                                                        los, sobald sie 8 mm erreicht)
    Objekt in der Klaue gewandert                              3 mm
    Objekt seitlich vom Ziel                                   17-19 mm

Zwei gleich grosse Posten von je ~8 mm, die sich addieren koennen. Die naechsten Hebel waeren
also ein genauerer Blick (der Blick aus 34 mm Hoehe hat noch Parallaxe; das Objekt liegt nach dem
Ablegen auf dem Tisch und wird DANN genau gesehen - daraus liesse sich die Korrektur des Blicks
selbst lernen, ohne Teacher) und eine engere Hand-Toleranz. Nicht gemessen.

# Gemessen 2026-09-28: die Blickkorrektur selbst lernen (ehrliches Negativ, zwei Seeds)

`ACT23_BLICK_LERNEN` (b92c299, Vorgabe 0). Etikett ohne Teacher und ohne Simulator-Wahrheit: nach
dem Ablegen wird das Objekt auf dem Tisch GESEHEN; gelernt wird (Ridge) "gesehener Versatz, Handlage,
Hoehe -> Landestelle relativ zur Hand beim Loslassen" - Parallaxe und Drift in einem. 1 = Schatten
(lernt, benutzt den Rohblick), 2 = benutzt ab 12 Beispielen. FSM, SENK_NAH, Blick unter 35 mm,
Seed 9811, 150 Ep je Arm, gepaart:

    Etikett gegen Wahrheit                 1-3 mm (Median) -- das Selbst-Etikett ist gut
    Vorhersagefehler je 30 Ep              Schatten: roh 10-16, gelernt  9-16 mm
                                           benutzt:  roh 12-17, gelernt  5-11 mm
    zum WAHREN Ziel (Objekt gesehen, n=68) 17 mm -> 17 mm
    geliefert                              68 / 150 gegen 69 / 150 (14 | 15, p = 1,00)

**Das Etikett aus der eigenen Kamera ist genau (1-3 mm), das Lernen aber bringt kaum etwas:** im
Schattenarm sagt das gelernte Modell die Landestelle kaum besser vorher als der Rohblick, und wo es
benutzt wird, bleibt das Objekt 17 mm vom wahren Ziel, die Lieferungen gleich. Der naheliegende
Grund: die Landestelle enthaelt die Drift nach dem Loslassen (Median 12 mm), und die ist aus Blick,
Handlage und Hoehe nicht vorhersagbar. Der bessere Vorhersagefehler im benutzten Arm (5-11 mm)
schlaegt nicht auf die Endlage durch - ungeklaert.

**Seed 9812 (nachgetragen, 150 Ep je Arm):** Etikett gegen Wahrheit 4 mm. Hier sagt das gelernte
Modell auch im Schattenarm besser vorher (roh 10-18, gelernt 8-14 mm), im benutzten Arm roh 17-22
gegen gelernt 8-17 mm. Die Endlage wird trotzdem SCHLECHTER: 17 -> 20 mm zum wahren Ziel (Objekt
gesehen, n = 56), geliefert 58 gegen 56 (11 | 9, p = 0,82).

**Beide Seeds zusammen (300 Paare):** geliefert 126 gegen 125 (25 | 24, p = 1,00), zum wahren Ziel
17 -> 18 mm. **Ehrliches Negativ:** der Agent lernt aus eigener Beobachtung, die Landestelle
relativ zur Hand besser vorherzusagen, aber das bringt das Objekt nicht naeher ans Ziel. Warum eine
bessere Vorhersage nicht durchschlaegt, ist ungeklaert - eine Vermutung ist, dass die Drift von der
Handbewegung selbst abhaengt (groessere Korrektur, andere Drift), sodass das in einem Arm gelernte
Modell im anderen nicht gilt. Nicht gemessen. Der Schalter bleibt aus.

# BERICHTIGUNG (2026-09-28, spaet): "beim Loslassen" war NICHT der Moment des Loslassens

Die Ablage-Zeile nimmt ihren Schnappschuss im LETZTEN Schritt, in dem die Klaue geschlossen ist UND
das Objekt noch mehr als 14 mm ueber seiner Ruhelage haengt (`run_combined._release`). Solange
sofort nach dem Absenken losgelassen wurde (Vorgabe), war das praktisch derselbe Augenblick. Mit
`ACT16_SENK_NAH` (und `ACT16_OBJ_VERSATZ`, `ACT16_LUFT_H`) fuehrt die Hand aber UNTEN noch nach -
dann friert der Schnappschuss zu Beginn des Nachfuehrens ein. Diagnose (FSM, SENK_NAH, 62 Ablagen,
neue Protokollfelder Reichpunkt/Phase):

    Schnappschuss in Phase place nach median 30 Schritten (nicht beim Oeffnen)
    Reichpunkt - Ziel entlang der Klaue    Q25/50/75  -34 / -28 / -6 mm   (die Hand ist noch unterwegs)
    Objekt - Reichpunkt entlang            Q25/50/75   +8 / +12 / +18 mm  (quer 0) -- der Griff sitzt stabil
    Objekt in der Klaue Griff -> Schnappschuss: median 6 mm gewandert

**Folgen fuer die Seiten dieses Tages:** "seitlich beim Loslassen", "entlang der Klaue", "danach
gedriftet" und das "Fehlerbudget" in den SENK_NAH-, Objektblick-, LUFT- und Blick-Lern-Reihen sind
Werte eines FRUEHEREN Augenblicks; die "Drift" enthaelt die restliche Handbewegung. UNBERUEHRT sind
die Endlagen ("final", "zum WAHREN Ziel") und alle Lieferzahlen - und damit alle Wirkungsaussagen
(keine der Massnahmen aendert die Lieferungen). Das Etikett des Blick-Lerners (Ruhelage minus Hand
beim Loslassen) nutzt die richtige Handlage (`_objsicht["los"]`) und ist nicht betroffen.
Der Griff selbst ist stabil und bis auf L/T/U mittig (quer 1-2 mm; L, T, U 7-14 mm, gewollt: das L
wird am langen Zinken gegriffen).

# Nachgeprueft 2026-10-11: die Versatzkette entkraeftet das Negativ nicht

Der Versatz in der Klaue entsteht beim Absenken (Schieben, zu kurzes Reichen), nicht beim Sehen;
das erklaert den Sitz "+12 mm entlang", aendert aber keinen der Gruende dieser Seite. Ein Blick beim
Zufassen saehe unter der Klaue nichts Neues, und der Sitz sagt die Lieferung je Form weiterhin nicht
vorher. Siehe [Klauenlage und Griffversatz](/befunde/klauenlage-und-griffversatz.md).

# Was hier NICHT behauptet wird

Keine Wirkung. Alles ist Codeanalyse; die einzige Messung ist die Zerlegung des Ablagefehlers.

# Verwandt

* [Ablage-Schwelle im Teacher](/befunde/ablage-schwelle-im-teacher.md)
* [Der Tracker rastet auf dem Nachbarn ein](/befunde/ablenker-bindung-gemessen.md) - die Objekt-Aufmerksamkeit und ihr bekannter Fehler
* [act23-Modullandschaft](/mechanismen/act23-modullandschaft.md)
