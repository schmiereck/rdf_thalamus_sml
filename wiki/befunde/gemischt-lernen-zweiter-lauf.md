---
type: Befund
title: Die Policy legt auf jeder Sockelhoehe richtig ab - aber sie hat die Hoehe nicht als Funktion gelernt
description: 200 Episoden gemischt, Szenenwechsel alle zwei Episoden, damit rund 100 Kombinationen aus Sockelort und -hoehe. Die Verwechslung mit dem Zielort ist gebrochen (Korrelation 0,00 statt 0,54). In ihrer eigenen Verteilung trifft die Policy nach 200 Episoden alle drei Sockelhoehen auf 0 bis 4 mm - so genau wie auf dem Tisch - und verbessert sich dabei stetig. Die kontrafaktische Probe zeigt aber weiter eine Steigung von rund 2 bei R2 unter 0,32: an Orten, an denen nie ein Sockel stand, ueberschiesst sie. Gelernt ist eine verlaessliche Ablage, keine uebertragbare Funktion.
tags: [act23, stapeln, policy, curriculum, selbstlernen]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-20T00:00:00Z }
sources:
  - id: lauf
    resource: "Ein kopfloser Lauf auf einer Kopie von act23_state.pkl (ad9d768c), 4 x 50 Episoden (Seeds 5242-5245), ACT23_ZIEL_MISCH=0.5 ACT23_SOCKEL_WANDERT=1 ACT23_SOCKEL_HOEHEN=6,10,14 ACT23_SCENE_N=3 ACT23_SCENE_EVERY=2, Teacher fahrend"
    title: Zweiter gemischter Lernlauf
  - id: vorher
    resource: /befunde/gemischt-lernen-erster-lauf.md
    title: Der erste gemischte Lauf - dort waren es nur 10 Szenen
---

# Was geaendert wurde

Im [ersten gemischten Lauf](/befunde/gemischt-lernen-erster-lauf.md) wanderte der Sockel zwar, aber
eine Szene hielt zehn Episoden - **zehn Kombinationen aus Ort und Hoehe**, und die Ablagehoehe blieb
zu mehr als der Haelfte mit dem Zielort korreliert. Jetzt Szenenwechsel alle zwei Episoden:
**100 Kombinationen** in 200 Episoden, sonst unveraendert.

# Die Verwechslung ist gebrochen

    Korrelation der Hoehenspalte mit dem Zielort
      fester Sockel   (erster Lernlauf)   Zielortstreuung  +- 6,5 / +- 8,7 mm
      10 Szenen       (erster gemischt)   r = -0,54 (x),  +0,65 (y)
      100 Szenen      (dieser Lauf)       r = +0,00 (x),  -0,06 (y),  Streuung +- 47 / +- 25 mm

Damit ist die Frage ueberhaupt erst stellbar: die Hoehe steht jetzt unabhaengig vom Ort in den
Daten.

# Die Policy legt auf jeder Hoehe richtig ab

    Stapel-Absenkzeilen, Netz gegen Etikett (mm), je Sockelhoehe

    Stand |   6 mm      10 mm      14 mm   | Tischablage (aktuelle Zeilen)
    ck000 |     -          -          -    |  4,7 mm
    ck050 |  29 / 24   34 / 28   41 / 32   |  9,7 mm
    ck100 |  26 / 24   30 / 28   40 / 32   |  6,7 mm
    ck150 |  28 / 24   29 / 28   43 / 32   |  9,2 mm
    ck200 |  24 / 24   32 / 28   34 / 32   |  6,2 mm

**Der Fehler faellt stetig: +5/+6/+9 mm nach 50 Episoden, +0/+4/+2 mm nach 200.** Nach 200 Episoden
legt die Policy auf dem Sockel so genau ab wie auf dem Tisch (dort +5,4 mm Median). Und sie tut das
fuer **drei verschiedene Hoehen**, nicht fuer eine gelernte Konstante.

    Stapel im Lauf: 65 gelungen, 10 daneben (200 Episoden, davon ~98 Stapelauftraege)

