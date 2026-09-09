---
type: Befund
title: Der Keim-Fix wirkt auf die direkte Zielgroesse - und nicht messbar auf die Quote
description: ACT23_KEIM_FIX senkt den Anteil falscher Trackerstarts unter mehrdeutigen Szenen von 51,5 auf 6,7 Prozent (gepaarter Seed-Sweep, Fisher p = 0,0001, beide Seeds gleichgerichtet). Die Lieferquote steigt gepoolt um 2,5 Punkte, p = 0,65 - die Hochrechnung von 3,5 Punkten ist damit weder bestaetigt noch widerlegt.
tags: [act23, wahrnehmung, tracker, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-09T02:00:00Z }
sources:
  - id: sweep
    resource: "Gepaarter Seed-Sweep: 4 kopflose Steuerungslaeufe je 120 Episoden (Seed 7 und 23, ACT23_KEIM_FIX 0/1), alle aus einem eingefrorenen Schnappschuss 98a293f2, gleichzeitig gefahren"
    title: Keim-Fix A/B
  - id: ursache
    resource: /befunde/keim-erreicht-tracker-nicht.md
    title: Der Befund, der die Reparatur begruendet
---

# Behauptung

Die Reparatur wirkt genau dort, wo sie soll: der Anteil **falscher Trackerstarts unter
mehrdeutigen Szenen** faellt von 51,5 % auf 6,7 %, in **beiden** Seeds gleichgerichtet, gepoolt
p = 0,0001. Der Keim greift statt in 0 % nun in 95-97 % der Episoden.

Auf die Lieferquote schlaegt das **nicht messbar** durch: gepoolt 50,4 -> 52,9 %, p = 0,65. Die
in [Der Keim erreicht den Tracker nie](/befunde/keim-erreicht-tracker-nicht.md) angestellte
Hochrechnung von ~3,5 Punkten ist damit **weder bestaetigt noch widerlegt**.

# Aufbau

**Gepaarter Seed-Sweep** statt eines einzelnen A/B-Paars - die Lehre aus
[Zwei Laeufe sind dieselbe Rechnung](/befunde/laeufe-sind-reproduzierbar.md): ein Lauf ist eine
Stichprobe, die Replikate sind die Seeds. Vier Laeufe je 120 Episoden, alle aus **einem**
eingefrorenen Schnappschuss (`98a293f2`), gleichzeitig gefahren, einziger Unterschied je Paar ist
`ACT23_KEIM_FIX`.

Zielgroesse ist bewusst **nicht** die Lieferquote: nur ~14 % der Episoden sind ueberhaupt
mehrdeutig, der Effekt ist also klein gegen die Nachweisgrenze von 26 Punkten je 50er-Fenster
([Rechnerlast](/befunde/rechnerlast.md)). Gemessen wird, was die Reparatur direkt betrifft.

# Zahlen

    Arm       Ep   Keim | mehrdeutig  Fehlstart | 1 Kand.  Fehlstart | Quote  | fremder Belief
    s7_aus   120     0% |         17   7 =  41% |     103    1 =  1% | 55,8 % |   9 =  7,5 %
    s7_an    120    95% |         14   1 =   7% |     106    1 =  1% | 55,8 % |  11 =  9,2 %
    s23_aus  120     0% |         16  10 =  62% |     104    6 =  6% | 45,0 % |  22 = 18,3 %
    s23_an   120    97% |         16   1 =   6% |     104    4 =  4% | 50,0 % |  10 =  8,3 %

    DIREKTE ZIELGROESSE: Fehlstart unter mehrdeutigen Szenen
      Seed  7   aus  7/17 = 41,2 %   an 1/14 =  7,1 %   Fisher p = 0,0454
      Seed 23   aus 10/16 = 62,5 %   an 1/16 =  6,2 %   Fisher p = 0,0021
      gepoolt   aus 17/33 = 51,5 %   an 2/30 =  6,7 %   Fisher p = 0,00010

    Lieferquote (Nebengroesse, unterversorgt)
      Seed  7   aus 67/120 = 55,8 %   an 67/120 = 55,8 %   p = 1,000
      Seed 23   aus 54/120 = 45,0 %   an 60/120 = 50,0 %   p = 0,518
      gepoolt   aus 121/240 = 50,4 %  an 127/240 = 52,9 %  p = 0,648

