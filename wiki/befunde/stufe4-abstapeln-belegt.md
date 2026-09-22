---
type: Befund
title: Stufe 4 belegt - die Relation in der Adresse hebt das Abstapeln von 14 auf 49 Prozent
description: Der saubere Durchgang, nachdem vier Maengel behoben waren. Die relationale Adresse liefert 17 von 35 gegen 5 von 35 mit der gewoehnlichen Adresse, also 49 gegen 14 Prozent bei Fisher p = 0,004 - die erste signifikante Wirkung dieser Linie. Im Vorlauf ohne die Reparaturen waren es 32 Prozent; der Vergleichsarm blieb bei genau 14, die Reparaturen wirken also dort, wo sie sollen. Die Adresse loest in 28 von 31 Versuchen auf (6 mm Median, nur noch 3 mehrdeutig statt 11), und der Glaube liegt mit 19 mm fast wieder im gewoehnlichen Bereich. Damit ist die Sprache rekursiv und das Umstapeln faellt heraus, ohne dass ein Verb dazukommt.
tags: [act23, stapeln, sprache, rekursion, erfolg]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-22T00:00:00Z }
sources:
  - id: ab
    resource: "Drei kopflose Laeufe auf Kopien von act23_state.pkl (ad9d768c), Seed 7001, ACT23_CHOREO=fsm, ACT23_SOCKEL_N=1, Chroma-Schnitt und Konzentrisch-Ausnahme in BEIDEN Armen: warm 40 Ep Stapelaufgabe mit ACT16_TASTEN + ACT23_HOEHE_TASTEN + ACT23_HOEHE_BELEGT (23 Tastwerte, 24 Schaetzerzeilen), dann NUR der Schaetzer in denselben Basiszustand verpflanzt, dann A und B je 35 Ep Abstapeln; Unterschied allein ACT23_ADR_RELATION=0 gegen =1. Gezaehlt ueber BEIDE Urteilszeilen, die uebereinstimmen."
    title: Das saubere Stufe-4-A/B
  - id: vorlauf
    resource: /befunde/stufe4-abstapeln-gemessen.md
    title: Der erste Durchgang und seine Berichtigung
---

# Ergebnis

    A  gewoehnliche Eigenschafts-Adresse     5 von 35 = 14 %
    B  relationale Adresse                  17 von 35 = 49 %

    Fisher p = 0,004

**Die erste signifikante Wirkung dieser Linie.** Zur Einordnung: die gewoehnliche
Transportaufgabe liefert auf demselben Zustand 40 bis 66 % - **das Abstapeln liegt damit im
Bereich des gewoehnlichen Transports**, obwohl es den Koerper erst finden, hoeher greifen und von
einer Auflage herunterholen muss.

# Die Reparaturen wirken dort, wo sie sollen

    ohne die Reparaturen (Vorlauf)   A 5 von 35 = 14 %    B 11 von 34 = 32 %
    mit den Reparaturen              A 5 von 35 = 14 %    B 17 von 35 = 49 %

**Der Vergleichsarm bleibt bei genau 5 von 35.** Das war die Vorhersage vor dem Lauf: alle vier
Reparaturen zielen auf den relationalen Zweig, ein Mitsteigen von A haette geheissen, dass etwas
davon nicht armspezifisch ist. Es steigt nicht.

Behoben waren:

1. **Drei Auslassungen im relationalen Zweig**, die jeder andere Adresspfad erfuellt: der
   Tracker-Keim (ohne ihn startet die Fovea blind auf dem wahrscheinlichsten Blob), `grasp_xy`
   statt des Schwerpunkts, und der Klauenversatz.
2. **Die Moebel-Schranke** im Paar-Kriterium: die Auflage ist das GROESSTE Ding im Bild. Ohne sie
   galten zwei Bruchstuecke desselben Koerpers als Stapel - gemessen eine "Auflage" von 263 px,
   wo die Platte 1400 hat.
3. **Der Hoehenschaetzer lernt das belegte Aussehen mit**
   ([gemessen](/befunde/schaetzer-auf-der-belegten-auflage.md): 34 % gegen 78 %).

# Die Zwischenschritte sagen dasselbe

                                  Vorlauf        sauberer Durchgang
    Adresse aufgeloest         27 von 38          28 von 31
    davon mehrdeutig                   6                   3
    kein Stapel gefunden               5                   0
    Adressfehler Median             6 mm                6 mm
    Glaube beim Loslassen       28-45 mm               19 mm

**Die Moebel-Schranke halbiert die Mehrdeutigkeit und beseitigt die Fehlanzeigen**, ohne den
Adressfehler zu veraendern - sie verwirft also Falsches, nicht Richtiges. Und der Glaube liegt mit
19 mm fast wieder im gewoehnlichen Bereich (5-18 mm), nachdem der Tracker seinen Keim bekommt.

# Was damit belegt ist

> **Die Sprache ist rekursiv.** `ADRESSE := (Farbe?, Form?, Groesse?) | RELATION ADRESSE` -
> dieselbe Relation im Subjekt wie im Ziel, und aus ihr faellt das **Umstapeln**, ohne dass ein
> Verb dazukommt.

Das ist der Ertrag, nicht die 49 %. Nach [Projektziel](/ziel.md) zaehlt, was der Agent selbst
kann: er adressiert jetzt einen Koerper ueber seine **Lage zu einem anderen**, findet ihn in
seinem eigenen Bild, greift ihn auf der richtigen Hoehe und traegt ihn fort - und keine dieser
Groessen kommt aus dem Simulator.

# Fallen

* **Ein Seed, ein Lauf je Arm.** `p = 0,004` ist ein Fisher-Test ueber 70 Episoden, kein
  gepaarter Sweep ueber Seeds. Nach [Messvorschrift](/messungen/act23-headless-ab.md) waere das
  die belastbarere Form; sie steht aus.
* **Die Reparaturen sind zusammen gemessen, nicht einzeln.** Welche der vier den Sprung von 32 auf
  49 % traegt, ist offen - moeglich ist auch, dass es nur eine ist.
* **Das belegte Aussehen bleibt duenn:** 1 von 23 Tastwerten. Der Schaetzer arbeitet also
  weiterhin fast nur mit dem leeren Aussehen, und dass es trotzdem reicht, ist eher Glueck als
  Konstruktion.
* **Ein Grundriss, eine Auflagenform, ein Objekt je Episode.** Mit drei Auflagenformen liegt der
  Schaetzer auf der Grundrate
  ([gemessen](/befunde/dritte-auflage-bricht-die-nachbarschaft.md)); dieser Befund sagt nichts
  ueber jene Welt.
* **Gezaehlt ueber beide Urteilszeilen**, die uebereinstimmen (17 und 17). Nach dem Zaehlfehler
  vom Vortag prueft das Auswerteskript das jetzt selbst und meldet eine Abweichung.

# Verwandt

* [Stufe 4 gemessen](/befunde/stufe4-abstapeln-gemessen.md) - der erste Durchgang und seine Berichtigung
* [Der Stapel wird sichtbar](/befunde/stapel-wird-sichtbar.md) - die Voraussetzung
* [Der Schaetzer auf der belegten Auflage](/befunde/schaetzer-auf-der-belegten-auflage.md) - eine der vier Reparaturen
* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - Stufe 4
* [Messvorschrift](/messungen/act23-headless-ab.md) - die zwei Fallen, die dieser Lauf vermeidet