# Aber eine uebertragbare Funktion ist es nicht

    kontrafaktisch: Tisch-Absenkzustaende, nur die Hoehenspalte auf 6 / 10 / 14 mm gesetzt

    Stand |  dZ bei 6 / 10 / 14 mm  | Steigung |  R2
    ck050 |  +10,2  +19,0  +27,7    |   1,46   | 0,24
    ck100 |  +15,2  +25,1  +32,8    |   2,03   | 0,29
    ck150 |  +22,2  +34,1  +48,1    |   2,58   | 0,32
    ck200 |  +15,8  +24,5  +33,9    |   1,98   | 0,15

    Soll: dZ = h, also Steigung 1

Die Antwort steigt in jedem Zwischenstand monoton mit der Hoehe - die Spalte ist also eine
**Groesse** und kein Schalter. Aber die Steigung liegt bei rund **2 statt 1**, und R2 bleibt unter
0,32: an Zustaenden, an denen nie ein Sockel stand, ueberschiesst die Policy, und die Streuung ueber
die Zustaende ist groesser als der Effekt der Hoehe selbst.

> **Gelernt ist eine verlaessliche Ablage auf dem Sockel, keine uebertragbare Regel "Ablagehoehe =
> Auflagenhoehe".** In der Naehe des Sockels stimmt es; anderswo nicht.

Die naheliegende Erklaerung, ungeprueft: die Hoehenspalte ist nicht der einzige Hinweis. Beim
Absenken ueber einer Auflage traegt auch die gemessene Objekthoehe Information, und die beiden
stimmen in echten Daten immer ueberein. Die kontrafaktische Probe aendert nur die eine und laesst
die andere auf Tischwerten stehen - das Netz sieht dann zwei widersprechende Hinweise. Ein Test
waere, beide gemeinsam zu setzen.

# Die Tischablage haelt - auf den Zustaenden, die noch vorkommen

    Tisch-Absenkung |Fehler| Median
      auf den AKTUELLEN Tischzeilen   4,7 -> 9,7 -> 6,7 -> 9,2 -> 6,2 mm
      auf dem ALTEN festen Probenset  4,7 -> 31,0 -> 23,3 -> 21,9 -> 21,2 mm

**Beide Zahlen sind richtig, und der Unterschied ist die Aussage.** Auf Zustaenden, die im Lauf
weiter vorkommen, bleibt die Tischablage innerhalb weniger Millimeter. Das feste Probenset stammt
aus Szenen mit VIER Objekten an anderen Plaetzen und ohne Sockel - diese Zustaende treten in diesem
Lauf nicht mehr auf, und dort wird die Policy deutlich schlechter.

Ob das schlimm ist, haengt an der Frage, die man stellt: als "verlernt sie die alte Aufgabe" gelesen,
lautet die Antwort **nein, solange die alte Aufgabe weiter vorkommt**. Als "bleibt sie auf einer
Welt brauchbar, die sie nicht mehr sieht", lautet sie **nein**.

# Fallen

* **`ebene: pruefstand`.** Gemessen ist das Netz. Ob die Policy selbst fahrend stapelt, ist ein
  `ACT23_CHOREO=netz`-Lauf und steht weiter aus - das ist jetzt der naechste Schritt.
* **Ein Lauf, ein Seed je Abschnitt.** Der stetige Abfall des Stapelfehlers ueber vier Staende ist
  das staerkste Einzelindiz; er ist nicht gegen einen zweiten Seed geprueft.
* **Der Teacher faehrt.** Die Ablagehoehe kommt weiter als Geruest aus dem Simulator; gemessen wird,
  ob die Policy sie NACHVOLLZIEHT, nicht ob sie sie selbst finden koennte.
* **Drei Hoehen.** Eine Steigung aus drei Stuetzstellen, und alle im Bereich 6-14 mm.
* **Die Stichprobe je Hoehe und Stand ist klein** (einige Dutzend Absenkzeilen).

# Verwandt

* [Gemischt lernen, erster Lauf](/befunde/gemischt-lernen-erster-lauf.md) - dieselbe Messung mit 10 statt 100 Szenen
* [Die Policy lernt die Ablagehoehe - als Ort](/befunde/policy-lernt-hoehe-als-ort.md) - der Lauf mit festem Sockel
* [Der Teacher widersprach dem Stapel](/befunde/teacher-widerspricht-dem-stapel.md) - die Vorbedingung
* [Der Arm stapelt](/befunde/stapeln-gemessen.md) - die Aufgabe selbst
