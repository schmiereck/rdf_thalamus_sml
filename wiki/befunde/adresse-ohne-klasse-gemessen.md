---
type: Befund
title: Der Formvektor ist die gute Adresse - ohne Klasse, aus einer Sichtung, nach 7 statt 22 Episoden
description: Drei frische Arme je 140 Episoden. Die Direkt-Adressierung eignet sich einen Koerper nach 7 Episoden an, der Weg ueber Klassengeburt und Bestaetigung braucht 22. Und die Aufloesung spaltet sich scharf nach der genannten Achse - die reine Formvektor-Adresse haelt in 72,7 und 76,5 Prozent der Episoden mit 5 mm Median und null groben Fehlern, die Adresse aus Farbe und Groessenband in 5,6 und 0,0 Prozent. Zum ersten Mal spricht eine Messung FUER die stetige Adressierung statt nur nicht dagegen.
tags: [act23, kommando, latent, selbstlernen, ab]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-16T00:00:00Z }
sources:
  - id: ab
    resource: "Drei frische kopflose Laeufe (ACT23_FRESH=1) je 140 Episoden, Seed 4242, NOVEL_WEITER=1 in allen dreien"
    title: kette / direkt / beides
  - id: bau
    resource: /mechanismen/adresse-ohne-klasse.md
    title: Der Bau und die zwei Defekte, die dabei auffielen
---

# Aufbau

    Arm      zusaetzlich zu NOVEL_WEITER=1
    kette    FREIE_VERGABE=1                              Klasse + Knopf, der bekannte Weg
    direkt   EIG_DIREKT=1 EIG_STETIG=1                    eine Sichtung statt der Kette
    beides   FREIE_VERGABE=1 EIG_DIREKT=1 EIG_STETIG=1    stoert der neue den alten Weg?

**Das ist KEIN Ein-Schalter-A/B**, sondern ein Vergleich zweier **Mechanismen** fuer dieselbe
Sache. Wer die Spalten wie eine Einzelvariable liest, liest falsch.

# Aneignung: 7 gegen 22 Episoden

    kette    Ep 22  Knopf 'Neue Form 2' auf obj_T
             Ep 23  Knopf 'Neue Form 3' auf obj_blue
             Ep 39  Knopf 'Neue Form 4' auf obj_X

    direkt   Ep  7  DIREKT  '~gesehen'        auf obj_T
             Ep 15  DIREKT  'farbe-1 + dick'  auf obj_X
             Ep 20  Knopf   'Neue Form 4'     auf obj_X

    beides   Ep  7  DIREKT  '~gesehen'        auf obj_T
             Ep 15  Knopf 'Neue Form 2' auf obj_blue  +  DIREKT 'farbe-1 + dick' auf obj_X
             Ep 18  Knopf 'Neue Form 3' auf obj_T
             Ep 47  Knopf 'Neue Form 4' auf obj_X

**Der erste Koerper wird nach 7 statt nach 22 Episoden kommandierbar** - dreimal schneller, und
ohne Geburt, ohne Bestaetigung, ohne Knopf. In `beides` kommt die Direkt-Adresse der ersten
Knopfvergabe um acht Episoden zuvor.

# Die Aufloesung spaltet sich scharf nach der genannten Achse

    Arm      Koerper   Adresse             aufgeloest  Rueckfall   Anteil   Median   grob >20mm
    direkt   obj_T     '~gesehen'              16          6       72,7 %   5,0 mm       0
    direkt   obj_X     'farbe-1 + dick'         1         17        5,6 %   141,3 mm     1
    beides   obj_T     '~gesehen'              13          4       76,5 %   5,1 mm       0
    beides   obj_X     'farbe-1 + dick'         0         21        0,0 %      -         0

    Formvektor gegen Farbe+Groesse:  29/39 gegen 1/39,  p = 1,5e-11
    (einzeln 0,000018 und 0,000000; Bonferroni bei zwei Koerpern 0,025)

**Die reine Formvektor-Adresse haelt.** `'~gesehen'` ist EINE Achse ohne Namen - nur der
8-dimensionale Einbettungsvektor - und sie loest in 72,7 bzw. 76,5 % der Episoden auf, mit 5 mm
Median, 100 % Eindeutigkeit und **null groben Fehlern**. Das trifft die
[Offline-Vorhersage](/mechanismen/adresse-ohne-klasse.md) auf den Punkt: dort hielten alle drei
Achsen zusammen in 72,2 % der Szenenwechsel.

**Die Adresse aus Farbe und Groessenband haelt nicht.** `'farbe-1 + dick'` loest in 5,6 bzw. 0,0 %
auf - und der eine Treffer lag **141 mm daneben**, also am falschen Koerper.

> Zum ersten Mal spricht eine Messung **fuer** die stetige Adressierung, statt nur nicht dagegen.
> Und sie spricht genau in der Richtung der
> [Nutzeridee](/fragen/stetige-adressierung.md): das Gute ist der LATENTE VEKTOR, das Schlechte
> sind die diskretisierten Achsen.