# Bewertung

* **Die Reparatur tut, was sie soll**, und der gepaarte Aufbau traegt: beide Seeds zeigen
  dieselbe Richtung, obwohl ihre Ausgangsquoten (41 % und 62 %) deutlich auseinanderliegen.
* **Kein Schaden an den Nachbarwerten.** Fehlstarts bei nur einem Kandidaten bleiben gleich
  (1 %) oder sinken (6 % -> 4 %); der Anteil fremder Beliefs faellt bei Seed 23 stark
  (18,3 -> 8,3 %) und steigt bei Seed 7 leicht (7,5 -> 9,2 %). Netto guenstig, einzeln Rauschen.
* **Die Quote bleibt offen, und das ist ein ehrliches Ergebnis, kein Messfehler.** Seed 7
  liefert mit sechs weniger Fehlstarts **exakt gleich viele** Episoden (67/120 in beiden Armen),
  Seed 23 sechs mehr. Wer daraus einen Quotengewinn liest, ueberliest die Streuung.

> **Warum "sechs Fehlstarts weniger" nicht "sechs Lieferungen mehr" heisst:** sobald die
> Reparatur die erste Entscheidung aendert, entkoppelt sich der Zufallsstrom und **alle**
> folgenden Episoden sind andere Szenen. Die Quotenspalten vergleichen zwei verschiedene
> Trajektorien, nicht dieselben Episoden mit und ohne Fix. Die direkte Zielgroesse ist davon
> unberuehrt, weil sie eine RATE innerhalb jedes Laufs misst.

# Was danach noch offen ist

**Zwei Restluecken, beide klein und beide benannt:**

1. **Ein zweiter, kleinerer Keim-Ausfall.** In ~3-5 % der Episoden steht
   `veroeffentlicht '__unset__'` - es wurde ueberhaupt kein Keim gesetzt. Ursache: trifft die
   Eigenschafts-Adressierung nichts, faellt `perceive()` auf die privilegierte wahre Lage zurueck
   und **veroeffentlicht dabei keinen Keim** (`pc_act23.py:2992`). Nicht repariert.
2. **Die Kennzahl saettigt bei wenigen Millimetern.** Zwei der verbleibenden Fehlstarts sind
   Etikettierungsartefakte: `obj_L: Keim JA | Start auf obj_U (2 mm) | eigenes Objekt 3 mm`. Wenn
   zwei Koerper 1 mm auseinander projizieren, ist "welcher Koerper ist naeher" keine sinnvolle
   Unterscheidung mehr. Die 6,7 % sind damit eher eine **Obergrenze** des Restfehlers.

# Folgen

**Der Nutzer hat die Vorgabe am 2026-09-09 auf `1` gestellt** (`ACT23_KEIM_FIX`). Dafuer sprach:
die direkte Zielgroesse verbessert sich um den Faktor 8 bei p = 0,0001, es ist die
Wiederherstellung des beabsichtigten Verhaltens und kein neues Verfahren, und an keiner
Nebengroesse ist Schaden messbar. Dagegen sprach nichts Gemessenes.

**Was dabei NICHT mitgekauft ist:** ein Quotengewinn. Wer diese Umstellung spaeter als
Quotenmassnahme zitiert, zitiert falsch - gepoolt 50,4 -> 52,9 % bei p = 0,65.

Geprueft ohne jede Umgebungsvariable: `[Keim] ... Keim JA (gesucht 'eig:obj_blue',
veroeffentlicht 'eig:obj_blue')`, und `ACT23_KEIM_FIX` erscheint nicht mehr in der Zeile
"Abweichungen von der Vorgabe". **Rueckfall in einer Zeile:** `ACT23_KEIM_FIX=0` - dann faellt
`_kkey` auf `key` zurueck, zifferngenau der Stand vor `d85250b`.

# Verwandt

* [Der Keim erreicht den Tracker nie](/befunde/keim-erreicht-tracker-nicht.md) - die Ursache
* [Der Tracker rastet auf dem Nachbarn ein](/befunde/ablenker-bindung-gemessen.md)
* [Zwei Laeufe sind dieselbe Rechnung](/befunde/laeufe-sind-reproduzierbar.md) - warum gepaart ueber Seeds
* [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md)
