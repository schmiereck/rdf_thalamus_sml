---
type: Befund
title: Die Daempfungsfunktion haengt nicht am Betrag der Verschiebung, sondern am Nachbarabstand - und sie ist die Verschmelzungsschwelle
description: Frei stehend ist die Aequivarianz praktisch exakt: 0,33 mm Restfehler bei 40 mm Verschiebung, p90 unter 0,8 mm. In Nachbarnaehe bricht nicht der Median, sondern der Schwanz - p90 bis 17 mm, und zwar ab dem Punkt, an dem die Verschiebung den Koerper in Verschmelzungsnaehe traegt. Die brauchbare Regel lautet delta < Nachbarabstand minus 40 mm. Dazu zwei Nebenbefunde: die Formeinbettung hat einen Rauschboden von 13 Prozent der Klassentrennung, und das Ziel-Latent ist NICHT exakt linear, sondern auf 12 bis 14 Prozent genau.
tags: [act23, latent, augmentierung, wahrnehmung]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-14T00:00:00Z }
sources:
  - id: sonde
    resource: "src/pc_cvnn/act23_daempfung.py -- 80 Szenen aus den Laufprotokollen, 6 Verschiebungen x 3 Richtungen je Koerper, rund 2400 gepruefte Verschiebungen, Zustand ad9d768c"
    title: Daempfungsmessung auf echten Laufszenen
  - id: idee
    resource: /fragen/latente-augmentierung.md
    title: Die Nutzeridee, deren Voraussetzung hier gemessen wird
---

# Der Auftrag

[Latente Augmentierung](/fragen/latente-augmentierung.md) verlangt ausdruecklich, die Voraussetzung
zu MESSEN statt anzunehmen: *"Szene rendern -> Latent, Objekt um delta verschieben -> rendern ->
Latent, gegen die Vorhersage halten. Das Ergebnis IST die Daempfungsfunktion."* Und sie nennt den
Einwand, an dem alles haengt: **die Daempfung muss vom KONTEXT abhaengen, nicht nur vom Betrag.**

Gemessen wird, wie gut die Vorstellung die Wirklichkeit trifft: Lage soll sich um `delta`
verschieben, Formeinbettung und Winkelphasen sollen **unveraendert** bleiben.

# Zahlen

    delta   Nachbar     n     Lagerest Median (p90)    Formdrift    Winkeldrift  verloren
       2   > 90 mm   312     0,12 mm  (0,31)          13 % Tr.        0,148         0
      10   > 90 mm   314     0,16 mm  (0,39)          14 % Tr.        0,158         0
      40   > 90 mm   330     0,33 mm  (0,76)          23 % Tr.        0,219         4

       2  60-90 mm    78     0,16 mm  (0,35)          15 % Tr.        0,167         0
      20  60-90 mm    80     0,22 mm  (0,50)          19 % Tr.        0,223         5
      30  60-90 mm    86     0,31 mm (10,68)          22 % Tr.        0,304         4
      40  60-90 mm    80     0,32 mm (11,47)          25 % Tr.        0,347         6

       2   < 60 mm    91     0,18 mm  (1,09)          16 % Tr.        0,142         2
      10   < 60 mm    87     0,23 mm (13,04)          20 % Tr.        0,325         4
      40   < 60 mm    75     0,52 mm (17,07)          27 % Tr.        0,467         5

    "Tr." = Anteil am Median-Abstand zwischen VERSCHIEDENEN Koerpern (1,88) -- eine Drift von
    100 % waere ein ganzer Koerperwechsel.

# Der Betrag ist die falsche Achse

**Frei stehend traegt die Aequivarianz praktisch unbegrenzt**: 0,33 mm Restfehler bei 40 mm
Verschiebung, also **unter einem Prozent von delta**, mit einem p90 von 0,76 mm. Eine Daempfung
nach dem Betrag - die Intuition hinter *"mit abnehmender Intensitaet"* - waere hier fast
ueberfluessig.

**In Nachbarnaehe bricht nicht der Median, sondern der Schwanz.** Der Median bleibt selbst bei
40 mm und engem Nachbarn bei 0,52 mm; der p90 springt auf 17 mm. Es gibt also keine sanfte
Verschlechterung, sondern eine Minderheit vollstaendig falscher Vorstellungen inmitten korrekter.

> **Der Einwand der Seite ist bestaetigt und zugleich verschaerft:** es ist nicht so, dass die
> Daempfung *auch* vom Kontext abhaengen muss - **der Kontext ist die einzige Achse, die zaehlt.**

# Und die Schwelle ist bekannt

Wo genau bricht es? Ablesbar an der Zeile, in der der p90 aus dem Rahmen faellt:

    Nachbar > 90 mm   bis 40 mm getestet, bricht NICHT
    Nachbar 60-90 mm  bis 20 mm sauber (p90 0,50), bricht bei 30 mm
    Nachbar < 60 mm   bis  5 mm sauber (p90 2,54), bricht bei 10 mm

