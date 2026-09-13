---
type: Befund
title: Beim Trennen eines verschmolzenen Blobs entscheidet die Farbquelle ueber Rettung und Verschlimmerung
description: Auf der Farbklasse zu trennen, die im Eigenschafts-Tripel steht, macht den Fehler dreimal groesser als nichts zu tun (33,2 statt 18,2 mm Median, 98 statt 38 Prozent ueber 20 mm) - denn diese Klasse wurde aus der Verschmelzung geschrieben und ist die Mischchroma. Auf der gebundenen Klasse aus colour_of_body zu trennen bringt 6,7 mm und 1,4 Prozent. Dieselbe Rechnung, entgegengesetztes Ergebnis, je nach Quelle.
tags: [act23, wahrnehmung, verschmelzung, kommando]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-13T00:00:00Z }
sources:
  - id: sonde
    resource: "Kalibriersonde auf einer Kopie von act23_state.pkl (ad9d768c): 4 Koerperpaare x 6 Abstaende (20-50 mm) x 20 Lagen = 480 Sichtungen, keine Persistenz, kein Lauf"
    title: Farbquelle und Trennschnitt
---

# Warum ueberhaupt gemessen

[Jeder grobe Adressfehler sitzt im obersten Band](/befunde/adressfehler-sind-verschmelzung.md)
zeigt: die Adressierung hat ein Verschmelzungsproblem. Der Form-Split existiert bereits
([Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md)) und sollte in den Eigenschafts-Pfad
eingebaut werden. Vor dem Lauf war eine Zahl zu klaeren: der Schnitt, ab dem eine Verschmelzung
angenommen wird. **Dabei fiel etwas Wichtigeres auf.**

# Der Fund

Alle 480 Sichtungen, gemessen wird der Abstand der gelieferten Lage zur wahren Lage des
gemeinten Koerpers. Nur die verschmolzenen Faelle (n = 148):

    nichts tun (heutiger Pfad)        Median 18,2 mm    ueber 20 mm  38,5 %
    Split auf der TRIPEL-Farbe        Median 33,2 mm    ueber 20 mm  98,4 %
    Split auf der GEBUNDENEN Farbe    Median  6,7 mm    ueber 20 mm   1,4 %

**Dieselbe Rechnung, entgegengesetztes Ergebnis.** Der Split auf der Tripel-Farbe ist nicht
nur nutzlos, er ist deutlich schlechter als gar nichts zu tun.

Der Grund ist im Nachhinein zwingend: die Farbachse des Tripels hat die Wuerfelei **aus der
Verschmelzung heraus** geschrieben. Sie ist die Klasse der MISCHCHROMA - im Lauf erkennbar an den
hohen, spaet geborenen Nummern (`farbe-50`, `farbe-59`, `farbe-64`), die in den groben Fehlern
auffielen. Auf dieser Klasse zu trennen holt genau das Material heraus, das die Mischung
verursacht hat, also ueberwiegend den NACHBARN.

`colour_of_body` ist dagegen per Bauart sauber: `_farbbindung_neu` **ueberspringt verschmolzene
Blobs** bei der Bindung (`area > area_hi` -> "Mischchroma, nicht binden"). Ein Koerper, der beim
Binden verschmolzen war, bleibt lieber ungebunden als falsch gebunden.

> **Der Form-Pfad hat das immer schon richtig gemacht** - er nimmt `colour_of_body.get(body)`.
> Beim Uebertragen in den Eigenschafts-Pfad lag es nahe, statt dessen die Farbachse des Tripels zu
> nehmen, weil sie "zur Adresse gehoert". Genau das waere die Verschlimmerung gewesen.

# Der Schnitt

Der Quotient *Abstand Teil-zu-Blob / Spanne des Teils* - massstabsrelativ, damit kein absolutes
Mass an die heutigen sieben Koerper gebunden wird:

    getrennte Blobs   n=332   Median 0,30   25% 0,23   75% 0,47   95% 1,03
    verschmolzene     n=148   Median 1,12   25% 0,78   75% 1,47   95% 2,02

    Schnitt   Verschmelzung erkannt   Fehlalarm auf getrennten
      0,5            91,9 %                   21,4 %
      0,8            72,3 %                    9,9 %
      1,0            60,8 %                    5,4 %

Gewaehlt: **0,8**. Mein erster, geratener Wert war 0,7 auf einer falschen Groessenordnung - die
Messung hat ihn ersetzt.

> **NEBENBEFUND ENTKRAEFTET IM LAUF (2026-09-14).** Der Abschnitt unten sagt, immer zu
> trennen sei besser. Im Lauf kehrt sich beides um: Median 3,2 -> 6,0 mm, grobe Fehler
> 3,1 -> 8,7 %. Der Grund steht unter *Fallen* auf dieser Seite und hat trotzdem nicht
> geschuetzt. **Die Farbquelle (gebunden statt Tripel) bleibt gueltig** - sie wurde im Lauf
> gar nicht gegeneinander geprueft, sondern durchgehend gebunden verwendet.
> Siehe [Der Form-Split im Eigenschafts-Pfad](/befunde/eig-split-im-lauf.md).

# Der Schnitt koennte ueberfluessig sein

Ueber ALLE 480 Sichtungen, verschmolzen und getrennt zusammen:

    heutiger Pfad             Median 8,5 mm    ueber 20 mm  11,9 %
    immer auf Solo-Farbe      Median 5,8 mm    ueber 20 mm   1,5 %

**Immer zu trennen ist in Median UND Ausreissern besser.** Das widerspricht der Annahme im
`perceive_colour`-Kommentar ("while the blobs are separate the component mean is exact (0mm) and
this split is slightly worse (6mm)") - die galt fuer den Blob-Schwerpunkt, nicht fuer den Abstand
zur WAHREN Koerperlage, und die beiden sind nicht dasselbe.

Beide Fassungen sind deshalb gebaut (`ACT23_EIG_SPLIT` 1 = mit Indiz, 2 = immer). Welche traegt,
entscheidet das A/B - **nicht diese Seite**.

# Fallen

* **`ebene: pruefstand`.** Nach der [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) sagt das
  ueber den Lauf nichts. Vier dokumentierte Faelle stehen dagegen.
* **Die Lagenverteilung ist nicht die des Laufs.** Die Sonde stellt gezielt nahe Nachbarn (20-50 mm)
  und ueberwiegt damit Verschmelzungen stark. Im Lauf sind die meisten Szenen nicht verschmolzen -
  der Gewinn "immer trennen" kann dort kleiner oder negativ sein.
* **Nur zwei Koerper je Szene**, der Lauf hat sieben.
* **Die Solo-Farbklasse der Sonde ist der Bestfall** fuer `colour_of_body`. Im Lauf kann die
  Bindung fehlen (dann greift der Split gar nicht) oder aus einer frueheren, ebenfalls
  verschmolzenen Szene stammen.
* **`obj_L` und `obj_X` teilen sich `farbe-4`.** Der Split allein trennt sie nicht; dafuer ist die
  gestufte Filterung nach Form und Groesse im Einbau vorgesehen.

# Verwandt

* [Jeder grobe Adressfehler sitzt im obersten Band](/befunde/adressfehler-sind-verschmelzung.md) - der Anlass
* [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md) - der bestehende Mechanismus
* [Verschmelzungs-Abstandskurve](/befunde/verschmelzung-abstandskurve.md)
* [Der Form-Split im Eigenschafts-Pfad](/befunde/eig-split-im-lauf.md) - der Lauf, der den Nebenbefund entkraeftet
* [Die Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)
