---
type: Befund
title: Selbst-Aneignung stockt - jede selbst geborene Klasse verhungert
description: Ueber zwei Langlaeufe hinweg: 17 von 17 und 14 von 14 selbst geborenen Formklassen verhungern, keine wird je kommandiert. Die Aneignungsmaschinerie laeuft, konvergiert aber nicht. Wunder Punkt fuer das Projektziel.
tags: [act23, selbstlernen, formklassen, negativ]
status: stable
evidenz: gemessen
ebene: langlauf
generated: { by: claude/opus-5, at: 2026-08-30T00:00:00Z }
verified: { by: human:thomas, at: 2026-08-30T15:10:00Z }
sources:
  - id: langlauf
    resource: /raw/index.md
    title: log/pc_act23_2026-08-26_13-44-26.txt - 1109 Episoden
  - id: nachfolger
    resource: /raw/index.md
    title: log/pc_act23_2026-08-28_17-20-45.txt - 1053 Episoden
---

# Behauptung

Der Agent sieht laufend Unbekanntes, legt Klassen dafuer an - und **keine setzt sich fest**.
Das trifft [das Projektziel](/ziel.md) direkt, denn die Lieferquote misst den Arm, nicht die
Aneignung.

# Zahlen

Langlauf ueber 1109 Episoden:[^langlauf]

    17 neue Klassen geboren (neu-307 .. neu-323)
    17 davon verhungert  ("nie stabil wiedererkannt"), meist nach 24-27 Episoden
        drei Ausreisser 110 / 143 / 191 Episoden, Ende gleich
     0 davon je kommandiert (518 Pruefzeilen, ausnahmslos "kommandiert 0x")
    die 4 etablierten stagnieren: neu-9 ~30 %  neu-13 ~3 %  neu-34 ~28 %  neu-285 ~43 %
    unzuordenbare Sichtungen 0 -> 214, LINEAR (~0,19 je Episode)

Nachfolgelauf ueber 1053 Episoden, hoehere Lieferquote (56,4 %), Aneignung unveraendert
still:[^nachfolger]

    14 Klassen geboren, 14 verhungert, 0 je kommandiert (451 Pruefzeilen)
    unzuordenbare Sichtungen linear 0 -> 191
    Einzige Bewegung: neu-34 steigt 15 % -> 41 %

# Bewertung

Die linear wachsende Zahl unzuordenbarer Sichtungen ist der Kern: der Zustrom an Neuem reisst
nicht ab, aber die Konsolidierung fehlt. Eine Klasse entsteht aus drei Sichtungen **einer
einzigen Lage** - das reicht nicht, um sie beim naechsten Winkel wiederzuerkennen. Der Engpass
sitzt damit bei der **Geburt** einer Klasse, nicht an der Anspruchsschwelle danach; zwei
Fassungen einer "Dicken-Wache" am Anspruch haben gemessen nichts geloest, siehe
[Pruefstandsfalle](/mechanismen/pruefstandsfalle.md).

Das heisst **nicht**, dass Aneignung grundsaetzlich scheitert. Es gibt einen sauberen
Gegenbeleg: der Agent hat sich `obj_Y` selbst angeeignet - Farbe, Formklasse und Knopf in
15 von 28 Episoden, ueber beide Seeds, ohne Etikett, und lieferte danach 61-70 %. Die Kernlehre
dort: **die gerenderte Chroma zaehlt, nicht die RGBA** aus der Szenendefinition.

Ebenfalls kein Defekt, sondern Saettigung: in einer spaeteren Probe waren alle 7 Koerper bereits
gebunden - es gab schlicht nichts mehr anzueignen. Wer "verhungern" misst, muss also pruefen, ob
ueberhaupt noch freie Koerper da sind.

# Fallen

* Eine Formklasse **friert bei 80 Exemplaren ein** (85 % veraltet). Ein erster Fix dafuer loeste
  eine gemessene Kaskade aus (die Klasse frisst das fremde Objekt); erst die zweite Fassung mit
  Sicherheitsschranke verhindert sie.
* **Gleicher Seed erzwingt in act23 keine gleiche Objektfolge.** Wer zwei Laeufe vergleicht,
  darf das nicht voraussetzen.

# Offen

Der Weg zur Konsolidierung ist nicht gemessen. Naheliegend und im Bestand als Nutzeridee
vermerkt: aus einem bestaetigten Griff viele verschobene und gedrehte Varianten **im Latent**
erzeugen - RoPE macht die Verschiebung zur exakten Phasendrehung, das Fundament existiert.
Siehe [offene Faeden](/fragen/offene-faeden-act23.md).

# Verwandt

* [1109 Episoden ohne Lernfortschritt](/befunde/langlauf-ohne-fortschritt.md)
* [Projektziel](/ziel.md)
