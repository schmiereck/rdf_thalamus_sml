---
type: Befund
title: Der sparsame Welt-Fit kostet nichts - 200 gegen 200 Episoden
description: FULL_EVERY=4 gegen die Vorgabe 1, je 200 Episoden im vollen Steuerungslauf. Lieferquote 51,5 gegen 52,5 Prozent (p = 0,92), Selbst-Aneignung ununterscheidbar, Laufzeit 2,95 statt 4,74 Stunden. Ein ehrliches Null-Ergebnis mit einem Nebengewinn.
tags: [act23, weltmodell, laufzeit, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-07T23:15:00Z }
sources:
  - id: armA
    resource: "Kopfloser Steuerungslauf, ACT23_WORLD_FULL_EVERY=1, 200 Episoden, 4,74 h"
    title: Arm A (Vorgabe)
  - id: armB
    resource: "Kopfloser Steuerungslauf, ACT23_WORLD_FULL_EVERY=4, ACT23_WORLD_EPOCHS_SHORT=20, 200 Episoden, 2,95 h"
    title: Arm B
---

# Behauptung

Der volle Welt-Fit nach **jeder** Episode ist auf act23-Ebene nicht nachweisbar besser als ein
voller Fit alle vier Episoden mit 20 Epochen dazwischen - weder in der Lieferquote noch in der
Selbst-Aneignung. Er kostet dabei **61 % mehr Laufzeit**.

Damit ist die Pruefstandsvorhersage aus
[Welt-Fit: Warmstart](/befunde/welt-fit-warmstart.md) auf der einzigen Ebene bestaetigt, auf der
das zaehlt - was in diesem Projekt eher die Ausnahme ist
([Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)).

# Aufbau

Nach [kopflosem A/B](/messungen/act23-headless-ab.md), mit **zwei bewussten Abweichungen** von
der dortigen Vorlage:

* **Nicht `ACT23_VIZ=0`.** Die Vorlage fuehrt ueber `main_diag()`; der geaenderte Fit sitzt aber
  in `run_self_learning_steering`, wo `main_diag` nie hinkommt. Beide Arme fuhren deshalb
  `ACT23_VIZ=1 ACT23_VIZ_HEADLESS=1 ACT23_AUTO_N=200` - denselben Pfad wie die GUI des Nutzers.
* **Nicht `ACT23_NO_PERSIST=1`.** Erstens sperrt der Schalter im kopflosen Lauf auch das
  **Laden** (beide Arme waeren bei null gestartet). Zweitens ist die Frage gerade, ob der
  billigere Fit ueber Hunderte Episoden schadet - ein eingefrorener Zustand koennte das nicht
  zeigen. Jeder Arm bekam eine **eigene Kopie** von `act23_state.pkl` (`f8395ba2...`, 11273
  Zeilen) und schrieb nur dorthin; die Datei des Nutzers blieb unangetastet.

Beide Arme liefen **gleichzeitig** - zulaessig und sogar vorzuziehen, seit
[Rechnerlast](/befunde/rechnerlast.md) zeigt, dass Last nur Zeit kostet: so sehen beide dieselben
Maschinenbedingungen, und ein Zeit-Konfounder kann sich nicht aufbauen. Einziger Unterschied
zwischen den Armen ist `ACT23_WORLD_FULL_EVERY`; `ACT23_DEBUG=1` stand in **beiden** (es
verschiebt den Zufallsstrom).

