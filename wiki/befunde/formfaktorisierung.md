---
type: Befund
title: Die Groesse dominiert die Form - und laesst sich nicht herausnormieren
description: Zwei Groessen DERSELBEN Form liegen im Deskriptorraum weiter auseinander (11,52) als zwei VERSCHIEDENE Formen gleicher Groesse (6,07). Vier Normierungsvarianten gemessen, alle gescheitert. Die Dicken-Wache am Anspruchstor in zwei Fassungen ebenfalls.
tags: [act23, formklassen, deskriptor, negativ]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-04T13:39:00Z }
verified: { by: human:thomas, at: 2026-09-04T13:39:00Z }
sources:
  - id: proben
    resource: "scratchpad/faktor_probe.py, skalen_probe.py, dicke_probe.py"
    title: 20-25 Sichtungen je Variante, je eigener Prozess
---

# Die Idee (Nutzer)

"Statt Objektklassen wuerden wir die Entstehung der drei EIGENSCHAFTEN als Klassen beobachten.
Damit waere ein genereller Weg fuer beliebige neue Objekte offen, als Kombination dieser
Eigenschaften."

Der Vorschlag ist **kein Umbau, sondern eine Vollendung** - drei der fuenf Achsen sind bereits
faktorisiert:

    FARBE       eigene Klassenfamilie (colour_openset, farbe-N)          fertig
    POSITION    RoPE-Phase, exakt und separat                            fertig
    AUSRICHTUNG _yaw_from(F) / _yaw4_from(F), aus derselben Transformation fertig
    ZUSTAND     lifted, slipped, rested, Griffdruck-Verlauf              teilweise
    GROESSE     NICHT faktorisiert, leckt in die Form; obj_h ist zudem PRIVILEGIERT

# Die Messung, die die Idee stuetzt

    Median-Abstand im Deskriptorraum (novel_th 7,72), 20 Sichtungen je Variante:
      GLEICHE Form, andere Breite:  Y10<->Y20  11,52 | Y14<->Y20  7,43 | Y10<->Y14  5,51
      ANDERE Form, gleiche Breite:  Y14<->T14   6,07 | Y10<->T14   7,10

**Die Groesse dominiert die Form.** Das erklaert den Fehlschlag beim 10-mm-Y vollstaendig: es
wurde von obj_T beansprucht, weil es dem T naeher ist (7,10) als seinem eigenen 20-mm-Bruder
(11,52).

Ursache im Code: `_harmonics_at` tastet auf **festen Weltradien** ab. Ein groesseres Objekt
fuellt mehr Ringe - der Deskriptor ist **nicht groesseninvariant**.

# "Groesse" ist keine einzelne Zahl

* Die **Spannweite** ist ueber alle drei Y-Breiten fast gleich (34/35/36 mm), weil sie von der
  Arm**laenge** bestimmt wird. Eine Normierung darauf half kaum (11,52 -> 10,30, Reihenfolge
  unveraendert). **Der erste Normierungsversuch scheiterte an der falschen Groesse.**
* Die **Materialdicke** trennt dagegen sauber (Distanztransformation, 90 %-Quantil):

        Y10 7,07 px (Streuung 0,07) | Y14 8,25 (0,16) | Y20 10,00 (0,05)
        T14 8,49 (0,21) | L 8,49 (0,50) | U 8,54 (0,54)

  Die Abstaende sind das 6- bis 40-fache der Streuung. Und T14 liegt nahe bei Y14, wie es sein
  **muss** (beide 14-mm-Balken) - die Dicke misst Dicke, nicht Identitaet. Der Wert wird in
  `perceive_all` bereits gerechnet, nur nicht als Kanal herausgefuehrt.

# Die Form laesst sich nicht groessenfrei normieren

Vier Varianten auf denselben rohen Harmonischen (25 Sichtungen je Koerper). Kennzahl =
groesster Groessen-Abstand / kleinster Form-Abstand; **unter 1,0 waere das Ziel**:

    heute: |F|, feste Ringe                     2,54
    Ringe an der DICKE skaliert                 2,23
    je Ring durch den DC-Anteil geteilt         2,13
    durch die Gesamtfuellung geteilt            2,42

**Keine kommt auch nur in die Naehe.** Die Groesseninformation ist kein Skalenfaktor, den man
herausdividieren kann - sie ist in die Harmonischen eingewoben: ein groesserer Arm fuellt mehr
Kreisumfang **je Ring**, und das ueberlebt jede Radien- oder Amplitudennormierung.

Der Ausweg, den dieselbe Messung zeigt: **die Faktorisierung gehoert NEBEN den Deskriptor, nicht
hinein** - nicht die Form groessenfrei machen, sondern die Groesse zu einem eigenen Kanal mit
Vetorecht.

