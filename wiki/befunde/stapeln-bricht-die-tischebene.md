---
type: Befund
title: Ein gestapelter Koerper liest 16 mm daneben - die Homographie ist eine EBENEN-Abbildung
description: Gemessen am echten Wahrnehmungspfad an 49 Stellen des Arbeitsraums. Flach liegend wird ein Wuerfel auf 0,8 mm genau lokalisiert, auf einem zweiten Wuerfel stehend auf 15,9 mm (4,6 bis 25,3 mm), an 12 Prozent der Stellen ueber der Liefertoleranz. Der Versatz zeigt zu 100 Prozent radial von der Kamera weg und korreliert mit r = 1,00 mit dem Kameraabstand - er ist reine Parallaxe, vollstaendig erklaert und kein Rauschen. Nebenbefund: das Groessenband kippt an einem Drittel der Stellen, weil der gestapelte Koerper 11 bis 16 Prozent GROESSER erscheint.
tags: [act23, wahrnehmung, stapeln, kommando]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-17T00:00:00Z }
sources:
  - id: sonde
    resource: "Offline: frischer ShapeClassifierModule, calibrate() aus 40 Punkten, dann perceive_all auf obj_red an 49 Gitterstellen des Arbeitsraums, je z=0,012 (flach) und z=0,036 (gestapelt)"
    title: Hoehenversatz der Tischebenen-Homographie
  - id: anlass
    resource: /fragen/stapeln-als-aufgabe.md
    title: Stapeln als neue Aufgabe (Nutzeridee)
---

# Die Frage

[Stapeln als neue Aufgabe](/fragen/stapeln-als-aufgabe.md) verlangt, dass ein Koerper auf einem
anderen zu liegen kommt. Die gesamte Wahrnehmung von act23 bildet aber ueber eine **Homographie**
ab - und eine Homographie ist eine Abbildung **Ebene auf Ebene**. `calibrate()` setzt obj_red zum
Anlernen auf `z=0,012`, also auf die Wuerfelmitte am Boden; ein gestapelter Wuerfel hat seine Mitte
bei `z=0,036`.

**Wie weit liest der Agent einen gestapelten Koerper daneben?** Das entscheidet, ob die Aufgabe
ueberhaupt beurteilbar ist, denn `SelfEvalModule` haelt einen Koerper ausserhalb der Tischebene
per Bauart fuer **nicht geliefert** - im Docstring steht es woertlich:

> *"A HANGING object (still in the claw, off the table plane) is naturally judged NOT delivered -
> the homography is a TABLE-plane map, so an off-plane blob mis-localises far from the goal."*

Bisher war das ein erwuenschter Nebeneffekt. Beim Stapeln trifft er den **Erfolgsfall**.

# Zahlen

    49 Stellen im Arbeitsraum (7x7 ueber [-0,11 .. 0,11] x [0,07 .. 0,21])

    Lokalisierungsfehler  FLACH   (z=0,012)   Median   0,8 mm    max  1,4 mm
    Lokalisierungsfehler  STAPEL  (z=0,036)   Median  15,9 mm    max 25,5 mm
    Versatz flach -> gestapelt                Median  15,4 mm    4,6 bis 25,3 mm
      davon radial von der Kamera weg         Median  15,4 mm    100 % positiv
    ueber der Liefertoleranz von 25 mm                12 % der Stellen
    Korrelation Versatz ~ Kameraabstand              r = +1,00

    scheinbare Groesse, flach -> gestapelt:   span   x1,114
                                              area   x1,161
                                              dicke  x1,054
    Groessenband kippt                        16 von 49 Stellen (Dickenachse, Vorgabe)
                                              15 von 49 Stellen (Spannenachse)

**Der flache Pfad ist einwandfrei** (0,8 mm) - gemessen wird also nicht ein schlechter Aufbau,
sondern genau der Hoeheneffekt.

# Warum, und warum das wichtig ist

Der Versatz ist **reine Parallaxe**. Die Kamera steht bei `(-0,17, 0,15, 0,32)`; ein Punkt auf
Hoehe `h` wird laengs des Sehstrahls auf die Kalibrierebene `h0` projiziert und wandert dabei um

    d = |p - p_kamera| * (h - h0) / (z_kamera - h)

von der Kamera weg. Mit `h - h0 = 0,024` und `z_kamera - h = 0,284` ist der Faktor 8,5 %, und die
gemessene Spanne 4,6 bis 25,3 mm ist genau die Spanne der Kameraabstaende im Arbeitsraum.