# Zahlen

    Lieferquote
      Arm A  FULL_EVERY=1 (Vorgabe)   105/200 = 52,5 %   Median-Abstand 24 mm
      Arm B  FULL_EVERY=4             103/200 = 51,5 %   Median-Abstand 24 mm
      Differenz -1,0 Punkte           Fisher exakt p = 0,9203

    Quote je 50 Episoden
      Arm A   44,0 | 50,0 | 62,0 | 54,0
      Arm B   44,0 | 58,0 | 50,0 | 54,0

    Laufzeit
      Arm A   Median 94,3 s je Episode (Lernen 74,9)   gesamt 4,74 h
      Arm B   Median 42,4 s je Episode (Lernen 19,2)   gesamt 2,95 h
      Welt-Fits: A 155, B 157 (davon 117 kurz) -- gleiche Belehrung, anderer Plan

    Selbst-Aneignung (das eigentliche Kriterium, s. /ziel.md)
      unzuordenbare Sichtungen je 50 Ep   A  0 | 14 | 30 | 43 (Ende 66)
                                          B  0 | 14 | 20 | 42 (Ende 58)
      mittlere Wiedererkennung je 50 Ep   A  15,7 | 20,2 | 27,6 | 29,1 %
                                          B  18,3 | 23,1 | 27,2 | 23,7 %
      neu geborene Formklassen            A 0, B 0 (beide sehen dieselben fuenf: neu-9,
                                          neu-13, neu-34, neu-285, neu-359)

    Objektmischung (gleicher Seed erzwingt KEINE gleiche Folge)
      obj_L     A 35 / 60,0 %  | B 20 / 35,0 %   p = 0,097
      obj_T     A 37 / 40,5 %  | B 40 / 50,0 %   p = 0,494
      obj_U     A 31 / 48,4 %  | B 35 / 51,4 %   p = 1,000
      obj_X     A 33 / 63,6 %  | B 36 / 66,7 %   p = 0,806
      obj_blue  A 34 / 61,8 %  | B 24 / 54,2 %   p = 0,598
      obj_green A 18 / 33,3 %  | B 25 / 52,0 %   p = 0,351
      obj_red   A 12 / 50,0 %  | B 20 / 40,0 %   p = 0,718
      keiner naehert sich der Bonferroni-Schranke 0,0071 bei sieben Objekten

# Bewertung

* **Die Zielgroesse ist tot gleich** (-1,0 Punkte, p = 0,92), und die Blockverlaeufe kreuzen
  sich. Bei n = 200 je Arm schliesst das Unterschiede oberhalb von rund 10 Punkten aus; kleinere
  bleiben offen. Das ist keine Schwaeche dieser Messung, sondern die Aufloesung, die
  [Rechnerlast](/befunde/rechnerlast.md) fuer act23 beziffert hat.
* **Die Selbst-Aneignung ist ebenfalls ununterscheidbar.** Das war der wichtigere Test: nach
  [Projektziel](/ziel.md) zaehlt Aneignung, nicht Lieferrate. Beide Arme lassen die
  unzuordenbaren Sichtungen gleich schnell linear wachsen und gebaeren **in 200 Episoden keine
  einzige** neue Klasse - eine unabhaengige Bestaetigung von
  [Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md), diesmal in beiden Armen.
* **Der Nebengewinn ist gross:** 1,79 Stunden auf 200 Episoden, also 61 % mehr Episoden je
  Stunde. Bei einer Nachweisgrenze von 26 Punkten je 50er-Fenster entscheidet genau das, wie
  viele belastbare A/Bs ueberhaupt bezahlbar sind.

# Fallen und Vorbehalte

* **Eine Nebengroesse lehnt gegen B:** "Griff hielt nicht (Drucksensor)" 11,0 % (A) gegen 17,0 %
  (B), Fisher p = 0,112. Nicht signifikant, und bei mehreren betrachteten Nebengroessen erst
  recht nicht - aber es ist der einzige Wert, der in eine Richtung zeigt, und deshalb der, den
  ein zweiter Lauf zuerst nachpruefen sollte.
* **Die Anfahrgenauigkeit ist in diesem A/B NICHT gemessen.** `ACT16_GLAUBDIAG` stand in keinem
  der beiden Arme, es gibt also keine `[Glaube]`-Zeilen. Die
  [Ablenker-Bindung](/befunde/ablenker-anfahrt.md) laesst sich aus diesen Laeufen nicht
  beurteilen; wer sie mitmessen will, muss den Schalter setzen.
* **`FULL_EVERY=4` ist ein Punkt, keine Kurve.** Ob 10 oder 20 ebenso folgenlos waeren, ist
  ungemessen - die Aufnahmekraft sinkt mit n weiter, und der Pruefstand hat sie als den einzigen
  echten Verlust ausgewiesen.

# Folgen

Der Schalter bleibt vorerst auf `1`. Das Ergebnis **traegt** eine Umstellung auf `4` - es ist
kein Grund dagegen gefunden, und der Zeitgewinn ist der groesste einzelne Hebel fuer kuenftige
Messungen - aber die Vorgabe aendert das Verhalten der laufenden GUI des Nutzers und ist
[dessen Entscheidung](/entscheidungen/welt-fit-plan.md).

# Verwandt

* [ACT23_WORLD_FULL_EVERY](/entscheidungen/welt-fit-plan.md) - der Schalter
* [Welt-Fit: Warmstart](/befunde/welt-fit-warmstart.md) - die Pruefstandsvorhersage, hier bestaetigt
* [Rechnerlast](/befunde/rechnerlast.md) - die Nachweisgrenze
