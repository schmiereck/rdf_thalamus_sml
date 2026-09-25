---
type: Befund
title: Ruecksetz-Versuch - nur die Policy traegt die Leistung, sie lernt nach, aber langsam; Weltmodell und Fovea kosten zurueckgesetzt zunaechst nichts
description: Je eine Kopie des Live-Zustands mit EINEM frischen Lerner, 100 Episoden auf identischen Szenen gegen die unveraenderte Kontrolle. Policy frisch - die Quote faellt von 60 auf 0 Prozent und erholt sich in 100 Episoden auf 25-30, der Abstand zum Teacher sinkt von 39 auf rund 21 mm (Kontrolle 7,5) und stockt dort; McNemar p < 0,001 in beiden Haelften. Weltmodell frisch - in den ersten 50 Episoden exakt gleich viele Lieferungen wie die Kontrolle (26 gegen 26), danach 19 gegen 27 (p = 0,021). Fovea frisch - das Warmup stellt sie auf 7,6 mm her, online sinkt sie in ~60 Episoden auf Kontrollniveau; Lieferungen erst 29 gegen 26, spaeter 23 gegen 32 (p = 0,012). Die beiden spaeten Rueckgaenge ueberleben Bonferroni (0,0083) nicht. Deutung - die Lerner sind nicht lernunfaehig, sondern SATT an ihrem Lernziel, und das Lernziel der Policy ist der Teacher.
tags: [act23, lernen, policy, weltmodell, fovea, methode, gepaart]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-09-25T00:00:00Z }
sources:
  - id: lauf
    resource: "Kopien von act23_state.pkl (ad9d768c, danach unveraendert), je ein Lerner frisch (scratchpad-Werkzeug ruecksetzen.py: RuntimePolicyModule(rng=4) | WorldModelModule(k=5, off_max=0.008, feat_dim=38) | Schluessel 'fovea' entfernt -> Warmup), Kontrolle unveraendert. Seed 9701, 100 Ep, ACT23_SZENE_JE_EPISODE=1 ACT23_AUTO_CURIOUS=0, sonst Vorgaben; zwei Bloecke zu zwei Prozessen"
    title: Vier Arme, identische Szenen
  - id: rueckschau
    resource: /befunde/lernkurven-rueckschau.md
    title: Die flachen Lernkurven, die diese Frage aufwarfen
---

# Die Frage

Die [Rueckschau](/befunde/lernkurven-rueckschau.md) zeigt ueber 2162 Episoden keinen lernenden
Lerner. Flach kann **satt** heissen oder **lernunfaehig**. Das trennt nur eine Lernkurve von einem
niedrigen Stand aus: je eine Kopie mit einem frischen Lerner, gegen die Kontrolle auf identischen
Szenen (Szenen-Abdruck: 100/100, beim Weltmodell-Arm 92/100).

**Vorher festgehalten** (Board): Policy -> Erholung, offen wie schnell; Weltmodell -> langsam,
kleine Wirkung auf die Quote; Fovea -> das Warmup stellt sie sofort her.

# Ergebnis

    Block     Kontrolle   Policy frisch          Weltmodell frisch    Fovea frisch
              geliefert   gel.   |Netz-Teacher|  gel.   AUC  mu-Quote gel.   Fovea mm
     0-19        9          0       39,4 mm       10    0,55  -0,05    12      7,6
    20-39       12          0       32,2          10    0,41  +0,27    10      6,7
    40-59       14          5       23,2          13    0,65  -0,05    12      6,6
    60-79       11          4       23,8           6    0,45  +0,42     9      5,5
    80-99       12          6       21,4           9    0,53  +0,19     9      6,6
    (Kontrolle: |Netz-Teacher| 7,2-7,8 mm, Fovea 5,1-5,9 mm, Welt-AUC 0,60-0,87)

    McNemar gegen die Kontrolle (Bonferroni fuer 6 Tests: 0,0083)
      Policy       Ep  0-49:  2 gegen 26   (0 | 24)   p < 0,001   **
                   Ep 50-99: 13 gegen 32   (3 | 22)   p < 0,001   **
      Weltmodell   Ep  0-49: 26 gegen 26   (8 |  8)   p = 1,00
                   Ep 50-99: 19 gegen 27   (1 |  9)   p = 0,021
      Fovea        Ep  0-49: 29 gegen 26   (8 |  5)   p = 0,58
                   Ep 50-99: 23 gegen 32   (1 | 10)   p = 0,012

# Was das heisst

## 1. Die Leistung steckt in der Policy - und die lernt nach, aber langsam