Das ist kein neuer Grenzwert, sondern ein alter: eine Verschiebung traegt genau so lange, wie sie
den Koerper **nicht in Verschmelzungsnaehe** bringt. Die
[Verschmelzungs-Abstandskurve](/befunde/verschmelzung-abstandskurve.md) setzt die Verschmelzung bei
rund 40 mm an, und die Sonde verwirft ohnehin alles unter 25 mm als physisch unmoeglich - uebrig
bleibt genau das Band dazwischen.

    Brauchbare Regel:   delta  <  Nachbarabstand - 40 mm

**Die Daempfungsfunktion ist die Verschmelzungsschwelle, in delta ausgedrueckt.** Damit ist sie
keine frei zu waehlende Gewichtung mehr, sondern eine harte Zulaessigkeitsbedingung - und sie ist
je Stichprobe aus der Szene selbst berechenbar, ohne Modell und ohne Schaetzung.

# Zwei Nebenbefunde, die den Bau betreffen

**Die Formeinbettung hat einen Rauschboden.** Schon bei 2 mm Verschiebung driftet `desc_embed` um
**13 bis 16 %** der Klassentrennung - und steigt bis 40 mm nur auf 23 bis 27 %. Die Drift waechst
also kaum mit delta, sie ist von Anfang an da. Eine vorgestellte Variante traegt bei 2 mm fast
denselben Formfehler wie bei 20 mm. Fuer den Bau heisst das: **die Formkanaele unveraendert zu
uebernehmen ist so genau, wie der Deskriptor ueberhaupt ist** - und das ist auf 13 % genau, nicht
exakt.

**Das Ziel-Latent ist NICHT exakt linear.**

    delta  2 mm  ->  0,24 mm Rueckrechnungsfehler = 12 % von delta
    delta 20 mm  ->  2,40 mm                      = 12 %
    delta 40 mm  ->  5,46 mm                      = 14 %

Ein konstanter Relativfehler von rund 13 %. **Das korrigiert die Idee-Seite**, die sagt: *"Eine
Verschiebung ist im Latent EXAKT eine Phasendrehung, per Konstruktion"*. Das gilt fuer den
RoPE-Code selbst - aber `encode_world` ist eine **Gitter-Interpolation** ueber das trainierte
Zielmodul, und die lineare Rueckrechnung ueber `D` traegt diesen Fehler. Bei 5 mm sind das 0,6 mm
und belanglos; bei 40 mm sind es 5,5 mm und damit mehr als die Greiftoleranz.

# Was daraus fuer den Bau folgt

Ungebaut und ungemessen, aber jetzt beziffert statt geraten:

* **Verschiebung**: zulaessig bis `Nachbarabstand - 40 mm`, gedeckelt bei etwa 20 mm. Dort liegt
  der Lagerest unter 0,5 mm, die Formdrift bei ~19 % und der Ziel-Latent-Fehler bei 2,4 mm.
* **Keine Daempfung nach Betrag noetig** innerhalb dieser Schranke - ein Gewicht, das mit |delta|
  faellt, wuerde das Falsche daempfen.
* **Die Drehung ist NICHT mitgemessen.** Der Formdeskriptor ist drehinvariant (`np.abs(F)` wirft
  die Phase weg), die Winkelkanaele sind es nicht - das bleibt eine eigene Messung.

# Fallen

* **`ebene: pruefstand`.** Gemessen ist die WAHRNEHMUNG einer verschobenen Szene, nicht der Ausgang
  eines Griffs. Ob ein Griff an der vorgestellten Lage geglueckt WAERE, sagt das nicht - und genau
  das ist die Behauptung, auf der die Augmentierung beruht.
* **2604 Verschiebungen wurden verworfen** (unmoeglich oder ausserhalb des Arbeitsraums). Die
  Zulaessigkeitsregel oben gilt also fuer das, was uebrig bleibt.
* **Der Yaw wird je Szene neu gewuerfelt**, innerhalb einer Szene aber festgehalten - sonst waere
  der Vergleich vorher/nachher wertlos.
* **"verloren"** sind Faelle, in denen die verschobene Szene gar keine brauchbare Detektion mehr
  liefert; sie sind selten (0-6 je Zelle) und gehen nicht in die Mediane ein.

# Verwandt

* [Latente Augmentierung](/fragen/latente-augmentierung.md) - die Idee, deren Voraussetzung hier gemessen ist
* [Verschmelzungs-Abstandskurve](/befunde/verschmelzung-abstandskurve.md) - die Schwelle, die hier wieder auftaucht
* [Die Wiedervorlage](/mechanismen/wiedervorlage.md) - die Szenenquelle
* [Exekutionsvarianz](/befunde/exekutionsvarianz.md) - warum ein Erfolg uebertragbar ist und ein Fehlschlag nicht
