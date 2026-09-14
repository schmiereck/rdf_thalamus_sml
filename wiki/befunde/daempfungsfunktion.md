---
type: Befund
title: Die Daempfungsfunktion haengt nicht am Betrag der Verschiebung, sondern am Nachbarabstand - und sie ist die Verschmelzungsschwelle
description: VERSCHIEBUNG: frei stehend ist die Aequivarianz praktisch exakt: 0,33 mm Restfehler bei 40 mm Verschiebung, p90 unter 0,8 mm. In Nachbarnaehe bricht nicht der Median, sondern der Schwanz - p90 bis 17 mm, und zwar ab dem Punkt, an dem die Verschiebung den Koerper in Verschmelzungsnaehe traegt. Die brauchbare Regel lautet delta < Nachbarabstand minus 40 mm. Dazu zwei Nebenbefunde: die Formeinbettung hat einen Rauschboden von 13 Prozent der Klassentrennung, und das Ziel-Latent ist NICHT exakt linear, sondern auf 12 bis 14 Prozent genau. DREHUNG: nur yaw4 traegt sie, und zwar mit UMGEKEHRTEM Vorzeichen; yaw ist unbrauchbar, der Schwerpunkt wandert bis 2,5 mm, und der drehinvariante Deskriptor driftet doppelt so stark wie bei einer Verschiebung.
tags: [act23, latent, augmentierung, wahrnehmung]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-14T00:00:00Z }
sources:
  - id: sonde
    resource: "src/pc_cvnn/act23_daempfung.py -- 80 Szenen aus den Laufprotokollen, 6 Verschiebungen x 3 Richtungen je Koerper, rund 2400 gepruefte Verschiebungen, Zustand ad9d768c"
    title: Daempfungsmessung auf echten Laufszenen
  - id: dreh
    resource: "dieselbe Sonde im Modus DF_MODUS=dreh -- 50 Szenen, Winkel 5 bis 45 Grad, rund 180 Drehungen je Winkel"
    title: Drehmessung
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
* **Die Drehung ist teurer** und braucht eigene Regeln - s. den Abschnitt unten.

# Die Drehung: nur ein Kanal traegt sie, und er laeuft rueckwaerts

Vorhergesagt waere bei einer Drehung um theta: Lage unveraendert, Form unveraendert (der
Deskriptor ist mit `np.abs(F)` drehinvariant gebaut), `yaw` um theta weiter (mod 180 Grad),
`yaw4` um theta (mod 90 Grad).

    20 Grad Drehung, je ~30 Faelle       Lagedrift   Formdrift    yaw-Rest   yaw4-Rest
      obj_L                                2,51 mm    35 % Tr.     8,9 Grad    5,2 Grad
      obj_T                                1,80 mm    30 %        14,1        6,7
      obj_U                                1,52 mm    34 %         7,8        1,9
      obj_blue  (Wuerfel)                  0,36 mm    22 %        18,0        1,9
      obj_green (Wuerfel)                  0,25 mm    24 %        18,5        4,2
      obj_red   (Wuerfel)                  0,33 mm    21 %        18,5        2,4

**Das Vorzeichen ist umgekehrt.** Die Vorzeichenprobe ueber alle Koerper:

    theta      yaw4 mit +theta   yaw4 mit -theta
      5 Grad      10,0 Grad          1,9 Grad
     10           19,2              2,3
     20           38,1              3,3
     45            5,1              5,1     (bei 45 Grad fallen beide zusammen, mod 90)

Mit `+theta` ist der Rest genau `2*theta` - der Kanal laeuft der Koerperdrehung also **entgegen**
(eine Spiegelung im Kamera-/Homographie-Pfad). **Wer das Vorzeichen raet, faelscht jede
vorgestellte Drehung um den doppelten Winkel.** Mit `-theta` traegt `yaw4` sauber: 2 bis 5 Grad
Rest ueber alle Koerper, auch die laenglichen.

**`yaw` (k=2) ist nicht brauchbar.** Auf den drei Wuerfeln ist der Rest gleich theta - die
k=2-Phase ist auf einem Quadrat entartet, wie es die
[Formfaktorisierung](/befunde/formfaktorisierung.md) beschreibt. Auf den laenglichen Koerpern ist
er mit 8 bis 14 Grad bei 20 Grad Drehung immer noch die Haelfte des Winkels.

Zwei weitere Vorhersagen fallen:

* **Die Lage ist NICHT invariant.** Bei den asymmetrischen Koerpern wandert der wahrgenommene
  Schwerpunkt um bis zu 2,5 mm (obj_L bei 20 Grad), bei den Wuerfeln um 0,3 mm. Eine vorgestellte
  Drehung muss den Greifbezug mitdrehen, nicht nur den Winkel setzen.
* **Der "drehinvariante" Deskriptor ist es nicht.** 21 bis 35 % der Klassentrennung bei 20 Grad,
  gegen einen Rauschboden von 13 bis 16 %. Die Invarianz gilt fuer die Konstruktion, nicht fuer
  die gerenderte Ansicht aus der schraegen Kamera.

> **Verschiebung und Drehung sind wirklich nicht symmetrisch zu behandeln - aber anders, als die
> Idee-Seite vermutete.** Dort war der Grund, dass der Deskriptor die Phase wegwirft. Gemessen ist
> der Grund, dass die Drehung **teurer** ist: sie bewegt den Schwerpunkt, sie treibt den
> Formdeskriptor doppelt so weit wie eine vergleichbare Verschiebung, und nur einer ihrer beiden
> Winkelkanaele traegt sie ueberhaupt.

**Fuer den Bau:** Drehungen nur ueber `yaw4` und mit umgekehrtem Vorzeichen; `yaw` aus der
Vorstellung herauslassen; den Greifbezug mitdrehen; und den Winkelbereich klein halten - bei
20 Grad ist die Formdrift schon so gross wie bei 40 mm Verschiebung.

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
* [Formfaktorisierung](/befunde/formfaktorisierung.md) - die Entartung der k=2-Phase auf dem Wuerfel
* [Exekutionsvarianz](/befunde/exekutionsvarianz.md) - warum ein Erfolg uebertragbar ist und ein Fehlschlag nicht
