---
type: Befund
title: Stufe 4 auf EINEM Seed - 49 gegen 14 Prozent, im gepaarten Sweep NICHT reproduziert
description: Der Einzelseed-Durchgang nach vier Reparaturen: 17 von 35 gegen 5 von 35, also 49 gegen 14 Prozent bei Fisher p = 0,004. EINGESCHRAENKT 2026-09-22 - der gepaarte Sweep ueber acht Seeds reproduziert das nicht (38 gegen 33 Prozent, Vorzeichentest p = 0,69), und dieser Seed war in BEIDEN Armen ein Ausreisser in entgegengesetzte Richtungen. Die Wirkungsaussage faellt; die Sprachzahlen und der Mechanismus bleiben.
tags: [act23, stapeln, sprache, rekursion, eingeschraenkt]
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

# EINGESCHRAENKT 2026-09-22: der gepaarte Sweep reproduziert das nicht

Alles auf dieser Seite steht auf **einem Seed**. Der
[gepaarte Sweep ueber acht Seeds](/befunde/stufe4-sweep-widerlegt.md) sagt etwas anderes:

    gepoolt ueber 8 Seeds    A 66/200 = 33 %    B 76/200 = 38 %
    Vorzeichentest           B besser 4, A besser 2, gleich 2   ->   p = 0,69

**Dieser Seed war in BEIDEN Armen ein Ausreisser, und zwar in entgegengesetzte Richtungen:** A mit
14 % unter der Sweep-Spanne von 20-60 %, B mit 49 % ueber der von 28-44 %. Die 35 Punkte waren
nicht der Effekt, sondern die Summe zweier Zufaelle.

**Die Wirkungsaussage unten faellt.** Was bleibt, sind die Sprachzahlen (aus anderen Zeilen
gezaehlt) und der Mechanismus selbst.

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

* **Ein Seed, ein Lauf je Arm -- und der Sweep ist inzwischen gelaufen.** `p = 0,004` war ein
  Fisher-Test ueber 70 Episoden eines einzigen Seeds. Der gepaarte Sweep ueber acht Seeds
  **reproduziert die Wirkung nicht** (38 gegen 33 %, p = 0,69), s.
  [dort](/befunde/stufe4-sweep-widerlegt.md). Die Streuung zwischen den Seeds ist riesig (Arm A
  20-60 %); ueber sie hinweg sind 10 Punkte mit acht Seeds nicht aufzuloesen.
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
