---
type: Befund
title: Der Welt-Fit ist bereits ein Warmstart - und nach einer Epoche konvergiert
description: world.train(600) setzt die Gewichte nicht zurueck, laeuft also jede Episode auf konvergierten Gewichten weiter. Die MSE steht nach EINER Epoche; 599 wandern im Rauschen. Kurze Fits weichen weniger vom 600er-Fit ab als zwei 600er-Fits voneinander. Was die 600 Epochen kaufen, ist allein Aufnahmekraft fuer widersprechende Erfahrung.
tags: [act23, weltmodell, laufzeit]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-07T17:30:00Z }
sources:
  - id: code
    resource: "src/pc_cvnn/pc_act19.py:47 (Policy.fit), src/pc_cvnn/arm_modules/world_model.py:506 (train)"
    title: Quelltext - fit() initialisiert keine Gewichte
  - id: sonde
    resource: "Scratchpad-Sonden auf einer Kopie von state/act23_state.pkl (11273 Zeilen, 5 Mitglieder, feat_dim 38, CROSS=True)"
    title: Konvergenz-, Sigma- und Aufnahmemessung
---

# Behauptung

Die Frage "geht ein Warmstart" hat eine unerwartete Antwort: **es ist schon einer.**
`Policy.fit` legt `W1/b1/W2/b2` nie neu an - die Gewichte entstehen ausschliesslich in
`__init__`. `world.train(600)` setzt also jede Episode 600 Epochen auf **bereits konvergierte**
Gewichte obendrauf. Der Fit ist nach einer Epoche fertig; der Rest ist bezahltes Rauschen.

Was die 600 Epochen dennoch kaufen, ist **nicht** Genauigkeit, sondern **Aufnahmekraft**: wie
schnell das Modell einer Erfahrung folgt, die dem Bestand widerspricht.

# Zahlen

**Der Fit ist warm** (Quelltext plus Probe): eine Epoche auf 100 Zeilen aendert `W1` um 0,0018
bei einer Gewichtsstreuung von 5,90. Ein Kaltstart wuerde die Matrix komplett neu wuerfeln.

**Konvergenz** - MSE ueber alle 11273 Zeilen, ein Mitglied, frischer Block-Bootstrap:

    Epochen      0        1        5       20      100      200      600
    MSE     0.085406 0.084391 0.084504 0.084002 0.083563 0.083028 0.084217
    Kosten: 18-19 ms je Epoche und Mitglied -> 600 x 5 = ~57 s je Episode

Der gesamte Gewinn faellt in der **ersten** Epoche an. Danach schwankt die MSE um +-0,001, und
der 600er-Wert ist schlechter als der 200er.

**mu und sigma**, 400 echte Zeilen, 3 Runden - gemessen gegen die **Eigenstreuung zweier
legitimer 600-Epochen-Fits mit verschiedenen Seeds**. Das ist die Rauschgrenze, unter der ein
Unterschied nichts bedeutet:

    600 Epochen, anderer Seed   |dmu| 0.0268  |dsigma| 0.0261  r = 0.9921   <- Kontrolle
    200 Epochen                 |dmu| 0.0128  |dsigma| 0.0158  r = 0.9983
     50 Epochen                 |dmu| 0.0237  |dsigma| 0.0258  r = 0.9938
     20 Epochen                 |dmu| 0.0231  |dsigma| 0.0231  r = 0.9955
      5 Epochen                 |dmu| 0.0246  |dsigma| 0.0241  r = 0.9935

    sigma absolut: Ausgang 0.1490 | 600 Ep 0.1509/0.1498 | 200 0.1478 | 50 0.1497
                   | 20 0.1461 | 5 0.1479

**Jede** verkuerzte Fassung liegt naeher am 600er-Fit als zwei 600er-Fits aneinander. Das ist
wichtig, weil sigma die Aktionswahl (`mu - lam*sigma`), die Neugier-Objektwahl und die
Neigungsneugier steuert - dort haette ein Schaden zuerst auftreten muessen.

**Aufnahme neuer Erfahrung.** 30 bestehende Zeilen mit **umgedrehtem** Etikett angehaengt, dann
8 simulierte Episoden; verfolgt wird der mittlere Fehler auf genau diesen Zeilen (Start 0,5759):

    600 jede Episode (heute)     61.1 s/Ep   Ende 0.5308   sigma 0.1435
    200 jede Episode             20.8 s/Ep   Ende 0.5420   sigma 0.1411
    600 alle 4 Ep, sonst 20      16.7 s/Ep   Ende 0.5422   sigma 0.1397
    600 alle 4 Ep, sonst 50      18.7 s/Ep   Ende 0.5426   sigma 0.1400

    Verlauf des 600er-Arms: 0.5268 0.5363 0.5493 0.5217 0.5443 0.5321 0.5508 0.5308