> **`r = +1,00` ist der eigentliche Befund.** Der Fehler ist kein Rauschen, sondern eine exakte
> Funktion einer bekannten Groesse (Kameraabstand) und einer **verborgenen** (Hoehe). Er ist damit
> im Prinzip lernbar - und die Hoehe ist nicht unsichtbar, sie steckt im zweiten Kanal: derselbe
> Koerper erscheint zugleich **11 bis 16 % groesser**. Position und scheinbare Groesse widersprechen
> einander genau dann, wenn der Koerper hoch liegt.

# Die zweite Haelfte: die Groessenachse kippt

An **einem Drittel** der Stellen wechselt das Groessenband allein durch das Hochlegen
(`duenn -> mittel`, `mittel -> dick`; auf der Spannenachse `winzig -> klein`, `klein ->
mittelklein`). Das ist derselbe Fehler wie bei der Farbe, nur eine Achse weiter:

> Eine dauerhafte Adresse darf nur Achsen nennen, die **Eigenschaften des Koerpers** sind
> ([dauer-adresse-vertraegt-keine-farbe](/befunde/dauer-adresse-vertraegt-keine-farbe.md)).
> **Die scheinbare Groesse ist in einer Welt mit Stapeln keine mehr** - sie haengt an der Hoehe,
> und die Hoehe ist Zustand, nicht Identitaet.

Dass der 24-mm-Wuerfel sein Band im Median knapp haelt (span 22,2 gegen die Bandgrenze 22,5 mm),
ist Glueck, kein Entwurf.

# Was daraus folgt

1. **Stapeln ist ohne eine Hoehenvorstellung nicht beurteilbar.** Der Selbstrichter wuerde jeden
   gelungenen Stapel als Fehlschlag verbuchen, und der privilegierte Richter tut es auch:
   `rested = cpos[2] < cmd_half[2] + 0,010` heisst woertlich *"liegt auf dem Tisch"*.
2. **Es ist keine Sackgasse, sondern der Inhalt der Aufgabe.** Die Hoehe ist aus zwei
   widerspruechlichen Kanaelen (Ort und scheinbare Groesse) rekonstruierbar, systematisch und mit
   `r = 1,00` sauber. Wer Stapeln einfuehrt, fuehrt damit die dritte Dimension in eine
   Wahrnehmung ein, die heute flach ist - das ist der eigentliche Gewinn, nicht die Quote.
3. **Eine Abkuerzung ueber eine zweite Homographie waere Geruest.** Man koennte fuer `z=0,036` eine
   zweite Ebene kalibrieren und je nach Aufgabe umschalten. Das rechnet der Designer, nicht der
   Agent, und es zaehlt nach [Projektziel](/ziel.md) nicht als Loesung - hoechstens als
   Teacher-Signal, das zur Testzeit verschwindet.

# Fallen

* **`ebene: pruefstand`.** Gemessen ist der Wahrnehmungspfad in einer gestellten Szene, nicht ein
  act23-Lauf. Ueber Lieferquoten sagt das nichts.
* **Ein Koerper, eine Stapelhoehe.** Nur der 24-mm-Wuerfel auf einem zweiten, also `h = 0,036`.
  Hoehere Stapel wachsen ueberproportional (der Nenner `z_kamera - h` schrumpft mit).
* **Der Schwerpunkt der Silhouette ist nicht der Schwerpunkt des Koerpers.** Gerechnet wird mit
  dem Blob-Schwerpunkt, wie ihn `perceive_all` liefert - genau das, was der Agent sieht. Die
  geschlossene Formel oben ist deshalb eine Naeherung an die Messung, nicht umgekehrt.
* **Die Kamera steht fest.** Eine steilere Kamera (`top`) haette den Effekt fast nicht - dann waere
  aber die gemessene Ueberlegenheit der versetzten Kamera dahin, s. [act15](/chronik/act23.md).

# Verwandt

* [Stapeln als neue Aufgabe](/fragen/stapeln-als-aufgabe.md) - der Entwurf, zu dem dies die erste Messung ist
* [Eine dauerhafte Adresse darf keine Farbe nennen](/befunde/dauer-adresse-vertraegt-keine-farbe.md) - dieselbe Regel, eine Achse frueher
* [Ablage und Platzieren](/befunde/ablage-und-platzieren.md) - warum beim Ablegen bisher nur die seitliche Genauigkeit zaehlte
* [Kredit und Selbst-Urteil](/mechanismen/kredit-und-selbsturteil.md) - der Selbstrichter, der hier zum Problem wird
