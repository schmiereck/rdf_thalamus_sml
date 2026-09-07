---
type: Befund
title: Die Leistung der Policy haengt nicht an ihren Imitationsdaten
description: 21% mehr Daten, 20% bessere Daten, Online-AWR und zwei Langlaeufe zeigen dasselbe - nichts. Enthaelt die Nullsummen-Diagnose (altersblinde Verdraengung) und die Gegenkraft, die den Puffer trotzdem load-bearing macht.
tags: [act23, policy, imitation, negativ]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-01T22:12:00Z }
verified: { by: human:thomas, at: 2026-09-01T22:12:00Z }
sources:
  - id: ab
    resource: /raw/index.md
    title: act23-A/B je 250 Ep, identischer Startzustand, Seed 11, NO_PERSIST
---

# Behauptung

Aus **vier unabhaengigen Richtungen** kommt dasselbe Ergebnis:

    21% MEHR Imitationsdaten   (ACT23_IMIT_FAIL)          -> nichts, Wache sogar adversiv
    20% BESSERE Imitationsdaten (guetebewusste Verdraengung) -> nichts
    Online-AWR ueber viele Episoden                        -> Plateau
    zwei Langlaeufe ueber je 1000+ Episoden                -> kein Lernfortschritt

**Die Leistung der Policy haengt nicht an ihren Imitationsdaten.** Wer sie heben will, muss
woanders ansetzen. Das spart kuenftige Arbeit an diesem Puffer.

# Der Weg dorthin

**Wo die verworfenen Fehlschlaege herausfallen** - `pc_act23.py:3770`, eine Zeile:

    imit_ok = delivered and s_d is not None and s_d < imit_bar
    _q = wm_quality(s_d)          # das GEWICHT ist bereits abstandsgestuft!
    imit_bar = ACT23_IMIT_BAR = 0.025   # == die LIEFERTOLERANZ

`quality(d) = exp(-(d/0,025)^2)` ist eine glatte Glocke: 24 mm -> 0,398 | 26 mm -> 0,339 |
35 mm -> 0,141 | 50 mm -> 0,018. **Die Guete ist glatt, die Behandlung ist eine Klippe.**
Zwischen 24 und 26 mm liegen 0,06 Guete, aber der Unterschied in der Behandlung ist 0,398 gegen
null. Das **Bewertungs**kriterium ist ins **Lern**signal durchgeschlagen.

**Kein eigener Mechanismus - der Schwanz derselben Verteilung** (748 getragene Episoden):

    Endabstand  0-10 mm (n=125) 100,0% geliefert | 20-25 mm (n=152) 97,4%
                25-30 mm (n= 68)  16,2%          | 30-40 mm (n= 51)  0,0%
    Die 198 "daneben platziert": Median 32 mm, 56% unter 35 mm

**Der groessere Fund daneben:** der GRIFF-Teil dieser 198 ist so gut wie bei den Lieferungen -
Tragedruck Median 4,61 N gegen 4,86 N, Freigabehoehe identisch (23 mm), seitlicher Abstand beim
Oeffnen identisch, Driftweite identisch. Gegriffen, gehoben, getragen: alles gelungen. Verworfen
wird die **ganze Bahn**, weil die Ablage danebenging.

# Die Nullsummen-Diagnose

Das Tor zu oeffnen wurde gebaut und gemessen (`ACT23_IMIT_FAIL`, je 250 Ep):

    0) Vorschaltpruefung  AUS 0x "knapp daneben" | AN 37x   Imitationen 129 -> 156 (+21%)
    1) HAUPT Endabstand   18,0 -> 17,0 mm            Mann-Whitney p = 0,57
    2) Lieferquote        56,8% -> 54,8%             -2,0 Punkte, p = 0,72
    3) REGRESSIONSWACHE   Griff-Fehlschlaege 26,8 -> 30,0%   p = 0,49  -- FALSCHE RICHTUNG

**Die Ursache widerlegt meine eigene Vorabschaetzung.** Ich hatte "+8,5 % Gewicht" vorhergesagt -
unter der Annahme, dass **hinzugefuegt** wird. Der Selbst-Puffer ist randvoll (12000, jeder
Schluessel bei exakt 1500), und `runtime_policy.py:194` verdraengt

    while len(self._Xi) > IMIT_CAP:   # evict the OLDEST sample of the FULLEST key

**altersbasiert - die Guete wird nicht gefragt.** Ein neuer Eintrag mit Gewicht 0,2 verdraengt
einen alten mit 0,9. Es wird also nichts hinzugefuegt, sondern **ersetzt**.

> **Solange die Verdraengung gueteblind ist, ist JEDES Hinzufuegen von Lernstoff ein
> Nullsummenspiel.**

# Guetebewusste Verdraengung - wirkt, schadet nicht, bringt nichts

