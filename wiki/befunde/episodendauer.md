---
type: Befund
title: Die Episodendauer haengt am Welt-Fit, nicht am Wachstum
description: Die "Lernen"-Phase ist praktisch vollstaendig world.train(600). Sie steigt unter Rechnerlast von 77 auf 130 s - ein Sprung, keine Rampe. Die internen Puffer wachsen dabei um 2-6 %; der Verdacht "er wird langsam, weil er mehr weiss" ist falsch.
tags: [act23, laufzeit, weltmodell]
status: stable
evidenz: gemessen
ebene: langlauf
generated: { by: claude/opus-5, at: 2026-09-07T16:00:00Z }
sources:
  - id: lauf932
    resource: log/pc_act23_2026-09-05_22-06-51_5152.txt
    title: GUI-Langlauf, 932 Episoden, 41 h
---

# Behauptung

Die Phase `[Zeit] ... | Lernen` ist im Wesentlichen **ein einziger Aufruf**: `world.train(600)`.
Sie kostet je Episode 77 s auf freiem Rechner und 130 s unter Last. Der Anstieg ist ein
**Sprung** an der Lastgrenze, keine Rampe mit der Laufzeit - der naheliegende Verdacht "die
Auswertung dauert immer laenger, weil die Puffer wachsen" traegt nicht.

# Zahlen

Mediane je 50 Episoden aus 932 Episoden ueber 41 Stunden.[^lauf932] Die beiden Lastfenster
(`run_history` im Vollbild) sind fett markiert:

    Ep     0- 49   Lernen  76,2 s   Ausfuehrung  65,9 s   gesamt 132,4 s
    Ep    50- 99   Lernen  77,6 s   Ausfuehrung  61,9 s   gesamt 137,2 s
    Ep   100-149   Lernen  78,8 s   Ausfuehrung  65,7 s   gesamt 134,1 s
    Ep   150-199   Lernen  79,2 s   Ausfuehrung  60,7 s   gesamt 137,0 s
    Ep  *200-249*  Lernen 126,2 s   Ausfuehrung  54,5 s   gesamt 180,2 s   <- Last
    Ep  *250-299*  Lernen  99,8 s   Ausfuehrung  69,3 s   gesamt 173,6 s   <- Last endet
    Ep   300-349   Lernen  73,2 s   Ausfuehrung  60,2 s   gesamt 132,6 s
    Ep   350-399   Lernen  77,0 s   ...
    Ep   400-799   Lernen  75,8 bis 84,2 s
    Ep  *800-849*  Lernen 138,5 s   Ausfuehrung  91,2 s   gesamt 222,4 s   <- Last
    Ep  *850-899*  Lernen 141,4 s   Ausfuehrung  96,4 s   gesamt 238,5 s   <- Last
    Ep   900-931   Lernen  87,0 s   Ausfuehrung 133,6 s   gesamt 219,1 s

    zusammengefasst    belastet   frei
      Lernen            129,9 s   77,5 s
      Ausfuehrung        77,0 s   65,6 s
      gesamt            200,7 s  136,7 s

Zurueck auf 73-84 s nach dem Schliessen von `run_history`, beide Male. Ueber 900 Episoden
hinweg gibt es **keinen Trend** ausserhalb der Lastfenster.

Die Zuordnung zum Welt-Fit ist ueber alle 932 Episoden **exakt** trennscharf: von 173 Episoden
unter 40 s Lernzeit hat **keine einzige** einen Welt-Fit, von 759 Episoden ueber 40 s haben
**alle 759** einen. Die internen Groessen
wuchsen im selben Zeitraum nur um 2-6 % (Weltmodell 10515 -> 10724 Zeilen, Latent 5001 -> 5281);
DAgger- und Selbst-Puffer sind mit 24000/12000 fest.

# Bewertung

* **Last kostet ~53 s je Episode**, also rund 40 % der Gesamtdauer. Vermutete Ursache ist
  BLAS-Thread-Ueberbuchung, nicht die Last selbst: `run_history` verbrauchte in einem Fenster nur
  264 s CPU-Zeit, kostete den Lauf aber rund 4300 s. Ungemessen.
* **Die Ausfuehrung reagiert schwaecher** (65,6 -> 77,0 s) und ist teilweise Renderarbeit.
  Der letzte Block (Ep 900-931, Ausfuehrung 133,6 s bei normaler Lernzeit) faellt aus dem Muster
  und ist unerklaert.
* **Kein Wachstumseffekt.** Wer die Verlangsamung dem gelernten Bestand zuschreibt, misst die
  Last mit.

# Der ungenutzte Hebel

`world.train(epochs=600)` laeuft **jede** Episode ueber den vollen Puffer von ~10500 Zeilen, um
**eine** neue Zeile einzuarbeiten. Das ist rund die Haelfte der Gesamtlaufzeit fuer 0,01 % neue
Daten. Ein warmgestartetes Nachtrainieren mit wenigen Epochen, oder ein voller Fit nur alle n
Episoden, waere ein reiner Zeitgewinn ohne Eingriff in die Architektur - **nicht gebaut**.

**Nachgemessen** (2026-09-07): der Fit startet **nicht** vom Nullpunkt, er ist bereits ein
Warmstart, und er ist nach einer Epoche konvergiert. Der Hebel besteht also - kostet aber
Aufnahmekraft fuer widersprechende Erfahrung. Siehe
[Welt-Fit: Warmstart](/befunde/welt-fit-warmstart.md).

# Verwandt

* [Rechnerlast beeinflusst die Lieferquote nicht](/befunde/rechnerlast.md) - dieselbe Lastgrenze,
  die andere Zielgroesse
