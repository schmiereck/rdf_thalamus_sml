---
type: Befund
title: Lernkurven in der Rueckschau - ueber 2162 Episoden lernt kein Lerner messbar, und das Weltmodell ist ueberzuversichtlich
description: Prequentielle Auswertung (Vorhersage vor der Episode gegen ihren Ausgang) der beiden Langlaeufe, aus denen der heutige Zustand stammt (1109 und 1053 Episoden). Je 150er-Block flach - Lieferquote, Fovea gegen Detektor (5-6 mm), Policy gegen Teacher (9 mm), Selbsturteil (85-93 %), Weltmodell. Das Weltmodell trennt Erfolg und Misserfolg im Lauf mit AUC 0,59-0,60, kaum ueber dem, was die blosse Objektquote im Nachhinein liefert (0,57-0,58), und ist deutlich ueberzuversichtlich - mittleres mu 0,68 gegen eingetretene 0,45 bzw. 0,66 gegen 0,56; wo es 0,9-1,0 sagt, gelingt gut die Haelfte. Sein Brier-Wert ist nicht besser als eine konstante Vorhersage der Grundrate. Offen - satt oder lernunfaehig; dafuer der Ruecksetz-Versuch.
tags: [act23, lernen, weltmodell, langlauf, methode]
status: stable
evidenz: gemessen
ebene: langlauf
generated: { by: claude/opus-5.5, at: 2026-09-25T00:00:00Z }
sources:
  - id: logs
    resource: "log/pc_act23_2026-08-26_13-44-26.txt (1109 Ep) und log/pc_act23_2026-08-28_17-20-45.txt (1053 Ep, daraus act23_state.pkl); Zeilen [Welt-Vorhersage], [Fovea-Servo], [Stufe 2] |Netz-Teacher|, [Selbst-Urteil], [Auto]"
    title: Die beiden Langlaeufe des Live-Zustands
  - id: exv
    resource: /befunde/exekutionsvarianz.md
    title: Das Weltmodell sammelt das lernbare Signal nicht ein
---

# Die Frage

Nutzerauftrag: aus der **Lerngeschwindigkeit** etwas lernen. Das uebliche Mass ist der
prequentielle Fehler: wie gut sagt ein Lerner die NAECHSTE Episode voraus, bevor er auf ihr
lernt. Die Protokolle enthalten dafuer je Episode drei Groessen - und es gibt 724 Protokolle, darunter
die beiden Langlaeufe, aus denen der heutige Zustand stammt.

# Ergebnis

    Lauf 26.08. (1109 Ep)
    Block        geliefert  Welt Brier  Welt AUC  Fovea mm  Netz-Teacher  Selbsturteil
       0- 149      40 %       0,326      0,639      5,5        9,1           91 %
     300- 449      44 %       0,322      0,563      6,1        9,3           91 %
     600- 749      41 %       0,334      0,538      5,3        9,4           89 %
     900-1049      44 %       0,310      0,578      5,8        8,9           93 %

    Lauf 28.08. (1053 Ep, daraus der Live-Zustand)
       0- 149      58 %       0,233      0,656      5,2        8,9           91 %
     300- 449      54 %       0,262      0,585      5,5        9,3           93 %
     600- 749      56 %       0,274      0,543      5,2        9,3           86 %
     900-1049      57 %       0,261      0,577      6,0        9,3           90 %

**Kein Lerner zeigt eine Lernkurve.** Das bestaetigt den
[Langlauf-Befund](/befunde/langlauf-ohne-fortschritt.md) jetzt auch fuer die inneren Groessen jedes
einzelnen Lerners, nicht nur fuer die Quote.

## Das Weltmodell ist ueberzuversichtlich

    Lauf        mittleres mu   eingetreten   Brier Modell   Brier konstant   AUC Modell   AUC nur Objekt*
    26.08.         0,680          0,447         0,303           0,247          0,592        0,578
    28.08.         0,655          0,564         0,252           0,246          0,601        0,572

    Kalibrierung (Lauf 26.08.)
      mu 0,3-0,5   n = 168   vorhergesagt 0,43   eingetreten 0,35
      mu 0,5-0,7   n = 421                0,61                0,41
      mu 0,7-0,9   n = 396                0,79                0,50
      mu 0,9-1,0   n =  77                0,95                0,55

    * Objektquote im Nachhinein aus demselben Lauf - geschoent, also eine Obergrenze fuer "nur Objekt"

Drei Dinge:

1. **Die Vorhersage ist systematisch zu hoch**, um 0,1 bis 0,4 je nach Hoehe. Plausible Ursache,
   nicht geprueft: das Modell WAEHLT die Aktion nach seiner eigenen optimistischen Schaetzung
   (LCB ueber die Kandidaten), und das Maximum vieler verrauschter Schaetzungen ist nach oben
   verzerrt (Fluch des Siegers).
2. **Die Trennkraft ist im Lauf 0,60** - gegen 0,76, die es beim Start ueber sich selbst meldet
   (`[Welt-Guete]`, Halteteil mit Luecke aus dem eigenen Puffer). Zwischen "was es auf seinen
   Daten kann" und "was es auf der naechsten Episode kann" liegen 0,16.
3. **Es liefert kaum mehr als das Objekt.** Das passt zum
   [Weltmodell-Deckel](/befunde/exekutionsvarianz.md) (dort AUC 0,49 auf den eigenen Episoden, bei
   einer lernbaren Obergrenze von 82 %).

# Was offen bleibt

Flach kann **satt** heissen (alles gelernt, was die Architektur fassen kann) oder **lernunfaehig**
(die Lernschleife bewegt nichts mehr). Die Rueckschau trennt das nicht - dafuer braucht es eine
Lernkurve von einem NIEDRIGEN Stand aus. Das ist der
[Ruecksetz-Versuch](/befunde/ruecksetz-versuch.md): je eine Kopie mit einem frischen Lerner.

# Fallen

* **Die Fovea-Groesse misst Netz gegen Detektor**, nicht gegen die Wahrheit.
* **|Netz-Teacher| ist eine Schattenmessung** auf den besuchten Zustaenden; der Teacher ist selbst
  eine Regel, die Groesse misst also Nachahmung, nicht Koennen.
* **Die Objektquote als Vergleich ist im Nachhinein berechnet** und damit guenstiger, als ein
  echter Vorhersager sie haette.

# Verwandt

* [1109 Episoden ohne Lernfortschritt](/befunde/langlauf-ohne-fortschritt.md)
* [Die Ausfuehrung ist nicht der Deckel des Weltmodells](/befunde/exekutionsvarianz.md)
* [Struktur-Experte](/fragen/struktur-experte.md) - Lerngeschwindigkeit als Fitness