# Bewertung

* **Der Warmstart ist keine Baustelle, sondern der Ist-Zustand.** Wer die Laufzeit senken will,
  muss an der Epochenzahl ansetzen, nicht am Warmstart.
* **Die 600 Epochen sind fuer die Genauigkeit vollstaendig verschwendet** und fuer mu/sigma
  ununterscheidbar von 5 Epochen.
* **Sie sind nicht ganz umsonst:** die Aufnahme widersprechender Erfahrung ist beim vollen Fit
  rund dreimal staerker (0,576 -> 0,531 gegen -> 0,556 bei 50 Epochen). Das ist der einzige
  gemessene Vorteil, und er ist real.
* **Ein Zwischenweg holt die Zeit fast ganz zurueck:** voller Fit alle 4 Episoden, 20 dazwischen
  kostet 16,7 statt 61,1 s je Episode - Faktor 3,7 - und landet auf 0,5422 gegen 0,5308.
  **Ehrlich:** dieser Abstand von 0,011 liegt innerhalb der Eigenschwankung des 600er-Arms
  (0,5217 bis 0,5508 ueber seine eigenen 8 Runden), aber alle drei sparsamen Plaene landen
  gemeinsam bei 0,542 und der volle bei 0,531. Mit einem Seed ist das **nicht** als Rauschen
  abzutun. Die Richtung begünstigt den vollen Fit, die Groesse ist ungeklaert.
* **Ein Nebenbefund, der schwerer wiegt als die Laufzeit:** in *keiner* Einstellung kommt das
  Modell den neuen Etiketten nahe - von 0,576 auf bestenfalls 0,531 bei einem Sollwert von 0.
  30 widersprechende Zeilen gegen 11273 bewegen es kaum. Das passt zu AUC 0,489 aus der
  [Exekutionsvarianz](/befunde/exekutionsvarianz.md): das Modell sammelt lernbares Signal nicht
  ein, und die Epochenzahl ist nicht der Grund.

**Was das ausdruecklich NICHT heisst:** dass eine Umstellung die Lieferquote oder die
Selbst-Aneignung nicht beruehrt. Das ist ein Pruefstandsergebnis und sagt einen act23-Lauf
nicht vorher, siehe [Die Pruefstandsfalle](/mechanismen/pruefstandsfalle.md). Belegt ist nur:
mu und sigma bleiben innerhalb der Eigenstreuung, und das Verhalten haengt an genau diesen
beiden Groessen.

# Wenn es gebaut wird

`epochs=600` steht an sechs Stellen in `pc_act23.py` (267, 292, 371, 402, 2055, 4139). Nur
**4139** ist der Fit je Episode nach genau einer neuen Zeile - der teure. **2055 ist der
Anfangsfit auf frischen Versuchen und muss voll bleiben**; die uebrigen sind
Diagnose-Einsprungpunkte. Eine Umstellung gehoert hinter einen Schalter (etwa
`ACT23_WORLD_EPOCHS` / `ACT23_WORLD_FULL_EVERY`) und braucht ein A/B nach
[kopflosem A/B](/messungen/act23-headless-ab.md), bevor sie Vorgabe wird.

Nebenbefund zur Normierung: `fit(set_norm=True)` zieht `imu`/`isd` bei **jedem** Aufruf neu aus
dem Bootstrap. Der Versatz zwischen zwei Ziehungen betraegt hoechstens 0,063 Standardabweichungen
- eine milde Stoerung der warmen Gewichte, kein Handlungsbedarf.

# Warum das ueberhaupt zaehlt

Nicht, weil ein schneller Arm das Ziel waere - er ist es
[ausdruecklich nicht](/ziel.md). Sondern weil
[Rechnerlast](/befunde/rechnerlast.md) die Nachweisgrenze beziffert hat: ein 50-Episoden-Fenster
schwankt allein aus Zufall um 26 Punkte. Belastbare A/Bs brauchen also **viele** Episoden, und
die Episodendauer entscheidet, wie viele davon bezahlbar sind.

# Verwandt

* [Episodendauer](/befunde/episodendauer.md) - die Messung im Lauf, die diese Sonde ausgeloest hat
* [Rechnerlast](/befunde/rechnerlast.md) - die Nachweisgrenze
* [Exekutionsvarianz](/befunde/exekutionsvarianz.md) - das Modell sammelt Signal nicht ein
