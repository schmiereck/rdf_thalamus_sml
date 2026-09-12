---
type: Befund
title: Der Form-Rueckhalte-Test - verallgemeinert wird ueber die Proportion, nicht ueber die Groesse
description: Eine nie gesehene Form faellt in 36 Prozent der Faelle in die richtige Kategorie, in 54 Prozent gilt sie als neuartig. Die Aufschluesselung zeigt eine scharfe Asymmetrie: laengliche Formen werden zu 69 Prozent richtig einsortiert, quadratische zu 3 Prozent. Die Kontrolle ueber die Groesse erklaert es - ab dem 1,3-fachen des bekannten Masses bricht die Erkennung, unabhaengig von der Form.
tags: [act23, wahrnehmung, formklassen, generalisierung]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-12T14:00:00Z }
sources:
  - id: probe
    resource: "src/pc_cvnn/act23_form_rueckhalt.py, 8 Proportionen x 12 Lagen auf einer Kopie von act23_state.pkl (ad9d768c); Kontrolle: 10 Groessen x 12 Lagen"
    title: Form-Rueckhalte-Test und Groessen-Kontrolle
---

# Warum dieser Test

Aus [Geburtenrate und Saettigung](/befunde/geburtenrate-und-saettigung.md): "mehr Geburten" ist
kein gutes Ziel, weil eine Geburt "das kenne ich nicht" bedeutet. Die Frage, die
[das Projektziel](/ziel.md) trifft, ist die nach **Verallgemeinerung**:

> Stellt man eine nie gesehene Form hin - faellt sie in die passende bestehende Kategorie
> (**richtig**), gebiert sie eine neue (**neu** = uebersegmentiert), oder landet sie in der
> falschen (**falsch** = verwechselt)?

Die Sollkategorie wird **vor** der Messung aus der Geometrie festgelegt (Verhaeltnis >= 2,5 ->
"lang", < 1,4 -> "viereckig", dazwischen kein Soll), und die Zuordnung Kategorie -> Klassenname
wird **empirisch** bestimmt, nicht verdrahtet: die bekannten Koerper werden gezeigt und gefragt,
wie die Wahrnehmung sie nennt.

    Kategorie 'lang'      = neu-9, neu-285      (obj_T, obj_X)
    Kategorie 'viereckig' = cube                (obj_red, obj_green, obj_blue)

Nichts wird gelernt, nichts gespeichert - der Zustand ist vorher wie nachher `ad9d768c`.

# Zahlen

    Halbmasse [mm]   Verh.      Soll | richtig  neu  falsch | genannt
    34 x  4          8,5:1      lang |    5      7     0    | neu-9 5, None 7
    30 x  6          5,0:1      lang |    9      3     0    | neu-9 9, None 3
    26 x  9          2,9:1      lang |   11      1     0    | neu-9 11, None 1
    22 x  9          2,4:1        -- |   --     --    --    | neu-9 10, None 2
    18 x 11          1,6:1        -- |   --     --    --    | neu-9 3, L 3, None 6
    16 x 13          1,2:1 viereckig |    1      6     5    | None 6, cube 1, L 5
    20 x 18          1,1:1 viereckig |    0     11     1    | None 11, neu-285 1
    26 x 24          1,1:1 viereckig |    0     11     1    | None 11, neu-34 1

    BILANZ (n = 72)   richtig 26 = 36,1 %   neu 39 = 54,2 %   falsch 7 = 9,7 %

    Aufgeschluesselt
      Kategorie "lang"        25/36 = 69,4 % richtig,  0 falsch
      Kategorie "viereckig"    1/36 =  2,8 % richtig,  7 falsch

# Die Kontrolle erklaert die Asymmetrie: es ist die GROESSE

Quadrate bei konstantem Seitenverhaeltnis, nur die Groesse variiert:

    Halbmass   relativ zum Wuerfel   genannt
      12 mm         1,00x            cube 8, L 4
      14 mm         1,17x            L 8, cube 2, None 2
      16 mm         1,33x            None 10, L 2
      18 mm         1,50x            None 8, L 3, neu-285 1
      20 mm         1,67x            None 12
      24 mm         2,00x            None 12 (3x neu-34)

