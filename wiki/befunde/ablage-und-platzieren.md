---
type: Befund
title: Beim Ablegen zaehlt nur die seitliche Genauigkeit
description: Der Endfehler ist praktisch vollstaendig der Fehler, den die Policy beim Loslassen schon hatte (r = 0,98). Die Drift danach verbessert eher. Meine eigene Empfehlung "die Policy senkt zu wenig ab" ist damit nicht handlungsrelevant.
tags: [act23, ablage, policy]
status: stable
evidenz: gemessen
ebene: langlauf
generated: { by: claude/opus-5, at: 2026-07-26T00:00:00Z }
verified: { by: human:thomas, at: 2026-07-26T00:00:00Z }
sources:
  - id: chronik
    resource: /chronik/act23.md
    title: act23-Chronik, Ablage-Eintraege 2026-07-23 bis 2026-07-26
---

# Behauptung

Der Hebel beim Ablegen ist **ausschliesslich die laterale Zielgenauigkeit im Carry**. Weder die
Ablegehoehe noch eine separate Platzierphase erklaeren etwas.

# Zahlen

    n = 197 (bestaetigt eine erste Messung mit n = 13):
      seitlicher Fehler beim Loslassen   Median 25 mm
      Drift danach                              11 mm
      Endfehler                                 21 mm
      Korrelation seitlich <-> final      r = +0,98
      Korrelation Drift    <-> final      r = -0,39   (die Drift VERBESSERT in 8 von 13 Faellen)

Also: selbst **wenn** zu hoch losgelassen wird, schadet es nicht.

**Der Platzierfehler ist griffgetrieben, nicht platzierspezifisch** (177 L-Episoden):

    Griffpunkt zentral (<15 mm off)             -> Median 24 mm
    Wrist ausgerichtet                          -> Median 20 mm, 70% <= 30 mm
    GUTER Griff (zentral UND ausgerichtet, n=44) -> Median 19 mm, 70% geliefert
    Griffpunkt daneben                          -> Median 38 mm, 49% grob
    Wrist daneben/gespiegelt                    -> Median 39 mm, 48% grob

Die "16 von 40 daneben platziert" sind groesstenteils derselbe Hebel wie die
[Wrist-Konditionierung](/befunde/wrist-ausrichtung.md) - sie schrumpfen von allein, **kein
separater Fix noetig**.

**Das einzige echte Platzier-/Release-Residuum:** ~5 % (9/177) schleudern das L 100-285 mm trotz
perfektem Griff. **Bimodal** (enger Cluster 4-32 mm, dann Ausreisser 96-285 mm, nichts
dazwischen) = ein **diskretes Ereignis** (Release-Flick, Lift-Whip oder Rutsch ueber die
Tischkante), nicht graduelle Streuung. 285 mm ist mehr als die ganze Arbeitsraumbreite (240 mm).

# Aus der Pufferanalyse

    Divergenz Policy gegen Teacher je Regime:
      Anfahrt (offen)     67,2% des Puffers /  3,1 mm
      Recovery             7,5%              /  3,5 mm
      Schliessen/Heben    20,9%              /  3,6 mm
      CARRY/place          4,4%              / 13,2 mm   = 4x schlechter
        davon "carry ueber Ziel"   896 Samples / 12,7 mm
              "senken aufs Ziel"   157 Samples / 16,1 mm  (Teacher 0,018 gegen Policy 0,034)
        die SELBST-IMITATIONS-Demos senken sogar nur auf 0,050
    36% der Carry-Vorhersagen liegen UEBER dem Teacher-Maximum, bis 0,123 statt CARRY_Z = 0,090

Das erklaert zwei Nutzerbeobachtungen woertlich: "hebt es unendlich hoch in den Himmel"
(Hoehen-Extrapolation) und "rutscht beim Transport aus dem Greifer" (aus ~5 cm fallen gelassen).

**Aber:** die Absenk-Diskrepanz existiert im Puffer und erzeugt **keinen Ergebnis-Schaden**
(siehe r = 0,98 oben). Meine Empfehlung "die Policy senkt 16 mm zu wenig ab, das ist der Hebel"
ist damit **nicht handlungsrelevant**.

# Recovery-DAgger - meine eigene Empfehlung widerlegt

Vor dem Bauen den persistierten Policy-Puffer vermessen:

    Recovery-Zustaende (Greifer zu + Hand auf Tragehoehe + Objekt noch am Boden)
      1802/24000 = 7,5% im DAgger-Puffer (nach dem geschuetzten CORE sogar 11%)
      korrekt gelabelt (aim_z = OVER_Z, 100% "oeffne")
      die Policy FUEHRT SIE AUS: |aim - Teacher| 3,5 mm, oeffnet in 98% der Faelle

Ein Recovery-DAgger wuerde ein funktionierendes Regime nachtrainieren. Die act21-Uebertragung
(7/12 -> 11/12) gilt dort, wo die Daten wirklich fehlten - in act23 fehlen sie nicht.

# Fallen

* **Es gibt ZWEI `pc_act16.py` mit verschiedenen Vorgaben** - `src/pc/pc_act16.py` mit
  `J5_OPEN=1.08` gegen `src/pc_cvnn/pc_act16.py` mit **0.54**; `pc_act23` importiert die
  pc_cvnn-Variante. Mit den falschen Schwellen kippt die Regime-Zuordnung komplett (die Anfahrt
  schien 0,67 % statt 67 %). **Bei jeder act23-Pufferanalyse `import pc_cvnn.pc_act16`.**
* **Mein erster Ablage-Messversuch war falsch.** Der Ausloeser "erstes `j5 > J5_CLOSED_TH` bei
  angehobenem Objekt" feuerte schon beim **Abheben**, weil die Klaue waehrend des Tragens ohnehin
  meist ueber der Schwelle steht. Signatur des Fehlers: "Fallhoehe" konstant 14-15 mm = exakt die
  Hebeschwelle. Korrigiert auf "LETZTER Schritt mit `j5 < J5_CLOSED_TH` und angehobenem Objekt".
* Das Regime "loslassen" zaehlt in beiden Puffern 0 Samples - **teils ein Definitionsartefakt**
  (sobald das Objekt aufsetzt, gilt es nicht mehr als gegriffen).

# Folgen

Die laterale Genauigkeit steckt in der `RuntimePolicy`, und die lernt **nicht** vom Weltmodell
(das waehlt nur Wrist und Grip). Der Ort dafuer waere die Selbst-Imitation. Genau dort ist der
Ertrag inzwischen gemessen und liegt bei null - siehe
[Imitationspuffer](/befunde/imitationspuffer.md).

# Verwandt

* [Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md)
* [U-Form-Engpass](/befunde/u-form-engpass.md)
