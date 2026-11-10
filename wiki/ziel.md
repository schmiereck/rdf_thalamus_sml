---
type: Referenz
title: Projektziel und Erfolgskriterium
description: Das uebergreifende Kriterium - die Architektur soll neue Farben, Formen, Umgebungen und Aufgaben SELBST lernen. Den geskripteten Teacher zu schlagen ist ausdruecklich nicht verlangt.
tags: [ziel, prinzip]
status: stable
evidenz: gemessen
ebene: code
generated: { by: claude/opus-5, at: 2026-09-07T00:00:00Z }
sources:
  - id: nutzer
    resource: "Nutzeraussagen 2026-07-07 und 2026-07-14, uebernommen aus dem Memory-Bestand"
    title: Thomas Schmiereck, wiederholt bestaetigt
---

# Behauptung

Gesucht ist eine **Architektur**, der man neue Farben, Formen, Umgebungen und Aufgaben geben
kann und die sie **selbst lernt** - selbstueberwacht, ohne geskripteten Lehrer. Nicht gesucht
ist ein effizient arbeitender 6-DOF-Arm.

Das Bild des Nutzers: ein **spielendes, lernendes Kind**, das die Welt entdeckt, Dinge
ausprobiert und dabei lernt. Die Lieferquote des Arms bleibt der **Massstab** fuer einzelne
Implementierungen, aber sie ist nicht das Ziel.

# Bewertung

Daraus folgt, wie ein Ergebnis zu beurteilen ist:

* Ein selbst gelerntes Ergebnis, das **schlechter** ist als der Teacher, ist **kein
  Misserfolg**. Es darf nicht als solcher dargestellt werden.
* Die richtigen Fragen sind: Lernt der Agent aus **eigenen** Versuchen? Verallgemeinert er auf
  zurueckgehaltene Formen und Aufgaben **ohne Nachstellen von Hand**? Wird er mit mehr
  Erfahrung besser?
* Der Teacher ist bestenfalls ein **sicherer Prior** zum Bootstrappen, nie das Ziel.

# Zwei harte Architekturregeln

**Alles laeuft durch ein lernendes Netz.** (Seit 2026-11-10 nicht mehr auf PC-CVNN festgelegt, siehe
[Entscheidung](/entscheidungen/lernendes-netz-statt-pc-cvnn.md).) Keine Positionen, die von mathematischen
Algorithmen erkannt und eingespeist werden. Ein zweites Auge mit anderer Wahrnehmung ist
willkommen - aber nur, wenn es selbst ein lernendes Netz ist. `perceive_all` (CC-Segmentierung
+ Homographie + PCA) ist genau die Kruecke, die abgebaut werden soll; es gilt als
Uebergangsgeruest.

**Keine festen Regeln zur Laufzeit ausserhalb des Trainings.** Das Netz soll entscheiden, auch
wann der Greifer schliesst. Details und der geloeste Praezedenzfall stehen in
[Laufzeitregeln](/mechanismen/laufzeit-regeln.md).

# Die Welt, in der das messbar ist

Bis 2026-09-10 trug jede Form **genau eine** Farbe (nur der Wuerfel drei), und in 5 von 6
Farbklassen bestimmte die Farbe die Form eindeutig. In dieser Welt kann ein Netz "orange -> L"
lernen und liegt zu 100 % richtig - Generalisierung ueber Farb/Form-**Kombinationen** war dort
schlicht nicht pruefbar. Seit dem 2026-09-10 werden die Farben je Episode permutiert
([Farbe und Form entkoppelt](/befunde/farb-mischung.md)). **Quotenzahlen von vor und nach diesem
Datum vergleichen zwei verschiedene Aufgaben.**

# Fallen

Der Kern dieses Ziels wird beim Messen leicht verraten: fast alle Kennzahlen im Projekt
(Lieferquote, Endabstand, Teacher-Abstand) messen den **Arm**, nicht die **Aneignung**. Eine
Aenderung, die die Quote hebt und die Selbst-Aneignung nicht beruehrt, trifft das Ziel nicht.
Der offene wunde Punkt dazu ist [Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md).

# Verwandt

* [Greif-Lerndeckel](/befunde/greif-lerndeckel.md) - warum eine Aufgabe nahe der Decke
  Selbstlernen gar nicht zeigen **kann**, und wo es dann doch gelang
* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md)