Frisch zurueckgesetzt liefert sie 40 Episoden lang **nichts**, dann 25-30 %. Ihr Abstand zum
Teacher faellt von 39 auf rund 22 mm und **stockt dort** - die Kontrolle steht bei 7,5 mm. Die
Policy ist also nicht lernunfaehig; aber was sie in 100 Episoden nachholt, ist ein Bruchteil dessen,
was im Zustand steckt.

Warum es stockt, zeigt der Puffer (am Code): die ersten 8000 Beispiele sind als **Kern** vor dem
Verdraengen geschuetzt, weil sie urspruenglich aus dem Teacher-gefahrenen Warmup stammen. Beim
frischen Arm fuhr die FSM nur 2 Episoden, dann uebernahm die untrainierte Policy - ihr Kern sind
ihre eigenen schlechten Anfangsversuche, fuer immer. Und die Selbst-Imitation braucht Erfolge: der
erste kam nach 40 Episoden. **Die Leistung des Live-Zustands stammt zu einem guten Teil aus dem
Warmup und seinen Teacher-Vorfuehrungen**, nicht aus dem laufenden Lernen.

## 2. Weltmodell und Online-Fovea: zurueckgesetzt zunaechst kostenlos

Mit einem **leeren** Weltmodell liefert der Arm in den ersten 50 Episoden genau so oft wie mit dem
aus 12322 Versuchen gelernten (26 gegen 26). Das passt zur Rueckschau (Trennkraft 0,60) und zum
[Weltmodell-Deckel](/befunde/exekutionsvarianz.md): was es gelernt hat, zeigt sich in der Quote
nicht. Die Fovea wird vom Warmup auf 7,6 mm hergestellt und sinkt online in etwa 60 Episoden auf das
Kontrollniveau - **der einzige Lerner mit einer sichtbaren, abgeschlossenen Online-Lernkurve**,
ohne Wirkung auf die Quote in der ersten Haelfte.

Beide Arme verlieren in der ZWEITEN Haelfte (19 gegen 27, 23 gegen 32). Das ueberlebt die
Bonferroni-Schranke nicht, und die Kontrolle hatte dort ihren besten Block (14 von 20). Ein Hinweis,
kein Befund - beim Weltmodell passt er zur wachsenden Ueberzuversicht des jungen Modells (mu-Quote
bis +0,42).

## 3. Die Antwort auf "satt oder lernunfaehig": satt - am Teacher

Das Lernziel der Policy ist die Nachahmung des Teachers (DAgger-Etiketten aus `reactive_subgoal`)
plus die eigenen Erfolge, die selbst teacheraehnlich sind. Bei 7,5-9 mm Abstand ist dieses Ziel
**erreicht**; weiteres Lernen hat nichts mehr zu holen. Die flachen Langlaeufe sind damit kein
Versagen der Lernschleife, sondern ein erreichtes Lernziel. Das ist dieselbe Wand wie im
[Greif-Lerndeckel](/befunde/greif-lerndeckel.md) von der anderen Seite gesehen - und "ueber den
Teacher hinaus lernen" ist dort gemessen geschlossen.

**Fuer das [Projektziel](/ziel.md)** folgt daraus: Lerngeschwindigkeit ist nur dort eine sinnvolle
Messgroesse, wo das Lernziel noch NICHT erreicht ist - bei NEUEM (neue Farbe, neue Form, neues
Wort, neue Aufgabe), nicht beim Greifen der alten Koerper.

# Fallen

* **Ein Seed, eine Kette je Arm.** Die Policy-Wirkung ist riesig und sicher; alles andere ist
  Hinweis.
* **Der Weltmodell-Arm war nur in 92 von 100 Episoden szenengleich** - ein leeres Modell waehlt
  andere Aktionen und zieht dabei offenbar anders aus dem Zufall. Gezaehlt sind nur gleiche.
* **Frisch ist nicht "wie am ersten Tag".** Beim Policy-Arm fehlte das Warmup, das ein echter
  Neustart haette (der Start ueberspringt es, sobald ein Zustand geladen ist). Das Nachlernen ist
  also langsamer als ein vollstaendiger Neubeginn.

# Verwandt

* [Lernkurven in der Rueckschau](/befunde/lernkurven-rueckschau.md) - die Frage
* [1109 Episoden ohne Lernfortschritt](/befunde/langlauf-ohne-fortschritt.md)
* [Greif-Lerndeckel](/befunde/greif-lerndeckel.md) - ueber den Teacher hinaus: geschlossen
* [Struktur-Experte](/fragen/struktur-experte.md) - Lerngeschwindigkeit als Fitness, jetzt mit Einschraenkung
