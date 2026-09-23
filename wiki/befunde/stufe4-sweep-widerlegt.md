---
type: Befund
title: Der gepaarte Sweep widerlegt die Stufe-4-Wirkung - 8 Seeds sagen 38 gegen 33 Prozent, nicht 49 gegen 14
description: Die Wirkungsaussage von Stufe 4 stand auf EINEM Seed. Der gepaarte Sweep ueber acht Seeds, je 25 Episoden pro Arm aus demselben Zustand, sagt etwas anderes - B gewinnt in 4 Seeds, A in 2, zwei sind gleich, Vorzeichentest p = 0,69. Gepoolt 76 von 200 gegen 66 von 200, also 38 gegen 33 Prozent bei Fisher p = 0,35. Der urspruengliche Seed war in BEIDEN Armen ein Ausreisser - A mit 14 Prozent unter der Sweep-Spanne von 20 bis 60, B mit 49 ueber der von 28 bis 44. Die 35 Punkte Abstand waren ein Zufall dieses einen Seeds. Die Sprachzahlen bleiben unberuehrt; die Wirkungsaussage faellt.
tags: [act23, stapeln, sprache, negativ, messen, seeds]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-22T00:00:00Z }
sources:
  - id: sweep
    resource: "Gepaarter Sweep auf Kopien von act23_state.pkl (ad9d768c): ein Warmlauf (40 Ep, Seed 7001, Tasten + belegtes Aussehen, 23 Tastwerte) liefert den Hoehenschaetzer, der in ALLE Seeds verpflanzt wird; dann Seeds 8101-8108, je Arm 25 Ep Abstapeln aus demselben Zustand, A und B parallel. ACT23_CHOREO=fsm, ACT23_SOCKEL_N=1, Chroma-Schnitt und Konzentrisch-Ausnahme in beiden Armen; Unterschied allein ACT23_ADR_RELATION=0 gegen =1"
    title: Der gepaarte Sweep
  - id: einzeln
    resource: /befunde/stufe4-abstapeln-belegt.md
    title: Die Einzelseed-Messung, die hier eingeschraenkt wird
---

# Ergebnis

     Seed        A            B         B - A
     8101    8/25  32 %    8/25  32 %      0
     8102    5/25  20 %   10/25  40 %    +20
     8103   15/25  60 %   10/25  40 %    -20
     8104    7/25  28 %    7/25  28 %      0
     8105    6/25  24 %   11/25  44 %    +20
     8106    6/25  24 %   11/25  44 %    +20
     8107   13/25  52 %    8/25  32 %    -20
     8108    6/25  24 %   11/25  44 %    +20
    gesamt  66/200 33 %   76/200 38 %

    Vorzeichentest: B besser 4, A besser 2, gleich 2   ->   p = 0,69
    gepoolter Fisher (nur zur Einordnung)              ->   p = 0,35

**Die Wirkungsaussage faellt.** Aus 49 gegen 14 Prozent mit p = 0,004 wird 38 gegen 33 mit
p = 0,69.

# Warum der Einzelseed so anders aussah

    Arm    Sweep-Spanne ueber 8 Seeds    Seed 7001 (die Einzelmessung)
    A          20 bis 60 %                      14 %
    B          28 bis 44 %                      49 %

**Der urspruengliche Seed war in BEIDEN Armen ein Ausreisser, und zwar in entgegengesetzte
Richtungen.** A lag unter der gesamten Spanne, B darueber. Die 35 Punkte Abstand waren damit
nicht der Effekt, sondern die Summe zweier Zufaelle.

Das ist genau der Fall, vor dem die [Messvorschrift](/messungen/act23-headless-ab.md) warnt:
*"Die Replikate sind die SEEDS, nicht die Wiederholungen."* Ich hatte sie zitiert, als ich die
Einzelmessung als offene Flanke benannte - und trotzdem eine Wirkung behauptet.

## Die Streuung ueber die Seeds ist riesig

Arm A schwankt zwischen 20 und 60 Prozent. **Ueber diese Spanne hinweg ist ein Unterschied von
10 Punkten mit acht Seeds nicht aufzuloesen** - der Vorzeichentest kann hier bestenfalls 0,0078
erreichen, und dafuer muessten alle acht in dieselbe Richtung zeigen. Zwei tun das Gegenteil,
zwei sind exakt gleich.

# Was bleibt

* **Alle Sprachzahlen.** Die Adresse loest auf, der Arm findet den gestapelten Koerper, greift
  ihn auf der richtigen Hoehe und traegt ihn fort. Das ist unabhaengig von der Quote gemessen
  ([dort](/befunde/stufe4-abstapeln-belegt.md): 28 von 31 aufgeloest, 6 mm Median) und vom Sweep
  nicht beruehrt.