# Lieferquote - nicht das Kriterium, aber sie sagt etwas

    kette   14/140 = 10,0 %
    direkt   7/140 =  5,0 %   (gegen kette p = 0,17)
    beides  13/140 =  9,3 %   (gegen kette p = 1,00)

Nichts loest auf, und die Quote war nie der Massstab ([ziel.md](/ziel.md)). Was sie zeigt:
**`beides` ist von `kette` nicht zu unterscheiden** - die Direkt-Adressierung stoert den
regulaeren Weg also nicht. Dass `direkt` allein tiefer liegt, ist bei 7 gegen 14 Lieferungen
nicht zu trennen; plausibel ist, dass dort in 21 Episoden ein Koerper mit nicht aufloesender
Adresse geuebt wurde.

# Was NICHT gezeigt ist

**Ein Koerper je Adresstyp.** `'~gesehen'` sass auf obj_T, `'farbe-1 + dick'` auf obj_X. Ob die
Formachse besser ist oder obj_T der leichtere Koerper, **trennt diese Messung nicht**. Zwei
unabhaengige Indizien stuetzen die Achsen-Lesart, ersetzen sie aber nicht:

* Das oberste Groessenband ist gemessen das Band der VERSCHMOLZENEN Blobs - 26 von 26 groben
  Adressierungsfehlern lagen dort ([Befund](/befunde/adressfehler-sind-verschmelzung.md)).
  `'dick'` ist dieses Band.
* obj_X ist der Koerper, dem als einzigem eine gebundene Farbklasse fehlt, und seine GERENDERTE
  Chroma ist von obj_L kaum zu unterscheiden ([[act23-kreuz-farbkollision]]).

**Der billige naechste Schritt, der es entscheidet:** die Formachse in JEDER Direkt-Adresse
erzwingen (sie war bei obj_X vorhanden - `resolve()` gab die trainierte Klasse `cube` - die
Wuerfelei hat sie nur nicht gezogen) und obj_X erneut messen. Dann stehen beide Koerper mit
derselben Achse da.

# Zwei Defekte, die der Lauf gefunden hat

Beide sind auf der [Mechanismus-Seite](/mechanismen/adresse-ohne-klasse.md) ausgefuehrt:

1. **`area_hi` war der falsche Verschmelzungsschutz** - die allererste Adresse entstand auf einem
   Fleck, den die Formstufe im selben Blick als `('verschmolzen', 603px)` gemeldet hatte, und
   loeste danach in keiner Episode mehr auf. Jetzt sperrt die Farbstreuung (`_merge_th`).
2. **`eig_bezug` fror den Notnagel ein.** Der Cache stand vor der Fallunterscheidung, also galt im
   frischen Lauf dauerhaft 1,86, waehrend das gemessene Bezugsmass nach 46 Episoden bei 2,257 lag
   - die Formtoleranz war 21 % zu eng, genau in der Konfiguration, in der die Direkt-Adressierung
   arbeitet. Der Docstring versprach das Gegenteil.

Vor Reparatur 2 loesten die Adressen in 3 von 18 Faellen auf, danach in 29 von 78 insgesamt und in
29 von 39 auf der Formachse.

# Fallen

* **Ein Seed, drei Arme, 140 Episoden.** Die strukturellen Aussagen (Ep 7 gegen 22, die
  Achsen-Spaltung) sind mechanisch belegt und hoch signifikant; Quote und Geburtenzahlen sind es
  nicht.
* **Die Adresse ist eingefroren** und wird nie nachgefuehrt. 23 bzw. 25 Rueckfaelle sind der Preis.
* **Reiner Formvektor heisst `servo=False`** - kein Tracker kann einem Vektor folgen, die Fovea
  bleibt also aus. Dass die Adresse trotzdem auf 5 mm trifft, ist bemerkenswert und heisst auch:
  eine Fovea auf dem Einbettungsvektor waere ein eigener, lohnender Bau.
* **Der Erzeuger verformt obj_T zu einem 60x8-mm-Balken.** Gestreckte Formen sind die
  lagesensitivsten im Deskriptor - dass ausgerechnet dort 72 % halten, ist die konservative
  Richtung, kein Rosinenpicken.
* **Die Welt hat weiter sieben Koerper.** Nach obj_X schweigt der Erzeuger, in allen drei Armen.
* **Vorgabe bleibt 0** fuer `ACT23_EIG_DIREKT`.

# Verwandt

* [Die Adresse ohne Klasse](/mechanismen/adresse-ohne-klasse.md) - der Bau
* [Stetig adressieren statt Klassen vergeben](/fragen/stetige-adressierung.md) - die These, hier zum ersten Mal gestuetzt
* [Die stetige Adressierung im Lauf](/befunde/stetige-adressierung-im-lauf.md) - der neutrale Schritt davor
* [Der Erzeuger reicht die Probe-Rolle weiter](/befunde/erzeuger-repariert.md) - der Bezugsarm
* [Adressfehler sind Verschmelzung](/befunde/adressfehler-sind-verschmelzung.md) - warum das oberste Band verdaechtig ist
