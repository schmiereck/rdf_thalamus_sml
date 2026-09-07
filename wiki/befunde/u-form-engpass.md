---
type: Befund
title: Der U-Form-Engpass liegt nicht im Aktionsraum
description: Fuenf unabhaengige Anlaeufe (erzwungener Wrist, erzwungener Griffpunkt, Kombination, offene Suche, Dosislauf) liegen alle auf oder unter der Ausgangslage. Der Greifpunkt im offenen Schlitz ist wahr, aber folgenlos.
tags: [act23, u-form, greifen, negativ]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-08-29T19:55:00Z }
verified: { by: human:thomas, at: 2026-08-29T19:55:00Z }
sources:
  - id: chronik
    resource: /chronik/act23.md
    title: act23-Chronik, U-Eintraege 2026-07-16 bis 2026-07-24
  - id: schlitz
    resource: /raw/index.md
    title: 322 U- und 313 L-Episoden aus vier Laeufen, scratchpad/schlitz.py
---

# Behauptung

Die U-Form liegt seit jeher ~17 Punkte unter den uebrigen Objekten. **Ihr Engpass ist nicht die
Aktionswahl** (Offset, Wrist, Grip, sanft), sondern Mechanik und Anfahrt.

# Fuenf Anlaeufe, alle <= Ausgangslage

    Ausgangslage                     9/20  = 45%
    erzwungener Wrist (relwrist=0)  10/20
    erzwungener Griffpunkt (Basis)   5/20  - schlechter
    Kombination                     11/20
    offene Suche im vollen Aktionsraum, 600 gepinnte Episoden
      (Worker-Merge, 137 frische Etiketten)     11/40 = 27,5%   einseitig p ~ 0,09 fuer SCHLECHTER

Die Wahl blieb dabei unkonditioniert (relwrist im Mittel 39 Grad), die Griffpunkte weiter im
offenen Schlitz.

# Der Greifpunkt im Schlitz - wahr, aber folgenlos

`assets/bracket_arm.xml`, obj_U, Koerperrahmen in mm:

    Zinke links   x [-30,-16]  y [-7,+21]    SCHLITZ: x [-16,+16], y [-7,+21] = 32 x 28 mm
    Zinke rechts  x [+16,+30]  y [-7,+21]
    Basisbalken   x [-30,+30]  y [-21,-7]
    Koerperursprung -> IM SCHLITZ, 7,0 mm bis zum Material
    Flaechen-Schwerpunkt -> IM SCHLITZ, 3,1 mm bis zum Material

Ursache im Code (`shape_classifier.py:599-603`): `select()` gibt als Greifpunkt das **Material
naechst dem Schwerpunkt**; der U-Schwerpunkt liegt in der Konkavitaet. Der Kommentar sagt selbst
"best for thin-bar shapes" - fuer das L getunt.

    obj_U  Greifpunkt IM MATERIAL   98/322 = 30,4%   geliefert 37,8%
           Greifpunkt DANEBEN      224/322 = 69,6%   geliefert 39,3%   Fisher p = 0,81
                                   (Median 3,0 mm daneben)
    obj_L  IM MATERIAL             279/313 = 89,1%   geliefert 54,5%
           DANEBEN                  34/313 = 10,9%   geliefert 41,2%   p = 0,15

Der Agent zielt bei der U wirklich meist in die Luft - nur schluckt die 10 mm dicke Backe die
3 mm. **Beim L-Arm gibt es das Problem gar nicht.**

Ebenfalls widerlegt (alle p > 0,27): Verdrehung waehrend der Handhabung, schiefe Lage in der
Klaue, Ziel Basisbalken gegen Zinke.

# Der einzige echte U-Effekt

    U-Form    11/322  = 3,4% aller Episoden scheitern am FLACH-Kriterium
    uebrige   15/1823 = 0,8%                       Fisher p = 0,00069

Vierfach erhoeht, ueberlebt Bonferroni fuer die acht gefahrenen Tests. Die U kippt beim Ablegen
auf eine Zinke statt flach zu liegen. **Aber: 3,4 von rund 17 Punkten Rueckstand.** Der Rest
bleibt unerklaert.

# Was wirklich geholfen hat: Geometrie und Greifpunkt-Auswahl

* **Schlitz 14 -> 24 -> 32 mm.** Der 16-mm-Finger verkeilte sich im 14-mm-Ausschnitt, der Arm
  konnte ihn nicht abschuetteln.
* **Dichtester-Punkt-Griff** (`ACT23_U_DENSEGRASP`, Vorgabe AN): statt "Material naechst dem
  Schwerpunkt" der Distanztransformations-Maximalpunkt (der Basisbalken). Diagnosebild:
  select()-Griff Materialdicke 1-2 px gegen 8 px am dichtesten Punkt, 16-21 mm auseinander.
  1 px = greift ins Leere. A/B (80 Ep je Arm, ein Seed): 16/80 = 20 % -> 25/80 = 31 %, **+11 Punkte**.

**Kritische Entlarvung dabei:** der ganze Gewinn steckt im Eimer "geliefert TROTZ
'nicht gegriffen'-Etikett" (2 -> 12). Diese Episoden liefern sauber bei ~20 mm mit grosser
U-Drehung. Der Basisgriff traegt das U **flach** ins Ziel, ohne die 20-mm-Hebeschwelle zu
reissen - und die Elif-Kette erreicht den Erfolgszweig nie.
Siehe [Kredit und Selbst-Urteil](/mechanismen/kredit-und-selbsturteil.md).

# Fallen

* **Das Lieferkriterium ist kein reiner Abstandstest** (`pc_act16.py:57` und `:807`):

        rested = cpos[2] < cmd_half[2] + 0.010      # Objekt liegt FLACH auf dem Tisch
        ok = err < 25 mm  UND  rested

  Es gibt Lieferungen bei 25 mm und Misserfolge bei 6 mm. **Jeder Misserfolg unter 25 mm ist ein
  "lag nicht flach"-Fall.** Wer act23-Logs auswertet, darf `Abstand` nicht als Kriterium
  behandeln.
* **Den Greifpunkt der U nicht "reparieren"** - er ist nicht die Ursache, und ein
  Greifpunkt-Sonderfall waere genau die Art geskripteter Regel, die der Nutzer nicht will.
* **Das U-Richter-Band schwankt.** Im 498-Ep-Lauf 12/13 = 92 % korrekt, im 746-Ep-Lauf 7/13 = 54 %
  (gepoolt 19/26 = 73 %, schlechter als Wuerfel bei 95-100 %). Die gelockerte U-Bar produzierte
  dort 6 Falsch-Positive - die vergiftende Richtung. Da Us Engpass ohnehin nicht die Aktionswahl
  ist, haben Extra-U-Etiketten wenig Wert.

# Wo anzusetzen waere

Beim **Ablegen** (kippt auf eine Zinke) und bei der **Anfahrt-Trajektorie**, nicht beim Greifen
und nicht bei der Ausrichtung. Die Klaue ueber dem Schlitz erwischt zu ~45 % zufaellig eine
Zinke; zuverlaessig zu machen braucht etwas ausserhalb der heutigen Aktions-Parametrisierung.

# Verwandt

* [Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md)
* [Nagelneigung](/befunde/nagelneigung.md)