* **Der Mechanismus.** `ADRESSE := ... | RELATION ADRESSE` funktioniert - er ist gebaut, er loest
  auf, er fuehrt zu einem getragenen Koerper. Nach [Projektziel](/ziel.md) ist das der Ertrag.
* **Die vier Reparaturen.** Dass der Vergleichsarm A auf Seed 7001 bei genau 5 von 35 blieb,
  waehrend B stieg, bleibt richtig beobachtet - es sagt nur weniger, als ich daraus gemacht habe.

# Was faellt

* **"Die erste signifikante Wirkung dieser Linie."** Es gibt sie nicht.
* **"Die relationale Adresse verdoppelt das Abstapeln."** Ueber acht Seeds sind es 5 Punkte, und
  die sind nicht von null zu trennen.

# Was die Protokolle nebenbei zeigen (nachgereicht 2026-09-23)

## Die Arme sind nur je Seed gepaart, nicht je Episode

    Seed   gleiche Szene in A und B   erste Abweichung bei Episode
    8101          17 von 25                    8
    8102          22 von 25                    1
    8103           5 von 25                    3
    8104           7 von 25                    2
    8105           6 von 25                    2
    8106          15 von 25                   14
    8107           5 von 25                    3
    8108          11 von 25                    8
    gesamt        88 von 200

Szenenwahl und Entscheidungen ziehen aus DEMSELBEN Zufallsgenerator (`crng`); sobald ein Arm
einmal anders entscheidet, verschiebt sich die Szenenfolge. **Nach zwei, drei Episoden sehen
die Arme verschiedene Welten** - der "gepaarte" Sweep ist also nur auf Seed-Ebene gepaart, und
die Streuung zwischen den Szenen landet vollstaendig im Vergleich.

## Der Vergleichsarm findet den Stapel ebenfalls

    Arm   relational aufgeloest   gehoben (>1 N)   losgelassen   geliefert
    A              0                  99              116            66
    B            140                 112              128            76

**Arm A hebt den gestapelten Koerper in 99 von 200 Episoden** - ohne die relationale Adresse.
Der Grund: der Chroma-Schnitt mit Konzentrisch-Ausnahme lief in BEIDEN Armen, der Stapel war
also auch fuer die gewoehnliche Eigenschafts-Adresse sichtbar. **Verglichen wurde damit nur die
Adresse, nicht Stufe 4 als Ganzes** - der groesste Schritt, die Sichtbarkeit (vorher 0 von 25),
steckt in beiden Armen. Die richtige Kontrolle fuer "was bringt Stufe 4" waere ein Arm OHNE den
Schnitt.

# Fallen

* **Ein gemeinsamer Hoehenschaetzer fuer alle Seeds.** Das war Absicht - gefragt war die Adresse,
  nicht der Schaetzer - nimmt aber eine Streuquelle heraus. Ein Sweep, der auch den Warmlauf je
  Seed fuehrt, koennte anders ausfallen; er ist nicht gelaufen.
* **25 Episoden je Arm und Seed.** Die Aufloesung je Seed ist damit 4 Punkte, und die Quoten
  springen in Vielfachen davon. Mehr Episoden je Seed haetten die Spanne nicht kleiner gemacht -
  sie ist zwischen den Seeds, nicht innerhalb.
* **Zwei Seeds meldeten abweichende Urteilszeilen** (8105 und 8107). Nachgesehen: in je einer
  Episode **fehlt die Selbst-Urteil-Zeile ganz**, die `[Auto]`-Zeile ist in allen 25 da. Kein
  Widerspruch im Urteil, eine unvollstaendige Zweitzeile - gezaehlt wurde `[Auto]`. Der
  Gegencheck sollte kuenftig nur dort vergleichen, wo beide Zeilen existieren.
* **Beide Arme liegen ueber dem, was Seed 7001 fuer A zeigte.** 33 und 38 Prozent gegen 14 -
  wer Abstapel-Quoten aus dieser Linie zitiert, nehme die Sweep-Zahlen, nicht die Einzelmessung.

# Verwandt

* [Stufe 4 belegt](/befunde/stufe4-abstapeln-belegt.md) - die Einzelmessung, hier eingeschraenkt
* [Messvorschrift](/messungen/act23-headless-ab.md) - "die Replikate sind die SEEDS"
* [Zwei Laeufe sind dieselbe Rechnung](/befunde/laeufe-sind-reproduzierbar.md) - warum Wiederholungen nichts bringen
* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - Stufe 4
