---
type: Befund
title: Nachbarnaehe kostet 14 Punkte - in 16 Prozent der Episoden
description: Ueber 1868 Episoden: steht der naechste Nachbar naeher als 55 mm, faellt die Lieferquote von 54,9 auf 41,1 Prozent (p < 0,0001), und alle sieben Objekte zeigen dieselbe Richtung. Das betrifft 15,6 Prozent der Episoden und erklaert rund 2,2 Punkte der Gesamtquote. Die Schwelle liegt bei 55 mm, nicht bei den 35 mm, ab denen der Split die Position rettet.
tags: [act23, wahrnehmung, verschmelzung, langlauf]
status: stable
evidenz: gemessen
ebene: langlauf
generated: { by: claude/opus-5, at: 2026-09-09T22:00:00Z }
sources:
  - id: laeufe
    resource: "log/pc_act23_2026-09-05_22-06-51_5152.txt (932 Ep) plus alle Laeufe vom 06.-09.09.; 1868 Episoden mit Lagen und Kommando"
    title: Auszaehlung ueber die Laufprotokolle
  - id: kurve
    resource: /befunde/verschmelzung-abstandskurve.md
    title: Die Pruefstandskurve, deren zweite Haelfte hier beantwortet wird
---

# Behauptung

Die zweite Haelfte der Verschmelzungsfrage - *wie oft kommt das im Lauf vor?* - ist beantwortet,
und sie faellt groesser aus als die erste vermuten liess:

* **Der kritische Bereich unter 35 mm ist selten: 2,1 % der Episoden.**
* **Der Bereich, in dem es messbar wehtut, ist viel breiter: unter 55 mm sind es 15,6 %** - und
  dort faellt die Lieferquote von 54,9 % auf 41,1 %, also um **13,9 Punkte** (p < 0,0001).
* Hochgerechnet erklaert das rund **2,2 Punkte** der Gesamtquote.

# Zahlen

1868 Episoden aus den Protokollen; je Episode der Abstand des **kommandierten** Koerpers zu
seinem naechsten nicht geparkten Nachbarn.[^laeufe]

    Abstand [mm]   Episoden   Anteil   Lieferquote
          0 - 25         13     0,7 %    5/13   = 38,5 %
         25 - 35         27     1,4 %   10/27   = 37,0 %
         35 - 45         79     4,2 %   33/79   = 41,8 %
         45 - 55        173     9,3 %   72/173  = 41,6 %
         55 - 65        177     9,5 %   97/177  = 54,8 %
         65 - 75        202    10,8 %  115/202  = 56,9 %
            > 75       1197    64,1 %  654/1197 = 54,6 %

    Median Nachbarabstand 89 mm; 10. Perzentil 49 mm, 25. Perzentil 65 mm

Wo liegt die Schwelle im **Ausgang**?

    Schnitt    Episoden darunter   Quote darunter   Quote darueber   Diff     p
     < 35 mm      40 =  2,1 %          37,5 %           53,1 %      -15,6   0,0553
     < 45 mm     119 =  6,4 %          40,3 %           53,6 %      -13,3   0,0058
     < 55 mm     292 = 15,6 %          41,1 %           54,9 %      -13,9   0,0000
     < 65 mm     469 = 25,1 %          46,3 %           55,0 %       -8,7   0,0011
     < 75 mm     671 = 35,9 %          49,5 %           54,6 %       -5,2   0,0336

Der schaerfste Schnitt liegt bei **55 mm**. Darunter bricht die Quote ein, darueber ist sie flach
(54,8 / 56,9 / 54,6 % in den drei oberen Baendern).

# Die Kontrolle: es liegt nicht am Objektmix

Enge Szenen koennten einfach haeufiger die schwierigen Koerper treffen. Tun sie nicht - **alle
sieben Objekte zeigen dieselbe Richtung**:

    Objekt      < 55 mm   Quote  |  >= 55 mm   Quote
    obj_L            38   44,7 % |       217   50,2 %
    obj_T            48   35,4 % |       278   54,3 %
    obj_U            48   35,4 % |       259   45,6 %
    obj_X            54   42,6 % |       271   66,1 %
    obj_blue         48   50,0 % |       228   68,9 %
    obj_green        34   41,2 % |       170   46,5 %
    obj_red          22   36,4 % |       153   47,7 %

Vorzeichentest 7 von 7 gleichgerichtet: **p = 0,0156**.

# Bewertung

**Die Schwelle im Ausgang (55 mm) liegt weiter draussen als die, ab der der Split die Position
rettet (35 mm) - und passt zu der, ab der er die FORMKLASSE rettet (65 mm).** Das ist der
interessanteste Teil: die
[Abstandskurve](/befunde/verschmelzung-abstandskurve.md) hat gezeigt, dass Position und Identitaet
zwei verschiedene Rettungen sind. Die Lieferquote folgt der **Identitaet**, nicht der Position.
Anders gesagt: zu wissen *wo* etwas ist, genuegt nicht, wenn unklar bleibt, *was* es ist.

**Das ist eine Beobachtung, kein Eingriff.** Enger Nachbar und schlechter Ausgang treten
gemeinsam auf; welcher Anteil davon auf die **Verschmelzung** entfaellt, ist damit **nicht**
entschieden. Mindestens drei Mechanismen kommen in Frage und sind hier nicht getrennt:

1. Verschmelzung in der Wahrnehmung (der hier untersuchte),
2. die Klaue rammt beim Anfahren oder Tragen den Nachbarn,
3. der Greifpunkt selbst ist in Nachbarschaft schlechter waehlbar.

Die 2,2 Punkte sind daher eine **Obergrenze** dessen, was eine perfekte Verschmelzungs-Loesung
einbringen koennte - nicht ihr erwarteter Ertrag.

# Fallen

* **Protokollierte Split-Rettungen sind kein Mass fuer die Verschmelzungshaeufigkeit.** In den
  1868 Episoden steht genau **eine** `[Farb-Split]`/`[Form-Split]`-Zeile. Der Grund: der Tracker
  ruft den Split je Bild auf und zaehlt ihn nur in `vc._fsv`, gedruckt wird er allein aus
  `perceive()`. Wer die Haeufigkeit an den Logzeilen abliest, unterschaetzt sie um Groessenordnungen.
* **Das Nachbar-Merkmal im Weltmodell taugt dafuer nicht** - es steht nur auf 6 % der Pufferzeilen
  ([Merkmale kommen zu spaet](/befunde/merkmale-kommen-zu-spaet.md)). Die Auszaehlung hier geht
  ueber die `[dbg] before`-Zeilen der Protokolle und ist damit vollstaendig.

# Folgen

Damit ist der Faden aus [offene Faeden](/fragen/offene-faeden-act23.md) in beiden Haelften
beantwortet: **ab wann** (Split traegt ab 35 mm, Formklasse erst ab 65 mm) und **wie oft**
(15,6 % der Episoden unter 55 mm, 2,1 % unter 35 mm).

Der naechstliegende Hebel folgt aus der Kombination: nicht die Position, sondern die
**Formklassen-Rettung** ist der schwache Teil. Sie ist der Grund, warum die Wirkung bis 55 mm
reicht, obwohl die Position ab 35 mm sicher zurueckkommt. Ungemessen bleibt, ob sich der
Form-Split verbessern laesst.

# Verwandt

* [Verschmelzung: die Abstandskurve](/befunde/verschmelzung-abstandskurve.md) - die erste Haelfte der Frage
* [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md)
* [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) - dessen Formachse hiervon betroffen ist