# Die Dicken-Wache - beide Fassungen gescheitert

**Fassung 1** (Pruefung nach dem Anspruch, je 200 Ep, 10-mm-Y, Seed 11):

    1) HAUPT  10-mm-Y: AUS kein Kandidat, kein Knopf | AN kein Kandidat, kein Knopf
    2) Ansprueche von neu-9   137x -> 105x   (-24%)   Wache FEUERT
       novel-Meldungen         53  -> 122    (2,3x)   Wache erzeugt Neuheit
    3) Regressionswache  L 92->96 | U 93->97 | T 100->100 | X 78->77   sauber
    4) Lieferquote       48,0 -> 48,5%

**Die Wache annulliert, sie leitet nicht um.** In `resolve` gewinnt neu-9 den Wettbewerb, die
Wache greift erst danach und macht daraus ein `None`. Und der Knopf zaehlt genau das Feld, das
die Wache leert. **Ohne Umleitung kein Treffer, ohne Treffer nie ein Knopf.**

**Fassung 2** (Pruefung IN der Kandidatenschleife, unpassende Klassen werden uebersprungen,
bevor bester und zweitbester feststehen):

    1) HAUPT Knopf                 AUS nein | AN nein
    2) Treffer des Kandidaten      AUS max 2 in 12 Blicken | AN max 0
    3) Vetos (neue Logzeile)       AUS 0 | AN 567 Ansprueche in 163 Blicken
    4) Regression   L 92->90 | U 93->97 | T 100->100 | X 78->85
    5) Lieferquote                 48,0% -> 44,5%

**Der entscheidende Befund: mit UND ohne Wache holt der Kandidat nur 0-2 Treffer in 12 Blicken.
Der Engpass liegt nicht im Anspruchswettbewerb.** Eine junge Klasse, aus 3 Sichtungen EINER Lage
geboren, erkennt ihr Objekt in anderen Lagen nicht wieder - das ist eine **Repraesentations-**,
keine Wettbewerbsgrenze. Genau dafuer existiert `OPEN_MARGIN`; die Wache nimmt der jungen Klasse
diese Kruecke teilweise weg und macht es schlimmer.

Stand: `ACT_SHAPE_DICKE_WACHE` Vorgabe **AUS** (beide Fassungen). Die Dicke selbst bleibt ein
sauberer Kanal - nur ihre Verwendung **am Anspruchstor** traegt nicht. Der Veto-Logschalter
`ACT_SHAPE_DICKE_LOG` bleibt.

# Fallen

* **Ein selbst eingefuehrter Konfounder.** Der Kontrollarm hatte 0 Geburten, waehrend derselbe
  Aufbau zwei Tage zuvor 4 hatte. Die einzige wirksame Aenderung war die
  **Exemplar-Auffrischung**, die ich ohne Nutzennachweis auf Vorgabe AN gesetzt hatte. Der
  Isolierlauf bestaetigt es zifferngenau:

        Lauf                              Geburten  Kandidat  novel  neu-9-Ansprueche
        Wache AUS, Auffrischung AUS           4        JA       53        137
        Wache AN,  Auffrischung AUS           4        JA      122        105
        Wache AUS, Auffrischung AN            0        nein     42        138
        frueher (Referenzlauf)                4        JA       53        137

  **Ich hatte mir die Vergleichsgrundlage unter den Fuessen weggezogen.**
  Uebergreifend: **wer eine Kette von A/Bs faehrt, darf die Vorgaben zwischendrin nicht
  verschieben - auch nicht "sichere" Verbesserungen ohne Nutzennachweis.**
* **Eine Wache, die nur verneinen kann, loest kein Zuordnungsproblem.** Die Vorschaltpruefung
  testete nur EINE Richtung ("wird der falsche Anspruch verworfen?") und nie die Gegenrichtung
  ("kann die richtige Klasse danach gewinnen?").
* **Fallende Prozente sind nicht dasselbe wie fallende Trefferzahlen.** Der Kandidat neu-338
  bekam in 8 Blicken genau EINEN Treffer (0/50/33/25/20/14/12 % = ein Treffer ueber wachsendem
  Nenner); ich hatte das zuerst als "sie gewinnt Ansprueche" fehlgelesen.
* **Dritte Fehlvorhersage einer isolierten Messung.** Meine Vorschaltpruefung (junge Klasse mit
  2 Exemplaren: Wache AUS 10/12, AN 12/12) sagte das **Gegenteil** voraus. Siehe
  [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md).

# Verwandt

* [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) - die umgesetzte Form der Idee
* [Formklassen-Lebenszyklus](/mechanismen/formklassen-lebenszyklus.md)