Gebaut (`ACT23_IMIT_EVICT_QUAL`, Vorgabe AN): die Schluessel-Balance bleibt (gemessen noetig -
reines FIFO liess haeufige Erfolge die seltenen ausspuelen, U 60 % -> 10 %), aber innerhalb des
vollsten Schluessels darf nur die **aeltere Haelfte** verdraengt werden, und dort zuerst der
**schwaechste**.

Nicht rein nach Guete: dann blieben uralte gute Demos ewig liegen, waehrend die Policy
weiterlernt. **Alter UND Guete.**

    Einheitstest (300 Ep, Kapazitaet 400): mittlere Guete 0,501 -> 0,689, Median 0,534 -> 0,809,
      Anteil < 0,2 von 17,5% auf 10,2%; Schluessel-Balance in beiden PERFEKT; aelteste 25% 0,558 -> 0,876

    act23-A/B, je 250 Ep, identischer Startzustand:
      0) VORSCHALTPRUEFUNG  Puffer-Guete  0,712 -> 0,852  (+0,140)  KLAR BESTANDEN
      1) HAUPT Lieferquote  56,8% -> 57,6%   +0,8 Punkte   Fisher p = 0,928
      2) Endabstand         18,0 -> 17,0 mm  Mann-Whitney p = 0,137
      3) REGRESSIONSWACHE   Griff-Fehlschlaege 26,8% -> 26,4%   p = 1,000

Der Mechanismus tut nachweislich, wofuer er gebaut wurde, und schadet nicht - **bringt aber
keinen messbaren Gewinn**. Nachweisgrenze war vorab mit ~13 Punkten angemeldet, beobachtet sind
+0,8; "kein Effekt" und "kleiner Effekt" sind nicht unterscheidbar. Vorgabe AN, weil es strikte
Datenhygiene ist und nichts kostet - der **Nutzen ist unbewiesen**, das gehoert dazugesagt.

# Die Gegenkraft: der Puffer ist trotzdem tragend

Ein aelterer Befund steht dagegen und ist nicht aufgeloest: **der Selbst-Imitationspuffer traegt
die Faehigkeit, die ueber den Teacher hinausgeht.** In einer Probe mit geleertem `_Xi` und
abgeschalteter Selbst-Imitation brachen **beide** Objekte ein (Wuerfel 85 % -> 12 %). Die
DAgger-Etiketten allein reproduzieren das riegel-abhaengige Teacherverhalten.

Daraus vier architektonische Lehren:

1. Guard-frei hat die gelernte Policy den geskripteten Teacher **uebertroffen** (U 60 % gegen
   5 % im Block) - der Teacher ist Etikettquelle, keine Decke.
2. Der Selbst-Imitationspuffer ist der **Traeger** dieser Faehigkeit.
3. Reines FIFO auf Erfolgspuffern erzeugt **Rich-get-richer-Ausloeschung** der seltenen
   Faehigkeit.
4. **DAgger von einem Teacher, der im aktuellen Regime falsch liegt, VERLERNT entdeckte
   Faehigkeiten.** Fix: "der Teacher korrigiert Fehlschlaege, er darf einen selbst validierten
   Erfolg nicht ueberschreiben" - eine Episode steuert **entweder** ihre eigenen sicheren
   Aktionen **oder** die Teacher-Korrekturen bei, nie beide widersprechenden Mengen.

# Fallen

* **Median-Vergleiche auf zweigipfligen Verteilungen sind wertlos.** Ich hielt kurz den "Versatz
  entlang der Klaue" fuer die Ursache (Median +1 mm bei Lieferungen gegen -7 mm bei
  Fehlschlaegen). Richtig getestet trennt er nicht (81,6 % gegen 76,5 %, p = 0,39) - die
  Verteilung ist zweigipflig, beide Extreme liefern gleich gut.
* `ACT23_IMIT_FAIL` ist gebaut, Vorgabe AUS. Die Begruendung steht als Kommentar an der
  Konstante, damit niemand denselben Weg zweimal geht.

# Offen

Der **grosse Weg** (phasenweise Gutschrift) ist unangetastet: `anfahren`/`greifen`/`tragen` aus
den 198 verworfenen Episoden sind echte gelungene Demonstrationen und gehoeren mit **vollem**
Gewicht in den Puffer; nur `ablegen` wird gedaempft. Die Phasen stehen im Log bereits. Grob
+36 % Greif-Demonstrationen bei vollem Gewicht statt +8,5 % bei gedaempftem. Erwartung nach dem
Obigen: gering.

# Verwandt

* [Ablage und Platzieren](/befunde/ablage-und-platzieren.md)
* [Kredit und Selbst-Urteil](/mechanismen/kredit-und-selbsturteil.md)
* [1109 Episoden ohne Lernfortschritt](/befunde/langlauf-ohne-fortschritt.md)