Lange Balken bei konstantem Verhaeltnis 3:1:

    Halbmass   relativ zu obj_T      genannt
      15 mm         0,71x            cube 7, neu-9 4, None 1
      21 mm         1,00x            neu-9 12       <- das bekannte Mass
      27 mm         1,29x            neu-9 8, None 4
      33 mm         1,57x            None 12

**Beide Kategorien brechen bei rund dem 1,3-fachen des bekannten Masses**, und zwar unabhaengig
von der Form. Die "viereckig"-Kategorie schneidet im Rueckhalte-Test nur deshalb so viel
schlechter ab, weil der Wuerfel mit 12 mm der **kleinste** Koerper ist - jede quadratische Probe
lag schon jenseits seiner Reichweite. Der Balken hat mit 21 mm mehr Luft nach unten und oben.

Der Deskriptor verallgemeinert also **ueber die Proportion** (2,9:1 bis 8,5:1 werden alle als
derselbe Balken erkannt - genau die Grobkategorie aus der Nutzerfrage), aber **nicht ueber die
Groesse**.

Das bestaetigt [Formfaktorisierung](/befunde/formfaktorisierung.md) - dort gemessen: die Groesse
dominiert die Form (11,52 gegen 6,07), und vier Versuche, die Form groessenfrei zu normieren,
sind gescheitert. Neu ist hier, **wo die Grenze liegt (Faktor ~1,3) und was sie kostet**: die
Haelfte aller Verallgemeinerungsfaelle.

# Bewertung

* **Die gute Nachricht ist die Proportions-Invarianz.** Ein 34x4-Balken und ein 26x9-Balken
  landen beide bei `neu-9`, obwohl das Verhaeltnis um den Faktor 3 auseinanderliegt. Das ist
  genau das, was der Nutzer beschrieben hat - "die eher langen" als eine Kategorie.
* **Der Engpass ist die Groessen-Invarianz, und sie fehlt vollstaendig.** Jenseits von
  Faktor 1,3 ist alles "neuartig". Die 54 % Uebersegmentierung im Rueckhalte-Test sind fast
  ausschliesslich das.
* **Verwechslungen sind selten (9,7 %) und konzentriert.** Fuenf der sieben entfallen auf eine
  einzige Probe (16x13), die als `L` gelesen wird. In der "lang"-Kategorie gibt es **null**
  Verwechslungen.
* **Die Metrik taugt.** Sie trennt die drei Ausgaenge sauber, braucht keinen Lauf, veraendert
  keinen Zustand und ist in Minuten wiederholbar - damit ist sie als Fortschrittsmass fuer die
  Aneignungslinie brauchbar, anders als die Geburtenzahl.

# Fallen

* **Der Wuerfel ist der kleinste Koerper.** Dadurch ist die "viereckig"-Kategorie systematisch
  benachteiligt; die 2,8 % sind kein Aussage ueber Quadrate, sondern ueber Groessen jenseits des
  Bekannten. Wer den Test wiederholt, sollte auch **kleinere** Proben fahren.
* **`obj_T` als Probe-Koerper ist selbst eine bekannte Form** (`neu-9`). "Nie gesehen" gilt fuer
  die PROPORTION, nicht fuer den Koerper. Eine topologisch neue Form (Ring, Dreieck) ist damit
  nicht geprueft.
* **Bei 1,6:1 zerfaellt alles** (neu-9 3, L 3, None 6). Die Grenzzone zwischen den Kategorien ist
  breit und unentschieden - deshalb ist sie ohne Sollvorgabe gefahren und nicht in die Bilanz
  eingegangen.

# Was daraus folgt

Der naechste Hebel ist damit benannt und **nicht** die Geburtenrate: **Groessen-Invarianz des
Formdeskriptors**. Vier Anlaeufe dazu sind laut
[Formfaktorisierung](/befunde/formfaktorisierung.md) bereits gescheitert - dieser Befund sagt
aber erstmals, **wie viel** daran haengt (die Haelfte der Verallgemeinerungsfaelle) und liefert
eine billige Metrik, um einen fuenften Anlauf zu bewerten.

# Verwandt

* [Geburtenrate und Saettigung](/befunde/geburtenrate-und-saettigung.md) - warum diese Metrik
* [Formfaktorisierung](/befunde/formfaktorisierung.md) - die Groesse dominiert die Form
* [Farb-Rueckhalte-Test](/befunde/farbe-form-rueckhalt.md) - dieselbe Bauart fuer die Farbachse
* [Projektziel](/ziel.md)
